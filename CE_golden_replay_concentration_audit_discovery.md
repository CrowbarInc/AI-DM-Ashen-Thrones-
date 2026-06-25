# CE — Golden Replay Concentration Audit Discovery

## Executive Summary

Replay maintenance was historically highly concentrated in `tests/test_golden_replay.py`, which has 38 commits in the available history and 32 touches in the 30 days ending 2026-06-24. That historical count is still the largest in the replay maintenance surface. However, commit `b7c5b2c` on 2026-06-17 decomposed the file into focused owner modules, and the current file is only a 19-line redirect stub with one test.

Current executable scenario ownership is therefore substantially more distributed than the history total alone suggests. The six acceptance-blocking scenarios live in `tests/test_golden_replay_structural_invariants.py`; long-session, direct-seam, scenario-spine, projection, fallback-projection, helper-contract, and protected-report bridge responsibilities have separate test modules.

Concentration has not disappeared. It has migrated into shared infrastructure:

- `tests/helpers/golden_replay.py`: 25 commits, 1,863 lines, 68 top-level definitions, and approximately 45 importing files.
- `tests/helpers/failure_dashboard_report.py`: 21 commits, 3,145 lines, 82 top-level definitions, and approximately 21 importing files.
- `docs/testing/protected_replay_manifest.md`: 17 commits; generated protected-field bookkeeping is coupled to the acceptance projection registry.
- `tests/helpers/golden_replay_projection.py`: 15 commits, 1,532 lines, 76 top-level definitions, and approximately 17 importing files.
- `game/final_emission_replay_projection.py`: 11 commits, 781 lines, 25 top-level definitions, and approximately 23 importing files.

The protected scenario registry itself is not currently a high-churn file: `tests/helpers/protected_replay_registry.py` has two commits. Its bottleneck risk comes from authority and fan-out rather than touch count: it mechanically controls the six-case protected corpus, four-case BX speaker corpus, marker collection parity, trend windows, semantic-mutation probes, and several closeout checks.

Overall assessment: **historically centralized, currently partially distributed, with residual concentration in broad helpers, projection schemas, diagnostic/report generation, and manifest synchronization**.

### Method and Scope

- Repository history is available and is not shallow.
- Audit date: 2026-06-24.
- Windows are inclusive from 2026-05-25 (30 days), 2026-04-25 (60 days), and 2026-03-26 (90 days).
- The measured maintenance set contains 110 tracked files and 55 commits. It includes replay tests, replay/governance registries, replay helpers, diagnostic helpers, canonical top-level replay artifacts, the long-session fixture, manifest/tooling files, and the runtime read-side replay projection.
- Generated per-run storage under `artifacts/golden_replay/**/_storage/**`, trend-window run snapshots, and the very large `artifacts/bv3b_replay_refresh/**` / `artifacts/bv3f_replay_refresh/**` runtime captures were inventoried as replay assets but excluded from per-file concentration ranking. Counting every generated scene/state snapshot would measure corpus volume rather than maintenance ownership.
- All 55 measured commits are authored by `CrowBarInc`; author diversity cannot be assessed beyond that single recorded identity.

## Replay File Inventory

| Category | File | Purpose | Notes |
|---|---|---|---|
| Primary golden replay tests | `tests/test_golden_replay.py` | Historical suite entry point | Now a 19-line redirect stub after `b7c5b2c`; historical hotspot only. |
| Primary golden replay tests | `tests/test_golden_replay_structural_invariants.py` | Six protected short end-to-end scenarios | Sole `pytest.mark.golden_replay` protected corpus owner. |
| Primary golden replay tests | `tests/test_golden_replay_long_session.py` | 25-turn stability, resume, and diagnostic sessions | Supporting/diagnostic, not protected marker authority. |
| Primary golden replay tests | `tests/test_golden_replay_direct_seam.py` | Direct final-emission/gate observation | Supporting coverage. |
| Primary golden replay tests | `tests/test_golden_replay_scenario_spine.py` | Three-branch scenario-spine smoke | Supporting coverage. |
| Primary golden replay tests | `tests/test_golden_replay_projection.py` | Acceptance projection, protected-field registry, manifest parity | 810 lines and 33 definitions; current concentrated projection contract suite. |
| Primary golden replay tests | `tests/test_golden_replay_fallback_projection.py` | Fallback, ownership, sanitizer, lineage, and split-owner projection | 1,145 lines and 33 definitions; largest current replay test module. |
| Primary golden replay tests | `tests/test_golden_replay_helper_contracts.py` | Expectation builders and renderer contracts | Unit-level helper ownership. |
| Primary golden replay tests | `tests/test_golden_replay_protected_bridge.py` | Protected assertion-to-report bridge | One narrow integration test. |
| Primary golden replay tests | `tests/test_golden_replay_trend.py` | Two-run drift/trend window behavior | Advisory/reporting lane. |
| Primary golden replay tests | `tests/test_bx_speaker_identity_golden_replay.py` | Protected BX speaker-parity cases | Separate `bx_speaker_parity` protected corpus. |
| Protected replay registry | `tests/helpers/protected_replay_registry.py` | Scenario registry and corpus filters | Mechanical scenario authority; 16 entries: six BW protected, four BX protected, six supporting. |
| Protected replay registry | `tests/test_protected_replay_registry.py` | Registry validation and marker collection parity | Executes pytest collection subprocesses. |
| Protected replay registry | `docs/testing/protected_replay_manifest.md` | Human/governance acceptance authority | Includes generated 41-field protected observation table. |
| Protected replay registry | `tools/refresh_protected_replay_manifest.py` | Checks/writes generated manifest field section | Consumes acceptance projection registry and opening metadata parity checks. |
| Protected replay registry | `tests/replay_governance_registry.py` | Drift bucket → governance decision records | Separate governance registry, not scenario corpus membership. |
| Protected replay registry | `tests/replay_governance_{contract,approval_contract,traceability_contract}.py` | Governance contracts | Static test-side policy surfaces. |
| Protected replay registry | `docs/testing/replay_governance_{registry,contract,authority,approval_contract,traceability_contract}.md` | Governance documentation | Promoted together in commit `ef5fc34f`. |
| Replay helpers/utilities | `tests/helpers/golden_replay.py` | Orchestration, assertions, summaries, drift comparison, profiles, report bridge | Broadest reusable replay hub. |
| Replay helpers/utilities | `tests/helpers/golden_replay_api.py` | Narrow public facade over broad helper | Eight measured importers; implementation still resides in the broad module. |
| Replay helpers/utilities | `tests/helpers/golden_replay_fixtures.py` | Deterministic chat stubs, seed worlds, payload factories | 404 lines; relatively low history churn. |
| Replay helpers/utilities | `tests/helpers/golden_replay_profiles.py` | Long-session profile definitions | Focused supporting helper. |
| Replay helpers/utilities | `tests/helpers/golden_replay_trend.py` | Protected corpus execution and trend-window comparison | Consumes scenario registry and replay fixtures. |
| Replay helpers/utilities | `tests/helpers/replay_observed_row_fixtures.py` | Synthetic observed rows | Shared by projection and diagnostic tests. |
| Replay helpers/utilities | `tests/helpers/replay_drift_{taxonomy,rows,longitudinal,hotspots,trends,risk,reports}.py` | Drift classification and aggregation family | Distributed files, but coordinated by dashboard/reporting code. |
| Replay helpers/utilities | `tests/helpers/replay_bug_recurrence.py` | Bug-class recurrence data processing | Feeds recurrence diagnostics. |
| Replay helpers/utilities | `tests/helpers/protected_replay_observation_corpus.py` | Protected failure observation corpus | Used by recurrence history population. |
| Replay helpers/utilities | `tests/helpers/protected_replay_trend_movement.py` | Trend movement calculations | Protected replay trend support. |
| Replay diagnostics/reporting | `tests/helpers/failure_dashboard_report.py` | Dashboard rows; protected failure, drift, longitudinal, hotspot, risk, recurrence, and stability artifact rendering/writing | 3,145 lines; clearest current diagnostic bottleneck. |
| Replay diagnostics/reporting | `tests/helpers/failure_classifier.py` | Failure classification and owner routing | 13 commits; shared by replay and non-replay failure tests. |
| Replay diagnostics/reporting | `game/final_emission_replay_projection.py` | Runtime read-side FEM lineage projection | Diagnostic/read-side production module; explicitly not acceptance schema authority. |
| Replay diagnostics/reporting | `tests/test_failure_dashboard_report.py` | Diagnostic renderer tests | Direct owner for report formatting. |
| Replay diagnostics/reporting | `tests/test_failure_dashboard_controlled_failures.py` | Opt-in dashboard probes | Probes are skipped unless explicitly requested. |
| Replay diagnostics/reporting | `tools/run_protected_replay_trend.py` | Trend-window CLI | Advisory/report generation. |
| Replay diagnostics/reporting | `tools/expand_protected_replay_observations.py` | Expands failure corpus observations | Used by recurrence population. |
| Replay diagnostics/reporting | `artifacts/golden_replay/replay_failure_report.md` | Canonical protected failure report artifact | Generated diagnostic output. |
| Replay diagnostics/reporting | `artifacts/golden_replay/owner_drift_{hotspots,longitudinal,risk,trends}.{json,md}` | Drift aggregation artifacts | Frequently updated together, creating multi-file churn. |
| Replay diagnostics/reporting | `artifacts/golden_replay/bug_recurrence_{event_log,history,session_diagnostic_event_log}.*` | Recurrence history and event artifacts | Frequently regenerated as a family. |
| Replay fixtures/corpus/assets | `data/validation/scenario_spines/frontier_gate_long_session.json` | Authoritative long-session scenario-spine fixture | Consumed by `golden_replay.py`. |
| Replay fixtures/corpus/assets | `artifacts/golden_replay/trend_window/**` | BW run envelopes, comparisons, histories, storage snapshots | Generated trend corpus; excluded from per-file concentration ranking. |
| Replay fixtures/corpus/assets | `artifacts/golden_replay/trend_window_2/**` | BZ second-window runs, comparisons, movement reports, storage snapshots | Generated trend corpus; excluded from ranking. |
| Replay fixtures/corpus/assets | `artifacts/bv3b_replay_refresh/**` | Replay corpus refresh captures | Thousands of generated runtime files; asset volume, not a useful ownership unit. |
| Replay fixtures/corpus/assets | `artifacts/bv3f_replay_refresh/**` | Later replay corpus refresh captures | Same exclusion rationale. |
| Docs/manifests | `docs/testing/protected_replay_manifest.md` | Current protected acceptance and schema documentation | High-churn governance/documentation file. |
| Docs/manifests | `docs/audits/discovery/cycle_au_golden_replay_ownership_compression_recon.md` | Historical ownership/concentration recon | Documents the pre-decomposition 3,100-line suite. |
| Docs/manifests | `audits/cycle_au_golden_replay_owner_mapping.md` | Assertion-family owner map | Useful follow-up routing evidence. |
| Docs/manifests | `docs/audits/closeouts/BW_protected_replay_trend_window_closeout.md` | Protected corpus/trend closeout | Documents six-scenario BW authority. |
| Docs/manifests | `docs/audits/closeouts/BX_speaker_identity_end_to_end_parity_closeout.md` | BX corpus closeout | Documents four protected speaker-parity scenarios. |
| Docs/manifests | `docs/audits/CB_feature_boundary_guardrails.md` and `docs/audits/CB_feature_boundary_registry.json` | Change-boundary governance | Treat replay surfaces as a high-risk governed boundary. |

## Touch Concentration

The table reports the top maintenance files plus current focal owners. Because the repository's measured replay history starts within the last 90 days, most 60-day and 90-day values equal total touches.

| File | Total Touches | 30d | 60d | 90d | Notes |
|---|---:|---:|---:|---:|---|
| `tests/test_golden_replay.py` | 38 | 32 | 38 | 38 | Historical monolith; no longer current implementation hub after 2026-06-17. |
| `tests/helpers/golden_replay.py` | 25 | 21 | 25 | 25 | Current orchestration/assertion/summary hub. |
| `tests/helpers/failure_dashboard_report.py` | 21 | 18 | 21 | 21 | Current diagnostics/reporting hub. |
| `docs/testing/protected_replay_manifest.md` | 17 | 17 | 17 | 17 | Generated schema section plus governance text. |
| `tests/helpers/golden_replay_projection.py` | 15 | 15 | 15 | 15 | Acceptance schema/projection authority. |
| `tests/helpers/failure_classifier.py` | 13 | 9 | 13 | 13 | Cross-cutting failure/owner classification. |
| `game/final_emission_replay_projection.py` | 11 | 11 | 11 | 11 | Runtime diagnostic/read-side projection. |
| `tests/test_golden_replay_fallback_projection.py` | 8 | 8 | 8 | 8 | Largest current replay test; broad fallback ownership matrix. |
| `tests/test_golden_replay_projection.py` | 7 | 7 | 7 | 7 | Projection, registry, and manifest locks. |
| `tools/refresh_protected_replay_manifest.py` | 7 | 7 | 7 | 7 | Registry/manifest synchronization tool. |
| `artifacts/golden_replay/bug_recurrence_history.md` | 6 | 6 | 6 | 6 | Generated output churn. |
| `artifacts/golden_replay/bug_recurrence_history.json` | 5 | 5 | 5 | 5 | Generated output churn. |
| `artifacts/golden_replay/owner_drift_hotspots.json` | 5 | 5 | 5 | 5 | Usually updated with companion Markdown/risk/trend files. |
| `artifacts/golden_replay/owner_drift_hotspots.md` | 5 | 5 | 5 | 5 | Generated output churn. |
| `artifacts/golden_replay/owner_drift_risk.json` | 5 | 5 | 5 | 5 | Generated output churn. |
| `artifacts/golden_replay/owner_drift_risk.md` | 5 | 5 | 5 | 5 | Generated output churn. |
| `tests/helpers/replay_drift_taxonomy.py` | 5 | 5 | 5 | 5 | Taxonomy helper, lower churn than central report assembler. |
| `tests/test_golden_replay_helper_contracts.py` | 5 | 5 | 5 | 5 | Focused post-split helper tests. |
| `tests/helpers/golden_replay_trend.py` | 3 | 3 | 3 | 3 | Protected corpus execution/trend hub. |
| `tests/helpers/golden_replay_api.py` | 2 | 2 | 2 | 2 | Stable facade; broad implementation remains behind it. |
| `tests/helpers/protected_replay_registry.py` | 2 | 2 | 2 | 2 | Low touch count but high authority/fan-out. |
| `tests/test_golden_replay_{direct_seam,protected_bridge,structural_invariants}.py` | 2 each | 2 | 2 | 2 | Focused files introduced during decomposition and later adjusted. |
| `tests/helpers/golden_replay_{fixtures,profiles}.py` | 1 each | 1 | 1 | 1 | Stable focused support. |
| `tests/test_golden_replay_{long_session,scenario_spine,trend}.py` | 1 each | 1 | 1 | 1 | Focused owners with little subsequent churn. |

### Is `tests/test_golden_replay.py` Disproportionately Touched?

Historically, yes. Its 38 touches exceed the next replay file (`tests/helpers/golden_replay.py`, 25) by 52%, and exceed the current focused scenario modules by an order of magnitude.

Currently, no. The final touch to the stub is the 2026-06-17 decomposition commit. Replay work after that date touches focused test modules, helpers, registry/manifest files, and diagnostics instead. The historical total should therefore be treated as evidence that drove decomposition, not evidence that the stub remains the active bottleneck.

The stronger current concentration signal is the combination of file size, fan-in, and touch count in `golden_replay.py`, `golden_replay_projection.py`, and `failure_dashboard_report.py`.

## Top Replay-Touch Commits

| Commit | Date | Author | Replay Files Touched | Summary | Classification |
|---|---|---|---:|---|---|
| `7651237b` | 2026-06-21 | CrowBarInc | 30 | Maintenance economics closeout updated many generated reports plus projection/tests/tools. | Diagnostic/report regeneration plus projection maintenance |
| `d65a5350` | 2026-06-19 | CrowBarInc | 25 | Added fallback incidence/economics/risk/remediation artifact family. | Diagnostic-only change / generated output |
| `6210a5d6` | 2026-06-06 | CrowBarInc | 23 | Added drift taxonomy, longitudinal, hotspot, trend, and risk helpers/tests/artifacts. | Diagnostic-only change |
| `d7895ba0` | 2026-06-22 | CrowBarInc | 17 | Added speaker-observation behavior, BX protected cases, registry entries, projection, and regenerated recurrence outputs. | Real behavior change plus registry bookkeeping |
| `1603880a` | 2026-06-12 | CrowBarInc | 16 | Redistributed hotspot tests and helpers while refreshing diagnostic artifacts. | Helper/test ownership refactor |
| `3f5ee0c3` | 2026-06-20 | CrowBarInc | 14 | Populated recurrence history/event artifacts and protected bridge support. | Diagnostic-only / expected artifact update |
| `ca830c20` | 2026-06-10 | CrowBarInc | 14 | Compressed replay surface behind API/helpers and focused tests. | Helper refactor |
| `ef5fc34f` | 2026-06-07 | CrowBarInc | 14 | Added replay governance registries, contracts, tests, and docs. | Ownership/governance update |
| `dcf8d0a3` | 2026-06-06 | CrowBarInc | 13 | Promoted longitudinal stability reporting and artifacts. | Diagnostic/governance update |
| `06f81c62` | 2026-06-10 | CrowBarInc | 12 | Consolidated assertion families across golden replay, drift, and governance tests. | Helper/test refactor |
| `d067e519` | 2026-06-10 | CrowBarInc | 11 | Simplified replay harness and drift helper family. | Helper refactor |
| `fc48d7ab` | 2026-06-11 | CrowBarInc | 10 | Simplified assertions and refreshed drift/recurrence artifacts. | Test maintenance plus expected artifact churn |

Additional representative commits:

- `b7c5b2c` (2026-06-17): split 803 lines out of `tests/test_golden_replay.py` into five focused modules; helper/test ownership refactor.
- `b086b75` (2026-05-25): added runtime lineage instrumentation across production, replay, dashboard, and validation surfaces; real behavior/observability change.
- `98bc059` (2026-05-11): introduced failure classification/dashboard infrastructure and coupled it to golden replay; diagnostic foundation.
- `ac1ba90` (2026-05-11): introduced the scenario-spine baseline suite; real replay coverage change.

## Edit Classification

The counts below are estimates across the 55 measured commits. Several commits deliberately combine behavior, tests, governance, and generated artifacts, so categories are not mutually exclusive.

| Category | Count/Estimate | Example Commits | Interpretation |
|---|---:|---|---|
| Real replay behavior or observation change | ≈10 | `ac1ba90`, `b086b75`, `d7895ba`, `0e5fe3a` | Adds/changes exercised behavior, runtime observation, protected speaker parity, or mutation attribution. |
| Golden output / expected fixture or artifact update | ≈12 | `d65a535`, `7651237`, `3f5ee0c`, `fc48d7a` | Churn is dominated by generated JSON/Markdown diagnostics rather than hand-authored expected prose snapshots. |
| Registry bookkeeping | ≈6 | `a31cb35`, `d7895ba`, `97b1836`, `7651237` | Scenario membership, protected field paths, marker parity, or manifest synchronization. |
| Diagnostic-only change | ≈15 | `98bc059`, `6210a5d`, `3f5ee0c`, `d65a535` | Adds classifiers, dashboards, drift, recurrence, risk, or trend reports without changing acceptance semantics. |
| Helper refactor | ≈14 | `b7c5b2c`, `ca830c2`, `d067e51`, `06f81c6`, `e9263f1` | Splits tests, introduces facade/helper boundaries, or redistributes assertion families. |
| Ownership/governance update | ≈10 | `ef5fc34`, `2619bb5`, `7ed7a8b`, `f7e73fb` | Declares authority, protection status, approval rules, and owner boundaries. |
| Test stabilization / flake fix | 0–2 | No unambiguous dedicated flake commit found | Determinism and stable-seed work appears embedded in larger replay/governance blocks, not isolated as flake fixes. |
| Unrelated drive-by edit | 0 clear cases | None identified | Replay files were generally touched by replay-specific or adjacent ownership work. |

## `tests/test_golden_replay.py` Responsibility Map

### Current Responsibilities

The file currently owns only:

- A historical redirect/documentation note naming the focused owner files.
- A governance boundary comment.
- One smoke assertion that its module docstring exists.

It no longer executes replay orchestration, registry validation, diagnostics, fixture assertions, protected replay enforcement, projection contracts, or long-session coverage.

### Historical Responsibilities

Before `b7c5b2c`, the file combined:

- Protected end-to-end replay scenarios.
- Long-session replay and resume persistence.
- Scenario-spine smoke orchestration.
- Projection adapter and protected-field registry locks.
- Manifest parity.
- Fallback/owner/sanitizer/lineage projection.
- Golden assertion helper behavior.
- Protected failure-report recording.
- Rerun drift scorecards and report rendering.
- Stability summaries and owner-drift classification.

The earlier Cycle AU recon measured approximately 3,100 lines and identified it as the current late-cycle replay hotspot. Successive AU/AX/BB/BC/BG/BI/BL/BM commits then moved those responsibilities out.

### Current Focused Owners

| Responsibility | Current Owner |
|---|---|
| Six protected scenarios and marker | `tests/test_golden_replay_structural_invariants.py` |
| Long-session replay/profile consumption | `tests/test_golden_replay_long_session.py` |
| Direct gate/final-emission seam | `tests/test_golden_replay_direct_seam.py` |
| Scenario-spine smoke | `tests/test_golden_replay_scenario_spine.py` |
| Acceptance projection and manifest locks | `tests/test_golden_replay_projection.py` |
| Fallback/owner/lineage projection matrix | `tests/test_golden_replay_fallback_projection.py` |
| Helper contracts | `tests/test_golden_replay_helper_contracts.py` |
| Protected assertion/report bridge | `tests/test_golden_replay_protected_bridge.py` |
| Trend-window behavior | `tests/test_golden_replay_trend.py` |

### Imports and Dependencies

The stub has no module-level imports. The focused files depend principally on:

- `tests.helpers.golden_replay` and `tests.helpers.golden_replay_api`.
- `tests.helpers.golden_replay_fixtures` and `golden_replay_profiles`.
- `tests.helpers.golden_replay_projection`.
- `tests.helpers.failure_dashboard_report`.
- `game.api`, `game.storage`, `game.models`, scenario-spine modules, and final-emission projection/read-view modules.

### Suspected Overload Points

Smaller tests already own most former responsibilities. Remaining overload is visible in:

- `tests/test_golden_replay_fallback_projection.py` at 1,145 lines, spanning opening, sealed, strict-social, visibility, sanitizer, upstream-fast, classifier alignment, long-session summaries, and acceptance matrices.
- `tests/test_golden_replay_projection.py` at 810 lines, mixing adapter behavior, registry parity, manifest tooling, extraction coverage, sanitizer projection, speaker parity, and closeout governance.
- Broad shared helpers that allow focused tests to remain small but centralize many unrelated changes.

## Protected Replay Registry Analysis

### Location

There are two distinct registry concepts:

1. Scenario/corpus authority: `tests/helpers/protected_replay_registry.py`.
2. Drift governance decisions: `tests/replay_governance_registry.py`.

The protected observation field schema is a third registry-like authority in `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS`, rendered into `docs/testing/protected_replay_manifest.md`.

### Scenario Registry Schema

`ProtectedReplayScenarioEntry` is a frozen dataclass with:

- `scenario_id`
- `test_module`
- `test_name`
- `protection_status` (`PROTECTED`, `SUPPORTING`, `ADVISORY`, `DEPRECATED`)
- `bw_dimensions`
- `sort_key`
- `category`
- derived `test_node_id`

The registry is a sorted immutable tuple. Current composition:

- Six `PROTECTED` `END_TO_END_PROTECTED` scenarios used by the BW/BZ corpus.
- Four `PROTECTED` `BX_SPEAKER_PARITY_PROTECTED` scenarios.
- Six `SUPPORTING` scenarios across direct seam, long session, and scenario spine.

Validation checks uniqueness, stable order, test-node IDs, dimensions, and fixed protected corpus sizes.

### Consumers

Direct consumers include:

- `tests/test_protected_replay_registry.py`
- `tests/helpers/golden_replay_trend.py`
- `tests/test_bw_protected_replay_trend_window_closeout.py`
- `tests/test_bz_protected_replay_trend_window_2.py`
- `tests/test_bz_protected_replay_trend_window_2_closeout.py`
- `tests/test_by2_protected_semantic_mutation_measurement.py`
- `tests/test_by3_strict_social_semantic_mutation.py`
- `tests/helpers/protected_semantic_mutation_measurement.py`
- `tools/run_protected_replay_trend.py`

The registry also indirectly governs marker collection and trend-window corpus identity.

### Change Pattern

- Two commits touch the scenario registry: `a31cb35` (BW protected trend window) and `d7895ba` (BX speaker parity).
- Those changes are mostly deliberate corpus promotion/bookkeeping tied to new protected capabilities, not routine edits for every replay behavior change.
- The scenario registry therefore has low observed bookkeeping frequency.
- The protected field registry/manifest pair is more active: projection authority has 15 touches, the manifest 17, and the refresh tool seven.

### Bottleneck Risk

- Scenario registry risk: **medium authority risk, low churn risk**. Many consumers depend on stable IDs/order/counts, but ordinary supporting replay changes do not necessarily edit it.
- Protected observation registry risk: **high maintenance risk**. A protected field change can require projection logic, registry metadata, manifest regeneration, parity tests, classifier overlap, and acceptance review.
- Governance registry risk: **medium**. It is centralized policy by design but is separate from replay execution.

## Replay Helpers and Diagnostics Analysis

### Main Helper Surfaces

| File | Main Public Surface | Consumers/Coupling |
|---|---|---|
| `tests/helpers/golden_replay.py` | `run_golden_replay`, expectation builders/assertions, drift comparison/classification, summaries, scorecards, Markdown rendering | High fan-in; imports game API/storage, transcript runner, projection, classifier, drift taxonomy, and dashboard recording. |
| `tests/helpers/golden_replay_api.py` | Narrow re-export facade plus `observed_turn_from_payload` | Improves import stability, but does not reduce implementation concentration. |
| `tests/helpers/golden_replay_projection.py` | 41-field protected schema, extraction registry, `project_turn_observation`, drift buckets, fallback-family precedence, manifest rendering/parity | High coupling to runtime read-side projection, sanitizer, speaker observation, transcript/debug trace helpers, manifest tooling, and classifier evidence. |
| `tests/helpers/golden_replay_fixtures.py` | Deterministic GPT stubs, intent suppression, world/session seeds, synthetic payload projection | Reusable and comparatively focused. |
| `tests/helpers/golden_replay_profiles.py` | Long-session profile constants/data | Focused and reusable. |
| `tests/helpers/golden_replay_trend.py` | Execute protected corpus; compare/write trend windows; parity and guardrails | Coupled to scenario registry, fixtures, and generated artifacts. |
| `game/final_emission_replay_projection.py` | `build_fem_runtime_lineage_events`, FEM normalization/readers, sealed/visibility/source/mutation projections | Reusable read-side runtime diagnostics; explicitly separated from acceptance authority. |

### Main Diagnostic Surfaces

| File | Main Public Surface | Invocation Mode |
|---|---|---|
| `tests/helpers/failure_dashboard_report.py` | Build/classify rows; record rows/events; render/write dashboard, protected failure, drift, stability, recurrence, hotspot, trend, risk, and lifecycle artifacts | Mostly opt-in artifact writing at pytest session end; protected assertion failures can be recorded during test flow. |
| `tests/helpers/failure_classifier.py` | Failure category/severity/owner classification and validation | Used in normal test assertion/projection paths and diagnostics. |
| `tests/helpers/replay_drift_*.py` | Taxonomy, rows, longitudinal, hotspot, trend, risk, report aggregation | Advisory/report paths and focused tests. |
| `tests/conftest.py` | CLI/env switches and `pytest_sessionfinish` artifact writing | Artifact generation only when requested by flags/env; controlled failure probes are opt-in. |

### Failure-Only vs Normal Flow

- Protected assertion evaluation is part of normal replay test flow.
- `assert_protected_golden_turn_observation` records protected failure details when an assertion fails.
- Generic failure-dashboard rows and runtime-lineage events are recorded only when `ASHEN_WRITE_FAILURE_DASHBOARD` or the corresponding pytest option is enabled.
- Dashboard, rerun drift, and long-session scorecard files are written during `pytest_sessionfinish`, gated by explicit flags/environment variables.
- Runtime lineage projection can run during ordinary replay observation, but its report/artifact persistence is diagnostic and opt-in.
- Protected replay trend execution is an explicit tool/test lane, not hidden in every normal replay test.

### Test Coverage

Coverage is broad and distributed across:

- `tests/test_golden_replay_projection.py`
- `tests/test_golden_replay_fallback_projection.py`
- `tests/test_golden_replay_helper_contracts.py`
- `tests/test_golden_replay_protected_bridge.py`
- `tests/test_failure_dashboard_report.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_failure_classifier.py`
- `tests/test_replay_drift_{taxonomy,longitudinal,hotspots,trends,risk}.py`
- `tests/test_final_emission_meta.py`
- `tests/test_runtime_lineage_telemetry.py`
- `tests/test_protected_replay_registry.py`

The concern is not absent tests; it is that broad helpers and report assemblers coordinate many tested domains.

## Ownership Distribution Assessment

### High Fan-In

Approximate import counts from code search:

| File | Approximate Importing Files | Assessment |
|---|---:|---|
| `tests/helpers/golden_replay.py` | 45 | Primary replay helper bottleneck. |
| `game/final_emission_replay_projection.py` | 23 | Broad read-side lineage dependency. |
| `tests/helpers/failure_dashboard_report.py` | 21 | Diagnostic/reporting bottleneck. |
| `tests/helpers/golden_replay_projection.py` | 17 | Acceptance schema/projection bottleneck. |
| `tests/helpers/golden_replay_api.py` | 8 | Useful facade, but less adopted than direct broad-helper imports. |
| `tests/helpers/protected_replay_registry.py` | 6 direct importers | Moderate direct fan-in; greater indirect authority via trend helpers/tools. |
| `tests/replay_governance_registry.py` | 4 | Narrow governance authority. |

Existing repository fan-in documentation independently reports the replay/governance boundary as 44 modules with aggregate fan-in 200 and fan-out 150, reinforcing that this is a highly connected maintenance domain.

### High Fan-Out

- `tests/helpers/golden_replay.py` imports runtime chat/storage/models, scenario-spine evaluation, transcript storage, failure classification, drift taxonomy, acceptance projection, dashboard recording, and lineage reporting.
- `tests/helpers/failure_dashboard_report.py` imports classification sync, acceptance field paths, runtime lineage reporting, recurrence helpers, and replay drift reports; it renders many artifact families.
- `tests/helpers/golden_replay_projection.py` reaches into runtime final-emission projection, final speaker observation, sanitizer checks, provenance constants, lineage telemetry, transcript/debug trace helpers, and manifest generation.
- `tests/test_golden_replay_fallback_projection.py` spans multiple runtime ownership views and acceptance/classifier contracts.

### Likely Bottleneck Files

1. `tests/helpers/golden_replay.py`
2. `tests/helpers/failure_dashboard_report.py`
3. `tests/helpers/golden_replay_projection.py`
4. `docs/testing/protected_replay_manifest.md` plus `tools/refresh_protected_replay_manifest.py`
5. `tests/test_golden_replay_fallback_projection.py`
6. `game/final_emission_replay_projection.py`
7. `tests/helpers/protected_replay_registry.py` for corpus-authority changes

### Direct Answers

- **Which replay assets absorb the majority of edits?** Historically `tests/test_golden_replay.py`; currently the broad helper, dashboard/report helper, acceptance projection helper, protected manifest, runtime lineage projection, and generated diagnostic artifact families.
- **Is replay ownership sufficiently distributed?** Scenario execution ownership is now reasonably distributed. Schema, helper, diagnostics, and reporting ownership remains only partially distributed.
- **Is replay maintenance bottlenecked?** Yes, but the bottleneck moved from one mega-test into a small set of shared hubs and synchronized artifacts.
- **What files are the likely bottlenecks?** `golden_replay.py`, `failure_dashboard_report.py`, `golden_replay_projection.py`, the protected manifest/refresh pair, `test_golden_replay_fallback_projection.py`, and the runtime replay projection.

## Replay Maintenance Cost Signals

- Historical large-test concentration: 38 commits to the former monolith.
- Residual helper concentration: 25 commits and approximately 45 importers for `golden_replay.py`.
- Diagnostic concentration: 21 commits, 3,145 lines, and 82 definitions in `failure_dashboard_report.py`.
- Protected schema synchronization: projection registry + generated manifest + refresh tool + parity tests.
- Forty-one protected observation paths, 39 structural and two semantic, create broad schema blast radius.
- Multi-file generated artifact churn: top commits touch 25–30 replay files, largely JSON/Markdown report families.
- Repeated paired outputs: JSON and Markdown versions of hotspots, risk, trends, recurrence, incidence, economics, remediation, and ROI.
- Mixed commits: behavior, registry, diagnostics, and generated outputs frequently land together, obscuring the true source of maintenance cost.
- Registry authority fan-out: only two scenario-registry edits, but many tests/tools assume exact counts, IDs, order, categories, dimensions, and marker collection.
- Projection coupling: acceptance projection consumes runtime projection, sanitizer, speaker observation, transcript/debug trace, and classifier-facing presence metadata.
- Facade underuse: `golden_replay_api.py` has only eight importers while direct broad-helper imports remain common.
- Current test concentration: fallback projection (1,145 lines) and general projection (810 lines) are the next likely test-level hotspots.
- Contributor concentration: all measured commits have one Git author identity, so social ownership appears fully centralized in available history even where file ownership is structurally distributed.

## Recommended Next Blocks

Do not implement these in CE discovery.

1. **CE1 — Reproducible concentration metric**
   - Add a read-only script that defines the canonical replay maintenance set and emits per-file touches, windows, multi-file commits, authors, line counts, and import fan-in.
   - Separate generated corpus snapshots from maintainable authority files.

2. **CE2 — Diagnostic/report family split**
   - Decompose `failure_dashboard_report.py` by artifact family: protected failure/dashboard, drift/stability, recurrence lifecycle, and persistence/writers.
   - Preserve public compatibility facades and byte-identical report output.

3. **CE3 — Acceptance projection ownership split**
   - Separate protected schema/manifest rendering, payload extraction, fallback/sanitizer projection, and speaker-parity projection behind a stable facade.
   - Keep `PROTECTED_OBSERVATION_FIELDS` as one explicit authority unless a governed schema migration is approved.

4. **CE4 — Fallback projection test decomposition**
   - Split `tests/test_golden_replay_fallback_projection.py` by opening/sealed, visibility/referential, sanitizer/upstream-fast, and long-session/acceptance-matrix responsibilities.
   - Do not weaken cross-owner parity assertions.

5. **CE5 — Generated artifact churn reduction**
   - Define which replay reports are canonical versioned evidence versus reproducible local outputs.
   - Consider one manifest/index for paired JSON/Markdown artifacts and isolate regeneration-only commits from behavior changes.

## Files to Pass Back to ChatGPT

Minimum follow-up set:

- `CE_golden_replay_concentration_audit_discovery.md`
- `tests/test_golden_replay.py`
- `tests/test_golden_replay_structural_invariants.py`
- `tests/test_golden_replay_projection.py`
- `tests/test_golden_replay_fallback_projection.py`
- `tests/helpers/protected_replay_registry.py`
- `tests/test_protected_replay_registry.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_api.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/failure_dashboard_report.py`
- `game/final_emission_replay_projection.py`
- `docs/testing/protected_replay_manifest.md`
- `tools/refresh_protected_replay_manifest.py`
- `docs/audits/discovery/cycle_au_golden_replay_ownership_compression_recon.md`
- `audits/cycle_au_golden_replay_owner_mapping.md`

No separate raw Git output file was generated; the measured concentration results and scope are embedded in this report.
