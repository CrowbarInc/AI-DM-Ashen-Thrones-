# Cycle AU2 Golden Replay Owner Mapping

## Purpose

This artifact makes ownership explicit for the golden replay assertion families
inventoried in AU1. It is a planning and routing map only: no tests are moved,
no replay behavior changes, no expected diagnostics change, and golden replay
coverage remains unchanged.

Sources:

- `audits/cycle_au_replay_assertion_family_inventory.md`
- `cycle_au_golden_replay_ownership_compression_recon.md`

## Owner Bucket Definitions

| Owner bucket | Definition | Non-goal |
|---|---|---|
| Golden replay hard-fail orchestration | End-to-end replay acceptance and supporting replay orchestration that must continue to prove full `chat`/storage/projection behavior through real replay paths. | Does not own runtime route, speaker, fallback, gate, sanitizer, or diagnostics semantics. |
| Replay projection owner | Read-side observed-turn projection contracts, protected observation registry, extraction registry, unavailable-field representation, raw-signal presence, and projection helper parity. | Does not own gameplay behavior or protected scenario acceptance. |
| Diagnostics/report owner | Failure dashboard rows, protected replay failure report rendering/writing, rerun scorecard artifacts, opt-in diagnostic recording, and byte-sensitive operator report text. | Does not own runtime behavior or hard-fail replay coverage. |
| Drift taxonomy owner | Rerun delta classification, owner-drift buckets, trend/hotspot/risk aggregation, report-only drift scorecards, and stability ownership projections. | Does not own replay execution or runtime subsystem behavior. |
| Fallback/final-emission owner | Fallback owner-bucket proofs, final-emission read-side lineage projection, sealed/visibility/upstream-prepared/sanitizer owner splits, and gate/fallback contract surfaces. | Does not own golden replay orchestration or replay report formatting. |
| Helper extraction | Reusable assertion fragments, synthetic factories, summary/renderer helper contracts, and golden-facing helper shape. | Does not become a new mega-owner; helpers should remain narrow and imported by owner tests only when they reduce duplication. |

## Owner Bucket Map

### Golden replay hard-fail orchestration

Owned assertion families:

- Directed NPC question protected replay.
- Vocative override protected replay.
- Wrong-speaker strict-social protected replay.
- Thin answer action-outcome protected replay.
- Sanitizer scaffold leakage protected replay.
- Lead follow-up dialogue lock protected replay.
- Frontier Gate social-inquiry 25-turn stability.
- Frontier Gate resume persistence supporting probe.
- Frontier Gate direct-intrusion diagnostic stability.
- Scenario spine three-branch structural smoke.

Current files:

- `tests/test_golden_replay.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_fixtures.py`
- `data/validation/scenario_spines/frontier_gate_long_session.json`

Proposed future owner files:

- Keep primary ownership in `tests/test_golden_replay.py`.
- Helper-only support may live in `tests/helpers/golden_replay.py` or `tests/helpers/golden_replay_fixtures.py`.

What should remain in `tests/test_golden_replay.py`:

- Full protected E2E replay tests.
- Long-session acceptance thresholds and debug context until a later closeout preserves them exactly.
- Scenario spine smoke orchestration.
- Minimal bridge assertions proving owner-moved projection fields still survive the real replay path.

What may move later:

- Inline assertion-fragment construction that can call existing helpers without weakening the scenario.
- Repeated long-session threshold checks only after helper tests prove identical semantics.

### Replay projection owner

Owned assertion families:

- Projection adapter equivalence.
- Dual fallback-family read-side precedence.
- Direct-seam observed turn helper projection.
- Protected replay manifest parity.
- Protected path representation and extraction registry.
- Sanitizer lineage projection where the concern is observed-turn extraction rather than sanitizer behavior.

Current files:

- `tests/test_golden_replay.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/golden_replay_fixtures.py`
- `tools/refresh_protected_replay_manifest.py`
- `docs/testing/protected_replay_manifest.md`

Proposed future owner files:

- New focused projection test module, recommended name: `tests/test_golden_replay_projection.py`.
- Existing helper authority: `tests/helpers/golden_replay_projection.py`.
- Existing fixture authority: `tests/helpers/golden_replay_fixtures.py`.

What should remain in `tests/test_golden_replay.py`:

- Real replay bridge checks that projected fields are present in protected scenarios.
- No broad registry/extraction matrix after equivalent projection-owner tests exist.

What may move later:

- Synthetic `project_turn_observation` and `project_synthetic_turn` assertions.
- Manifest parity tests.
- Protected path count/coverage tests.
- Dual-family read-side projection tests.

### Diagnostics/report owner

Owned assertion families:

- Protected failure report bridge.
- Drift classifier bucket counts when the assertion is about failure row/report shape.
- Runtime lineage diagnostic classification boundary.
- Rerun scorecard rendering and writers.
- Golden replay markdown/report helper rendering where report text, not replay behavior, is under test.

Current files:

- `tests/test_golden_replay.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/failure_classifier.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_failure_dashboard_controlled_failures.py`

Proposed future owner files:

- Prefer existing `tests/test_failure_classification_contract.py` for contract/schema assertions.
- Prefer existing `tests/test_failure_dashboard_controlled_failures.py` for dashboard behavior probes.
- If needed, create a narrow `tests/test_failure_dashboard_report.py` for renderer/writer unit coverage.

What should remain in `tests/test_golden_replay.py`:

- At most one bridge proving protected replay assertion failure recording is wired from golden assertions into diagnostics.
- No broad markdown report body checks once equivalent diagnostics owner tests exist.

What may move later:

- Protected failure report headings and table formatting.
- Rerun scorecard JSON/markdown writer tests.
- Opt-in diagnostic recording tests.
- Runtime-lineage diagnostic recording boundary tests.

### Drift taxonomy owner

Owned assertion families:

- Synthetic rerun comparison deltas.
- Response-delta frequency deltas.
- Owner drift rows from rerun deltas.
- Stability classification rows derived from scorecards.
- Longitudinal, hotspot, trend, and risk aggregation.

Current files:

- `tests/test_golden_replay.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/replay_drift_taxonomy.py`
- `tests/helpers/replay_drift_hotspots.py`
- `tests/helpers/replay_drift_risk.py`
- `tests/test_replay_drift_taxonomy.py`
- `tests/test_replay_drift_hotspots.py`
- `tests/test_replay_drift_longitudinal.py`
- `tests/test_replay_drift_trends.py`
- `tests/test_replay_drift_risk.py`
- `tests/test_stability_reporting_contract.py`

Proposed future owner files:

- Existing replay drift tests listed above.
- Existing `tests/test_stability_reporting_contract.py` for stability schema/governance assertions.
- Optional narrow fixture helper, if needed: `tests/helpers/replay_drift_fixtures.py`.

What should remain in `tests/test_golden_replay.py`:

- Assertions that real replay summaries produce inputs compatible with drift/taxonomy helpers.
- Long-session acceptance thresholds until separately extracted.

What may move later:

- Synthetic `_synthetic_rerun_turn` / `_synthetic_rerun_scorecard` style tests.
- Rerun frequency delta unit tests.
- Owner drift classification row shape tests.
- Stability ownership projection tests that use fabricated scorecards.

### Fallback/final-emission owner

Owned assertion families:

- Opening fallback owner projection.
- Runtime lineage projection from observed turn/FEM.
- Neutral speaker grounding fallback family.
- Scene-action fallback speaker absence optionality, when tied to fallback classification.
- Sealed and strict-social fallback owner projection.
- Visibility fallback evidence projection.
- Upstream prepared emission telemetry.
- Sanitizer empty fallback and strict-social split projection.

Current files:

- `tests/test_golden_replay.py`
- `game/final_emission_replay_projection.py`
- `game/final_emission_meta.py`
- `tests/test_final_emission_meta.py`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_visibility.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_output_sanitizer.py`

Proposed future owner files:

- Existing `tests/test_opening_fallback_owner_bucket.py` for opening owner bucket semantics.
- Existing `tests/test_final_emission_meta.py` and `tests/test_final_emission_gate.py` for final-emission metadata/gate contracts.
- Existing `tests/test_final_emission_visibility.py` for visibility fallback.
- Existing `tests/test_failure_classification_contract.py` for cross-layer owner-bucket value contracts.
- Existing sanitizer owner tests for sanitizer lineage/fallback behavior.

What should remain in `tests/test_golden_replay.py`:

- Replay-path proof that owner/fallback projection fields survive through real golden scenarios.
- Protected E2E fallback observations that contribute to hard-fail acceptance.

What may move later:

- Synthetic owner-bucket projection tests.
- Synthetic lineage projection tests.
- Prepared-emission telemetry projection tests.
- Sanitizer owner split projection tests that do not require replay execution.

### Helper extraction

Owned assertion families:

- Assertion helper dotted-path and debug behavior.
- Golden markdown report renderer.
- Long-session replay summary renderer.
- Long-session stability scorecard helper shape.
- Route/speaker expectation fragments.
- Reusable synthetic row/scorecard factories, only if multiple owner files need them.

Current files:

- `tests/test_golden_replay.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_fixtures.py`
- `tests/helpers/opening_fallback_evidence.py`

Proposed future owner files:

- Existing `tests/helpers/golden_replay.py` for expectation, summary, scorecard, and markdown helper implementations.
- Existing `tests/helpers/golden_replay_fixtures.py` for replay/synthetic payload factories.
- Existing `tests/helpers/opening_fallback_evidence.py` for opening fallback expected field factories.
- Optional narrow `tests/helpers/replay_drift_fixtures.py` only if AU movement creates repeated fabricated rerun rows.

What should remain in `tests/test_golden_replay.py`:

- Calls to helper fragments from protected scenarios.
- Scenario-specific expectations that are easier to understand inline and are not duplicated.

What may move later:

- Unit-level helper behavior assertions.
- Repeated threshold/assertion bundles after helper contracts prove exact equivalence.
- Synthetic factories that otherwise would be copied into multiple owner tests.

## Do Not Move Yet

The following must remain in `tests/test_golden_replay.py` until later AU blocks add equivalent owner coverage and a closeout preserves golden replay semantics:

- `test_golden_replay_directed_npc_question_structural_invariants`
- `test_golden_replay_vocative_override_after_prior_continuity_structural_invariants`
- `test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants`
- `test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants`
- `test_golden_replay_sanitizer_scaffold_leakage_structural_invariants`
- `test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants`
- `test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability`
- `test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting`
- `test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability`
- `test_golden_replay_scenario_spine_three_branch_structural_smoke`

Do not move yet:

- Any protected E2E replay scenario that exercises the real `chat` path.
- Long-session acceptance thresholds and recurrence-key allowlists.
- Debug context strings used to explain golden replay failures.
- Diagnostic report expected strings or command text.
- Protected observation field count, protected drift bucket assignments, or manifest output semantics.

## Recommended Import and Constant Strategy

Do not add a new shared "golden replay owner registry" module in AU2. A new code module would risk becoming a mega-owner before tests are actually moved.

Recommended future strategy:

- Keep executable constants with the narrow owner that already owns the behavior.
- Projection constants stay in `tests/helpers/golden_replay_projection.py`.
- Replay expectation helpers stay in `tests/helpers/golden_replay.py`.
- Golden replay fixture factories stay in `tests/helpers/golden_replay_fixtures.py`.
- Failure report paths, environment variables, and renderer/writer helpers stay in `tests/helpers/failure_dashboard_report.py`.
- Drift taxonomy labels and aggregation helpers stay in `tests/helpers/replay_drift_taxonomy.py` and related drift helper modules.
- Opening fallback expected fields and compatibility-local test vocabulary stay in `tests/helpers/opening_fallback_evidence.py`.
- Final-emission read-side lineage constants stay in `game/final_emission_replay_projection.py` / `game/final_emission_meta.py`.

For later AU blocks:

- Prefer importing existing owner constants directly from their owner modules.
- If multiple future tests need the same fabricated rerun rows, add a narrow fixture helper rather than a global owner registry.
- If multiple future tests need the same assertion family list, keep that list as documentation in this audit artifact unless code needs executable data.
- Do not have production modules import from tests or audit docs.
- Do not have `tests/test_golden_replay.py` import a new broad AU owner map just to route assertions; golden replay should become thinner by calling narrow helpers, not by consulting a central registry.

## Validation Commands

Recommended for AU2:

```bash
python -m pytest tests/test_ownership_registry.py tests/test_failure_classification_contract.py -q --tb=short
python tools/test_audit.py --check
```

No validation command is required to prove runtime behavior for this mapping-only artifact, but the commands above are the ownership/governance slice to run after later owner-map edits.

