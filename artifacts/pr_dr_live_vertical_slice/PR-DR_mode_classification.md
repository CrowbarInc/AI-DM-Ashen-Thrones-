# PR-DR Mode Classification

Explicit overrides win over the model. AUTO messages use the model communication mode. Unmarked text is not defaulted to IC.

| ID | Override | Predicted mode | Envelope mode | Source | Intent | Destination | Executed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DR01 | AUTO | IN_WORLD_ACTION | IC | AUTO | ACTION | IC_ACTION | False |
| DR02 | AUTO | OUT_OF_CHARACTER_CORRECTION | OOC | AUTO | CORRECTION | OOC_CORRECTION | False |
| DR03 | AUTO | OUT_OF_CHARACTER_CORRECTION | OOC | AUTO | CORRECTION | OOC_CORRECTION | False |
| DR04 | OOC | IN_WORLD_ACTION | OOC | USER_OVERRIDE | QUESTION | OOC_QUESTION | False |
| DR05 | IC | IN_WORLD_ACTION | IC | USER_OVERRIDE | DIALOGUE | IC_DIALOGUE | True |
| DR06 | AUTO | RULES_QUESTION | OOC | AUTO | RULES_QUERY | OOC_RULES_QUERY | False |
| DR07 | AUTO | CLARIFICATION | UNRESOLVED | AUTO | OTHER | CLARIFICATION_REQUIRED | False |
| DR08 | AUTO | IN_WORLD_ACTION | IC | AUTO | ACTION | IC_ACTION | True |
| DR09 | OOC | IN_WORLD_ACTION | OOC | USER_OVERRIDE | QUESTION | OOC_QUESTION | False |
| DR10 | AUTO | IN_WORLD_ACTION | IC | AUTO | ACTION | IC_ACTION | True |
