# BV7B — Consumer-Layer Smoke Extraction

**Date:** 2026-06-21  
**Scope:** Extract AC/RD/RT consumer seams from `emission_smoke_assertions`; migrate consumers; measure fan-in.  
**Constraint:** No runtime, replay, or assertion semantic changes.

---

## Executive summary

BV7B split the three residual consumer-layer assertion families into dedicated helper modules, kept `emission_smoke_assertions` as a **compatibility barrel** (re-exports via `__all__`), and migrated **16 consumer suites** to direct family imports.

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| **`emission_smoke_assertions` FI** | **30** | **15** | **−15 (−50%)** |
| **`replay_smoke_assertions` FI** | 46 | **46** | 0 |
| **`gate_integration_smoke` FI** | 39 | **39** | 0 |
| **`response_type_smoke` FI** | 0 (n/a) | **16** | +16 (new) |
| **`actor_consistency_smoke` FI** | 0 (n/a) | **4** | +4 (new) |
| **`route_determinism_smoke` FI** | 0 (n/a) | **4** | +4 (new) |
| Phase target (12–18 on monolith) | — | **15** | **Met** |

> **Note:** New family modules use lazy `game.*` delegates (same as pre-extraction monolith). BU ecosystem scan only lists modules with top-level production imports; family FI above counts **direct Python importers** (including the compatibility barrel). Re-run `python scripts/bu_final_emission_coupling_discovery.py` after any top-level import alignment if BU CSV rows for family modules are required.

---

## Modules created

| Module | Symbols owned | Production fan-out (lazy) |
|---|---|---|
| `tests/helpers/response_type_smoke.py` | `response_type_contract`, `enforce_response_type_contract_layer`, `assert_response_type_meta`, `assert_response_type_contract_surfaces` | `game.final_emission_response_type` |
| `tests/helpers/actor_consistency_smoke.py` | `validate_answer_completeness`, `apply_answer_completeness_layer`, `skip_answer_completeness_layer` | `game.final_emission_validators`, `game.final_emission_repairs` |
| `tests/helpers/route_determinism_smoke.py` | RD validator/repair seams + boundary validate-only smoke | `game.final_emission_validators`, `game.final_emission_repairs` |

`tests/helpers/emission_smoke_assertions.py` retains phrase/route/speaker smoke, re-exports all extracted symbols, and imports family modules for the barrel.

---

## Consumer migration

**Method:** `scripts/bv7b_migrate_consumer_imports.py` — AST import split by RT/AC/RD symbol class.

| Category | Files migrated |
|---|---:|
| Response-type (RT) only or RT + smoke split | 14 |
| Actor-consistency (AC) + RD mixed | 3 |
| **Total files touched** | **30** (includes monolith-only rewrites) |
| **Net FI reduction** | **15 importers** left on monolith |

**Remaining monolith importers (15):** phrase/route/speaker smoke suites, contract test (partial), and `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH` constant consumer.

---

## Governance updates

| Area | Change |
|---|---|
| BJ-4 registry lock | Validates BV7B family modules + monolith `__all__` re-exports |
| `_BD6_*_SMOKE_FACADE` paths | Added RT/AC/RD facade paths |
| `_BV7B_EXTRACTED_*_SYMBOLS` | Registry constants for extracted families |

---

## Regression validation

```text
pytest tests/test_emission_smoke_assertions_contract.py
pytest tests/test_turn_pipeline_shared.py
pytest tests/test_ownership_registry.py -k smoke
pytest tests/test_response_delta_requirement.py
pytest tests/test_answer_completeness_rules.py
pytest tests/test_final_emission_boundary_convergence.py
```

---

## Evidence

| Source | Role |
|---|---|
| `docs/audits/BU_import_fan_in_fan_out.csv` | Post-BV7B monolith FI (15) |
| [BV7B_remaining_importers.md](BV7B_remaining_importers.md) | Residual importer inventory |
| [BV7B_hub_reclassification.md](BV7B_hub_reclassification.md) | Hub concentration analysis |
| [BV7A_bridge_extraction.md](BV7A_bridge_extraction.md) | Pre-BV7B baseline (30 FI) |
