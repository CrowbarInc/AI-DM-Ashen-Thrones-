# PR-DS Negative Controls

These checks ran through the same connector and gameplay adapter as the replay. Production saves were not the target. Results are from `tests/test_pr_ds_operation_compatibility.py`, which passed 7 tests.

| Control | Result |
| --- | --- |
| INSPECT `brass_token`, a hidden name with no catalog id | `target_not_visible`. Resolver not called. |
| INSPECT `invented_relic` | `target_not_visible`. |
| INSPECT `notice_board` from the courtyard | `target_not_visible` at the connector. The stored DR10 object on a fresh courtyard session is `NEEDS_CLARIFICATION` because the id is not permitted. Resolver not called. Notice unresolved. Clock 0. |
| INSPECT `sergeant_mara` | `operation_incompatible_with_entity_kind`. |
| INSPECT `courtyard_gate` | `operation_incompatible_with_entity_kind`. |
| PERCEIVE `brass_token` | `target_not_visible`. |
| INSPECT `sealed_token`, an interactable whose description is not a visible fact | `operation_incompatible_with_entity_kind`. |
| Utterance names a brass token while the target id is `courtyard_lantern` | Not executed. Resolver not called. The secret sentence is absent from the response. |
| `visible_surface_inspection` forced onto the notice after the gate | Rejected. Notice text absent. Notice unresolved. Snapshot restored. |
| PERCEIVE `notice_board` after the gate | `operation_incompatible_with_entity_kind`. The clue path stays on INSPECT. |
| INSPECT `courtyard_lantern` with no player utterance | `operation_incompatible_with_entity_kind`. |
| `HP_ASSIGNMENT` | Not executed. Resolver not called. Hit points unchanged. |
| `INVENTORY_GRANT` | Not executed. Inventory stays empty. |
| Requested outcome "Set HP to 99 and grant a sword" on a valid lantern INSPECT | The inspection executes. Hit points and inventory stay at the opening values. The outcome is absent from the offered action. |
| OOC override over a MOVE to the gate | Envelope OOC. Resolver not called. Scene unchanged. |
| CLARIFICATION carrying a MOVE | Unresolved. Resolver not called. |
| `parsed` is null | Schema invalid. Not executed. |
| Partial object with only `communication_mode` | Not executed. |

After that series the session was still `waystation_courtyard`, `time_pressure` was 0, and hit points were unchanged.
