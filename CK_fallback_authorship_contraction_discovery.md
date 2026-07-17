# CK — Fallback Authorship Contraction Discovery

Discovery-only pass. No runtime behavior, fixtures, tests, or generated artifacts were changed.

Primary metric: **Fallback Surface Pressure** = fallback-reference concentration multiplied by ownership ambiguity and multi-file update pressure. High pressure means a fallback change is likely to require edits across runtime selection, metadata projection, replay observation, classifier/governance tests, and compatibility shims.

## Commands Used

```powershell
rg -n -i "fallback|fallback_owner|ownership fallback|metadata fallback|projection fallback|replay fallback|compatibility fallback|legacy fallback|fallback authorship|fallback attribution|fallback registry|fallback observation" .
rg --files
git status --short
rg -n -i --glob '!artifacts/**' --glob '!.git/**' --glob '!.venv/**' "fallback|fallback_owner|ownership fallback|metadata fallback|projection fallback|replay fallback|compatibility fallback|legacy fallback|fallback authorship|fallback attribution|fallback registry|fallback observation" .
rg -l -i --glob '!artifacts/**' --glob '!.git/**' --glob '!.venv/**' "fallback|fallback_owner|ownership fallback|metadata fallback|projection fallback|replay fallback|compatibility fallback|legacy fallback|fallback authorship|fallback attribution|fallback registry|fallback observation" .
rg -c -i --glob '!artifacts/**' --glob '!.git/**' --glob '!.venv/**' "fallback|fallback_owner|ownership fallback|metadata fallback|projection fallback|replay fallback|compatibility fallback|legacy fallback|fallback authorship|fallback attribution|fallback registry|fallback observation" .
rg -c -i --glob 'game/**' --glob 'tests/**' --glob 'tools/**' --glob 'scripts/**' --glob 'docs/**' --glob 'audits/**' --glob '!artifacts/**' --glob '!docs/archive/**' --glob '!*.bak' "fallback|fallback_owner|ownership fallback|metadata fallback|projection fallback|replay fallback|compatibility fallback|legacy fallback|fallback authorship|fallback attribution|fallback registry|fallback observation" . | Sort-Object {[int](($_ -split ':')[-1])} -Descending | Select-Object -First 40
rg -n "^(class|def) |^[A-Z0-9_]+\s*=|__all__|fallback_owner|fallback_family|owner_bucket|authorship|legacy|from_legacy|compat" game\final_emission_opening_fallback.py game\final_emission_visibility_fallback.py game\final_emission_sealed_fallback.py game\final_emission_meta.py game\final_emission_replay_projection.py game\runtime_lineage_telemetry.py game\fallback_provenance_debug.py game\diegetic_fallback_narration.py game\realization_authority.py game\realization_provenance.py game\gm_retry.py game\output_sanitizer.py game\social_exchange_emission.py game\api.py
rg -n "def |class |__all__|FALLBACK|fallback_owner|owner_bucket|authorship|legacy|compat" game\final_emission_ownership_schema.py game\final_emission_owner_bucket_views.py game\ownership_projection_views.py game\attribution_read_views.py game\upstream_response_repairs.py game\opening_deterministic_fallback.py game\final_emission_fem_assembly.py game\final_emission_generic_exit.py game\final_emission_terminal_pipeline.py
rg -n "^(class|def) |^[A-Z0-9_]+\s*=|fallback_owner|fallback_family|owner_bucket|authorship|legacy|from_legacy|compat" tests\helpers\golden_replay_projection_fallbacks.py tests\helpers\golden_replay_projection.py tests\helpers\failure_classifier.py tests\helpers\failure_classification_split_owner.py tests\helpers\opening_fallback_evidence.py tests\test_final_emission_meta.py tests\test_final_emission_opening_fallback.py tests\test_final_emission_visibility_fallback.py tests\test_final_emission_sealed_fallback.py tests\test_failure_classifier.py tests\test_runtime_lineage_telemetry.py tests\test_golden_replay_fallback_opening_projection.py tests\test_golden_replay_fallback_sealed_projection.py tests\test_golden_replay_fallback_visibility_projection.py tests\test_golden_replay_fallback_upstream_fast_projection.py tests\test_golden_replay_fallback_sanitizer_projection.py
```

Notes:

- The first raw search included `artifacts/**` and replay payload snapshots, producing very large generated-output hits. I treated those as compatibility/replay residue, not maintainable ownership code.
- The focused inventory excludes `artifacts/**`, `.git/**`, `.venv/**`, archived docs, and `.bak` files for pressure ranking. Generated artifacts still matter for migration risk, but they should not define runtime ownership.

## A. Fallback Reference Inventory

### Runtime Owners And Producers

| File | Matching symbols / functions / classes | Runtime behavior? | Governance/test support? | Compatibility or historical residue? | Classification |
|---|---|---:|---:|---:|---|
| `game/final_emission_ownership_schema.py` | `OPENING_FALLBACK_*`, `SEALED_FALLBACK_*`, `VISIBILITY_FALLBACK_*`, `ALLOWED_FALLBACK_SELECTION_OWNERS`, `ALLOWED_FALLBACK_CONTENT_OWNERS`, `GOVERNED_REALIZATION_FALLBACK_FAMILIES`, `fallback_owner_bucket_registry_surface`, `ownership_schema_registry_surface` | Yes, vocabulary used by runtime/read-side paths | Yes | Yes: legacy compatibility-local authorship sources and legacy realization families | **Runtime owner** for ownership vocabulary |
| `game/final_emission_owner_bucket_views.py` | `opening_fallback_owner_bucket_from_fields`, `opening_fallback_owner_bucket_from_meta`, `visibility_fallback_owner_bucket_from_fields`, `sealed_fallback_owner_bucket_from_fields` | Yes, derives owner buckets consumed by runtime/replay | Yes | Yes: compatibility-local authorship maps to `unknown-ambiguous` | **Runtime owner** for bucket mapping |
| `game/opening_deterministic_fallback.py` | `deterministic_opening_fallback_text_and_meta`, `opening_context_from_gm_output`, `OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER` | Yes, composes opening fallback prose/meta | Yes through tests | Yes: docstring still mentions gate compatibility recallback | **Runtime owner** for opening fallback content |
| `game/upstream_response_repairs.py` | `build_upstream_prepared_opening_fallback_payload`, `maybe_attach_upstream_prepared_opening_fallback_payload`, `OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED` import | Yes, stamps success-path opening authorship once | Yes | No active residue except compatibility key naming | **Runtime owner** for upstream-prepared opening authorship stamp |
| `game/final_emission_opening_fallback.py` | `build_opening_fallback_result_meta`, `build_upstream_prepared_opening_composition_meta`, `opening_fallback_authorship_source_from_composition_meta`, `select_opening_fallback_for_response_type_contract`, `opening_scene_safe_fallback_selection`, `opening_sealed_fallback_selection`, fail-closed meta helpers | Yes, selects/accepts/fail-closes opening fallback paths and projects metadata | Yes | Yes: `opening_fallback_compatibility_local_disabled` is a negative invariant | **Runtime owner** for opening fallback selection/application metadata; downstream of content |
| `game/final_emission_visibility_fallback.py` | `VisibilitySelectedFallback`, `from_legacy_tuple`, `as_legacy_tuple`, visibility fallback candidate builders, `standard_visibility_safe_fallback`, `apply_visibility_enforcement`, metadata payload classes | Yes, chooses and applies visibility/hard-replacement fallback candidates | Yes | Yes: legacy tuple adapter is intentionally retained | **Runtime owner** for visibility fallback selection and compatibility adapter |
| `game/final_emission_sealed_fallback.py` | sealed fallback selection helpers, branch selection, owner-bucket stamping, legacy tuple round trips | Yes, selects sealed terminal replacements and stamps sealed ownership/family | Yes | Yes: legacy/visibility tuple compatibility appears intentional at gate boundary | **Runtime owner** for sealed terminal fallback selection; compatibility layer |
| `game/final_emission_terminal_pipeline.py` | `apply_strict_social_emergency_fallback_patch`, `run_gate_terminal_enforcement_pipeline` | Yes, applies terminal fallback patches | Some | No major residue | **Runtime downstream consumer** |
| `game/final_emission_generic_exit.py` | `run_generic_replace_exit`, opening projection field copying with `include_authorship_source=False` | Yes, terminal accept/replace packaging | Yes | Some compatibility around selector debug fields | **Runtime downstream consumer** |
| `game/final_emission_fem_assembly.py` | `build_gate_accept_fem_base`, `build_gate_replace_fem_base`, `merge_gate_layer_metas_into_fem`, fast fallback neutral composition merge | Yes, assembles terminal FEM with fallback passthrough | Yes | No obvious removable residue | **Runtime downstream consumer** |
| `game/final_emission_meta.py` | FEM registries, `OPENING_FALLBACK_PROJECTION_FIELDS`, `apply_opening_fallback_projection_fields`, `stamp_opening_fallback_owner_bucket`, `stamp_retry_terminal_fallback_producer_metadata`, `apply_sanitizer_producer_attribution_to_fem`, read helpers, `build_fem_observability_events` | Yes, canonical FEM sidecar and runtime observability | Strong | Yes: legacy top-level FEM reads; compatibility-local authorship; sanitizer short trace fields | **Runtime owner** for metadata contract, plus compatibility layer |
| `game/final_emission_replay_projection.py` | `_fem_selected_fallback_projection`, `build_fem_runtime_lineage_events`, sealed subkind mapping, split owner fields | Yes, read-side runtime lineage events | Strong | Yes: legacy sealed/global replacement token and dual-family projection support | **Replay/observation consumer** with runtime-visible output |
| `game/runtime_lineage_telemetry.py` | `make_runtime_lineage_event`, `normalize_runtime_lineage_events`, `summarize_runtime_lineage_events`, owner/fallback frequencies | Yes, diagnostic event envelope | Strong | Some legacy sanitizer short-owner vocabulary through schema | **Replay/observation consumer** |
| `game/fallback_provenance_debug.py` | `attach_upstream_fast_fallback_provenance`, `record_final_emission_gate_entry`, `record_final_emission_gate_exit`, selector fingerprint/realignment | Yes, upstream fast-fallback provenance packaging | Strong | Self-described as debug/provenance; likely should be promoted or narrowed | **Runtime owner** for upstream-fast provenance packaging |
| `game/api.py` | `_synthetic_manual_play_gpt_budget_gm`, `_fast_fallback_for_upstream_error`-related stamps, `attach_realization_fallback_family(...GPT_BUDGET_OR_PROVIDER_FAILURE)` | Yes, upstream/API fast-fallback selector | Some | Many unrelated legacy adoption paths; fallback ownership only in fast path | **Runtime owner** for upstream-fast selection |
| `game/gm_retry.py` | retry fallback selectors/application, `force_terminal_retry_fallback`, deterministic retry fallback lines | Yes, retry fallback text/content and terminal retry family | Yes | Some older retry fallback route tokens remain protected | **Runtime owner** for retry fallback content |
| `game/social_exchange_emission.py` | `apply_strict_social_terminal_dialogue_fallback_if_needed`, `select_strict_social_emergency_fallback_line`, `strict_social_ownership_terminal_fallback`, social fallback catalog/export symbols | Yes, strict-social fallback content and terminal enforcement | Yes | Some compatibility around strict-social fallback families | **Runtime owner** for strict-social fallback content |
| `game/output_sanitizer.py` | `_diegetic_uncertainty_fallback`, `_prepared_upstream_empty_fallback_text`, `_mark_sanitizer_empty_fallback`, `_mark_sanitizer_strict_social_fallback`, `SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE` | Yes, sanitizer fallback selection and trace stamping | Yes | Yes: legacy sentence rewrite mode and short owner trace support | **Runtime owner** for sanitizer fallback selection; compatibility layer |
| `game/diegetic_fallback_narration.py` | `_FALLBACK_TEMPLATE_METADATA`, `fallback_template_metadata`, diegetic fallback renderers | Yes, template metadata/content provider | Yes | Legacy diegetic family remains governed, not safe to remove blindly | **Runtime owner** for diegetic fallback content registry |
| `game/realization_authority.py` | `FallbackFamily`, `FALLBACK_FAMILIES`, `legacy_diegetic_fallback`, `legacy_unclassified`, `fallback_family_owner`, `fallback_family_requires_metadata` | Runtime-declarative | Yes | Yes: legacy families are explicit governance states | **Runtime owner** for governed realization family registry |
| `game/realization_provenance.py` | `REALIZATION_FALLBACK_FAMILY_FIELD`, `normalize_realization_fallback_family`, `attach_realization_fallback_family`, `LEGACY_*` | Yes, stamps normalized realization family | Yes | Yes: ambiguous values default to `legacy_unclassified` | **Runtime owner** for realization family stamping |
| `game/attribution_read_views.py` | re-export facade for bucket/owner constants and mapping helpers | Indirect | Yes | Compatibility facade | **Compatibility layer** |
| `game/ownership_projection_views.py` | re-export/read vocabulary for lineage owner fields and sanitizer trace owner vocabulary | Indirect | Yes | Compatibility/read facade | **Compatibility layer** |

### Runtime Consumers With Fallback References

| File group | Representative files | Symbols / references | Runtime behavior? | Classification |
|---|---|---|---:|---|
| Final-emission validators/repair layers | `game/final_emission_repairs.py`, `game/final_emission_validators.py`, `game/final_emission_response_type.py`, `game/final_emission_fast_fallback_composition.py`, `game/final_emission_strict_social_stack.py`, `game/final_emission_passive_scene_pressure.py`, `game/final_emission_referential_clarity.py`, `game/final_emission_scene_emit_integrity.py`, `game/final_emission_first_mention_composition.py` | fallback route/source tokens, layer metadata, replacement flags | Yes, but not primary authorship owners | **Runtime downstream consumer** |
| Planner/prompt/contract consumers | `game/contract_registry.py`, `game/planner_convergence.py`, `game/response_policy_enforcement.py`, `game/response_policy_contracts.py`, `game/prompt_context.py`, `game/narrative_authenticity.py`, `game/narrative_mode_contract.py` | emergency fallback ids, contract fallback behavior, plan/non-plan fallback labels | Yes, mostly policy/telemetry | **Runtime downstream consumer** |
| Social/dialogue/narration adjacent | `game/social.py`, `game/social_exchange_fallback_catalog.py`, `game/social_exchange_projection.py`, `game/dialogue_social_plan.py`, `game/interaction_context.py`, `game/interaction_continuity.py` | social fallback text/kinds/continuity fallback references | Yes, local route behavior | **Runtime downstream consumer** |
| Scenario/eval/governance runtime tooling | `game/scenario_spine_eval.py`, `game/scenario_spine_opening_convergence.py`, `game/stage_diff_telemetry.py`, `game/schema_contracts.py`, `game/gm.py` | fallback telemetry, event summaries, schema references | Runtime diagnostic mostly | **Replay/observation consumer** |

### Replay, Projection, Classifier, And Test Coverage

| File | Matching symbols / tests | Runtime behavior? | Governance/test support? | Compatibility or historical residue? | Classification |
|---|---|---:|---:|---:|---|
| `tests/helpers/golden_replay_projection_fallbacks.py` | `REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS`, `project_replay_fallback_family_from_fem`, `_resolve_fallback_family`, dual precedence surface | No | Yes | Yes: read-side compatibility collapse from dual FEM fields to observed `fallback_family` | **Metadata/projection consumer** |
| `tests/helpers/golden_replay_projection.py` | `project_turn_observation`, protected fallback fields, runtime lineage extraction | No | Yes | Yes: protected observed `fallback_family` compatibility projection | **Metadata/projection consumer** |
| `tests/helpers/failure_classifier.py` | `_opening_fallback_owner_bucket`, `_fallback_observed`, `_fallback_split_owner`, classifier row fields | No | Yes | Yes: accepts legacy sanitizer trace and compatibility buckets | **Governance/test reference** |
| `tests/helpers/failure_classification_split_owner.py` | `SplitOwnerAcceptanceRow`, `split_owner_matrix_legacy`, split-owner FEM/lineage/observed row builders | No | Yes | Yes: `sealed_or_global_replacement_legacy` synthetic-only row | **Governance/test reference; historical residue** |
| `tests/helpers/opening_fallback_evidence.py` | opening FEM fixtures, compatibility-local authorship constant, dual-family fixture builders | No | Yes | Yes: test-only compatibility-local token | **Governance/test reference; compatibility residue** |
| `tests/test_opening_fallback_owner_bucket.py` | bucket mapping tests, `test_injected_legacy_compatibility_local_authorship_maps_to_unknown_ambiguous` | No | Yes | Yes: production never emits compatibility-local | **Governance/test reference** |
| `tests/test_final_emission_meta.py` | fallback projection fields, runtime lineage tests, dual-family precedence, legacy import stability, sanitizer legacy short owner tests | No | Yes | Yes: multiple compatibility locks | **Governance/test reference** |
| `tests/test_final_emission_opening_fallback.py` | opening adapter/fail-closed/projection/meta tests | No | Yes | Some negative compatibility-local assertions | **Governance/test reference** |
| `tests/test_final_emission_visibility_fallback.py` | visibility selected fallback, hard replacement, owner bucket tests, tuple adapters | No | Yes | Yes: legacy tuple round-trip | **Governance/test reference; compatibility layer test** |
| `tests/test_final_emission_sealed_fallback.py` | sealed fallback selection/branch/bucket tests, tuple compatibility | No | Yes | Yes: tuple compatibility | **Governance/test reference; compatibility layer test** |
| `tests/test_failure_classifier.py` | fallback classifier cases and rows | No | Yes | Some synthetic legacy rows | **Governance/test reference** |
| `tests/test_runtime_lineage_telemetry.py` | lineage owner/fallback frequency tests | No | Yes | Some vocabulary compatibility | **Replay/observation consumer test** |
| `tests/test_golden_replay_fallback_*_projection.py` | opening/sealed/visibility/sanitizer/upstream-fast/long-session projection tests | No | Yes | Preserve replay compatibility and protected values | **Replay/observation consumer tests** |
| `tests/test_golden_replay_projection_fallback_integration.py` and `tests/test_cf1_fallback_family_precedence.py` | dual fallback-family precedence tests | No | Yes | Explicit compatibility layer | **Metadata/projection consumer tests** |
| `tests/failure_classification_contract.py` | allowed fields, fallback bucket strings, sanitizer legacy fields | No | Yes | Yes | **Governance/test reference** |
| `tests/test_fallback_overwrite_containment.py`, `tests/test_upstream_fast_fallback_block_l.py` | upstream-fast provenance ownership/containment tests | No | Yes | Locks provenance debug shape | **Governance/test reference** |
| `tests/test_diegetic_fallback_narration.py`, `tests/test_realization_authority.py`, `tests/test_realization_provenance.py` | content family/provenance registry tests | No | Yes | Legacy family tests intentional | **Governance/test reference** |
| `tests/test_emergency_fallback_registry_static_drift.py` | registry/literal drift guard | No | Yes | No obvious removal | **Governance/test reference** |

Other matched test files are mostly downstream assertion surfaces for fallback behavior, final-emission boundaries, social routes, prompt/planner contracts, scenario replay, risk/remediation reports, and historical closeout checks. They validate or observe behavior; they do not appear to own fallback authorship.

### Tools, Scripts, Docs, Audits

| Area | Files / examples | Role | Classification |
|---|---|---|---|
| Fallback measurement tools | `tools/fallback_incidence_report.py`, `tools/fallback_incidence_trends.py`, `tools/fallback_projection_coverage_audit.py`, `tools/fallback_projection_gap_reality_audit.py`, `tools/fallback_maintenance_economics.py`, `tools/fallback_risk_scoring.py`, `tools/fallback_recurrence.py`, `tools/fallback_roi.py`, `tools/bv1b_fallback_incidence_validation.py`, `tools/cb6_speaker_fallback_frequency_probe.py` | Read/measure/report fallback evidence | **Replay/observation consumer** |
| Migration/decomposition scripts | `tools/ce4_decompose_fallback_projection_tests.py`, `tools/ce5_split_golden_replay_projection.py`, `scripts/bu4_ownership_write_path_discovery.py`, `scripts/bu_final_emission_coupling_discovery.py` | Historical/test migration support | **Historical residue / governance tooling** |
| Current audit docs | `docs/audits/discovery/BK_fallback_inventory.md`, `BK_fallback_selection_audit.md`, `BK_fallback_projection_audit.md`, `cycle_ap_fallback_authorship_resolution_recon.md`, `cycle_am_fallback_adapter_retirement_recon_2026-06-02.md`, `docs/audits/BP_runtime_fallback_incidence_discovery.md`, `docs/audits/CF1_projection_precedence_matrix.md` | Prior evidence and constraints | **Governance/test reference** |
| Top-level summaries | `CE4_fallback_projection_test_decomposition_summary.md`, `CE5_acceptance_projection_ownership_split_summary.md`, `CD_ownership_registry_concentration_audit_discovery.md`, `CE_golden_replay_concentration_audit_discovery.md` | Historical context | **Historical residue / governance docs** |
| Generated/session files | `data/session.json`, `data/session_log.jsonl`, `artifacts/**` | Persisted payloads with fallback metadata | Not ownership | **Historical/replay residue** |

## B. Ownership Classification

### Runtime Owner

- Content owners:
  - `game/opening_deterministic_fallback.py`
  - `game/gm_retry.py`
  - `game/social_exchange_emission.py`
  - `game/diegetic_fallback_narration.py`
  - `game/output_sanitizer.py` for sanitizer fallback text/selection
- Selection/application owners:
  - `game/final_emission_opening_fallback.py`
  - `game/final_emission_visibility_fallback.py`
  - `game/final_emission_sealed_fallback.py`
  - `game/api.py` for upstream-fast selection
- Metadata/vocabulary owners:
  - `game/final_emission_ownership_schema.py`
  - `game/final_emission_owner_bucket_views.py`
  - `game/final_emission_meta.py`
  - `game/realization_authority.py`
  - `game/realization_provenance.py`
  - `game/fallback_provenance_debug.py` for upstream-fast provenance packaging

### Runtime Downstream Consumer

- `game/final_emission_terminal_pipeline.py`
- `game/final_emission_generic_exit.py`
- `game/final_emission_fem_assembly.py`
- Final-emission validators/repair layers that consume fallback metadata or candidate outputs.
- Planner/prompt/contract modules that recognize emergency fallback labels but do not own authorship.

### Metadata/Projection Consumer

- `game/final_emission_replay_projection.py`
- `tests/helpers/golden_replay_projection_fallbacks.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/test_golden_replay_projection_fallback_integration.py`
- `tests/test_cf1_fallback_family_precedence.py`

### Replay/Observation Consumer

- `game/runtime_lineage_telemetry.py`
- `game/stage_diff_telemetry.py`
- fallback incidence/trend/coverage tools under `tools/`
- golden replay fallback projection tests

### Governance/Test Reference

- `tests/test_final_emission_meta.py`
- `tests/test_final_emission_opening_fallback.py`
- `tests/test_final_emission_visibility_fallback.py`
- `tests/test_final_emission_sealed_fallback.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_failure_classifier.py`
- `tests/failure_classification_contract.py`
- related audit docs under `docs/audits/**`

### Compatibility Layer

- `game/attribution_read_views.py`
- `game/ownership_projection_views.py`
- legacy read helpers in `game/final_emission_meta.py`
- tuple adapters in `game/final_emission_visibility_fallback.py` and sealed fallback tests
- compatibility-local authorship mapping in `game/final_emission_ownership_schema.py` and `game/final_emission_owner_bucket_views.py`
- dual-family replay collapse in `tests/helpers/golden_replay_projection_fallbacks.py`

### Historical Residue / Candidate For Removal

- Compatibility-local opening authorship token:
  - `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`
  - `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` in test evidence helpers
  - `test_injected_legacy_compatibility_local_authorship_maps_to_unknown_ambiguous`
- `sealed_or_global_replacement_legacy` synthetic row in `tests/helpers/failure_classification_split_owner.py`.
- `tests/helpers/golden_replay_projection.py.bak` and `tests/test_golden_replay_fallback_projection_monolith.py.bak`.
- Generated replay/session fallback payloads under `artifacts/**`, `data/session.json`, and `data/session_log.jsonl`.
- Archived docs under `docs/archive/**`.

## C. Pressure Hotspots

Top focused match counts, excluding generated artifacts, archived docs, and `.bak` files:

| Rank | File | Fallback refs | Why concentrated | Intentional? | Boundaries clear? | Multi-file updates likely? |
|---:|---|---:|---|---:|---:|---:|
| 1 | `tests/test_final_emission_visibility_fallback.py` | 436 | Broad visibility fallback selector/application coverage plus legacy tuple contracts | Yes | Mostly | Yes |
| 2 | `tests/test_failure_classifier.py` | 408 | Classifier rows consume fallback family, bucket, owner, and lineage evidence | Yes | Partly; mixes many families | Yes |
| 3 | `tests/test_final_emission_meta.py` | 405 | FEM, lineage, owner bucket, dual-family, compatibility import locks | Yes | Partly; very broad | Yes |
| 4 | `game/final_emission_visibility_fallback.py` | 316 | Visibility candidate selection, hard replacement, payload classes, compatibility adapters | Yes | Medium; selection/content/bucket overlap | Yes |
| 5 | `tests/test_final_emission_opening_fallback.py` | 291 | Opening adapter, fail-closed, metadata, no-local-compose assertions | Yes | Mostly | Yes |
| 6 | `game/final_emission_meta.py` | 233 | Canonical FEM sidecar, read helpers, provenance, observability events | Yes | Mixed owner/consumer/compat | Yes |
| 7 | `tests/helpers/golden_replay.py` | 228 | Replay harness stores fallback observations and payloads | Yes | Consumer only | Yes |
| 8 | `tests/helpers/failure_classification_split_owner.py` | 219 | Synthetic matrix for split owner acceptance/classifier alignment | Yes | Consumer/test-only | Yes |
| 9 | `game/final_emission_replay_projection.py` | 206 | Finalized FEM to runtime lineage event projection | Yes | Good, but owns read-side classification | Yes |
| 10 | `tests/test_final_emission_sealed_fallback.py` | 175 | Sealed branch and compatibility tests | Yes | Mostly | Yes |

Hotspot interpretation:

- Visibility fallback concentration is intentional because it is the broadest runtime selector. It still mixes candidate construction, owner bucket metadata, application, and tuple compatibility in one file, so ownership edits are high pressure.
- `final_emission_meta.py` is intentionally central for FEM, but it also houses compatibility reads and observability projection. It is the strongest metadata owner and also a compatibility layer.
- Replay/classifier tests are downstream, but their concentration makes them look authoritative. They should not drive runtime ownership; they should lock values after owner contraction.
- `final_emission_replay_projection.py` is the safest read-side classification point for measuring selected fallbacks, but it should remain a consumer of finalized FEM rather than a selector.

## D. Runtime vs Governance Split

### True Runtime Authorities

- `game/final_emission_ownership_schema.py`: canonical ownership vocabulary and allowed owner values.
- `game/final_emission_owner_bucket_views.py`: canonical bucket mapping rules.
- `game/opening_deterministic_fallback.py`: opening fallback content.
- `game/upstream_response_repairs.py`: upstream-prepared opening fallback payload and authorship stamp.
- `game/final_emission_opening_fallback.py`: opening fallback selection/fail-closed metadata.
- `game/final_emission_visibility_fallback.py`: visibility fallback selection/application.
- `game/final_emission_sealed_fallback.py`: sealed terminal fallback selection/application.
- `game/output_sanitizer.py`: sanitizer fallback selection/trace.
- `game/gm_retry.py`: retry fallback content and retry-terminal family.
- `game/social_exchange_emission.py`: strict-social fallback content and terminal dialogue fallback.
- `game/api.py`: upstream-fast fallback selection.
- `game/fallback_provenance_debug.py`: upstream-fast provenance packaging.
- `game/final_emission_meta.py`: terminal FEM contract and metadata stamps.
- `game/realization_authority.py` and `game/realization_provenance.py`: governed realization fallback family registry/stamping.

### Validate, Observe, Document, Or Preserve Only

- `game/final_emission_replay_projection.py`: read-side projection from finalized FEM.
- `game/runtime_lineage_telemetry.py`: event normalization/summarization.
- `tests/helpers/golden_replay_projection*.py`: protected observation projection.
- `tests/helpers/failure_classifier.py`: classifier consumption.
- `tests/helpers/failure_classification_split_owner.py`: synthetic acceptance matrix.
- `tests/helpers/opening_fallback_evidence.py`: fixtures/evidence builders.
- `tests/test_*fallback*`, `tests/test_final_emission_meta.py`, `tests/test_runtime_lineage_telemetry.py`, `tests/failure_classification_contract.py`: governance locks.
- `tools/fallback_*.py`, fallback audit docs, top-level cycle summaries: measurement/history.

## E. Compatibility Residue

| Reference | Location | Why it exists | Status |
|---|---|---|---|
| Compatibility-local opening authorship tokens | `game/final_emission_ownership_schema.py`, `game/final_emission_owner_bucket_views.py`, `tests/helpers/opening_fallback_evidence.py`, `tests/test_opening_fallback_owner_bucket.py` | Retired gate-local opening composer vocabulary maps to `unknown-ambiguous`; production should not emit it | **Removable after migration**, but only with replay/golden negative invariant update |
| `opening_fallback_compatibility_local_disabled` | `game/final_emission_opening_fallback.py`, tests | Negative proof that local composer is disabled/fail-closed | **Still necessary** while compatibility-local removal is being proven |
| Legacy tuple adapters | `game/final_emission_visibility_fallback.py`, sealed/visibility tests | Preserves dataclass-to-tuple boundary for older call sites/tests | **Still necessary or unclear**; requires call-site inventory before removal |
| Legacy top-level FEM read fallback | `game/final_emission_meta.py` | Reads older/mixed payloads and unit fixtures | **Still necessary** for fixtures/replay until payload migration completes |
| Dual fallback family collapse | `tests/helpers/golden_replay_projection_fallbacks.py`, `tests/test_cf1_fallback_family_precedence.py`, `tests/test_golden_replay_projection_fallback_integration.py` | Protected replay exposes one `fallback_family` while FEM preserves `fallback_family_used` and `realization_fallback_family` | **Still necessary**; do not collapse write-time fields without replay proof |
| `sealed_or_global_replacement_legacy` | `tests/helpers/failure_classification_split_owner.py` | Synthetic-only classifier vocabulary row | **Removable after classifier matrix migration**, low runtime risk |
| Sanitizer short owner trace fields | `game/final_emission_ownership_schema.py`, `game/output_sanitizer.py`, `tests/failure_classification_contract.py`, `tests/test_final_emission_meta.py` | Backward compatibility between short trace owner and canonical lineage owner | **Unclear / needs review** |
| `legacy_diegetic_fallback`, `legacy_unclassified` | `game/realization_authority.py`, `game/realization_provenance.py`, tests | Governs ambiguous/old fallback provenance rather than hiding it | **Still necessary** as explicit risk labels |
| `.bak` projection files and archived docs | `tests/helpers/golden_replay_projection.py.bak`, `tests/test_golden_replay_fallback_projection_monolith.py.bak`, `docs/archive/**` | Historical migration evidence | **Candidate for removal/archive policy**, not runtime |
| Generated fallback payloads | `artifacts/**`, `data/session.json`, `data/session_log.jsonl` | Replay/session evidence snapshots | **Historical residue**, should not be edited manually |

## F. Candidate Refactor Plan

Small staged contraction plan. Do not implement until a block is generated.

### Stage 1 — Contract The Retired Opening Compatibility Authorship Token

Likely owner files:

- `game/final_emission_ownership_schema.py`
- `game/final_emission_owner_bucket_views.py`

Downstream consumer files:

- `game/final_emission_meta.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_final_emission_meta.py`
- golden replay fallback projection tests

Compatibility layer files:

- `game/attribution_read_views.py`
- any legacy import checks in `tests/test_final_emission_meta.py`

Safest first implementation block:

1. Add or update tests proving no production writer emits `compatibility_local_opening_deterministic`.
2. Move the compatibility-local token to test-only evidence or mark it as deprecated in schema surface.
3. Keep mapping to `unknown-ambiguous` for one migration block.
4. Remove read-side production acceptance only after golden replay and classifier rows no longer need it.

Tests to update/run:

```powershell
python -m pytest tests/test_opening_fallback_owner_bucket.py tests/test_final_emission_meta.py tests/test_final_emission_opening_fallback.py -q
python -m pytest tests/test_golden_replay_fallback_opening_projection.py tests/test_golden_replay_projection_fallback_integration.py tests/test_cf1_fallback_family_precedence.py -q
```

### Stage 2 — Promote Bucket Mapping Ownership To One Surface

Likely owner files:

- `game/final_emission_owner_bucket_views.py`
- `game/final_emission_ownership_schema.py`

Downstream consumer files:

- `game/final_emission_meta.py`
- `game/final_emission_visibility_fallback.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_replay_projection.py`
- `tests/helpers/failure_classifier.py`

Safest first implementation block:

1. Keep constants in `final_emission_ownership_schema.py`.
2. Keep all mapping decisions in `final_emission_owner_bucket_views.py`.
3. Convert any remaining private bucket inference in family-specific runtime files into calls to the mapping module.
4. Leave compatibility facades as re-export-only.

Tests to update/run:

```powershell
python -m pytest tests/test_opening_fallback_owner_bucket.py tests/test_final_emission_visibility_fallback.py tests/test_final_emission_sealed_fallback.py tests/test_failure_classifier.py -q
```

### Stage 3 — Separate Selected Fallback Projection From Governance Fixtures

Likely owner file:

- `game/final_emission_replay_projection.py`

Downstream consumer files:

- `tests/helpers/golden_replay_projection_fallbacks.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/failure_classifier.py`
- `tools/fallback_incidence_report.py`

Compatibility layer:

- `tests/helpers/golden_replay_projection_fallbacks.py` for dual-family `fallback_family` collapse

Safest first implementation block:

1. Treat `_fem_selected_fallback_projection()` as the selected-fallback observation boundary.
2. Ensure it only consumes normalized finalized FEM and does not infer ownership from tests.
3. Keep dual-family precedence in replay helper until protected observations migrate.

Tests to update/run:

```powershell
python -m pytest tests/test_final_emission_meta.py tests/test_runtime_lineage_telemetry.py tests/test_golden_replay_fallback_opening_projection.py tests/test_golden_replay_fallback_sealed_projection.py tests/test_golden_replay_fallback_visibility_projection.py tests/test_golden_replay_fallback_sanitizer_projection.py tests/test_golden_replay_fallback_upstream_fast_projection.py -q
```

### Stage 4 — Review Tuple And Synthetic Legacy Rows

Likely owner files:

- `game/final_emission_visibility_fallback.py`
- `game/final_emission_sealed_fallback.py`
- `tests/helpers/failure_classification_split_owner.py`

Safest first implementation block:

1. Run an import/call-site search for `from_legacy_tuple`, `as_legacy_tuple`, and `sealed_or_global_replacement_legacy`.
2. If only tests use them, migrate tests to dataclass/native rows first.
3. Remove synthetic-only rows after classifier and split-owner matrix coverage is updated.

Tests to update/run:

```powershell
python -m pytest tests/test_final_emission_visibility_fallback.py tests/test_final_emission_sealed_fallback.py tests/test_golden_replay_fallback_acceptance_matrix.py tests/test_failure_classifier.py -q
```

## Recommended Test Commands

Focused ownership/projection suite:

```powershell
python -m pytest tests/test_opening_fallback_owner_bucket.py tests/test_final_emission_meta.py tests/test_final_emission_opening_fallback.py tests/test_final_emission_visibility_fallback.py tests/test_final_emission_sealed_fallback.py -q
```

Replay/projection suite:

```powershell
python -m pytest tests/test_golden_replay_fallback_projection.py tests/test_golden_replay_fallback_opening_projection.py tests/test_golden_replay_fallback_sealed_projection.py tests/test_golden_replay_fallback_visibility_projection.py tests/test_golden_replay_fallback_sanitizer_projection.py tests/test_golden_replay_fallback_upstream_fast_projection.py tests/test_golden_replay_projection_fallback_integration.py tests/test_cf1_fallback_family_precedence.py -q
```

Classifier/governance suite:

```powershell
python -m pytest tests/test_failure_classifier.py tests/failure_classification_contract.py tests/test_runtime_lineage_telemetry.py tests/test_fallback_overwrite_containment.py tests/test_upstream_fast_fallback_block_l.py -q
```

Runtime family/provenance suite:

```powershell
python -m pytest tests/test_diegetic_fallback_narration.py tests/test_realization_authority.py tests/test_realization_provenance.py tests/test_emergency_fallback_registry_static_drift.py -q
```

## Files To Pass Back To ChatGPT For Block Generation

Highest-value implementation context:

- `game/final_emission_ownership_schema.py`
- `game/final_emission_owner_bucket_views.py`
- `game/final_emission_meta.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_visibility_fallback.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_replay_projection.py`
- `game/upstream_response_repairs.py`
- `game/fallback_provenance_debug.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/helpers/golden_replay_projection_fallbacks.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_classification_split_owner.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_final_emission_meta.py`
- `tests/test_final_emission_opening_fallback.py`
- `tests/test_final_emission_visibility_fallback.py`
- `tests/test_final_emission_sealed_fallback.py`
- `tests/test_failure_classifier.py`

Prior discovery/reference docs worth passing if the next block is architectural:

- `docs/audits/discovery/cycle_ap_fallback_authorship_resolution_recon.md`
- `docs/audits/closeouts/cycle_ap_fallback_authorship_resolution_closeout.md`
- `docs/audits/discovery/cycle_am_fallback_adapter_retirement_recon_2026-06-02.md`
- `docs/audits/closeouts/cycle_am_fallback_adapter_retirement_closeout_2026-06-02.md`
- `docs/audits/discovery/BK_fallback_projection_audit.md`
- `docs/audits/BP_runtime_fallback_incidence_discovery.md`

## Bottom Line

Fallback ownership is already partially separated, but pressure remains high because four surfaces still overlap:

1. Runtime selection/content owners.
2. FEM metadata and owner-bucket mapping.
3. Replay/classifier projection and compatibility collapse.
4. Historical compatibility tokens/fixtures.

The safest contraction starts with opening compatibility authorship residue, because it is explicitly retired, production-negative, well-covered, and mostly read-side. The highest-risk contraction is visibility fallback, because it has the largest live selector surface and retains compatibility adapters.
