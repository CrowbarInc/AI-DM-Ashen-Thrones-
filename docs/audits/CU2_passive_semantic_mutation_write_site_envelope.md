# CU2 Passive Semantic Mutation Write-Site Envelope

## Summary

CU2 adds passive, metadata-only write-site attribution for selected active-stream semantic mutations. It records where a mutation was written instead of relying only on later replay projection/classifier inference.

Runtime player-facing text behavior was not intentionally changed.

Protected replay schema was not promoted or expanded in this block.

## Files Changed

- `game/final_emission_meta.py`
- `game/output_sanitizer.py`
- `game/final_emission_terminal_pipeline.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_acceptance_quality.py`
- `game/final_emission_finalize.py`
- `game/fallback_provenance_debug.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_visibility_fallback.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/test_final_emission_meta.py`
- `tests/test_output_sanitizer.py`
- `tests/test_golden_replay_projection_semantic.py`
- `tests/test_final_emission_boundary_no_semantic_repair.py`
- `docs/audits/CU2_passive_semantic_mutation_write_site_envelope.md`

## Envelope Shape

Records are appended under:

- `semantic_mutation_write_sites`

The helper is:

- `game.final_emission_meta.append_semantic_mutation_write_site`

Fields are bounded metadata only. No full before/after text is stored.

Core fields:

- `mutation_id`
- `write_site_family`
- `write_site_file`
- `write_site_function`
- `before_semantic_hash`
- `after_semantic_hash`
- `selected_active_stream`
- `candidate_only`

Optional diagnostic fields:

- `owner`
- `route`
- `source`
- `speaker`
- `mutation_reason`
- `compatibility_status`
- `fallback_family`
- `repair_family`
- `turn_id`
- `replay_id`
- `trace_id`

Allowed families:

- `sanitizer`
- `fallback`
- `repair`
- `final_emission`

The list is capped at 16 records. Malformed metadata, unsupported families, and unchanged normalized hashes are no-ops.

## Families Wired

- Sanitizer: strip-only changes, legacy sentence rewrite changes, empty sanitizer fallback, strict-social sanitizer fallback, and gate-sealed sanitizer fallback.
- Fallback: sealed route replacements through `prepare_sealed_replacement_route_meta`, strict-social emergency fallback patch, and N4 sealed fallback replacement.
- Repair: fallback-behavior repair and referent/referential-clarity local repair paths.
- Final emission: final sanitizer/strip packaging, route-illegal strip/reseal, upstream fallback overwrite containment restoration, and accepted opening reassertion.

Prepared fallback candidates are not recorded. Records are appended only when selected text becomes the active stream.

## Projection

`tests/helpers/golden_replay_projection.py` now copies optional FEM `semantic_mutation_write_sites` into observed turn diagnostics when present.

This is diagnostic-only:

- It is absent-safe.
- It does not add a protected observation field.
- Existing semantic mutation summary projection remains intact.

## Tests Added Or Updated

- Helper append/no-op/bounding/no-full-text tests in `tests/test_final_emission_meta.py`.
- Sanitizer positive/no-op attribution assertions in `tests/test_output_sanitizer.py`.
- Selected sealed fallback attribution test in `tests/test_final_emission_meta.py`.
- Final-boundary strip attribution and referent repair attribution tests in `tests/test_final_emission_boundary_no_semantic_repair.py`.
- Diagnostic projection carry-through and protected-field non-promotion test in `tests/test_golden_replay_projection_semantic.py`.

## Validation

Passed:

- `pytest tests/test_final_emission_meta.py::test_semantic_mutation_write_site_helper_appends_bounds_and_omits_text tests/test_final_emission_meta.py::test_semantic_mutation_write_site_helper_noops_on_bad_metadata tests/test_final_emission_meta.py::test_prepare_sealed_replacement_route_meta_records_selected_fallback_write_site tests/test_output_sanitizer.py::test_strip_only_mode_drops_scaffold_without_diegetic_template_substitution tests/test_output_sanitizer.py::test_strip_only_preserves_clean_atmospheric_narration tests/test_golden_replay_projection_semantic.py::test_semantic_mutation_write_sites_project_diagnostically_not_protected tests/test_final_emission_boundary_no_semantic_repair.py::test_finalize_route_illegal_strip_records_final_emission_write_site tests/test_final_emission_boundary_no_semantic_repair.py::test_terminal_referent_clarity_repair_records_repair_write_site -q`
- `pytest tests/test_final_emission_visibility_fallback.py -q`
- `pytest tests/test_output_sanitizer.py -q`
- `pytest tests/test_golden_replay_projection_semantic.py tests/test_final_emission_boundary_no_semantic_repair.py -q`
- `pytest tests/test_gate_boundary_governance.py -q`

Broad focused attempt with full `tests/test_final_emission_meta.py` found an unrelated pre-existing static-lock failure:

- `tests/test_final_emission_meta.py::test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only`
- Offender reported: `tests/test_fallback_incidence_report.py:150:'compatibility_local_opening_deterministic'`

Compatibility-governance attempt also found unrelated pre-existing import guard failures outside this CU2 patch:

- `tests/helpers/replacement_attribution_inventory.py` direct read-cluster authority imports.
- `tests/test_golden_replay_projection_fallback_integration.py` direct `game.social_exchange_emission` compat-barrel import.

## Remaining Gaps

- Prompt/policy instrumentation is intentionally not included.
- Candidate-vs-selected fallback attribution remains limited to selected active-stream writes.
- Protected replay promotion is intentionally deferred.
- No large replay corpus was added or refreshed.
