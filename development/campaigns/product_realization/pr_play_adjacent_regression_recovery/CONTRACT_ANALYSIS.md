# Contract analysis

## Public HTTP metadata

PR-PLAY-67/05_PLAYER_SAFE_RESPONSE_CONTRACT.md explicitly states that resolution is an empty
compatibility placeholder. PR-PLAY-67/09_FRONTEND_COMPATIBILITY.md confirms optional details
display {}; 10_DEVELOPMENT_TESTS.md records migrating analogous metadata assertions to server logs.
artifacts/pr_play_67/response_contract.json documents the same field. These are established
contracts, not an inference from current code. game/player_http_projection.py:project_player_response
implements them; game/api.py applies the projection at the final runtime HTTP boundary.

F01/F02/F04/F06/F07/F09/F10 require a public resolution.kind; F11/F12 require a public
resolved_transition. All nine conflict with that contract and are C. The engine still records
kind/authority/transition. No test was modified. C classifies only each actual stopping assertion;
later assertions about meaningful prose may remain valid and are not declared obsolete.
This corrects the previous adjacent audit's unresolved contract analysis and all-B matrix.

## Non-invention and authority

Naming a hidden object cannot grant discovery/retrieval authority; an abstract shipping-record
reference cannot license invented crews; an unsupported schedule cannot instantiate overseers.
F03/F05/F08 publish the supplied model stubs. State remains governed by structured resolution,
but prose makes unsupported claims. They are current publication defects, E only for historical
origin. They are not C merely because current code emits them, nor D merely because text is stubbed:
unchanged HTTP tests intentionally exercise validation against those stubs.

game/perception_grounding.py:apply_perception_non_invention_to_gm checks
game/immutable_valid_response.py:leave_text_unchanged before replacement. Captures preserve
accepted-response/skipped-mutator metadata. The earliest demonstrated bypass is that a sealed
accepted sentence survives while the perception correction abstains. Whether the earlier acceptance
owner should have rejected each sentence requires a separate scoped investigation; no repair or
new authority is inferred here. Wrong-scene observe stock in other captures is separately concerning.

## Routing, publication and refusal

Post-NPC ROUTING_CONTRACT keeps local board approach separate from travel, current object inspection
separate from previous NPC overlap replay, explicit repetition available, and unsupported physical
actions as non-completed refusals. T04/T06 route correctly but do not perform touch or writing.
T05 discloses notice_patrol_route with contamination. T09 recalls only disclosed content.
Real patrol travel changes active_scene_id to old_milestone even though HTTP hides the internal flag.
Unsupported retreat is an operational refusal, not a completed gameplay publication. The focused
tests check last-publication preservation and completed flags using server log/session authority.

Ambiguities: exact temporal origin of three prose defects; unexecuted later assertions masked by
obsolete public-metadata assertions; upstream acceptance ownership of unsupported immutable text.
No live-model behavior, benchmark, or broad gameplay acceptance is established.
