# AT-OPT-05 Summary

**Verdict: A/PASS.** Compact-instruction eligibility is mapped, `transition.transition_required` is traced to a same-scene scene-id stamp, and the F3 reconstruction is measured without a provider call. Production instruction selection was not changed.

The flag on the reconstructed frontier-gate turn is true because the attached plan’s only transition signal is `state_mutations.scene.scene_id = frontier_gate`. The CTIR for “I examine the notice board.” has `resolved_transition: false`. Before and after anchors are both `frontier_gate`. Narrative mode stays `action_outcome`. Scene-advancement flags stay false. The compact gate still closes, because `must_advance_scene` is copied from that flag.

That is an implementation defect in `_derive_transition_node`. The runtime writer stamps the current scene id on every narration. The predicate treats any scene id as a required location change. It does not mean the player asked to change scenes, and it does not switch the narrative mode to transition.

Forcing the existing compact path on that same payload would shrink the serialized request from 80,403 bytes to 70,263 (10,140 bytes, 12.61%). The admission estimate would fall from 26,865 to 23,485, minus 3,380. That estimate is bytes divided by 3, plus 64. It is not a provider bill. The recorded F3 input remains 22,777. The compact user list drops the visibility, first-mention, and speaker-selection hard rules. Those losses are not safe to take as a side effect of correcting the flag.

## Selected next step

AT-OPT-06 should correct the same-scene `scene_id` predicate and hold compact selection where it is now for plan-backed turns. Do not start that edit in this cycle. Do not open PR-PLAY-80.

Reports in this directory. Evidence: `artifacts/at_opt_05/eligibility_analysis.json`.
