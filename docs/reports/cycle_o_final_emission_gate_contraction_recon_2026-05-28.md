# Cycle O Final Emission Gate Contraction Recon - 2026-05-28

## Recommendation

Recommended Cycle O cluster: **replay projection helpers**.

Reason: this is the safest meaningful contraction target left after prior opening and visibility extraction work. It is read-side only, already has direct unit tests plus golden replay and scenario-spine projection coverage, and can be extracted without changing emitted text, route selection, fallback authorship, or FEM write-time semantics. It also reduces reasons to touch the gate-adjacent final-emission metadata module when replay/dashboard projection logic changes.

Do not mix this with opening fallback, strict-social fallback, visibility fallback, or provenance tagging in the same implementation block.

## 1. Main Gate Inventory

Primary final-emission gate files:

- `game/final_emission_gate.py`: canonical final-emission orchestration owner. Main public entrypoint is `apply_final_emission_gate(...)` at about lines 8719-10400.
- `game/final_emission_meta.py`: FEM packaging, read-side normalization, runtime-lineage projection, observability projection, dead-turn projection.
- `game/final_emission_opening_fallback.py`: already-extracted opening fallback adapter.
- `game/final_emission_visibility_fallback.py`: already-extracted visibility fallback helper/context/payload module.
- `game/final_emission_sealed_fallback.py`: sealed fallback selection/stamping helper module.
- `game/realization_provenance.py`: fallback-family normalization/stamping vocabulary.
- `game/fallback_provenance_debug.py`: upstream fast-fallback provenance trace/entry-exit observation.

Major branch clusters inside `game/final_emission_gate.py`:

| Cluster | Approx. range | Responsibility | Current helper usage | Current tests touching it | Mutation/selection/projection role |
|---|---:|---|---|---|---|
| Non-strict sealed fallback providers/selectors | 351-554, 10160-10395 | Assemble/select terminal fallback for non-strict replace path. | `game.final_emission_sealed_fallback`, opening adapter, social fallback helpers, anti-reset helper. | `tests/test_final_emission_gate.py` selector snapshots around 4691-5328; visibility tests; golden replay projection tests. | Selects fallback, mutates output on replace, tags FEM/provenance. |
| Narration constraint debug projection | 556-1154 | Compact read-side/debug projection of visibility/speaker/response constraints. | Local helpers plus visibility contract resolver. | `tests/test_final_emission_gate.py` around 2573-2967. | Projects audit/debug state only. |
| Contract validation layer cluster | 1156-3809 | Tone, narrative authority, anti-railroading, context separation, purity, answer shape, scene anchor validation/metadata. | Domain validators and merge helpers. | `tests/test_final_emission_gate.py` broad tests around 3064-3802, plus dedicated validator suites. | Mostly validation/projection; some mutation seams still guarded by boundary contract. |
| Opening response-type/fallback branch | 3818-4400, 9690-9715, 10146-10158 | Scene-opening validation, prepared opening fallback selection, fail-closed metadata, accepted opening reassertion. | `game.final_emission_opening_fallback`, `game.opening_deterministic_fallback`, upstream prepared repair helpers. | `tests/test_final_emission_gate.py` around 3933-4498 and 5521-5918; `tests/test_final_emission_opening_fallback.py`; golden direct seam opening tests. | Selects fallback or accepts candidate; mutates output through response-type repair path; tags FEM. |
| Finalize/packaging and upstream fallback containment | 4686-4996 | Final output packaging, route-illegal stock stripping, provenance trace entry/exit, mutation lineage refresh. | `game.fallback_provenance_debug`, `game.final_emission_meta`, sanitizer trace helpers. | `tests/test_final_emission_gate.py` around 6512-6580; fallback overwrite tests; golden sanitizer projection tests. | Mutates packaging only; projects provenance/mutation lineage. |
| Passive scene / visible scene composition | 5100-6881 | Passive pressure fallback, visible entity catalog, first-mention composition candidates, scene-safe fallback construction. | Scene/world/lead helpers; visibility fallback context builders. | `tests/test_final_emission_visibility.py`; `tests/test_final_emission_gate.py` visibility/opening tests. | Selects fallback candidates; can feed visibility fallback. |
| Visibility enforcement | 6882-7665 | Visibility, first-mention, referential clarity replacement/local repair routing. | `game.narration_visibility`, `game.final_emission_visibility_fallback`. | `tests/test_final_emission_visibility.py`; `tests/test_final_emission_visibility_fallback.py`; golden projection tests. | Selects fallback, mutates output, tags FEM/provenance. |
| Interaction continuity / speaker bridge | 7670-8315 | Interaction continuity validation, repair metadata, speaker enforcement bridge. | `game.interaction_continuity`, `game.speaker_contract_enforcement`. | `tests/test_final_emission_gate.py` around 645-813 and 703-770; continuity suites; golden replay. | Mutates speaker/continuity output in guarded cases; projects audit state. |
| Referent clarity pre-finalize, narrative-mode output, acceptance-quality floor | 8322-8543, 8544-8718 | Final referent metadata, NMO legality, N4 acceptance-quality floor seam. | `game.final_emission_repairs`, `game.final_emission_meta`, `game.acceptance_quality`. | `tests/test_final_emission_gate.py` around 668-695, 128-458, 6603-6751; C4 pipeline tests. | Mutates via N4/NMO replacement paths; projects FEM. |
| Main apply orchestration | 8719-10400 | Layer order, strict-social integration, accept/replace paths, visibility/NMO/AQ/finalize calls. | All helper modules above. | `tests/test_final_emission_gate.py`; `tests/test_c4_narrative_mode_live_pipeline.py`; `tests/test_golden_replay.py`. | Routes, selects fallbacks, mutates final output, stamps/projections. |

Replay/projection cluster outside the main gate:

- `game/final_emission_meta.py` lines 1190-1627: helper projection logic for FEM runtime lineage events.
- `tests/helpers/golden_replay.py` lines 586-820 and 1120-1480: replay observation, fallback owner summaries, runtime lineage debug projection.
- `tools/run_scenario_spine_validation.py` runtime-lineage projection/summary consumers.

## 2. Cluster Suitability Matrix

| Cluster | Current files/functions | Estimated orchestration density | Behavior-risk level | Test coverage strength | Replay sensitivity | Extraction readiness | Recommended / Not Recommended | Reason |
|---|---|---:|---|---|---|---|---|---|
| Opening fallback | `game/final_emission_gate.py::_enforce_response_type_contract`, `_opening_scene_safe_fallback_tuple`; `game/final_emission_opening_fallback.py` | Medium | Medium | Strong | High | Partly already extracted | Not Recommended | Already contracted in prior cycles. Remaining inline code still controls response-type behavior and accepted-opening reassertion, so another move risks opening semantics. |
| Strict-social fallback | `apply_final_emission_gate`, `build_final_strict_social_response`, strict-social NMO/fallback branches | High | High | Strong | High | Low | Not Recommended | Large density payoff, but it crosses dialogue legality, sanitizer fallback, visibility, NMO, speaker, and terminal fallback authorship. Too behavior-sensitive for Cycle O. |
| Visibility fallback | `_apply_visibility_enforcement`, `_apply_first_mention_enforcement`, `_apply_referential_clarity_enforcement`; `game/final_emission_visibility_fallback.py` | High | Medium-high | Strong | High | Medium | Not Recommended | Helper module is already substantial. Remaining gate code owns mutation/order/logging and should not be moved until a narrower branch is isolated. |
| Replay projection helpers | `game/final_emission_meta.py::_fem_selected_fallback_projection`, `_append_fem_mutation_projections`, `build_fem_runtime_lineage_events`; replay/scenario-spine consumers | Medium-high | Low | Strong | High but read-side | High | **Recommended** | Pure projection from finalized FEM. Strong direct tests and replay/dashboard consumers. No emitted text, routing, or fallback selection changes required. |
| Provenance tagging | `game.realization_provenance`, `game.final_emission_sealed_fallback`, gate `attach_realization_fallback_family` calls, FEM owner buckets | Medium | Medium | Strong | High | Medium | Not Recommended | Tagging is behavior-adjacent because provenance/fallback authorship is acceptance evidence. Better treated as invariant while extracting replay projection helpers. |

## 3. Best Single Cluster Recommendation

Pick exactly one cluster for Cycle O: **replay projection helpers**.

Why this beats the other candidates:

- It is read-side only. The source data is already finalized FEM; extraction cannot change the player-facing emission unless imports or callers are accidentally changed.
- It has high density relative to risk. `game/final_emission_meta.py` lines 1190-1627 contain fallback selection projection, gate outcome projection, speaker repair projection, mutation projection, recurrence event construction, and de-duplication.
- It is already covered by direct tests: `tests/test_final_emission_meta.py` checks conservative fallback projection, strict-social/sanitizer projection, opening/fail-closed projection, mutation projection, speaker repair projection, and unified bundle exposure.
- It is replay-sensitive in a useful way: golden replay and scenario-spine tests consume the projection and would detect shape/owner/fallback drift.
- Opening and visibility have already been partially extracted, so further contraction there would likely move order-sensitive mutation code. Strict-social is denser but too entangled. Provenance tagging is better held still while projection extraction gives a safe place to centralize read-side interpretation.

## 4. Existing Protection Inventory

Direct tests for chosen cluster:

- `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_acceptance_outcomes_do_not_invent_fallbacks`
- `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_opening_and_fail_closed_fallbacks`
- `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_strict_social_and_sanitizer_fallbacks`
- `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_is_conservative_serializable_and_recurrence_ready`
- `tests/test_final_emission_meta.py::test_assemble_unified_observational_bundle_exposes_fem_runtime_lineage_sibling_surface`
- `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_explicit_speaker_contract_repairs`
- `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_interaction_continuity_repairs`
- `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_explicit_mutation_evidence_without_explosion`
- `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_sanitizer_and_unknown_post_gate_mutation`

Replay/projection tests:

- `tests/test_golden_replay.py::test_golden_observed_turn_projects_runtime_lineage_and_prefers_existing_events`
- `tests/test_golden_replay.py::test_golden_observed_turn_projects_fail_closed_sealed_gate_opening_owner_bucket`
- `tests/test_golden_replay.py::test_golden_observed_turn_projects_sealed_fallback_owner_bucket`
- `tests/test_golden_replay.py::test_golden_observed_turn_projects_strict_social_sealed_fallback_owner_bucket`
- `tests/test_golden_replay.py::test_golden_observed_turn_projects_visibility_fallback_evidence`
- `tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_20_turn_structural_stability`

Scenario-spine/dashboard tests:

- `tests/test_run_scenario_spine_validation.py::test_transcript_meta_runtime_lineage_prefers_projected_bundle_and_projects_fem_fallback`
- `tests/test_run_scenario_spine_validation.py::test_build_runtime_lineage_summary_counts_frequency_and_recurrence_without_scoring_fields`
- `tests/test_run_scenario_spine_validation.py::test_cycle_i_opening_attribution_survives_prepared_payload_gate_lineage_and_diagnostics`
- `tests/test_run_scenario_spine_validation.py::test_all_branches_aggregate_artifacts_and_payload`
- `tests/test_runtime_lineage_telemetry.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`

Relevant fixtures/artifacts:

- `docs/testing/protected_replay_manifest.md`
- `data/validation/scenario_spines/frontier_gate_long_session.json`
- `data/validation/scenario_spines/c1a_opening_convergence_paths.json`
- `audits/golden_replay_baseline_2026-05-11.md`
- `docs/audits/cycle_k_replay_promotion_recon_2026-05-26.md`
- `docs/reports/cycle_h_runtime_lineage_closure_2026-05-25.md`

Narrow commands:

```bash
python -m pytest tests/test_final_emission_meta.py -q
python -m pytest tests/test_golden_replay.py::test_golden_observed_turn_projects_runtime_lineage_and_prefers_existing_events tests/test_run_scenario_spine_validation.py::test_transcript_meta_runtime_lineage_prefers_projected_bundle_and_projects_fem_fallback -q
```

Broader replay/full-suite protection:

```bash
python -m pytest tests/test_golden_replay.py -q
python -m pytest tests/test_run_scenario_spine_validation.py tests/test_runtime_lineage_telemetry.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q
python -m pytest -q
```

## 5. Missing Protection

Minimum before/after protection before refactor:

- Add one narrow regression test in `tests/test_final_emission_meta.py` that snapshots the runtime-lineage event sequence for a FEM containing both `visibility_replacement_applied=True` and `sealed_fallback_owner_bucket`. This protects the visibility/sealed projection split while moving helpers.
- Add one replay fixture assertion in `tests/test_golden_replay.py::test_golden_observed_turn_projects_visibility_fallback_evidence` or a sibling test that asserts the projected `runtime_lineage_events` include `fallback_selected` with `fallback_kind == "visibility_or_scene_replacement"` and `gate_outcome` with `gate_path == "visibility_or_scene_replaced"`.
- Add one scenario-spine/dashboard assertion in `tests/test_run_scenario_spine_validation.py` that a visibility replacement projected from FEM contributes to `fallback_frequency` and `gate_path_frequency` without requiring a live chat run.

No broad new infrastructure is needed.

## 6. Extraction Seam Proposal

Chosen cluster only: replay projection helpers.

Source file/function:

- Source: `game/final_emission_meta.py`
- Current public function to preserve: `build_fem_runtime_lineage_events(fem)`

Proposed destination:

- `game/final_emission_replay_projection.py`

Proposed helper functions:

- `build_fem_runtime_lineage_events(fem)`
- `_fem_selected_fallback_projection(fem)`
- `_fem_speaker_repair_projections(fem)`
- `_append_fem_mutation_projections(events, fem, fallback, speaker_projections)`
- `_fem_mutation_lineage_tokens(fem)`
- `_append_fem_lineage_event(events, event)`

Inputs:

- A FEM-shaped mapping after normalization or raw finalized FEM.
- Existing constants and event helpers from `game.runtime_lineage_telemetry`.
- Owner-bucket helper `opening_fallback_owner_bucket_from_meta`.

Outputs:

- A bounded `list[dict[str, Any]]` of runtime-lineage events, max 16 events, JSON serializable, stable recurrence keys.

Invariants:

- Prepared payload presence alone must not create fallback-selection evidence.
- Accept-unchanged and accept-repaired outcomes must not invent fallback events.
- Opening prepared and opening fail-closed projections must keep distinct fallback kinds and owner buckets.
- Strict-social emergency and strict-social deterministic fallback projections must remain distinct.
- Sanitizer fallback events must remain owned by `game.output_sanitizer` and staged as `sanitizer`.
- Visibility/sealed replacement projection must keep `visibility_or_scene_replacement` and `visibility_or_scene_replaced`.
- Existing public import path `game.final_emission_meta.build_fem_runtime_lineage_events` must remain as a compatibility wrapper or re-export.

What must NOT move:

- `normalize_final_emission_meta_for_observability`
- `build_fem_observability_events`
- `assemble_unified_observational_telemetry_bundle` public bundle API, except import/call wiring to the extracted helper.
- FEM write-time mutation functions such as `ensure_final_emission_meta_dict`, `patch_final_emission_meta`, `refresh_final_emission_mutation_lineage`.
- Any gate fallback selection, output mutation, final-route stamping, or final-emitted-source assignment.

What remains owned by the main gate:

- Emitted text selection/mutation.
- Branch order in `apply_final_emission_gate`.
- Strict-social, visibility, opening, NMO, N4, and sealed fallback route semantics.
- The actual FEM evidence that projection reads.

## 7. Selector/Provenance Consolidation Opportunities

For replay projection only:

- Consolidate repeated fallback-projection tuple handling into a small internal typed shape or `NamedTuple` in the new helper module. This is safe if it preserves the existing tuple fields exactly at the wrapper boundary.
- Keep owner/provenance interpretation read-side. Do not merge with `game.realization_provenance` or sealed/visibility/opening stamping during Cycle O.
- Do not consolidate `opening_fallback_owner_bucket_from_meta` into the new module; it is already a canonical read-side owner-bucket helper in `game.final_emission_meta.py`.
- Do not alter recurrence-key construction. That remains owned by `game.runtime_lineage_telemetry.make_runtime_lineage_event`.

## 8. Branch-Local Ownership Comments

Proposed comments:

| File | Approx. location | Purpose | Exact comment text draft |
|---|---:|---|---|
| `game/final_emission_meta.py` | Above compatibility wrapper for `build_fem_runtime_lineage_events` after extraction | Clarify this is legacy import surface only. | `# Compatibility surface: runtime-lineage projection lives in final_emission_replay_projection; keep this import path stable for replay/dashboard consumers.` |
| `game/final_emission_replay_projection.py` | Module docstring/top | Prevent future behavior logic from moving into projection. | `"""Read-side FEM replay/runtime-lineage projection helpers. This module must not select fallbacks, mutate output, or stamp write-time FEM."""` |
| `game/final_emission_replay_projection.py` | Above `_fem_selected_fallback_projection` | Clarify evidence threshold. | `# Projection only: infer fallback selection from finalized FEM evidence, never from prepared payload availability alone.` |
| `game/final_emission_replay_projection.py` | Above sanitizer branch in `_fem_selected_fallback_projection` | Clarify sanitizer ownership. | `# Sanitizer fallback projection keeps sanitizer stage/owner even when surfaced through final-emission telemetry.` |
| `game/final_emission_replay_projection.py` | Above opening branch in `_fem_selected_fallback_projection` | Clarify authorship split. | `# Opening projection separates gate selection ownership from upstream-prepared prose authorship.` |
| `tests/helpers/golden_replay.py` | Above `_runtime_lineage_events_from_payload` | Clarify precedence. | `# Prefer preprojected bundle events; falling back to FEM projection is a replay diagnostic convenience, not runtime behavior.` |

## 9. Risk Register

- Replay drift: event ordering, event count cap, recurrence keys, or fallback/gate outcome pairing could change if helper extraction changes de-duplication order.
- Fallback authorship drift: opening prepared fallback could lose `fallback_authorship_source == "upstream_prepared_opening_fallback"` or owner bucket `upstream-prepared`.
- Provenance/tagging drift: `fallback_kind`, `gate_path`, `owner`, and `stage` fields are diagnostic contract surfaces used by golden replay and scenario-spine summaries.
- Strict-social drift: strict-social emergency and deterministic fallback projection must stay distinct even though no strict-social behavior moves.
- Visibility drift: visibility replacement projection must remain a replay projection, not a new visibility fallback owner.
- Fixture churn: golden replay debug strings and scenario-spine lineage summaries can churn if event order or field presence changes.
- Hidden semantic mutation risk: low, provided no gate imports are changed except the public projection call/re-export and no FEM write-time stamping moves.

## 10. Recommended Implementation Blocks

Block O1 — Projection Lock
Purpose:
Add the minimum missing projection protection before extraction.
Files likely touched:
`tests/test_final_emission_meta.py`, `tests/test_golden_replay.py`, optionally `tests/test_run_scenario_spine_validation.py`.
Behavior change: No
Tests to run:
`python -m pytest tests/test_final_emission_meta.py tests/test_golden_replay.py::test_golden_observed_turn_projects_visibility_fallback_evidence tests/test_run_scenario_spine_validation.py::test_transcript_meta_runtime_lineage_prefers_projected_bundle_and_projects_fem_fallback -q`
Exit criteria:
New assertions fail against intentional projection drift and pass against current behavior.

Block O2 — Helper Extraction
Purpose:
Move runtime-lineage FEM projection internals into `game/final_emission_replay_projection.py` while preserving `game.final_emission_meta.build_fem_runtime_lineage_events` as a wrapper/re-export.
Files likely touched:
`game/final_emission_meta.py`, `game/final_emission_replay_projection.py`.
Behavior change: No
Tests to run:
`python -m pytest tests/test_final_emission_meta.py -q`
Exit criteria:
Public API still imports from `game.final_emission_meta`; event lists and recurrence keys are unchanged.

Block O3 — Replay Projection Confirmation
Purpose:
Confirm replay, dashboard, and scenario-spine consumers still see identical projected lineage surfaces.
Files likely touched:
None expected beyond O1/O2 files.
Behavior change: No
Tests to run:
`python -m pytest tests/test_golden_replay.py tests/test_run_scenario_spine_validation.py tests/test_runtime_lineage_telemetry.py -q`
Exit criteria:
Golden projection rows, protected replay, scenario-spine lineage summary, and runtime-lineage telemetry tests pass.

Block O4 — Full Protection Sweep
Purpose:
Run broad protection after the no-behavior extraction.
Files likely touched:
None expected.
Behavior change: No
Tests to run:
`python -m pytest -q`
Exit criteria:
Full suite passes or any unrelated pre-existing failures are documented separately with no projection drift.
