# Earned — API Contract

**Status:** Phase 1 output. Companion document: `spec/spec.md`, which holds the
data model, the selection algorithm, the lifecycle and the constants this
document refers to by name.

**Scope:** the week-one loop only — Sunday intake, one rule-selected card, start
/ not-now / done, the pre-commit, the receipt. Endpoints that exist only for
later phases are listed unspecified in §17.

Markers are as in `spec.md`: **[LOCKED]** restated and cited, **[DERIVED]** forced
but not written in those words, **[OPEN]** genuinely unsettled and listed in
`spec.md` §15.

---

## 1. Conventions

| | |
|---|---|
| Base path | `/api` |
| Encoding | JSON, UTF-8 |
| Auth | **None in week one.** Every request acts as the configured user (`EARNED_USER_ID`). `decisions.md` §6 |
| Timestamps in and out | UTC, ISO-8601 |
| Dates in and out | `YYYY-MM-DD`, **user-local** |
| Durations | integer **minutes** (`spec.md` D1) |
| Unknown fields in a request body | rejected, 422 |

Every handler filters by `user_id` even though there is one user. Week one is
where that habit is established or lost (`decisions.md` §6).

### Error shape **[DERIVED]**

```json
{ "error": { "code": "commitment_not_found", "message": "…", "field": null } }
```

| Status | Used for |
|---|---|
| 400 | Malformed request |
| 404 | Unknown id, or an id belonging to another user (**not** 403 — do not confirm existence) |
| 409 | State conflict: starting a resolved card, closing a closed commitment, answering an already-answered question |
| 422 | Validation failure, including enum violations and out-of-range durations |
| 502 | Upstream model failure on parse (**never** on card copy — see §3) |

---

## 2. The forbidden number at the API boundary

**[LOCKED]** `decisions.md` §1, design law L4.

`effort_remaining` and `banked_effort_minutes` **never appear in any response
body**, in any unit, under any name, on any endpoint, including debug and
admin ones. This is asserted by walking serialised responses, not by reading
route code (`spec.md` G1).

Also forbidden in responses, as the same number in costume: not-now counts,
decline tallies, "sessions remaining", percentage complete, `x of y` progress,
and any "leisure at risk" figure.

**The conservative reading, taken here and marked:** `effort_minutes` — the total
the user typed or approved — is returned by the commitment endpoints (§10) and by
nothing else. It is not returned anywhere alongside a banked figure, because
returning both hands the client a subtraction and a progress bar is one commit
away.

> **OPEN-17.** Whether the total may be returned at all is not settled by any
> source. It is specced permissively here only on the commitment endpoints, where
> the user is editing the number they themselves supplied. If the answer turns out
> to be no, the change is a single serialiser field.

---

## 3. `GET /api/card`

The single most important endpoint. Returns the card, or a reason there isn't
one.

**This endpoint writes.** When conditions are right and no live card exists, it
selects, sizes, generates copy, and **persists a card row before responding**
(`decisions.md` §4 — cards are persisted when offered, not computed on read). A
`GET` with a side effect is unusual and is chosen over `POST /api/card/offer`
because the client's only interaction is "show me the card"; the naming is
`spec.md` **[DERIVED]**.

> **OPEN-7.** In week one, with no push and no heartbeat, an app open is the only
> event that can trigger an offer — which collapses "offered" and "seen" into one
> moment and makes `never_touched` structurally rare. The persist-on-offer rule
> exists to protect exactly that signal, so this is called out rather than papered
> over. It does not block the endpoint's shape.

### Response — card available (200)

```json
{
  "card": {
    "id": "c_01H…",
    "commitment_id": "cm_01H…",
    "title": "the eval",
    "duration_minutes": 45,
    "copy_text": "45 minutes on the eval. Evening starts at 8.",
    "state": "offered",
    "offered_at": "2026-08-20T17:12:04Z"
  },
  "quiet": null
}
```

`copy_text` is read from the row. **Nothing is generated during this request when
a live card already exists.**

### Response — no card (200, not 204)

```json
{
  "card": null,
  "quiet": { "reason": "everything_closed" }
}
```

`reason` is one of `evening_started`, `window_under_floor`, `everything_closed`,
`nothing_due`, `cap_reached`, `after_not_now` (`spec.md` §10.1).

**The server returns the reason; the client renders the sentence** — stated that
way in `decisions.md` §5 and `copy-spec.md` §5, so the strings live in a shared
client constant module and the eval asserts them there (`spec.md` G13). 200 with
a null card, never 204: a blank screen is indistinguishable from a broken app,
which is the whole argument for the reason field.

> **OPEN-14.** Several reasons can be true at once. No precedence is written
> down, and the order decides which sentence is seen.

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-CARD-1 | With a live unresolved card for today, the endpoint returns that same card row and issues **zero** model calls (`spec.md` G5) |
| AC-CARD-2 | With no live card and conditions right, a `card` row is written **before** the response is sent; the returned `id` exists in the database |
| AC-CARD-3 | The persisted row carries `score_at_offer`, `window_minutes_at_offer`, `copy_source` and `slot_boundary`, all non-null |
| AC-CARD-4 | Selection matches the `spec.md` §7.1 fixture exactly, given the fixture state |
| AC-CARD-5 | A stubbed model client that raises on invocation does not fail selection — the selector never calls it (`spec.md` G4) |
| AC-CARD-6 | A copy-model call exceeding `COPY_TIMEOUT_SECONDS` yields a stored card with fallback text and `copy_source='fallback'`, **200 not 502**, and the text is unchanged on every subsequent read (`spec.md` G6) |
| AC-CARD-7 | `duration_minutes` is always between 25 and 120 inclusive; a computed window below 25 produces `quiet.reason='window_under_floor'` and **no card row** |
| AC-CARD-8 | The first card of a day has `slot_boundary=1`; every later card that day has `slot_boundary=0` (`spec.md` G7) |
| AC-CARD-9 | `copy_text` contains the commitment title byte-identical to `commitment.title`, and the reward label byte-identical when the slot is filled (`spec.md` G8) |
| AC-CARD-10 | No response field, at any nesting depth, exposes remaining or banked effort (`spec.md` G1) |
| AC-CARD-11 | When a card offered earlier is stale on the merits, it closes to `never_touched` and a card for the current moment is offered; the stale row is untouched otherwise and no overdue flag appears in the response |
| AC-CARD-12 | The response after a `not_now` with nothing further to offer carries `reason='after_not_now'` and **never** one of the other five (`copy-spec.md` §5) |
| AC-CARD-13 | Each quiet response writes one `quiet_render` row with the matching reason |
| AC-CARD-14 | With every commitment closed, `reason='everything_closed'`; with none due, `nothing_due`. The two are never interchanged |

---

## 4. `POST /api/cards/{id}/start`

Records the Start tap and returns the pre-commit options.

**Request:** empty body.

**Response (200)**

```json
{
  "card_id": "c_01H…",
  "started_at": "2026-08-20T17:13:40Z",
  "precommit": {
    "prompt": "How long are you giving it?",
    "options_minutes": [30, 45, 60, 75]
  }
}
```

**Tap options are generated around the offered slice by the backend**, not chosen
by the copy model — same rule as every other slot (`copy-spec.md` §6).

**The wording is fixed and is not a model output.** *"How long are you giving
it?"* asks for a commitment without questioning one. *"How long are you actually
going for?"* and *"How long, really?"* both fail: they doubt the answer before it
is given (`copy-spec.md` §6).

> **OPEN-12** governed the option set as well as the slice, since the options are
> generated around a slice whose sizing function is unwritten.
>
> **OPEN-20 — the option-generation function itself. [RESOLVED.]** Neither
> source named a rule for turning an offered duration into a set of tappable
> options, and this doc's own illustrative example (`[20, 30, 45, 60]` for a
> 45-minute offer) silently violated its own AC-START-5, since 20 falls under
> the 25-minute offer floor. **Decision: `{offered-15, offered, offered+15,
> offered+30}`, deduped, clamped to `[10, 120]`** — see the amended AC-START-5
> above. Confirmed with the user 2026-09.

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-START-1 | `started_at` is written to the card row and `state` becomes `started` |
| AC-START-2 | Starting a card already in `started` or `resolved` returns 409 and mutates nothing |
| AC-START-3 | The prompt string equals `copy-spec.md` case 15 exactly |
| AC-START-4 | Options are produced by the backend; a stubbed model client is never invoked |
| AC-START-5 | **Amended, OPEN-20.** Every option is between 10 and 120 inclusive — not 25. 25 is the minimum the app will *offer*, not the minimum the user may *commit* to; clamping precommit options to the offer floor would make an honest low estimate unrepresentable and corrupt the estimate-vs-actual data (`copy-spec.md` §6's "three numbers, not two"). Options are `{offered-15, offered, offered+15, offered+30}`, deduped, clamped to `[10, 120]`. Confirmed with the user 2026-09; implemented in `backend/app/cards.py` |

---

## 5. `POST /api/cards/{id}/precommit`

Records the user's own number. Separate from Start so that `started_at` is the
Start tap and not the moment a number was chosen — the elapsed measurement
depends on it.

**Request**

```json
{ "minutes": 20 }
```

**Response (200):** `{ "card_id": "…", "precommit_minutes": 20 }`

**Three numbers, not two** (`copy-spec.md` §6): the offer, the pre-commit, the
elapsed. Offered 45, said 20, did 25 separates *the app sized it wrong* from *you
stopped early*. None of the three may be back-filled from another.

**The pre-commit estimates the work, not the leisure.** A work estimate has a
measurable actual; a leisure estimate has none, and week one has no mechanism to
ask when a gaming session ended (`copy-spec.md` §6, resolving the CUJ-3 divergence
recorded in `blueprint.md`'s precedence header).

> **OPEN-19.** Whether the pre-commit is skippable is not stated. The column is
> nullable, so a skip is representable; whether the UI offers one is unsettled.

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-PRE-1 | `precommit_minutes` is stored and never overwrites `duration_minutes` |
| AC-PRE-2 | A pre-commit on a card that has not been started returns 409 |
| AC-PRE-3 | A second pre-commit on the same card returns 409 |
| AC-PRE-4 | The stored value may differ from every offered option without error — it is the user's number |

---

## 6. `POST /api/cards/{id}/not-now`

**Request:** empty body. **Response (200):** `{ "card_id": "…", "outcome": "not_now" }`

**Declining does not end the day.** The same commitment can return in a smaller
slice later (`decisions.md` §4). The response carries **no** follow-up copy, no
acknowledgement token, and no count. *"Okay. Nothing else right now."* was cut
because the token registers the decline, and registering is one step from noting
(`copy-spec.md` §5).

> **OPEN-13.** How much smaller the re-offer is, and the minimum interval before
> one may arrive, are unspecified. With no interval the next card can arrive
> immediately, which is the nagging-on-a-timer the source explicitly rejects.

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-NOTNOW-1 | `outcome='not_now'`, `state='resolved'`; no duration is written |
| AC-NOTNOW-2 | The response body contains no message, no count, and no tally of any kind |
| AC-NOTNOW-3 | The commitment remains `open` and remains a selection candidate |
| AC-NOTNOW-4 | The immediately following `GET /api/card` never returns a card for a *different* commitment chosen because this one was declined (`decisions.md` §4 — no cycling for a yes) |
| AC-NOTNOW-5 | No response anywhere exposes how many times a commitment has been declined |

---

## 7. `POST /api/cards/{id}/done` — Tap A

Handles both shapes of Tap A: after a Start, and without one.

**Request:** empty body.

**Response (200)**

```json
{ "card_id": "c_01H…", "outcome": "completed", "elapsed_minutes": 25 }
```

Behaviour **[LOCKED]** `decisions.md` §4:

| Card state | Outcome | Duration |
|---|---|---|
| `started` | `completed` | `elapsed_minutes = ended_at − started_at`, **real** |
| `offered` | `done_no_start` | none — work happened away from the app |

**No duration is ever invented.** Auto-close at midnight and auto-close after the
card's stated length were both rejected: they feed a made-up number to the thing
that is supposed to be learning real durations, which poisons the calibration
well quietly.

> **OPEN-11.** Whether `done_no_start` banks any effort against the commitment is
> unspecified. If it banks nothing, `effort_remaining` overstates the work left
> for every session done away from the app.

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-DONE-1 | From `started`: `outcome='completed'`, `elapsed_minutes` computed from real timestamps, `commitment.banked_effort_minutes` increased by that amount |
| AC-DONE-2 | From `offered`: `outcome='done_no_start'`, `elapsed_minutes` **null** |
| AC-DONE-3 | No code path writes `elapsed_minutes` from `duration_minutes` or `precommit_minutes` |
| AC-DONE-4 | Tap A does not close the commitment — `status` stays `open` regardless of the resulting remaining effort (`decisions.md` §1) |
| AC-DONE-5 | The response contains no remaining, banked, or progress figure |
| AC-DONE-6 | Calibration queries built on this data exclude `done_no_start` rows (`spec.md` G9) |

---

## 8. `POST /api/commitments/{id}/close` — Tap B

**Request:** empty body. **Response (200):** `{ "commitment_id": "…", "status": "closed" }`

Tap B is the only thing that closes a commitment. The app never infers completion
from effort exhaustion, because effort estimates are wrong constantly and that
inference would be wrong constantly (`decisions.md` §1).

> **OPEN-9.** Where this is tapped is unspecified. The week-one card carries three
> buttons — start / not-now / done (`blueprint.md` §14) — and Tap B is none of
> them. The endpoint is specified; its surface is not.

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-CLOSE-1 | `status='closed'`, `closed_at` set; the commitment stops being a selection candidate |
| AC-CLOSE-2 | Closing an already-closed or expired commitment returns 409 |
| AC-CLOSE-3 | No code path outside this endpoint sets `status='closed'` — asserted directly, since inferred completion is the failure this tap exists to prevent |
| AC-CLOSE-4 | With every commitment closed, the next `GET /api/card` returns `reason='everything_closed'` |

---

## 9. `POST /api/intake/parse`

Messy plan text → proposed commitments. **Writes nothing.**

**Request**

```json
{ "text": "…the week's plan, pasted…", "reference_date": "2026-08-23" }
```

`reference_date` is the user's local date, sent so that "Tuesday" has a chance of
resolving to the right week — one of the five named parser failure shapes
(`decisions.md` §5). **[DERIVED]**

**Response (200)**

```json
{
  "proposed": [
    {
      "title": "eval for lesson 3",
      "category": "marc_lessons",
      "stakes": "high",
      "deadline": "2026-08-27",
      "proposed_effort_minutes": 360
    },
    {
      "title": "reading week 4",
      "category": null,
      "stakes": "ordinary",
      "deadline": "2026-08-25",
      "proposed_effort_minutes": 60
    }
  ]
}
```

`category` is **null** when the parser produced something outside the enum. It
renders blank on the review screen and the user assigns one of the three before
saving. **No fallback bucket** — a fallback is a fourth category through the back
door (`decisions.md` §1).

On malformed model output the endpoint returns **502**. That leaves nothing to
review, which is precisely why the manual add form is a permanent floor and not a
convenience (`decisions.md` §5).

The model binding lives in build config, not here (`copy-spec.md` preamble).

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-PARSE-1 | The endpoint writes **no** rows. Asserted by row counts before and after, on every table |
| AC-PARSE-2 | Any category outside the three is returned as `null`, never coerced and never bucketed |
| AC-PARSE-3 | `reference_date` is passed to the model; relative-date fixtures ("Tuesday") resolve against it |
| AC-PARSE-4 | Malformed model output returns 502 with an error body, never a partial list presented as complete |
| AC-PARSE-5 | Effort is returned as `proposed_effort_minutes`, never as `effort_minutes` — the proposal and the value in force are different fields all the way through (`decisions.md` §1) |
| AC-PARSE-6 | The eval fixture set covers all five named failure shapes: merged commitments, wrong-week dates, invented category, wildly wrong effort, malformed JSON |

---

## 10. `POST /api/commitments`

One endpoint, two callers: **the review screen's Save** (a list) and **the manual
add form** (a list of one). Same validation both ways.

**Request**

```json
{
  "commitments": [
    {
      "title": "eval for lesson 3",
      "category": "marc_lessons",
      "stakes": "high",
      "deadline": "2026-08-27",
      "effort_minutes": 240,
      "proposed_effort_minutes": 360,
      "source": "parsed"
    }
  ]
}
```

`proposed_effort_minutes` is carried from the parse response through the review
screen and stored **alongside** the corrected value. **Both values are stored** —
the guess and the correction — as calibration signal (`decisions.md` §1). It is
`null` and `source` is `manual` for the add form, which has **no AI anywhere near
it**.

**Response (201):** the created commitments, echoing `effort_minutes` and never
`banked_effort_minutes` or `effort_remaining_minutes` (§2).

**Nothing touches the database until approved.** This endpoint *is* the approval
(`decisions.md` §5).

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-CM-1 | A commitment with `category` null, absent, or outside the enum is rejected 422; nothing in the batch is written |
| AC-CM-2 | The batch is atomic — a single invalid row rejects the whole request |
| AC-CM-3 | `deadline` absent is rejected 422. The column is nullable; **the flow is not** (`decisions.md` §1) |
| AC-CM-4 | `stakes` outside `high`/`ordinary` is rejected 422 |
| AC-CM-5 | `proposed_effort_minutes` and `effort_minutes` are stored independently; a save where the user overwrote the estimate preserves both |
| AC-CM-6 | `source='manual'` requests complete with the model client stubbed to raise |
| AC-CM-7 | The response contains no banked or remaining figure |
| AC-CM-8 | Saved commitments become selection candidates immediately — the next `GET /api/card` can offer one |

---

## 11. `GET /api/receipt`

**Query:** `?evening_date=YYYY-MM-DD` — optional; defaults to the current evening
under the rollover rule (`spec.md` §9.3).

**Response (200)**

```json
{
  "evening_date": "2026-08-19",
  "frozen": true,
  "body_lines": ["45 minutes on the eval", "20 minutes on the reading"],
  "sat_on_top_line": "Last night sat on top of the reading, due Thursday.",
  "expiry_lines": ["Nothing on the essay — the deadline was today."],
  "earned_question": {
    "shown": true,
    "text": "Did last night feel earned?",
    "state": "never_seen"
  },
  "pending_ask": {
    "card_id": "c_01H…",
    "text": "You started the eval last night — did that happen?"
  }
}
```

**Structure rules that are assertions, not styling** (`copy-spec.md` §7):

- **`body_lines` may be empty and the response shape does not change.** Two
  sessions is two lines, one is one line, zero is no lines, same frame. **Nothing
  is special-cased.**
- **No count preamble.** *"Two sessions today:"* is a summary a zero day cannot
  have; every candidate for that slot is a consolation.
- **`expiry_lines` render on zero days too.** A fact about a commitment is not a
  characterisation of your day.
- **No compensating line exists in the schema** for the zero day. There is nowhere
  to put one, which is the intent.

**`sat_on_top_line` fires on exactly one condition:** today's **highest-scoring
card that was offered and banked nothing**. No card offered → no line. Offered and
completed → no line. Declined at 90, re-offered at 20, completed → no line,
effort was banked. Read from `card.score_at_offer`, not re-scored at read time.

**Tense switches on freeze:** *tonight* live, *last night* frozen.

**`earned_question.shown` is true only when `frozen` is true.** Asking *"did
tonight feel earned?"* at 8:01pm rates an evening one minute old — the primary
outcome measure asked before the thing it measures occurs (`copy-spec.md` §8).

**`pending_ask` is present at most once per card, ever** (§13).

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-RCPT-1 | A zero-session day returns the identical key set with `body_lines: []` — no extra field, no message, no null-object stand-in (`spec.md` G11) |
| AC-RCPT-2 | An expiry line renders on a zero day, in the same position as on any other day |
| AC-RCPT-3 | `sat_on_top_line` is null when today's highest-scoring offered card banked effort |
| AC-RCPT-4 | `sat_on_top_line` is null when no card was offered today |
| AC-RCPT-5 | The line names the highest-scoring **offered** card, not the highest-scoring commitment — the distinction is the whole point of persisting `score_at_offer` |
| AC-RCPT-6 | Live receipts use *tonight*; frozen receipts use *last night* |
| AC-RCPT-7 | Requesting a receipt before `evening_start` returns 404 — the receipt is available at the evening-start hour (`decisions.md` §5) |
| AC-RCPT-8 | A live receipt request issues **zero** model calls beyond those already made at card-write time, and a frozen receipt reads stored text only |
| AC-RCPT-9 | `earned_question.shown` is false on a live receipt and true on every frozen one, **including zero days** (`spec.md` G12) |
| AC-RCPT-10 | No line, in any field, contains a remaining, owed, or missed figure |
| AC-RCPT-11 | Reading a frozen receipt with `earned_state='never_seen'` transitions it to `seen_dismissed` only on explicit dismissal (§12), never merely by being fetched |

---

## 12. `POST /api/receipts/{evening_date}/earned`

**Request:** `{ "value": true }` · `{ "value": false }` · `{ "dismissed": true }`

**Response (200):** `{ "evening_date": "…", "earned_state": "answered", "earned_value": true }`

Three states, mirroring the card outcome buckets (`copy-spec.md` §8):

| Value | Meaning |
|---|---|
| `answered` | yes/no recorded |
| `seen_dismissed` | receipt opened, question deliberately not answered |
| `never_seen` | receipt never opened |

**`seen_dismissed` is a distinct stored value, never a null that looks like a
bug.** Non-response on zero days is the highest-signal data in the product — the
closest available measure of the feeling the app exists to address. Forcing a
binary destroys it; collapsing `seen_dismissed` into `never_seen` loses it just as
completely.

`answered_at` is recorded separately from `evening_date` so that lag can be
derived. It exists to tell you whether the primary outcome measure decays with
recall (`copy-spec.md` §8).

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-EARN-1 | `answered_at` is stored and is never assumed equal to `evening_date` |
| AC-EARN-2 | A dismissal stores `seen_dismissed` — never null, never `never_seen` |
| AC-EARN-3 | The question is available on **every** frozen receipt, zero days included; there is no suppression path |
| AC-EARN-4 | Answering twice returns 409 |
| AC-EARN-5 | Derived lag is computed at read and stored nowhere |

---

## 13. `POST /api/cards/{id}/resolve`

Resolves an `abandoned_unknown` card.

**Request:** `{ "resolution": "confirmed" | "denied" | "dismissed" }`

**Response (200):** `{ "card_id": "…", "outcome": "abandoned_unknown", "resolution": "confirmed" }`

**Asked once.** On a screen deliberately opened, long after the session ended —
L2-safe. A genuine question with an unknown answer, which is the only reason it is
not a nag, **and why it must never be asked twice** (`copy-spec.md` §7).

**Dismissal closes the card.** One lost session beats a question that learns to
follow you.

The resolution is recorded on the existing bucket, not as a new one. `dismissed`,
like `done_no_start`, **cannot feed duration calibration** — collapsing it into
"never started" would lose the difference between *didn't answer* and *didn't
happen* all the way down to the calibration layer, which is where the damage
would be done.

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-RESOLVE-1 | After any resolution, `pending_ask` never appears for that card again — asserted across a rollover, not just within a session (`spec.md` G10) |
| AC-RESOLVE-2 | `dismissed` closes the card and records the resolution; it does not become `never_touched` |
| AC-RESOLVE-3 | `confirmed` records that the session happened and still writes **no** duration |
| AC-RESOLVE-4 | Calibration queries exclude `dismissed` and `done_no_start` alike |
| AC-RESOLVE-5 | At most one `pending_ask` is served per receipt fetch |

---

## 14. `GET /api/settings` · `PATCH /api/settings`

**Fields:** `evening_start` (`HH:MM` local), `timezone` (IANA).

`evening_start` is **the only time boundary the app has** — everything before it
is available, everything after is leisure. One field, set at Sunday intake,
user-adjustable in seconds. No calendar, no permissions, no per-card question
(`decisions.md` §3).

Known and accepted for week one: it does not know whether those hours are
actually free (calendar OAuth is v1), and it does not know if tonight is
different. **A "different tonight" tap is deliberately left out** — find out by
use whether it is missed. Do not add one because it seems obviously useful.

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-SET-1 | Changing `evening_start` changes the window used by the very next `GET /api/card` |
| AC-SET-2 | An invalid `HH:MM` or unknown timezone is rejected 422 |
| AC-SET-3 | No per-day, per-weekday, or per-tonight override field exists on this endpoint |

---

## 15. `GET /api/rewards` · `POST /api/rewards`

**POST body:** `{ "label": "Pro Clubs with Michael & Braden", "kind": "social", "timing": "external_clock", "usual_time": "21:00" }`

`kind` (`social` / `solo` / `either`) and `timing` (`external_clock` / `planned` /
`none`) are the two axes `decisions.md` §8 types the reward list along. Only
`timing` decides slot eligibility; `kind` is carried because the copy note turns
on the social/solo distinction.

Rewards are **typed at intake, specific, with examples next to the field** —
"Rocket League with Josh and Tom" lands, "Gaming" sounds like a habit app
(`decisions.md` §8). `label` is stored and rendered **verbatim**; the copy model
writes around it and never rewords it. *"The lads are on at 9"* is not available
to the app, because "the lads" is a group it would have to infer, and inference in
the copy layer is how it eventually names the wrong people (`copy-spec.md` §3).

> **OPEN-6.** How a stored reward becomes *tonight's* reward — and where the "at
> 9" in the rendered sentence comes from — is unspecified. `usual_time` exists as
> the obvious place to hang it, but nothing says a stored usual time is sufficient
> grounds to assert the reward is on tonight, and **invented leisure is forbidden**
> (`copy-spec.md` §3). This is the gap with the most direct line to the product
> eval: if most cards name no reward, the month-long measurement is measuring a
> to-do app.

### Acceptance criteria

| # | Criterion |
|---|---|
| AC-RW-1 | `label` round-trips byte-identical, including `&` and names |
| AC-RW-2 | `kind` outside `social`/`solo`/`either` and `timing` outside `external_clock`/`planned`/`none` are rejected 422 |
| AC-RW-3 | A reward with `timing='none'` never fills the card's reward slot (`copy-spec.md` §3) |
| AC-RW-4 | No card copy contains a reward label absent from this table (`spec.md` G8) |

---

## 16. Endpoint summary

| Method | Path | Writes | Ticket |
|---|---|---|---|
| GET | `/api/card` | **yes — persists on offer** | T3, T4, T5 |
| POST | `/api/cards/{id}/start` | yes | T5 |
| POST | `/api/cards/{id}/precommit` | yes | T5 |
| POST | `/api/cards/{id}/not-now` | yes | T5 |
| POST | `/api/cards/{id}/done` | yes | T1, T5 |
| POST | `/api/cards/{id}/resolve` | yes | T5 |
| POST | `/api/commitments/{id}/close` | yes | T1 |
| POST | `/api/intake/parse` | **no** | T2 |
| POST | `/api/commitments` | yes | T1, T2, T5 |
| GET | `/api/receipt` | freeze side effect only | T5 |
| POST | `/api/receipts/{date}/earned` | yes | T5 |
| GET/PATCH | `/api/settings` | yes | T1, T5 |
| GET/POST | `/api/rewards` | yes | T1, T4 |

---

## 17. Deliberately absent from week one

Named so their absence reads as a decision rather than an oversight, and so
nobody adds one because the REST shape looked incomplete.

| Endpoint | Why not |
|---|---|
| `GET /api/commitments` | No commitment-list view in week-one scope (`phased-development-plan.md` T5). A list view is also the natural home for a progress bar, so it does not arrive casually |
| `PATCH /api/commitments/{id}` | Post-save editing is unspecified. The review screen is where correction happens |
| `DELETE` on anything | No deletion path is specified anywhere |
| Auth, signup, login, session | Out by decision, not by omission (`decisions.md` §6) |
| Push subscription / heartbeat | Phase 4 |
| Calendar OAuth | v1 |
| Weekly pattern / synthesis | Phase 4, CUJ-5 |
| Any endpoint returning progress, streaks, or trend | Forbidden by L4, not merely unbuilt |

---

## 18. Global acceptance criteria

These are not per-endpoint. They run against the whole surface.

| # | Criterion |
|---|---|
| AC-G1 | A test walks **every** endpoint's serialised response and fails if any key or value exposes remaining effort, banked effort, decline counts, or a completion percentage (`spec.md` G1, G2) |
| AC-G2 | A test asserts the six quiet-reason strings character for character (`spec.md` G13) |
| AC-G3 | Every endpoint filters by `user_id`; a fixture with two users proves no cross-read (`decisions.md` §6) |
| AC-G4 | With the model client stubbed to raise, the whole loop still runs: manual add → card with fallback copy → start → pre-commit → done → receipt. **This is the fallback-first build order as a test** (`copy-spec.md` §11) |
| AC-G5 | Every offered card resolves into exactly one outcome bucket; none remains null past the rollover except an `abandoned_unknown` awaiting its single ask (`spec.md` G15) |
| AC-G6 | The rejected-variants table (`copy-spec.md` §10) runs as the card-copy eval set, with the stated verdict and reason attached to each line |
| AC-G7 | No test, fixture, or seed script sets `commitment.status='closed'` other than through §8 |

**AC-G4 is the gate for the whole of week one.** If the loop does not run with
the model unavailable, the model is load-bearing in a system whose sources say it
must not be: the AI writes sentences, it never picks cards, and the fallback is
the baseline the model has to beat.
