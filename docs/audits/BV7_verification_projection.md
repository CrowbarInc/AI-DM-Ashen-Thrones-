# BV7 — Smoke Facade Verification Projection

**Date:** 2026-06-21 (updated post-BV7A)  
**Scope:** Project fan-in and maintenance impact through smoke facade decomposition.

---

## BV7A actuals (2026-06-21)

| Module | BV7 baseline | BV7A after | Delta |
|---|---:|---:|---:|
| `emission_smoke_assertions` | **73** | **30** | **−43** |
| `replay_smoke_assertions` | — | **46** | +46 (new) |
| `gate_integration_smoke` | — | **39** | +39 (new) |

**BV7A phase target (monolith ≤55):** **Met** at **30 FI**.

Bridge extraction + 64 consumer migrations completed in a **single cycle** (combined planned Phase 1 re-export split and Phase 2A/2B migration). See [BV7A_bridge_extraction.md](BV7A_bridge_extraction.md).

---

## Fan-in projection (revised)

| Stage | `emission_smoke_assertions` FI | Ecosystem #1 hub | Status |
|---|---:|---|---|
| BV7 baseline | **73** | Yes | Complete |
| BV7A (extract + migrate bridges) | **30** | No | **Complete** |
| BV7B (consumer-layer smoke extract) | **~12–18** | No | Planned |
| BV7C (route/phrase/speaker smoke split) | **~5–10** | No | Planned |
| BV7D (governance / barrel retirement) | **≤5** | No | Planned |

**Largest FI nodes post-BV7A:** `replay_smoke_assertions` (46), `gate_integration_smoke` (39), then production hubs (`final_emission_text` / `social_exchange_emission` at 52). Monolith hub warning **cleared**.

---

## Maintenance impact (current vs projected)

| Work type | Pre-BV7A | Post-BV7A (now) | Post BV7B–D |
|---|---|---|---|
| FEM read path change | 42 files via monolith | **43 via `replay_smoke_assertions`** | Unchanged owner |
| Gate orchestration seam change | 37 files via monolith | **37 via `gate_integration_smoke`** | Unchanged owner |
| Smoke phrase tuple edit | 4 files + monolith | 4 files + monolith | ≤2 modules |
| Route smoke assertion edit | 8 files + monolith | 8 files + monolith | `route_smoke_assertions` |
| New integration test default import | Added to #1 hub | **Must target bridge module** | Registry-governed |
| Monolith re-export compatibility | n/a | **Active** (`__all__`) | Deprecated → removed |

---

## Remaining migrations

| Bucket | Importers still on monolith | Est. Δ FI | Risk |
|---|---:|---:|---|
| Mixed smoke + AC/RD + `response_type_contract` | ~22 | −12 to −18 | Low–medium |
| Smoke-only (`turn_pipeline_shared`, social/open-call) | ~8 | −8 | Low |
| Contract / registry-owned facade tests | 2 | 0 (keep) | — |
| Barrel re-export consumers (compat) | 0 direct | — | Re-export only |

**Phase 2 achievable FI (BV7B):** **~12–18** on monolith after consumer-layer extraction and remaining mixed-suite migration.

---

## Success criteria

| Criterion | BV7 baseline | BV7A | BV7B target |
|---|---|---|---|
| Monolith FI | 73 | **30** ✓ | ≤18 |
| Monolith FI rank | #1 | **Not #1** ✓ | ≤#3 |
| Top symbol on monolith | 58% (`final_emission_meta_from_output`) | **N/A** (symbol moved) ✓ | ≤35% on any remaining symbol |
| Bridge ownership separated | No | **Yes** ✓ | — |
| Compatibility barrel intact | — | **Yes** ✓ | Until FI ≤5 |

---

## Recommendation (updated)

**BV7A validated the decomposition thesis.** Fan-in fell **−59%** on the monolith with zero semantic test changes. Continue with **BV7B consumer-layer smoke extraction** (`consumer_layer_smoke` / `repairs_consumer_facade` alignment) before pure route/phrase splits.

**Do not revert bridge imports** — new integration tests should import `replay_smoke_assertions` or `gate_integration_smoke` directly; use monolith only for phrase/route smoke or transitional compat.

---

## Evidence

| Source | Role |
|---|---|
| [BV7A_bridge_extraction.md](BV7A_bridge_extraction.md) | BV7A closeout metrics |
| [BV7_concentration_report.md](BV7_concentration_report.md) | Pre-BV7A hub analysis |
| [BV7_decomposition_candidates.md](BV7_decomposition_candidates.md) | Remaining extraction candidates |
| `docs/audits/BU_import_fan_in_fan_out.csv` | Authoritative FI scan |
