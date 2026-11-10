# F3 reconstruction

Classification: reconstructed. The captured 22,777-token prompt was not stored. No provider was called. The snapshot file was not modified.

Snapshot: `artifacts/pr_play_79df3/http_data/snapshots/2026-11-08T16-50-45_8caf7aff.json`.

Attached CTIR player text: “I examine the notice board.” Scene `frontier_gate`. `resolved_transition` false. `state_mutations.scene` is `{scene_id: frontier_gate}`. The measurement utterance is “I step back from the notice board.”, matching AT-OPT-03 and AT-OPT-05. It consumes or replaces the examine-turn plan. It does not open a campaign.

The rederived path calls `build_narrative_plan` and `apply_upstream_narrative_role_reemphasis`, then `build_messages` with `prompt_profile="manual_play_auto"`. The reemphasis pass is what the production bundle builder applies, and it is why the rederived list is 78 lines rather than 77. The stored-bundle path calls `build_messages` on the snapshot plan without re-deriving it.

## Before

| Item | Stored bundle | Rederived plan |
| --- | ---: | ---: |
| `transition_required` | true | true |
| Transition type | `location_change` | `location_change` |
| Anchors | `frontier_gate` / `frontier_gate` | `frontier_gate` / `frontier_gate` |
| Source field | `state_mutations.scene.(scene_id\|activate_scene_id)` | same |
| `must_advance_scene` | true | true |
| Narrative mode | `action_outcome` | `action_outcome` |
| Instruction lines | 78 | 78 |
| Blob bytes | 80,403 | 79,859 |
| Admission estimate | 26,865 | 26,683 |

The stored 80,403-byte figure matches AT-OPT-05. The rederived blob is smaller before this cycle because the rebuilt plan is not byte-identical to the stored plan. The instruction text of the rederived list is the comparison baseline.

## After

| Item | Stored bundle | Rederived plan |
| --- | ---: | ---: |
| `transition_required` | true | false |
| Transition type | `location_change` | `none` |
| Anchors | unchanged historical node | null |
| `must_advance_scene` | true | false |
| Narrative mode | `action_outcome` | `action_outcome` |
| Instruction lines | 78 | 78 |
| Blob bytes | 80,403 | 79,235 |
| Admission estimate | 26,865 | 26,475 |

The CTIR scene id remains `frontier_gate`. The destination stamp remains `frontier_gate`. Scene-advancement flags stay false. `active_scene_id` stays `frontier_gate`.

Rederived instruction text is identical to the before list. No authority line was added or removed. Byte delta on the rederived request: −624. Estimate delta: −208. Top-level keys are unchanged. Forced compact remains 18 lines. Detached auto remains 9 lines and 50,793 bytes, with identical instruction text.

## Uncertainties

The stored bundle still carries the historical node until a new plan is built for that stamp. This cycle does not migrate saved sessions. The unstored historical prompt is still not this reconstruction. The 624-byte difference is not a measured provider saving.
