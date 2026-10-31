# 22 — Expression Control

| Arm | Path | Validation success | Net vs baseline |
|---|---|---:|---:|
| I8 | Production expression of a gold authorized plan | 44/54 (81.5%) | +26 |
| I10B | Same plan, expression disabled | 45/54 (83.3%) | +27 |
| I10C | Separate provider call constrained to that sentence | 53/54 (98.1%) | +35 |

I10B is one success ahead of I8. The differing turn is c06t07: the host line is ignorance and passes UNKNOWN; expression adds a specific claim about Tamsin and fails. Baseline expression calls were 27 of 164 turns. Most player-facing lines are already host templates, including "I can't reliably answer that just now."

I10C is not `/api/chat`. It does not bind an addressee and does not seal a session. Its 53/54 score shows that a model can repeat an authorized sentence. The one miss is c06t06, whose authorized sentence is ignorance because the PARTIAL label names no eligible source. The model repeated that sentence, and the rubric correctly rejected it.

Expression cost for I10C: 54 calls, 4761 input tokens, 802 output tokens. This is diagnostic cost, not production cost. Restricted hits: 0.
