# AT-OPT-06 Summary

**Verdict: A/PASS.** A same-scene scene-id stamp is no longer a required location change, and plan-backed `manual_play_auto` narration still uses the full instruction list.

Failure class: implementation. `_derive_transition_node` treated `state_mutations.scene.scene_id` as a transition signal even when that id was the current scene. On the F3 examine-turn CTIR both anchors were `frontier_gate`, `resolved_transition` was false, and the node was still a required `location_change`. Narrative mode stayed `action_outcome`.

After the correction, re-deriving that CTIR yields `transition_required` false and type `none`. `must_advance_scene` is false. The assembled auto request stays on 78 instruction lines. Those lines are identical to the pre-change rederived list. The serialized request falls from 79,859 bytes to 79,235, admission estimate 26,683 to 26,475, minus 624 bytes and 208 estimate. That estimate is bytes divided by 3, plus 64. It is not a provider bill. The recorded F3 input remains 22,777. Explicit compact and the detached no-resolution path are unchanged.

## Correctness changes

- Same known scene ids do not set `transition_required` or `location_change`.
- A different scene id, `activate_scene_id`, `resolved_transition`, arrival, time skip, and the other existing state-change flags still set `transition_required`.
- Equality does not clear an independent signal.
- A stamp-matched narrative plan keeps `manual_play_auto` on the full instruction list. The decision no longer depends on the false transition flag.

## F3 outcome

Current and destination scene on the attached CTIR remain `frontier_gate`. The rederived node is not a location change. The historical stored bundle on the snapshot is not rewritten, so a `build_messages` call that only consumes that stored node still reports the old required flag. A fresh derivation does not.

## Instruction preservation

Authority lines for visibility, first mention, speaker selection, scene anchor, and the policy-bridge fact limit remain. Forced compact is still 18 lines. Detached auto is still 9 lines and 50,793 bytes.

## Remaining limitations

A missing current scene id with a nonempty stamp still uses the previous defensive signal, because sameness cannot be proven. Narrative mode is not redefined. Stored bundles built before this correction are not migrated. No Gameplay Benchmark and no live provider call were run. The 624-byte change is not a playability or token-saving claim.

## Recommended next step

Close this runtime-optimization sequence. Do not start AT-OPT-07. Return to PR-PLAY / ATGB gameplay as a separate authorization. Do not open PR-PLAY-80 from this handoff. Do not cap production openings at 3,000.

Reports in this directory. Evidence: `artifacts/at_opt_06/`.
