import dataclasses
import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.db import SCHEMA
from app.selection import SelectionResult, select_commitment

USER_ID = "u_test"
TODAY = date(2026, 9, 20)


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    connection.execute(
        "INSERT INTO user (id, timezone, evening_start, created_at) VALUES (?, ?, ?, ?)",
        (USER_ID, "UTC", "20:00", "2026-01-01T00:00:00Z"),
    )
    connection.commit()
    yield connection
    connection.close()


def insert_commitment(
    conn,
    *,
    title,
    stakes,
    deadline,
    effort_minutes,
    banked_effort_minutes=0,
    status="open",
):
    commitment_id = f"cm_{uuid.uuid4().hex}"
    conn.execute(
        """
        INSERT INTO commitment (
            id, user_id, title, category, stakes, deadline,
            effort_minutes, banked_effort_minutes, status, source, created_at
        ) VALUES (?, ?, ?, 'build', ?, ?, ?, ?, ?, 'manual', ?)
        """,
        (
            commitment_id,
            USER_ID,
            title,
            stakes,
            deadline.isoformat(),
            effort_minutes,
            banked_effort_minutes,
            status,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    return commitment_id


def test_worked_example_fixture_eval_wins(conn):
    # spec/spec.md §7.1
    eval_id = insert_commitment(
        conn, title="eval", stakes="high",
        deadline=TODAY + timedelta(days=2), effort_minutes=240,
    )
    insert_commitment(
        conn, title="reading", stakes="ordinary",
        deadline=TODAY + timedelta(days=1), effort_minutes=60,
    )
    insert_commitment(
        conn, title="build", stakes="ordinary",
        deadline=TODAY + timedelta(days=9), effort_minutes=300,
    )

    result = select_commitment(conn, USER_ID, "UTC", today=TODAY)

    # spec/spec.md D1 — durations are stored in minutes throughout, not the
    # hours used in the worked example's table; ordering is scale-invariant,
    # so 240min/2days * 2 = 240 here where the hours-based table reads 4.0.
    assert result.commitment_id == eval_id
    assert result.score == pytest.approx(240.0)


def test_past_deadline_is_expired_and_excluded(conn):
    # OPEN-2, resolved: past deadlines fall out of scoring entirely.
    expired_id = insert_commitment(
        conn, title="overdue", stakes="high",
        deadline=TODAY - timedelta(days=1), effort_minutes=999,
    )
    live_id = insert_commitment(
        conn, title="alive", stakes="ordinary",
        deadline=TODAY + timedelta(days=5), effort_minutes=50,
    )

    result = select_commitment(conn, USER_ID, "UTC", today=TODAY)

    assert result.commitment_id == live_id

    row = conn.execute(
        "SELECT status, expired_at FROM commitment WHERE id = ?", (expired_id,)
    ).fetchone()
    assert row["status"] == "expired"
    assert row["expired_at"] is not None


def test_only_expired_commitment_yields_no_selection(conn):
    insert_commitment(
        conn, title="overdue", stakes="high",
        deadline=TODAY - timedelta(days=1), effort_minutes=999,
    )

    assert select_commitment(conn, USER_ID, "UTC", today=TODAY) is None


def test_deadline_today_is_not_expired_and_scores_without_division_by_zero(conn):
    due_today_id = insert_commitment(
        conn, title="due today", stakes="ordinary",
        deadline=TODAY, effort_minutes=100,
    )
    insert_commitment(
        conn, title="due later", stakes="ordinary",
        deadline=TODAY + timedelta(days=10), effort_minutes=100,
    )

    result = select_commitment(conn, USER_ID, "UTC", today=TODAY)

    assert result.commitment_id == due_today_id
    row = conn.execute(
        "SELECT status FROM commitment WHERE id = ?", (due_today_id,)
    ).fetchone()
    assert row["status"] == "open"


def test_closed_commitments_are_not_candidates(conn):
    insert_commitment(
        conn, title="closed", stakes="high",
        deadline=TODAY + timedelta(days=1), effort_minutes=500,
        status="closed",
    )

    assert select_commitment(conn, USER_ID, "UTC", today=TODAY) is None


def test_selection_result_exposes_no_effort_or_banked_figure():
    # decisions.md §1, L4 — asserted as a test, not left as an intention.
    field_names = {f.name for f in dataclasses.fields(SelectionResult)}
    assert field_names == {"commitment_id", "score"}


def test_no_model_dependency_in_selection_module():
    # decisions.md §2 / spec.md G4 — no LLM anywhere in the selection path.
    import app.selection as selection_module

    source = open(selection_module.__file__).read().lower()
    for forbidden in ("openai", "anthropic", "requests", "httpx", "aiohttp"):
        assert forbidden not in source
