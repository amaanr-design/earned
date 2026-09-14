# Earned — Specification

**Status:** Phase 1 output. Companion document: `spec/api.md`.
**Sources, in precedence order:** `decisions.md` → `copy-spec.md` → `phased-development-plan.md` → `blueprint.md`.

> **What this document is.** A transcription of decisions already made, into the
> shapes a build needs: tables, fields, constants, state machines. It contains no
> new design. Where the locked documents settle something, this document restates
> it and cites the section. Where they do not, it says **OPEN** and stops.
>
> **What this document is not.** It does not resolve open items, and it does not
> quietly pick a value to keep a paragraph tidy. Several open items are unset on
> purpose (`decisions.md` §7, `copy-spec.md` §12); a spec that guessed them would
> destroy the reason they were left open.

**Reading the markers:**

| Marker | Meaning |
|---|---|
| **[LOCKED]** | Restated from a source document. Cited. Do not change here — change the source. |
| **[DERIVED]** | Forced by a locked decision but not written down in those words. Listed in full in §14 so every one is auditable. |
| **[OPEN]** | Genuinely unsettled. Listed in §15. Do not resolve by guessing. |

---

## 1. Scope of this spec

**In:** the week-one loop — Sunday intake, one rule-selected card, start / not-now
/ done, the pre-commit, the receipt. SQLite, single user, no auth, no push, no
learning. (`blueprint.md` §14, `phased-development-plan.md` Phase 2.)

**Schema-only, feature deferred:** `user_id` on every row (`decisions.md` §6),
`target_count` and recurrence for counted commitments (`decisions.md` §6), lint
flag rows and quiet-reason render counts (`copy-spec.md` §2, §9).

**Out entirely:** push, heartbeat, calendar OAuth, `user.md` profile, weekly
pattern, learning and calibration, agentic intake, auth. These have Phase 4+
homes in the plan and no fields in week one beyond those named above.

---

## 2. Units, time and identity

| Rule | Value | Source |
|---|---|---|
| Effort and slice durations | **integer minutes**, everywhere, including commitment totals | **[DERIVED]** — sources use hours for effort ("6h", "2.25h") and minutes for slices; one unit is required for arithmetic. Minutes is the finer of the two. |
| Timestamps | UTC, ISO-8601, stored as TEXT | **[DERIVED]** |
| Dates and day arithmetic | the **user's** local timezone, from `user.timezone` | **[LOCKED]** `decisions.md` §6 (timezone field on user) |
| The day boundary | **the rollover hour**, not midnight — see §9.3 | **[DERIVED]**, and see OPEN-8 |
| Current user in week one | one row, id supplied by config (`EARNED_USER_ID`) | **[LOCKED]** `decisions.md` §6 — "week one has one user; hardcode which one" |

Every query filters by `user_id`. No exceptions, including week one, including
the single-user endpoints. That is the entire point of doing it now
(`decisions.md` §6).

---

## 3. Constants

Single module, imported everywhere, never re-typed inline. Values marked OPEN
must be represented as named constants even while unset, so that setting them
later is a one-line change and so that grep finds every use.

| Constant | Value | Source |
|---|---|---|
| `SLICE_FLOOR_MINUTES` | **25** | `decisions.md` §3 |
| `SLICE_CEILING_MINUTES` | **120** | `decisions.md` §3 |
| `DAILY_CARD_CAP` | **3** | `decisions.md` §3 |
| `STAKES_MULTIPLIER` | `high: 2`, `ordinary: 1` | `decisions.md` §2 |
| `COPY_TIMEOUT_SECONDS` | **3** | `copy-spec.md` §3 |
| `ROLLOVER_HOUR` | **4** (local) | `decisions.md` §5 — stated as "~4am, technical, never seen" |
| `CATEGORIES` | `coursework`, `marc_lessons`, `build` | `decisions.md` §1 — closed enum, exactly three |
| `STAKES` | `high`, `ordinary` | `decisions.md` §1 — exactly two |
| `DEADLINE_CLAUSE_WINDOW_N` | **OPEN-3** | `copy-spec.md` §3, §12 |
| `NEGLECT_MULTIPLIER` | **OPEN-1** — not implemented in week one | `decisions.md` §2 |

`decisions.md` §3 explicitly caps the day "not because 4 is wrong" — the cap is
an observation instrument. It is a constant so it can be moved after watching,
not a hardcoded 3 in a query.

---

## 4. Entities

### 4.1 The distinction that generates everything else

A **commitment** is a thing you have said you will do, carrying a **total effort
estimate**. A **card** is a time-bounded slice of one commitment, offered on a
given day. Six hours of eval does not arrive as one card. **[LOCKED]**
`decisions.md` §1.

Consequences that the schema must hold:

- Effort lives on the commitment; duration lives on the card.
- Completion of a card is not completion of a commitment. Two different taps
  (§4.2).
- A card is a row, written at the moment it is offered — not a computed view
  (§8.1).

### 4.2 The two taps **[LOCKED]** `decisions.md` §1

| Tap | Meaning | Effect |
|---|---|---|
| **Tap A** | "that session happened" | Logs elapsed effort against the commitment. The normal tap, every session. |
| **Tap B** | "this whole thing is finished" | Rare. Closes the commitment. |

Tap B exists so the app never infers completion from effort exhaustion. Effort
estimates are wrong constantly, so that inference would be wrong constantly.

> **OPEN-9.** The week-one card carries three buttons — start / not-now / done
> (`blueprint.md` §14). Tap B has no surface named in any source document. Where
> it is tapped is unspecified.

### 4.3 Effort estimates **[LOCKED]** `decisions.md` §1

The parser proposes; the user may overwrite; **both values are stored**. The
delta is calibration signal. This forces two columns, not one:
`proposed_effort_minutes` (nullable — null for manually added commitments) and
`effort_minutes` (the value in force).

### 4.4 The forbidden number **[LOCKED]** `decisions.md` §1, design law L4

```
effort_remaining = effort_minutes − banked_effort_minutes
```

**Stored** — selection needs it. **Never returned by the API, never rendered in
any view, in any unit, in any costume.** Equally forbidden, because they are the
same number wearing different clothes (`decisions.md` §1):

- not-now tallies
- "leisure you'll lose" warnings
- weekly quotas that roll over when missed
- any progress bar, percentage, or "x of y" derived from the above

This is enforced as a **test**, not as a design intention — see §13. It is
exactly the kind of thing that reappears three weeks later as a helpful progress
indicator.

### 4.5 Deadlines **[LOCKED]** `decisions.md` §1

Every v1 commitment requires a deadline. The **column is nullable**; the
**intake flow must produce one** — the parser proposes it or the review screen
asks. A commitment with no deadline makes `urgency` undefined and would need a
second selector; building two selectors before one is proven is the failure mode.

### 4.6 Categories **[LOCKED]** `decisions.md` §1

Exactly three: `coursework`, `marc_lessons`, `build`. An unrecognised category
from the parser renders on the review screen **blank**, and the user assigns one
of the three before save. **No fallback bucket** — a fallback is a fourth
category through the back door. Therefore `category` is `NOT NULL` at the
database level and nullable only in the parser's proposal payload. **[DERIVED]**

### 4.7 Stakes **[LOCKED]** `decisions.md` §1

Exactly two: `high`, `ordinary`. Set at intake. Two, not three, because with
three everything lands in the middle. Stakes is stable and known when the plan is
written; urgency is computed and moves daily. They answer different questions.

### 4.8 Rewards **[LOCKED]** `decisions.md` §8, `copy-spec.md` §3

User-supplied, specific, typed at intake, **rendered verbatim**. The list splits
two ways and the split is load-bearing for copy: social rewards carry an
**external clock** ("the lads are on at 9" works because someone else set the
time); solo rewards do not; planned ones are known days ahead.

The reward slot fills **only if the reward is known and time-bound**
(`copy-spec.md` §3). Invented leisure is forbidden — it is a lie by the tenth use
and an unfalsifiable one.

The v1 list, as supplied (`decisions.md` §8) — the week-one seed and the copy
fixture set:

| Reward | Type | Timing |
|---|---|---|
| Pro Clubs with Michael & Braden | social, others present | external clock — they're on when they're on |
| Overwatch with Shaan (brother) | social, others present | external clock |
| Single player gaming night | solo | none |
| Movie night | either | planned |
| Night out with family or friends | social | planned, fixed |

The source types the list along **two axes** — what kind of thing it is, and
whether a clock outside the app governs it — and the schema keeps them as two
columns rather than flattening them, because the copy note turns on the second
one and the analysis lives in the first. **[DERIVED]**

> **OPEN-6.** Nothing in any source says *how a reward becomes tonight's reward*,
> or where the "at 9" in *"then Pro Clubs with Michael and Braden at 9"* comes
> from. The reward list is static; the sentence needs a time and a reason to
> believe it applies to this evening. This is not cosmetic: `copy-spec.md` §3
> notes that if most cards name no reward, the month-long eval measures a to-do
> app and a flat result would not mean the bet failed — it would mean the bet was
> never on screen.

---

## 5. Data model

Field-by-field. Types are SQLite. "Req" = required at write time.

### 5.1 `user`

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK | ✓ | UUID |
| `timezone` | TEXT | ✓ | IANA name. All day arithmetic uses it. `decisions.md` §6 |
| `evening_start` | TEXT | ✓ | `HH:MM` local. The only time boundary the app has. `decisions.md` §3 |
| `created_at` | TEXT | ✓ | |

Out of week one by explicit decision: signup, login, password reset, email
verification, sessions (`decisions.md` §6).

### 5.2 `commitment`

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK | ✓ | |
| `user_id` | TEXT FK | ✓ | |
| `title` | TEXT | ✓ | **Verbatim in copy.** Never reworded by the copy model (`copy-spec.md` §3) |
| `category` | TEXT | ✓ | One of three. No fallback |
| `stakes` | TEXT | ✓ | `high` / `ordinary` |
| `deadline` | TEXT | — | Local date `YYYY-MM-DD`. Nullable column, required by the flow (§4.5) |
| `effort_minutes` | INTEGER | ✓ | Total effort in force |
| `proposed_effort_minutes` | INTEGER | — | The parser's guess. Null when manually added. Kept as calibration signal (§4.3) |
| `banked_effort_minutes` | INTEGER | ✓ | Default 0. Sum of banked session durations |
| `effort_remaining_minutes` | INTEGER | ✓ | **GENERATED, STORED.** `effort_minutes − banked_effort_minutes`. **Never leaves the backend** (§4.4) |
| `status` | TEXT | ✓ | `open` / `closed` / `expired` — §8.4 |
| `closed_at` | TEXT | — | Set by Tap B |
| `expired_at` | TEXT | — | Set at the rollover after the deadline passes |
| `target_count` | INTEGER | — | **Reserved.** Counted commitments. Null in week one (`decisions.md` §6) |
| `completed_count` | INTEGER | — | **Reserved.** Null in week one |
| `recurrence` | TEXT | — | **Reserved.** Shape deliberately unspecified — see OPEN-10 |
| `source` | TEXT | ✓ | `parsed` / `manual` — which path it entered by |
| `created_at` | TEXT | ✓ | |

Generating `effort_remaining_minutes` rather than maintaining it by hand is
**[DERIVED]**: `decisions.md` §1 requires it stored, and a generated column
cannot drift from its inputs.

**Counted-commitment guards, in words, because they must survive contact with a
future implementer** (`decisions.md` §6):

1. **The week resets clean.** Missing 3 does not mean 4 next week.
2. **2 of 3 is not a failure state.** It is two sessions that happened. Nothing
   on screen mourns the third.

A weekly target that can be missed is a streak wearing a costume, and streaks are
the named delete trigger (L4).

### 5.3 `reward`

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK | ✓ | |
| `user_id` | TEXT FK | ✓ | |
| `label` | TEXT | ✓ | **Verbatim.** "Pro Clubs with Michael & Braden" — not "the lads" |
| `kind` | TEXT | ✓ | `social` / `solo` / `either` — the Type column of `decisions.md` §8 |
| `timing` | TEXT | ✓ | `external_clock` / `planned` / `none` — the Time-bound column. Only the first two may fill the slot |
| `usual_time` | TEXT | — | `HH:MM`. See OPEN-6 — how this reaches a given card is unspecified |
| `created_at` | TEXT | ✓ | |

### 5.4 `card`

The central table. Written **when offered** (§8.1).

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK | ✓ | |
| `user_id` | TEXT FK | ✓ | |
| `commitment_id` | TEXT FK | ✓ | |
| `offered_at` | TEXT | ✓ | |
| `offer_date` | TEXT | ✓ | Local day (rollover-based, §9.3). Indexed — the daily cap and the receipt both count on it |
| `duration_minutes` | INTEGER | ✓ | The offered slice |
| `score_at_offer` | REAL | ✓ | The selection score at the moment of offer. **[DERIVED]** — receipt line 17 names "today's highest-scoring card that was offered and banked nothing" (`copy-spec.md` §7), which is unreadable unless the score is on the row |
| `window_minutes_at_offer` | INTEGER | ✓ | Minutes to `evening_start` when offered. Debugging and slice-sizing evidence |
| `copy_text` | TEXT | ✓ | The sentence, **written at card-write time and stored** (`copy-spec.md` §3) |
| `copy_source` | TEXT | ✓ | `model` / `fallback`. Feeds the fallback rate (`copy-spec.md` §9) |
| `slot_boundary` | INTEGER | ✓ | 0/1. Backend decision, once a day, first card only (`copy-spec.md` §3) |
| `slot_reward_id` | TEXT FK | — | Null when no reward slot |
| `slot_deadline_days` | INTEGER | — | Non-null only inside the OPEN-3 window |
| `state` | TEXT | ✓ | `offered` / `started` / `resolved` |
| `outcome` | TEXT | — | One of the five buckets (§8.3). Null while unresolved |
| `started_at` | TEXT | — | Set by Start |
| `precommit_minutes` | INTEGER | — | The user's own number, at Start (`copy-spec.md` §6) |
| `ended_at` | TEXT | — | Set by Tap A |
| `elapsed_minutes` | INTEGER | — | `ended_at − started_at`. **Real, never invented** (§8.3) |
| `resolution` | TEXT | — | `confirmed` / `denied` / `dismissed` — `abandoned_unknown` only (`copy-spec.md` §7) |
| `resolved_at` | TEXT | — | |

**Three numbers, not two** (`copy-spec.md` §6): `duration_minutes` (the app's
offer), `precommit_minutes` (yours), `elapsed_minutes` (the truth). Offered 45,
said 20, did 25 separates *the app sized it wrong* from *you stopped early*,
which are different corrections. All three columns are required for that, and
none may be back-filled from another.

### 5.5 `receipt`

The live receipt is computed. **The frozen receipt is a row** — the weekly
pattern reads five real receipts rather than re-narrating history, and Marc reads
the same sentence you did (`decisions.md` §5).

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK | ✓ | |
| `user_id` | TEXT FK | ✓ | |
| `evening_date` | TEXT | ✓ | The evening being recorded. Unique with `user_id` |
| `body_lines` | TEXT | ✓ | JSON array of rendered strings, one per banked session. **May be empty** — the zero day is not special-cased (`copy-spec.md` §7) |
| `sat_on_top_line` | TEXT | — | Line 17, if it fired |
| `expiry_lines` | TEXT | — | JSON array. Line 18. **Renders on zero days too** |
| `frozen_at` | TEXT | ✓ | |
| `earned_state` | TEXT | ✓ | `never_seen` / `seen_dismissed` / `answered` (`copy-spec.md` §8) |
| `earned_value` | INTEGER | — | 0/1, only when `answered` |
| `answered_at` | TEXT | — | When the answer was given — **not** the evening it describes |

`earned_state` is a **stored value in all three states**, never a null that looks
like a bug. Non-response on zero days is the highest-signal data in the product;
collapsing `seen_dismissed` into `never_seen` loses it completely
(`copy-spec.md` §8).

**Lag** (`answered_at − evening_date`) is derived at read, not stored. It exists
to tell you whether the primary outcome measure decays with recall
(`copy-spec.md` §8).

### 5.6 `lint_flag` — schema now, batch job later

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK | ✓ | |
| `user_id` | TEXT FK | ✓ | |
| `card_id` | TEXT FK | — | |
| `text` | TEXT | ✓ | The rendered line |
| `matched_words` | TEXT | ✓ | JSON array |
| `created_at` | TEXT | ✓ | |

Word list (`copy-spec.md` §2): `again · still · only · finally · at last · back
on it · as usual · managed to`.

**Advisory, never blocking.** Runs **outside the request path** — writes a row,
adds no latency, no cost, never blocks a render. **A flagged line that is correct
is the expected case, not a defect.**

### 5.7 `quiet_render` — schema now, weekly review later

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK | ✓ | |
| `user_id` | TEXT FK | ✓ | |
| `reason` | TEXT | ✓ | §10.1 enum |
| `rendered_at` | TEXT | ✓ | |
| `local_date` | TEXT | ✓ | |

The failure mode that cannot be caught in a review session is a line reading as
pointed on its twentieth appearance. It is not fixable by writing better
sentences; it is caught by counting (`copy-spec.md` §9).

---

## 6. SQLite DDL

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE user (
    id             TEXT PRIMARY KEY,
    timezone       TEXT NOT NULL,
    evening_start  TEXT NOT NULL,                      -- 'HH:MM' local
    created_at     TEXT NOT NULL
);

CREATE TABLE commitment (
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

CREATE INDEX idx_commitment_selection
    ON commitment(user_id, status, deadline);

CREATE TABLE reward (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES user(id),
    label         TEXT NOT NULL,                        -- verbatim in copy
    kind          TEXT NOT NULL CHECK (kind IN ('social','solo','either')),
    timing        TEXT NOT NULL
                  CHECK (timing IN ('external_clock','planned','none')),
    usual_time    TEXT,                                 -- 'HH:MM'
    created_at    TEXT NOT NULL
);

CREATE TABLE card (
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
    slot_reward_id          TEXT REFERENCES reward(id),
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

CREATE INDEX idx_card_day  ON card(user_id, offer_date);
CREATE INDEX idx_card_open ON card(user_id, state);

CREATE TABLE receipt (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES user(id),
    evening_date    TEXT NOT NULL,
    body_lines      TEXT NOT NULL DEFAULT '[]',         -- JSON array; empty is normal
    sat_on_top_line TEXT,
    expiry_lines    TEXT,                               -- JSON array
    frozen_at       TEXT NOT NULL,
    earned_state    TEXT NOT NULL DEFAULT 'never_seen'
                    CHECK (earned_state IN ('never_seen','seen_dismissed','answered')),
    earned_value    INTEGER CHECK (earned_value IS NULL OR earned_value IN (0,1)),
    answered_at     TEXT,
    UNIQUE (user_id, evening_date)
);

CREATE TABLE lint_flag (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES user(id),
    card_id       TEXT REFERENCES card(id),
    text          TEXT NOT NULL,
    matched_words TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE quiet_render (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES user(id),
    reason      TEXT NOT NULL
                CHECK (reason IN ('evening_started','window_under_floor',
                                  'everything_closed','nothing_due',
                                  'cap_reached','after_not_now')),
    rendered_at TEXT NOT NULL,
    local_date  TEXT NOT NULL
);
```

**Note on the `duration_minutes` CHECK.** The floor and ceiling are also
constants in application code (§3). The duplication is deliberate: the constraint
is the last line of defence if a future code path forgets, and a 15-minute card
on a six-hour eval is an insult that burns a card (`decisions.md` §3).

---

## 7. Selection

### 7.1 The algorithm **[LOCKED]** `decisions.md` §2

Fully deterministic. **No LLM anywhere in the selection path.** The AI writes the
sentence; it never picks the card.

```
urgency           = effort_remaining / days_remaining
stakes_multiplier = 2 if stakes == 'high' else 1
score             = urgency * stakes_multiplier
```

Highest score wins. Candidates are the user's commitments with `status = 'open'`.

**Worked example, reproduced as a test fixture** (`decisions.md` §2):

| Commitment | Effort left | Days left | Stakes | Score |
|---|---|---|---|---|
| Eval | 4h | 2 | high | 4.0 |
| Reading | 1h | 1 | ordinary | 1.0 |
| Build | 5h | 9 | ordinary | 0.55 |

Eval wins. (Effort in hours here matches the source table; the implementation
uses minutes throughout, and the ordering is scale-invariant.)

### 7.2 No deadline-day override **[LOCKED]** `decisions.md` §2

A thing due *today* can lose to a thing due tomorrow. Accepted deliberately: a
4-hour high-stakes eval due tomorrow is a bigger fire than a 1-hour ordinary
reading due tonight.

**Accepted consequence: a commitment can expire without the app ever having named
it.** This is not a bug. It is "one thing, not a list" plus "silence on failure"
working as designed. The receipt narrates it afterwards, which is where
consequence belongs.

Rejected, and to stay rejected: deadline-day queue-jumping; a card carrying a
tail mentioning a second item.

### 7.3 Starvation **[LOCKED]** `decisions.md` §2

Anything that loses today scores higher tomorrow, because `days_remaining`
shrinks on its own. Starvation is temporary by construction — **except** for
large commitments with distant deadlines, which lose to every small fire,
correctly, every day, until the deadline closes in and it is a scramble. That
reproduces failure mode 3 faithfully in software.

The agreed fix is a **neglect nudge**: days since last touched feeds the score as
a small multiplier.

> **OPEN-1.** The multiplier value is deliberately unset. **Do not guess it
> before the selector has run on real data.** For week one the multiplier is not
> implemented at all; the weekly pattern surfacing "the build hasn't been touched
> in three weeks" is sufficient and has no parameter to get wrong.

### 7.4 Pacing rate — display only **[LOCKED]** `decisions.md` §2

`effort_remaining / weeks_remaining`, computed fresh, **never stored**. Not a
quota, not an allotment, never accumulates. Skip a week and the number rises on
its own because reality got heavier — nothing was owed, nothing rolled over.

Feeds the weekly pattern (Phase 4), not week one.

**Rejected:** stored per-week allotments (an allotment you don't meet becomes a
debt, which compounds silently into an accusation) and a ramp that puts more
hours nearer the deadline (that encodes the failure mode as a feature).

### 7.5 Gaps in the selection maths

These are arithmetic edges the locked documents do not reach. Each one changes
which card gets offered, so none can be quietly defaulted.

> **OPEN-2 — `days_remaining` at or past the deadline.** `urgency =
> effort_remaining / days_remaining` divides by zero on the deadline day itself
> and goes negative after it. Both the definition of `days_remaining` (whole days?
> fractional? floor of one?) and the deadline-day behaviour are unspecified. This
> is the single highest-impact unset value in the selector: it decides what
> happens on precisely the days that matter most.

> **OPEN-4 — exhausted effort without Tap B.** A commitment whose
> `effort_remaining` reaches 0 scores 0 and will never be offered again — which
> is completion inferred from effort exhaustion, the exact inference Tap B exists
> to prevent (`decisions.md` §1). Whether `effort_remaining` clamps at a floor,
> whether banked may exceed total, and how such a commitment returns to
> contention are all unspecified.

> **OPEN-5 — ties.** Two commitments with equal scores have no defined order. A
> deterministic selector needs a total order or its tests are flaky by
> construction.

> **OPEN-11 — `done_no_start` and banked effort.** `done_no_start` records that a
> session happened but carries no real number (`decisions.md` §4). If it banks
> nothing, `effort_remaining` overstates the work left for every session done away
> from the app, which inflates urgency for exactly the commitments being worked on
> hardest.

---

## 8. Card lifecycle

### 8.1 Cards are persisted when offered **[LOCKED]** `decisions.md` §4

Not computed on read. **Critical:** if a card is only calculated when the page
opens, a card you never opened was never offered as far as the database is
concerned — and re-entry learning is built entirely on the record of things
offered and ignored.

> **OPEN-7 — what triggers an offer in week one.** The heartbeat is Phase 4 and
> there is no push. The only event available in week one is the user opening the
> app, which makes "offered" and "seen" the same moment and makes
> `never_touched` structurally rarer than the design assumes. Whether week one
> accepts that, or generates on some other trigger, is not settled anywhere.
> It is called out because it silently weakens the learning signal the persist-on-offer
> rule exists to protect. (The API shape for this is in `api.md` §3.)

### 8.2 Slice sizing **[LOCKED, with a gap]** `decisions.md` §3

Slices fit the current window, bounded: **floor 25 minutes** — below this the app
offers nothing; **ceiling 120 minutes**.

**Ceiling ≠ offer size.** Calibration shrinks *offers* toward what actually gets
finished (offer 120, consistently do 40 → start offering ~45). The 120 ceiling
stays as a hard cap for the rare genuinely clear afternoon.

> **OPEN-12 — the sizing function.** The bounds are locked; the function from
> (window, effort remaining, calibration history) to an offered slice is not
> written down. Week one also has no calibration history to shrink toward, so
> week one needs a starting rule that is not the calibration rule.

### 8.3 Outcome buckets **[LOCKED]** `decisions.md` §4

Every offered card lands in exactly one. Most are invisible to the user and
recorded anyway — **the silent ones are the primary learning signal.**

| Bucket | Meaning | Duration data |
|---|---|---|
| `never_touched` | Offered, no tap | none |
| `not_now` | Declined | none |
| `completed` | Start → Tap A | real start + end |
| `abandoned_unknown` | Started, never closed | resolved by asking |
| `done_no_start` | Tap A without start (work happened away from the app) | none |

**`abandoned_unknown` resolution:** leave the card open and ask **once**, next
time the app is opened. Resolution values `confirmed` / `denied` / `dismissed`
are recorded on the existing bucket, not as new buckets (`copy-spec.md` §7).

**Rejected: auto-close at midnight, and auto-close after the card's stated
length.** Both invent a number and feed it to the thing that is supposed to be
learning real durations. That poisons the calibration well quietly.

`done_no_start` and `dismissed` **cannot feed duration calibration** — there is
no real number in either. Any calibration query must exclude them explicitly, and
that exclusion is a test (§13).

**Staleness.** A card offered at 6pm is stale by 9pm **on the merits** — a
45-minute card does not fit an evening that has already started. The card
regenerates for the current moment; the 6pm card closes quietly into
`never_touched`. **No overdue indicator.** Same reason as no warnings: it is a
scold.

### 8.4 Commitment status transitions **[DERIVED]**

| From | To | Trigger |
|---|---|---|
| `open` | `closed` | Tap B |
| `open` | `expired` | the rollover following the deadline date |

Expired commitments are not selection candidates, and their expiry is what
receipt line 18 reads. Only the `open` → `closed` transition is stated outright
in the sources; `open` → `expired` is forced by line 18 needing something to
read.

### 8.5 Not-now behaviour **[LOCKED]** `decisions.md` §4

Declining does not end the day. The **same commitment** can return in a **smaller
slice** later — 90 minutes was too much at six; 20 at nine is a different offer,
not a repeat.

**Rejected:** cycling through other commitments looking for a yes (trains you to
decline until something easy appears); faster re-offers for urgent items
(nagging on a timer, which is what gets apps deleted).

Repeated not-nows **do** feed learning — but only into *how the app offers*
(smaller slices, earlier in the day). They must never surface as anything
resembling a tally of refusals. That is L4 in a new unit.

> **OPEN-13 — the re-offer rule.** How much smaller the re-offer is, and how long
> after the decline it may arrive, are both unspecified. With no minimum interval
> the next card can arrive immediately, which is the nagging the source explicitly
> rejects — so this gap has a direction, and week one needs some value.

### 8.6 The daily cap **[LOCKED, with a gap]** `decisions.md` §3

**3 cards/day.** "Not because 4 is wrong, but because the unseen failure mode is
the app being chatty on a good day and training you to stop looking. Cap it,
watch, adjust."

Cadence is **one card at a time, not one a day**: a new card comes when conditions
are right — enough window left for a real slice, and something worth surfacing.
Finish at 4pm with four hours before evening → another card. Finish at 7:40pm →
nothing; the window is under the floor and the app goes quiet for the night.

> **OPEN-8 — what counts against the cap, and against which day.** Whether a
> `not_now` card, a stale `never_touched` card, or a smaller re-offer of the same
> commitment each consume one of the three is unspecified — and so is whether
> "day" here means the rollover day (§2) or the calendar day. Three declines
> ending the day is a very different app from three *offers* ending it.

### 8.7 No warnings, ever **[LOCKED]** `decisions.md` §4

Explicitly rejected: *"decline this and your leisure goes down."* Three reasons,
all from the design laws:

1. **It isn't true.** The app has no authority over the evening (L1). The first
   night you decline and game until 1am anyway, the app has been caught bluffing.
2. **It's a scold.** Not-now is free — no guilt copy, no follow-up.
3. **It's the deficit column in a new unit.** Hours-you-owe becomes
   leisure-you'll-lose.

**Where the teeth actually live:** the receipt, narrated afterwards when nothing
can be interrupted, and humans — the aunt, Marc — via the weekly pattern (L6).

---

## 9. Copy generation

### 9.1 The skeleton **[LOCKED]** `copy-spec.md` §3

**Every slot's presence is decided deterministically. The copy model only fills
the slots it is handed.** The copy model never decides *whether* to mention the
reward, the boundary, or the deadline — it receives a filled struct and writes
around it. An empty slot cannot be re-filled by a chatty model.

| Slot | Source | Presence decided by |
|---|---|---|
| `duration` | selection + calibration | always present |
| `title` | commitment title, **verbatim** | always present |
| `reward` | reward list, **verbatim**, only if known and time-bound | backend |
| `boundary` | `evening_start` | backend — **once per day, first card** |
| `deadline` | deadline arithmetic | backend — only inside the window (OPEN-3) |

**Titles and rewards are verbatim.** Same discipline as no-LLM-in-selection: if
the copy layer can rename the work, a wrong card has no stack trace.

The **fallback template uses the same slots**, so a fallback render and a model
render name the thing identically. That is what makes them comparable in the
eval.

### 9.2 Generation timing **[LOCKED]** `copy-spec.md` §3

Copy is generated **at card-write time** and stored on the card row. Opening the
app is a database read.

There is **no read-time latency budget**, because nothing is being generated
while you look at it. What is needed instead is a **generation-time timeout**:
if the copy model has not returned within `COPY_TIMEOUT_SECONDS` (3), the card is
stored with the fallback template text, and that is what the card says —
**permanently**.

- No retry on read
- No text swapping under your eyes
- No spinner
- No dependency on the model being up at the moment you open the app

The timeout is watched through the **fallback rate**, not tuned by hand: a
fallback card is already a card judged acceptable — it is the baseline the model
has to beat.

**Model naming.** This document says **the copy model** and **the judge model**,
never a product name. The current binding lives in build config
(`copy-spec.md` preamble). See §16 for the correction this implies for ticket T4.

### 9.3 The rollover and the day **[DERIVED from]** `decisions.md` §5

`ROLLOVER_HOUR` (04:00 local) is the boundary for: freezing the receipt, expiring
commitments past their deadline, moving started-but-unclosed cards into
`abandoned_unknown`, and — see OPEN-8 — probably the daily cap. Only the receipt
freeze is stated outright; the others are derived from it, on the grounds that
two competing day boundaries in one app is a bug generator.

### 9.4 Boundary guards **[LOCKED]** `copy-spec.md` §3

**Once a day.** First card of the day gets `boundary: true`; later cards get
`false`. The copy model cannot know what it said this morning, so this is a
backend boolean, never a model judgment.

**Coordinating conjunctions only.** The boundary clause joins with `and`, or a
full stop. Never `then`, `once`, `after`, `when that's done`.

The asymmetry is deliberate: *"45 minutes on the eval, then Pro Clubs with
Michael and Braden at 9"* is safe with `then`, because that 9pm clock belongs to
Michael and Braden and runs whether the work happens or not. The same `then`
attached to the boundary is unsafe, because the app owns that field and the
sentence begins to read as ownership.

**Named drift target:** *"the evening's yours once this is done."* A conditional
is a gate, and L1 says the app has no gate to offer. **It will arrive looking
like a small improvement.**

**Reward slot, three states:** named reward (known and time-bound) · boundary
(`evening_start`, always true, always available) · empty. **Empty is normal on
later cards and forbidden on the first.**

### 9.5 The card sentences **[LOCKED]** `copy-spec.md` §4

The nine cases are the eval set for card copy and are not restated here — they
live in `copy-spec.md` §4 and are cited from `api.md` per endpoint. What the
build needs from them:

- Case 9 (fallback) renders `{duration} on {title}.` plus the boundary sentence
  when `slot_boundary` is set. **Built first** (`copy-spec.md` §11) — if the copy
  model cannot beat it, the API dependency has not earned its place.
- Case 8 (counted commitment) confirms the count is **absent from copy** though
  present in the model. Nothing mourns the third.

### 9.6 The two rules **[LOCKED]** `copy-spec.md` §1

**R1 — fact, not evaluation.** A line may state what is or what happened; it may
not evaluate it. R1 bans evaluating the person's performance; it does not ban
evaluating the night. *"Enjoy tonight"* passes.

**R2 — scope.** The card speaks only about the session in front of it; the
receipt only about the day that ended. **Neither may cite a prior card's outcome
as a reason for the present one.** R2 exists because *"No card tonight — you
skipped the eval earlier"* passes R1 cleanly and is exactly the sentence that
must never render. What makes it a scold is reach, not tone.

There is no third rule. A second-person ban was considered and rejected: it
targets the grammar scolds usually wear rather than the failure itself, and it
costs *"you've earned it"* — the thesis of the product in four words.

---

## 10. Quiet screens and the receipt

### 10.1 Quiet reasons **[LOCKED]** `decisions.md` §5, `copy-spec.md` §5

The server **always returns a reason** when there is no card. A blank screen is
indistinguishable from a broken app, and the reason field costs one string.

| Code | Reason | Sentence (exact, assertable) |
|---|---|---|
| `evening_started` | Evening already started | *The evening's already started.* |
| `window_under_floor` | Window shorter than the floor | *Not enough time for a proper go at anything.* |
| `everything_closed` | Everything closed | *That's everything closed. Enjoy tonight.* |
| `nothing_due` | Nothing due | *Nothing due tonight.* |
| `cap_reached` | Daily cap reached | *That's the day.* |
| `after_not_now` | After a not-now | *Nothing else right now.* |

**No rotation.** A fixed, small, auditable set — no variants, no rotation index,
no state. Brevity kills wallpaper, not variety; when a line goes stale the fix is
to rewrite it shorter, never to add alternates. A side benefit: the eval asserts
the exact strings.

Notes that must survive into the tests:

- `evening_started` and `window_under_floor` are **two states, not one**. The
  single original line was false at 4pm on a day full of meetings.
- `everything_closed` is the only line keeping a second clause, because *"enjoy
  tonight"* adds rather than restates, and it is the one night that earns a small
  congratulation.
- `cap_reached` **makes no claim about what got done.** The cap can be reached
  with three cards offered and all three declined. *"That's enough for today"* is
  the failing version.
- `after_not_now` **must not reuse the others.** Reusing the no-card line after a
  decline is a small dishonesty that reads as passive aggression, and it is
  operationally different: the same commitment can return in a smaller slice, so
  the day is not over. Hence *right now*, not *tonight*.

> **OPEN-14 — reason precedence.** More than one reason can be true at once
> (evening started *and* everything closed; cap reached *and* window under floor).
> No precedence order is written down, and the order decides which sentence a user
> actually sees.

### 10.2 Receipt timing **[LOCKED]** `decisions.md` §5

- **Available at the evening-start hour** — the same field as slice windowing
- **Recomputes live** while the day is still running; do a session at 9 and it
  updates
- **Freezes at the rollover hour** into a permanent record

Why not fully fresh: the copy model writes the sentence, so recomputing means a
model call every open — cost, latency, and *different words each time* about the
same evening, which undermines the one thing the receipt is for.

Evening-start is the right boundary, not midnight and not sleep: L2 says the app
speaks at the boundary before a session; the receipt is that boundary from the
other side.

**Accepted gap:** with no push the receipt must be opened deliberately, so it may
not be read until the next morning.

### 10.3 Receipt contents **[LOCKED]** `copy-spec.md` §7

**The body is a list, not a sentence.** Two sessions is two lines. One is one
line. Zero is no lines, same frame. **Nothing is special-cased.**

**A count preamble is forbidden.** *"Two sessions today:"* is a summary sentence,
and a zero day cannot have one — every candidate is a consolation.

Lines below the list:

| # | Case | Sentence |
|---|---|---|
| 17 | Evening sat on a live commitment | *Tonight sat on top of the reading, due Thursday.* |
| 18 | Commitment expired | *Nothing on the essay — the deadline was today.* |
| 20 | `abandoned_unknown` resolution | *You started the eval last night — did that happen?* |
| 21 | The earned question | *Did last night feel earned?* — yes · no · dismissible |

**Line 17 fires on exactly one condition:** it names the commitment from **today's
highest-scoring card that was offered and banked nothing**. Nothing else.

- No card offered today → no line
- Card offered and completed → nothing sat on top of it
- Declined at 90, re-offered at 20, completed → no line; effort was banked

A day-count cap was rejected in favour of this. "Scored meaningfully" becomes
"was actually offered", which is a fact rather than a parameter.

**Tense switches on freeze:** *tonight* on the live receipt, *last night* on the
frozen one.

**Line 17 and the L5 collision, resolved:** the receipt may state what happened
and what did not, but never a word that evaluates it. L5 bans verdicts, not
facts. *"Tonight sat on top of the reading, due today"* passes; the same sentence
with *"— again"* fails.

**The zero-day receipt (19)** is structurally identical to every other receipt,
with an empty list. No compensating line, no softening, no acknowledgement of the
emptiness. **An expiry line still renders** — it is a fact about a commitment, not
a characterisation of your day. **The layout does not collapse:** the empty list
keeps its space and the lines below keep their fixed position. If the layout
reflows so the expiry line floats to the top, the app has tidied the absence
away, and tidying an absence is a comment on it. **The gap is the point** — and
this is a layout assertion, not a note (§13).

**Recorded, not treated as a defect:** the first zero-day receipt will land hard.
That is the design working.

### 10.4 The `abandoned_unknown` ask **[LOCKED]** `copy-spec.md` §7

Asked **once**, on a screen deliberately opened, long after the session ended.
L2-safe. A genuine question with an unknown answer, which is the only reason it
is not a nag — **and why it must never be asked twice.**

**Dismissal closes the card.** One lost session beats a question that learns to
follow you.

### 10.5 The earned question **[LOCKED]** `copy-spec.md` §8

Asked **every day. Never suppressed.** Suppressing it on zero days biases the
primary outcome measure of the entire product toward good days.

Identical wording, identical position, whether the list above it has two rows or
none. On a zero day it is the last thing on a screen with nothing else on it.
**That is the design working as specified, and it will feel like more than it
is.**

**It lives on the frozen receipt, not the live one.** Asking *"did tonight feel
earned?"* at 8:01pm rates an evening one minute old. The question appears only on
the frozen receipt, on next open, about last night. The wording changes with the
timing.

Three states — `answered`, `seen_dismissed`, `never_seen` — mirroring the card
outcome buckets. Three columns — `evening_date`, `answered_at`, and lag derived
from the two.

---

## 11. Intake

### 11.1 Review before save **[LOCKED]** `decisions.md` §5

1. User pastes the week's plan
2. The parser returns structured commitments
3. Commitments render as **editable rows**
4. User corrects effort, dates, blank categories
5. Save writes to the database

**Nothing touches the database until approved.** This is where the effort-estimate
veto physically happens — it needs a screen to happen on. A junk parse under
save-first becomes live data to clean up.

Because both the proposal and the correction must be stored (§4.3), the parser's
proposed effort travels through the review screen in the client's payload and is
written at save time into `proposed_effort_minutes`. The parse call itself writes
nothing. **[DERIVED]**

### 11.2 Parser failure **[LOCKED]** `decisions.md` §5

Observed failure shapes to design for: merging two commitments into one;
resolving "Tuesday" to the wrong week, silently; inventing a category outside the
enum; guessing 4 hours for a 40-minute task; returning malformed JSON.

The first four are caught on the review screen. The last leaves nothing to
review — hence the **manual add-commitment form**: plain fields (title, category,
deadline, effort, stakes), **no AI anywhere near it**. It is a permanent floor
(week one has no auth and no push, so a total parse failure on the first Sunday
means an app with nothing in it) and it handles the thing that comes up on
Wednesday, which a Sunday paste cannot.

**Rejected: a raw-JSON editor.** Unusable on a phone, and it is the kind of
debugging tool that quietly stays in the product because it worked once.

To give "Tuesday" a chance of resolving correctly, the parse request carries the
user's current local date as a reference. **[DERIVED]**

---

## 12. Instrumentation **[LOCKED]** `copy-spec.md` §9

Schema in week one (§5.6, §5.7); the weekly review that reads it is later.

**Per-reason triggers** — one number across all reasons would be wrong, and only
three are bad news at all:

| Reason | Rough weekly trigger | What a high count means | Action |
|---|---|---|---|
| Evening already started | >10 | The card is not reaching you before evening | Not a copy problem — the evidence file for push |
| Window under floor | >5 | The floor or slice sizing is wrong for real days | Revisit the floor, not the sentence |
| Nothing due | >3 | Intake is thin | Check the intake, not the copy |
| Cap reached | >2 | **Good news** — three cards means real windows | None, unless paired with low completion |
| Everything closed | any | **Good news** | None |
| After a not-now | >5 | Declines are high; already feeds slice calibration | None. Copy unchanged |

**The wallpaper trigger:** any single reason firing more than about once a day
(>8 in a week) has become the app's default sentence. **The response is to
rewrite the line shorter. Never to add variants.**

**The two cross-cutting alarms:** quiet share of opens above 50% two weeks
running; opens per week falling 30%+ while the earned-rate is also falling.

**The engagement-metric guard, which is a build rule and not a note:**

> **Opens are never rendered alone.** The figure exists only as a pair with the
> earned-rate. A fall in opens with a steady earned-rate is recorded as
> **working, needs you less** — not as churn.

Forbidden responses, written down now so they arrive recognisable: increased push
frequency, reminders to open, streaks, anything that rewards opening. There is no
action that raises opens without breaking L1 or L2.

**Every number in this section is OPEN** (OPEN-15). They are named so they
function as triggers rather than statistics to read past — not because they are
right. The weekly review records whether a trigger fired *and whether it felt
correct*.

---

## 13. Guardrails — what must be a test

`blueprint.md` §13 and `decisions.md` §1 both insist these are assertions, not
intentions. Full per-endpoint criteria live in `api.md`; these are the
system-level ones.

| # | Assertion | Source |
|---|---|---|
| G1 | **No response body from any endpoint contains `effort_remaining`, `banked_effort_minutes`, or any value from which they can be subtracted out.** Asserted by walking serialised responses, not by reading route code | `decisions.md` §1, L4 |
| G2 | No rendered view contains an owed, missed, remaining, or "x of y" figure — including the counted-commitment views when they arrive | `blueprint.md` §13, `copy-spec.md` §10 |
| G3 | Card selection given a fixed state returns the fixed expected card. The §7.1 worked example is a fixture | `decisions.md` §2 |
| G4 | Selection makes **no model call**. Asserted by a stubbed client that fails the test if invoked | `decisions.md` §2, §8 |
| G5 | Copy is never generated on read. Opening a card issues **zero** model calls | `copy-spec.md` §3 |
| G6 | A copy-model timeout stores fallback text and `copy_source='fallback'`, and the text never changes afterwards | `copy-spec.md` §3 |
| G7 | `slot_boundary` is true for exactly one card per day — the first | `copy-spec.md` §3 |
| G8 | Titles and reward labels appear in `copy_text` **byte-identical** to their stored values | `copy-spec.md` §3 |
| G9 | Duration calibration queries exclude `done_no_start` and `dismissed` rows | `decisions.md` §4, `copy-spec.md` §7 |
| G10 | The `abandoned_unknown` question is served **once**; dismissal closes the card and it is never asked again | `copy-spec.md` §7 |
| G11 | The zero-day receipt returns the same structure as any other, with an empty list, and the layout does not reflow | `copy-spec.md` §7 |
| G12 | The earned question is present on every frozen receipt, including zero days | `copy-spec.md` §8 |
| G13 | Quiet-screen strings match §10.1 **exactly**, character for character | `copy-spec.md` §5 |
| G14 | No card is offered with `duration_minutes` outside 25–120 | `decisions.md` §3 |
| G15 | Every offered card resolves into exactly one outcome bucket; none stays null past the rollover except `abandoned_unknown` awaiting its ask | `decisions.md` §4 |

The eval set for card copy starts from `copy-spec.md` §10 — the rejected-variants
table is most of it already written, with the pass/fail verdict and the reason
attached to each line.

---

## 14. Derivations made in this document

Every place this spec put something in words the sources did not use, so each can
be checked rather than inherited.

| # | Derivation | Forced by |
|---|---|---|
| D1 | Effort and durations stored as integer minutes | Sources mix hours and minutes; arithmetic needs one unit |
| D2 | `effort_remaining_minutes` as a generated stored column | "must be stored" + a hand-maintained copy can drift |
| D3 | `category` NOT NULL in the database, nullable only in the parser proposal | "no fallback bucket" + "user assigns before save" |
| D4 | `score_at_offer` persisted on the card | Receipt line 17 reads "today's highest-scoring card that was offered" |
| D5 | `commitment.status = 'expired'` and `expired_at` | Receipt line 18 needs something to read |
| D6 | The rollover hour governs expiry and `abandoned_unknown` transitions, not just the receipt freeze | Two competing day boundaries in one app is a bug generator |
| D7 | Parse request carries the user's local reference date | The named parser failure "resolves Tuesday to the wrong week" |
| D8 | Pre-commit stored on the card row rather than a separate log | The three numbers describe one card |
| D9 | UTC storage, local-timezone arithmetic | `user.timezone` exists and every rule is stated in local terms |
| D10 | `reward.kind` and `reward.timing` as two columns rather than one | The source list is typed along two independent axes; the copy note turns on the second and would be lost if they were flattened |

---

## 15. Open items

Carried forward and newly surfaced. **Nothing in this table was decided by this
document.** Items 1, 3, 15 and 16 were left open deliberately by the source
documents; the rest are gaps this transcription hit.

| # | Item | Blocks | Status |
|---|---|---|---|
| **OPEN-1** | Neglect-nudge multiplier value | Selector refinement, not week one | Deliberately unset (`decisions.md` §7). Do not guess before the selector runs on real data |
| **OPEN-2** | `days_remaining` definition, and division by zero on the deadline day | **T3, week one** | Gap. Highest-impact unset value in the selector |
| **OPEN-3** | Deadline-clause window `N` | T4 | Deliberately unset (`copy-spec.md` §12). Placeholder during the build; one line of copy, not a data shape |
| **OPEN-4** | Commitment with `effort_remaining ≤ 0` and no Tap B | **T3, week one** | Gap. Currently reintroduces completion-by-exhaustion, which Tap B exists to prevent |
| **OPEN-5** | Tie-break for equal scores | **T3, week one** | Gap. A deterministic selector needs a total order |
| **OPEN-6** | How a reward attaches to tonight, and where its time comes from | **T4, week one** | Gap. Affects whether the central bet is on screen at all |
| **OPEN-7** | What triggers a card offer in week one, given no push and no heartbeat | **T3/T5, week one** | Gap. Weakens the persist-on-offer learning signal |
| **OPEN-8** | What counts against the 3/day cap, and which day boundary it uses | **T3, week one** | Gap |
| **OPEN-9** | Where Tap B is tapped | **T5, week one** | Gap. Two taps are specified; only three buttons exist |
| **OPEN-10** | `recurrence` column shape | Deferred with the feature | Reserved deliberately (`decisions.md` §6) |
| **OPEN-11** | Whether `done_no_start` banks effort | **T1/T3, week one** | Gap. Untracked, it inflates urgency on the hardest-worked commitments |
| **OPEN-12** | Slice-sizing function, and the week-one starting rule before calibration exists | **T3, week one** | Gap. Bounds are locked; the function is not |
| **OPEN-13** | Re-offer size reduction and minimum interval after a not-now | **T3, week one** | Gap with a direction — no interval means nagging, which is explicitly rejected |
| **OPEN-14** | Quiet-reason precedence when several are true | **T3/T5, week one** | Gap |
| **OPEN-15** | Quiet-reason trigger thresholds | Weekly review, later | Deliberately provisional (`copy-spec.md` §12) |
| **OPEN-16** | Instrumentation baseline start date | Later | Begins after the first full week without a code change; git says when |
| **OPEN-17** | Whether `effort_minutes` (total) may be returned alongside anything from which remaining is reconstructable | **T1/T5, week one** | Gap. See `api.md` §2 — the conservative reading is specced there and marked |
| **OPEN-18** | The real Tuesday | Everything | Still unset. The oldest open item in the project (`claude/handoff.md`) |
| **OPEN-19** | Whether the pre-commit is skippable | T5, week one | Gap. The column is nullable so a skip is representable; whether the UI offers one is unstated (`api.md` §5) |

**Thirteen of these block week-one code:** OPEN-2, 4, 5, 6, 7, 8, 9, 11, 12, 13,
14, 17, 19 — and five of them (2, 4, 5, 12, 13) land inside ticket T3 alone. That
is the real shape of the tickets session. T3 is not one ticket's worth of
decisions, and the four that are deliberately unset (1, 3, 15, 16) are not the
ones holding anything up.

---

## 16. Corrections to `phased-development-plan.md`

Two items in the plan predate the locked documents and will mislead a worker
reading the plan alone.

**T3 — card selection.** The plan describes the rule as *"nearest deadline × fits
window × category overdue"*, carried over from `blueprint.md` §7. **Superseded.**
The locked rule is `score = (effort_remaining / days_remaining) ×
stakes_multiplier` (`decisions.md` §2, §7.1 above). Category plays no part in
selection at all — categories describe what a thing is, stakes describe what it
costs to skip. Anything that reintroduces "category overdue" into the selector is
a regression to a rejected design.

**T4 — card copy.** The plan names **Flash**. `copy-spec.md` deliberately names no
product anywhere, saying only **the copy model** and **the judge model**, with the
binding recorded in build config — so that a rename, a version bump, or a change
of provider does not make the spec read as stale when nothing in it has changed.
The tier assignment in `blueprint.md` §12 stands; the product name does not belong
in a ticket.
