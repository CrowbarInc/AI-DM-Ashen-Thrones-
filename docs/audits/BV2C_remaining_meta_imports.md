# BV2C — Remaining `final_emission_meta` Direct Imports

**Date:** 2026-06-21  
**Baseline:** 31 importers (post-BV2B)  
**Post-BV2C:** **22 importers** (20 production + 2 governance/owner tests)

---

## Classification summary

| Class | Count | Policy |
|---|---:|---|
| Write owner (production) | 19 | Allowed — canonical FEM packaging authority |
| Read facade delegate | 1 | Allowed — `final_emission_meta_read` delegates to meta |
| FEM owner test suite | 1 | Allowed — `tests/test_final_emission_meta.py` |
| Import governance owner | 1 | Allowed — `tests/test_ownership_registry.py` |

All other modules must route read traffic through `final_emission_meta_read`, `final_emission_owner_bucket_views`, or `final_emission_replay_projection`.

---

## Production write owners (19 + delegate)

| Module | Role | Key symbols |
|---|---|---|
| `game/fallback_provenance_debug.py` | Fallback provenance packaging | `patch_final_emission_meta`, provenance keys |
| `game/final_emission_acceptance_quality.py` | N4 acceptance merge | `ensure_final_emission_meta_dict` |
| `game/final_emission_fem_assembly.py` | FEM assembly merges | NA/response-type merge helpers |
| `game/final_emission_finalize.py` | Finalize / sidecar packaging | `patch_final_emission_meta`, channel sidecar |
| `game/final_emission_gate_preflight_defaults.py` | Preflight layer defaults | `default_response_type_debug`, NA defaults |
| `game/final_emission_generic_exit.py` | Generic accept/replace exit | stamps, `response_type_decision_payload` |
| `game/final_emission_narration_constraint_debug.py` | Narration debug merge owner | `build/merge_narration_constraint_debug_meta` |
| `game/final_emission_narrative_mode_output.py` | NMO trace packaging | `merge_narrative_mode_output_into_final_emission_meta` |
| `game/final_emission_opening_fallback.py` | Opening fallback stamps | `stamp_opening_fallback_owner_bucket`, result meta |
| `game/final_emission_repairs.py` | Gate repair packaging | NA merge, producer stamps |
| `game/final_emission_response_type.py` | Response-type debug | `default_response_type_debug`, opening bucket stamp |
| `game/final_emission_sealed_fallback.py` | Sealed fallback stamps | `refresh_final_emission_mutation_lineage` |
| `game/final_emission_strict_social_stack.py` | Strict-social trunk | stamps, `response_type_decision_payload` |
| `game/final_emission_terminal_pipeline.py` | Terminal pipeline | `ensure_final_emission_meta_dict`, producer stamps |
| `game/final_emission_visibility_fallback.py` | Visibility fallback stamps | producer stamps, `stamp_visibility_fallback_owner_bucket_from_fields` |
| `game/gm_retry.py` | Retry terminal fallback | `read_final_emission_meta_dict` (co-located write stamp) |
| `game/interaction_continuity.py` | IC attach (lazy) | `ensure_final_emission_meta_dict` |
| `game/output_sanitizer.py` | Sanitizer producer attribution | `PRODUCER_REPAIR_KIND_*` |
| `game/upstream_response_repairs.py` | Upstream opening packaging (lazy) | `stamp_upstream_prepared_opening_producer_metadata` |
| `game/final_emission_meta_read.py` | **Read facade delegate** | All read-side re-exports |

### Migrated off meta in BV2C (production)

| Module | New import path |
|---|---|
| `game/opening_deterministic_fallback.py` | Owns `default_opening_fallback_context_mirror_values`; meta delegates |
| `game/narrative_authenticity.py` | `build_narrative_authenticity_emission_trace` via `final_emission_repairs` |
| `game/final_emission_sealed_fallback.py` | Bucket mapper via `owner_bucket_views` |
| `game/final_emission_visibility_fallback.py` | Bucket mapper via `owner_bucket_views` |
| `game/post_emission_speaker_adoption.py` | (BV2B) `meta_read` |

---

## Test / helper importers removed in BV2C

| Former importer | Migration |
|---|---|
| `tests/test_tone_escalation_rules.py` | `meta_read.default_response_type_debug` |
| `tests/test_final_emission_boundary_convergence.py` | `meta_read.default_response_type_debug` |
| `tests/test_opening_fallback_owner_bucket.py` | `meta_read.final_emission_meta_read_side_surface`; bucket via views |
| `tests/test_final_emission_gate_selector_snapshots.py` | `meta_read.infer_accept_path_final_emitted_source` |
| `tests/test_final_emission_channel_separation.py` | Read via `meta_read`; sidecar test moved to meta owner suite |
| `tests/test_final_emission_narration_constraint_debug.py` | Via `final_emission_narration_constraint_debug` module namespace |
| `tests/test_narrative_mode_output_validator.py` | Via `final_emission_narrative_mode_output` re-exports |

---

## Permanent test importers (2)

| Module | Class | Reason |
|---|---|---|
| `tests/test_final_emission_meta.py` | FEM owner suite | Canonical regression for meta surface, packaging, observability |
| `tests/test_ownership_registry.py` | Governance | Boundary locks; dynamic `import game.final_emission_meta as emission_meta` in BJ tests |

---

## Compatibility shims removed (BV2C)

| Removed re-export | Replacement |
|---|---|
| `opening_fallback_owner_bucket_from_*` on meta | `final_emission_owner_bucket_views` (private `_` aliases retained internally on meta for stamps) |
| `sealed_fallback_owner_bucket_from_fields` on meta | `final_emission_owner_bucket_views` |
| `visibility_fallback_owner_bucket_from_fields` on meta | `final_emission_owner_bucket_views` |
| `default_opening_fallback_context_mirror_values` body on meta | `opening_deterministic_fallback` (meta imports canonical definition) |

---

## Tools (out of ecosystem FI scan)

| Tool | Status |
|---|---|
| `tools/fallback_projection_coverage_audit.py` | Side-effect import order anchor (unchanged) |
| `tools/fallback_projection_gap_reality_audit.py` | Side-effect import order anchor (unchanged) |
| `tools/refresh_protected_replay_manifest.py` | Migrated → `meta_read.opening_fallback_metadata_field_registry_parity_errors` |

---

## Registry enforcement

Import lock enforced by:

- `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades`
- `test_bv2c_final_emission_meta_direct_import_guard_detects_synthetic_violation`
- `_BV2C_META_WRITE_OWNER_GAME_MODULES` production allowlist
- `_BV2C_META_DIRECT_IMPORT_TEST_ALLOWLIST` (2 paths)

New direct read imports of `game.final_emission_meta` outside these allowlists fail CI.
