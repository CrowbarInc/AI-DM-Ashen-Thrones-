# Protected replay CI maintenance — 2026-10-18

Scope: repair convergence-checks.yml after checkpoint 4320bcd. No Product Realization cycle was started.

## Actual CI failure and report provenance

The verified failed run is https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-/actions/runs/39144457802 (job 117725356507).
The command `python -m pytest -m golden_replay -q` exited **2 during collection**:
`tests/test_api_upstream_preflight.py:8` imported undeclared `httpx`.
The installed OpenAI 3.35.1 dependency used `httpx2`; it no longer happened to supply `httpx` transitively.
No replay test executed in that Actions invocation. All following normal workflow checks were skipped.

The artifact downloaded through GitHub's API is byte-identical to
`git show 4320bcd:artifacts/golden_replay/replay_failure_report.md`.
Its June 28 timestamp and Windows Python 3.14 path identify a historical local failure-injection run,
not the October 18 Ubuntu execution. The old workflow uploaded that tracked report after the unrelated collection failure.

## Replay contract investigation

- `strict_social_accept` describes acceptance of a strict-social candidate, not fallback selection.
  `normalized_social_candidate` is an intentional source label when the accepted candidate differs after normalization/integrity processing.
  That branch returns `used_internal_fallback=False` and `fallback_kind='none'` in `game/social_exchange_emission.py`.
  A missing fallback family is therefore valid; requiring fallback metadata for every accepted turn is incorrect.
- A `final_emission_mutation` event alone records a changed string, not proof of semantic or speaker drift.
  The historical report's normalized-candidate source and zero fallback events are consistent with acceptance without fallback.
  The report does not establish a current speaker defect.
- The CO102 test is deliberately opt-in and deliberately asserts the wrong speaker (`merchant`) to populate diagnostic failure buffers.
  Its normal skip condition is unchanged. With the opt-in enabled, the repaired probe fails as intended on
  `selected_speaker_id`: expected `merchant`, actual `runner`, and writes a fresh isolated report.
- Current production host-authorized speech may bypass generation and the legacy final gate. Its accepted-response record is sealed.
  Golden replay now consumes that record and checks its digest, final-text equality, immutable flag, hard-validation result,
  and speaker identity. Legacy response-type telemetry is optional only when those replacement integrity checks are present.
  Existing legacy expectations still fail on missing gate telemetry. No gate results are fabricated.
- Local reproduction exposed a real additional integrity defect: explicit internal stage headings could be sealed as valid,
  stripped by sanitization, then restored by accepted-text integrity. Hard validation now rejects headings such as
  `Planner:` or `Validator:` before sealing. It preserves ordinary scaffold-related world prose and quoted in-world speech.
- The diagnostic `<object object at ...>` was the missing-path sentinel returned by the sanitizer-mode lookup.
  The projection now converts that sentinel to JSON `null` / Python `None` before constructing observations.
  No sentinel implementation or gameplay semantics were changed.

Classification: dependency/environment defect (D), stale artifact/reporting defect (E), outdated replay expectation (B),
projection/serialization defect (C), and a narrowly repaired pre-seal validation defect (A).
The supplied fallback-family report itself was not a current engine failure.

## Changes

- Declare the directly imported `httpx` dependency.
- Write CI reports to a runner-temporary directory. Upload fresh stdout and JUnit results alongside the report.
  Explicit `shell: bash` preserves pipeline failure through GitHub's `-o pipefail` invocation when tee captures output.
  Collection failures without protected assertion rows generate a current execution summary with exit status and command.
- Project and validate accepted delivery; normalize the missing sanitizer mode.
- Reject explicit internal stage labels before response sealing.
- Disambiguate 18 test function names across six duplicate-name groups without changing any test body or assertion.
  Their exact bodies were compared with checkpoint 4320bcd. No allowlist exceptions were added.
- Teach the validation-layer audit to follow locally imported final-emission modules and inspect actual call sites.
  It still detects a removed final-text recheck, now covered by a synthetic split-module regression.
  Recognize `observability_attribution_read`, the existing read-only FEM facade, as a legal evaluator import.
- Add regression coverage for delivery tampering, speaker mismatch, failed hard validation, missing legacy telemetry,
  JSON-safe missing sanitizer mode, collection-failure report freshness, and internal-heading validation.

## Reproduction and validation

The host's bare Python launcher had no installed interpreter. Tests used an isolated Python 3.12 environment built from
the bundled runtime, with a fresh `pip install -r requirements.txt`. Initial investigation also used the existing local packages.
Windows sandbox atomic-replace permissions caused one exploratory replay rerun to fail during setup;
final checks used temporary storage outside that sandbox restriction. Live model calls remained blocked by the existing test guard.

Requested initial commands:

- `python -m pytest tests/test_co102_live_protected_replay_pipeline.py::test_co102_live_protected_replay_records_session_failure_artifacts -q --tb=short`: **1 skipped**, as designed without opt-in.
- `python -m pytest -m golden_replay -q --tb=short`: **5 failed, 1 passed, 1 skipped** before repair.
- Same golden replay lane after repair: **6 passed, 1 skipped**. All protected scenarios remain enabled.
- CO102 with `ASHEN_RUN_CO102_LIVE_VALIDATION=1`: **1 intentional failure**, on the injected wrong-speaker expectation; fresh report confirmed.
- Final repair-specific regression selection: **31 passed**.
- Broader related selection: **221 passed, 1 failed**; strict-social/speaker/projection selection: **194 passed, 2 failed**.
  The three failures below reproduce identically on an untouched export of 4320bcd. They were not disabled or rewritten:
  - `tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid`
    expects generated stew-price ignorance; current host instead selects the authored stew/rumor line.
  - `tests/test_bx_speaker_identity_end_to_end_parity.py::test_case_a_role_alias_guard_routes_to_guard_captain`
  - `tests/test_bx_speaker_identity_end_to_end_parity.py::test_case_b_canonical_id_guard_captain_remains_canonical`
    Both existing speaker-parity probes report `speaker_contract.mismatch_present`.
- A final combined changed-unit-suite run had **50 passed, 1 failed**, with only that same baseline raw-chat failure.

### Every convergence-workflow command

Commands below use `python` for the isolated Python executable. Pytest checks additionally wrote JUnit files and used
separate temporary directories; these output options do not change test selection. The workflow's protected lane also
captures stdout through tee and writes JUnit under runner.temp.

- `python -m pytest tests/test_evaluator_convergence_closeout.py -q` — PASS (1 tests).
- `python -m pytest tests/test_dead_turn_evaluation_threading.py tests/test_playability_eval.py tests/test_behavioral_gauntlet_eval.py tests/test_scenario_spine_eval.py tests/test_final_emission_meta.py tests/test_architecture_audit_tool.py tests/test_validation_layer_audit_smoke.py -q` — PASS (207 tests).
- `python -m pytest tests/test_final_emission_boundary_contract.py tests/test_final_emission_boundary_convergence.py -q` — PASS (113 tests).
- `python -m pytest tests/test_gate_convergence_closeout.py -q` — PASS (22 tests).
- `python -m pytest tests/test_validation_coverage_audit.py -q` — PASS (5 tests).
- `python -m pytest tests/test_ownership_registry.py tests/test_inventory_governance.py tests/test_gate_boundary_governance.py tests/test_replay_boundary_governance.py tests/test_ownership_write_path_governance.py -q` — Initially failed; maintenance correction applied; final rerun recorded below.
- `python scripts/check_split_owner_acceptance_matrix.py` — Exit 0 (PASS).
- `python tools/test_audit.py --check` — Initially failed; maintenance correction applied; final rerun recorded below.
- `python tools/refresh_protected_replay_manifest.py --check` — Exit 0 (PASS).
- `python tools/validation_layer_audit.py --strict` — Initially failed; maintenance correction applied; final rerun recorded below.
- `python tools/final_emission_ownership_audit.py --strict` — Exit 0 (PASS).
- `python tools/validation_coverage_audit.py --strict` — Exit 0 (PASS).
- `python tools/architecture_audit.py --print-summary` — Exit 0 (informational/advisory).
- `python tools/realization_layer_audit.py` — Exit 0 (informational/advisory).
- `python tools/realization_provenance_audit.py` — Exit 0 (informational/advisory).
- `python tools/c1_narration_seam_audit.py` — Exit 0 (informational/advisory).
- `python tools/ui_mode_separation_audit.py` — Exit 0 (informational/advisory).

Advisory architecture/realization reports still contain pre-existing findings; their commands exit 0 as designed.
Generated reports, local saves, historical review packages, caches, and temporary validation files are excluded from the maintenance commit.
Detailed local command outputs, JUnit records and baseline comparisons are retained under
`development/tmp/github_checkpoint/` (ignored local diagnostics).

Final governance rerun: **59 passed**. The strict validation-layer audit now reports **0 findings**.
`python tools/test_audit.py --check` passes: 8,990 tests derived, 66 registry-owned files / 597 total.
The test-inventory regeneration changed no semantic inventory content after the duplicate names were repaired.
All blocking convergence-workflow test selections and audit commands pass locally after these corrections.
GitHub Actions and push verification are reported separately after the maintenance commit.

### Related owner-suite commands

- `python -m pytest tests/test_api_upstream_preflight.py tests/test_golden_replay_projection.py tests/test_failure_dashboard_orchestration.py tests/test_failure_dashboard_report.py tests/test_golden_replay_fallback_sanitizer_projection.py tests/test_golden_replay_fallback_acceptance_matrix.py tests/test_pr_br_continuation18_immutable_boundary.py tests/test_pr_eg_r4_r1_delivery_integrity.py tests/test_pr_eg_r2c_speech_adoption.py tests/test_final_emission_gate.py tests/test_strict_social_emergency_fallback_dialogue.py tests/test_referential_clarity_strict_social_local_repair.py -q --tb=short` — 221 passed, 1 baseline failure.
- `python -m pytest tests/test_social_exchange_emission.py tests/test_speaker_contract_enforcement.py tests/test_bx_speaker_identity_end_to_end_parity.py tests/test_strict_social_answer_pressure_cashout.py tests/test_golden_replay_projection_modules.py tests/test_golden_replay_projection_presence_integration.py -q --tb=short` — 194 passed, 2 baseline failures.
