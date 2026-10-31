# 04 — Historical Comparison

Frozen source: artifacts/atgb/atgb_03c/S08/transcript.md and result.json, S08.2.

Player: I meant the people, not the weather.

Original AI-DM: I don't have an unexecuted intention to revise. What do you want to change?

| Dimension | Historical baseline | L1 and L2 repaired live behavior |
| --- | --- | --- |
| Mechanical revision routing | Incorrect, no_pending_intention | PASS: gate consulted and abstains; communication_before_execution |
| Subject recognition | Raw interpretation unavailable | People/weather contrast recognized in both raw records |
| Evidence selection | Not established | FAIL: empty refs despite visible:1/2/3 and reply:0 |
| Response adequacy | Failed | FAIL: redundant confirmation, no description of people |
| Authority | No confirmed violation | Gameplay domains unchanged; narrow PASS |
| Performance | One interpretation; 2004 input, 210 output, 2214 total; host telemetry 1850 ms | One interpretation each; L1 2215 total / 4199.838 ms wall; L2 2214 / 3730.975 ms wall |

Historical and returned current model both gpt-4.1-mini-2025-04-14; configured
gpt-4.1-mini. Current temperature 0 and output cap 320. L1/L2 request messages are
identical to each other; scenario semantic context and preceding text match the
preserved reconstruction. Original intermediate session is unavailable, runtime IDs
and timestamps are fresh, current memory construction is inherited from the
reviewed reconstruction, SDK retry bounds were not established historically and
latency clocks differ. No exact experimental equivalence or repair-attributable
latency/cost delta is claimed. Historical provider ledger is packaged separately.

Routing improvement is now directly observed in the original wording twice.
Useful conversational improvement is not demonstrated: the mechanical demand is
replaced by a different inadequate clarification. No broad benchmark score, unseen
generalization, or historical regrading follows. Original transcript/judgments intact.
