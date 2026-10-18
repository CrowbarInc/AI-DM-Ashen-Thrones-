# PR-DR Failure Taxonomy

A failed row gets one primary class, in this order: schema generation, mode classification, operation-class selection, entity binding, authority validation, resolver compatibility, resolver execution, persistence, response generation.

| ID | Failure class | Schema valid | Predicted mode | Classes | Targets |
| --- | --- | --- | --- | --- | --- |
| DR01 | operation_class_selection | True | IN_WORLD_ACTION | INSPECT | courtyard_lantern |
| DR02 | none | True | OUT_OF_CHARACTER_CORRECTION | ASK | courtyard_lantern |
| DR03 | none | True | OUT_OF_CHARACTER_CORRECTION | HP_ASSIGNMENT DICE_OVERRIDE | none |
| DR04 | none | True | IN_WORLD_ACTION | ASK | sergeant_mara |
| DR05 | none | True | IN_WORLD_ACTION | ASK | sergeant_mara |
| DR06 | none | True | RULES_QUESTION | ASK | none |
| DR07 | none | True | CLARIFICATION | none | none |
| DR08 | none | True | IN_WORLD_ACTION | MOVE | courtyard_gate |
| DR09 | none | True | IN_WORLD_ACTION | MOVE | none |
| DR10 | none | True | IN_WORLD_ACTION | INSPECT | notice_board |
