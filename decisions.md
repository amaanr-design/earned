# Earned — Decision Log

Pre-spec interrogation. Every decision below is locked unless marked OPEN.
The *reasons* matter as much as the decisions — they're what stops a decision
being quietly reversed later by someone (or some agent) who only sees the rule.

---

## 1. Entities

### Commitment vs card
A **commitment** is a thing you've said you'll do. It carries a **total effort
estimate**. A **card** is a time-bounded slice of one commitment offered on a
given day.

Six hours of eval does not arrive as one card.

### Two taps
- **Tap A** — "that session happened." Logs elapsed effort against the
  commitment. The normal tap, every session.
- **Tap B** — "this whole thing is finished." Rare, closes the commitment.

Why both: without Tap B the app has to infer completion from effort exhaustion
(estimated 6h, banked 6h, stop offering). Effort estimates are wrong constantly,
so that inference is wrong constantly.

### Effort estimates
AI proposes at intake, user can overwrite. **Both values are stored** — the
guess and the correction — as calibration signal.

Rationale: zero friction at intake, user keeps the veto, and the delta between
proposed and corrected is the training data that eventually lets the app stop
asking.

### The forbidden number
`remaining = total_effort − banked_effort` **must be stored** (selection needs
it) and **must never be returned by the API or rendered in any view.**

This is design law L4. "Four hours left" is a deficit figure — a *you owe me*
number. It is the same number as "hours you're behind," and it is the mechanism
that killed every previous system.

**Write this as a test.** It is exactly the kind of thing that reappears three
weeks later as a helpful progress bar.

The same rule applies to any re-derivation in a new unit:
- not-now tallies
- "leisure you'll lose" warnings
- weekly quotas that roll over when missed

All of these are the deficit column wearing a costume.

### Deadlines
**Every v1 commitment requires a deadline.** Nullable in the column, but the
parser must produce one or the intake flow asks.

Rationale: selection sorts by `stakes × urgency`, and urgency is
`effort_remaining ÷ days_remaining`. A commitment with no deadline makes that
term undefined and needs an entirely separate selection path. Building two
selectors before one is proven is the failure mode.

### Categories — fixed enum
1. `coursework`
2. `marc_lessons`
3. `build` (this app)

Three, not more. Friction-by-category is a rate over a small denominator — one
card a day means each bucket only collects a few dozen rows over months. Eight
categories learns nothing about any of them.

Coursework and Marc's lessons are split because they *feel* different to start,
and different feel is different friction. That they carry equal importance is
the stakes field's job, not the category's. Categories describe what a thing is;
stakes describe what it costs to skip.

**Unrecognised category from the parser:** the commitment appears on the review
screen with category blank, user assigns from the three before saving. Do not
add a fallback bucket — a fallback is a fourth category through the back door.

### Stakes — two levels
`high` and `ordinary`. Set at intake.

Two, not three, because with three everything lands in the middle.

Stakes is *not* urgency. Urgency is computed and changes daily on its own.
Stakes is stable, known when you write the plan, and answers a different
question: how much does it cost if this doesn't happen.

---

## 2. Selection algorithm

Fully deterministic. **No LLM anywhere in the selection path.** The AI writes
the sentence; it never picks the card.

```
urgency = effort_remaining / days_remaining
stakes_multiplier = 2 if high else 1
score = urgency * stakes_multiplier
```

Highest score wins.

### Worked example

| Commitment | Effort left | Days left | Stakes | Score |
|---|---|---|---|---|
| Eval | 4h | 2 | high | 4.0 |
| Reading | 1h | 1 | ordinary | 1.0 |
| Build | 5h | 9 | ordinary | 0.55 |

Eval wins.

### Why no deadline-day override
A thing due *today* can lose to a thing due tomorrow, and that was accepted
deliberately: a 4-hour high-stakes eval due tomorrow is a bigger fire than a
1-hour ordinary reading due tonight.

**Accepted consequence:** a commitment can expire without the app ever having
named it. This is not a bug — it's "one thing, not a list" plus "silence on
failure" working as designed. The receipt narrates it afterwards
("tonight sat on top of the reading, due today"), which is where consequence
belongs.

Rejected alternatives: deadline-day queue-jumping, and letting the card carry a
tail mentioning a second item. Both start the app down the road of having more
to say.

### Starvation
Anything that loses today scores higher tomorrow, because `days_remaining`
shrinks on its own. Starvation is temporary by construction.

**Except** for large commitments with distant deadlines — 20h over 6 weeks
scores ~0.48/day and loses to every small fire, correctly, every day, until the
deadline closes in and it's a scramble. This reproduces failure mode 3 (no
stakes until it's on fire) faithfully in software.

**Decision: neglect nudge.** Days since last touched feeds the score as a small
multiplier, so an untouched commitment climbs into contention on its own.

**The multiplier value is OPEN and deliberately unset.** Do not guess it before
the selector has run on real data. For week one, the weekly pattern surfacing
"the build hasn't been touched in three weeks" is sufficient and has no
parameter to get wrong.

### Pacing rate (display only)
`effort_remaining / weeks_remaining`, computed fresh, never stored.

Not a quota, not an allotment, never accumulates. Skip a week and the number
rises on its own because reality got heavier — nothing was owed, nothing rolled
over.

Feeds the weekly pattern: *"the build needs 4 hours a week from here, up from
3.3 a fortnight ago."*

**Rejected:** stored per-week allotments. An allotment you don't meet becomes a
debt, which compounds silently into an accusation. Also rejected: a ramp that
puts more hours nearer the deadline — that encodes the failure mode as a
feature.

---

## 3. Time and windows

### Evening start
One field at Sunday intake: **when does your evening start?** (e.g. 20:00).
User-adjustable in seconds.

This is the only time boundary the app needs. Everything before it is available;
everything after is leisure. No calendar, no permissions, no per-card question.

Known gaps, accepted for week one: it doesn't know if those hours are actually
free (calendar OAuth is v1), and it doesn't know if tonight is different. A
"different tonight" tap is deliberately left out — find out by use whether it's
missed.

### Slice sizing
Slices fit the current window, bounded:
- **Floor: 25 minutes.** Below this the app offers nothing.
- **Ceiling: 120 minutes.**

Why bounded: a 15-minute card on a 6-hour eval is an insult and burns a card. A
6-hour card is a wall nobody starts.

**Ceiling ≠ offer size.** Calibration shrinks *offers* toward what actually gets
finished (offer 120, consistently do 40 → start offering ~45). The 120 ceiling
stays as a hard cap for the rare genuinely clear afternoon.

### Cadence — one card at a time, not one a day
A new card comes when conditions are right: enough window left for a real slice,
and something worth surfacing.

Finish at 4pm with four hours before evening → another card.
Finish at 7:40pm → nothing. Window is under the floor, app goes quiet for the
night.

**Cap: 3 cards/day for week one.** Not because 4 is wrong, but because the
unseen failure mode is the app being chatty on a good day and training you to
stop looking. Cap it, watch, adjust.

---

## 4. Card lifecycle

### Cards are persisted when offered
Not computed on read.

Critical: if a card is only calculated when the page opens, a card you never
opened was never offered as far as the database is concerned. Re-entry learning
is built entirely on the record of things offered and ignored.

### Staleness
A card offered at 6pm is stale by 9pm **on the merits** — a 45-minute card
doesn't fit an evening that's already started. The card regenerates for the
current moment; the 6pm card closes quietly into `never_touched`.

**No overdue indicator.** Same reason as no warnings: it's a scold.

### Outcome buckets
Every offered card lands in exactly one. Most are invisible to the user and
recorded anyway — the silent ones are the primary learning signal.

| Bucket | Meaning | Duration data |
|---|---|---|
| `never_touched` | Offered, no tap | none |
| `not_now` | Declined | none |
| `completed` | Start → Tap A | real start + end |
| `abandoned_unknown` | Started, never closed | resolved by asking |
| `done_no_start` | Tap A without start (work happened away from app) | none |

**`abandoned_unknown` resolution:** leave the card open and ask **once**, next
time the app is opened — *"you started the eval last night, did that happen?"*

Rejected: auto-close at midnight, auto-close after the card's stated length.
Both invent a number and feed it to the thing that's supposed to be learning
real durations. That poisons the calibration well quietly.

This is L2-safe: the session is long over, nothing is being interrupted, and
it's on a screen the user chose to open.

`done_no_start` records that a session happened but **cannot feed duration
calibration** — there's no real number in it.

### Not-now behaviour
Declining does not end the day. The **same commitment** can return in a
**smaller slice** later — 90 minutes was too much at six; 20 at nine is a
different offer, not a repeat.

Rejected: cycling through other commitments looking for a yes (trains you to
decline until something easy appears), and faster re-offers for urgent items
(nagging on a timer, which is what gets apps deleted).

Repeated not-nows **do** feed learning — but only into *how the app offers*
(smaller slices, earlier in the day). They must never surface as anything
resembling a tally of refusals.

### No warnings, ever
Explicitly rejected: *"decline this and your leisure goes down."*

Three reasons, all from the design laws:
1. **It isn't true.** The app has no authority over the evening (L1). It cannot
   make leisure go down. The first night you decline and game until 1am anyway,
   the app has been caught bluffing.
2. **It's a scold.** Not-now is free — no guilt copy, no follow-up.
3. **It's the deficit column in a new unit.** Hours-you-owe becomes
   leisure-you'll-lose.

**Where the teeth actually live:** the receipt (narrated afterwards, when
nothing can be interrupted) and humans — the aunt, Marc — via the weekly
pattern. L6. The teeth are real; they're just somewhere the app can't get itself
deleted for.

---

## 5. API contract

### Card endpoint — quiet responses
The server **always returns a reason** when there's no card:
- window under floor
- everything closed
- nothing due
- daily cap reached

Rationale: a blank screen is indistinguishable from a broken app. The reason
field costs one string and is needed for debugging.

Client renders a **short, warm, work-free line**, varying by reason. "Everything
done" and "too late for a session" are genuinely different nights, and one
deserves a small congratulation.

**Copy rules — the difference between this and every blocked app:**

| Acceptable | Forbidden |
|---|---|
| "Nothing tonight. Enjoy it." | "You've got 10 minutes if you want it." *(pushing after deciding not to)* |
| "Nothing to offer — the evening's already started." | "No card tonight — you skipped the eval earlier." *(scold)* |

A quiet screen should feel like the app being **finished with you for the day**,
not disappointed in you.

### Sunday intake — review before save
1. User pastes the week's plan
2. Flash parses → structured commitments returned
3. Commitments render as **editable rows**
4. User corrects (effort, dates, blank categories)
5. Save writes to database

**Nothing touches the database until approved.** This is where the effort-
estimate veto physically happens — it needs a screen to happen on. A junk parse
under save-first becomes live data to clean up.

### Parser failure
Parsers fail. Observed failure shapes to design for:
- merges two commitments into one (5 → 4)
- resolves "Tuesday" to the wrong week, silently
- invents a category outside the enum
- guesses 4 hours for a 40-minute task
- returns malformed JSON, nothing parses

The first four are caught on the review screen. The last leaves nothing to
review.

**Decision: manual add-commitment form.** Plain fields — title, category,
deadline, effort, stakes — no AI anywhere near it.

Two reasons: it's a permanent floor (however badly the parser behaves,
commitments can always get in — week one has no auth and no push, so a total
parse failure on the first Sunday means an app with nothing in it), and it
handles the thing that comes up on Wednesday, which a Sunday paste can't.

**Rejected: a raw-JSON editor.** Hand-editing JSON on a phone is unusable as a
real feature, and it's the kind of debugging tool that quietly stays in the
product because it worked once.

### Receipt — hybrid
- **Available at evening-start hour** (the same field as slice windowing)
- **Recomputes live** while the day is still running — do a session at 9 and it
  updates
- **Freezes at a rollover hour** (~4am, technical, never seen) into a permanent
  record

Why not fully fresh: Flash writes the sentence, so recomputing means an LLM call
every open — cost, latency, and *different words each time* about the same
evening. That undermines the one thing the receipt is for.

Why frozen matters: the weekly pattern reads five real receipts rather than
re-narrating history, and Marc reads the same sentence you did.

**Why evening-start is the right boundary**, not midnight and not sleep: L2 says
the app speaks at the boundary before a session. The receipt is that boundary
from the other side — a sentence about the day that just ended, delivered as
leisure begins.

**Accepted gap:** with no push, the receipt has to be opened deliberately, so it
may not be read until the next morning. A morning receipt read sober is
arguably better. The "close the evening" moment arrives properly with push in
v1.

---

## 6. Schema decisions

### Multi-user from day one
**In:** users table, `user_id` on every row, timezone field on user, every query
filtered by user.

**Out:** signup, login, password reset, email verification, sessions. Week one
has one user; hardcode which one.

Rationale (Marc, direct): retrofitting for publishing is painful. Adding a user
column to five tables now is fifteen minutes; adding it after three weeks of
real data is a migration you'll be nervous about. The asymmetry does the
deciding.

### Counted commitments (Marc's model) — schema now, feature later
Marc's reframe: habits become tasks with a count. Gym = 3 sessions, deadline
Sunday, effort ≈ 2.25h. It then runs through the **existing** formula with no
changes:

- Monday: 2.25 ÷ 7 = 0.32 → sits quietly
- Saturday, 1 done: 1.5 ÷ 2 = 0.75 → climbs into contention on its own

This makes "fitness needs a separate selector" **false**, which is why fitness
was cut from v1. It's better than the reason for cutting it.

It also resolves Tap B for free: for a counted commitment the third Tap A *is*
Tap B. Completion is count-based and fires automatically.

**Two fields to leave room for now:**
- `target_count` — completion is "3 of 3", not effort exhaustion
- **recurrence** — the gym commitment regenerates each Sunday rather than
  closing forever. This is a genuinely new concept (a template spawning fresh
  commitments), and it's the same argument as multi-user: cheap now, annoying
  to retrofit.

**Two guards that must be written into the spec in words**, because a weekly
target that can be missed is a streak wearing a costume, and streaks are the
named delete trigger:
1. **The week resets clean.** Missing 3 does not mean 4 next week.
2. **2 of 3 is not a failure state.** It's two sessions that happened. Nothing
   on screen mourns the third.

**Build order:** schema fields now, feature after the week-one loop runs.
Fitness is the commitment type with the least evidence behind it — the wrong
thing to be debugging while still finding out whether the core loop works.
(This follows Marc's own second point: deploy fast, try the MVP, adapt.)

---

## 7. Open items

| # | Item | Notes |
|---|---|---|
| 1 | Neglect-nudge multiplier value | Deliberately unset. Do not guess before the selector runs on real data. |
| 2 | Which Tuesday | The date the loop runs on real life. Not set. |

---

## 8. Standing principles

- **The AI writes sentences. It never picks cards.** Selection is deterministic
  and testable.
- **Deficit figures are forbidden in any unit.** Hours remaining, not-now
  tallies, leisure-lost warnings, rolled-over weekly quotas. If a number can be
  read as *you owe me*, it doesn't render.
- **Silence is a designed output, not an absence.** The app having nothing to
  say is a feature, and it's what stops it becoming the notification you swipe
  away.
- **Teeth come from humans.** The app narrates; the aunt and Marc ask.
- **Specificity makes copy work.** "Rocket League with Josh and Tom" lands.
  "Gaming" sounds like a habit app. Rewards are typed at intake, specific, with
  examples next to the field.

### Reward list (v1, user-supplied)

| Reward | Type | Time-bound? |
|---|---|---|
| Pro Clubs with Michael & Braden | social, others present | yes — they're on when they're on |
| Overwatch with Shaan (brother) | social, others present | yes |
| Single player gaming night | solo | no |
| Movie night | either | planned |
| Night out with family or friends | social | planned, fixed |

**Note for copy:** these split two ways and the split matters. The social ones
have an **external clock** — "the lads are on at 9" works because it's true and
someone else set the time, which is exactly what makes the boundary real. The
solo ones don't, so copy has to lean on the thing itself rather than the hour.
Planned ones (movie night, night out) are known days in advance, which is the
only category the app could in principle anticipate.
- **Deploy fast, adapt the blueprint** (Marc). This document is a decision log,
  not a contract with the future.
