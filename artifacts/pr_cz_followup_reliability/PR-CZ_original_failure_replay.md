# PR-CZ Original Failure Replay

PR-CY Turn 1:
- Player: Guard Captain, do you prefer standing watch in the rain, or somewhere dry?
- Resolver: social.
- Active interlocutor in provider context: guard_captain.
- Reduced context: selected.
- Validation: accepted first attempt.
- Final: Guard Captain answered with a dry-watch/rain-watch preference.

PR-CY Turn 2:
- Player: Does the rain make it harder to keep watch?
- Reduced context: not selected.
- Active interlocutor: null in the original provider context.
- Recent log: contained Turn 1.
- Initial candidate: rejected.
- Retry candidate: rejected as `unauthorized_resolution_decision_fact` with `unsupported_narrator_lead`.
- Final: Guard Captain says, "I cannot answer that from what is settled here."

The exact PR-CY retry candidate is preserved in `PR-CZ_provider_candidate_replay.md`.

