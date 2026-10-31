# 19 — Corpus Design

170 manually authored questions; 34 distinct source families, 35 source records, 3 NPC profiles. Thirty fully eligible families contain 31 source records and five questions each. Four families test denied history/private/password/countersign evidence. Semantic situations are hand-written, not repeated template expansions. This is realistic synthetic prose, not sampled live campaign data.

Partitions: `{"development": {"families": 12, "cases": 60}, "validation": {"families": 11, "cases": 55}, "holdout": {"families": 11, "cases": 55}}`. Each family, including its two conflict records, stays in one partition. Categories and pre-authored claims/permissions reside in frozen partition JSON files.
