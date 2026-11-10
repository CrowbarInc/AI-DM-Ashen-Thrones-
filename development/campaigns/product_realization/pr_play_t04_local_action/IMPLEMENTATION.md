# Implementation

## Files

| File | Change |
|---|---|
| `game/local_interaction.py` | Added `resolve_transient_local_action` and its match, veto, authority, and narration helpers. `normalize_local_approach` is unchanged. |
| `game/conversational_orchestration.py` | `_local_presence_decision` consults the resolver for a unique local hit. `_transient_local_decision` wraps the record. Contact-only utterances are considered after committed movement returns none. |
| `game/api.py` | After the existing host-speech seal, a completed transient outcome whose sealed text still equals the authorized narration is marked successful, owned by `local_interaction`, stamped `FINAL_ENGINE_RESPONSE`, and recorded with `note_completed_publication`. |

`game/api.py` is involved because the conversational HTTP response returns before exploration. The seal and publication pointer already live in `_nonmutating_conversational_decision_response`. No new route was added.

## Action resolution

Eligible approach or contact becomes a conversational `ANSWER` with reason `transient_local_action_completed`, intent family `local_interaction`, and execution policy `record_transient_outcome`. The authorization payload is the transient record.

Ineligible utterances that still uniquely match a local object keep the previous decline. Utterances outside the class return none and keep travel, speech, inspection, or manipulation.

## Transient representation

The outcome is a dict on the decision authorization and, after the seal check, on `resolution.metadata.transient_local_action`. It does not write position, inventory, or scene state.

## Narration authorization

Narration is ordinary DM prose from the authorized parts only: approach, contact, or both, plus the current location sentence when the scene has a location. The publication step requires `narration_authorized`, no scene transition, no persistent change, and byte-for-byte equality with the sealed player-facing text. Scene-momentum appendages are not applied on this path.

## Immutable acceptance

The text still passes `seal_host_speech` before the success stamp. The T04 HTTP log records `immutable: true`, `hard_valid: true`, and authorization source `conversational_decision:transient_local_action_completed`. The accepted text, visible text, and publication pointer are the same sentence.
