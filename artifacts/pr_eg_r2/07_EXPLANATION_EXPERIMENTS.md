# 07 — Explanation Experiments

FRESH: 6 compact and 4 matched ablation outputs. Compact includes cautious uncertainty and unprovided causes/directions. “Nobody seems to know” widens personal ignorance into a world knowledge claim. Both rich B1 samples admit not knowing, while both minimal B1 samples infer northern geography. A name is not proof of direction or historical cause. This is limited provider/prompt evidence, not a qualified explanatory rule.

All samples, including unfavorable ones, follow. Input contexts are `frozen_cases.json` and each `prompts/<trial>.json`; raw provider output, returned model, exact context, hash, usage and latency are in `experiments.jsonl`. Direct validation includes a fixture-derived decision; preseal outcomes are separately retained in `provider_validator_results.json`.

| Trial | Player | Exact output | Input / output tokens | ms | Direct validator | Review |
| --- | --- | --- | --- | --- | --- | --- |
| B1_compact_1 | Why do they call it that? | Sergeant Mara says, "They just call it the north road because it's the street beyond the gate heading north. Nobody seems to know exactly how it got that name, though." | 478 / 43 | 985.8 | ungrounded_authoritative_rule | Invents heading north and the knowledge of everyone else. |
| B1_compact_2 | Why do they call it that? | Sergeant Mara says, "They call it the north road, but I don’t know why it got that name exactly." | 478 / 32 | 789.41 | ungrounded_authoritative_rule | No issue identified in this sample |
| B2_compact_1 | Was it named by a king? | Sergeant Mara says, "I don't know if a king named it; all I can tell you is it's called the north road." | 478 / 34 | 756.46 | ungrounded_authoritative_rule | No issue identified in this sample |
| B2_compact_2 | Was it named by a king? | Sergeant Mara says, "I don't have any details about who named it." | 478 / 23 | 905.87 | accept | No issue identified in this sample |
| B3_compact_1 | Does the name tell us its history? | Sergeant Mara says, "The street is called the north road, but no one around here knows how it got that name." | 479 / 33 | 1141.88 | ungrounded_authoritative_rule | Expands own uncertainty into no one around here knowing the origin. |
| B3_compact_2 | Does the name tell us its history? | Sergeant Mara says, "The name just means it's the road north of here, but I don't know why they picked that in the first place." | 479 / 37 | 982.52 | ungrounded_authoritative_rule | Infers north-of-here geography from the name. |
| B1_minimal_1 | Why do they call it that? | Sergeant Mara says, "They just call it the north road because it leads out past the northern gate, nothing fancy beyond that." | 382 / 34 | 713.44 | ungrounded_authoritative_rule | Invents a northern gate and a naming cause. |
| B1_minimal_2 | Why do they call it that? | Sergeant Mara says, "They call it the north road because it’s the street just beyond the gate, heading north—though why that name stuck, I don't rightly know." | 382 / 43 | 924.98 | ungrounded_authoritative_rule | Infers northbound direction from the road name. |
| B1_rich_1 | Why do they call it that? | Sergeant Mara says, "I don’t know why it’s called that, only that it is." | 613 / 28 | 777.53 | accept | No issue identified in this sample |
| B1_rich_2 | Why do they call it that? | Sergeant Mara says, "I don’t know why it got that name, just that it’s called the north road." | 613 / 32 | 769.07 | ungrounded_authoritative_rule | No issue identified in this sample |

Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
