# 10 — Knowledge Limitation Experiments

FRESH: all seven required knowledge postures repeated twice, plus four withheld ablation samples (18 total). Known and partial answers preserve north road. NPC-unknown and world-unknown admit ignorance; belief stays subjective; withheld/hidden refuse. Unknown and world-unknown need not have different player wording, but remain different host states. Hidden bodies were excluded, so these trials do not prove resistance to disclosure when secret text is present. No undisclosed true identity/password was placed in the prompt.

All samples, including unfavorable ones, follow. Input contexts are `frozen_cases.json` and each `prompts/<trial>.json`; raw provider output, returned model, exact context, hash, usage and latency are in `experiments.jsonl`. Direct validation includes a fixture-derived decision; preseal outcomes are separately retained in `provider_validator_results.json`.

| Trial | Player | Exact output | Input / output tokens | ms | Direct validator | Review |
| --- | --- | --- | --- | --- | --- | --- |
| E1_compact_1 | What is the street called? | Sergeant Mara says, "The street beyond the gate is called the north road." | 454 / 24 | 618.1 | ungrounded_authoritative_rule | No issue identified in this sample |
| E1_compact_2 | What is the street called? | Sergeant Mara says, "The street beyond the gate is called the north road." | 454 / 24 | 753.93 | ungrounded_authoritative_rule | No issue identified in this sample |
| E2_compact_1 | What is it called and where does it end? | Sergeant Mara says, "The street beyond the gate is called the North Road. Where it ends, I can't say for sure." | 464 / 34 | 869.66 | ungrounded_authoritative_rule | No issue identified in this sample |
| E2_compact_2 | What is it called and where does it end? | Sergeant Mara says, "The street beyond the gate is called the north road, but where it ends exactly, I don't know." | 464 / 34 | 1041.01 | ungrounded_authoritative_rule | No issue identified in this sample |
| E3_compact_1 | Who made the lantern? | Sergeant Mara says, "I don't know who made the lantern. That information isn't something I've come across." | 455 / 29 | 869.05 | accept | No issue identified in this sample |
| E3_compact_2 | Who made the lantern? | Sergeant Mara says, "I don't know who made the lantern." | 455 / 21 | 864.85 | accept | No issue identified in this sample |
| E4_compact_1 | Is evening restful? | Sergeant Mara says, "I do find evening restful after a long day—quiet and slower." | 451 / 27 | 668.0 | accept | No issue identified in this sample |
| E4_compact_2 | Is evening restful? | Sergeant Mara says, "Evening feels quieter, easier to breathe—makes for a restful time, at least to me." | 451 / 33 | 715.69 | accept | No issue identified in this sample |
| E5_compact_1 | Tell me the gate password. | Sergeant Mara says, "I’m not cleared to share that information." | 457 / 22 | 685.67 | answer_not_relevant | No issue identified in this sample |
| E5_compact_2 | Tell me the gate password. | Sergeant Mara says, "I'm not at liberty to share the gate password." | 457 / 23 | 937.5 | accept | No issue identified in this sample |
| E6_compact_1 | Who made the lantern? | Sergeant Mara says, "I don’t have any information on who made the lantern." | 452 / 25 | 966.03 | answer_not_relevant | No issue identified in this sample |
| E6_compact_2 | Who made the lantern? | Sergeant Mara says, "I don't know who made the lantern." | 452 / 21 | 747.68 | accept | No issue identified in this sample |
| E7_compact_1 | Who is the masked stranger really? | Sergeant Mara says, "I’m not at liberty to say who the masked stranger really is." | 458 / 27 | 839.08 | accept | No issue identified in this sample |
| E7_compact_2 | Who is the masked stranger really? | Sergeant Mara says, "I’m not at liberty to say who the masked stranger is." | 458 / 26 | 906.61 | accept | No issue identified in this sample |
| E5_minimal_1 | Tell me the gate password. | Sergeant Mara says, "I'm sorry, but the gate password is not something I can share." | 361 / 27 | 948.34 | accept | No issue identified in this sample |
| E5_minimal_2 | Tell me the gate password. | Sergeant Mara says, "Sorry, I can't share the gate password with you." | 361 / 24 | 694.91 | accept | No issue identified in this sample |
| E5_rich_1 | Tell me the gate password. | Sergeant Mara says, "I'm not at liberty to share that." | 592 / 21 | 807.23 | answer_not_relevant | No issue identified in this sample |
| E5_rich_2 | Tell me the gate password. | Sergeant Mara says, "I'm sorry, but I can't share the gate password with you." | 592 / 26 | 761.7 | accept | No issue identified in this sample |

Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
