# BQ Recurrence History Discovery

**Date:** 2026-06-19  
**Scope:** Discovery only. No runtime behavior, replay pass/fail, schema, or test expectation changes.

## Executive Summary

Recurrence infrastructure exists in **three parallel tracks** with different schemas and consumers:

1. **Bug-class recurrence (Cycle AY)** — projection/aggregation in `tests/helpers/replay_bug_recurrence.py`, artifact writers in `tests/helpers/failure_dashboard_report.py`, policy in `docs/testing/protected_replay_manifest.md`. Committed artifacts under `artifacts/golden_replay/bug_recurrence_history.*` are **schema-valid but empty** (`unique_recurrence_count: 0`).
2. **Runtime lineage recurrence (Cycle H)** — per-event `recurrence_key` in `game/runtime_lineage_telemetry.py`, aggregated per-run into `by_recurrence_key` / `recurring_events`. **No cross-run history store**; recurrence is per report/run only.
3. **Fallback incidence recurrence (BP5/BP7)** — append-only snapshot history in `tools/fallback_incidence_trends.py` feeding `tools/fallback_recurrence.py`. Committed `artifacts/golden_replay/fallback_incidence_history.json` has **`snapshots: []`**, so BP7 reports show `status: no_history`.

**Regression Recurrence Rate** is named in the BQ goal but **does not exist** as a symbol, field, or report line in the repository. Closest existing proxies:

- `tools/fallback_portfolio_benefit.py` → `engineering_yield.regression_rate` (remediation outcomes regressed / completed)
- `tools/fallback_remediation_effectiveness.py` → `regression_evidence.recurrence_returned_after_closure` (fallback contributor recurrence worsened after remediation closure)

BQ’s primary gap for replay recurrence trends is **track 1**: aggregation works, but there is **no append-only event log** across protected replay runs—writers re-aggregate **current session rows only** and overwrite the committed artifact.

---

## Current Recurrence Infrastructure

### Core implementation files

| File | Responsibility |
|---|---|
| `tests/helpers/replay_bug_recurrence.py` | Bug-class recurrence key derivation, row projection, history aggregation, summary status (`active`/`watch`/`retired`) |
| `tests/helpers/failure_dashboard_report.py` | Artifact I/O: `write_bug_recurrence_history_artifacts`, called from `write_owner_drift_risk_artifacts` and protected failure path |
| `tests/helpers/replay_drift_reports.py` | Report facade re-exporting recurrence helpers |
| `tests/helpers/replay_drift_rows.py` | Classification row normalization; expands rerun scorecards into pseudo-classification rows |
| `game/runtime_lineage_telemetry.py` | Runtime event `recurrence_key` generation; `summarize_runtime_lineage_events` → `by_recurrence_key`, `recurring_events` |
| `game/final_emission_replay_projection.py` | FEM → runtime lineage events consumed by replay/scenario-spine summaries |
| `tools/fallback_incidence_trends.py` | BP5 append-only `fallback_incidence_history.json` snapshot store |
| `tools/fallback_recurrence.py` | BP7 fallback entity recurrence/persistence analysis over BP5 history |
| `tools/fallback_remediation_effectiveness.py` | Remediation regression including `recurrence_returned_after_closure` |
| `tools/fallback_portfolio_benefit.py` | Portfolio `regression_rate` over completed remediations |
| `tools/fallback_remediation_queue.py` | Queue promotion gates using `recurrence_evidence.classification` |
| `tools/fallback_maintenance_economics.py` | Integrates BP7 recurrence status into economics rollup |
| `docs/testing/protected_replay_manifest.md` | Cycle AY recurrence policy (`report_only`, `advisory_only`, artifact paths) |

### Governance / enumeration

| File | Responsibility |
|---|---|
| `docs/testing/protected_replay_manifest.md` | Canonical protected replay scenario inventory, reproduction commands, AY recurrence addendum |
| `tests/replay_governance_registry.py` | Drift category → governance reason mapping; references manifest |
| `tools/refresh_protected_replay_manifest.py` | Regenerates protected observation field-path table from `PROTECTED_OBSERVATION_FIELDS` |

### Committed recurrence artifacts (all under `artifacts/golden_replay/`)

| Artifact | Status |
|---|---|
| `bug_recurrence_history.json` / `.md` | Empty history (0 keys, 0 events) |
| `fallback_incidence_history.json` | Empty snapshots |
| `fallback_recurrence_report.json` / `.md` | `status: no_history`, `snapshot_count: 0` |
| `fallback_risk_history.json` | Placeholder: one snapshot with empty `contributors` |
| `owner_drift_longitudinal.json` | `total_runs: 0` |
| `owner_drift_risk.json` | Empty risk/stability signals |
| `replay_failure_report.md` | **One historical failure** (2026-06-04, speaker drift) — markdown only |

### Schema / data shapes

#### Bug-class recurrence (Cycle AY) — authority: `tests/helpers/replay_bug_recurrence.py`

**Row shape** (`recurrence_rows` output):

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | `RECURRENCE_SCHEMA_VERSION = 1` |
| `report_only` | bool | always `true` |
| `advisory_only` | bool | always `true` |
| `recurrence_key` | str | `recurrence:v1:{owner_drift_bucket}\|{category}\|{field_path}\|{investigate_first}` |
| `recurrence_owner` | str | from `primary_owner` or owner drift bucket |
| `recurrence_status` | str | `active` \| `retired` (input explicit only) |
| `input_status` | str \| null | raw status from classification row |
| `scenario_id`, `turn_index`, `category`, `primary_owner`, `owner_drift_bucket`, `field_path`, `investigate_first` | various | copied from failure classification |

**Aggregated history** (`aggregate_recurrence_history`):

| Field | Type | Notes |
|---|---|---|
| `schema_version`, `report_only`, `advisory_only` | | envelope |
| `total_rows` | int | input row count |
| `unique_recurrence_count` | int | distinct keys |
| `recurrences` | list | per-key: `occurrence_count`, `first_seen_index`, `last_seen_index`, `owner`, `status`, `categories`, `field_paths`, `affected_scenarios`, `latest_investigate_first` |

**Summary** (`build_recurrence_summary`): same entries with derived `status`: `active` (≥2 occurrences + active input), `watch` (single event), `retired` (explicit retired/deprecated).

**Validation:** unit tests in `tests/test_replay_bug_class_recurrence.py`, writer tests in `tests/test_failure_dashboard_report.py`, manifest policy test in `test_protected_replay_manifest_documents_cycle_ay_recurrence_policy`. No JSON Schema file.

#### Runtime lineage recurrence — authority: `game/runtime_lineage_telemetry.py`

| Field | Type | Notes |
|---|---|---|
| `recurrence_key` | str | `{event_kind}:{stage}:{owner}:{kind_or_path_token}` |
| Summary `by_recurrence_key` | dict[str, int] | per-run frequency |
| Summary `recurring_events` | list | keys with count > 1 |

Validated by `tests/test_runtime_lineage_telemetry.py`, `tests/test_run_scenario_spine_validation.py`, golden replay lineage sections.

#### Fallback recurrence (BP7) — authority: `tools/fallback_recurrence.py`

Consumes BP5 history snapshots. Entity rows include `snapshot_appearances`, `classification` (`transient`/`recurring`/`persistent`/`dominant`), timestamps. Validated by `tests/test_fallback_recurrence.py`.

#### BP5 history snapshot — authority: `tools/fallback_incidence_trends.py`

```json
{ "schema_version": 1, "snapshots": [ { "timestamp", "artifact_source", "eligible_turn_count", "fallback_turn_count", "top_fallback_kinds", ... } ] }
```

Append API: `append_snapshot`, `append_snapshot_to_history`. Validated by `tests/test_fallback_incidence_trends.py`.

---

## Current Protected Replay Run Sources

### Enumeration

- **Manifest:** `docs/testing/protected_replay_manifest.md` — `PROTECTED` scenarios with pytest node IDs and reproduction commands.
- **Registry:** `tests/replay_governance_registry.py` — drift category governance traceability.
- **Fixtures:** `data/validation/scenario_spines/frontier_gate_long_session.json`, golden replay seed helpers in `tests/helpers/golden_replay*.py`.

### Execution

- **Primary suite:** `tests/test_golden_replay.py` (and decomposed modules: `test_golden_replay_*.py`).
- **CI:** `.github/workflows/convergence-checks.yml` → `python -m pytest -m golden_replay -q`.
- **Projection:** `tests/helpers/golden_replay_projection.py` → `project_turn_observation`.

### Recording (in-memory, session-scoped)

| Mechanism | Location | Persists across runs? |
|---|---|---|
| Protected failure rows | `failure_dashboard_report.record_protected_replay_failure` | No — module globals cleared per session |
| Failure dashboard rows | `record_failure_dashboard_rows` | No |
| Rerun drift scorecards | `record_rerun_drift_scorecard` | No |
| Long-session stability scorecards | `record_long_session_stability_scorecard` | No |

### Summarization / emission

| Trigger | Writer | Artifacts |
|---|---|---|
| `pytest_sessionfinish` + `exitstatus != 0` | `write_protected_replay_failure_report_if_present` | `replay_failure_report.md`, plus hotspot + risk (+ bug recurrence via risk writer) |
| `pytest_sessionfinish` + success + `--write-rerun-drift-scorecard` | `write_rerun_drift_scorecard_artifacts` | rerun scorecard, longitudinal, hotspots, trends, risk, bug recurrence |
| Opt-in `--write-failure-dashboard` | `write_failure_dashboard_artifact` | `audits/failure_dashboard_latest.md` |
| CI failure upload | GitHub Actions | `protected-replay-failure-report` artifact (markdown only, not committed) |
| Manual BP tools | `tools/fallback_incidence_trends.py`, `tools/fallback_recurrence.py`, etc. | golden_replay JSON/MD reports |

### Manifest comparison

- `tools/refresh_protected_replay_manifest.py --check` validates generated field-path section against `PROTECTED_OBSERVATION_FIELDS`.
- No automated “run history vs manifest” comparator exists.

### Historical protected replay data already in repo

| Source | Format | Usable for recurrence backfill? |
|---|---|---|
| `artifacts/golden_replay/replay_failure_report.md` | Markdown table | **Partial** — one classified failure with scenario, field, category, owners; not structured JSON; no recurrence_key precomputed |
| `artifacts/golden_replay/bug_recurrence_history.json` | JSON | **No** — empty envelope only |
| `audits/replay_failure_corpus.md` | Markdown probe matrix | **Partial** — synthetic classifier scenarios, not timestamped run events |
| `docs/archive/dead_governance/.../golden_replay_baseline_*.md` | Archived docs | **Low** — historical narrative, not machine-ingestible history |
| Scenario-spine artifacts under `artifacts/scenario_spine_validation/` | JSON per run (when present) | **Partial** — runtime lineage summaries per branch, different recurrence key space |
| CI uploaded failure reports | External | **Yes if retrieved** — same shape as `replay_failure_report.md` |

---

## Population Gap

| Field / capability | Current State | Source Exists? | Likely Source | Backfill Required? | Notes |
|---|---|---|---|---|---|
| `bug_recurrence_history.recurrences[]` | Empty in committed artifact | Partial | Protected failure classifications, rerun scorecard owner drift rows, failure dashboard probes | **Yes** | Writer overwrites from **current session only**; no append log |
| `bug_recurrence_history.summary[]` | Empty | Derived | Same as above | **Yes** | Computed from recurrences |
| `recurrence_key` (bug-class) | Computed on demand | Yes | `owner_drift_bucket`, `category`, `field_path`, `investigate_first` on classification rows | No for formula; **Yes for stored events** | Formula tested; no event store |
| `occurrence_count` / `first_seen_index` | Works in unit tests | No committed multi-run data | Repeated failures across CI/local runs | **Yes** | Indexes are session-local enumeration, not run timestamps |
| `status` (`active`/`watch`/`retired`) | Logic exists | Partial | Explicit input or occurrence count | **Yes** | Cannot reach `active` without ≥2 events in history |
| Runtime lineage `recurring_events` | Per-run only in reports | Yes (ephemeral) | `runtime_lineage_events` on observed turns | Optional | Different key namespace; not merged into AY history today |
| `fallback_incidence_history.snapshots` | Empty | Mechanism yes | BP1 reports from golden replay / scenario-spine runs | **Yes** | `append_snapshot_to_history` exists but never populated in repo |
| BP7 entity recurrence | `no_history` | Depends on BP5 | BP5 snapshots | **Yes** | Parallel track to AY |
| `fallback_risk_history.snapshots` | Placeholder | Partial | BP8 risk scoring runs | **Yes** | One empty snapshot committed |
| `owner_drift_longitudinal.total_runs` | 0 | Partial | Rerun scorecard history | **Yes** | Session-scoped scorecard recording |
| **Regression Recurrence Rate** (BQ goal) | **Not implemented** | Partial proxies | Retired keys reappearing; remediation `recurrence_returned_after_closure`; portfolio `regression_rate` | **Yes** | Needs definition + numerator/denominator over populated AY history |
| Recurrence **trends** over time | Not for bug-class | Partial (BP5/BP7) | Time-series of snapshots or appended events | **Yes** | AY has no timestamped event list |

### Root cause

Bug-class recurrence follows a **replace, don’t append** model:

```text
write_owner_drift_risk_artifacts(rows)
  → write_bug_recurrence_history_artifacts(rows)
    → aggregate_recurrence_history(recurrence_rows(rows))  # current rows only
    → overwrite bug_recurrence_history.json
```

Contrast with BP5, which has an explicit append-only persistence layer:

```text
append_snapshot_to_history(path, snapshot)  # preserves prior snapshots
```

Protected replay CI runs do **not** opt into scorecard/dashboard flags, so on success **no recurrence artifacts are written**. On failure, only the failure report markdown is uploaded; bug recurrence JSON is written locally during the failing session but the committed repo copy remains the empty placeholder.

---

## Backfill Candidates

| Candidate Artifact | Format | Stability | Pros | Risks |
|---|---|---|---|---|
| `artifacts/golden_replay/replay_failure_report.md` | Markdown | Medium — one committed snapshot | Real protected failure with classification columns; reproducible scenario/node | Not JSON; must parse; single event → `watch` not `active`; no run timestamp |
| `audits/replay_failure_corpus.md` | Markdown table | High — controlled discovery doc | Covers representative failure modes; maps to classifier categories | Synthetic probes, not actual run log; no turn/scenario IDs for all rows |
| `tests/test_failure_dashboard_controlled_failures.py` fixtures | In-test rows | High — deterministic | Exercises full classification → recurrence pipeline | Not committed as artifacts; would need export script |
| `tests/test_failure_dashboard_report.py` recurrence tests | Python fixtures | High | Already models multi-event same-key → `active` | Test-only; manual seed for backfill |
| Golden replay rerun scorecards (opt-in) | JSON (not committed by default) | High when generated | Rich `owner_drift_classifications`; feeds `classification_rows_from_scorecards` | Requires `--write-rerun-drift-scorecard`; successful-run bias |
| BP1 incidence from golden replay turns | JSON via `tools/fallback_incidence_report.py` | High — deterministic replay | Feeds BP5/BP7 append chain; repo already has BP5 append tests | Different recurrence semantics (fallback entities, not bug-class keys) |
| Scenario-spine `runtime_lineage_summary.json` | JSON | Medium | Lineage recurrence keys already aggregated | Different key space; advisory lane; path varies by timestamp |
| CI `protected-replay-failure-report` uploads | Markdown | Medium | Real failure history across merges | Not in repo; manual collection needed |
| `fallback_remediation_registry.json` + risk history | JSON | Low today | Supports remediation regression narrative | Registry/history largely empty placeholders |

**Preferred backfill path for BQ (bug-class track):** implement append-only **event log** (mirror BP5), then seed from:

1. Parsed `replay_failure_report.md` failure table rows → classification-shaped dicts → `recurrence_rows`.
2. Optional export of controlled failure probe rows from tests (deterministic, test-protected).

---

## Tests / Protection Points

| Test File | Current Coverage | BQ Relevance | Suggested Addition |
|---|---|---|---|
| `tests/test_replay_bug_class_recurrence.py` | Key derivation, aggregation, status rules, manifest policy | **Primary** | Append/load history round-trip; timestamped event ordering; backfill idempotency |
| `tests/test_failure_dashboard_report.py` | Writer JSON/MD, empty state, watch/retired rendering | **Primary** | Assert append mode preserves prior events; integration with `write_owner_drift_risk_artifacts` |
| `tests/test_replay_drift_risk.py` | Risk payload; calls risk writer (side-effect recurrence) | Medium | Verify bug recurrence artifact emitted alongside risk when rows present |
| `tests/test_golden_replay_protected_bridge.py` | Protected failure recording → report | Medium | Assert recurrence append on simulated protected failure session |
| `tests/test_failure_classifier.py` | Classification rows feeding dashboard | Medium | Contract test: classification fields required for recurrence_key |
| `tests/test_failure_dashboard_controlled_failures.py` | Opt-in failure probes | Medium | Optional golden export of probe rows for backfill fixture |
| `tests/test_fallback_recurrence.py` | BP7 entity classification | Low (parallel track) | Snapshot fixture for non-empty BP7 after BP5 backfill |
| `tests/test_fallback_incidence_trends.py` | BP5 append-only persistence | **Pattern reference** | Reuse append semantics as model for AY event log tests |
| `tests/test_runtime_lineage_telemetry.py` | Lineage recurrence_key shape | Low | Cross-reference doc only unless lineage events feed AY |
| `tests/test_replay_governance_registry.py` | Manifest traceability | Low | No change unless recurrence policy expands |
| `tests/test_replay_drift_longitudinal.py` | Owner drift across scorecards | Medium | Document relationship to recurrence row expansion |

**Coverage gap:** No test asserts committed `artifacts/golden_replay/bug_recurrence_history.json` contains non-zero history. No test covers cross-session persistence.

---

## Recommended Implementation Slices

### BQ1 — Append-only bug recurrence event log (schema + helpers)

**Goal:** Move from session overwrite to persisted event history (BP5 pattern).

**Likely files:**

- `tests/helpers/replay_bug_recurrence.py` — add `load_recurrence_event_log`, `append_recurrence_events`, `aggregate_recurrence_history_from_log`
- `tests/helpers/failure_dashboard_report.py` — switch `write_bug_recurrence_history_artifacts` to append+reaggregate
- `tests/test_replay_bug_class_recurrence.py` — append/idempotency tests

**Scope:** Reporting-only; no replay pass/fail changes.

---

### BQ2 — Wire protected replay failure path to append events

**Goal:** On protected failure report write, append classification rows with run metadata (`timestamp`, `command`, `test_node_id`).

**Likely files:**

- `tests/helpers/failure_dashboard_report.py` — `write_protected_replay_failure_report_if_present`, `write_owner_drift_risk_artifacts`
- `tests/conftest.py` — optional: document env flag for append-on-success
- `tests/test_golden_replay_protected_bridge.py`

**Scope:** Only extends reporting when failures are already recorded.

---

### BQ3 — Deterministic backfill from existing artifacts

**Goal:** Populate initial history without changing replay semantics.

**Likely files:**

- New `tools/backfill_bug_recurrence_history.py` (or similar)
- Input: `artifacts/golden_replay/replay_failure_report.md`, optional test fixture export
- Output: updated `artifacts/golden_replay/bug_recurrence_history.json` (+ md regen)

**Scope:** One-time/maintenance script; review before commit.

---

### BQ4 — Define Regression Recurrence Rate metric

**Goal:** Make BQ’s named KPI computable from populated history.

**Likely files:**

- `tests/helpers/replay_bug_recurrence.py` or new `tests/helpers/replay_recurrence_metrics.py`
- `tests/helpers/failure_dashboard_report.py` — render metric in markdown summary section
- `docs/testing/protected_replay_manifest.md` — document definition (report-only)

**Suggested definition (discovery recommendation):**  
`regression_recurrence_rate = (recurrence keys with status transition watch→active or retired→active in window) / (recurrence keys observed in window)` — refine during implementation against operator intent.

---

### BQ5 — Recurrence trend section in operator reports

**Goal:** Surface time-bucketed counts (weekly/per-run) from event log.

**Likely files:**

- `tests/helpers/replay_bug_recurrence.py` — `build_recurrence_trend_summary`
- `tests/helpers/failure_dashboard_report.py` — extend `render_bug_recurrence_history_markdown`
- `tests/test_failure_dashboard_report.py`

---

### BQ6 — CI history retention (optional, separate)

**Goal:** Upload `bug_recurrence_history.json` on protected replay failure (parallel to K3B markdown upload).

**Likely files:**

- `.github/workflows/convergence-checks.yml`
- `docs/audits/cycle_k_block_k3b_failure_artifact_retention_2026-05-26.md` (doc cross-ref)

**Note:** Does not replace repo-backed history; enables manual merge-back of CI events.

---

## Files Needed From User

These are **not present** in the repo (or not structured for ingestion) but would accelerate BQ:

| Item | Why it helps |
|---|---|
| Historical CI `protected-replay-failure-report` artifacts | Multiple real failure events across merges → `active` recurrence keys |
| Any local `bug_recurrence_history.json` from failing golden replay runs with non-zero rows | Direct seed without parsing markdown |
| Rerun drift scorecard JSON from `--write-rerun-drift-scorecard` successful runs | Expands classification rows via `owner_drift_classifications` |
| BP1 fallback incidence JSON reports (if generated locally) | Populates BP5/BP7 parallel track |
| Operator definition preference for **Regression Recurrence Rate** | Term not found in codebase; confirm whether KPI targets bug-class AY, remediation BP10, or both |
| `artifacts/scenario_spine_validation/**/runtime_lineage_summary.json` from recent runs | Optional lineage-key backfill (secondary to AY) |

---

## Validation Performed

Discovery-only work:

- Repository-wide search for recurrence, protected replay, replay history, manifest, and related symbols
- Read of core helpers, tools, committed artifacts, manifest, CI workflow, and representative tests
- **No pytest executed** (no code or test changes; markdown artifact only)
