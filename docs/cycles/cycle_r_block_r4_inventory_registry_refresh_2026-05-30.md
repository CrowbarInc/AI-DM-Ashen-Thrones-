# Cycle R / R4 — Inventory Refresh + Registry Neighbor Expansion

**Date:** 2026-05-30  
**Status:** Complete — governance refresh green.

---

## Inventory count before / after

| Metric | Before (stale snapshot) | After (`py -3 tools/test_audit.py`) |
| --- | --- | --- |
| `summary.generated_utc` | 2026-04-25T00:34:24Z | 2026-05-30T19:07:18Z |
| `files[]` rows | **260** | **306** |
| Collected tests | **3419** (stale per-test rows) | **4247** (live `pytest --collect-only`) |
| Schema version | 2 | 2 |

The prior inventory under-counted modules and tests; refresh aligns `tests/test_inventory.json` with the current suite.

---

## Registry entries changed

### New responsibility groups (17 total, was 15)

| Group id | Direct owner | Purpose |
| --- | --- | --- |
| `final_emission_meta_projection` | `tests/test_final_emission_meta.py` | FEM projection / read-path semantics |
| `final_emission_visibility_semantics` | `tests/test_final_emission_visibility.py` | Visibility fallback semantics (phrase/stock replace path) |

### Updated groups (neighbor slots)

| Group id | Field | Paths added |
| --- | --- | --- |
| `final_emission_gate_orchestration` | `downstream_consumer_suites` | `test_turn_pipeline_shared.py`, `test_answer_completeness_rules.py`, `test_response_delta_requirement.py`, `test_interaction_continuity_repair.py`, `test_diegetic_fallback_narration.py` |
| `final_emission_meta_projection` | `downstream_consumer_suites` | `test_turn_packet_stage_diff_integration.py`, `test_diegetic_fallback_narration.py` |
| `final_emission_visibility_semantics` | `downstream_consumer_suites` | `test_turn_pipeline_shared.py` |
| `output_sanitizer_final_string_cleanup` | `downstream_consumer_suites` | `test_turn_pipeline_shared.py`, `test_prompt_and_guard.py` |
| `prompt_context_contract_assembly` | `downstream_consumer_suites` | `test_prompt_and_guard.py` |
| `social_emission_legality_surface` | `downstream_consumer_suites` | `test_answer_completeness_rules.py`, `test_response_delta_requirement.py` |
| `gauntlet_playability_validation` | `gauntlet_suites` | `test_golden_replay.py` (with existing `test_behavioral_gauntlet_smoke.py`) |

### Governance allowlist (inventory refresh fallout)

Four cross-file duplicate `test_*` names between `test_realization_layer_audit.py` and `test_realization_provenance_audit.py` were newly visible after refresh; added to `_CROSS_FILE_DUPLICATE_ALLOWLIST` with reasons (parallel audit-tool smoke, not duplicate semantics).

---

## Downstream / smoke neighbors added (Cycle R–touched)

| File | Registry roles (post-R4) |
| --- | --- |
| `tests/test_turn_pipeline_shared.py` | `downstream_consumer_suite` → gate orchestration, visibility semantics, output sanitizer |
| `tests/test_prompt_and_guard.py` | `downstream_consumer_suite` → prompt context, output sanitizer |
| `tests/test_golden_replay.py` | **`gauntlet_suite`** → gauntlet/playability (replay/observation; **not** gate `downstream_consumer`) |
| `tests/test_answer_completeness_rules.py` | `downstream_consumer_suite` → gate orchestration, social emission legality |
| `tests/test_response_delta_requirement.py` | `downstream_consumer_suite` → gate orchestration, social emission legality |
| `tests/test_interaction_continuity_repair.py` | `downstream_consumer_suite` → gate orchestration |
| `tests/test_diegetic_fallback_narration.py` | `downstream_consumer_suite` → gate orchestration, FEM meta projection |
| `tests/test_turn_packet_stage_diff_integration.py` | `downstream_consumer_suite` → FEM meta projection |

Machine-readable index: `tests/test_inventory.json` → `ownership_registry_index.files_roles` (regenerated with audit).

---

## Ownership boundaries documented (post R1–R3)

| Concern | Canonical direct owner | Downstream may… |
| --- | --- | --- |
| Final-emission **gate orchestration** (layer order, `final_route` tables, opening/strict-social integration) | `tests/test_final_emission_gate.py` | Smoke route-class / FEM fields; **not** re-lock full route matrices |
| FEM **projection / read** semantics | `tests/test_final_emission_meta.py` | Assert FEM attachment / key presence |
| **Phrase legality** (procedural bans, sanitizer strings, visibility stock, question-resolution tables) | `tests/test_output_sanitizer.py`, `tests/test_final_emission_visibility.py`, `tests/test_social_exchange_emission.py` | HTTP or application smoke only (R2 thinned pipeline/social consumers) |
| **Golden replay** structural observation | `tests/test_golden_replay.py` (gauntlet replay neighbor) | **Must not** be thinned as downstream duplication of gate/sanitizer owners |

Narrative also added to `tests/TEST_AUDIT.md` (Cycle R governance paragraph).

---

## Files intentionally not added (and why)

| Path | Reason |
| --- | --- |
| `tests/test_golden_replay.py` under `final_emission_gate_orchestration.downstream_consumer_suites` | Replay/observation is **not** gate downstream ownership; registered as **`gauntlet_suite`** only |
| `tests/test_broadcast_open_call_social.py` | Out of R4 neighbor list; open-call routing covered elsewhere |
| `tests/test_social_speaker_grounding.py` | R2 target only; not a gate/FEM neighbor in R4 scope |
| `tests/helpers/final_emission_gate_fixtures.py` | Support module (R1); not a collected `test_*.py` inventory row |
| `tests/test_final_emission_gate.py` / `tests/test_output_sanitizer.py` / owner suites | Already **direct_owner** entries — neighbors point *to* consumers, not owners |
| Long-session / transcript / structural replay modules | Preserved as replay/transcript coverage; not expanded in this pass |

---

## Files changed (governance only)

| File | Change |
| --- | --- |
| `tests/test_inventory.json` | Regenerated via `tools/test_audit.py` |
| `tests/test_ownership_registry.py` | Neighbor expansion + 2 new groups + audit duplicate allowlist |
| `tests/TEST_AUDIT.md` | Cycle R governance boundary paragraph |

**Production code:** none.  
**Test assertions:** none (only registry allowlist entries required by post-refresh governance validation).

---

## Tests run and results

| Command | Result |
| --- | --- |
| `py -3 tools/test_audit.py` | **PASS** — wrote inventory (4247 tests, 306 files) |
| `py -3 -m pytest tests/test_ownership_registry.py tests/test_test_audit_tool.py -q` | **PASS** (25 items) |
| `py -3 -m pytest tests/test_golden_replay.py -m golden_replay -q` | **PASS** (53 items) |

---

## Confirmation: governance-only

- No `game/` or runtime modules modified.
- No downstream test assertion changes for R1–R3 behavior.
- Registry/inventory/TEST_AUDIT updates document ownership after fanout reduction; golden replay and gate/meta **direct_owner** suites remain authoritative for route and replay semantics.
