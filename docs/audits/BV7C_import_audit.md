# BV7C — Final `emission_smoke_assertions` Import Audit

**Date:** 2026-06-21  
**Baseline:** `emission_smoke_assertions` FI = **15** (post-BV7B)  
**Method:** AST + import-regex scan (`scripts/bv7_smoke_facade_discovery.py`); reconciled with `scripts/bu_final_emission_coupling_discovery.py` (`docs/audits/BU_import_fan_in_fan_out.csv`).

---

## Executive answer

All **15 static fan-in importers** belong to intentional smoke families (phrase, route wiring, speaker/open-call) or the compatibility constant `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH`. **No residual AC/RD/RT or BV7A bridge imports** remain on the monolith. Two governance suites use dynamic module imports (excluded from static FI).

---

## Static importers (15) — all classified in-scope

| # | Module | Smoke family | Symbols imported |
|---:|---|---|---|
| 1 | `tests/test_turn_pipeline_shared.py` | phrase + route | phrase hygiene bundle + dialogue-lock route smoke |
| 2 | `tests/test_emission_smoke_assertions_contract.py` | phrase | repair/phrase smoke helpers (contract owner) |
| 3 | `tests/test_mixed_state_recovery_regressions.py` | phrase | `assert_global_visibility_stock_absent`, `assert_no_social_visible_intro_filler_smoke` |
| 4 | `tests/test_broad_address_social_bid.py` | phrase + speaker | `assert_no_unresolved_stock_phrases`, `assert_open_social_solicitation_route` |
| 5 | `tests/test_synthetic_smoke.py` | phrase | `SMOKE_SYNTHETIC_*` pattern tuples |
| 6 | `tests/test_social_speaker_grounding.py` | speaker | `assert_social_grounding_smoke` |
| 7 | `tests/test_broadcast_open_call_social.py` | speaker | open-call routing smoke bundle |
| 8 | `tests/test_interaction_continuity_repair.py` | route + speaker | route smoke + `assert_continuity_validation_failed_without_repair` |
| 9 | `tests/test_turn_packet_stage_diff_integration.py` | route | `assert_final_route_present_smoke` |
| 10 | `tests/test_c4_narrative_mode_live_pipeline.py` | route | `assert_final_route_*` |
| 11 | `tests/test_diegetic_fallback_narration.py` | route | `assert_final_route_*` |
| 12 | `tests/test_empty_social_retry_regressions.py` | route | `assert_final_route_replaced_or_not_accept` |
| 13 | `tests/test_opening_start_seam_regressions.py` | route | `has_non_accept_final_route_smoke` |
| 14 | `tests/test_social_exchange_emission.py` | route | `assert_final_route_replaced_or_not_accept` |
| 15 | `tests/test_answer_completeness_rules.py` | compatibility | `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH` only (AC/RD on family modules) |

---

## By smoke family

| Family | Importers | Verdict |
|---|---:|---|
| **Phrase smoke** | 5 | Intentional — BE6 layer-2 HTTP hygiene |
| **Route wiring smoke** | 8 | Intentional — AL3 downstream route sentinels |
| **Speaker / open-call smoke** | 4 | Intentional — social routing smoke (overlap with route on 2 suites) |
| **Compatibility constant** | 1 | Intentional — monkeypatch seam retained on monolith |
| **Intentional aggregation (barrel fan-out)** | 5 helper modules | Family modules + gate/replay bridges import monolith for re-export only |

---

## Dynamic importers (excluded from static FI)

| Module | Pattern | Purpose |
|---|---|---|
| `tests/test_ownership_registry.py` | `from tests.helpers import emission_smoke_assertions as smoke` | Governance introspection (BJ-39 RT seam) |
| `tests/test_final_emission_gate_delegator_regression.py` | lazy import in test body | Delegator regression harness |

---

## Out-of-scope importers (verified absent)

| Former family | Expected facade | Residual monolith imports |
|---|---|---:|
| Response-type (RT) | `response_type_smoke` | **0** |
| Actor-consistency (AC) | `actor_consistency_smoke` | **0** |
| Route-determinism (RD) | `route_determinism_smoke` | **0** |
| FEM read bridge | `replay_smoke_assertions` | **0** |
| Gate integration bridge | `gate_integration_smoke` | **0** |

---

## Evidence

| Source | Role |
|---|---|
| [BV7B_remaining_importers.md](BV7B_remaining_importers.md) | Pre-BV7C importer inventory |
| `artifacts/bv7_smoke_analysis.json` | Live AST scan (17 file hits incl. dynamic; 15 static FI) |
| `tests/test_ownership_registry.py` | `test_bv7c_emission_smoke_assertions_concentration_locked` |
| `docs/audits/BU_import_fan_in_fan_out.csv` | Module FI = 15 |
