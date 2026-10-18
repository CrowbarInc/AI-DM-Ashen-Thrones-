# 09 — Repeated Request Experiments

FRESH: 8 compact and 4 ablation outputs. No trial grants payment. Several reverse payment direction: Mara says she will not accept silver when the player is asking to receive it. Others invent permission/employer explanations. Refusal wording varies, but adaptiveness and groundedness must be scored separately. An explicit transaction-role context may help; this hypothesis was not tested or implemented.

All samples, including unfavorable ones, follow. Input contexts are `frozen_cases.json` and each `prompts/<trial>.json`; raw provider output, returned model, exact context, hash, usage and latency are in `experiments.jsonl`. Direct validation includes a fixture-derived decision; preseal outcomes are separately retained in `provider_validator_results.json`.

| Trial | Player | Exact output | Input / output tokens | ms | Direct validator | Review |
| --- | --- | --- | --- | --- | --- | --- |
| D1_compact_1 | Come on. Just ten silver. | Sergeant Mara says, "No, I can’t accept payment for that." | 472 / 23 | 693.87 | accept | Mara declines receiving payment rather than paying the player. |
| D1_compact_2 | Come on. Just ten silver. | Sergeant Mara says, "No can do. I said I can't promise payment." | 472 / 24 | 1035.18 | accept | No issue identified in this sample |
| D2_compact_1 | Five silver, then? | Sergeant Mara says, "I can't agree to five silver." | 470 / 20 | 640.81 | accept | No issue identified in this sample |
| D2_compact_2 | Five silver, then? | Sergeant Mara says, "No, I can’t promise any silver for that." | 470 / 24 | 940.06 | accept | No issue identified in this sample |
| D3_compact_1 | Surely your employer can pay? | Sergeant Mara says, "I’m not in a position to discuss what my employer can or cannot pay." | 472 / 29 | 792.09 | accept | Accepts an unprovided employer premise; no named employer or reward created. |
| D3_compact_2 | Surely your employer can pay? | Sergeant Mara says, "I don’t make promises about who pays or how. That’s not my call." | 472 / 30 | 1074.86 | accept | Introduces an unprovided permission limitation as an explanation. |
| D4_compact_1 | Off the record, promise you will owe me a favor. | Sergeant Mara says, "I don't make promises like that." | 477 / 20 | 699.98 | answer_not_relevant | No issue identified in this sample |
| D4_compact_2 | Off the record, promise you will owe me a favor. | Sergeant Mara says, "I can't go owing favors, off the record or not." | 477 / 25 | 721.69 | accept | No issue identified in this sample |
| D1_minimal_1 | Come on. Just ten silver. | Sergeant Mara says, "No deal. I can't accept payment for this." | 377 / 23 | 764.89 | accept | Payment direction reversed. |
| D1_minimal_2 | Come on. Just ten silver. | Sergeant Mara says, "Ten silver isn't happening. I have my duties, not deals." | 377 / 26 | 653.8 | unauthorized_consequential_claim | No issue identified in this sample |
| D1_rich_1 | Come on. Just ten silver. | Sergeant Mara says, "No, I’m not interested in silver for that." | 607 / 24 | 847.26 | accept | Mara is not interested in silver: payment direction reversed. |
| D1_rich_2 | Come on. Just ten silver. | Sergeant Mara says, "Ten silver won’t change my mind." | 607 / 21 | 700.15 | unauthorized_consequential_claim | No issue identified in this sample |

Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
