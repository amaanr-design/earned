# Blueprint — working title: *Earned*

**Status:** pre-spec. This is the input to the Lesson 2 spec-driven process, not the spec itself.
**Author:** Amaan · **Date:** 29 July 2026

---

## 1. Goal

**Make leisure feel earned.**

Not less gaming. Not more studying. The *quality* of the hours already being spent.

The premise: the leisure happens either way. A system that tries to prevent it loses, gets routed around, and gets deleted. A system that changes whether those hours land as *clean* or *guilty* is competing for something it can actually win.

Everything below is downstream of that sentence.

---

## 2. The user

**Primary (me):** has a plan and isn't executing it. Not overloaded, not disorganised, not short of ideas. The gap is entirely between decided and done.

**Published user:** the same person. Someone with a plan they're not executing.

**Explicitly not for:** people who don't know what they want yet, people drowning in obligations who need triage, teams, professionals with packed calendars.

That cut kills a lot of work: no goal-setting wizard, no values exercise, no coaching onboarding, no priority framework. Onboarding's only job is to get an *existing* plan in fast and start the same day.

---

## 3. Failure mechanisms this is built against

Ranked from my own history, not from a persona doc.

1. **Initiation** — the task is clear, I can't start. Happens at home, at the computer.
2. **Absorption** — a session swallows the evening.
3. **No stakes until it's on fire** — nothing moves until a deadline burns.
4. **Ambiguity in the moment** — present but least severe.

**Death causes of previous systems:**
- Google Calendar sectioned into study/gym blocks → notifications ignored within days. It showed only obligations; leisure filled the gaps invisibly, so the day always looked like a bill.
- Apple Reminders → degraded to bin-day reminders. No fun, no pull.
- Common thread: **nothing happened when I ignored them.**

---

## 4. Design laws

Non-negotiable. Every feature gets checked against these.

| # | Law | Why |
|---|-----|-----|
| L1 | **Never gate. Only colour.** The app has zero authority over leisure. It cannot withhold, block, or unlock anything. | Any system that ends or blocks a session gets deleted within a week. Stated flat out. |
| L2 | **One leverage point: the boundary.** It speaks *before* a session and *after* one. Never during. | Interruption mid-flow is the delete trigger. |
| L3 | **Praise on delivery, silence on failure.** Absence of acknowledgement is the only negative signal it ever sends. | I don't respond to being scolded. Silence is felt without being reprimanded. |
| L4 | **No streaks. No deficit column. Ever.** Trend, not compliance. | See §5 — this is evidence-backed, not taste. |
| L5 | **Same night no judgment; over months honest mirror.** | Aggregate patterns are information. Same-night verdicts are shame. |
| L6 | **Teeth come from humans, not software.** The app never scolds. Reality does. | The one accountability mechanism with a proven track record in my life is my aunt checking in. |
| L7 | **Self-report is the foundation; observation is enrichment.** Core loop must work with zero permissions granted. | Required for publishing (§9). Also happens to be honest, since I don't lie to it. |

---

## 5. What the research says

**The category exists and every player breaks L1.** Achieve!, LockedIn, BePresent, Fluid Focus all sell "earn your screen time" — and all implement it as *app blocking you unlock with coins*. BePresent adds streaks, leaderboards, a monetary stake, and a "BEAST MODE." Every one of those is on my delete list. **Same emotional promise, opposite mechanism. That's the position.**

**Streaks are actively harmful.** The "what-the-hell effect" — once a streak breaks, users quit entirely. The abstinence violation effect (Marlatt & Gordon): one slip triggers full abandonment when the system treats it as proof of failure. A JMIR scoping review found up to 72% of users disengage from lifestyle/mental-health apps within 90 days. Worst of all: users do *degraded* versions of a habit to protect a streak — the streak survives, the habit dies. → L4.

**The "one card" space is aimed at the wrong person.** Sunsama = a 10–15 minute daily planning ritual (too much overhead, dies fast). Motion = full auto-schedule, but users report fighting the algorithm and losing agency. Both assume tasks are already captured and both serve the *overloaded*. Nobody serves "has a plan, isn't moving." Narrow slot, defensible.

**The uncomfortable one.** Earned leisure has real evidence — Milkman, Minson & Volpp (2014) found a 51% increase in gym visits from temptation bundling; Kirgios et al. (2020) found 10–14% higher weekly workout odds at 17 weeks post-intervention. Underneath sits Premack's principle. **But the effect came from enforced restriction** — the audiobooks physically lived at the gym. L1 removes the restriction.

→ **The central bet of this product: that *narrating* earned-ness reproduces some fraction of an effect measured under enforcement.** This is untested. It might be small. It might be nothing. It is the thing the first eval must measure (§12).

---

## 6. Core loop / CUJs

### CUJ-1 · Sunday intake (weekly, ~5 min, high friction, user-initiated)
Paste the plan, brain-dump the week, or connect a calendar. The app turns it into structured commitments with categories and deadlines.
*This is the Smart Inbox parser, reused.*

### CUJ-2 · The card (daily, ~5 sec, zero friction, app-initiated)
One thing. Not a list. Sized to the time actually available, chosen for what's nearest to burning.
> *"45 minutes on the eval, then the lads are on at 9."*
Three responses: **start** · **not now** · **done**. "Not now" is free and costs nothing — no guilt copy, no follow-up nag.

### CUJ-3 · The pre-commit (evening, ~3 sec, zero friction)
Same interaction as the card. *And what's the plan after?* One tap for intended session length. **No enforcement whatsoever.** It exists for two reasons: the act of saying it out loud, and — structurally — it is how the app generates estimate-vs-actual data (§11).

### CUJ-4 · The receipt (end of day, ~10 sec, passive)
What got banked today. What the evening sat on top of. One optional binary tap: *did tonight feel earned?* — that single field is the primary outcome measure for §12.
**Contains no deficit column.** Shows what was done, never what was owed.

### CUJ-5 · The weekly pattern (Sunday, ~2 min, passive)
Three sentences a human would actually say, plus the trend. Explicitly designed to be **shown to my aunt / mentioned to Marc** — the artefact that makes a human check-in sharper.

**Friction/proactivity summary:**

| Feature | Friction | Proactivity |
|---|---|---|
| Sunday intake | High (deliberate) | Reminder only |
| The card | Near-zero | **Proactive push** |
| Pre-commit | Near-zero | Bundled with card |
| Receipt | Zero (passive) | Passive, no push |
| Weekly pattern | Zero (passive) | Gentle Sunday nudge |

---

## 7. Deterministic vs AI

The most important table in this document. Most of what looks like "AI learning you" is arithmetic.

### Deterministic — no LLM, ever
- Did the card get completed (boolean from a tap)
- Completion rate by time-of-day, by category
- Estimated vs actual duration (medians, drift)
- Days-until-deadline arithmetic
- **Card *selection*** — rule-based: nearest deadline × fits available window × category overdue
- Rolling trend (no streaks)
- Whether and when to push (threshold rules + cron)
- Receipt contents (aggregation)

### AI — LLM does the language, not the logic
- **Sunday intake parsing** — messy plan → structured commitments *(= the Smart Inbox parser)*
- **Card copy** — writing the one sentence, in my register, naming the specific reward waiting
- **Weekly synthesis** — numbers → three human sentences
- Optional: classifying calendar events into categories

**The key separation: selection is deterministic, wording is AI.** Selection stays predictable, debuggable, free, and testable with normal unit tests. Wording gets warmth and variety and is eval-tested. If the card ever picks the wrong thing, that's a bug with a stack trace, not a prompt to tune.

---

## 8. Agentic flows

**v1: none.** Deliberately.

An autonomous multi-step agent acting on my day has an asymmetric downside here — one badly-timed or wrong autonomous action produces exactly the annoyance that gets the app deleted (L1, L2). The nightly "what to push" job is a *scheduled deterministic job*, not an agent, and calling it one would be dressing up a cron.

**The one place agentic earns its keep later:** the Sunday intake as a **multi-turn interview** rather than a single parse — the app grilling me the way this blueprint got produced. Genuinely agentic, genuinely valuable, and it doubles as the onboarding solution for published users (§2: get an existing plan in fast). Ship it as v2 once the deterministic core is proven.

---

## 9. Signal layer — pluggable, never load-bearing

The core loop must work with **zero permissions granted**. Signals are enrichment that make it sharper for whoever grants them.

| Signal | Availability | v1? |
|---|---|---|
| Self-report (taps) | Everyone, always | ✅ Foundation |
| Google Calendar (OAuth) | Everyone, cross-platform | ✅ |
| GitHub commits | Everyone, no permission theatre; good work proxy for me | v1.5 |
| macOS Screen Time (`knowledgeC.db`) | Me only — needs Full Disk Access, native agent | Optional later |
| iOS Screen Time | Effectively unavailable | ❌ |

**Why the bottom two are out.** macOS Screen Time is readable from a local SQLite DB but requires Full Disk Access granted manually in System Settings — fine for me, a brutal onboarding ask for a stranger, and impossible from a web app. iOS requires the `com.apple.developer.family-controls` entitlement (manual Apple approval, days to weeks) and returns **opaque tokens** — you can shield an app but can never learn which apps the user has. "You spent four hours in Steam" is not obtainable on iOS by any published app.

Designing signals as pluggable satisfies Marc's warning about retrofitting: I'm just a user with every switch on.

---

## 10. Surface & architecture

**PWA.** Installable on Windows (Chrome/Edge), macOS, and iPhone. Convertible to native later.

**Device mapping:**

| Moment | Device | Why |
|---|---|---|
| Card + pre-commit | **Windows desktop** | This is where the gaming happens. The boundary is a literal machine switch — exploit it. |
| Receipt | iPhone | End of day, away from the desk |
| Sunday intake + weekly pattern | Mac | Sit-down, deliberate |

**The one architectural consequence.** iOS gives PWAs **no background execution** — no Background Sync, no Periodic Background Sync, no Background Fetch, no timeline for any of them. The app cannot wake itself up at 7:58pm. **Every proactive moment must be a server-scheduled push.** The "when to speak" logic lives in the backend; the client is a thin surface. Design this in from day one.

**Revised per Marc's feedback — heartbeat, not fixed times.** Originally scoped as a scheduled push at a set time (e.g. 7:58pm). Marc pointed at OpenClaw's heartbeat pattern: a lightweight job wakes on a loose interval (every 30–60 min, or staggered), checks a short list of conditions, and stays silent unless something genuinely warrants surfacing — cron is for exact times, heartbeat is for "check often, speak rarely." This fits better: gaming doesn't start at a fixed time, and a rigid push risks becoming the next ignored Google Calendar notification. The card should surface when conditions are actually right — desktop active, evening underway, a card still pending — not on a clock. Silence criteria matter as much as the check itself (L2, L3: never interrupt, never nag).

**iOS push caveats:** only works once installed to the Home Screen (a Safari tab cannot receive push, regardless of permission), permission prompt must follow a direct tap — so onboarding must sequence *install → then ask*. Delivery ~70–85% vs 90–95% on Android, and Safari may clear service-worker state after long inactivity. **Never make push the only path to the card.** PWAs also can't use Time Sensitive notifications that break through Focus Mode — which L2 would have ruled out anyway.

**Publishing note:** Apple removed standalone PWA support in the **EU** under the DMA (iOS 17.4) — EU users get a Safari tab with no push. Irrelevant to me; relevant the day a European signs up.

**Stack:** React + Vite (PWA) · FastAPI + scheduler · SQLite → Postgres · svcs for services. Same as Lessons 1–2, deliberately — boring and AI-fluent.

---

## 11. Recursive learning

What it should know in month three that it didn't in week one:

1. **Time-of-day reliability** — which blocks actually get executed. *"You never do the 9am block. Stop offering it."*
2. **Duration calibration** — says 45, does 20 → starts offering 25, because those finish.
3. **Friction by category** — some work starts easily, some never starts. Those need smaller cards, earlier slots.
4. **Motivator inventory** — what's actually pulling. For me: a new game, or friends online. The card names the *specific* reward waiting, not a generic one.
5. **Re-entry** ← *highest value, nobody does this well.* With no streaks, the app's real skill is **the restart after five dead days.** What card, at what time, brought me back last time?
6. **Fire proximity** — learns I engage three days before a deadline, starts surfacing it at four, then five. Walks the fuse backwards over months.

**Structural requirement:** all of this needs a record of **prediction vs outcome**. That is what promotes the pre-commit from a nice-to-have to load-bearing infrastructure. Said 45 on the eval → did 20 → one training row. Without it, the app has outcomes with nothing to compare them against and can never learn anything sharper than "he was active Tuesday."

**Revised per Marc's feedback — a `user.md`, not just raw tables.** Marc pointed at OpenClaw's memory model: a small, curated, durable profile file the agent reads every session and occasionally rewrites, kept separate from the raw daily log underneath it. Applying that here — instead of the card-copy LLM re-deriving patterns from raw event tables on every call, maintain an actual `user.md`: a short, plain-text profile —
> *"Responds to gaming-with-friends as a named reward. Rarely completes 9am blocks — avoid. Needs re-entry cards under 20 minutes after a gap of 3+ days."*

The **weekly synthesis job (§12, Pro tier)** is what updates it — small, deliberate edits each week, not an ever-growing diary. Raw taps and receipts stay underneath as the log; `user.md` stays small and high-signal because it gets read on every card generation. This is a cleaner split of the deterministic/AI line in §7: the *facts* (completion rates, durations) are still deterministic arithmetic; `user.md` is the AI's curated *summary* of those facts, and it's what actually gets injected into the Flash prompt for card copy.

---

## 12. Model tiering

Marc's steer: Gemini for everything non-coding — much cheaper, strong at this class of work. *(Check current model names before building; the tier matters more than the version.)*

| Job | Tier | Rationale |
|---|---|---|
| Card copy | **Flash** | One sentence, high frequency, latency-sensitive, low stakes |
| Intake parsing | **Flash** | Structured extraction; eval-tested; the Smart Inbox pattern |
| Weekly synthesis | **Pro** | Once a week, needs actual judgment across a month of data |
| Eval judge | **Pro** | LLM-as-judge from Lesson 1, spot-checked |
| Everything in §7 deterministic | **No model** | It's arithmetic |

Running the top tier on the card would be slow, expensive, and no better.

---

## 13. Guardrails & the first eval

**Tests (deterministic):** card selection given a fixed state, duration maths, deadline arithmetic, "no deficit column" as an actual assertion — a test that fails if any view renders an owed/missed figure. That last one is a design law encoded as a test, which is the right way to keep a law alive under an agent.

**Eval (the AI parts):** intake parsing (reuse the Lesson 1 eval set), and card copy scored on: does it name a specific action, is it sized to the window, does it name the real reward, is it free of scolding.

**The product eval — the one that matters.** Central hypothesis: *does narrated earned-ness change behaviour without enforcement?* (§5)

Measured on myself, over weeks:
- Card acceptance rate (does it get tapped)
- Completion rate of accepted cards
- Estimate-vs-actual convergence over time
- Do banked days cluster — does a banked day predict the next
- **"Did tonight feel earned?"** — the single binary tap on the receipt, the closest direct measure of the goal in §1

If this comes back flat after a month, the honest answer is that the bet didn't pay and the design needs enforcement it can't have — which is worth knowing, and is a better outcome than shipping something pretty and never checking.

---

## 14. Scope

**Week one — must be running on my real life, not just built.**
Sunday intake (paste → parse) · one rule-selected card on a page I open · start/not-now/done · leisure pre-commit · receipt. SQLite, no auth, no push, no learning. Ugly is fine.

**v1** — push (Windows first), calendar OAuth, weekly pattern, the trend view, real evals.

**v2** — the interview-style intake (§8), GitHub signal, published onboarding, multi-user auth.

**Later / maybe never** — Mac agent for Screen Time, native wrappers, anything social.

**The trap to name out loud:** building this can easily *become* the procrastination. Six weeks of satisfying work on a thing that never meets a Tuesday. Hence week-one scope. **The most impressive possible outcome is not the architecture — it's "I've run it for three weeks, here's what it caught."**

---

## 15. Open questions

- **Name.** *Earned* is a placeholder.
- Does this become the hackathon project, or stay separate?
- Sunday intake: how much can be inferred from calendar vs asked directly?
- Where does fitness fit? It's the one goal with **no real deadline** — coursework and Marc's checkpoints have genuine fires, fitness has none. It may need a manufactured stake, and that's the hardest unsolved piece here.
- Published-user accountability: my aunt is a real person. What's the equivalent for a stranger — nothing, an export, or a genuine invite-a-human feature?
