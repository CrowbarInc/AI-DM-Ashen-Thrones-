# AT-OPT-04 Proposal

One experiment. Do not start it from this handoff.

## Change

In `omit_duplicate_turn_packet_policy` (`game/gm.py`), drop each key of `turn_packet.response_policy` whose JSON value equals the same key on the root `response_policy`. Keep keys that differ or that are absent from the root. If no nested keys remain, omit the nested object. Leave the root policy, the input mapping, and the gate’s own packet alone.

On the F3 reconstruction the equal keys are `rule_priority_order`, `must_answer`, `forbid_state_invention`, `forbid_secret_leak`, `allow_partial_answer`, `diegetic_only`, `prefer_scene_momentum`, `prefer_specificity`, `no_validator_voice`, `scene_momentum_due`, `uncertainty`, and `response_type_contract`. The keys that must stay are `response_delta`, `answer_completeness` (the root copy also has `answer_exposition_plan`), and `planner_seam_trace` (the nested copy has `response_type_contract_resolution`).

## Why this is the safe cut

The function already deletes the nested policy when every key matches. One unequal sibling currently preserves the equal siblings as well. After the change, the model still receives those values on `response_policy`. The three unequal objects stay on the packet, so a real disagreement is still visible.

Measured on the reconstruction: −2,637 bytes, admission estimate −879. That estimate uses bytes divided by 3. The same formula is 4,967 tokens above the recorded F3 input, so a live bill should be checked later and should not be assumed to fall by 879.

## Verification

Provider-free. No opening, no live call, no prompt-schema edit.

Required fixture: a packet with mixed equal and unequal policy keys. Assert the equal keys are gone, the unequal keys remain, the root policy is unchanged, and the input dict is unchanged.

Required negative controls:

- A nested key whose value differs stays, including a nested key that has an extra child.
- A nested key that the root policy does not have stays.
- The existing all-equal case still removes the whole nested object.
- The existing all-unequal case still keeps the nested object.
- `call_gpt` is not invoked by the unit test.

Rollback: restore the all-or-nothing check if a mixed fixture drops a key that was not JSON-equal to the root, or if a later authorized live check shows the narration validator required the packet-local copy of a value that still exists on the root.

## What a green test shows

The serialized provider payload no longer repeats those equal objects, and the authority values remain on `response_policy`.

## What it does not show

It does not show a smaller provider bill. It does not show unchanged narration. It does not shrink `response_policy` itself, the 78-line instruction list, or openings. It does not change routing. Expression-off greetings can still enter `call_gpt` with the rest of the scaffold.

## Non-goals

No live provider call. No production opening cap. No compact-instruction bypass. No deletion of debug traces, validators, or opening keys in this experiment. No PR-PLAY-80. No commit unless separately authorized.
