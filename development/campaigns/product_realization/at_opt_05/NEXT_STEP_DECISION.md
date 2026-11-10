# Next-step decision

**Outcome 1. Proceed to AT-OPT-06.** One implementation experiment. Do not start it in this cycle.

## Experiment

Correct the same-scene scene-id predicate, and hold compact selection for plan-backed `manual_play_auto` turns so the correction does not select compact.

1. In `_derive_transition_node`, do not treat `state_mutations.scene.scene_id` as a transition signal when it equals `ctir.scene_id` and no other signal is present. Keep `activate_scene_id`, a different scene id, `target_scene_id`, `resolved_transition`, scene-change flags, and an explicit transition kind.
2. In `_should_use_manual_play_compact_prompt`, after the explicit `manual_play_compact` short-circuit, return false for `manual_play_auto` when a stamp-matched narrative plan is present. Today those turns stay on the full list only because the false flag sets `must_advance_scene`. Removing the flag without this hold selects compact.

`prompt_context.py` is already dirty from earlier work. The next edit has to keep those unrelated changes.

## Why this, and not the compact swap

The flag is wrong on the recorded examine turn, the milestone look, and the 79 and 79B session bundles: required `location_change`, identical anchors, `resolved_transition` false, source field the scene-id stamp. Mode stays `action_outcome`. That is the earliest incorrect decision.

Expected effect of the predicate fix alone, measured by the forced-compact run, would be the 10,140-byte / 3,380-estimate reduction on this reconstruction, plus `must_advance_scene` becoming false. That reduction deletes visibility, first-mention, and speaker hard rules. Those risks are understood and are not accepted.

The selected experiment’s measurable benefit is the node: same-scene `scene_id` yields `transition_required` false and type `none`. The request-size change should be that object and the obligation boolean, not the compact list. Compact eligibility on the attached F3 auto build must stay off. Rollback if that build’s instruction count moves off 78, or if `activate_scene_id`, a different scene id, `target_scene_id`, `resolved_transition`, `arrived_at_scene`, or `time_skip` stops setting `transition_required`.

## Verification the next cycle needs

- Existing `tests/test_narrative_planning_transition_node.py` stays green. It does not cover same-scene `scene_id`. Add that case, and add same-scene `scene_id` combined with `resolved_transition` so the other signal still wins.
- Provider-free rebuild of snapshot `2026-11-08T16-50-45_8caf7aff`: node not required, `must_advance_scene` false, auto profile still 78 instruction lines.
- Explicit `manual_play_compact` still forces compact.
- Detached no-resolution auto path still selects compact. Do not use that as proof the plan-backed list can shrink.
- Do not repair the three preexisting `KeyError`s (`provider_context_projection`, `gm_only`, `social_context`). This cycle reproduced them: 15 passed, 3 failed, in `artifacts/at_opt_05/focused_junit.xml`.
- No live provider call. No production opening cap.

## Candidates not selected

| Candidate | Why it is not the experiment |
| --- | --- |
| A alone, flag fix with compact left to follow | Opens compact on ordinary plan-backed turns. Authority loss is demonstrated |
| B, refine eligibility while keeping the flag | The flag is not an accurate required transition. Tightening the gate around a false label leaves the false `location_change` in the payload |
| C, keep full instructions because the gate is justified | The gate is justified for `resolved_transition` and a real scene activation. It is not justified for the current scene id |
| D, delete only redundant instruction lines | Echo-ban overlap is real and small. The large lines are not redundant. A line-level deletion is a different, wider edit |
| E, instrument before deciding | The predicate, the F3 node, the mode mismatch, and the compact diff are already measured |

## Non-goals

- Do not change narrative-mode priority. `target_scene_id` and `time_skip` can require a node while mode stays `continuation`. That mismatch is out of scope.
- Do not select compact for plan-backed turns.
- Do not cap openings at 3,000 tokens.
- Do not open PR-PLAY-80. The gameplay handoff remains the one already in `docs/NEXT_SESSION.md`: publication and live NPC work are ahead of a new play milestone, and this cycle does not replace that handoff.
- Do not treat 3,380 as a provider saving.
