# Earned — Copy Spec

Sibling to `decisions.md`. Covers every sentence the app can render.
Locked unless marked OPEN. Rationale is kept alongside each rule for the same
reason as the decision log: a rule without its reason gets reversed by whoever
only reads the rule.

Every sentence below has been through review. Where a case has no sentence, that
is the decision, not an omission.

**On model naming.** This document says **the copy model** and **the judge
model**, never a product name. Blueprint §12 assigns those roles to a cheap fast
tier and a reasoning tier respectively, with its own caveat that the tier matters
more than the version. The current binding is recorded in the build config, not
here — so a rename, a version bump, or a change of provider does not make this
spec read as stale when nothing in it has changed.

---

## 1. The two rules

Every rendered string is judged against exactly these. Nothing else is a rule.

### R1 — Fact, not evaluation

A line may state what is or what happened. It may not evaluate it.

**Evaluative** = any comparison to a prior state, an expectation, or a norm.

**R1 bans evaluating the person's performance. It does not ban evaluating the
night.** *"Enjoy tonight"* is a statement about the evening and evaluates
nothing about you. This distinction matters in the strict direction: a reading of
R1 that forbids a warm word on the single best night of the month is a rule
producing a bad sentence, which means the rule is being misread.

Passes: *"still due Thursday"*, *"the deadline was today"*, *"tonight sat on top
of the reading"*, *"enjoy tonight"*.
Fails: *"back on it"*, *"only 25 minutes again"*, *"finally"*, *"that's enough
for today"*.

### R2 — Scope

The card speaks only about the session in front of it.
The receipt speaks only about the day that ended.
**Neither may cite a prior card's outcome as a reason for the present one.**

R2 exists because R1 alone does not catch the canonical scold. *"No card
tonight — you skipped the eval earlier"* is bare fact, past tense, no
comparison. It passes R1 cleanly and it is exactly the sentence that must never
render. What makes it a scold is reach, not tone.

### Why there is no third rule

A second-person ban was considered and rejected. It targets the grammar scolds
usually wear rather than the failure itself, and it costs *"you've earned it"* —
the thesis of the product in four words. `You` is permitted throughout.

---

## 2. The lint (advisory, never blocking)

A word list flags lines for weekly review. **It does not reject them.**

> again · still · only · finally · at last · back on it · as usual · managed to

It runs **outside the request path** — writes a flag row, adds no latency, no
cost, never blocks a render. Flags are read in batch alongside the receipts.

**A flagged line that is correct is the expected case, not a defect.** *"Still
due Thursday"* is bare fact. *"Only 25 minutes in the window"* is a true
constraint. Both flag; both ship.

The list misses scolds using none of these words, and catches legitimate
sentences using several. That is why R1 and R2 are the judge — applied by the
judge model on a sample, not by string matching on every card.

---

## 3. The skeleton

**Every slot's presence is decided deterministically. The copy model only fills
the slots it is handed.**

This is blueprint §7's deterministic/AI line pushed one level down, into the
sentence. The copy model never decides *whether* to mention the reward, the boundary, or
the deadline — it receives a filled struct and writes around it. An empty slot
cannot be re-filled by a chatty model.

| Slot | Source | Presence decided by |
|---|---|---|
| `duration` | selection + calibration | always present |
| `title` | commitment title, **verbatim** | always present |
| `reward` | reward list, **verbatim**, only if known and time-bound | backend |
| `boundary` | `evening_start` field | backend — **once per day, first card** |
| `deadline` | deadline arithmetic | backend — only inside the window |

### Titles and rewards are verbatim slots

The copy model writes *around* them and never rewords them. Same discipline as
no-LLM-in-selection: if the copy layer can rename the work, a wrong card has no
stack trace.

This settles a copy question by structure rather than taste. The reward list
holds *"Pro Clubs with Michael & Braden"*, so that is what renders. *"The lads
are on at 9"* is not available to the app — "the lads" is a group it would have
to infer, and inference in the copy layer is how it eventually names the wrong
people.

**The fallback template uses the same slots**, so a fallback render and a model
render name the thing identically. That is what makes them comparable in the
eval.

### Copy is generated at card-write time. Read is always instant.

The sentence is written when the card is written and stored on the card row.
Opening the app is a database read.

**There is no read-time latency budget**, because nothing is being generated
while you look at it. What is needed instead is a **generation-time timeout**: if
the copy model has not returned by the limit, the card is stored with the
fallback template text, and that is what the card says — **permanently**.

- No retry on read
- No text swapping under your eyes
- No spinner
- No dependency on the model being up at the moment you open the app

This also keeps the offered-card record and the text you actually saw as the
same row, which is what makes the re-entry learning in blueprint §11 honest —
`decisions.md` already requires cards to be persisted when offered rather than
computed on read.

**The timeout is 3 seconds.**

This is the one number in either document that costs nothing to get wrong. A
timeout set too tight produces a fallback card, and a fallback card is already
a card you decided was acceptable — it is the baseline the model has to beat.
There is no failure state hiding behind it.

Watch it through the fallback rate rather than by tuning it: if 3 seconds is too
tight for the prompt, the fallback count says so, and if the cards read fine
anyway, that is §11's argument arriving on its own.

### The reward slot has three states

1. **Named reward** — known and time-bound (an external clock, or a planned night)
2. **Boundary** — `evening_start`, always true, always available
3. **Empty**

Invented leisure is forbidden. It is a lie by the tenth use and an
*unfalsifiable* one — you cannot correct the app about a reward that never
existed.

The boundary state exists to protect blueprint §13. If most cards name no
reward, the month-long eval measures a to-do app, and a flat result would not
mean the bet failed — it would mean the bet was never on screen.

**Empty is normal on later cards and forbidden on the first.** Earned-ness gets
stated once, on the card that has to get you started. Restating it on card three
is wallpaper.

This is not a compromise. Cadence in `decisions.md` is *one card at a time, not
one a day* — a second card only arrives if a session finishes with a real window
still left. On a normal evening-weighted day that means one card, and it carries
the boundary. Cards two and three only happen on a day already being worked
through, where you are mid-flow and do not need the thesis restated.

**Rejected:** later cards carrying the window as a substitute fact — *"25
minutes on the reading. Two hours before 8."* That is a countdown, countdowns
are pressure with a clock on them, and it is the closest thing yet to a deficit
figure that is not one.

### Boundary guards

**Once a day.** Three cards each ending in the boundary is wallpaper by
Wednesday, and wallpaper stops being read. First card of the day gets
`boundary: true`; later cards get `false`. The copy model cannot know what it said this
morning, so this is a backend boolean, never a model judgment.

**Coordinating conjunctions only.** The boundary clause joins with `and`, or a
full stop. Never `then`, `once`, `after`, `when that's done`.

Note the asymmetry in the named-reward case: *"45 minutes on the eval, then Pro
Clubs with Michael and Braden at 9"* is safe with `then`, because that 9pm clock
belongs to Michael and Braden and runs whether the work happens or not. The same
`then` attached to the boundary is unsafe, because the app owns that field and
the sentence begins to read as ownership.

**Named drift target:** *"the evening's yours once this is done."* That is a
conditional, a conditional is a gate, and L1 says the app has no gate to offer.
It will arrive looking like a small improvement.

**Ownership note:** *"the evening's yours at 8"* was rejected in favour of
*"evening starts at 8"* for the same reason in miniature — the possessive
asserts the app granted something it did not.

### Deadline clause on cards

Bare fact only. Never comparative. Rendered only inside the last **N** days.

Kept rather than omitted: the deadline already drives selection, so omitting it
means the app is using something load-bearing and not saying it. That opacity is
what makes Motion users fight the algorithm (blueprint §5). Saying it keeps
selection legible.

**N is OPEN.** Do not guess it before the selector runs on real data. N is the
dosage dial — a large N turns *"due tomorrow"* into ambient pressure on
everything.

### Forbidden in every slot, permanently

`effort_remaining` in any unit or costume. L4.

---

## 4. Card sentences

| # | Case | Sentence | Slots | The thing that could have failed |
|---|---|---|---|---|
| 1 | First card, no known reward | *45 minutes on the eval. Evening starts at 8.* | duration, title, boundary | Full stop, no conditional. No possessive — the app grants nothing |
| 2 | Later card, boundary spent | *25 minutes on the reading.* | duration, title | No `another` — that would cite the earlier card (R2) |
| 3 | Named time-bound reward | *45 minutes on the eval, then Pro Clubs with Michael and Braden at 9.* | duration, title, reward | `then` is safe: external clock, not the app's. Reward verbatim from intake |
| 4 | Planned reward | *40 minutes on the reading. Movie night at 8.* | duration, title, reward | Full stop, not a conditional |
| 5 | Inside deadline window | *45 minutes on the eval, due tomorrow.* | duration, title, deadline | Bare fact, no comparison (R1) |
| 6 | Re-offer, smaller slice | *20 minutes on the eval.* | duration, title | Silent about the decline. The slice is the only thing that changed (R2) |
| 7 | Re-entry after a gap | *20 minutes on the build.* | duration, title | No acknowledgement of the gap (R1 — comparison to a norm) |
| 8 | Counted commitment | *45 minutes at the gym, before Sunday.* | duration, title, deadline | The count is absent from copy though present in the model. Nothing mourns the third |
| 9 | Fallback, copy model unavailable | *45 minutes on the eval.* (+ *Evening starts at 8.* when flagged) | duration, title, boundary | Same slots as the model path — comparable in the eval |

---

## 5. Quiet screens

The server always returns a reason. The client renders a short, warm, work-free
line. A quiet screen should feel like the app being **finished with you for the
day**, not disappointed in you.

### State the reason. Stop.

On a quiet screen the outcome is already visible — there is no card. Saying it
anyway is redundant, and **redundancy repeated is how a line acquires a tone it
did not have on first sight.** By the twentieth appearance the second sentence
reads as the app making sure you noticed.

So *"The evening's already started. Nothing tonight."* becomes *"The evening's
already started."*

| # | Reason | Sentence |
|---|---|---|
| 10a | Evening already started | *The evening's already started.* |
| 10b | Window shorter than the floor | *Not enough time for a proper go at anything.* |
| 11 | Everything closed | *That's everything closed. Enjoy tonight.* |
| 12 | Nothing due | *Nothing due tonight.* |
| 13 | Daily cap reached | *That's the day.* |
| 14 | After a not-now | *Nothing else right now.* |

**10a and 10b are two states, not one.** The original single line was false at
4pm on a day full of meetings — "the evening's already started" and "the window
is too short for a real session" are different facts and need different
sentences.

**11 is the only line that keeps a second clause**, because *"enjoy tonight"*
adds something rather than restating. It is also the one night that earns a small
congratulation, and it passes R1 under the person/night distinction in §1.

**13 makes no claim about what got done.** The cap can be reached with three
cards offered and all three declined. *"That's enough for today"* is the failing
version.

**14 is a distinct state and must not reuse 10–13.** Reusing the no-card line
after a decline is a small dishonesty — there *was* something, it was declined,
and the app pretending otherwise reads as passive aggression. It is also
operationally different: the same commitment can return in a smaller slice later,
so the day is not over. Hence *right now*, not *tonight*.

The acknowledgement token was cut. *"Okay. Nothing else right now."* registers
the decline, and registering is one step from noting.

**Known and accepted:** *right now* is temporally open and at high frequency may
read as *I'll be back* — nagging-on-a-timer arriving through tense rather than
behaviour. It is still the best available version, because the alternatives imply
the day is over when it is not. Instrumented, not redesigned.

### No rotation

Quiet lines are a fixed, small, auditable set. **No variants, no rotation index,
no state.** The finding was that brevity kills wallpaper, not variety — so when a
line goes stale the fix is to rewrite it shorter, never to add alternates. A
side benefit: the eval can assert the exact strings.

---

## 6. Pre-commit

| # | Case | Sentence |
|---|---|---|
| 15 | Intended length | *How long are you giving it?* (tapped options, no typing) |

Fires on **Start**, immediately after the card. Length only, tapped. Typing at
this moment is exactly the friction that kills a three-second interaction.

### The pre-commit estimates the work, not the leisure

CUJ-3 reads as the leisure ("what's the plan after?"). Blueprint §11's worked
example is the work ("said 45 on the eval → did 20"). **Resolved in favour of
the work**, on the ground that decides it:

**A work estimate has a measurable actual. A leisure estimate has none.** Start
plus Tap A gives real elapsed minutes. Nothing signals when a gaming session
ended, and week one has no mechanism to ask. Estimating leisure produces a
number that can never be checked against anything, which means blueprint §11
learns nothing from it.

Any value in saying the leisure out loud is a bonus, not infrastructure — and
this spec does not build infrastructure for it.

### Three numbers, not two

The card carries the app's offer. The pre-commit carries yours. Tap A carries
the truth.

| Number | Source |
|---|---|
| offered slice | selection + calibration |
| pre-commit | the user, at Start |
| elapsed | start → Tap A |

Offered 45, said 20, did 25 is a richer training row than offered 45, did 25 —
it separates *the app sized it wrong* from *you stopped early*, which are
different corrections.

**Tap options are generated around the offered slice** by the backend, not
chosen by the copy model. Same rule as every other slot.

**Wording guard.** The pre-commit asks for a number the app has just proposed,
so it is one wrong verb away from reading as a challenge. *"How long are you
actually going for?"* and *"How long, really?"* both fail — they doubt the
answer before it is given. *"How long are you giving it?"* asks for a commitment
without questioning one.

---

## 7. Receipt

### The body is a list, not a sentence

```
45 minutes on the eval
20 minutes on the reading
```

Two sessions is two lines. One is one line. Zero is no lines, same frame.
**Nothing is special-cased.**

**A count preamble is forbidden.** *"Two sessions today:"* is a summary
sentence, and a zero day cannot have one — every candidate is a consolation. A
summary would make the zero day structurally different, which is precisely what
§7's zero-day rule forbids. Removing it also dissolves the one-session case
entirely, which is the sign it was right.

### Lines below the list

These are facts about the day rather than summaries of it, so they survive.

| # | Case | Sentence |
|---|---|---|
| 17 | Evening sat on a live commitment | *Tonight sat on top of the reading, due Thursday.* |
| 18 | Commitment expired | *Nothing on the essay — the deadline was today.* |
| 20 | `abandoned_unknown` resolution | *You started the eval last night — did that happen?* |
| 21 | The earned question | *Did last night feel earned?* — yes · no · dismissible |

### 17 — when the sat-on-top line fires

**It names the commitment from today's highest-scoring card that was offered and
banked nothing.** Nothing else.

This reads state the database already holds — cards are persisted when offered —
rather than re-scoring, and it needs no threshold to guess:

- No card offered today → no line
- Card offered and completed → nothing sat on top of it
- Card declined at 90 minutes, re-offered at 20, completed → no line, effort was banked

A day-count cap was rejected in favour of this. The point of the line is that the
evening sat on top of something with weight behind it; a deadline three weeks out
has none, and the line firing anyway is how it becomes furniture. "Scored
meaningfully" becomes "was actually offered," which is a fact rather than a
parameter.

**Tense switches on freeze:** *tonight* on the live receipt, *last night* on the
frozen one. The receipt already switches on freeze, so this needs no new
mechanism.

### 17 and the L5 collision

L5 says *same night, no judgment*. The receipt is same-night, and *what the
evening sat on top of* is its sharpest sentence.

**Resolved:** the receipt may state what happened and what did not, but never a
word that evaluates it. L5 bans verdicts, not facts. *"Tonight sat on top of the
reading, due today"* passes. *"Tonight sat on top of the reading — again"*
fails. That gives an eval something to check instead of a vibe.

### 19 — the zero-day receipt

**Structurally identical to every other receipt, with an empty list.** Same
frame, same shape, nothing where the sessions would be. No compensating line, no
softening, no acknowledgement of the emptiness. The absence is visible and
unremarked.

Any characterisation of a zero day is evaluative however gently phrased, because
the only true characterisation is *nothing happened*. That is an R1 violation
dressed as kindness. Every candidate sentence for that slot is either a
consolation or a nudge, and both are verdicts.

**An expiry line still renders on a zero day.** Zero rows above, the expiry line
below. It is a fact about a commitment, not a characterisation of your day — the
same distinction that admits *"enjoy tonight"*. The empty list speaks for itself
beside it.

**The layout does not collapse.** The empty list keeps its space and the lines
below keep their fixed position. If the layout reflows so the expiry line floats
to the top, the app has tidied the absence away, and tidying an absence is a
comment on it. The gap is the point.

**Recorded, not treated as a defect:** the first zero-day receipt will land hard.
That is the design working. If it proves genuinely unbearable after real use,
that is data, and it is the kind only obtainable by shipping it as specified.

### 20 — the `abandoned_unknown` ask

Asked **once**, on a screen deliberately opened, long after the session ended.
L2-safe. A genuine question with an unknown answer, which is the only reason it
is not a nag — and why it must never be asked twice.

**Dismissal closes the card.** One lost session beats a question that learns to
follow you.

Resolution is recorded on the existing bucket, not as a new one:

| Resolution | Meaning |
|---|---|
| `confirmed` | the session happened |
| `denied` | it did not |
| `dismissed` | asked, not answered, card closed |

`dismissed`, like `done_no_start`, **cannot feed duration calibration** — there
is no real number in it. Collapsing `dismissed` into "never started" would lose
the difference between *didn't answer* and *didn't happen* all the way down to
the calibration layer, which is where the damage would actually be done.

---

## 8. The earned question — timing and storage

Asked **every day. Never suppressed.** Suppressing it on zero days biases the
primary outcome measure of the entire product toward good days and quietly
breaks blueprint §13.

Identical wording, identical position, whether the list above it has two rows or
none. On a zero day it is the last thing on a screen with nothing else on it.
That is the design working as specified, and it will feel like more than it is.

### It lives on the frozen receipt, not the live one

The live receipt is available at `evening_start`. Asking *"did tonight feel
earned?"* at 8:01pm rates an evening one minute old — the primary outcome
measure asked before the thing it measures occurs.

**Decision:** the question appears only on the **frozen** receipt, on next open,
about last night. Hence *"did last night feel earned?"* — the wording changes
with the timing. Sober and retrospective.

This turns the accepted gap in `decisions.md` §5 (no push, so the receipt may
not be read until morning) from a compromise into the design.

**Caveat recorded:** open the app on Tuesday afternoon and you are rating Monday
night from a distance. Recall degrades.

### Three columns, not one

| Column | Meaning |
|---|---|
| `evening_date` | the evening being rated |
| `answered_at` | when the answer was given |
| *(derived)* lag | the gap — tells you whether the measure decays |

Cheap now; it protects the metric the whole month is built around. Later you can
check whether same-morning answers and two-days-later answers behave
differently.

### Three states, not two

| Value | Meaning |
|---|---|
| `answered` | yes/no recorded |
| `seen_dismissed` | receipt opened, question deliberately not answered |
| `never_seen` | receipt never opened |

Mirrors the card outcome buckets. **`seen_dismissed` is a distinct stored value,
never a null that looks like a bug.**

Non-response on zero days is the highest-signal data in the product — the
closest available measure of the feeling the app exists to address. Forcing a
binary destroys it, and collapsing `seen_dismissed` into `never_seen` loses it
just as completely.

---

## 9. Instrumentation and triggers

The failure mode that cannot be caught in a review session is a line reading as
pointed on its twentieth appearance. It is not fixable by writing better
sentences. It is caught by counting.

**Count every quiet-reason render and put the counts in the weekly review**,
alongside the lint flags and the receipts. Same discipline as the lint: do not
enforce in the moment, observe in batch.

### Per-reason triggers

One number across all reasons would be wrong. A high count means something
different for each, and only three are bad news at all.

| Reason | Rough weekly trigger | What a high count means | Action |
|---|---|---|---|
| Evening already started | **>10** | The card is not reaching you before evening | Not a copy problem — this is the evidence file for push |
| Window under floor | **>5** | The 25-minute floor or slice sizing is wrong for real days | Revisit the floor, not the sentence |
| Nothing due | **>3** | Intake is thin — Sunday's paste missed the week | Check the intake, not the copy |
| Cap reached | **>2** | **Good news** — three cards means real windows | None, unless paired with low completion |
| Everything closed | any | **Good news** | None |
| After a not-now | **>5** | Declines are high; already feeds slice calibration | None. Copy unchanged |

### Fallback rate

Count cards written with the fallback text because the copy model timed out.
It is not a copy trigger — it is the honest answer to whether the model
dependency is earning its place (§11). A high fallback rate with no felt
difference in the cards is the strongest possible argument for dropping the
model entirely.

### The wallpaper trigger

Any single reason firing **more than about once a day** — call it >8 in a week —
has become the app's default sentence, whatever else is true.

**The response is to rewrite the line shorter. Never to add variants.** Brevity
is what stops wallpaper; variety just hides it somewhere unobservable.

### The two cross-cutting alarms

1. **Quiet share of opens above 50%, two weeks running.** More than half of opens
   producing nothing teaches you that opening is pointless. Raw counts cannot show
   this — a high count in a genuinely busy week is harmless.
2. **Opens per week falling 30%+ while the earned-rate is also falling.** The only
   leading indicator here. Every system in the blueprint's death-causes list died
   this way, and it is visible in the data about a week before it would be felt.

### The engagement-metric guard

Opens are the most dangerous number in this document. Once an engagement metric
is on a weekly page, the temptation is to make it go up — and that is the road
to push notifications, streaks, and every mechanism this app exists to avoid.

> **Opens are never rendered alone.** The figure exists only as a pair with the
> earned-rate. A fall in opens with a steady earned-rate is recorded as
> **working, needs you less** — not as churn.

**Named drift target:** if the pair does trip, the response is a design question,
never a re-engagement feature. Forbidden responses, written down now so they
arrive recognisable — increased push frequency, reminders to open, streaks,
anything that rewards opening. There is no action that raises opens without
breaking L1 or L2.

### No baseline in week one

A 30% fall needs something to fall from, and the first weeks are atypical because
the user is also the developer.

**The baseline begins after the first full week in which the code does not
change.** Git says when that happened. "A couple of weeks" would be
unconsciously dated from whenever the graph was first opened.

### Every number here is OPEN

Same status as the neglect-nudge multiplier. They are named now so they function
as triggers rather than statistics to read past — not because they are right.

**The weekly review records whether a trigger fired and whether it felt
correct**, so the numbers calibrate off real reaction rather than staying frozen
at a guess.

---

## 10. Rejected variants

The eval set starts here. Each of these is plausible, several are improvements
someone will propose, and all of them fail.

| Rejected | Fails | Why |
|---|---|---|
| *Another 25 minutes on the reading.* | R2 | Cites the earlier card |
| *It's been a while — 20 minutes on the build.* | R1, R2 | Comparison to a norm; reaches backwards |
| *Back on it — 30 minutes on the build.* | R1 | Lint-flagged and genuinely evaluative |
| *2 of 3 gym sessions done.* | R1 | A progress figure that mourns the third |
| *45 minutes on the eval, then the evening's yours.* | gate | Conditional binds leisure to work |
| *The evening's yours once this is done.* | gate | The named drift target |
| *45 minutes on the eval, and the evening's yours at 8.* | ownership | Possessive asserts the app granted it |
| *25 minutes on the reading. Two hours before 8.* | countdown | Pressure with a clock on it |
| *No card tonight — you skipped the eval earlier.* | R2 | The canonical scold. Passes R1 |
| *You've got 10 minutes if you want it.* | floor, L1 | Pushing after the app decided not to |
| *The evening's already started. Nothing tonight.* | redundancy | Outcome is already on screen; repeated, it reads as pointed |
| *Okay. Nothing else right now.* | registering | The token registers the decline |
| *Nothing tonight, enjoy it.* **after a not-now** | state | True line, wrong state. Reads as passive aggression |
| *Two sessions today: 45 minutes on the eval…* | structure | A summary the zero day cannot have |
| *Quiet one today.* | R1 | Characterising a zero day |
| *Only 25 minutes tonight.* | R1 | `only` compared to an expectation |
| *Only 25 minutes in the window.* | **passes** | Same word, a true constraint. Flags, ships — the lint working correctly |
| *Four hours left on the eval.* | L4 | The forbidden number |
| *That's enough for today.* | R1 | A verdict on the day |
| *You're on a roll.* | L4 | A streak in prose |

---

## 11. Build order

**Fallback template first, not last.**

A deterministic baseline the copy model has to beat is how you avoid paying for warmth you
cannot measure. Build it, run on it for a few days, and you will have an honest
sense of what is actually missing before writing a single prompt.

If the copy model cannot beat `{duration} on {title}.`, the API dependency has not earned
its place.

The skeleton — fixed slots, the copy model filling tone within them — is what makes the
comparison possible at all. Free-form copy means a bad card cannot be diagnosed:
no way to tell bad wording from a bad underlying decision.

---

## 12. Open items

| # | Item | Notes |
|---|---|---|
| 1 | Deadline-clause window `N` | The dosage dial. Placeholder chosen during the build — affects one line of copy, not a data shape, so it is cheap to change once it has been seen firing |
| 2 | Quiet-reason trigger numbers | All provisional. Calibrate off recorded reactions |
| 3 | Baseline start date | Begins after the first full week without a code change |
