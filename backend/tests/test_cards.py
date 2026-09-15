import sqlite3
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.cards import CardService
from app.db import SCHEMA

USER_ID = "u_test"
TIMEZONE = "UTC"
EVENING_START = "20:00"
TODAY = date(2026, 9, 20)  # a Sunday, so start-of-week == TODAY


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    connection.execute(
        "INSERT INTO user (id, timezone, evening_start, created_at) VALUES (?, ?, ?, ?)",
        (USER_ID, TIMEZONE, EVENING_START, "2026-01-01T00:00:00Z"),
    )
    connection.commit()
    yield connection
    connection.close()


@pytest.fixture
def service(conn):
    return CardService(conn)


def at(hour, minute=0, day_offset=0):
    return datetime(
        TODAY.year, TODAY.month, TODAY.day, hour, minute, tzinfo=ZoneInfo(TIMEZONE)
    ) + timedelta(days=day_offset)


def insert_commitment(
    conn, *, title="eval", stakes="ordinary", deadline=None,
    effort_minutes=500, banked_effort_minutes=0, status="open", closed_at=None,
):
    if deadline is None:
        deadline = TODAY + timedelta(days=5)
    commitment_id = f"cm_{uuid.uuid4().hex}"
    conn.execute(
        """
        INSERT INTO commitment (
            id, user_id, title, category, stakes, deadline,
            effort_minutes, banked_effort_minutes, status, closed_at,
            source, created_at
        ) VALUES (?, ?, ?, 'build', ?, ?, ?, ?, ?, ?, 'manual', ?)
        """,
        (
            commitment_id, USER_ID, title, stakes, deadline.isoformat(),
            effort_minutes, banked_effort_minutes, status, closed_at,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    return commitment_id


def insert_card(
    conn, *, commitment_id, offer_date, duration_minutes, outcome=None,
    state="resolved", offered_at=None,
):
    card_id = f"c_{uuid.uuid4().hex}"
    conn.execute(
        """
        INSERT INTO card (
            id, user_id, commitment_id, offered_at, offer_date,
            duration_minutes, score_at_offer, window_minutes_at_offer,
            copy_text, copy_source, state, outcome
        ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 'x', 'fallback', ?, ?)
        """,
        (
            card_id, USER_ID, commitment_id,
            offered_at or f"{offer_date.isoformat()}T12:00:00Z",
            offer_date.isoformat(), duration_minutes, state, outcome,
        ),
    )
    conn.commit()
    return card_id


# --- fresh offers -----------------------------------------------------


def test_fresh_offer_sizes_at_45_anchor_and_persists(service, conn):
    commitment_id = insert_commitment(conn, title="the eval", effort_minutes=500)

    result = service.get_or_offer(
        USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(14)
    )

    assert result["quiet"] is None
    card = result["card"]
    assert card["commitment_id"] == commitment_id
    assert card["duration_minutes"] == 45
    assert card["copy_text"] == "45 minutes on the eval. Evening starts at 8."
    assert card["state"] == "offered"

    row = conn.execute("SELECT * FROM card WHERE id = ?", (card["id"],)).fetchone()
    assert row["copy_source"] == "fallback"
    assert row["slot_boundary"] == 1


def test_second_card_of_day_has_no_boundary_clause(service, conn):
    insert_commitment(conn, title="the reading", effort_minutes=500, deadline=TODAY + timedelta(days=1))
    first = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(10))
    # Complete/resolve the first so a second can be offered.
    conn.execute(
        "UPDATE card SET state = 'resolved', outcome = 'completed' WHERE id = ?",
        (first["card"]["id"],),
    )
    conn.commit()

    second = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(11))

    assert second["card"]["copy_text"] == "45 minutes on the reading."


def test_slice_clamped_to_effort_remaining(service, conn):
    insert_commitment(conn, title="tiny task", effort_minutes=30)

    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(10))

    assert result["card"]["duration_minutes"] == 30


def test_slice_clamped_to_window(service, conn):
    insert_commitment(conn, title="big task", effort_minutes=500)
    # 30 minutes until evening_start (20:00) -> window binds below the anchor.
    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(19, 30))

    assert result["card"]["duration_minutes"] == 30


# --- quiet reasons ------------------------------------------------------


def test_evening_started_reason(service, conn):
    insert_commitment(conn)
    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(21))
    assert result == {"card": None, "quiet": {"reason": "evening_started"}}


def test_window_under_floor_reason_never_rounds_up(service, conn):
    insert_commitment(conn, effort_minutes=500)
    # 15 minutes until evening_start — below the 25-minute floor.
    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(19, 45))
    assert result == {"card": None, "quiet": {"reason": "window_under_floor"}}


def test_nothing_due_when_no_commitments_ever_existed(service, conn):
    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(10))
    assert result == {"card": None, "quiet": {"reason": "nothing_due"}}


def test_nothing_due_when_open_commitments_exist_but_none_closed_recently(service, conn):
    # A returning user with an open commitment that just isn't selectable
    # right now doesn't happen in this model (selection always picks the
    # highest scorer among any open commitment) — but a commitment closed
    # long ago, outside the current week, must not read as "everything
    # closed" this week.
    insert_commitment(
        conn, status="closed", closed_at=(TODAY - timedelta(days=30)).isoformat() + "T00:00:00Z"
    )
    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(10))
    assert result == {"card": None, "quiet": {"reason": "nothing_due"}}


def test_everything_closed_when_closed_this_week(service, conn):
    insert_commitment(
        conn, status="closed", closed_at=TODAY.isoformat() + "T09:00:00Z"
    )
    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(10))
    assert result == {"card": None, "quiet": {"reason": "everything_closed"}}


def test_cap_reached_checked_before_evening_started(service, conn):
    commitment_id = insert_commitment(conn)
    for _ in range(3):
        insert_card(conn, commitment_id=commitment_id, offer_date=TODAY, duration_minutes=30)

    # It's also past evening_start, which would independently be quiet too —
    # cap must win, per the confirmed precedence.
    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(22))
    assert result == {"card": None, "quiet": {"reason": "cap_reached"}}


def test_quiet_response_writes_a_quiet_render_row(service, conn):
    insert_commitment(conn)
    service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(21))

    rows = conn.execute(
        "SELECT reason, local_date FROM quiet_render WHERE user_id = ?", (USER_ID,)
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["reason"] == "evening_started"
    assert rows[0]["local_date"] == TODAY.isoformat()


# --- live card handling ---------------------------------------------------


def test_live_offered_card_returned_unchanged_when_still_fits(service, conn):
    insert_commitment(conn, effort_minutes=500)
    first = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(14))
    before_count = conn.execute("SELECT COUNT(*) AS n FROM card").fetchone()["n"]

    second = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(14, 5))

    assert second["card"]["id"] == first["card"]["id"]
    after_count = conn.execute("SELECT COUNT(*) AS n FROM card").fetchone()["n"]
    assert after_count == before_count


def test_stale_offered_card_closes_to_never_touched_and_reoffers(service, conn):
    insert_commitment(conn, title="the eval", effort_minutes=500)
    first = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(18))
    first_id = first["card"]["id"]

    # Time passes; the evening has now genuinely started, the earlier
    # offer no longer fits.
    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(21))

    stale_row = conn.execute("SELECT state, outcome FROM card WHERE id = ?", (first_id,)).fetchone()
    assert stale_row["state"] == "resolved"
    assert stale_row["outcome"] == "never_touched"
    assert result == {"card": None, "quiet": {"reason": "evening_started"}}


def test_started_card_is_returned_regardless_of_the_clock(service, conn):
    insert_commitment(conn, title="the eval", effort_minutes=500)
    first = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(14))
    conn.execute(
        "UPDATE card SET state = 'started', started_at = ? WHERE id = ?",
        (at(14, 5).isoformat(), first["card"]["id"]),
    )
    conn.commit()

    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(23))

    assert result["card"]["id"] == first["card"]["id"]
    assert result["quiet"] is None


# --- re-offer after a decline ----------------------------------------------


def test_reoffer_halves_the_declined_duration(service, conn):
    # Exercises the halving arithmetic on its own terms. Note: with the
    # week-one anchor fixed at 45 (SLICE_STARTING_ANCHOR_MINUTES), a *fresh*
    # offer can never actually reach 60 — this fixture stands in for a prior
    # offer regardless of how it was sized, purely to prove 60 -> 30. In
    # practice, given anchor=45 and floor=25, 45 // 2 = 22 already fails the
    # floor, so real re-offers exhaust after exactly one decline; a second,
    # successful halving is not reachable through a fresh anchor-sized offer.
    # Worth knowing: "continues down on repeated declines" only bites when
    # the original offer was smaller than 50 minutes to start with.
    commitment_id = insert_commitment(conn, title="the eval", effort_minutes=500)
    insert_card(conn, commitment_id=commitment_id, offer_date=TODAY, duration_minutes=60, outcome="not_now")

    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(14))

    assert result["card"]["duration_minutes"] == 30


def test_reoffer_below_floor_yields_after_not_now_per_ac_card_12(service, conn):
    commitment_id = insert_commitment(conn, title="the eval", effort_minutes=500)
    insert_card(conn, commitment_id=commitment_id, offer_date=TODAY, duration_minutes=40, outcome="not_now")
    # 40 // 2 = 20, below the 25-minute floor.

    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(14))

    assert result == {"card": None, "quiet": {"reason": "after_not_now"}}


def test_reoffer_does_not_cycle_to_a_different_commitment(service, conn):
    declined_id = insert_commitment(conn, title="declined", stakes="high", effort_minutes=1000)
    insert_card(conn, commitment_id=declined_id, offer_date=TODAY, duration_minutes=40, outcome="not_now")
    # A second, lower-scoring commitment exists and could theoretically be
    # offered instead — decisions.md §4 rejects that cycling.
    insert_commitment(conn, title="other", stakes="ordinary", effort_minutes=60)

    result = service.get_or_offer(USER_ID, TIMEZONE, EVENING_START, today=TODAY, now=at(14))

    assert result == {"card": None, "quiet": {"reason": "after_not_now"}}


def test_no_model_dependency_in_cards_module():
    import app.cards as cards_module

    source = open(cards_module.__file__).read().lower()
    for forbidden in ("openai", "anthropic", "requests", "httpx", "aiohttp"):
        assert forbidden not in source
