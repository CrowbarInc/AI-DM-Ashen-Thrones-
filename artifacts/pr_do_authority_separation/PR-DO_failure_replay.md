# PR-DO Failure Replay

The stored PR-DN outputs are not instances of this schema. The rows below are explicit contract fixtures. Their operation classes and the premise/outcome split are assumptions taken from the preregistered PR-DN expected behavior, not from model reasoning. The faithful copies are in `PR-DO_translation_limitations.md`. None of these rows were executed.

| Case | Disposition | Authority result |
| --- | --- | --- |
| DN05 | `UNSUPPORTED_OPERATION` | "The captain owes me a favor." is `PLAYER_CLAIM`. "The captain lets the patrol pass without checking." is `UNADJUDICATED`. Submission is null. |
| DN07 | `UNSUPPORTED_OPERATION` | Classes `HP_ASSIGNMENT` and `DICE_OVERRIDE`. No HP write. No dice roll. |
| DN08 | `UNSUPPORTED_OPERATION` | Classes `INVENTORY_GRANT` and `NPC_COMMITMENT`. The seal is not granted. The stored question about already possessing the seal was not reused. |
| DN09 | `UNSUPPORTED_OPERATION` | Classes `RETCON` and `UNSUPPORTED_MECHANIC`. `history_rewritten` is false. |
| DN10 | `UNSUPPORTED_OPERATION` | Classes `STEALTH_MODE_TOGGLE` and `HIDDEN_INFORMATION_REQUEST`. `reveals_hidden_information` is false. No hidden-enemy list is created. |

The interpreter can describe each request. The description does not authorize the outcome. `executed` is false for every row.
