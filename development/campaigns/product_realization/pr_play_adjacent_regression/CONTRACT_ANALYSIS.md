# Contract analysis

## Player HTTP publication

`game/player_http_projection.py` is the player DTO. Its `project_player_response` keeps `gm_output.player_facing_text` and, when `resolution` is present, sets that field to `{}`. The comment says the public body must not carry resolver claims, state diffs, or hidden discoveries.

`/api/chat` projects the completed turn through `_project_player_runtime_response` in `game/api.py`. The default mode is player. The twelve tests read `response["resolution"]` after that projection.

That DTO behavior predates the handoff. The projection module was not one of the four edited files, and the pre-handoff package uses the same `api.py` and the same projection module. Failures 1, 2, 4, 6, 7, 9, 10, 11, and the key error in 12 are the empty object. Failures 11 and 12 raise `KeyError` because the key is absent, not because the engine left the transition unset.

These assertions are not classified as obsolete. The grounding tests also require sentences the DTO does not strip. An empty `resolution` explains the kind and transition assertions. It does not explain a published stub. A later cycle can retire the public-kind assertions only with an explicit decision that the log, not the player body, is the contract those tests should read.

## Inspection and non-invention

`tests/test_referenced_surface_grounding_inspection_resolution.py` requires:

- an unknown named object to stay uninstantiated and to be investigated as unsupported;
- a narration-only bell not to become an authority;
- an abstract ledger not to publish a physical inventory;
- a readable authored surface to publish its clue;
- a hidden object not to be revealed by naming it;
- an authored alias to bind the interactable;
- the roster board to be inspected without the observe stock;
- the notice board read to discover `notice_patrol_route`.

The engine log meets the kind and authority for those cases on both packages. The published sentence does not, where perception replacement is skipped. The skipped list includes `apply_perception_non_invention_to_gm`. `leave_text_unchanged` in `game/immutable_valid_response.py` tells a mutator not to replace an accepted immutable response. The handoff did not edit that function or the perception hook.

Failures 3, 5, and 8 are conflicts with the non-invention contract, not with an authorized handoff behavior. The handoff did not authorize publishing a Glassport ledger, a token retrieval, or four overseers.

Failure 10's sentence agrees with the notice-clue contract. Only the public kind disagrees.

## Travel and unsupported action

`test_sequence_patrol_travel_reaches_the_movement_resolver` requires the missing-patrol trail to reach the movement resolver, move to `old_milestone`, and set `resolved_transition`. The scene change and the arrival sentence happen. The public flag does not.

`test_sequence_unsupported_actions_invent_nothing` requires no invented Captain Voss, no glass observatory route, and no footprint invention. The current sentences do that: an addressee clarification, `destination_not_established`, and `referent_not_in_scene`. Scene and turn counter stay put. The failing line is the public transition flag on the clarification.

The handoff's local-contact decline does not own these utterances. The glass observatory still declines as an unknown destination on the current tree.

## Handoff routing contract

The post-NPC contract, from `development/campaigns/product_realization/pr_play_post_npc/ROUTING_CONTRACT.md` and the focused tests, is narrower than these twelve assertions:

- a unique current-scene object is not an unestablished destination;
- overlap with the previous NPC sentence does not replay that sentence for a non-question or a named object;
- an explicit repeat still replays;
- a past-tense question about an established object is an inspection;
- an unbound physical attempt declines without an inventory change;
- a real exit still travels;
- hidden notice facts stay hidden.

This audit's replay matches that contract. It does not extend the contract to "player JSON must include `resolution.kind`". The handoff tests already read kind from the session log, not from the public body.

## Unresolved ambiguity

The player DTO and the older HTTP tests disagree about whether `resolution.kind` is public. That disagreement is older than the handoff and is not resolved by reclassifying the tests. The sentence failures are not ambiguous: the stub is the published text, and no handoff contract authorizes it.

No contract in this audit says the brass-token stub, the Glassport stub, or the overseer stub is the intended player sentence.
