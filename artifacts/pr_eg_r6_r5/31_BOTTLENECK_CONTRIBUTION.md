# 31 — Bottleneck Contribution

Ranked by demonstrated change in the validation reply, not by how often a reason string appears.

| Rank | Stage | Evidence | Isolated effect | Combined effect | Security | Repair size |
|---|---|---|---|---|---|---|
| 1 | Referent bind and witness gates | Corrections 0/25. I9 still returns unlisted role changes, invalid correction operations, and unwitnessed requests on turns I8 answers. unexpected_referent_operation 27 and unwitnessed_referent_request 19 on the full baseline. | I2 net +4 | Intent+referent net +5; I9 net +14 while these gates still run | High. A looser witness check can accept an invented role. | Local, if limited to spans the utterance already contains |
| 2 | Question and source correspondence together | I3 net −2, I5 net −3, question+source net +8 with 7 only-by-combination. no_relevant_source 26. | Either side negative | Both sides positive; I9 higher | High. A softer match can accept a related non-answer or a hidden lexical hit. | Local to `coverage()` / `named_coverage`, after both propositions exist |
| 3 | Authorized plan to speech | I8 net +26, I10B net +27 | The plan substitution is the ceiling of the current speaker | Expression off is one turn better | The helper already refuses unpermitted sources | No production change recommended. The speaker is not the bottleneck |
| 4 | Sufficiency label | I7 net +2. F13 is usually downstream of an earlier miss | Small | Correspondence+sufficiency adds no extra joint fixes | Upgrade is blocked | Do not build a new classifier first |
| 5 | Intent act | I1 net +1 | Negligible | Small joint gain with referent | Low | Do not retune the act label first |
| 6 | Source-id retrieval | I4 net 0, zero reason changes | None | Retrieval+correspondence equals I6 | The filter never added hidden rows | Do not add a candidate retriever |
| 7 | Expression wording | 27 expression calls on 164 turns. One measured distortion (c06t07) | I8 vs I10B differs by one turn | I10C is a different path | The distortion invented a specific ignorance, not a secret | A guard that keeps host ignorance lines is enough |

F11 and F13 are common in the first-failure file because a rejected plan becomes unknown. They are symptoms of ranks 1 and 2.
