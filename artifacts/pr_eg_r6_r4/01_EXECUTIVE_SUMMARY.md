# 01 — Executive Summary

No production migration is justified. The primary comparison isolates correspondence using gold question meanings and identical eligible prose. B requires authored facts, while C must validate AI proposals against those facts. B recovers structured answers cheaply but loses prose-only cases; C mostly fails its proposal contract. Actual production interpretations reduce B substantially.

| Architecture | Supported answer success | Relevance | Sufficiency | Acceptance errors | Rejections of answerable cases |
|---|---:|---:|---:|---:|---:|
| A | 158/168 (94.0%) | 165/168 (98.2%) | 160/168 (95.2%) | 0 | 3 |
| B | 160/168 (95.2%) | 160/168 (95.2%) | 160/168 (95.2%) | 0 | 8 |
| C | 53/168 (31.5%) | 53/168 (31.5%) | 85/168 (50.6%) | 0 | 83 |


This table covers 168 nonambiguous cases. All 176 cases and the excluded ambiguity diagnostics are preserved. B/C consumed a gold ambiguity bit that the A kernel did not: that defect prevents using the eight ambiguity cases as evidence of superiority. A is the unchanged production correspondence kernel/prompt inside a shared aggregator, not a full production rewrite or /api/chat qualification.

Verdict: **C — INCONCLUSIVE / FURTHER DISCOVERY REQUIRED**. There were zero tested source-access violations; semantic correctness and low manual authoring burden remain unresolved. Do not begin PR-EH.
