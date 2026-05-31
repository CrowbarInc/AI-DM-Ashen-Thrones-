# Cycle P - Fallback Family Collapse Recon - 2026-05-28

Scope: reconnaissance and mapping only. No runtime behavior, fallback prose, fixtures, tests, schemas, or projections were intentionally changed.

## A. Executive Summary

- Fallback authorship is now mostly ambiguous at the projection and ownership-vocabulary layer, not because multiple live paths visibly author the same successful opening text.
- Successful opening fallback content has a strong content owner (`game.opening_deterministic_fallback`) and packaging owner (`game.upstream_response_repairs`), but runtime lineage still reports the selected fallback event owner as `game.final_emission_gate`.
- Strict-social fallback content is primarily owned by `game.social_exchange_emission`, while final emission and sanitizer paths can select, consume, or re-stamp it; sanitizer already models split selection/prose ownership more clearly than gate lineage.
- `fallback_family_used`, `realization_fallback_family`, `final_emitted_source`, owner buckets, sanitizer trace fields, and runtime-lineage events describe overlapping but non-identical concepts.
- Duplicate patch pressure remains around final-emission replacement branches: some sites are projection-only, but several still perform late output mutation after upstream preparation or strict-social selection.
- The safest next implementation should define a canonical owner vocabulary first, then contract one family at a time, starting with opening fallback attribution/projection rather than fallback prose.

## B. Fallback Family Inventory

| Family | Current owner | Candidate canonical owner | Files/functions | Projection fields touched | Tests | Risk |
|---|---|---|---|---|---|---|
| Successful opening deterministic fallback | Content: `game.opening_deterministic_fallback`; payload: `game.upstream_response_repairs`; selector/projection: gate/meta | Content owner: `game.opening_deterministic_fallback`; payload owner: `game.upstream_response_repairs`; selector explicitly separate | `deterministic_opening_fallback_text_and_meta`; `build_upstream_prepared_opening_fallback_payload`; `maybe_attach_upstream_prepared_opening_fallback_payload`; `_enforce_response_type_contract`; `_opening_scene_safe_fallback_tuple` | `opening_fallback_authorship_source`, `opening_fallback_owner_bucket`, `fallback_family_used=scene_opening`, `fallback_temporal_frame`, `realization_fallback_family`, runtime `fallback_authorship_source` | `tests/test_upstream_response_repairs.py`; `tests/test_opening_fallback_owner_bucket.py`; `tests/test_final_emission_gate.py`; `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py` | Medium-high: projection owner still says gate for content authored upstream |
| Opening fail-closed marker | Gate / opening adapter | `game.final_emission_opening_fallback` plus gate as terminal selector | `_opening_fail_closed_meta_*`; `_opening_scene_safe_fallback_tuple`; `_enforce_response_type_contract` | `opening_fallback_failed_closed`, `blocked_repair_kind`, `opening_fallback_owner_bucket=sealed-gate`, `final_emitted_source` | `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py`; `tests/test_final_emission_gate.py` | Low-medium: distinct marker, but shares opening labels |
| Strict-social deterministic fallback | Content and filtering: `game.social_exchange_emission`; selector/consumer: gate or sanitizer | `game.social_exchange_emission` for content; gate/sanitizer as selectors only | `build_final_strict_social_response`; `deterministic_social_fallback_line`; `minimal_social_emergency_fallback_line`; `strict_social_ownership_terminal_fallback`; `lawful_strict_social_dialogue_emergency_fallback_line`; `apply_strict_social_terminal_dialogue_fallback_if_needed` | `final_emitted_source`, `fallback_kind`, `fallback_pool`, `realization_fallback_family=strict_social_deterministic_fallback`, sanitizer split owner fields | `tests/test_social_exchange_emission.py`; `tests/test_strict_social_emergency_fallback_dialogue.py`; `tests/test_final_emission_gate.py`; `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py` | High: multiple selectors, late gate patches, social legality entanglement |
| Sanitizer empty fallback | Selection: `game.output_sanitizer`; stock text source: upstream prepared emission | Keep split: sanitizer selection, upstream stock source | `_prepared_empty_fallback_text`; `_mark_sanitizer_empty_fallback`; `sanitize_player_facing_output` | `sanitizer_empty_fallback_used`, `sanitizer_empty_fallback_source`, `sanitizer_empty_fallback_owner`, sanitizer lineage fields | `tests/test_output_sanitizer.py`; `tests/test_golden_replay.py`; `tests/test_failure_classifier.py` | Low: split owner already explicit |
| Sanitizer strict-social fallback | Selection: sanitizer; prose: strict-social emission | Keep split: `game.output_sanitizer` selector, `game.social_exchange_emission` prose | `_mark_sanitizer_strict_social_fallback`; `social_fallback_line_for_sanitizer` | `sanitizer_strict_social_fallback_used`, `sanitizer_strict_social_selection_owner`, `sanitizer_strict_social_prose_owner`, `sanitizer_strict_social_source` | `tests/test_output_sanitizer.py`; `tests/test_golden_replay.py`; `tests/test_final_emission_meta.py` | Low-medium: good model for other split-owner families |
| Upstream prepared answer/action fallback | Text/package: `game.upstream_response_repairs`; selector: gate response-type contract | `game.upstream_response_repairs` | `build_upstream_prepared_emission_payload`; `_enforce_response_type_contract` | `upstream_prepared_emission_used`, `upstream_prepared_emission_source`, `realization_fallback_family=upstream_prepared_emission`, runtime `response_type_prepared_emission` | `tests/test_upstream_response_repairs.py`; `tests/test_final_emission_gate.py`; `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py`; `tests/test_failure_classifier.py` | Medium: runtime lineage reports gate owner for selection |
| Visibility / referential replacement fallback | Gate orchestration; helper is route/metadata-only | Keep gate as selector; content owner should remain underlying selected family | `_apply_visibility_enforcement`; `_standard_visibility_safe_fallback`; `game.final_emission_visibility_fallback` helpers | `visibility_replacement_applied`, `visibility_fallback_owner_bucket`, `visibility_fallback_pool`, `visibility_fallback_kind`, runtime `visibility_or_scene_replacement` | `tests/test_final_emission_visibility.py`; `tests/test_final_emission_visibility_fallback.py`; `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py` | High: route family may mask opening/social/global content owner |
| Sealed/global terminal replacement | Gate selector; sealed helper route/meta; injected prose owners | Gate for terminal route only; prose owners remain injected providers | `_select_non_strict_replace_path_terminal_sealed_fallback_selection`; `assemble_non_strict_sealed_fallback_selection`; `stamp_sealed_fallback_realization_family` | `sealed_fallback_owner_bucket`, `realization_fallback_family=gate_terminal_repair`, `final_emitted_source`, `fallback_family_used` | `tests/test_final_emission_gate.py`; `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py` | Medium-high: selector/provider boundary is still broad |
| Retry terminal fallback | `game.gm_retry`, sometimes strict-social/diegetic helpers | Retry owner, with provider-specific content owners documented | `select_deterministic_retry_fallback_line`; `force_terminal_retry_fallback`; strict-social retry fallback helpers | retry tags, `realization_fallback_family=retry_terminal_fallback`, runtime/final source when projected | `tests/test_gm_retry.py`; `tests/test_retry_tone_alignment.py`; transcript regressions | Medium: many providers behind one retry family |
| Upstream fast fallback | API/GM error handling; provenance helper | API/GM for selection; `fallback_provenance_debug` for fingerprint/provenance only | `attach_upstream_fast_fallback_provenance`; `realign_fallback_provenance_selector_to_current_text`; API/GM fast fallback paths | `fallback_provenance_trace`, source/fingerprint, stage-diff fallback fields | `tests/test_upstream_fast_fallback_block_l.py`; `tests/test_fallback_overwrite_containment.py`; `tests/test_turn_packet_stage_diff_integration.py` | Medium: provenance is diagnostic and temporary-feeling |
| Fallback behavior repair | Repair layer, not a selected fallback family | `game.final_emission_repairs` / `game.fallback_behavior` | `_apply_fallback_behavior_layer`; `repair_fallback_behavior`; `validate_fallback_behavior` | `fallback_behavior_repaired`, `fallback_behavior_repair_mode`, mutation lineage | `tests/test_final_emission_repairs.py`; `tests/test_fallback_behavior_gate.py`; `tests/test_fallback_behavior_repairs.py` | Medium: late semantic-ish repair must not become fallback author |

## C. Opening Fallback Lineage

1. Creation:
   - `game.opening_deterministic_fallback.deterministic_opening_fallback_text_and_meta` composes text from `opening_curated_facts` and returns composition metadata.
   - `game.upstream_response_repairs.build_upstream_prepared_opening_fallback_payload` packages that text as `prepared_opening_fallback_text` with `opening_fallback_authorship_source="upstream_prepared_opening_fallback"`.
   - `maybe_attach_upstream_prepared_opening_fallback_payload` silently attaches the package before final emission when `resolution.kind == "scene_opening"` and curated facts are usable.

2. Normalization / validation:
   - `game.final_emission_gate._enforce_response_type_contract` validates candidate scene-opening output with `validate_opening_output` and `is_valid_opening`.
   - If the candidate fails, it selects a usable upstream prepared opening payload or a sealed fail-closed marker. The current code does not re-author successful opening prose in the gate.
   - `game.final_emission_opening_fallback._gm_output_normalized_for_opening_context` normalizes malformed/missing curated facts to an empty list for fail-closed handling.

3. Projection:
   - `game.final_emission_meta.opening_fallback_owner_bucket_from_meta` maps successful prepared opening to `upstream-prepared` and fail-closed marker to `sealed-gate`.
   - `game.final_emission_replay_projection.build_fem_runtime_lineage_events` projects successful opening as `fallback_kind="scene_opening"` and includes `fallback_authorship_source` plus `fallback_owner_bucket`, but still emits `owner="game.final_emission_gate"`.
   - `tests/helpers/golden_replay.py` projects `opening_fallback_authorship_source`, `opening_fallback_owner_bucket`, `fallback_family`, and runtime lineage into observed turns.

4. Logging / replay:
   - Gate writes final-emission decisions through `log_final_emission_decision` and final traces through `log_final_emission_trace`.
   - Golden replay protects `opening_fallback_path` in `docs/testing/protected_replay_manifest.md`.
   - Scenario-spine and failure dashboards consume runtime-lineage summaries and owner buckets.

5. Duplicate owners / patch sites:
   - Content owner and payload owner are clear, but runtime lineage still treats gate as selected-fallback owner.
   - `game.opening_deterministic_fallback` and `game.upstream_response_repairs` docstrings still mention a gate compatibility re-call, while `game.final_emission_opening_fallback` says it does not author opening prose.
   - Final emission still copies opening composition fields into FEM in multiple branches.

6. Final-emission work that belongs upstream:
   - Final emission should keep selecting prepared payloads and fail-closed markers, but any future successful opening content composition or prepared payload rebuilding should remain upstream/opening-owned.
   - The next implementation should treat gate-side opening field copying as projection/packaging, not content ownership.

## D. Strict-Social Fallback Ownership

1. Selection:
   - `apply_final_emission_gate` decides whether strict-social finalization applies using `strict_social_emission_will_apply` and `effective_strict_social_resolution_for_emission`.
   - `build_final_strict_social_response` is then the main strict-social writer/selector for candidate filtering, deterministic fallback selection, and emergency fallback selection.
   - Sanitizer selects a strict-social fallback only when strip-only sanitizer handling empties strict-social output.

2. Decision owner:
   - Route activation is shared between social route helpers and final gate orchestration.
   - Terminal strict-social content decisions live in `game.social_exchange_emission`.
   - Gate owns branch order, later validation layers, FEM writes, visibility/NMO/AQ replacement integration, and final packaging.

3. Text/content owner:
   - `game.social_exchange_emission` owns `deterministic_social_fallback_line`, `minimal_social_emergency_fallback_line`, `strict_social_ownership_terminal_fallback`, `lawful_strict_social_dialogue_emergency_fallback_line`, and `social_fallback_line_for_sanitizer`.
   - Gate-owned strict-social mutations should be framed as selection/application or legality replacement, not prose authorship.

4. Source-family/provenance projection:
   - `build_final_strict_social_response` attaches `STRICT_SOCIAL_DETERMINISTIC_FALLBACK` to details.
   - Gate copies or rewrites `final_emitted_source`, `fallback_kind`, `fallback_pool`, and `realization_fallback_family`.
   - Sanitizer exposes split fields: `sanitizer_strict_social_selection_owner="output_sanitizer"` and `sanitizer_strict_social_prose_owner="strict_social_emission"`.
   - Runtime-lineage projection currently reports strict-social selected fallbacks with `owner="game.final_emission_gate"`.

5. Ambiguity:
   - Final emission may replace strict-social output with `minimal_social_emergency_fallback` after response-type, interaction-continuity, narrative-mode-output, or acceptance-quality checks.
   - Those patches are legal selection/application sites, but they duplicate the same minimal social emergency line and can obscure that strict-social emission owns the content.

6. Current enforcing tests:
   - `tests/test_social_exchange_emission.py`
   - `tests/test_strict_social_emergency_fallback_dialogue.py`
   - `tests/test_final_emission_gate.py`
   - `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_strict_social_and_sanitizer_fallbacks`
   - `tests/test_output_sanitizer.py`
   - `tests/test_golden_replay.py::test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants`

## E. Source-Family / Provenance Projection Map

| Site | Fields assigned/normalized | Classification |
|---|---|---|
| `game.realization_authority.FALLBACK_FAMILIES` | registered fallback families and owner profiles | Authority registry, no runtime mutation |
| `game.realization_provenance.normalize_realization_fallback_family` / `attach_realization_fallback_family` | `realization_fallback_family` | Metadata normalization/stamping |
| `game.upstream_response_repairs.build_upstream_prepared_opening_fallback_payload` | `opening_fallback_authorship_source`, `fallback_family_used`, `fallback_temporal_frame`, `realization_fallback_family` | Upstream prepared payload packaging |
| `game.upstream_response_repairs.build_upstream_prepared_emission_payload` | prepared answer/action/sanitizer stock, `realization_fallback_family=upstream_prepared_emission` | Upstream prepared payload packaging |
| `game.final_emission_gate._enforce_response_type_contract` | `response_type_repair_kind`, `opening_recovered_via_fallback`, `upstream_prepared_emission_*`, opening fail-closed fields | Gate selection and FEM debug preparation |
| `game.final_emission_gate.apply_final_emission_gate` strict-social branches | `final_emitted_source`, `fallback_kind`, `fallback_pool`, `realization_fallback_family`, `post_gate_mutation_detected` | Gate orchestration/application; some suspicious late patches |
| `game.final_emission_gate` non-strict replace path | `fallback_family_used`, `fallback_temporal_frame`, `final_emitted_source`, opening copied fields, sealed stamp | Gate terminal replacement packaging |
| `game.final_emission_sealed_fallback.stamp_sealed_fallback_realization_family` | `realization_fallback_family`, `sealed_fallback_owner_bucket` | Safe route/projection helper |
| `game.final_emission_visibility_fallback` helpers | `visibility_fallback_owner_bucket`, pool/kind payloads | Safe route/projection helper |
| `game.final_emission_meta.opening_fallback_owner_bucket_from_meta` | `opening_fallback_owner_bucket` computed read-side | Safe projection-only helper |
| `game.final_emission_replay_projection._fem_selected_fallback_projection` | runtime `fallback_kind`, `gate_path`, `stage`, `owner`, `source`; opening owner bucket/authorship side fields | Safe projection-only, but owner semantics ambiguous |
| `tests/helpers/golden_replay.observed_turn_from_payload` | observed `fallback_family`, `opening_fallback_owner_bucket`, sanitizer fields, runtime lineage | Replay projection helper |
| `tests/helpers/failure_classifier.py` | `source_family`, `primary_owner`, `emission_sublayer`, allowlist validation | Test/diagnostic classification projection |
| `tests/failure_classification_contract.py` | allowed `source_family`, fallback source/family tags, sanitizer owner fields | Test-only allowlist |
| `game.output_sanitizer` sanitizer markers | sanitizer empty/strict-social owner/source fields and lineage counters | Selection/provenance trace, good split-owner model |
| `game.fallback_provenance_debug` | `fallback_provenance_trace`, fingerprints, selected/current text alignment | Provenance diagnostic helper |
| `game.stage_diff_telemetry` | `fallback_source`, `fallback_stage`, `fallback_kind` | Telemetry projection |

## F. Duplicate Fallback Patch Candidates

| Site | Classification | Recommendation |
|---|---|---|
| Opening composition field copying in `_enforce_response_type_contract` and non-strict replace FEM assembly | Legacy compatibility / projection packaging | Extract helper after owner contract; do not change behavior first |
| `game.final_emission_opening_fallback._opening_fail_closed_meta_*` repeated meta shapes | Legacy compatibility shim | Extract shared fail-closed meta helper later if tests lock exact fields |
| Runtime opening selected event owner plus separate owner bucket | Projection-only ambiguity | Move to split owner semantics or canonical owner projection in next phase |
| Strict-social minimal emergency patches after response-type failure, interaction-continuity fallback, NMO fallback, and N4/AQ fallback | Suspicious semantic/application overlap | Move ownership labels upstream or extract a gate helper that applies pre-authored strict-social emergency text without reclassifying content |
| `build_final_strict_social_response` deterministic fallback then gate fallback-behavior layer | Suspicious semantic mutation | Leave behavior untouched now; next phase should prove whether fallback-behavior can mutate strict-social content after canonical social fallback |
| Sanitizer empty fallback trace and replay projection | Safe projection/selection helper | Keep; use as split-owner precedent |
| Sanitizer strict-social split owner fields | Safe projection/selection helper | Keep; mirror pattern for gate-selected strict-social if needed |
| Sealed fallback stamping helper | Safe projection-only helper | Keep |
| Visibility fallback owner bucket / pool / kind helpers | Safe route/projection helper | Keep, but do not make them content owners |
| `fallback_behavior` repair metadata merging in multiple accept/replace paths | Legacy repair/application shim | Leave untouched until fallback-behavior ownership cycle |
| Fast fallback provenance realignment after late composition repair | Diagnostic/provenance patch | Keep; run containment tests before any change |

## G. Replay / Test Protection Plan

Minimum commands before and after implementation:

```powershell
python -m pytest tests/test_opening_fallback_owner_bucket.py -q
python -m pytest tests/test_upstream_response_repairs.py tests/test_final_emission_meta.py -q
python -m pytest tests/test_golden_replay.py::test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership tests/test_golden_replay.py::test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership tests/test_golden_replay.py::test_golden_observed_turn_projects_runtime_lineage_and_prefers_existing_events -q
python -m pytest tests/test_social_exchange_emission.py tests/test_strict_social_emergency_fallback_dialogue.py tests/test_output_sanitizer.py -q
python -m pytest tests/test_run_scenario_spine_validation.py tests/test_runtime_lineage_telemetry.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q
```

Protected fixtures / scenarios:

- `opening_fallback_path`
- `wrong_speaker_strict_social_emission`
- `synthetic_opening_owner`
- `synthetic_opening_owner_fail_closed`
- `synthetic_strict_social_sealed_owner`
- `strict_social_sanitizer_split`
- `sanitizer_empty_projection`
- `frontier_gate_long_session`
- `c1a_opening_convergence_paths.json`

Expected artifacts and surfaces:

- Golden replay observed turns preserve `final_emitted_source`, `fallback_family`, `opening_fallback_authorship_source`, and `opening_fallback_owner_bucket`.
- `fem_runtime_lineage_events` remains bounded, serializable, recurrence-ready, and non-scoring.
- Scenario-spine summaries keep fallback frequency, fallback-authorship frequency, gate-path frequency, mutation-kind frequency, and recurrence summaries stable unless intentionally contracted.
- Failure classifier rows keep valid `source_family` values and dashboard evidence strings.

Known fragile assertions:

- `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_opening_and_fail_closed_fallbacks` currently asserts selected opening `owner == "game.final_emission_gate"` while also asserting `fallback_owner_bucket == "upstream-prepared"`.
- Golden replay opening tests assert no `compatibility_local_opening_deterministic` ownership.
- Sanitizer strict-social tests assert split owner names exactly.
- Scenario-spine runtime-lineage tests may depend on recurrence keys if owner semantics change.

## H. Recommended Implementation Blocks

| Block | Objective | Files likely touched | Behavior-change risk | Tests to run | Dependency |
|---|---|---|---|---|---|
| P1 - Owner semantics contract | Decide whether runtime-lineage `owner` means selector, content author, or split fields | docs/report follow-up; `game.runtime_lineage_telemetry.py` docs; `tests/test_final_emission_meta.py` | None if docs/tests only | `python -m pytest tests/test_final_emission_meta.py -q` | First |
| P2 - Opening canonical owner projection | Make successful opening fallback have one canonical owner in projection while preserving gate path and fail-closed gate ownership | `game/final_emission_replay_projection.py`; `game/final_emission_meta.py`; `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py` | Low: projection-only, but replay artifacts may churn | opening/golden commands above | After P1 |
| P3 - Opening metadata helper extraction | Consolidate repeated opening FEM field projection/copying without changing emitted text | `game/final_emission_gate.py`; possibly `game/final_emission_opening_fallback.py` | Medium: gate branch packaging is brittle | `tests/test_final_emission_gate.py tests/test_opening_fallback_owner_bucket.py tests/test_golden_replay.py -q` | After P2 |
| P4 - Strict-social split projection | Mirror sanitizer split owner model for gate-selected strict-social fallback | `game/final_emission_replay_projection.py`; `game/final_emission_meta.py`; strict-social tests | Medium: diagnostics and recurrence keys change | strict-social/social/golden commands above | After P1/P2 |
| P5 - Strict-social late patch inventory cleanup | Extract a helper for applying already-authored minimal social emergency text at final emission patches | `game/final_emission_gate.py`; maybe `game/social_exchange_emission.py` | High: output mutation paths, NMO/AQ/IC branch order | `tests/test_final_emission_gate.py tests/test_social_exchange_emission.py tests/test_strict_social_emergency_fallback_dialogue.py -q` | Sequential after P4 |
| P6 - Source-family allowlist update | Align classifier/dashboard allowlists with the settled owner vocabulary | `tests/failure_classification_contract.py`; `tests/helpers/failure_classifier.py`; dashboard helper/tests | Low-medium: diagnostic-only but protected | classifier/dashboard/golden commands above | After projection changes |

## Files Inspected

- `game/opening_deterministic_fallback.py`
- `game/upstream_response_repairs.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `game/final_emission_sealed_fallback.py`
- `game/social_exchange_emission.py`
- `game/output_sanitizer.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/fallback_provenance_debug.py`
- `tests/test_final_emission_meta.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_golden_replay.py`
- `tests/test_output_sanitizer.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_failure_classifier.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_dashboard_report.py`
- `docs/testing/protected_replay_manifest.md`
- `docs/cycles/cycle_i_fallback_authorship_recon_2026-05-25.md`
- `docs/cycles/cycle_o_final_emission_gate_contraction_recon_2026-05-28.md`

## Commands Run

```powershell
rg --files
git status --short
rg -n -i "fallback" game tests docs audits tools
rg -n -i "strict social|strict-social|social fallback|source_family|source family|fallback_source|prepared fallback|upstream prepared|normalized fallback" game tests docs audits tools
rg -n -i "replay invariant|final emission|emission gate|gate fallback|fallback patch|repair payload|provenance|projection" game tests docs audits tools
rg -n "def .*fallback|class .*Fallback|FALLBACK|fallback_family|source_family|final_emitted_source|opening_fallback|strict_social|realization_fallback_family" ...
Get-Content ... targeted production, test, and report files
```

## Tests Run

Initial attempts using `python -m pytest ...` failed because `python` is not on PATH in this PowerShell environment. The focused protection slice was then run with the bundled runtime plus repo venv site-packages:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests/test_opening_fallback_owner_bucket.py tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_opening_and_fail_closed_fallbacks tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_strict_social_and_sanitizer_fallbacks -q
```

Result: `12 passed`.

## Unresolved Questions

- Should runtime-lineage `owner` remain the selector/application owner, or should selected fallback events use canonical content owner with a separate `selection_owner`?
- Should successful opening fallback be reclassified out of broad `legacy_diegetic_fallback`, or is `fallback_family_used="scene_opening"` plus owner bucket sufficient?
- Should gate-selected strict-social fallback adopt the sanitizer split-owner vocabulary exactly?
- Which late strict-social replacements are purely legal application of already-authored fallback text, and which are semantic mutation candidates?
- Should compatibility-local opening vocabulary remain as a sentinel forever, or be retired after projection split semantics are locked?
