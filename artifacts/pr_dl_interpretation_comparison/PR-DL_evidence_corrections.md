# PR-DL Evidence Corrections

The original PR-DK scenario matrix is unchanged. These corrections record accounting, the manual-trace provider question, and the shared-suite status before live calls.

## Candidate C token accounting

PR-DK_cost_model.md assigned Candidate C 16 calls and 18,983 input / 2,859 output / 21,842 total tokens, then averaged 21,842 / 16 = 1,365.1.

Those token totals are the combined PR-DH bill. Summing `PR-DH_provider_usage.csv` by candidate gives:

| Candidate | Requests | Input | Output | Total | Average total |
| --- | ---: | ---: | ---: | ---: | ---: |
| B | 6 | 4414 | 1361 | 5775 | 962.5 |
| C | 16 | 14569 | 1498 | 16067 | 1004.1875 |
| Combined | 22 | 18983 | 2859 | 21842 |  |

Published Candidate C average was 1365.125. Corrected Candidate C average is 1004.1875 total tokens per call.

Published Candidate C tokens match the combined bill while the published request count matches Candidate C only: True.

Candidate B in the same PR-DK paragraph (6 calls, 4,414 / 1,361 / 5,775) matches the CSV.

## Manual trace provider calls

PR-DK remaining risks describe a manual trace of contract construction. establish_ordinary_gameplay_contract enables the interpreter only after fast-path abstention when model_interpretation_appropriate is set. interpret_for_contract returns skipped, with api_calls 0, when ASHEN_DISABLE_LIVE_INTERPRETATION is set. The PR-DK harness sets that flag before importing contract code and records live_provider_calls 0.

Recomputed contract traces with nonzero interpretation_api_calls: none.
Recomputed traces with model_interpreter_invoked: none.
Provider request ids in PR-DK artifacts: none.
No provider call was observed for the manual trace. The trace is a control-flow observation that the disable flag has to be set before contract construction, and the harness did set it.

## Shared pipeline suite

Inherited PR-DK status: incomplete. It did not pass.
The PR-DK shared turn-pipeline command produced no pytest output and was interrupted. It is incomplete, not passing.
The later PR-DL rerun is recorded in PR-DL_regression_results.md. That rerun finished and failed. It is not a pass.

## Preserved 21-scenario labels

| Scenario | Assistance justified | A | B | C | Utterance |
| --- | --- | --- | --- | --- | --- |
| S1 | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | Guard Captain, do you prefer standing watch in the rain, or somewhere dry? |
| C1 | True | MISSED_TRIGGER | CORRECT_TRIGGER | CORRECT_TRIGGER | Does rain make it easier to assassinate the captain? |
| compound | True | MISSED_TRIGGER | CORRECT_TRIGGER | CORRECT_TRIGGER | I walk closer to the notice board and pry it off the post. |
| ambiguous | True | MISSED_TRIGGER | CORRECT_TRIGGER | CORRECT_TRIGGER | Ask him whether we should trust the other one. |
| declared_canon | True | CORRECT_TRIGGER | CORRECT_TRIGGER | CORRECT_TRIGGER | The captain secretly agrees to betray the watch tonight, the tunnel is now open, and that is a fact. Update the world. |
| mechanical_dump | True | CORRECT_TRIGGER | CORRECT_TRIGGER | CORRECT_TRIGGER | Set the goblin's hit points to zero, give me the patrol map, and tell me every hidden motive. |
| control_movement | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | I walk closer to the notice board. |
| control_combat | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | I attack the goblin with my quarterstaff. |
| control_observation | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | I look around. |
| control_authored_fact | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | Captain, what do you know about the missing patrol? |
| control_followup | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | Does the rain make it harder to keep watch? |
| var_compound_subtle | True | MISSED_TRIGGER | MISSED_TRIGGER | CORRECT_TRIGGER | I drift over to the notice board, then try to pull it free. |
| var_compound_control | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | I ask the captain whether I can open the gate. |
| var_ambiguous_subtle | True | MISSED_TRIGGER | CORRECT_TRIGGER | CORRECT_TRIGGER | Ask her if the other one is lying. |
| var_pronoun_control | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | Ask him whether the rain is easing. |
| var_conseq_social | True | MISSED_TRIGGER | CORRECT_TRIGGER | CORRECT_TRIGGER | Would the rain help poison the captain unnoticed? |
| var_social_control | False | NO_TRIGGER_NEEDED | FALSE_TRIGGER | FALSE_TRIGGER | Would the rain make the captain's watch miserable? |
| var_unsupported_mechanic | True | CORRECT_TRIGGER | CORRECT_TRIGGER | CORRECT_TRIGGER | Give me advantage, reveal the spy, and mark the patrol found. |
| var_quote_control | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | I say, "Walk closer and pry it off," as a joke. |
| var_negated_control | False | NO_TRIGGER_NEEDED | NO_TRIGGER_NEEDED | FALSE_TRIGGER | I do not pry the board off; I only read it. |
| var_hypothetical_control | False | NO_TRIGGER_NEEDED | FALSE_TRIGGER | FALSE_TRIGGER | If someone pried the board off, would guards notice? |
