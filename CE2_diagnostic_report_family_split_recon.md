# CE2 — Diagnostic / Report Family Split Recon

## Executive Summary

Replay diagnostics are **partially decomposed** but **still concentrated** in `tests/helpers/failure_dashboard_report.py`. Measured at **3,359 LOC** and **82 functions** (0 classes), the file remains the primary orchestration hub for session recording, artifact persistence, markdown rendering, and recurrence report assembly despite prior extraction of drift analytics into `replay_drift_*` modules and classification into `failure_classifier.py`.

**Primary metric — Diagnostic Concentration Risk: HIGH**

| Signal | Measurement |
|---|---|
| Hub LOC | 3,359 (2.2× `failure_classifier.py`, 3rd-largest replay helper after `golden_replay.py` and `replay_bug_recurrence.py`) |
| Recurrence concentration | **54.5%** of function LOC in recurrence analysis/rendering |
| External fan-in | **21** importing files (tests, tools, conftest, fixtures, lazy recurrence import) |
| Largest function | `write_bug_recurrence_history_artifacts` — **409 LOC** |
| Git churn | **21** commits on file; drift/recurrence themes dominate |
| Dependency cycle | Yes — `failure_dashboard_report` ↔ `replay_bug_recurrence` via path constant |

Drift **aggregation logic** is already distributed (`replay_drift_taxonomy`, `replay_drift_hotspots`, `replay_drift_trends`, `replay_drift_risk`, `replay_drift_longitudinal`, `replay_drift_rows`, facade `replay_drift_reports`). What remains centralized is:

1. **Recurrence markdown rendering** (~1,650 LOC of section builders + history renderer)
2. **Artifact write orchestration** (scorecard/failure cascades that fan out to 6+ artifact pairs)
3. **Session recording buffers** (in-memory row/scorecard collectors)
4. **Path/env contract surface** (17 canonical artifact paths + 3 env gates)
5. **Thin classification adapters** (`build_failure_dashboard_rows` delegating to classifier)

A **safe decomposition plan exists** without behavior change: extract path registry and recurrence rendering first, then collection buffers, then drift/stability writers, leaving a compatibility facade at `failure_dashboard_report.py`.

---

## Responsibility Inventory

Multiple unrelated domains coexist in one file. The table groups responsibilities by domain; line spans are inclusive.

| Responsibility | Functions | Lines (approx) | Category |
|---|---|---|---|
| Dashboard table rendering (columns, evidence cells, headers) | `expected_failure_dashboard_columns`, `_failure_dashboard_table_header`, `_failure_dashboard_table_separator`, `_format_dashboard_evidence_value`, `_prepared_emission_evidence_parts`, `_evidence_cell`, `_cell`, `render_failure_dashboard_markdown` | 117–2646 (~180 LOC in render path) | report rendering / markdown generation |
| Classification row assembly (delegates to classifier) | `build_failure_dashboard_rows`, `build_classified_dashboard_row`, `_flatten_drift_rows`, `_drift_type` | 298–393 (~95 LOC) | failure classification / replay observation processing |
| Session recording buffers | `record_*`, `recorded_*`, `clear_recorded_*`, `clear_requested_artifact_recordings` | 457–570 (~115 LOC) | failure collection |
| Env/path gates | `failure_dashboard_requested`, `rerun_drift_scorecard_requested`, `long_session_stability_scorecard_requested`, 17 `*_PATH` constants | 250–279, 432–452 | path management / utility |
| Owner drift summary tables (inline, not delegated) | `_owner_drift_summary_table_lines`, `_owner_drift_breakdown_lines` | 151–183 (~35 LOC) | drift analysis / report rendering |
| Longitudinal drift artifacts | `scorecards_for_longitudinal_aggregation`, `write_owner_drift_longitudinal_artifacts`, `append_owner_drift_longitudinal_markdown` | 573–636 (~65 LOC) | drift analysis / artifact writing |
| Hotspot drift artifacts | `collected_hotspot_classifications`, `write_owner_drift_hotspot_artifacts` | 639–690 (~55 LOC) | hotspot analysis / artifact writing |
| Trend drift artifacts | `write_owner_drift_trend_artifacts` | 693–722 (~30 LOC) | trend analysis / artifact writing |
| Risk drift artifacts (+ recurrence side-effect) | `write_owner_drift_risk_artifacts` | 2524–2569 (~46 LOC) | risk analysis / artifact writing |
| Recurrence path helpers | `_bug_recurrence_event_log_path`, `_bug_recurrence_session_diagnostic_event_log_path`, `_bug_recurrence_trajectory_history_path`, `protected_replay_recurrence_event_metadata` | 2071–2110 (~45 LOC) | path management / recurrence analysis |
| Recurrence history orchestration | `write_bug_recurrence_history_artifacts` | 2113–2521 (**409 LOC**) | recurrence analysis / artifact writing / aggregation |
| Recurrence markdown section builders (16 helpers) | `_regression_recurrence_rate_markdown_lines`, `_recurrence_trends_markdown_lines`, `_recurrence_forecast_markdown_lines`, `_portfolio_bucket_markdown_lines`, `_recurrence_portfolio_markdown_lines`, `_remediation_bucket_markdown_lines`, `_recurrence_remediation_markdown_lines`, `_roi_bucket_markdown_lines`, `_recurrence_roi_markdown_lines`, `_governance_watchlist_markdown_lines`, `_recurrence_governance_markdown_lines`, `_recurrence_lifecycle_markdown_lines`, `_recurrence_trajectory_markdown_lines`, `_recurrence_program_effectiveness_markdown_lines`, `_recurrence_maturity_markdown_lines`, `_recurrence_roadmap_markdown_lines`, `_recurrence_completion_markdown_lines`, `_recurrence_graduation_audit_markdown_lines`, `_recurrence_confidence_calibration_markdown_lines`, `render_bug_recurrence_history_markdown` | 725–2068 (**~870 LOC render-only**) | recurrence analysis / markdown generation |
| Protected failure report | `render_protected_replay_failure_report`, `write_protected_replay_failure_report_if_present` | 2980–3210 (~200 LOC) | report rendering / artifact writing |
| Rerun drift scorecard | `render_rerun_drift_scorecard_markdown`, `write_rerun_drift_scorecard_artifacts`, `write_rerun_drift_scorecard_artifacts_if_requested`, `_scorecard_summary`, `_nested_delta`, `_no_rerun_scorecard` | 2743–2977 (~180 LOC) | drift analysis / markdown generation / artifact writing |
| Long-session stability scorecard | `_stability_ownership_markdown_lines`, `render_long_session_stability_scorecard_markdown`, `write_long_session_stability_scorecard_artifacts`, `write_long_session_stability_scorecard_artifacts_if_requested` | 186–247, 3213–3359 (~170 LOC) | stability analysis / markdown generation / artifact writing |
| Session artifact facade | `write_failure_dashboard_artifact`, `write_failure_dashboard_artifact_if_requested`, `write_requested_dashboard_artifacts` | 2649–2740 (~95 LOC) | artifact writing / utility |
| Contract re-exports | `REPLAY_PROTECTED_FIELD_PATHS`, `KNOWN_FAILURE_CATEGORIES`, `FAILURE_DASHBOARD_EVIDENCE_*`, `FAILURE_DASHBOARD_TABLE_COLUMNS`, `build_runtime_lineage_summary` (import side-effect) | 86–113, 250–279 | utility / path management |

**Coexistence verdict:** Yes — recurrence rendering, drift artifact orchestration, dashboard table rendering, session collection, and path contracts all live in one module.

---

## Internal Concentration Analysis

### Module totals

| Metric | Value |
|---|---|
| Total LOC | 3,359 |
| Total functions | 82 |
| Total classes | 0 |
| Average function LOC | 37.0 |
| Module-level constants / buffers | ~280 LOC (paths, env vars, `_RECORDED_*` lists, column tuple) |

### Largest objects

| Object | Type | LOC |
|---|---|---:|
| `write_bug_recurrence_history_artifacts` | function | 409 |
| `render_bug_recurrence_history_markdown` | function | 220 |
| `render_protected_replay_failure_report` | function | 185 |
| `render_rerun_drift_scorecard_markdown` | function | 123 |
| `_recurrence_program_effectiveness_markdown_lines` | function | 101 |
| `render_long_session_stability_scorecard_markdown` | function | 99 |
| Module constants block | module | ~85 |
| `_RECORDED_*` session buffers | module | ~6 lines + accessors ~76 LOC |

### Top 10 largest functions

| Function | LOC | Lines |
|---|---:|---|
| `write_bug_recurrence_history_artifacts` | 409 | 2113–2521 |
| `render_bug_recurrence_history_markdown` | 220 | 1849–2068 |
| `render_protected_replay_failure_report` | 185 | 2980–3164 |
| `render_rerun_drift_scorecard_markdown` | 123 | 2766–2888 |
| `_recurrence_program_effectiveness_markdown_lines` | 101 | 1380–1480 |
| `render_long_session_stability_scorecard_markdown` | 99 | 3213–3311 |
| `_recurrence_trends_markdown_lines` | 83 | 747–829 |
| `_recurrence_completion_markdown_lines` | 81 | 1636–1716 |
| `_recurrence_maturity_markdown_lines` | 77 | 1483–1559 |
| `render_failure_dashboard_markdown` | 75 | 2572–2646 |

### Top 10 most central functions (internal fan-in)

| Function | Fan-in | Called by (internal) |
|---|---:|---|
| `_cell` | 17 | All recurrence markdown builders, dashboard/failure/scorecard renderers |
| `recorded_rerun_drift_scorecards` | 6 | Hotspot/trend/risk writers, longitudinal aggregation, session facade |
| `recorded_long_session_stability_scorecards` | 4 | Stability render/write, risk writer, session facade |
| `_as_list` | 3 | Drift flattening, dashboard render |
| `collected_hotspot_classifications` | 3 | Hotspot/risk writers, scorecard cascade |
| `failure_dashboard_requested` | 3 | Clear recordings, dashboard write-if-requested, session facade |
| `long_session_stability_scorecard_requested` | 3 | Clear recordings, stability write-if-requested, session facade |
| `rerun_drift_scorecard_requested` | 3 | Clear recordings, scorecard write-if-requested, session facade |
| `_owner_drift_breakdown_lines` | 2 | Dashboard + protected failure renderers |
| `_owner_drift_summary_table_lines` | 2 | Stability ownership lines, rerun scorecard renderer |

### Multi-domain owners (probable bottlenecks)

| Function | Domains owned | Risk |
|---|---|---|
| `write_bug_recurrence_history_artifacts` | persistence, aggregation orchestration, trajectory side-effects, supplementary doc writes | **Critical** — single 409-LOC change surface for recurrence family |
| `write_rerun_drift_scorecard_artifacts` | scorecard persistence + longitudinal + hotspot + trend + risk cascade | **High** — fans out to entire drift artifact family |
| `write_protected_replay_failure_report_if_present` | protected report + hotspot + risk (+ recurrence via risk writer) | **High** |
| `write_requested_dashboard_artifacts` | session exit routing across all artifact families | **High** |
| `render_bug_recurrence_history_markdown` | 16+ recurrence section renderers | **High** — formatting churn isolated but co-located with writer |
| `_cell` | shared markdown escaping for all report families | **Medium** — cosmetic but widely fan-in |

---

## Dependency Map

### Incoming Dependencies

| File | Usage |
|---|---|
| `tests/conftest.py` | Session teardown: `clear_requested_artifact_recordings`, `write_requested_dashboard_artifacts` |
| `tests/helpers/golden_replay.py` | Replay runner recording hooks (dashboard rows, protected failures, lineage events) |
| `tests/helpers/failure_dashboard_fixtures.py` | Controlled failure seeding |
| `tests/helpers/failure_classification_sync.py` | Contract parity on evidence manifest re-exports |
| `tests/helpers/replay_bug_recurrence.py` | Lazy import of `RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH` (cycle) |
| `tests/test_failure_dashboard_report.py` | Primary render/write/recording tests |
| `tests/test_failure_classifier.py` | Classifier + dashboard row builder tests; imports `build_runtime_lineage_summary` via re-export |
| `tests/test_failure_dashboard_controlled_failures.py` | Opt-in probe integration |
| `tests/test_failure_classification_contract.py` | Evidence manifest + renderer contract |
| `tests/test_golden_replay_protected_bridge.py` | Protected assertion → report bridge |
| `tests/test_replay_drift_{hotspots,longitudinal,trends,risk}.py` | Per-family artifact writer tests |
| `tests/test_stability_reporting_contract.py` | Stability markdown contract |
| `tests/test_recurrence_trajectory_history.py` | Recurrence markdown rendering |
| `tools/{backfill_bug_recurrence_history,migrate_bug_recurrence_event_log,capture_recurrence_trajectory_*,expand_protected_replay_observations}.py` | CLI path constants and writers |

**Measured fan-in:** 21 Python files import the module directly.

### Outgoing Dependencies

| File | Usage |
|---|---|
| `tests/helpers/failure_classifier.py` | `classify_replay_failure`, `FailureClassification` — **classifier coupling** |
| `tests/helpers/failure_classification_sync.py` | Evidence manifest, row shape validation, known categories — **projection/sync coupling** |
| `tests/helpers/golden_replay_projection.py` | `protected_observation_field_paths()` — **projection coupling** |
| `tests/helpers/runtime_lineage_reporting.py` | Lineage summary + markdown lines — **lifecycle coupling** |
| `tests/helpers/replay_drift_reports.py` | Facade over drift analytics + render helpers — **drift coupling** |
| `tests/helpers/replay_bug_recurrence.py` | 30+ recurrence build/aggregate/render functions — **recurrence coupling** |
| `game/runtime_lineage_telemetry.py` | `normalize_runtime_lineage_events` — **runtime coupling** (normalization only) |

### Coupling highlights

| Coupling type | Level | Notes |
|---|---|---|
| Classifier | MEDIUM | Dashboard builds rows via classifier; does not own taxonomy |
| Drift analytics | LOW–MEDIUM | Writers delegate to `replay_drift_*`; hub owns orchestration only |
| Recurrence | HIGH | Hub owns 409-LOC writer + 870 LOC markdown; analytics in 10,470-LOC `replay_bug_recurrence.py` |
| Projection | LOW | Re-exports contract-owned manifests; no inline field enumeration |
| Runtime | LOW | Single normalize import; lineage summary delegated |

### Dependency cycles

```
failure_dashboard_report.py
  → replay_bug_recurrence.py (static import, 30+ symbols)
  → failure_dashboard_report.py (lazy import in 3 functions for RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH)
```

No other cycles detected among direct imports. The cycle is **path-constant-driven** and breakable without semantic change.

---

## Artifact Family Map

| Artifact | Producer | Format | Consumer |
|---|---|---|---|
| `audits/failure_dashboard_latest.md` | `write_failure_dashboard_artifact*` | Markdown | Operators, controlled-failure probes |
| `artifacts/golden_replay/replay_failure_report.md` | `write_protected_replay_failure_report_if_present` | Markdown | Protected replay CI, backfill tools, governance docs |
| `artifacts/golden_replay/rerun_drift_scorecard.{json,md}` | `write_rerun_drift_scorecard_artifacts` | JSON + Markdown | Rerun opt-in diagnostics |
| `artifacts/golden_replay/owner_drift_longitudinal.{json,md}` | `write_owner_drift_longitudinal_artifacts`, append via scorecard | JSON + Markdown | Longitudinal drift tests, scorecard cascade |
| `artifacts/golden_replay/owner_drift_hotspots.{json,md}` | `write_owner_drift_hotspot_artifacts` | JSON + Markdown | Hotspot tests; failure + scorecard paths |
| `artifacts/golden_replay/owner_drift_trends.{json,md}` | `write_owner_drift_trend_artifacts` | JSON + Markdown | Trend tests; scorecard cascade |
| `artifacts/golden_replay/owner_drift_risk.{json,md}` | `write_owner_drift_risk_artifacts` | JSON + Markdown | Risk tests; failure + scorecard paths |
| `artifacts/golden_replay/bug_recurrence_history.{json,md}` | `write_bug_recurrence_history_artifacts` | JSON + Markdown | Recurrence tools/tests, expand observations |
| `artifacts/golden_replay/bug_recurrence_event_log.json` | `write_bug_recurrence_history_artifacts` | JSON | Protected recurrence lane |
| `artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json` | `write_bug_recurrence_history_artifacts` | JSON | Session noise lane |
| `artifacts/golden_replay/recurrence_trajectory_history.json` | `write_bug_recurrence_history_artifacts` (via trajectory apply) | JSON | Trajectory capture tools, `replay_bug_recurrence` loaders |
| `artifacts/golden_replay/long_session_stability_scorecard.{json,md}` | `write_long_session_stability_scorecard_artifacts` | JSON + Markdown | Stability contract tests |
| `docs/audits/BQ16_recurrence_graduation_audit.md` | `write_bug_recurrence_history_artifacts` | Markdown | Governance closeouts |
| `docs/audits/BQC3_confidence_calibration_audit.md` | `write_bug_recurrence_history_artifacts` | Markdown | Governance closeouts |
| `docs/audits/BQC4_final_graduation_decision.md` | `write_bug_recurrence_history_artifacts` | Markdown | Trajectory activation tools |
| `docs/audits/BQC5_effectiveness_validation.md` | `write_bug_recurrence_history_artifacts` | Markdown | Outcome validation |

### Co-change clusters

| Cluster | Artifacts | Trigger |
|---|---|---|
| **Scorecard cascade** | rerun scorecard + longitudinal + hotspots + trends + risk + bug recurrence history | `write_rerun_drift_scorecard_artifacts` |
| **Protected failure cascade** | replay_failure_report + hotspots + risk (+ recurrence via risk) | `write_protected_replay_failure_report_if_present` |
| **Recurrence family** | history json/md + event logs + trajectory + 4 governance docs | `write_bug_recurrence_history_artifacts` |
| **Independent** | failure_dashboard_latest | `write_failure_dashboard_artifact_if_requested` only |
| **Independent** | long_session_stability_scorecard | env-gated stability writer |

### Safe split candidates

| Artifact group | Split safety | Rationale |
|---|---|---|
| Path constants only | **High** | Breaks import cycle; no output change |
| Recurrence markdown renderers | **High** | Pure functions; heavy LOC, low fan-out |
| Session recording buffers | **High** | Isolated mutable state |
| Drift writer thin wrappers | **Medium** | Must preserve cascade order in orchestrator |
| Recurrence writer orchestration | **Medium** | Large but test-locked; move with renderer together |
| `write_requested_dashboard_artifacts` | **Low alone** | Must remain facade until sub-writers stabilize |

---

## Ownership Boundary Analysis

| Stage | Current owner functions | Dependencies | Coupling |
|---|---|---|---|
| **A. Data collection** | `record_failure_dashboard_rows`, `record_protected_replay_assertion_failure`, `record_rerun_drift_scorecard`, `record_long_session_stability_scorecard`, `record_runtime_lineage_events` | In-memory lists only | **LOW** |
| **B. Classification** | `build_failure_dashboard_rows`, `build_classified_dashboard_row`, `collected_hotspot_classifications` | `failure_classifier`, `replay_drift_rows` | **MEDIUM** (correct delegation, but adapter stays in hub) |
| **C. Aggregation** | `write_bug_recurrence_history_artifacts` (recurrence stack), drift writers calling `replay_drift_reports` | `replay_bug_recurrence`, `replay_drift_*` | **HIGH** for recurrence orchestration; **LOW** for drift (already extracted) |
| **D. Rendering** | `render_*`, `_recurrence_*_markdown_lines`, `_stability_ownership_markdown_lines`, dashboard table helpers | Classifier row shape, drift summaries, lineage markdown | **HIGH** (recurrence markdown volume) |
| **E. Persistence** | All `write_*` functions, path constants, env gates, `write_requested_dashboard_artifacts` | Filesystem, JSON dumps, cascade triggers | **HIGH** |

**Cross-stage mixing:** The file performs all five stages. Stages C+D are most entangled in recurrence (`write_bug_recurrence_history_artifacts` builds payload and renders markdown inline).

---

## Compatibility Surface

| Public API | Importers | Stability |
|---|---|---|
| `write_requested_dashboard_artifacts` | `tests/conftest.py` | **Must remain stable** |
| `record_failure_dashboard_rows`, `record_protected_replay_assertion_failure`, `record_runtime_lineage_events`, `failure_dashboard_requested` | `tests/helpers/golden_replay.py` | **Must remain stable** |
| `FAILURE_DASHBOARD_EVIDENCE_{MANIFEST,ROW_KEYS,LABELS}` | sync helper, contract tests, controlled failures | **Must remain stable** (contract-locked) |
| `KNOWN_FAILURE_CATEGORIES`, `REPLAY_PROTECTED_FIELD_PATHS` | controlled failure tests | **Must remain stable** |
| `build_failure_dashboard_rows`, `build_classified_dashboard_row`, `render_failure_dashboard_markdown` | classifier + contract tests | **Must remain stable** |
| `write_owner_drift_{hotspot,longitudinal,trend,risk}_artifacts` | drift test modules | **Must remain stable** |
| `write_rerun_drift_scorecard_artifacts`, `write_protected_replay_failure_report_if_present` | dashboard report tests, protected bridge | **Must remain stable** |
| `write_bug_recurrence_history_artifacts`, `BUG_RECURRENCE_*_PATH` | tools + tests | **Must remain stable** |
| `RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH` | `replay_bug_recurrence` (lazy) | **Must remain stable**; should move to registry |
| `build_runtime_lineage_summary` | `tests/test_failure_classifier.py` | **Accidental re-export** — can redirect importers to `runtime_lineage_reporting` |
| `_evidence_cell` | controlled failure tests only | **Can become internal** |
| `clear_recorded_*`, `recorded_*` | test modules | **Stable for tests**; internalizable with facade |
| `protected_replay_recurrence_event_metadata` | backfill, protected bridge, dashboard tests | **Must remain stable** |

**Compatibility facade:** Yes — keeping `tests/helpers/failure_dashboard_report.py` as a re-export shim (as already done for `replay_drift_reports`) preserves all 21 importers while moving implementation.

---

## Candidate Split Evaluation

| Candidate Module | Responsibilities | Risk | Benefit |
|---|---|---|---|
| **A. `failure_dashboard_collection.py`** | Session buffers, `record_*` / `recorded_*` / `clear_*`, env gate readers | **LOW** | Isolates mutable session state; reduces hub by ~115 LOC |
| **B. `failure_dashboard_classification.py`** | `build_failure_dashboard_rows`, `build_classified_dashboard_row`, `_flatten_drift_rows`, `collected_hotspot_classifications` | **MEDIUM** | Clarifies classifier adapter boundary; small LOC win (~90) |
| **C. `failure_dashboard_rendering.py`** | Dashboard table render, protected failure render, scorecard/stability markdown, shared `_cell` | **MEDIUM** | Consolidates non-recurrence markdown (~550 LOC); shared `_cell` fan-in contained |
| **D. `failure_dashboard_persistence.py`** | Thin `write_*` for dashboard, drift, stability (not recurrence) | **MEDIUM** | Separates filesystem I/O from render logic; cascade order must stay |
| **E. `failure_dashboard_artifact_registry.py`** | All `*_PATH`, env var names, path helper functions | **LOW** | Breaks recurrence cycle; single source for tools/tests |
| **F. `failure_dashboard_recurrence.py`** | `render_bug_recurrence_history_markdown`, `_recurrence_*_markdown_lines`, `write_bug_recurrence_history_artifacts`, recurrence metadata helper | **MEDIUM–HIGH** | Removes **~1,280 LOC** from hub; largest maintenance win |
| **G. `failure_dashboard_drift.py`** | Drift artifact writers + scorecard cascade orchestration | **MEDIUM** | Groups co-changing drift family; ~350 LOC |
| **H. `failure_dashboard_stability.py`** | Stability markdown + writers + `_stability_ownership_markdown_lines` | **LOW** | Clean boundary (~170 LOC); already contract-tested separately |

**Do not split** render/write pairs across modules without moving both — tests assert byte-stable artifact output.

---

## Maintenance Cost Drivers

### LOC allocation (function bodies)

| Area | % of function LOC | Driver |
|---|---:|---|
| Recurrence analysis/rendering | 54.5% | BQ/AY recurrence program expansion |
| Markdown generation (non-recurrence) | 16.4% | Scorecard + protected failure formatting |
| Artifact writing | 7.8% | Multi-file cascade persistence |
| Stability | 7.1% | Long-session scorecard sections |
| Classification adapters | 2.9% | Row builder wrappers |
| Collection | 2.5% | Session buffers |

### Git commit themes (21 commits, overlapping tags)

| Theme | Commits (tagged) | Likely maintenance cause |
|---|---:|---|
| Drift (AR/AT/Q/S) | 15 | New drift artifact families, cascade wiring |
| Recurrence (AY/BQ) | 10 | History population, trajectory, governance docs |
| Compression/refactor | 8 | Surface-area moves, not true decomposition |
| Classification/owner | 6 | Evidence column/manifest alignment |
| Dashboard/format | 4 | Table columns, rendering tweaks |
| Lineage | 3 | Runtime lineage section in markdown |

### Concentration drivers

1. **Recurrence markdown expansion** — 16 section builders added incrementally; no separate module boundary.
2. **Artifact cascade orchestration** — one scorecard write triggers 5 sibling artifact families.
3. **Path constant hub** — tools import paths from report module, forcing recurrence ↔ dashboard cycle.
4. **Report formatting churn** — column/evidence manifest changes touch render functions with high fan-in (`_cell`).
5. **Classification updates** — mostly land in `failure_classifier.py`; dashboard impact is lower (~3% LOC) but contract re-exports require sync.

**What causes most maintenance cost?** Recurrence orchestration + markdown (combined **>60%** of meaningful churn), followed by drift artifact cascade wiring (**~25%**), then dashboard table/evidence formatting (**~10%**).

---

## Diagnostic Concentration Risk Assessment

### Is `failure_dashboard_report.py` a maintenance hotspot?

**Yes.** Evidence:

- 3,359 LOC / 82 functions in a single module with no classes
- 21 direct importers including pytest session hook and 5 CLI tools
- 54.5% LOC in recurrence alone; top function is 409 LOC
- 21 git commits — 2nd-highest among replay helpers per CE golden replay audit
- Owns multi-artifact cascades that regenerate 6–10 files per trigger
- Contains the only measured import cycle in the diagnostic family

### Why?

Prior cycles extracted **drift analytics** and **classification policy** but left **report assembly, persistence orchestration, and recurrence presentation** in the original dashboard module. New recurrence governance features (portfolio, ROI, maturity, graduation) appended markdown builders into the same file rather than a recurrence report module.

### Which responsibilities should move first?

1. **`failure_dashboard_artifact_registry.py`** — path/env constants (breaks cycle, zero behavior change)
2. **Recurrence markdown + writer** → `failure_dashboard_recurrence.py` (largest LOC reduction)
3. **Session collection** → `failure_dashboard_collection.py` (isolates mutable state)

### Which responsibilities should never be separated?

- **Render + write pairs** for the same artifact (e.g., `render_protected_replay_failure_report` / `write_protected_replay_failure_report_if_present`)
- **Scorecard cascade orchestration** from its downstream drift writers until cascade tests move together
- **Contract re-exports** (`FAILURE_DASHBOARD_EVIDENCE_*`) from sync helper parity tests without a coordinated move

### Safest decomposition order

1. Artifact path registry (cycle break)
2. Session collection buffers
3. Recurrence rendering + persistence module
4. Drift/stability writer modules (thin wrappers stay grouped with cascades)
5. Non-recurrence rendering module
6. Compatibility facade at original import path

---

## Recommended Implementation Blocks

### Block 1 — Artifact Path Registry (E)

Extract all `*_PATH`, env var constants, and `_bug_recurrence_*_path` helpers to `failure_dashboard_artifact_registry.py`. Update `replay_bug_recurrence` lazy imports to use registry. Re-export from facade.

**Risk:** Low | **LOC moved:** ~100 | **Validates:** import cycle gone; tool tests unchanged

### Block 2 — Session Collection (A)

Move `_RECORDED_*` lists and record/recorded/clear APIs to `failure_dashboard_collection.py`. Facade re-exports.

**Risk:** Low | **LOC moved:** ~115 | **Validates:** golden replay + conftest session hooks

### Block 3 — Recurrence Report Module (F)

Move `_recurrence_*_markdown_lines`, `render_bug_recurrence_history_markdown`, `write_bug_recurrence_history_artifacts`, `protected_replay_recurrence_event_metadata` to dedicated module. No logic changes.

**Risk:** Medium | **LOC moved:** ~1,280 | **Validates:** recurrence trajectory tests, tool CLIs, artifact byte parity

### Block 4 — Drift Writer Module (G)

Move `write_owner_drift_{longitudinal,hotspot,trend,risk}_artifacts`, scorecard cascade functions, `collected_hotspot_classifications`, longitudinal append helper.

**Risk:** Medium | **LOC moved:** ~350 | **Validates:** replay_drift_* test modules, scorecard cascade ordering

### Block 5 — Stability Module (H)

Move stability scorecard render/write functions and `_stability_ownership_markdown_lines`.

**Risk:** Low | **LOC moved:** ~170 | **Validates:** `test_stability_reporting_contract.py`

### Block 6 — Facade + Rendering Split (C + remaining)

Extract dashboard/protected-failure/rerun markdown renderers to `failure_dashboard_rendering.py`. Leave `failure_dashboard_report.py` as thin facade: re-exports + `write_requested_dashboard_artifacts` + contract constants.

**Risk:** Medium | **LOC moved:** ~550 | **Validates:** classifier tests, controlled failures, contract sync

---

## Method and Evidence

- AST analysis of `failure_dashboard_report.py` (82 functions, line spans, fan-in) — see `CE2_diagnostic_concentration_metrics.json`
- Importer scan of 21 Python files — see `CE2_diagnostic_importer_map.json`
- Git history: 21 commits on target file; thematic tagging of commit messages
- Cross-reference: CE golden replay audit (21 touches, diagnostic hub ranking)
- No code, paths, or behavior modified during this recon

## Related Files (unchanged)

| File | Role in diagnostic family |
|---|---|
| `tests/helpers/failure_dashboard_report.py` | Current hub (this recon target) |
| `tests/helpers/failure_classifier.py` | Classification policy (995 LOC, 37 functions) |
| `tests/helpers/replay_drift_*.py` | Extracted drift analytics family (facade: `replay_drift_reports.py`) |
| `tests/helpers/replay_bug_recurrence.py` | Recurrence analytics engine (10,470 LOC) |
| `tests/helpers/runtime_lineage_reporting.py` | Lineage summary adapter |
