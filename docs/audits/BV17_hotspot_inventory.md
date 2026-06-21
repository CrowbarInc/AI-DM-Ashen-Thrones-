# BV17 — Hotspot Inventory

**Date:** 2026-06-21  
**Scope:** Entire repository (post BV16C closeout)  
**Method:** `python scripts/bu_final_emission_coupling_discovery.py` + `python tools/bv17_hotspot_reassessment.py`  
**Primary question:** After retiring major hubs and fallback families, what is the largest remaining source of maintenance cost?

---

## Executive answer

Post BV12–BV16C, remaining fan-in concentrates in governed domain authorities and legitimate production owners — not accidental hubs.

**Recommended next cycle:** **REPOSITORY_CONTRACTION_COMPLETE**

Post BV12–BV16C, the top-25 concentration is dominated by governed domain authorities (smoke 99 FI, text 59 FI, social 82 FI, gate/terminal 41 FI) and legitimate production authorities. Accidental compat shim FI totals 18 (text 4 + social 12 + smoke 2). No module exceeds 8% ecosystem fan-in share. Remaining optional work (visibility test seams, 1 fallback event) is marginal ROI.

---

## Repository hotspot scan

### Concentration summary

| Metric | Value |
| --- | --- |
| Modules (BU + supplemental) | 230 |
| Total fan-in | 1109 |
| Top-1 share | 5.1% |
| Top-5 share | 18.9% |

### Fan-in / fan-out by maintenance area

| Area | Modules | Fan-in | Fan-out | Top module (FI/FO) |
| --- | --- | --- | --- | --- |
| replay | 10 | 137 | 34 | tests.helpers.replay_fem_read_smoke (56/1) |
| fallback | 7 | 90 | 53 | game.final_emission_visibility_fallback (31/20) |
| attribution | 11 | 133 | 24 | game.realization_provenance (29/1) |
| final_emission | 42 | 386 | 222 | game.final_emission_text_formatting (51/0) |
| speaker_finalize | 6 | 34 | 36 | game.speaker_contract_enforcement (15/7) |
| tests_smoke | 4 | 59 | 10 | tests.helpers.gate_orchestration_smoke (39/2) |
| tests_registry | 1 | 0 | 57 | tests.test_ownership_registry (0/57) |
| text_domain | 0 | 0 | 0 | — |
| social_domain | 5 | 94 | 33 | game.social_exchange_policy (33/8) |

### Post-contraction domain clusters

| Cluster | FI | Status |
| --- | --- | --- |
| Smoke domain hubs (replay_fem + gate_orch + fallback_bridge) | 99 | Governed (BV12C) |
| Smoke compat shims (replay_smoke + gate_integration) | 2 | Shim-only (FI ≤2 each) |
| Text domain hubs (formatting + policy) | 59 | Governed (BV13C) |
| Text compat barrel | 4 | Shim-only (FI 4) |
| Social domain hubs (policy + catalog + validation + projection) | 82 | Governed (BV14C) |
| Social compat barrel | 12 | Shim-only (FI 12, capped) |
| Gate + terminal authorities | 41 | Governed (BV15/BV16C) |
| Read-side authority cluster | 19 | Closed (BV10) |
| Read facades | 48 | Governed (BV10) |

### Helper concentration

| Metric | Value |
| --- | --- |
| Helper modules | 34 |
| Helper FI total | 318 |
| Top-3 helper share | 37.1% |

| Helper module | FI | FO |
| --- | --- | --- |
| tests.helpers.replay_fem_read_smoke | 56 | 1 |
| tests.helpers.gate_orchestration_smoke | 39 | 2 |
| tests.helpers.opening_fallback_evidence | 23 | 4 |
| tests.helpers.failure_dashboard_report | 16 | 7 |
| tests.helpers.emission_smoke_assertions | 15 | 5 |
| tests.helpers.replay_drift_taxonomy | 15 | 3 |
| tests.helpers.strict_social_harness | 15 | 7 |
| tests.helpers.golden_replay_projection | 14 | 6 |
| tests.helpers.failure_classifier | 13 | 4 |
| tests.helpers.failure_classification_sync | 12 | 10 |

### Governance concentration

| Signal | Value |
| --- | --- |
| Ownership registry collectors (`collect_*`) | 114 |
| Gate thin boundary lock lines | 929 |
| Registry bv12c markers | 52 |
| Registry bv13c markers | 49 |
| Registry bv14c markers | 52 |
| Registry bv15 markers | 0 |
| Registry bv16 markers | 26 |

### Recurrence concentration (BV8A view, unchanged)

| Metric | Before | After |
| --- | --- | --- |
| Total rows | 11 | 4 |
| Recurring keys | 1 | 0 |
| Dominant share | 0.7273 | 0.25 |

### Fallback concentration (unchanged)

| Snapshot | Fallback incidence | Events | Eligible turns |
| --- | --- | --- | --- |
| BV1B / current | 1.05% | 1 | 95 |

### Ownership concentration (domain refs)

| Ownership domain | Reference count |
| --- | --- |
| fallback_ownership | 2542 |
| gate_ownership | 660 |
| final_emission_ownership | 325 |
| speaker_ownership | 102 |
| replay_ownership | 77 |
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

---

## Evidence

| Source | Role |
|---|---|
| `docs/audits/BU_import_fan_in_fan_out.csv` | Fresh BU AST import graph (223 modules) |
| Full-repo AST scan | Social/read modules outside BU filter |
| `artifacts/bv11_hotspot_analysis.json` | BV11 baseline for deltas |
| `artifacts/bv8a_recurrence_history.json` | Recurrence view |
| `artifacts/bv1b_fallback_summary.json` | Fallback incidence |
| BV12–BV16C closeout reports | Contraction trajectory |

