# spec/spec.md §3 — single module, imported everywhere, never re-typed inline.

CATEGORIES = ("coursework", "marc_lessons", "build")
STAKES = ("high", "ordinary")
STAKES_MULTIPLIER = {"high": 2, "ordinary": 1}

ROLLOVER_HOUR = 4  # local hour; the day boundary is the rollover, not midnight

SLICE_FLOOR_MINUTES = 25
SLICE_CEILING_MINUTES = 120
DAILY_CARD_CAP = 3

# spec/spec.md OPEN-12 — week-one starting rule, no calibration history yet.
# Anchored on the number decisions.md §3 says calibration eventually converges
# toward ("offer 120, consistently do 40 -> start offering ~45"), rather than
# starting at the ceiling and walking down. Confirmed with the user 2026-09.
SLICE_STARTING_ANCHOR_MINUTES = 45

# spec/api.md §4, OPEN-20 — precommit options are generated around the
# offered duration, not clamped to the offer floor: 25 is the minimum the
# app will *offer*, not the minimum the user is allowed to *commit* to.
# Clamping here would corrupt the estimate-vs-actual data. Confirmed with
# the user 2026-09.
PRECOMMIT_DELTAS_MINUTES = (-15, 0, 15, 30)
PRECOMMIT_FLOOR_MINUTES = 10
PRECOMMIT_CEILING_MINUTES = 120

# copy-spec.md §6, case 15 — fixed wording, not a model output.
PRECOMMIT_PROMPT = "How long are you giving it?"

QUIET_REASONS = (
    "evening_started",
    "window_under_floor",
    "everything_closed",
    "nothing_due",
    "cap_reached",
    "after_not_now",
)
