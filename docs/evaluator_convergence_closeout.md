# Evaluator Convergence Closeout

Status: **converged / maintenance-grade**.

This closeout freezes the evaluator cleanup/convergence pass completed across Blocks A-F. The evaluator layer remains an offline, read-only consumer of finalized outputs, telemetry, and artifacts. It performs no runtime repairs, has no gate legality authority, and has no engine truth authority.

## Completed Scope

- Block A inventoried evaluator-owned modules, runners, tests, telemetry surfaces, overlap risks, and cleanup candidates in `docs/evaluator_convergence_inventory.md`.
- Block B classified telemetry surfaces and terminology so `_final_emission_meta`, normalized observational bundles, evaluator events, stage-diff telemetry, playability artifacts, and scenario-spine artifacts stay distinct.
- Block C pinned dead-turn ownership: evaluators consume FEM/dead-turn source data and do not infer dead turns from API-error-looking payload fields.
- Block D pinned playability versus behavioral gauntlet ownership: `game/playability_eval.py` remains the turn-level playability scorer, while `tests/helpers/behavioral_gauntlet_eval.py` remains a shallow transcript-slice regression helper.
- Block E pinned scenario-spine metadata terminology: scenario-spine transcript `meta` is an artifact envelope, while FEM correctness remains separately owned by FEM helpers/tests.
- Block F pinned governance audit scope: `tools/architecture_audit.py` remains broad repo governance, while `tools/validation_layer_audit.py` remains the narrow Objective #11 validation-layer separation checker.

## Protected Evaluator Invariants

- Evaluator code is offline and read-only.
- Evaluator output may inform humans, regression triage, and artifacts, but must not decide live routing, retries, emitted text, state mutation, gate legality, or engine truth.
- Evaluators perform no runtime repairs and must not become a live enforcement layer.
- Dead-turn gameplay exclusion is derived from FEM/dead-turn source metadata, not reclassified from transport errors, fallback strings, or API status fields.
- Telemetry is observational only. Normalized bundles and evaluator observability events are read-side views, not runtime policy buses.
- No policy by JSON: adding telemetry/event fields must not create hidden orchestration, legality, repair, or scoring authority.
- Runner summaries and operator markdown mirror evaluator output for humans; they do not create new evaluator scores or release gates.

## Intentional Overlaps That Remain

- Playability, behavioral gauntlet, narrative authenticity, and scenario-spine evaluators may use similar text heuristics because their scopes differ: turn score, transcript-slice regression, telemetry-backed NA scoring, and whole-session health.
- Dead-turn validity appears in FEM, playability, narrative authenticity, behavioral gauntlet, and runner artifacts as read-only source-derived visibility.
- Scenario-spine transcript `meta` may copy FEM and other runtime seam metadata into artifacts while still not owning FEM semantics.
- Architecture and validation-layer audits both discuss ownership drift, but at different scopes.
- Runner summaries intentionally duplicate selected evaluator fields for operator readability.

## Allowed Future Work

- Fix concrete bugs found by tests, operator artifacts, or audit findings.
- Add focused regression tests when evidence shows a boundary drifted.
- Clarify docs or comments when existing wording becomes stale.
- Add narrowly scoped telemetry normalization only when it preserves observational-only semantics and does not create a new policy surface.
- Update audit heuristics when a stable fixture proves wording or module movement made an existing check stale.

## Do Not Casually Reopen

- Do not broaden evaluator scope into runtime enforcement, gate legality, repair orchestration, engine truth, or planner structure ownership.
- Do not merge playability and behavioral gauntlet scoring.
- Do not collapse scenario-spine transcript metadata into FEM correctness.
- Do not treat runner summaries, markdown artifacts, normalized telemetry bundles, or audit output as canonical scoring or release policy.
- Do not refactor runtime code, change evaluator scoring behavior, or reopen Blocks A-F without concrete bug evidence.

## Recommended Test Slice

For future evaluator-boundary changes, run:

```powershell
python -m pytest tests/test_evaluator_convergence_closeout.py -q
python -m pytest tests/test_dead_turn_evaluation_threading.py tests/test_playability_eval.py tests/test_behavioral_gauntlet_eval.py tests/test_scenario_spine_eval.py tests/test_final_emission_meta.py tests/test_architecture_audit_tool.py tests/test_validation_layer_audit_smoke.py -q
```

Use the project-local Python environment if `python` is not available on PATH. The important contract is the test set, not the shell alias.
