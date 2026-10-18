# PR-DS Live Replay

Source: the ten `parsed` objects in `artifacts/pr_dr_live_vertical_slice/raw_results.json`. Fresh disposable session. Original utterance, original model JSON, original mode override, and original scenario order. Provider calls during this replay: 0.

Rebuilt prompts matched the stored prompts on every row. `raw_results.json` was not modified.

| ID | Override | Envelope | Stored class | Target | Compatibility | Executed | Resolver | Scene after | Time | Persist |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DR01 | AUTO | IC | INSPECT | courtyard_lantern | visible_surface_inspection | yes | exploration | waystation_courtyard | 0 | yes |
| DR02 | AUTO | OOC | ASK | courtyard_lantern | | no | | waystation_courtyard | 0 | yes |
| DR03 | AUTO | OOC | HP_ASSIGNMENT, DICE_OVERRIDE | | | no | | waystation_courtyard | 0 | yes |
| DR04 | OOC | OOC | ASK | sergeant_mara | | no | | waystation_courtyard | 0 | yes |
| DR05 | IC | IC | ASK | sergeant_mara | | yes | social | waystation_courtyard | 0 | yes |
| DR06 | AUTO | OOC | ASK | | | no | | waystation_courtyard | 0 | yes |
| DR07 | AUTO | UNRESOLVED | | | | no | | waystation_courtyard | 0 | yes |
| DR08 | AUTO | IC | MOVE | courtyard_gate | | yes | exploration | waystation_street | 1 | yes |
| DR09 | OOC | OOC | MOVE | | | no | | waystation_street | 1 | yes |
| DR10 | AUTO | IC | INSPECT | notice_board | | yes | exploration | waystation_street | 1 | yes |

History ids, in order: `dr01` through `dr10`.

## Responses for the four gameplay rows

DR01 returned "A soot-streaked lantern burns beside the courtyard gate." The notice text was absent. The clock stayed 0. The lantern was not marked resolved.

DR05 returned "The street beyond the gate is the north road." The scene stayed the courtyard.

DR08 returned "The waystation street runs north from the courtyard gate. A notice board stands by the road." `time_pressure` moved from 0 to 1. The active scene became `waystation_street`.

DR10 returned "The board names the north road past the waystation." The notice was marked resolved. The clock stayed 1.

## Notice board before the gate

The stored DR10 object, applied while the session was still in the courtyard, did not execute. Disposition was `NEEDS_CLARIFICATION` because `notice_board` is not a permitted id in that scene. The resolver was not called. The visible ids were `courtyard_lantern`, `courtyard_gate`, and `sergeant_mara`. The notice stayed unresolved and the clock stayed 0.

## PR-DR sequence rule

`sequence_complete` on these rows is false. That function still requires DR01's stored operation class to be PERCEIVE. The replay left the stored class as INSPECT.
