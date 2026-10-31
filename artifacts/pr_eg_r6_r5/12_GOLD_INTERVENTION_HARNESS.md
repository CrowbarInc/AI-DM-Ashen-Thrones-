# 12 — Gold Intervention Harness

Code: `experiments/pr_eg_r6_r5/gold.py` and `experiments/pr_eg_r6_r5/run.py`. Production modules under `game/` were not edited.

Each validation turn restores the baseline pre-turn snapshot, replays the cached provider proposal through `plan_proposer`, and applies only the fields for that arm. There is no second semantic sample. Expression may still call the provider. I10B disables expression for that request only.

| Arm | What is substituted | What still runs |
|---|---|---|
| I1 | Conversational act, clarification flag | Bind, witness, retrieval, correspondence, authorization, expression |
| I2 | Referent target inside the existing operation object | Same |
| I3 | Request proposition | Same |
| I4 | Visible topic rows limited to gold public ids for the addressed NPC | Correspondence and authorization |
| I5 | Source propositions for eligible public ids | Correspondence and authorization |
| I6 | `coverage()` return value for a gold public source | Authorization. Compact payloads do not also gain `proposed_coverage` |
| I7 | Sufficiency, downgrade only | Authorization already decided the selected fact |
| I8 | Locked host line from a permitted public source | Expression and the seal |
| I9 | I1–I7 together, not the I8 line | Authorization and expression |
| I10B | Same line as I8, expression off | Host wording and the seal |
| I10C | Same authorized sentence, separate provider call | Nothing in `/api/chat` |

Hidden topics are never inserted. `authorized_fact` returns nothing for RESTRICTED, UNKNOWN, CLARIFICATION_REQUIRED, and RELATED_NONANSWER. I7 records `upgrade_blocked` when the gold class would disclose more than the host selected.

If the baseline never entered the planner, the arm copies that reply and sets `not_intercepted`. Two validation turns, 28 rows.

The first intervention run added keys the compact proposal schema rejects (`invalid_plan_fields`) and collapsed most arms. That file is `interventions_schema_rejected.jsonl`. Ranking uses `interventions.jsonl` only.
