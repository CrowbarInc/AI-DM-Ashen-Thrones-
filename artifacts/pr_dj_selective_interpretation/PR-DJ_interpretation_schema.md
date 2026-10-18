# PR-DJ Interpretation Schema

Allowed statuses: `INTERPRETED`, `CLARIFICATION_REQUIRED`, `UNSUPPORTED_REQUEST`, `MULTI_ACTION`, `ABSTAIN`.

Allowed fields:

- `interpreted_intent`
- `referenced_entities`
- `unresolved_references`
- `multiple_action_components`
- `clarification_required`
- `clarification_question`
- `unsupported_action`
- `uncertainty`
- `non_authoritative_explanation`
- proposal fields accepted by `game.interpretation_proposal`

Forbidden fields include authoritative outcomes, dice results, HP changes, inventory mutations, world flags, hidden facts, resolver names, and execution authorization. The adapter rejects unknown top-level fields so accidental authority expansion fails closed.
