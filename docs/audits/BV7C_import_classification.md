# BV7C — Residual Import Classification

**Date:** 2026-06-21  
**Scope:** Every remaining direct importer of `tests.helpers.emission_smoke_assertions` after BV7B consumer extraction.

Classification key:

| Label | Meaning |
|---|---|
| **intentional** | Deliberate smoke-core or compatibility-barrel use; should remain on monolith |
| **migration candidate** | Could move to a named family module with low risk, but not required at FI=15 |
| **compatibility-only** | Imports only via barrel re-export path or governance introspection |

---

## Static test importers

| Module | Classification | Rationale |
|---|---|---|
| `tests/test_turn_pipeline_shared.py` | **intentional** | Primary AL4 HTTP/pipeline smoke neighbor; phrase + route bundle is charter |
| `tests/test_emission_smoke_assertions_contract.py` | **intentional** | Facade contract owner for phrase/repair smoke surface |
| `tests/test_mixed_state_recovery_regressions.py` | **intentional** | Phrase hygiene smoke for recovery regressions |
| `tests/test_broad_address_social_bid.py` | **intentional** | Phrase + open-call route smoke |
| `tests/test_synthetic_smoke.py` | **intentional** | Synthetic pattern tuple owner |
| `tests/test_social_speaker_grounding.py` | **intentional** | Speaker grounding smoke |
| `tests/test_broadcast_open_call_social.py` | **intentional** | Open-call / broadcast routing smoke |
| `tests/test_interaction_continuity_repair.py` | **intentional** | Route + continuity speaker smoke |
| `tests/test_turn_packet_stage_diff_integration.py` | **intentional** | Route wiring smoke |
| `tests/test_c4_narrative_mode_live_pipeline.py` | **intentional** | Route wiring smoke (gate/replay on family modules) |
| `tests/test_diegetic_fallback_narration.py` | **intentional** | Route wiring smoke (gate on `gate_integration_smoke`) |
| `tests/test_empty_social_retry_regressions.py` | **intentional** | Route wiring smoke |
| `tests/test_opening_start_seam_regressions.py` | **intentional** | Route sentinel smoke |
| `tests/test_social_exchange_emission.py` | **intentional** | Route wiring smoke (legality on owner suite) |
| `tests/test_answer_completeness_rules.py` | **compatibility-only** | Retains `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH` monkeypatch constant; AC/RD migrated |

---

## Dynamic / governance importers

| Module | Classification | Rationale |
|---|---|---|
| `tests/test_ownership_registry.py` | **compatibility-only** | Module-level import for BJ-39 governance introspection only |
| `tests/test_final_emission_gate_delegator_regression.py` | **compatibility-only** | Lazy import in delegator regression harness |

---

## Helper-module importers (barrel fan-out, not test FI)

| Module | Classification | Rationale |
|---|---|---|
| `tests/helpers/response_type_smoke.py` | **compatibility-only** | Re-export barrel dependency |
| `tests/helpers/actor_consistency_smoke.py` | **compatibility-only** | Re-export barrel dependency |
| `tests/helpers/route_determinism_smoke.py` | **compatibility-only** | Re-export barrel dependency |
| `tests/helpers/gate_integration_smoke.py` | **compatibility-only** | Re-export barrel dependency |
| `tests/helpers/replay_smoke_assertions.py` | **compatibility-only** | Re-export barrel dependency |

---

## Migration candidates (optional, not scheduled)

| Module | Candidate target | Notes |
|---|---|---|
| `tests/test_answer_completeness_rules.py` | move `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH` to `strict_social_harness` or `response_type_smoke` | **Low priority** — single constant; would drop monolith FI by 1 |
| Phrase-heavy subset (5 suites) | `fallback_smoke_assertions.py` | **Deferred** — FI already in 12–18 target band; BE6 triple-layer lock preserved |
| Route subset (8 suites) | `route_smoke_assertions.py` | **Deferred** — overlap with speaker smoke on 2 suites |
| Speaker subset (4 suites) | `speaker_smoke_assertions.py` | **Deferred** — BV8 may supersede via golden replay speaker path |

**No migration candidate is required for BV7 closeout.** All remaining imports are either intentional smoke-core or compatibility-only barrel paths.

---

## Summary

| Classification | Count (static test importers) |
|---|---:|
| intentional | 14 |
| compatibility-only | 1 |
| migration candidate | 0 (required) |

**Verdict:** Residual monolith concentration is **fully intentional** at FI=15.
