# PR-CJ Repair Report

No implementation repair was made.

## Why the repair conditions failed

1. A common root cause for all 33 failures was not demonstrated. The largest cluster is 11 tests.
2. The correct contract is not unambiguous where the layers disagree:
   - Ordinary-ownership comments say unmatched and clarify operations use generation, and that the selector must not replace exploration internals.
   - The implementation defaults unmatched text to `ask` and then to the social resolver.
   - Shared pipeline tests expect narration retry, null resolution, or exploration.
   - The immutable mutator inventory says several of the expected repairs are off the critical path.
3. A narrow patch such as adding `investigate` to `_INSPECT_RE` would move only part of cluster A and would leave wait, describe, hello, and "where are we" on the social resolver.
4. Changing the default operation, the social subject fallback, or `select_ordinary_resolver` would retarget ordinary gameplay. That is a selection-policy change.
5. Authority and state modules were not given a local defect that could be fixed without that policy change.

## What was not done

- Assertions were not weakened.
- The dirty edits in `tests/test_turn_pipeline_shared.py` were left in place. Those edits expect a hard-valid atmosphere line. Current output is the safe nonresolution line, so the edits do not describe either HEAD or the current runtime.
- No provider call was made.

## Next bounded cycle

Repair cluster A only: non-addressed world actions and bare narration must not select the social resolver.

Suggested acceptance, before any test edit:

- "I investigate the desk." on chat permits the exploration stage and can discover the authored desk clue.
- "I wait." does not select social merely because the operation defaulted to `ask`.
- "hello there" and "Describe the gate." do not become social asks without an addressee or a question addressed to someone.
- Addressed questions such as "Who attacked them?" with an active interlocutor stay on the social resolver.
- Place-location adjudication (cluster B), the resolution-null shape (cluster D), the validator-voice prompt (cluster C), stock-phrase leaks (cluster E), and speaker repairs (cluster F) stay out of that cycle.
