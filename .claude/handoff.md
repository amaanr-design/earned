# Earned — Handoff

Update the "Last session" block at the end of every session. Keep it short —
this is a pointer, not a log. Full reasoning lives in `decisions.md`.

---

## Where things stand

**Phase 0 — scaffold:** done. React + Vite PWA / FastAPI / SQLite / svcs.
Repo private on GitHub, git identity configured locally.

**Phase 1 — spec interrogation:** done. All entity, selection, lifecycle, and
API contract decisions locked in `decisions.md`. Nothing here is provisional
unless marked OPEN in that file.

**Card + receipt copy:** done. All 21 cases written and reviewed in
`copy-spec.md`. Governing rules, skeleton, and instrumentation locked there.

**Spec documents:** done. `spec/spec.md` and `spec/api.md` written — Phase 1's
stated output, two documents as planned. Pure transcription; no new design.

**Next:** tickets. T1–T6 confirmed against the spec with acceptance criteria
attached, then week-one build.

## Load-bearing decisions (see decisions.md for full reasoning)

- Commitment holds total effort; card is a time-bounded slice
- Tap A = session logged, Tap B = commitment closed
- `remaining_effort` stored, **never** returned by API or rendered — this is
  a hard rule, not a style preference
- Selection is deterministic: `score = (effort_remaining / days_remaining) *
  stakes_multiplier`. No LLM in the selection path, ever.
- Categories: `coursework`, `marc_lessons`, `build` — closed enum, exactly 3
- Stakes: `high` / `ordinary` — exactly 2 levels
- Slice window: floor 25 min, ceiling 120 min, sized to evening-start field
- Cards persisted at offer time, not computed on read
- Outcome buckets: `never_touched`, `not_now`, `completed`,
  `abandoned_unknown`, `done_no_start`
- No warnings, no scolds, no deficit figures anywhere in the UI, ever
- Multi-user schema from day one (user_id everywhere), auth deferred to v2
- Fitness deferred to v1.5 via count/recurrence model — schema fields
  (`target_count`, recurrence) reserved now, feature built later
- Copy is governed by two rules only (`copy-spec.md` §1): fact-not-evaluation,
  and scope. Everything else about wording is downstream of those.
- Copy generated at card-write time, 3s timeout, fallback text stored
  permanently on timeout. Read is always a database read.
- Pre-commit estimates the **work**, not the leisure — a work estimate has a
  measurable actual
- `blueprint.md` is superseded by `decisions.md` and `copy-spec.md` where they
  conflict; it carries a precedence header saying so

## Open items — do not resolve by guessing

The full list, numbered and with blocking status, is `spec/spec.md` §15 —
19 items, 13 of which block week-one code. Headlines:

- **Deliberately unset, still unset:** neglect-nudge multiplier · deadline-clause
  window `N` · quiet-reason trigger thresholds · instrumentation baseline (starts
  after the first full week without a code change)
- **Newly surfaced by the spec, and blocking:** `days_remaining` on the deadline
  day (divides by zero) · a commitment whose effort runs out without Tap B
  (completion by exhaustion through the back door) · score ties · how a reward
  attaches to tonight · what triggers an offer in week one with no push · what
  counts against the 3/day cap · where Tap B is tapped · whether
  `done_no_start` banks effort · the slice-sizing function · re-offer size and
  interval · quiet-reason precedence
- Five of the blockers land inside ticket T3 alone — that ticket is bigger than
  the plan's sketch suggests
- **Target date for "a real Tuesday" — still not set. Pick it.** Oldest open
  item in the project.

## Corrections carried into the tickets session

- **T3** in `phased-development-plan.md` still names the old selection rule
  ("nearest deadline × fits window × category overdue"). Superseded by
  `stakes × urgency`. Category plays no part in selection.
- **T4** names Flash. `copy-spec.md` deliberately names no product — "the copy
  model", binding in build config. The product name does not belong in a ticket.

## Reward list (for copy work)

Pro Clubs w/ Michael & Braden · Overwatch w/ Shaan · single-player gaming
night · movie night · night out w/ family or friends. See `decisions.md` §
Reward list for the social-vs-solo copy note.

---

## Last session

**Date:** 2026-08-13
**Did:** Closed Phase 1 spec interrogation (entities, selection algorithm,
lifecycle, API contract). Wrote `decisions.md`. Sent Marc an 8-day recap.
Folded in Marc's counted-commitment idea for fitness.
**Next session should:** Start card + receipt copy in a fresh chat, using
`decisions.md` + `blueprint.md` as input. Update this file afterward with
whatever copy patterns get locked.

## Last session

**Date:** 2026-08-18
**Did:** Card + receipt copy, start to finish. `copy-spec.md` written, reviewed
case by case, and locked — 12 sections, all 21 cases. Two governing rules
(fact-not-evaluation; scope). Skeleton: every slot's presence decided
deterministically, copy model only fills what it is handed; titles and rewards
verbatim. Boundary slot (`evening_start`) added as a true non-invented reward so
week-one cards aren't to-do items — once a day, first card only. Receipt body is
a list with no count preamble; zero day is the same frame with an empty list and
no compensating line. Earned question moved to the frozen receipt, retrospective,
dismissible, `seen_dismissed` stored distinctly. Pre-commit resolved to estimate
work, not leisure. Copy generated at card-write time with a 3s timeout and
permanent fallback. New instrumentation section: quiet-reason counts, wallpaper
trigger, fallback rate, and an explicit guard against treating opens as an
engagement metric. `blueprint.md` given a precedence header rather than being
amended. Spec is model-agnostic throughout — "the copy model", not a product
name.
**Next session should:** Write the spec document proper. `copy-spec.md` feeds T4
(card copy) and T5 (frontend) directly; its rejected-variants table is most of
the card-copy eval from blueprint §13 already written. Fallback template is
built first — the copy model has to beat it.
**Open:** nothing blocks code. Trigger thresholds and the deadline window `N`
are calibrate-later. The real Tuesday is still unpicked, and that is now the
oldest open item in the project.

## Last session

**Date:** 2026-08-20
**Did:** `spec/spec.md` and `spec/api.md`, transcribed from `decisions.md` and
`copy-spec.md`. Spec: seven tables with field-by-field notes and running SQLite
DDL (`effort_remaining` as a generated stored column, so it cannot drift and
cannot be hand-maintained wrong), constants module, selection, card lifecycle,
copy pipeline, receipt rules, instrumentation, and 15 system-level guardrail
assertions. API: 13 week-one endpoints with request/response shapes and numbered
acceptance criteria each, plus seven global ones. Every rendered string in both
documents traces verbatim to `copy-spec.md`. Two audit sections added on
purpose — §14 lists all ten places the spec put something into words the sources
did not use, and §15 lists the open items with blocking status, so neither
category can be inherited silently.
**Next session should:** Tickets. Confirm T1–T6 against the spec and attach
acceptance criteria — the structure is already sketched in the plan, so this is
confirmation, not invention. Carry the T3 and T4 corrections above. Note that
five week-one blockers sit inside T3, which may want splitting.
**Open:** the previous entry's "nothing blocks code" no longer holds. Thirteen
open items block week-one code — mostly small arithmetic and lifecycle edges the
design documents did not need to reach, but the selector cannot be written until
the `days_remaining` and exhausted-effort ones are settled. Still no real
Tuesday.

## Last session

**Date:** 2026-09-15
**Did:** Built the commitment table + manual add-commitment form (T1 slice),
the selection function (`app/selection.py`), and `GET /api/card`
(`app/cards.py`) — slice sizing, quiet-reason responses, card persistence at
offer time, deterministic fallback-only copy (no model call anywhere; verified
by test). 27 tests passing. Resolved five open items, each checked against the
user before implementation, all recorded in `spec/spec.md` with reasoning:
- **OPEN-2** — past-deadline commitments expire and drop out of scoring
  entirely; the deadline day itself floors `days_remaining` at 1.
- **OPEN-12** — week-one slice size = `min(45, window, effort_remaining)`,
  floored at 25, never rounded up. 45 is decisions.md's own calibration target.
- **OPEN-13** — re-offer after a decline is immediate (no cooldown — the app
  never pushes) and halves the prior declined duration for the same
  commitment; under-floor yields `after_not_now` per the already-locked
  AC-CARD-12.
- **OPEN-8** — every card row for today's rollover day counts against the cap,
  regardless of outcome.
- **OPEN-14** — quiet-reason precedence: `cap_reached` checked first.

Also settled an undocumented ambiguity (`spec/spec.md` D11): `everything_closed`
requires a Tap B within the current Sunday-based week; otherwise `nothing_due`,
so a returning user who never did intake isn't congratulated for an empty week.
**Next session should:** Tap A/B and not-now endpoints (start, precommit,
not-now, done, resolve — T5), then the receipt (T5). OPEN-9 (where Tap B is
tapped) needs a UI answer, not just an endpoint, before that lands. OPEN-4 and
OPEN-5 are the two open items left inside T3's original scope.
**Open:** eight items still block week-one code — OPEN-4, 5, 6, 7, 9, 11, 17,
19. Still no real Tuesday.

## Last session

**Date:** 2026-09-16
**Did:** Built the card screen (`frontend/src/CardScreen.jsx`) — calls
`GET /api/card`, renders the card's `copy_text` or the matching quiet line
(`frontend/src/quietReasons.js`, byte-identical to `copy-spec.md` §5), Start,
the precommit chooser, and Done (Tap A). Start and Done didn't exist on the
backend yet, so built those too, plus precommit, since the screen needed all
three end to end:
- `POST /api/cards/{id}/start`, `POST /api/cards/{id}/precommit`,
  `POST /api/cards/{id}/done` (`backend/app/cards.py`, `backend/app/main.py`)
- `backend/app/errors.py` — shared `ApiError` for the `{error:{code,message,field}}`
  shape, wired as a FastAPI exception handler
- 15 new tests in `backend/tests/test_cards.py`; 38 passing total

Resolved **OPEN-20** (new): the precommit option-generation function was
unwritten, and the spec's own example (`[20,30,45,60]` for a 45-min offer)
silently broke its own AC-START-5. Checked with the user: options are
`{offered-15, offered, offered+15, offered+30}`, deduped, clamped to
`[10, 120]` — **not** the 25-minute offer floor, since a commitment estimate
is allowed to be honestly lower than what the app would offer; clamping to
the offer floor would corrupt the estimate-vs-actual data. AC-START-5 amended
in `spec/api.md`, OPEN-20 added to `spec/spec.md` §15.

Also resolved, by extension of the already-locked "no duration is ever
invented" rule rather than by fresh guess: `done_no_start` banks nothing,
since there is no real number to bank.

**Verification:** full pytest suite, all three endpoints over real HTTP
(curl), and the Start→precommit→Done sequence via direct service calls.
Browser-verified the quiet-line path and the Done/Tap A path end to end
(started card → Done → banks elapsed effort → refetches to the correct
quiet line). **Could not** browser-verify the initial "offered card → Start
button" screen live — the sandbox's real clock was past midnight, and the
app's own rollover-day logic correctly treats that as evening-already-started
for any `evening_start`, so a genuinely offered card wasn't reachable through
the real endpoint at test time. Covered by the backend test suite instead.
**Next session should:** Not-now endpoint and button (T5) — the card screen
currently only has Start and Done, per this session's explicit scope. Then
`resolve` (the `abandoned_unknown` ask) and the receipt (T5). OPEN-9 (where
Tap B is tapped) still needs a UI answer.
**Open:** OPEN-4, 5, 6, 7, 9, 11, 17, 19 still block week-one code. OPEN-20 is
newly resolved and no longer in that count. Still no real Tuesday.

## Last session

**Date:** 2026-11-09
**Did:** (Catch-up: commit `465a602`, 2026-09-17, added `POST
/api/cards/{id}/not-now` and the Not now button — that session didn't update
this file.) Made the frontend an installable PWA shell. Kept the scaffold's
`vite-plugin-pwa` (checked with the user — the alternative was hand-rolling
`manifest.json` + `sw.js`) and configured it in `frontend/vite.config.js`:
- manifest: `display: standalone`, 192 + 512 icons (512 also `maskable`),
  theme/background `#16171d`; emitted as `manifest.webmanifest`
- Workbox `generateSW`: precaches the shell only (js/css/html/png/svg),
  cache-first; `skipWaiting` + `clientsClaim` + `cleanupOutdatedCaches` so a
  stale worker never serves an old build; **no `runtimeCaching`** — API
  responses are never cached; `/api/` denied from the navigation fallback
- `base: '/earned/'` for GitHub Pages, applied to `build` and `preview` only;
  `npm run dev` still serves at `/`. No service worker in dev.
- Registration moved to `src/main.jsx` (`virtual:pwa-register`,
  `injectRegister: false`)
- Icons generated by `frontend/scripts/gen-icons.mjs` (no deps): accent "E" on
  dark background, plus a 180px `apple-touch-icon.png`. `index.html` title is
  now "Earned" and it has a `theme-color` meta tag.
- `.claude/launch.json` gained `frontend-preview` (port 4173; open `/earned/`).

**Verification:** `npm run build` and `npm run preview` with the backend running.
At `/earned/` the worker is active and controlling at scope `/earned/`. The
precache holds 10 shell paths and zero `/api` entries. On reload the document,
JS and CSS came from the worker with 0 bytes transferred, while `/api/card` went
to the network. No console errors. I didn't open the DevTools installability
panel itself.
**Not done, deliberately:** no deploy (backend host undecided); no offline
behaviour for cards (open design question). **Known gap for deploy:** the
frontend calls absolute `/api/...` paths, which resolve against the origin. On
Pages those requests would reach github.io, not the backend. An API base URL
has to be decided together with the backend host.
**Next session should:** `resolve` (the `abandoned_unknown` ask) and the
receipt (T5). OPEN-9 (where Tap B is tapped) still needs a UI answer.
**Open:** OPEN-4, 5, 6, 7, 9, 11, 17, 19 still block week-one code. Offline
card behaviour and backend hosting are new, undecided, and not yet numbered in
`spec/spec.md` §15. Still no real Tuesday.
