# CP Corrective Locality Cohort #3 Discovery

Date: 2026-06-28

Scope: discovery/planning only. No fixes, golden files, cohort authority CSVs, or recurrence artifacts were changed.

## 1. Current Corrective Locality Baseline

Most recent locality work shows a frozen CA baseline plus later evidence that standalone CA1-qualifying fixes have not reappeared, while corrective pressure is being absorbed into structural programs.

- `artifacts/ca3_corrective_locality_report.md` / `.json`: first authoritative corrective-locality measurement; 10 qualifying fixes, median raw files touched 12.5, median effective files touched 7.0, median production files 2.5, largest family `opening_fallback` at 60%.
- `docs/baselines/ca_corrective_locality_baseline.md` / `.json`: frozen version 1 baseline; source cohort `docs/audits/CA_corrective_change_locality_cohort.csv`; notes no recurrence linkage and historical window ending 2026-05-20.
- `artifacts/ca5_candidate_inventory.md` / `.json`: post-baseline keyword intake, 26 candidates since 2026-05-20.
- `artifacts/ca6_reviewed_cohort_report.md`: 0 qualifying post-baseline fixes; 26 exclusions.
- `artifacts/ca8_corrective_fix_availability_report.md`: 9 embedded corrective-work candidates, 0 explicit fixes, availability rate 0.3462.
- `artifacts/ca9_embedded_corrective_attribution_report.md`: embedded share 1.0; categories include decomposition, fallback consolidation, ownership compression, replay stabilization.
- `artifacts/ca10_corrective_prevention_effectiveness_report.md`: preventive absorption ratio 1.0; structural programs plausibly prevent or absorb standalone corrective fixes.
- `artifacts/ca11_corrective_fix_watch_report.md` / `.json`: 0 new qualifying fixes, readiness state `no_new_fixes`, CA12 not ready.
- `artifacts/bug_fix_locality_report.md` and `artifacts/bug_fix_locality_regression_guard_report.md`: BR/BRL locality guard baseline; broader and less review-strict than CA.
- Recurrence outcome files: `docs/audits/CO103_outcome_lifecycle_inventory.md`, `docs/audits/CO104_outcome_retirement_propagation_report.md`, `docs/audits/CO105_multi_key_retirement_validation_report.md`, `docs/audits/CO106_active_recurrence_governance_audit.md`, `artifacts/golden_replay/bug_recurrence_event_log.json`, `artifacts/golden_replay/bug_recurrence_history.json`, `artifacts/golden_replay/bug_recurrence_history.md`.
- Tooling: `tools/corrective_change_locality.py`, `tools/corrective_change_candidate_inventory.py`, `tools/corrective_fix_watch.py`, `tools/corrective_prevention_effectiveness_report.py`, `tools/bug_fix_locality_report.py`, `tools/bug_fix_locality_regression_guard_report.py`, `tools/propagate_outcome_retirements.py`, `tools/capture_recurrence_trajectory_activation.py`.

Interpretation: locality improvements appear to be persisting in the strict metric as zero new explicit standalone fixes, but persistence is not yet proven by multiple unrelated new fix cycles. CO106 says existing recurrence keys have no unresolved engineering work; cohort #3 should create new, independent failure -> fix -> validation evidence.

## 2. Candidate Fix Cohort

| Candidate | Symptom / failure mode | Likely source files | Likely test/golden/replay files | Governance? | Blast radius | Why real corrective work | Risk |
|---|---|---|---|---|---|---|---|
| CP1 Sanitizer scaffold leak | Player-facing text leaks planner/router/validator/scaffold terms or malformed payload fragments. | `game/output_sanitizer.py`, `game/output_sanitizer_lineage.py`, maybe `game/final_emission_player_facing_narration_purity.py` | `tests/test_output_sanitizer.py`, `tests/test_golden_replay_structural_invariants.py`, `tests/test_golden_replay_fallback_sanitizer_projection.py` | Usually no; only if protected field list changes. | Low-medium | Fixes unsafe player-visible leakage, not cleanup. Existing protected scenario `sanitizer_scaffold_leakage` gives recurrence key potential. | Low |
| CP2 Directed NPC question route drift | Addressed NPC question routes as action/adjudication or loses dialogue/social lock. | `game/interaction_routing.py`, `game/interaction_context.py`, `game/dialogue_targeting.py`, maybe `game/api.py` | `tests/test_directed_social_routing.py`, `tests/test_dialogue_routing_lock.py`, `tests/test_local_observation_routing.py`, protected `directed_npc_question` in `tests/test_golden_replay_structural_invariants.py` | No unless split-owner matrix/classifier labels change. | Medium | Corrects misrouting visible to players and replay fields (`route_kind`, `trace.social_contract_trace.route_selected`). | Medium |
| CP3 Vocative speaker override regression | Explicit address after prior continuity fails to switch speaker or replay projection disagrees. | `game/interaction_context.py`, `game/speaker_contract_enforcement.py`, `game/final_emission_speaker_observation.py`, `game/post_emission_speaker_adoption.py` | `tests/test_vocative_direct_address_recovery.py`, `tests/test_speaker_contract_enforcement.py`, protected `vocative_override_after_prior_continuity` | Possibly recurrence retirement registry if new protected failure is fixed. | Medium | Fixes wrong speaker selection, a historical recurrence class with measurable selected-speaker outcomes. | Medium |
| CP4 BX guard parity drift | `guard`, `guard_captain`, `gate_guard`, or ambiguous guard cases collapse to wrong parity/status. | `game/speaker_contract_enforcement.py`, `game/final_emission_speaker_observation.py`, `game/dialogue_targeting.py` | `tests/test_bx_speaker_identity_end_to_end_parity.py`, `tests/test_bx_speaker_identity_golden_replay.py`, `tests/helpers/bx_guard_speaker_parity.py`; marker `bx_speaker_parity` | Likely only if retiring a new protected recurrence key. | Medium | Repairs concrete speaker identity defect; existing BX evidence path supports outcome validation. | Medium |
| CP5 Fallback-family projection mismatch | Protected replay projected `fallback_family` prefers wrong taxonomy or reports unavailable despite raw FEM fields. | `tests/helpers/golden_replay_projection.py`, `tests/helpers/golden_replay_projection_fallbacks.py`, `game/final_emission_replay_projection.py`, `game/realization_provenance.py`, `game/diegetic_fallback_narration.py` | `tests/test_golden_replay_projection_fallback_integration.py`, `tests/test_golden_replay_fallback_upstream_fast_projection.py`, `tests/test_golden_replay_projection_presence_integration.py`, `docs/testing/protected_replay_manifest.md` | Possible if protected field docs need refresh; avoid unless required. | Low-medium | Fixes replay observation/diagnostic correctness that affects recurrence classification, not cosmetic cleanup. | Low-medium |
| CP6 Lead follow-up dialogue lock break | Multi-turn NPC lead follow-up drops active target, route, or canonical entry metadata. | `game/interaction_continuity.py`, `game/interaction_context.py`, `game/prompt_context.py`, `game/conversational_memory_window.py` | protected `lead_followup_with_dialogue_lock`, `tests/test_interaction_continuity_contract.py`, `tests/test_interaction_continuity_repair.py`, `tests/test_prompt_context.py`, `tests/test_conversational_memory_window.py` | No unless coverage registry changes. | Medium | Repairs player-visible continuity failure with route/speaker replay metrics. | Medium |
| CP7 Opening fallback authorship/source drift | Opening fallback reports compatibility-local ownership or wrong upstream source despite acceptable prose. | `game/opening_deterministic_fallback.py`, `game/final_emission_opening_fallback.py`, `game/final_emission_meta.py`, `game/fallback_provenance_debug.py` | `tests/test_golden_replay_direct_seam.py::test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership`, `tests/test_golden_replay_fallback_opening_projection.py`, `tests/test_failure_classifier.py` opening-owner rows | Possible split-owner matrix if owner literals change; otherwise no. | Medium | Corrects ownership/source metadata that protected replay treats as acceptance-relevant. | Medium |
| CP8 Scenario-spine long-session degradation | 25-turn Frontier Gate branch shows late fallback spike, generic filler, amnesia, or branch convergence. | `game/scenario_spine_eval.py`, `game/scenario_spine_transition_convergence.py`, `game/prompt_context.py`, `game/social_memory.py` | `tests/test_scenario_spine_eval.py`, `tests/test_golden_replay_long_session.py`, `data/validation/scenario_spines/frontier_gate_long_session.json` | No unless scenario fixture or protected manifest changes; avoid golden fixture edits initially. | High | Repairs sustained-play regression measured by protected long-session stability, not test cleanup. | High |
| CP9 Upstream preflight/config self-invalidates | Startup preflight rejects valid config or mutates runtime call path; OpenAI token minima/health classification wrong. | `game/api_upstream_preflight.py`, `game/config.py`, maybe `game/model_routing.py` | `tests/test_api_upstream_preflight.py`, `tests/test_model_routing_config.py`, `docs/reports/openai_api_key_lazy_config_fix_20260520.md` | No. | Low | Fixes import/startup/runtime availability defect; historically CA-10 was similar. | Low |

Recommended cohort size: pick 5-7 from CP1, CP2, CP3/CP4, CP5, CP6, CP7, CP9. Keep CP8 as a later/high-risk candidate unless a clear failing signal appears.

## 3. Locality Measurement Plan

| Candidate | Expected files touched | Prod files | Governance files | Replay impact | Expected recurrence outcome | Evidence to capture |
|---|---:|---:|---:|---|---|---|
| CP1 Sanitizer scaffold leak | 2-4 | 1-2 | 0 | Protected `scaffold_leakage` / sanitizer fields should pass; possible new protected failure report before fix. | New semantic/sanitizer key fixed and optionally retired if failure was recorded. | Focused pytest output, before/after leaked string, `git diff --name-only`, replay failure row if present. |
| CP2 Directed NPC route drift | 2-5 | 1-3 | 0-1 | `route_kind`, canonical entry, `final_emitted_source` stable in `directed_npc_question`. | New route/fallback key prevented or retired after pass. | Focused route tests, golden replay node output, route debug before/after. |
| CP3 Vocative override | 2-5 | 1-3 | 0 | `selected_speaker_id` stable in vocative protected scenario. | Speaker-drift key fixed; compare recurrence history if protected failure recorded. | Speaker parity diagnostics, golden node, selected speaker before/after. |
| CP4 BX guard parity | 2-5 | 1-3 | 0-1 | BX marker suite green; selected speaker/source parity stable. | New BX-like key can be retired after `bx_speaker_parity` gate. | `pytest -m bx_speaker_parity`, parity record strings, recurrence registry only if needed. |
| CP5 Fallback projection | 2-4 | 0-1 | 0-1 | Projection presence and fallback-family fields classify correctly; no protected manifest drift unless field list changes. | Projection/fallback recurrence reduced; likely no production recurrence unless runtime field absent. | Projection tests, dashboard/classifier row before/after, manifest check if touched. |
| CP6 Lead follow-up lock | 3-6 | 2-4 | 0 | Protected lead follow-up and continuity tests preserve target/route. | Continuity or route key fixed if protected failure appears. | Golden node, continuity contract debug, prompt-context selected memory before/after. |
| CP7 Opening authorship | 2-5 | 1-3 | 0-1 | Direct-seam protected opening ownership/source stable. | Ownership/fallback key fixed or prevented. | Direct-seam test output, classifier evidence row, source/owner strings before/after. |
| CP8 Long-session degradation | 4-8 | 2-5 | 0-1 | Protected 25-turn replay passes without late degradation/fallback spike. | Potential stability/fallback recurrence fixed; high confidence only with replay artifact. | Long-session pytest output, scorecard if intentionally emitted, degradation diagnostics. |
| CP9 Preflight/config | 2-4 | 1-2 | 0 | No golden impact expected. | No replay recurrence; CA locality only, possibly availability/import recurrence. | `tests/test_api_upstream_preflight.py`, exact exception/health string before/after. |

After implementation, record:

- `git diff --name-only` and bucket counts: total files, production files, tests, governance/docs, generated artifacts.
- Focused pytest command output and exact failing/passing node names.
- If protected replay failed before fix: `artifacts/golden_replay/replay_failure_report.md`, corresponding `bug_recurrence_event_log.json` event, regenerated `bug_recurrence_history.{json,md}`.
- Any before/after diagnostic strings: `route_kind`, `selected_speaker_id`, `selected_speaker_source`, `fallback_family`, `final_emitted_source`, `scaffold_leakage`, `sanitizer_*`, `opening_fallback_owner_bucket`.
- Recurrence prevention evidence: passing protected node, no new session-only contamination, and retirement propagation only when a documented protected failure->fix key exists.

## 4. Existing Test / Replay Surface

Known from repo docs:

- Unit/full default: `python -m pytest -q` or `pytest` (uses `pytest.ini` `--basetemp=codex_pytest_tmp`).
- Fast lane: `pytest -m "not transcript and not slow"`.
- Golden replay: `python -m pytest -m golden_replay -q --tb=short`.
- Focused golden replay file: `python -m pytest tests/test_golden_replay.py -q --tb=short` is documented, but the file is now a redirect stub; prefer marker or focused decomposed files.
- Protected structural nodes: `python -m pytest tests/test_golden_replay_structural_invariants.py -q --tb=short`.
- Protected long session: `python -m pytest tests/test_golden_replay_long_session.py::test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability -q`.
- BX parity: `python -m pytest -m bx_speaker_parity -q --tb=short`.
- Failure classifier/dashboard diagnostics: `python -m pytest tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q --tb=short`.
- Projection/presence surface: `python -m pytest tests/test_golden_replay_projection.py tests/test_golden_replay_projection_presence_integration.py tests/test_golden_replay_projection_fallback_integration.py -q --tb=short` (inferred from file ownership).
- Governance/ownership checks: `python -m pytest tests/test_ownership_registry.py tests/test_inventory_governance.py tests/test_gate_boundary_governance.py tests/test_replay_boundary_governance.py tests/test_ownership_write_path_governance.py -q`.
- Split-owner governance: `python scripts/check_split_owner_acceptance_matrix.py`; refresh only when editing matrix/report: `python scripts/refresh_split_owner_acceptance_matrix.py`.
- Protected manifest check: `python tools/refresh_protected_replay_manifest.py --check`.
- Corrective locality tests: `python -m pytest tests/test_corrective_change_locality_classifier.py tests/test_corrective_change_locality_cohort.py tests/test_corrective_change_locality_git_collector.py tests/test_corrective_locality_baseline.py tests/test_corrective_locality_report.py tests/test_corrective_fix_watch.py -q` (inferred).
- CA candidate/locality tools: `python tools/corrective_change_candidate_inventory.py`, `python tools/corrective_change_locality.py`, `python tools/corrective_fix_watch.py`.
- Recurrence lifecycle: `python tools/capture_recurrence_trajectory_activation.py --generated-at <ISO8601Z>`, `python tools/propagate_outcome_retirements.py --dry-run --generated-at <ISO8601Z>`, `python tools/propagate_outcome_retirements.py --check`, `python tools/backfill_bug_recurrence_history.py`.
- Strict audits from CI inventory: `python tools/validation_layer_audit.py --strict`, `python tools/final_emission_ownership_audit.py --strict`, `python tools/validation_coverage_audit.py --strict`.

## 5. Recommended Execution Order

1. CP9 Preflight/config safety. Start with low-risk, non-replay corrective work to prove cohort accounting on a small production fix. Success: focused preflight tests pass and file count stays <=4. Stop/report if imports/config require broad API redesign.
2. CP1 Sanitizer scaffold leak. Low blast radius with strong protected signal. Success: sanitizer unit tests and `sanitizer_scaffold_leakage` protected node pass with no leaked terms. Stop/report if fix requires changing protected field taxonomy.
3. CP2 Directed NPC route drift. Core player-facing route behavior with clear golden protection. Success: route unit/integration tests and `directed_npc_question` pass. Stop/report if dialogue/action boundary needs policy rewrite across interaction modules.
4. CP3 or CP4 Speaker parity. Choose only one first to avoid over-concentrating cohort on speaker work. Success: selected-speaker/source parity stable and BX/vocative node passes. Stop/report if existing CO106 permanent-design keys are being reinterpreted as defects.
5. CP5 Fallback-family projection mismatch. Good replay/projection locality candidate after runtime-facing fixes. Success: projection and classifier tests pass without manifest field churn. Stop/report if change would rename public fallback concepts.
6. CP6 Lead follow-up continuity. More cross-module than route drift; run after routing/speaker fixes are stable. Success: protected lead-followup node and continuity tests pass. Stop/report if candidate requires large prompt-context/memory redesign.
7. CP7 Opening authorship/source drift. Include if cohort still needs fallback-family diversity, but avoid re-opening the historical opening-fallback concentration too early. Success: direct-seam opening test passes and owner/source diagnostics remain canonical. Stop/report if ownership matrix/governance edits dominate production fix.
8. CP8 Long-session degradation. Reserve for last or a separate block. Success: 25-turn protected replay passes and diagnostics show bounded degradation. Stop/report if fixture/golden changes appear necessary before production defect is isolated.

## 6. Files to provide for next block generation

- `CP_corrective_locality_cohort_3_discovery.md`
- `docs/baselines/ca_corrective_locality_baseline.md`
- `docs/baselines/ca_corrective_locality_baseline.json`
- `artifacts/ca3_corrective_locality_report.md`
- `artifacts/ca3_corrective_locality_report.json`
- `artifacts/ca5_candidate_inventory.md`
- `artifacts/ca6_reviewed_cohort_report.md`
- `artifacts/ca8_corrective_fix_availability_report.md`
- `artifacts/ca9_embedded_corrective_attribution_report.md`
- `artifacts/ca10_corrective_prevention_effectiveness_report.md`
- `artifacts/ca11_corrective_fix_watch_report.md`
- `docs/audits/CO103_outcome_lifecycle_inventory.md`
- `docs/audits/CO105_multi_key_retirement_validation_report.md`
- `docs/audits/CO106_active_recurrence_governance_audit.md`
- `docs/testing/protected_replay_manifest.md`
- Any failing focused pytest output for the chosen candidate.
- Key source/test files for the chosen candidate only, e.g. CP1: `game/output_sanitizer.py`, `game/output_sanitizer_lineage.py`, `tests/test_output_sanitizer.py`, `tests/test_golden_replay_structural_invariants.py`; CP2: `game/interaction_routing.py`, `game/interaction_context.py`, `tests/test_directed_social_routing.py`, `tests/test_dialogue_routing_lock.py`; CP4: `game/speaker_contract_enforcement.py`, `game/final_emission_speaker_observation.py`, `tests/test_bx_speaker_identity_golden_replay.py`, `tests/helpers/bx_guard_speaker_parity.py`.
