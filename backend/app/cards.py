"""spec/api.md §3 — GET /api/card.

Deterministic template copy only. No model call anywhere in this module —
same discipline as selection.py, and copy-spec.md §11's fallback-first build
order taken literally: this is the baseline the model has to beat, built
first and standing alone for now. `copy_source` is always 'fallback'.

Several decisions here resolve open items or fill gaps the locked documents
did not reach. Each is called out at the point it's made; the summary is in
`spec/spec.md` §7.5 / §10.1 / §15.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .constants import (
    DAILY_CARD_CAP,
    SLICE_CEILING_MINUTES,
    SLICE_FLOOR_MINUTES,
    SLICE_STARTING_ANCHOR_MINUTES,
)
from .selection import local_today, select_commitment


def _utc_now_iso() -> str:
    return datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds").replace("+00:00", "Z")


def _minutes_until_evening(
    today: date, evening_start: str, timezone_name: str, now: datetime
) -> float:
    hour, minute = (int(part) for part in evening_start.split(":"))
    evening_dt = datetime.combine(today, time(hour, minute), tzinfo=ZoneInfo(timezone_name))
    return (evening_dt - now).total_seconds() / 60


def _format_evening_hour(evening_start: str) -> str:
    hour, minute = (int(part) for part in evening_start.split(":"))
    period_hour = hour % 12 or 12
    if minute == 0:
        return str(period_hour)
    return f"{period_hour}:{minute:02d}"


def _render_fallback_copy(duration_minutes: int, title: str, boundary: bool, evening_start: str) -> str:
    text = f"{duration_minutes} minutes on {title}."
    if boundary:
        text += f" Evening starts at {_format_evening_hour(evening_start)}."
    return text


def _start_of_week(today: date) -> date:
    # Sunday-based week, matching decisions.md §5's Sunday intake. "Recently"
    # is explicitly an OPEN item (§15) — this picks the current week as the
    # default, on the user's plain local calendar date, not rollover-shifted.
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)


def _to_local_date(iso_timestamp: str, timezone_name: str) -> date:
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    return dt.astimezone(ZoneInfo(timezone_name)).date()


def _closed_this_week(conn: sqlite3.Connection, user_id: str, today: date, timezone_name: str) -> bool:
    """Resolves the everything_closed / nothing_due split (undocumented
    ambiguity, decided with the user this session): everything_closed fires
    only if a commitment was closed within the current week; otherwise, with
    no open commitments, it's nothing_due — including a returning user who
    never did intake, who should not be congratulated for an empty week."""
    week_start = _start_of_week(today)
    rows = conn.execute(
        "SELECT closed_at FROM commitment WHERE user_id = ? AND status = 'closed' AND closed_at IS NOT NULL",
        (user_id,),
    ).fetchall()
    return any(_to_local_date(row["closed_at"], timezone_name) >= week_start for row in rows)


def _count_cards_today(conn: sqlite3.Connection, user_id: str, today: date) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM card WHERE user_id = ? AND offer_date = ?",
        (user_id, today.isoformat()),
    ).fetchone()
    return row["n"]


def _latest_not_now(conn: sqlite3.Connection, commitment_id: str, today: date):
    return conn.execute(
        """
        SELECT duration_minutes FROM card
        WHERE commitment_id = ? AND offer_date = ? AND outcome = 'not_now'
        ORDER BY offered_at DESC LIMIT 1
        """,
        (commitment_id, today.isoformat()),
    ).fetchone()


def _serialize_card(row) -> dict:
    return {
        "id": row["id"],
        "commitment_id": row["commitment_id"],
        "title": row["title"],
        "duration_minutes": row["duration_minutes"],
        "copy_text": row["copy_text"],
        "state": row["state"],
        "offered_at": row["offered_at"],
    }


def _quiet(conn: sqlite3.Connection, user_id: str, today: date, reason: str) -> dict:
    # AC-CARD-13 — each quiet response writes one quiet_render row.
    conn.execute(
        "INSERT INTO quiet_render (id, user_id, reason, rendered_at, local_date) VALUES (?, ?, ?, ?, ?)",
        (f"qr_{uuid.uuid4().hex}", user_id, reason, _utc_now_iso(), today.isoformat()),
    )
    conn.commit()
    return {"card": None, "quiet": {"reason": reason}}


@dataclass
class CardService:
    conn: sqlite3.Connection

    def get_or_offer(
        self,
        user_id: str,
        timezone_name: str,
        evening_start: str,
        today: date | None = None,
        now: datetime | None = None,
    ) -> dict:
        conn = self.conn
        if now is None:
            now = datetime.now(ZoneInfo(timezone_name))
        if today is None:
            today = local_today(timezone_name)

        live = conn.execute(
            """
            SELECT card.*, commitment.title AS title
            FROM card JOIN commitment ON commitment.id = card.commitment_id
            WHERE card.user_id = ? AND card.offer_date = ? AND card.state IN ('offered','started')
            ORDER BY card.offered_at DESC LIMIT 1
            """,
            (user_id, today.isoformat()),
        ).fetchone()

        if live is not None:
            if live["state"] == "started":
                # Mid-session — never stale, regardless of the clock.
                return {"card": _serialize_card(live), "quiet": None}

            window = _minutes_until_evening(today, evening_start, timezone_name, now)
            if window > 0 and window >= live["duration_minutes"]:
                # AC-CARD-1 — still fits; return as-is, zero new writes.
                return {"card": _serialize_card(live), "quiet": None}

            # AC-CARD-11 — stale on the merits: closes quietly, never
            # surfaced as overdue. Falls through to offer a fresh card.
            conn.execute(
                "UPDATE card SET state = 'resolved', outcome = 'never_touched', resolved_at = ? WHERE id = ?",
                (_utc_now_iso(), live["id"]),
            )
            conn.commit()

        # OPEN-14, resolved: cap is checked before any time-window state.
        if _count_cards_today(conn, user_id, today) >= DAILY_CARD_CAP:
            return self._quiet(user_id, today, "cap_reached")

        window = _minutes_until_evening(today, evening_start, timezone_name, now)
        if window <= 0:
            return self._quiet(user_id, today, "evening_started")

        selection = select_commitment(conn, user_id, timezone_name, today=today)
        if selection is None:
            reason = (
                "everything_closed"
                if _closed_this_week(conn, user_id, today, timezone_name)
                else "nothing_due"
            )
            return self._quiet(user_id, today, reason)

        commitment = conn.execute(
            "SELECT title, effort_remaining_minutes FROM commitment WHERE id = ?",
            (selection.commitment_id,),
        ).fetchone()

        prior_decline = self._latest_not_now(selection.commitment_id, today)
        if prior_decline is not None:
            # OPEN-13, resolved: immediate re-offer, halved from the most
            # recently declined duration for this same commitment today.
            # No cycling to a different commitment on decline
            # (decisions.md §4) — if the halved slice doesn't clear the
            # floor, that's after_not_now, per AC-CARD-12, not a fresh
            # window_under_floor read.
            candidate = prior_decline["duration_minutes"] // 2
            if candidate < SLICE_FLOOR_MINUTES:
                return self._quiet(user_id, today, "after_not_now")
        else:
            # OPEN-12, resolved: week-one starting rule, no calibration
            # history yet. Anchored at 45 rather than the ceiling; never
            # rounded up to the floor.
            candidate = min(
                SLICE_STARTING_ANCHOR_MINUTES,
                int(window),
                commitment["effort_remaining_minutes"],
            )
            if candidate < SLICE_FLOOR_MINUTES:
                return self._quiet(user_id, today, "window_under_floor")

        duration_minutes = min(candidate, SLICE_CEILING_MINUTES)
        is_first_today = self._count_cards_today(user_id, today) == 0

        copy_text = _render_fallback_copy(
            duration_minutes, commitment["title"], is_first_today, evening_start
        )

        card_id = f"c_{uuid.uuid4().hex}"
        offered_at = _utc_now_iso()
        conn.execute(
            """
            INSERT INTO card (
                id, user_id, commitment_id, offered_at, offer_date,
                duration_minutes, score_at_offer, window_minutes_at_offer,
                copy_text, copy_source, slot_boundary, state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'fallback', ?, 'offered')
            """,
            (
                card_id,
                user_id,
                selection.commitment_id,
                offered_at,
                today.isoformat(),
                duration_minutes,
                selection.score,
                int(window),
                copy_text,
                1 if is_first_today else 0,
            ),
        )
        conn.commit()

        return {
            "card": {
                "id": card_id,
                "commitment_id": selection.commitment_id,
                "title": commitment["title"],
                "duration_minutes": duration_minutes,
                "copy_text": copy_text,
                "state": "offered",
                "offered_at": offered_at,
            },
            "quiet": None,
        }

    def _count_cards_today(self, user_id: str, today: date) -> int:
        return _count_cards_today(self.conn, user_id, today)

    def _latest_not_now(self, commitment_id: str, today: date):
        return _latest_not_now(self.conn, commitment_id, today)

    def _quiet(self, user_id: str, today: date, reason: str) -> dict:
        return _quiet(self.conn, user_id, today, reason)


def card_service_factory(svcs_container):
    conn = svcs_container.get(sqlite3.Connection)
    yield CardService(conn)
