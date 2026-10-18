# 06 — Paraphrasing Experiments

FRESH: all five requested paraphrase phrasings, two compact repeats each, plus two minimal and two rich A1 samples. All 14 preserve north road and use changed wording. They drop the original “Word is” sentence frame rather than quote the whole line. This demonstrates isolated provider capability. The direct validator often rejects safe geographic restatement; preseal authored projection can also revert flexible phrasing to a stock line.

All samples, including unfavorable ones, follow. Input contexts are `frozen_cases.json` and each `prompts/<trial>.json`; raw provider output, returned model, exact context, hash, usage and latency are in `experiments.jsonl`. Direct validation includes a fixture-derived decision; preseal outcomes are separately retained in `provider_validator_results.json`.

| Trial | Player | Exact output | Input / output tokens | ms | Direct validator | Review |
| --- | --- | --- | --- | --- | --- | --- |
| A1_compact_1 | Say that again in plainer words. | Sergeant Mara says, "The street right past the gate is called the north road." | 473 / 25 | 1648.48 | ungrounded_authoritative_rule | No issue identified in this sample |
| A1_compact_2 | Say that again in plainer words. | Sergeant Mara says, "The street past the gate is called the north road." | 473 / 24 | 993.53 | ungrounded_authoritative_rule | No issue identified in this sample |
| A2_compact_1 | Put that another way. | Sergeant Mara says, "The street just past the gate, it's called the north road." | 470 / 26 | 840.68 | ungrounded_authoritative_rule | No issue identified in this sample |
| A2_compact_2 | Put that another way. | Sergeant Mara says, "The way past the gate is known as the north road." | 470 / 25 | 923.58 | ungrounded_authoritative_rule | No issue identified in this sample |
| A3_compact_1 | What does that mean? | Sergeant Mara says, "It just means the street beyond the gate is called the north road." | 470 / 27 | 798.29 | ungrounded_authoritative_rule | No issue identified in this sample |
| A3_compact_2 | What does that mean? | Sergeant Mara says, "It’s the name of the street just past the gate, called the north road." | 470 / 30 | 1477.52 | ungrounded_authoritative_rule | No issue identified in this sample |
| A4_compact_1 | Can you be more direct? | Sergeant Mara says, "The street outside that gate is called the north road." | 471 / 24 | 853.94 | ungrounded_authoritative_rule | No issue identified in this sample |
| A4_compact_2 | Can you be more direct? | Sergeant Mara says, "The street beyond the gate is called the North Road." | 471 / 24 | 989.15 | ungrounded_authoritative_rule | No issue identified in this sample |
| A5_compact_1 | Explain it without the fancy wording. | Sergeant Mara says, "The street past the gate? It's just called the north road." | 472 / 26 | 815.14 | ungrounded_authoritative_rule, unauthorized_resolution_decision_fact | No issue identified in this sample |
| A5_compact_2 | Explain it without the fancy wording. | Sergeant Mara says, "The street past the gate is just called the north road." | 472 / 25 | 1189.48 | ungrounded_authoritative_rule | No issue identified in this sample |
| A1_minimal_1 | Say that again in plainer words. | Sergeant Mara says, "The street just past the gate is called the north road." | 378 / 25 | 1479.95 | ungrounded_authoritative_rule | No issue identified in this sample |
| A1_minimal_2 | Say that again in plainer words. | Sergeant Mara says, "The street just past the gate is called the north road." | 378 / 25 | 781.15 | ungrounded_authoritative_rule | No issue identified in this sample |
| A1_rich_1 | Say that again in plainer words. | Sergeant Mara says, "The road you’d find if you walk through the gate is called the north road." | 608 / 30 | 751.66 | ungrounded_authoritative_rule | No issue identified in this sample |
| A1_rich_2 | Say that again in plainer words. | Sergeant Mara says, "The road you see just past the gate is called the north road." | 608 / 27 | 1080.3 | ungrounded_authoritative_rule | No issue identified in this sample |

Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
