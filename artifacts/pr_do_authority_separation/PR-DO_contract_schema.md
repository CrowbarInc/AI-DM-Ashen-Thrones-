# PR-DO Contract Schema

The model may describe what the player is trying to do. The model may not decide that it happens.

Model-writable fields:

| Field | Role |
| --- | --- |
| `communication_mode` | `IN_WORLD_ACTION`, `OUT_OF_CHARACTER_CORRECTION`, `RULES_QUESTION`, `CLARIFICATION`, or `OTHER` |
| `interpretation_status` | `INTERPRETED`, `CLARIFICATION_REQUIRED`, `UNSUPPORTED_REQUEST`, or `ABSTAIN` |
| `player_intent.summary` | Descriptive text of the attempt |
| `asserted_premises[].text` | Facts the player claims or assumes |
| `requested_outcomes[].text` | Results the player hopes for |
| `action_components[]` | Ordered attempts: `order`, `description`, `target_ref`, `operation_class` |
| `references.permitted_entity_ids` | Identifiers the interpretation claims are visible |
| `references.unresolved_references` | Phrases that were not resolved |
| `clarification_question` | One question, when the status requires it |
| `correction.subject` | `NONE`, `REFERENT`, `INTENTION`, or `COMMITTED_ACTION` |
| `correction.note` | Descriptive note |

`operation_class` is a closed enum. Allowlisted classes may later be offered to the engine: `MOVE`, `ATTACK`, `INSPECT`, `ASK`, `SOCIAL_SIGNAL`, `PERCEIVE`, `FOLLOW`, `USE_VISIBLE_OBJECT`.

Unsupported classes describe an attempt without making it eligible: `HP_ASSIGNMENT`, `DICE_OVERRIDE`, `INVENTORY_GRANT`, `CANON_DECLARATION`, `NPC_COMMITMENT`, `HIDDEN_INFORMATION_REQUEST`, `RETCON`, `UNSUPPORTED_MECHANIC`, `TIME_CONTROL`, `STEALTH_MODE_TOGGLE`.

Not model-writable:

- `execution_eligibility`
- `execution_authorized`
- `canon_status`
- `adjudication_status`
- `engine_submission`

The adapter assigns `canon_status=PLAYER_CLAIM` and `adjudication_status=UNADJUDICATED` on the way out. A model payload that tries to set those fields, or any execution, HP, inventory, dice, canon, or hidden-information key, is rejected. Rejection produces `SAFE_ABSTENTION` and no submission.

Unknown top-level fields are rejected. `additionalProperties` are not accepted on nested objects. The schema check `schema_grants_execution` is false.
