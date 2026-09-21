# RC-13 Turn Trace

| Milestone | Turn | Observation |
|---|---:|---|
| First unprofiled subtype | `act_02` | `sealed_replacement_mutation`; cumulative mutation count 2 |
| Referential-clarity subtype | `act_14` | `referential_clarity_replacement_mutation`; cumulative count 13 |
| First aggregate breach | `act_19` | cumulative count 15 exceeds profile maximum 14 |
| Final | `act_25` | 19 mutation events; replay health remains clean |

Final mutation frequencies: fallback 7, final-emission 4, response-type repair 2, speaker repair 1, sealed replacement 4, and referential-clarity replacement 1.

Final event frequencies: fallback-selected 7, gate-outcome 25, mutation 19, and speaker-repair 1. The complete per-turn event sequence is in `rc13_turn_trace.json`.
