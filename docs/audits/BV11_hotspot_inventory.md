# BV11 — Hotspot Inventory

**Date:** 2026-06-21  
**Scope:** Entire repository (post BV10 closeout)  
**Method:** `python tools/bv11_hotspot_reassessment.py` + `scripts/bu_final_emission_coupling_discovery.py`  
**Primary question:** What is now the largest source of maintenance drag after BV10?

---

## Executive answer

Post-BV10, replay_smoke_assertions (FI 56) is the largest single module; the smoke bridge cluster (95 FI) exceeds gate/terminal convergence (56 FI).

**Recommended next cycle:** **BV12** — Smoke bridge domain decomposition (BV10B continuation)

---

## Repository hotspot scan

### Fan-in / fan-out by maintenance area

| Area | Modules | Fan-in | Fan-out | Top module (FI/FO) |
| --- | --- | --- | --- | --- |
| replay | 9 | 136 | 33 | tests.helpers.replay_smoke_assertions (56/1) |
| fallback | 7 | 76 | 50 | game.final_emission_visibility_fallback (17/18) |
| attribution | 11 | 132 | 23 | game.realization_provenance (28/1) |
| final_emission | 39 | 381 | 210 | game.final_emission_text (52/1) |
| speaker_finalize | 6 | 34 | 30 | game.speaker_contract_enforcement (15/4) |
| tests_smoke | 2 | 54 | 7 | tests.helpers.gate_integration_smoke (39/2) |
| tests_registry | 1 | 0 | 57 | tests.test_ownership_registry (0/57) |

### BV10 read-cluster closeout (supplemental)

| Cluster | FI |
| --- | --- |
| Authority cluster (meta_read + bucket + schema) | 19 |
| Read facades (attribution + observability + projection) | 48 |
| Smoke bridge (replay_smoke + gate_integration) | 95 |

### Recurrence concentration (BV8A view, unchanged)

| Metric | Before | After |
| --- | --- | --- |
| Total rows | 11 | 4 |
| Recurring keys | 1 | 0 |
| Dominant share | 0.7273 | 0.25 |
| Active keys | 4 | 3 |

### Fallback concentration (unchanged)

| Snapshot | Fallback incidence | Events | Eligible turns |
| --- | --- | --- | --- |
| BV1B / current | 1.05% | 1 | 95 |
| BV4B current | 1.05% | — | — |

### Ownership concentration (domain refs)

| Ownership domain | Reference count |
| --- | --- |
| fallback_ownership | 2539 |
| gate_ownership | 650 |
| final_emission_ownership | 321 |
| speaker_ownership | 102 |
| replay_ownership | 76 |
| semantic_replacement_attribution | 20 |

### Test concentration (import hubs)

| Game module | Test file count |
| --- | --- |
| game.storage | 93 |
| game.defaults | 77 |
| game.api | 54 |
| game.final_emission_gate | 46 |
| game.interaction_context | 45 |
| game.gm | 43 |
| game.final_emission_meta | 39 |
| game.prompt_context | 30 |
| game.ctir | 29 |
| game.leads | 28 |

Legacy smoke facade (emission_smoke, post-BV7): FI **17**, FO **9**

---

## Evidence

| Source | Role |
|---|---|
| `docs/audits/BU_import_fan_in_fan_out.csv` | Module FI/FO (BU ecosystem) |
| Full-repo AST scan | Read facade FI (outside BU filter) |
| `artifacts/bv9_hotspot_analysis.json` | BV9 baseline for deltas |
| `docs/audits/BV10_read_cluster_verification.md` | BV10 closeout verification |
| `artifacts/bv8a_recurrence_history.json` | Recurrence view |
| `artifacts/bv1b_fallback_summary.json` | Fallback incidence |

