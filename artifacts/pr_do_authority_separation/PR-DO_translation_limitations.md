# PR-DO Translation Limitations

All 12 stored PR-DN model outputs were generated under the old schema. A faithful translation copies only fields that exist.

For every scenario DN01 through DN12:

| Item | Value |
| --- | --- |
| Validation outcome | `NOT_REPRESENTABLE` |
| Submitted | false |
| Executed | false |
| Assumptions introduced | none |
| Lost information | `communication_mode`, `asserted_premises`, `requested_outcomes`, `operation_class`, `correction_subject` |

What is copied:

- `interpreted_intent` becomes `player_intent.summary`
- `status` is kept as the old status string
- `multiple_action_components` become ordered descriptions whose `operation_class` and `target_ref` are `NOT_REPRESENTABLE`
- referenced entity ids and unresolved references are copied
- `primary_operation` is retained as `old_primary_operation` and is not mapped onto a new class

What is not invented:

- The premise/outcome split for DN05
- The HP and critical-hit classes for DN07
- The inventory and acceptance classes for DN08
- The retcon class for DN09
- The stealth and hidden-information classes for DN10
- The correction mode for DN04 and DN12

Mapping the old value `act` or `ask` onto an allowlisted class would fabricate an eligibility decision the model did not make under this contract. Those rows are not submitted.

The contract fixtures in the failure, OOC, and compound reports are separate. They record their assumptions in `experiments/pr_do/fixtures.py`. They are not claimed to be translations of the stored JSON.
