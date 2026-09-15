import sqlite3
from collections.abc import Iterator
from datetime import datetime, timezone

from .config import DATABASE_PATH, EARNED_USER_ID

SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    id             TEXT PRIMARY KEY,
    timezone       TEXT NOT NULL,
    evening_start  TEXT NOT NULL,                      -- 'HH:MM' local
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS commitment (
    id                       TEXT PRIMARY KEY,
    user_id                  TEXT NOT NULL REFERENCES user(id),
    title                    TEXT NOT NULL,
    category                 TEXT NOT NULL
                             CHECK (category IN ('coursework','marc_lessons','build')),
    stakes                   TEXT NOT NULL
                             CHECK (stakes IN ('high','ordinary')),
    deadline                 TEXT,                     -- 'YYYY-MM-DD' local; required by the flow
    effort_minutes           INTEGER NOT NULL CHECK (effort_minutes > 0),
    proposed_effort_minutes  INTEGER,                  -- parser's guess; NULL when manual
    banked_effort_minutes    INTEGER NOT NULL DEFAULT 0,
    effort_remaining_minutes INTEGER
                             GENERATED ALWAYS AS (effort_minutes - banked_effort_minutes) STORED,
    status                   TEXT NOT NULL DEFAULT 'open'
                             CHECK (status IN ('open','closed','expired')),
    closed_at                TEXT,
    expired_at               TEXT,
    target_count             INTEGER,                  -- reserved, NULL in week one
    completed_count          INTEGER,                  -- reserved, NULL in week one
    recurrence               TEXT,                     -- reserved, shape unspecified (OPEN-10)
    source                   TEXT NOT NULL
                             CHECK (source IN ('parsed','manual')),
    created_at               TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_commitment_selection
    ON commitment(user_id, status, deadline);

CREATE TABLE IF NOT EXISTS card (
    id                      TEXT PRIMARY KEY,
    user_id                 TEXT NOT NULL REFERENCES user(id),
    commitment_id           TEXT NOT NULL REFERENCES commitment(id),
    offered_at              TEXT NOT NULL,
    offer_date              TEXT NOT NULL,              -- rollover-based local day
    duration_minutes        INTEGER NOT NULL
                            CHECK (duration_minutes BETWEEN 25 AND 120),
    score_at_offer          REAL NOT NULL,
    window_minutes_at_offer INTEGER NOT NULL,
    copy_text               TEXT NOT NULL,
    copy_source             TEXT NOT NULL CHECK (copy_source IN ('model','fallback')),
    slot_boundary           INTEGER NOT NULL DEFAULT 0 CHECK (slot_boundary IN (0,1)),
    slot_reward_id          TEXT,                       -- reward table not built yet (OPEN-6 deferred)
    slot_deadline_days      INTEGER,
    state                   TEXT NOT NULL DEFAULT 'offered'
                            CHECK (state IN ('offered','started','resolved')),
    outcome                 TEXT
                            CHECK (outcome IS NULL OR outcome IN
                                ('never_touched','not_now','completed',
                                 'abandoned_unknown','done_no_start')),
    started_at              TEXT,
    precommit_minutes       INTEGER,
    ended_at                TEXT,
    elapsed_minutes         INTEGER,
    resolution              TEXT
                            CHECK (resolution IS NULL OR resolution IN
                                ('confirmed','denied','dismissed')),
    resolved_at             TEXT
);

CREATE INDEX IF NOT EXISTS idx_card_day  ON card(user_id, offer_date);
CREATE INDEX IF NOT EXISTS idx_card_open ON card(user_id, state);

CREATE TABLE IF NOT EXISTS quiet_render (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES user(id),
    reason      TEXT NOT NULL
                CHECK (reason IN ('evening_started','window_under_floor',
                                  'everything_closed','nothing_due',
                                  'cap_reached','after_not_now')),
    rendered_at TEXT NOT NULL,
    local_date  TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _ensure_default_user(conn)
    conn.commit()
    return conn


def _ensure_default_user(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT id FROM user WHERE id = ?", (EARNED_USER_ID,)
    ).fetchone()
    if row is not None:
        return
    conn.execute(
        "INSERT INTO user (id, timezone, evening_start, created_at) VALUES (?, ?, ?, ?)",
        (
            EARNED_USER_ID,
            "UTC",
            "20:00",
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        ),
    )


def make_connection_factory() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
