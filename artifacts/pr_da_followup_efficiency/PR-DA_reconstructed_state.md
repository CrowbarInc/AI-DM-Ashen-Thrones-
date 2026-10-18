# PR-DA Reconstructed State

Session payload is the session object returned by the PR-CY Turn 1 API response. The transcript is the first session_log line only. Documents that differ from the post-Turn-2 isolated copies are replaced with the Turn 1 API documents.

Turn 1 player input: Guard Captain, do you prefer standing watch in the rain, or somewhere dry?

Accepted Turn 1 answer marker present: I suppose most would prefer dry ground

Preserved from the Turn 1 engine return and the Turn 1 log line:

- Scene: frontier_gate.
- NPC: guard_captain, still addressable and present in the world roster.
- Discourse focus active interlocutor: guard_captain.
- Interaction target: guard_captain.
- Turn counter: 2, the value recorded after the successful Turn 1.
- Recent conversation: the Turn 1 exchange only. The Turn 2 refusal log line was excluded.

T1 state_after matches T2 state_before: True.

Document choices: `{"world": "replaced_with_t1_api_document", "character": "isolated_copy_matches_t1_api", "campaign": "isolated_copy_matches_t1_api", "conditions": "isolated_copy_matches_t1_api", "combat": "isolated_copy_matches_t1_api"}`.

Verification problems: none.

The reconstructed session is stored under `artifacts/pr_da_followup_efficiency/evidence/isolated_session/`. Production saves were not used as the gameplay session.
