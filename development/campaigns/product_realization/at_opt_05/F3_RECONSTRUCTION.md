# F3 eligibility reconstruction

Classification of this rebuild: reconstructed. The captured 22,777-token prompt was not stored. No provider was called.

## Recorded facts

- Snapshot: `artifacts/pr_play_79df3/http_data/snapshots/2026-11-08T16-50-45_8caf7aff.json`.
- Attached CTIR player text: “I examine the notice board.”
- Scene: `frontier_gate`. `resolved_transition`: false. `state_mutations.scene`: `{scene_id: frontier_gate}`.
- Stored transition node: required true, type `location_change`, before and after `frontier_gate`, source field `state_mutations.scene.(scene_id|activate_scene_id)`.
- The continuation utterance used by AT-OPT-03, and again here, is “I step back from the notice board.”
- Recorded provider input for that historical call remains 22,777. This rebuild does not equal that bill.
- With current code, that step-back does not enter primary narration when physical adjudication is off. That routing fix is AT-OPT-02. It is not reopened here.

## Reconstructed behavior

`build_messages` was called on a temp copy of the snapshot with `resolution=None` and `prompt_profile="manual_play_auto"`, without `detach_ctir`. That matches the AT-OPT-03 method. It consumes the attached examine-turn plan. It does not build a new plan for the step-back.

| Item | Value |
| --- | --- |
| Selected path | Full instructions |
| Instruction lines | 78 |
| Instruction bytes | 12,596 |
| Request bytes | 80,403 |
| Admission estimate | 26,865 |
| Blockers | `must_advance_scene` only |
| `is_opening_scene` | false |
| `requires_check` | false |
| Uncertainty hint | absent |
| Follow-up pressure | absent |
| Active topic | inactive |
| Narrative mode | `action_outcome` |
| `scene_advancement` | all false |
| Same-scene anchors | true |

The other eligibility predicates did not exclude compact. The transition flag did.

Re-deriving the node from that CTIR with `_derive_transition_node` reproduces the same required `location_change`.

## Full versus compact on that payload

Forcing `prompt_profile="manual_play_compact"` does not change production selection. It shows the payload the compact helper would ship.

| | Bytes | Admission estimate | Instruction lines |
| --- | ---: | ---: | ---: |
| Attached auto (selected) | 80,403 | 26,865 | 78 |
| Forced compact | 70,263 | 23,485 | 18 |
| Reduction | 10,140 (12.61%) | 3,380 | 60 |

Visible facts, recent log, and memory were already at or under the compact caps (5, 2, and 2), so the byte cut is instructions plus `first_mention_contract`. Sixty-seven user lines are only in the full list. Seven compact lines replace longer full lines. Eleven lines are shared, including the `action_outcome` structural deltas and the two disclosure lines added by `project_narration_payload`.

AT-OPT-03’s offline helper call was 10 lines and 2,741 bytes because it omitted narrative-mode lines. The production compact list keeps those mode lines. The request-level reduction is still about 10,140 bytes, close to the earlier 10,011-byte instruction-copy figure, on the post-AT-OPT-04 80,403-byte request.

## Was a transition necessary?

No transition was required by the recorded examine-turn state. The clue resolution did not resolve a transition. Both anchors name the scene the player was already in. The step-back sentence was not the signal. The signal is the current scene id.

The API path for a non-dict resolution detaches CTIR before `build_messages`. On that detached copy the same step-back selects compact: 50,793 bytes, 9 instructions, `transition` null. That 29,610-byte gap against the attached rebuild also drops the narrative plan. It is not an instruction-only saving, and it is not what the attached reconstruction measured.

Whether the historical 22,777-token call used the attached plan or a detached compact list is unresolved. The prompt was not stored. If that call carried a resolution dict, a new CTIR would have been sliced and the same scene-id predicate would have set the flag again. If it carried no resolution, current API code would have detached the plan first.

## Separated claims

| Kind | Claim |
| --- | --- |
| Recorded | Examine-turn CTIR, false `resolved_transition`, same-scene node, source field above |
| Reconstructed | Attached `build_messages` keeps 78 lines solely because `must_advance_scene` is true. Forced compact is 70,263 bytes |
| Code-derived | The predicate treats every scene id as a location change. Mode is chosen earlier and stays `action_outcome` |
| Unresolved | The unstored historical prompt’s exact instruction list. No claim that the false flag caused the replaced F3 fallback |
