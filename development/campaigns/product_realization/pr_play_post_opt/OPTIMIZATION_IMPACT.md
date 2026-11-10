# Optimization impact

Presence in the current tree was confirmed by the existing focused tests: 61 passed, 0 failed. That run is `tests/test_at_opt_02_retreat_and_budget.py`, `tests/test_at_opt_04_mixed_key_policy.py`, `tests/test_at_opt_06_same_scene_transition.py`, and `tests/test_at_opt_06_instruction_eligibility.py`. Those tests were written with the corrections. They show the corrections are still in the tree. They do not by themselves show a better play session.

## AT-OPT-02 retreat routing

**Exercised and passed.**

T12, with physical adjudication unset, returned `unresolved_retreat_without_adjudication`, did not enter `call_gpt`, did not change turn, scene, position, or `last_publication`, and wrote no publication event. The same sentence is the F3 retreat. Here it was spoken at Old Milestone, after the player had left the board. The refusal still matches the disabled-adjudication contract.

## AT-OPT-02 verification budget

**Exercised and passed, outside the chat loop.**

`apply_verification_budget()` installed 3,000 total tokens. A total of 200,000 was rejected and the 3,000 ceiling remained. With provider calls left enabled, an estimate of 28,000 was refused as `input-token ceiling` and the invoke stub was not called. An estimate of 100 was admitted and a local stub completed. The stub's 14 tokens are not a provider bill.

The chat loop had provider calls disabled, so its own admission probe stopped on `provider calls disabled` before the token ceiling was consulted. Gameplay admissions after that probe: none. A budget refusal remains distinct from completed gameplay: T12's operational refusal is a routing refusal, and the token-ceiling refusal never produced a player sentence.

## AT-OPT-04 mixed-key policy deduplication

**Not exercised.**

No gameplay turn reached payload serialization. The four `call_gpt` entries returned at the disabled-provider or retry-disabled branch, which is before the nested-policy projection is sent. The focused mixed-key tests passed. This session does not show the deduplication changing a player response.

## AT-OPT-06 same-scene transition

**Not exercised at the transition-node layer. Outcome-level scene identity stayed consistent.**

Ordinary turns T01 through T10 remained in `frontier_gate`. T11 was a real authored transition to `old_milestone`, with `resolved_transition` true. The session did not rebuild a narration plan, so `transition_required` on a same-scene stamp was not measured here. Scene stability on the ordinary turns is compatible with the correction and is not a new proof of it.

## AT-OPT-06 full-instruction safeguard

**Not exercised.**

No plan-backed `manual_play_auto` request was assembled. Instruction counts were not measured. The focused eligibility tests passed.

## What this does not show

The 624-byte AT-OPT-06 reconstruction delta and the AT-OPT-04 byte reduction were not remeasured. They remain admission estimates, not provider bills. This session does not show that those corrections made the conversation more playable.
