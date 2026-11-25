# Next step

Recommended next milestone: a separately authorized live validation of carried-object grounding. Do not start it from this handoff.

Scope, if authorized:

- Provider OpenAI, model `gpt-4.1-mini`.
- Four ordinary `/api/chat` interpretation calls: A1 volume, A2 follow-up, A3 prepared-spell question, and one two-book ambiguity control.
- Caps, timeout, retry policy, and the $0.06 ceiling are in `LIVE_VALIDATION_PLAN.md`.
- Leave the `uncertain_actionable_coverage` gate in place. Do not include A4 or B1.
- Do not resume `pr_play_social_check_repeat_and_legacy_stance`.

This milestone's deterministic repair is complete enough to justify that live check. It is not evidence that the live model now selects `spellbook`. If the authorized run still returns a null target, the host binding from this milestone is the expected safety net for a unique book. If it still asks which spellbook while the catalog contains exactly one, that is a new model-behavior finding and not a reason to invent a second book or to bypass admission.

No further production subsystem should start before that result. Combat, socialization, exploration, and inventory mechanics stay as they are.
