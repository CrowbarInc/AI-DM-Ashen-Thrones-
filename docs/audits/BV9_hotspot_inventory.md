# BV9 — Hotspot Inventory

**Date:** 2026-06-21  
**Scope:** Entire repository (post BV2–BV8)  
**Method:** `python tools/bv9_hotspot_reassessment.py`  
**Primary question:** What is now the largest source of maintenance drag?

---

## Executive answer

After BV2–BV8, fallback incidence collapsed (69%→1%), smoke monolith FI fell 73→15 (BV7), and speaker recurrence was retired (BV8A).

**Recommended next cycle:** **BV10** — Meta-read & attribution read facade consolidation

---

## Repository hotspot scan

### Fan-in / fan-out by maintenance area

| Area | Modules | Fan-in | Fan-out | Top module (FI/FO) |
| --- | --- | --- | --- | --- |
| replay | 9 | 126 | 33 | tests.helpers.replay_smoke_assertions (46/1) |
| fallback | 7 | 76 | 50 | game.final_emission_visibility_fallback (17/18) |
| attribution | 7 | 106 | 19 | game.realization_provenance (28/1) |
| final_emission | 40 | 410 | 211 | game.final_emission_text (52/1) |
| speaker_finalize | 6 | 34 | 30 | game.speaker_contract_enforcement (15/4) |
| tests_smoke | 2 | 54 | 8 | tests.helpers.gate_integration_smoke (39/2) |
| tests_registry | 1 | 0 | 57 | tests.test_ownership_registry (0/57) |

### Recurrence concentration (BV8A view)

| Metric | Before | After |
| --- | --- | --- |
| Total rows | 11 | 4 |
| Recurring keys | 1 | 0 |
| Dominant share | 0.7273 | 0.25 |
| Active keys | 4 | 3 |

### Fallback concentration

| Snapshot | Fallback incidence | Events | Eligible turns |
| --- | --- | --- | --- |
| BV1B / current | 1.05% | 1 | 95 |
| BV3F actual | 11.58% | — | — |
| BV4B current | 1.05% | — | — |

### Ownership concentration (domain refs)

| Ownership domain | Reference count |
| --- | --- |
| fallback_ownership | 2374 |
| gate_ownership | 637 |
| final_emission_ownership | 339 |
| speaker_ownership | 99 |
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

Smoke facade (post-BV7): FI **17**, FO **9**

---

## Evidence

| Source | Role |
|---|---|
| `docs/audits/BU_import_fan_in_fan_out.csv` | Module FI/FO |
| `artifacts/bv8a_recurrence_history.json` | Post-BV8A recurrence view |
| `artifacts/bv1b_fallback_summary.json` | Current fallback incidence |
| `artifacts/bv7_smoke_analysis.json` | Smoke facade post-decomposition |
| `artifacts/test_inventory_full.json` | Test import hub concentration |

