// copy-spec.md §5 — quiet-reason lines. Fixed, small, auditable set: no
// variants, no rotation. The server returns the reason; this is the shared
// client constant module that renders the sentence (spec/api.md §3, AC-G2).

export const QUIET_REASON_TEXT = {
  evening_started: "The evening's already started.",
  window_under_floor: 'Not enough time for a proper go at anything.',
  everything_closed: "That's everything closed. Enjoy tonight.",
  nothing_due: 'Nothing due tonight.',
  cap_reached: "That's the day.",
  after_not_now: 'Nothing else right now.',
}
