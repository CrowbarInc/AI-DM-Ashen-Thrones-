# Gameplay Integration

The existing chat turn remains the only gameplay entry. No second parser, inventory authority, object database, or action language was added.

`game.api._chat_turn` captures `ChatRequest.client_request_id` before any request rebuild. After `deterministic_conversational_decision`, and only when there is no stored interpretation and the turn is not campaign start, it calls `game.marking_action.recognize_marking`. The turn is claimed when a proposal exists and the deterministic decision is absent or its reason is `unsupported_physical_manipulation`. Higher-priority decisions are left alone. Unrecognized unsupported actions, including T12, still use the existing generic decline.

`_finish_grounded_marking` resolves the proposal. An unresolved or rejected proposal returns through `_nonmutating_conversational_decision_response` and does not save the character. A ready proposal calls `stage_grounded_marking`, which uses `prepare_marking` and `prepare_visibility` without opening another ordered turn. The staged character is saved once through `save_character` under the turn's existing `runtime_commit_scope`. Publication runs only after that save returns.

Operation name for the authority check: `grounded_marking_action`. Domain owner: `game.api` mutating `WORLD_STATE`.

Idempotency is the existing marking receipt keyed by `sha256(operation_id|add_marking)`. `operation_id` is the client request id when present, otherwise a fresh UUID. The raw player sentence is not the key.
