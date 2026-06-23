# Cycle J — Gate Cluster Extraction Recon

Date: 2026-05-26

## Executive Recommendation

Recommended cluster: **opening fallback**

Reason: Opening fallback has a bounded block of selection and fail-closed policy still owned by `game/final_emission_gate.py`, while its prose composer and upstream prepared-payload packager are already separate and protected by explicit Cycle I ownership/lineage tests. This leaves a meaningful but narrow gate reduction opportunity without moving authored text, route ordering, or public behavior.

Why this fits Cycle J: A first extraction can preserve the existing gate contract exactly: successful opening prose remains owned by `game.opening_deterministic_fallback`, successful packaging remains owned by `game.upstream_response_repairs`, and the extracted policy remains a gate-selected opening decision with fail-closed semantics unchanged. The directly related targeted suite passes before any extraction work.

## Candidate Cluster Comparison

`Files Found` counts primary runtime owner/implementation files, with immediately relevant adjacent projection/helper owners included where noted.

| Cluster | Files Found | Test Coverage | Entanglement | Extraction Risk | Recommendation |
|---|---:|---:|---|---|---|
| opening fallback | 4 primary + 1 adjacent sealed-family helper | Strong: direct gate, payload, ownership, FEM, replay, spine, API coverage | Partially centralized; prose and packaging are out of gate, selection/fail-close remains inline | Medium | **Extract first** |
| visibility fallback | 3 primary | Strong: route/helper, visibility, gate, replay/classifier coverage | Centralized already; remaining gate work mixes legality, selection, output, and branch order | Medium-high for additional extraction | Wait; Cycle D already extracted its safe helper layer |
| strict-social fallback | 4 primary | Strong: social emission, emergency, gate, sanitizer, replay coverage | Partially centralized but crosses sanitizer, visibility, response-type, first-mention, referential, and NMO/N4 enforcement | High | Wait; too entangled for the first Cycle J extraction |
| source-family tagging | 4 principal runtime/projection owners, plus consumers | Strong: provenance authority/audit, sealed gate, replay, classifier contract coverage | Centralized in existing provenance/classifier helpers; not chiefly a gate-owned behavior block | Medium contract risk with low gate-reduction value | Wait; preserve as an invariant of the selected extraction |

## Recommended Extraction Seam

The smallest viable target is a narrow opening fallback **selection policy adapter**, proposed as `game/final_emission_opening_fallback.py`. It should select the existing prepared opening payload or the existing fail-closed result and return the same tuple/meta shape already consumed by the gate. It should not author prose, mutate final output, log, or change routing.

Functions likely to move or be wrapped from `game/final_emission_gate.py`:

- `_opening_curated_facts_have_attachable_non_empty_strings`
- `_opening_curated_facts_schema_ok`
- `_gm_output_normalized_for_opening_context`
- `_opening_fail_closed_meta_upstream_missing_insufficient_curated_facts`
- `_upstream_prepared_opening_fallback_payload_if_usable`
- `_recover_upstream_opening_fallback_stub_payload`
- `_opening_maybe_attach_upstream_prepare_build_failed_on_emission_debug`
- `_opening_fail_closed_meta_upstream_maybe_attach_prepare_failed`
- `_opening_fail_closed_meta_upstream_stub_rebuild_failed`
- `_opening_scene_safe_fallback_tuple`

Behavior that must remain unchanged:

- The prepared upstream payload wins when structurally usable.
- Missing, insufficient, or unrecoverable opening payload data emits the same fail-closed marker and metadata.
- `apply_final_emission_gate`, output mutation, final FEM assembly, gate logging, response-type enforcement order, and visibility-driven opening selection remain in `game/final_emission_gate.py`.
- `deterministic_opening_fallback_text_and_meta` remains the prose/content owner; `build_upstream_prepared_opening_fallback_payload` remains the packager.
- Opening output validation (`validate_opening_output`, `is_valid_opening`) remains gate legality behavior for this first seam.

Tests that should guard the seam later are existing characterization tests in `tests/test_final_emission_gate.py`, `tests/test_upstream_response_repairs.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_final_emission_meta.py`, `tests/test_golden_replay.py`, and `tests/test_run_scenario_spine_validation.py`. New tests, if added during extraction, should be narrow parity tests for the adapter's returned selection/meta shape rather than new behavior.

## Current Ownership Map

### Opening Fallback

- `game/opening_deterministic_fallback.py`: `opening_context_from_gm_output` and `deterministic_opening_fallback_text_and_meta` own curated-fact-to-opening prose/content composition.
- `game/upstream_response_repairs.py`: `is_structurally_usable_upstream_prepared_opening_fallback_payload`, `build_upstream_prepared_opening_fallback_payload`, and `maybe_attach_upstream_prepared_opening_fallback_payload` own preparation and attachment of the upstream fallback payload.
- `game/final_emission_gate.py`: `_opening_scene_safe_fallback_tuple` and its adjacent opening helpers select prepared versus fail-closed behavior; `_enforce_response_type_contract`, `_standard_visibility_safe_fallback`, and `apply_final_emission_gate` integrate the selection with route order, final output, FEM, and logging.
- `game/final_emission_meta.py`: `opening_fallback_owner_bucket_from_fields`, `opening_fallback_owner_bucket_from_meta`, `_fem_selected_fallback_projection`, and `build_fem_runtime_lineage_events` own readable owner-bucket and lineage projection.
- `game/final_emission_sealed_fallback.py`: `stamp_sealed_fallback_realization_family` is an adjacent common sealed-route family-stamping owner, not the opening prose owner.

### Visibility Fallback

- `game/narration_visibility.py`: visibility, first-mention, and referential-clarity validation contracts.
- `game/final_emission_visibility_fallback.py`: already-extracted pure route, payload, metadata, annotation, owner-bucket, and logging-context helpers.
- `game/final_emission_gate.py`: `_standard_visibility_safe_fallback`, `_apply_visibility_enforcement`, `_apply_first_mention_enforcement`, and `_apply_referential_clarity_enforcement` retain output selection, mutation, ordering, and logging.

### Strict-Social Fallback

- `game/social_exchange_emission.py`: strict-social emergency/dialogue fallback text and core social replacement policy, including `apply_strict_social_terminal_dialogue_fallback_if_needed`, `strict_social_ownership_terminal_fallback`, and `social_fallback_line_for_sanitizer`.
- `game/final_emission_gate.py`: strict-social gate integration plus first-mention exemption, local pronoun repair, visibility, and final enforcement sequencing.
- `game/output_sanitizer.py`: empty-output sanitizer path and its strict-social fallback marker/selection.
- `game/final_emission_meta.py`: fallback projection and runtime lineage for the emitted choice.

### Source-Family Tagging

- Runtime family authority is already concentrated in `game/realization_authority.py` (`FALLBACK_FAMILIES`) and `game/realization_provenance.py` (`normalize_realization_fallback_family`, `attach_realization_fallback_family`).
- Sealed fallback family stamping is already isolated in `game/final_emission_sealed_fallback.py`.
- Replay/dashboard `source_family` classification is separately owned by `tests/helpers/failure_classifier.py` (`CATEGORY_RULES`, `_source_family_for`, `classify_replay_failure`) and schema-locked by `tests/failure_classification_contract.py`.
- The gate consumes or preserves these tags; it is not the sole owner of the tagging concern.

## Tests and Fixtures

Opening fallback direct assertions:

- `tests/test_final_emission_gate.py`: prepared-payload preference, unusable/missing payload fail-close behavior, exact opening fallback snapshot, FEM attribution, visibility-routed opening fallback, and sealed fail-closed recording.
- `tests/test_upstream_response_repairs.py`: prepared opening payload shape, replacement, attachment, and failure behavior.
- `tests/test_opening_fallback_owner_bucket.py`: successful prepared versus fail-closed owner-bucket mapping.
- `tests/test_final_emission_meta.py`: FEM runtime-lineage projection for opening and fail-closed paths.
- `tests/test_golden_replay.py`: opening owner-bucket and replay evidence retention.
- `tests/test_run_scenario_spine_validation.py`: Cycle I opening attribution through prepared payload, gate lineage, and diagnostics.
- `tests/test_start_campaign_api.py`: opening fallback basis uses the journal seed rather than visible-facts leakage.

Opening fixtures and replay dependencies:

- `tests/test_final_emission_gate.py::_opening_gm_output` and `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK`.
- `data/scenes/frontier_gate.json`.
- `data/validation/scenario_spines/c1a_opening_convergence_paths.json` and `data/validation/scenario_spines/frontier_gate_long_session.json`.
- `tests/helpers/golden_replay.py` and the FEM/runtime-lineage diagnostic projections consumed by replay/spine reporting.

Other candidate coverage reviewed:

- Visibility: `tests/test_final_emission_visibility.py`, visibility sections of `tests/test_final_emission_gate.py`, `tests/test_referential_clarity_strict_social_local_repair.py`, `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, and `tests/test_failure_dashboard_controlled_failures.py`.
- Strict-social: `tests/test_social_exchange_emission.py`, `tests/test_strict_social_emergency_fallback_dialogue.py`, strict-social portions of `tests/test_final_emission_gate.py`, `tests/test_output_sanitizer.py`, `tests/test_turn_pipeline_shared.py`, and `tests/test_golden_replay.py`.
- Source-family tagging: `tests/test_realization_provenance.py`, `tests/test_realization_provenance_audit.py`, `tests/test_realization_authority.py`, `tests/test_failure_classifier.py`, `tests/test_failure_classification_contract.py`, and replay/dashboard tests.

Documentation and audit references reviewed:

- `docs/cycles/cycle_i_fallback_authorship_recon_2026-05-25.md`.
- `docs/cycles/cycle_i_a_opening_owner_semantics_contract_2026-05-26.md`.
- `docs/cycles/cycle_i_fallback_authorship_contraction_closure_2026-05-26.md`.
- `audits/cycle_d_visibility_fallback_contraction_closure_2026-05-13.md`.
- `audits/cycle_f_final_gate_hotspot_touch_budget_20260518.md`.
- `docs/final_emission_gate_reduction_plan.md`, `docs/final_emission_ownership_convergence.md`, and `docs/gate_cleanup_inventory.md`.

## Risks / Invariants

- Fallback owner assignment must remain split: successful prepared opening content is `upstream-prepared`, while fail-closed opening remains `sealed-gate`; selector/event ownership remains `game.final_emission_gate`.
- Fallback lineage must retain the Cycle I distinction between authored prose source and gate-selected event owner, including `fallback_authorship_source`.
- Replay stability is strict: exact opening text, fail-closed marker, FEM projection, runtime lineage, golden replay evidence, and scenario-spine diagnostics must not change.
- Evaluator assumptions must remain intact: opening fallback basis stays grounded in the journal/curated facts, without substituting visible-facts or visibility metadata as composition input.
- Logging and telemetry surfaces must preserve current FEM fields, owner buckets, source-family stamping, and failure/debug annotations.
- Source-family tags such as `scene_opening` and sealed fallback realization-family stamping are invariants of the extraction, not part of the first move.
- Gate legality and ordering must remain stable: opening validation, response-type enforcement, visibility-to-opening routing, and prevention of generic observe/action fallback on opening paths stay under the gate's orchestration.
- Duplicate fail-closed metadata construction in the opening block is a legitimate extraction target, but merging semantically distinct failure reasons would be a behavior/telemetry change and is out of scope.
- Visibility should wait because its safe metadata/route helper layer was already extracted in Cycle D; the residual work owns output and enforcement ordering.
- Strict-social should wait because selection is split between emission, gate, and sanitizer paths and interacts with multiple terminal enforcement rules.
- Source-family tagging should wait because it is already centralized across runtime provenance and diagnostic classifier contracts; moving it offers little gate reduction while risking reporting compatibility.

## Files to Pass Back to ChatGPT

For implementation-block planning of the recommended opening selection seam:

- `game/final_emission_gate.py`
- `game/opening_deterministic_fallback.py`
- `game/upstream_response_repairs.py`
- `game/final_emission_meta.py`
- `game/final_emission_sealed_fallback.py`
- `tests/test_final_emission_gate.py`
- `tests/test_upstream_response_repairs.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/helpers/golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`
- `tests/test_start_campaign_api.py`
- `data/scenes/frontier_gate.json`
- `data/validation/scenario_spines/c1a_opening_convergence_paths.json`
- `docs/cycles/cycle_i_a_opening_owner_semantics_contract_2026-05-26.md`
- `docs/cycles/cycle_i_fallback_authorship_contraction_closure_2026-05-26.md`
- `audits/cycle_f_final_gate_hotspot_touch_budget_20260518.md`

## Commands Run

- `git status --short --branch`, `Get-ChildItem -Force -Name`, and `Get-Location`: confirmed the workspace/branch and an initially clean worktree.
- Broad and narrowed `rg -n -i` searches across `game`, `tests`, `tools`, `docs`, and `audits` for opening, visibility, strict-social, gate, fallback, source-family, provenance, and realization-family terms: located implementations, consumers, tests, diagnostics, and prior audit/report material.
- `rg --files` filtered for tests, fixtures, snapshots, golden replay, gate, opening, visibility, social, and source files: identified the candidate behavior and fixture surfaces.
- Targeted `Get-Content` reads of the owner modules, relevant test/helper blocks, and Cycle D/F/I documentation: established existing ownership contracts and prior extraction boundaries.
- `git log --oneline --max-count=12 -- <relevant files>`: confirmed the recent Cycle I opening attribution and earlier fallback/gate contraction history.
- `$env:PYTHONPATH='.\.venv\Lib\site-packages'; <bundled-python> -m pytest tests\test_opening_fallback_owner_bucket.py tests\test_upstream_response_repairs.py tests\test_final_emission_meta.py tests\test_golden_replay.py tests\test_run_scenario_spine_validation.py tests\test_final_emission_gate.py tests\test_start_campaign_api.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_j_recon`: passed, 408 targeted tests.

## No-Change Confirmation

No production code, tests, fixtures, snapshots, or behavior were modified during this recon. The only intentional repository addition is this reconnaissance report. Targeted pytest was run for verification and used `codex_pytest_tmp_cycle_j_recon` as its temporary test directory.
