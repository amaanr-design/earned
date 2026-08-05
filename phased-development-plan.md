# Phased development plan — Earned

Per Marc's feedback: this follows the Lesson 2 process (spec → tickets → parallel waves → review), applied to my own project rather than Smart Inbox. Sessions kept short and focused, commit at every working checkpoint, GitHub set up before any code.

Input to this plan: `blueprint.md` (v2, updated with the heartbeat and user.md revisions).

---

## Phase 0 — Repo setup
**One short session.**
- GitHub repo created, private, initialized with a README pointing at the blueprint.
- Claude Code scaffolds the project skeleton (React + Vite PWA / FastAPI / SQLite / svcs) — same stack as Smart Inbox, deliberately, per L-boring-and-popular from Lesson 1.
- `.env` + `.gitignore` from the start. `.worktreeinclude` added even though I'm not running Conductor yet — costs nothing now, saves a scramble later if I parallelize.
- First commit: empty scaffold running locally.

**Gate:** app boots, shows a blank page, git history exists.

---

## Phase 1 — Spec interrogation (Lesson 2, Part 1)
**One or two sessions, advisor model in chat — not Claude Code.**
- Feed the advisor `blueprint.md` directly and ask it to interrogate me the way I was interrogated to produce it — but now at spec granularity: exact data shapes, exact API contract, the deterministic/AI split from §7 turned into function signatures, edge cases (empty Sunday intake, a day with zero cards, what a receipt looks like on a day nothing happened).
- Explicit non-goals carried over from the blueprint so the spec doesn't quietly regrow scope: no auth in v1, no push in week one, no agentic intake yet.
- Output: `/spec/spec.md` and `/spec/api.md`, committed.

**Gate:** a stranger could read the spec and tell whether a given build is done and right — same bar as Lesson 2.

---

## Phase 2 — Tickets, week-one scope only
**One session.**
Per the blueprint's §14 week-one scope: Sunday intake, one rule-selected card, start/not-now/done, leisure pre-commit, receipt. No push, no auth, no learning yet — those are later phases, not later tickets within this one.

Rough ticket shape (finalized by the advisor against the actual spec, not decided here):
- **T1 — data layer**: tasks/commitments table, receipt log, pre-commit log
- **T2 — intake parser**: reuse the Smart Inbox parser pattern, adapted to commitments with categories/deadlines
- **T3 — card selection**: deterministic rule (nearest deadline × fits window × category overdue) — no LLM, per §7
- **T4 — card copy**: Flash-tier wording, eval-tested per §13
- **T5 — frontend**: intake box, single-card view, three-button response, pre-commit prompt, receipt view — no deficit column, enforced as an actual test assertion per §13
- **T6 — guardrails**: wire tests + eval into the run command, all green end to end

CLAUDE.md written before any ticket starts (Lesson 2, Part 3) — stack, commands, the no-deficit-column rule stated explicitly so no worker quietly adds one back.

**Gate:** every ticket has acceptance criteria and a named guardrail; dependencies mapped into waves.

---

## Phase 3 — Build, week one
**Several short sessions — this is deliberately not parallelized yet.**
Week one is small enough that spinning up multiple worktrees is its own overhead (Lesson 2's own warning: "reaching for the whole machinery on small work is its own kind of vibe-coding"). Build T1→T6 roughly in order, commit at each green checkpoint, run the full test suite before calling anything done.

By the end of this phase: something ugly, running on SQLite, that I open and use on my actual week — not a demo.

**Gate:** I've used it for real, on a real week, before moving on. This is the one non-negotiable gate in the whole plan — nothing in Phase 4 starts until this one is genuinely true, per the blueprint's own warning about the project becoming the procrastination.

---

## Phase 4 — v1: heartbeat, calendar, profile
**This is where parallel waves start earning their keep — 3+ independent pieces.**
- **Heartbeat job** (replaces the fixed-time push from the original blueprint): scheduled backend process, loose interval, silence-by-default, wakes the card logic only when conditions are actually right.
- **Google Calendar OAuth** as a second intake source alongside manual paste.
- **`user.md` profile**: the weekly synthesis job starts writing curated, durable notes about me — motivators, unreliable time blocks, re-entry patterns — read back in on every card generation.
- **Weekly pattern view** (CUJ-5).

These three are close to independent (heartbeat scheduling, calendar OAuth, profile writing) — a reasonable candidate for actual parallel worktrees per Lesson 2, Part 4, once each has its own ticket and contract.

**Gate:** the card shows up without a fixed clock time and without nagging; a week of real use produces a `user.md` I'd recognize as accurate.

---

## Phase 5 — First real product eval
**Not a coding phase — a measurement one.**
Per blueprint §13: does narrated earned-ness change anything without enforcement. By this point there should be enough weeks of receipts and pre-commits to look at card acceptance rate, completion rate, estimate-vs-actual convergence, and the "did tonight feel earned" tap.

This is the checkpoint where I find out if the central bet paid off, and it's the thing worth actually bringing to Marc and my aunt — not a feature list.

---

## Later (v2 and beyond — not scheduled yet)
Agentic Sunday intake (multi-turn interview), GitHub commits as a signal, published-user onboarding, auth, fitness stakes (still unsolved), optional Mac agent for Screen Time.

---

## Standing rules for every phase
- Short, focused sessions — stop and commit rather than let one session sprawl across unrelated tickets.
- Commit at every green checkpoint (Lesson 1, Part 2 habit).
- Full test suite run before anything is called done (CLAUDE.md rule, Lesson 2).
- No deficit column, ever — checked by an actual test, not just a design intention.
- If a worker (or I) hit a question the spec can't answer, that's a spec bug — fix the spec, not the code, then continue (Lesson 2, Part 5).
