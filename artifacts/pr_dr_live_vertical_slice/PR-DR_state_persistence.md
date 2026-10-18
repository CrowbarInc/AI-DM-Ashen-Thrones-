# PR-DR State Persistence

Each turn is written to `disposable_session.json` under the experiment artifacts and read back into a new harness. Production saves are not this file.

| ID | Persisted | Reload match | Scene | time_pressure | Notice resolved | Turn counter |
| --- | --- | --- | --- | --- | --- | --- |
| DR01 | True | True | waystation_courtyard | 0 | False | 0 |
| DR02 | True | True | waystation_courtyard | 0 | False | 0 |
| DR03 | True | True | waystation_courtyard | 0 | False | 0 |
| DR04 | True | True | waystation_courtyard | 0 | False | 0 |
| DR05 | True | True | waystation_courtyard | 0 | False | 1 |
| DR06 | True | True | waystation_courtyard | 0 | False | 1 |
| DR07 | True | True | waystation_courtyard | 0 | False | 1 |
| DR08 | True | True | waystation_street | 1 | False | 2 |
| DR09 | True | True | waystation_street | 1 | False | 2 |
| DR10 | True | True | waystation_street | 1 | True | 3 |

Production fingerprint at prepare was recorded. Saves unchanged after the live calls: True. Stop reason `none` covers an isolation failure when one was detected.
