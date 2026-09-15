"""spec/spec.md §7 — the selection algorithm.

Fully deterministic. No model call anywhere in this module, ever
(decisions.md §2 — "the AI writes the sentence; it never picks the card";
spec.md G4). Nothing in here returns `effort_remaining` or
`banked_effort_minutes` — decisions.md §1, design law L4.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .constants import ROLLOVER_HOUR, STAKES_MULTIPLIER


@dataclass(frozen=True)
class SelectionResult:
    """What the selector is allowed to hand back. No effort or banked figure
    lives on this type on purpose — see the module docstring."""

    commitment_id: str
    score: float


def local_today(timezone: str, rollover_hour: int = ROLLOVER_HOUR) -> date:
    """spec/spec.md §9.3 — the day boundary is the rollover hour, not midnight."""
    now = datetime.now(ZoneInfo(timezone))
    if now.hour < rollover_hour:
        now -= timedelta(days=1)
    return now.date()


def _utc_now_iso() -> str:
    return datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds").replace("+00:00", "Z")


def select_commitment(
    conn: sqlite3.Connection,
    user_id: str,
    timezone: str,
    today: date | None = None,
) -> SelectionResult | None:
    """spec/spec.md §7.1.

    ```
    urgency           = effort_remaining / days_remaining
    stakes_multiplier = 2 if stakes == 'high' else 1
    score             = urgency * stakes_multiplier
    ```

    Highest score wins. Candidates are the user's commitments with
    `status = 'open'`.

    **OPEN-2, resolved (this session):** a commitment whose deadline has
    already passed is expired and falls out of scoring entirely — not a
    candidate, not a zero score, not clamped. Week one has no rollover job
    (OPEN-7 territory) to make that transition ahead of time, so it is made
    lazily here, on read: any open commitment past its deadline is flipped
    to `status='expired'` with `expired_at` set, then excluded, before
    scoring runs.

    The deadline day itself is not past — per spec.md §8.4 / D5, expiry
    happens at the rollover *following* the deadline date — so it is still a
    candidate. Scoring it would otherwise divide by zero; `days_remaining`
    is floored at 1 for that one day. This floor is a build-time necessity,
    not a re-opening of OPEN-2's remaining question (whole vs. fractional
    days elsewhere), which stays open.
    """
    if today is None:
        today = local_today(timezone)
    now_iso = _utc_now_iso()

    rows = conn.execute(
        """
        SELECT id, deadline, effort_remaining_minutes, stakes
        FROM commitment
        WHERE user_id = ? AND status = 'open'
        """,
        (user_id,),
    ).fetchall()

    candidates: list[tuple[float, str]] = []

    for row in rows:
        deadline = row["deadline"]
        if deadline is None:
            # decisions.md §1 — every v1 commitment requires a deadline via
            # the intake flow. A null one here is a data-integrity gap, not
            # a scoring case, so it is excluded rather than guessed at.
            continue

        days_until = (date.fromisoformat(deadline) - today).days

        if days_until < 0:
            conn.execute(
                "UPDATE commitment SET status = 'expired', expired_at = ? WHERE id = ?",
                (now_iso, row["id"]),
            )
            continue

        days_remaining = days_until if days_until > 0 else 1
        urgency = row["effort_remaining_minutes"] / days_remaining
        score = urgency * STAKES_MULTIPLIER[row["stakes"]]
        candidates.append((score, row["id"]))

    conn.commit()

    if not candidates:
        return None

    # Deterministic total order so tests are not flaky by construction
    # (OPEN-5). This does not resolve OPEN-5 — which commitment *should*
    # win a genuine tie is still an open design question; this only breaks
    # the tie the same way every time.
    best_score, best_id = max(candidates, key=lambda c: (c[0], c[1]))
    return SelectionResult(commitment_id=best_id, score=best_score)
