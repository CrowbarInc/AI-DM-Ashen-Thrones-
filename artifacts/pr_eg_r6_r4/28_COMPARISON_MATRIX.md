# 28 — Comparison Matrix

| Architecture | Supported answer success | Relevance | Sufficiency | Acceptance errors | Rejections of answerable cases |
|---|---:|---:|---:|---:|---:|
| A | 158/168 (94.0%) | 165/168 (98.2%) | 160/168 (95.2%) | 0 | 3 |
| B | 160/168 (95.2%) | 160/168 (95.2%) | 160/168 (95.2%) | 0 | 8 |
| C | 53/168 (31.5%) | 53/168 (31.5%) | 85/168 (50.6%) | 0 | 83 |


| Core stratum | A supported success | B supported success | C supported success |
|---|---:|---:|---:|
| DIRECT | 48/56 (85.7%) | 48/56 (85.7%) | 4/56 (7.1%) |
| PARTIAL | 30/32 (93.8%) | 32/32 (100.0%) | 1/32 (3.1%) |
| RELATED_NONANSWER | 32/32 (100.0%) | 32/32 (100.0%) | 0/32 (0.0%) |
| UNKNOWN | 32/32 (100.0%) | 32/32 (100.0%) | 32/32 (100.0%) |
| RESTRICTED | 16/16 (100.0%) | 16/16 (100.0%) | 16/16 (100.0%) |
| multi_role | 9/16 (56.2%) | 16/16 (100.0%) | 2/16 (12.5%) |
| paraphrase | 8/8 (100.0%) | 8/8 (100.0%) | 0/8 (0.0%) |
| open_world | 8/8 (100.0%) | 8/8 (100.0%) | 0/8 (0.0%) |


Validation/holdout paired counts against A:

{
  "validation": {
    "B": {
      "wins": 4,
      "losses": 3,
      "net": 1
    },
    "C": {
      "wins": 0,
      "losses": 41,
      "net": -41
    }
  },
  "holdout": {
    "B": {
      "wins": 3,
      "losses": 3,
      "net": 0
    },
    "C": {
      "wins": 0,
      "losses": 39,
      "net": -39
    }
  }
}

B has zero provider calls but high fact authoring/vocabulary cost. A has the lowest integration change because it is existing behavior; its gold-control success overstates production readiness. C adds a call and this prototype's strict validation rejects most proposals. A/B/C all pass tested source access checks. C has not earned generalization claims; B generalizes the unification algorithm but not semantic extraction. No architecture wins the combined authoring, correctness, production-interpretation and security decision.
