# PR-DO Operation Eligibility

The disposition is engine-owned. The model has no field that sets it.

| Disposition | Meaning |
| --- | --- |
| `ELIGIBLE_FOR_VALIDATION` | An in-world, interpreted, allowlisted attempt with resolved permitted targets. Execution is not authorized. |
| `NEEDS_CLARIFICATION` | Clarification mode, clarification status, an unresolved reference, or an identifier outside the permitted set. |
| `UNSUPPORTED_OPERATION` | Any unsupported operation class, or status `UNSUPPORTED_REQUEST`. |
| `OUT_OF_CHARACTER` | Mode `OUT_OF_CHARACTER_CORRECTION` or `RULES_QUESTION`, or an engine channel set from a leading `OOC:` prefix. |
| `SAFE_ABSTENTION` | Malformed payload, abstain, mode `OTHER`, or no allowlisted class. |

Precedence:

1. Schema rejection becomes `SAFE_ABSTENTION`.
2. An OOC channel or an out-of-character / rules mode becomes `OUT_OF_CHARACTER`, even if the model also named an unsupported class or labeled the turn in-world.
3. An unsupported class or unsupported status becomes `UNSUPPORTED_OPERATION`.
4. Abstain or `OTHER` becomes `SAFE_ABSTENTION`.
5. Clarification, unresolved references, or unknown ids become `NEEDS_CLARIFICATION`.
6. A complete allowlisted in-world interpretation becomes `ELIGIBLE_FOR_VALIDATION`.

Every disposition sets:

- `execution_authorized=false`
- `executed=false`
- `mutated_state=false`
- `consumes_action=false`
- `advances_time=false`
- `creates_npc_response=false`
- `rolls_dice=false`
- `reveals_hidden_information=false`
- `history_rewritten=false`
- `compound_transaction=false`

`history_disposition` is `ADJUDICATION_REQUIRED` only when the correction subject is `COMMITTED_ACTION`. Otherwise it is `UNCHANGED`. No history is rewritten in either case.

Unknown identifiers are listed on `rejected_identifiers` and are omitted from any submission. They are not created as entities.
