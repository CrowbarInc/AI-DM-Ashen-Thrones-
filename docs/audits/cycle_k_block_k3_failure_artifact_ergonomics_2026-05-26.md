# Replay Failure Artifact Ergonomics

## Current Failure Experience

Protected replay is enforced by the hard-fail CI command:

```bash
python -m pytest -m golden_replay -q
```

The current failure experience is useful at the assertion site, but incomplete as an acceptance-gate diagnostic workflow. The protected scenarios in `tests/test_golden_replay.py` generally use `assert_golden_turn_observation(...)` and supply `format_golden_replay_debug(...)` context. A failing assertion therefore reports its failed field, expected value, actual value, mismatch reason, scenario id, and projected turn telemetry in the pytest console log.

The repository also has a richer classification/dashboard path. `classify_golden_drift(...)` can create drift buckets and classification rows; `tests/helpers/failure_classifier.py` assigns category, severity, owner, and investigation target; `tests/helpers/failure_dashboard_report.py` can render `audits/failure_dashboard_latest.md`. That path is opt-in and is not automatically invoked when an ordinary protected scenario assertion fails.

| Surface | Path | Current Behavior | Visible In Current Replay CI |
|---|---|---|---|
| Acceptance command | `.github/workflows/convergence-checks.yml` | Runs `python -m pytest -m golden_replay -q` as a blocking step | Yes |
| Assertion failure text | `tests/helpers/golden_replay.py` | Emits reason, field path, expected value, actual value, and caller-provided debug context | Yes, when a protected assertion fails |
| Replay debug context | `tests/helpers/golden_replay.py` | Emits scenario/turn identifiers plus routing, speaker, emission, fallback, sanitizer, and runtime lineage fields | Yes, for tests passing this context |
| Drift classification | `tests/helpers/golden_replay.py`, `tests/helpers/failure_classifier.py` | Builds exact/structural/semantic drift and diagnostic owner classifications | Not for ordinary protected assertion failures |
| Dashboard artifact | `tests/helpers/failure_dashboard_report.py`, `tests/conftest.py` | Writes `audits/failure_dashboard_latest.md` only when enabled with the option or environment flag | No |
| CI artifact upload | `.github/workflows/convergence-checks.yml` | No replay artifact generation or upload step | No |

Information lost during current CI execution is not the raw failing observation: it is the structured interpretation of that observation. CI does not retain a canonical replay failure artifact with category, severity, likely owner, investigation target, or a reproduction block.

## Available Signals

Signal visibility is evaluated for a protected replay failure under the current CI command, not for controlled diagnostic probe tests.

| Failure Signal | Current Source | Status In Current CI Failure | Notes |
|---|---|---|---|
| Scenario id | `format_golden_replay_debug(...)`; pytest node id | Visible | Included in debug context for the end-to-end protected scenarios and exposed through the failed test node. |
| Field path | `_format_expected_failure(...)` | Visible | Direct assertion helper emits `field_path`. |
| Expected value | `_format_expected_failure(...)` | Visible | Direct assertion helper emits `expected`. |
| Actual value | `_format_expected_failure(...)` | Visible | Direct assertion helper emits `actual`, including `<missing>`. |
| Structural drift bucket | `classify_golden_drift(...)` | Available but hidden | Classifier can assign this bucket, but ordinary protected assertions do not call it on failure. |
| Semantic drift bucket | `classify_golden_drift(...)` | Available but hidden | Predicate failures such as scaffold leakage can be bucketed, but CI gets the assertion form only. |
| Exact drift bucket | `classify_golden_drift(...)` | Available but hidden when configured; otherwise unavailable | Exact prose comparison is explicitly opt-in through `exact_text`. |
| Fallback owner/source/family | Observed replay projection; debug context; dashboard rows | Visible where projected in debug context | Owner interpretation is not consolidated into one failure summary. |
| Sanitizer lineage | Observed replay projection; debug context; classification row | Visible where projected in debug context | Fields are present, but no failure-focused sanitizer summary is generated. |
| Runtime lineage | Observed replay projection; debug context; dashboard lineage summary | Visible as raw debug context; summary hidden | Dashboard can aggregate frequencies only when enabled and events are recorded. |
| Failure category | `classify_replay_failure(...)` | Available but hidden | Not produced for the direct assertion failure path. |
| Severity | `classify_failure_severity(...)` | Available but hidden | Not produced for the direct assertion failure path. |
| Owner classification | `determine_primary_owner(...)`, `determine_secondary_owner(...)` | Available but hidden | Not produced for the direct assertion failure path. |
| Primary investigation target | `build_investigation_target(...)` | Available but hidden | Not produced for the direct assertion failure path. |
| Reproduction command | Existing documentation | Unavailable in failure output | A developer must know or find the command separately. |
| Artifact location | Opt-in dashboard writer | Unavailable in current CI output | Current CI neither generates nor uploads a replay artifact. |

### Failure-Type Inventory

| Replay Failure Type | Existing Signal | Normal CI Console | Opt-In Dashboard Capability | Remaining Gap |
|---|---|---|---|---|
| Structural invariant mismatch | Field path, expected/actual, full debug observation | Visible | Category/owner/severity available if drift classification ran | Protected assertion failure is not automatically classified. |
| Semantic text or scaffold drift | Failing text/scaffold predicate and observation | Visible | Can classify sanitizer or semantic mutation ownership | No canonical failure row or owner in normal CI. |
| Exact text drift | Hash comparison in `classify_golden_drift(...)` | Unavailable unless a test invokes exact comparison | Available only for opt-in exact expectations | Exact drift is intentionally not a general protected replay invariant. |
| Fallback ownership/path mismatch | Opening/sealed/sanitizer fallback fields and runtime evidence | Visible in applicable debug contexts | Can assign fallback owner and investigation target | No focused fallback summary in the blocking run. |
| Sanitizer lineage mismatch | Sanitizer lineage fields in replay observation | Visible in debug context | Can classify sanitizer ownership | No automatic artifact classification for protected assertion failures. |
| Runtime lineage anomaly | Runtime lineage events projected by replay | Visible as raw event data when debug context is emitted | Dashboard can aggregate recurrence and gate/fallback frequency | No CI artifact and no concise per-failure lineage summary. |
| Projection or missing observation | `unavailable` and raw-signal evidence | Visible for assertion-level availability failure | Can distinguish projection/normalization/runtime absence | Ownership distinction remains hidden without classifier execution. |

## Missing Signals

- The blocking protected assertion path and the dashboard classification path are separate. A protected failure can fail CI while producing no classification row.
- The current CI invocation does not enable `--write-failure-dashboard`, and the workflow has no replay upload step.
- The dashboard writer records only rows passed through classification. Simply enabling the writer would not guarantee a useful artifact for the ordinary protected failures.
- Normal CI output has no standardized failure category, severity, primary owner, secondary owner, or `investigate_first` value.
- The assertion output does not provide a ready-to-run scenario-specific reproduction command or identify an artifact location.
- Debug context is comprehensive but verbose; it does not summarize the most relevant fallback and runtime lineage facts for the failed invariant.
- Exact drift is deliberately opt-in and should not be represented as generally available acceptance evidence.

## Proposed Artifact Structure

The canonical replay failure artifact should be a single Markdown report generated for a failed protected replay run:

```text
artifacts/golden_replay/replay_failure_report.md
```

This should be a reporting surface only. It must be populated from existing observed turn data and existing classification rules, without changing scenario inputs, protected assertions, failure thresholds, or pytest exit behavior.

| Artifact Field | Existing Source Or Derivation |
|---|---|
| Replay scenario | `scenario_id` from observed turn/result and failed pytest node |
| Failure category | `classify_replay_failure(...)` |
| Failed invariant | Assertion field path plus mismatch reason |
| Expected value | Existing assertion/drift row expected value |
| Actual value | Existing assertion/drift row actual value |
| Owner classification | Existing primary and secondary owner classification |
| Primary investigation target | Existing `build_investigation_target(...)` result |
| Runtime lineage summary | Existing runtime lineage events and `build_runtime_lineage_summary(...)` |
| Fallback summary | Existing fallback family, authorship source, owner bucket, and relevant sanitizer/opening fallback fields |
| Replay reproduction command | Standard commands below, including failed node id |
| Artifact location | Fixed canonical path above |

Recommended report layout:

1. Run summary: command, pytest status, generated timestamp, artifact path.
2. Failure table: scenario, test node id, failed invariant, category, severity, expected, actual, primary owner, investigate first.
3. Evidence per scenario: route/speaker/final emission fields, fallback summary, sanitizer summary, runtime lineage summary, unavailable fields.
4. Reproduce locally: scenario-specific command followed by marker-wide command.

The existing `audits/failure_dashboard_latest.md` is a useful diagnostic precursor, but it is currently opt-in, latest-run oriented, and does not reliably receive ordinary protected assertion failures. Promotion should treat the proposed failure-run report as the CI-facing canonical artifact and reuse the existing dashboard schema/rendering logic where practical.

## CI Integration Recommendation

Current generation path:

- `--write-failure-dashboard` or `ASHEN_WRITE_FAILURE_DASHBOARD=1` enables a `pytest_sessionfinish` write to `audits/failure_dashboard_latest.md`.
- The protected CI gate does not set either opt-in mechanism.
- The protected CI workflow does not upload replay artifacts.
- `content-lint.yml` demonstrates an existing repository pattern for `actions/upload-artifact@v4`, but it applies only to content-lint output today.

Recommendation: **upload the canonical replay failure artifact only on failure**.

Rationale:

- Passing runs do not require preserved diagnostic content.
- Failure-only artifacts keep the acceptance signal focused and avoid repeatedly publishing an empty or “no failures classified” report.
- A failing replay run is precisely when a structured owner/investigation summary saves developer time.

Prerequisite for CI wiring: add a reporting bridge in a later implementation block so protected assertion failures create classification-backed artifact content before the upload step runs. Enabling upload alone, or merely enabling the existing dashboard option, does not close the failure-path gap.

No workflow behavior is changed in this block.

## Developer Reproduction Standard

Marker-wide protected replay reproduction:

```bash
python -m pytest -m golden_replay -q
```

Scenario-specific reproduction format:

```bash
python -m pytest tests/test_golden_replay.py::<failed_test_node_id> -q
```

Example for an end-to-end protected scenario:

```bash
python -m pytest tests/test_golden_replay.py::test_golden_replay_directed_npc_question_structural_invariants -q
```

Existing opt-in dashboard command for diagnostic investigation:

```bash
python -m pytest -m golden_replay -q --write-failure-dashboard
```

Current opt-in output location:

```text
audits/failure_dashboard_latest.md
```

The future canonical failure report should print both reproduction commands and its artifact path in the CI log when a protected replay failure occurs.

## Implementation Recommendation

Implement failure artifact ergonomics as a later additive reporting block, before adjusting workflow artifact upload:

| Order | Recommendation | Purpose | Guardrail |
|---:|---|---|---|
| 1 | Create a reporting adapter for protected assertion failures | Transform the existing failed invariant plus observed turn into the existing classification schema | Preserve the existing assertion and pytest exit result unchanged. |
| 2 | Render one canonical failure-run report | Consolidate failed invariant, ownership, fallback, sanitizer, runtime lineage, and reproduction data | Write reporting output only; do not change replay selection or invariants. |
| 3 | Wire failure-only CI upload | Preserve the artifact on failing protected replay runs | Keep `python -m pytest -m golden_replay -q` a hard-fail acceptance check. |
| 4 | Consider longitudinal use in K4/K5 | Let threshold and trend policy consume structured reports later | Do not introduce threshold policy as an ergonomics side effect. |

The highest-value change is the adapter in step 1. Without it, the repository already has diagnostic pieces but not a reliable artifact for the failures that now block acceptance.

## Validation

Validation command run from the repository root:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -m golden_replay -q --tb=short --basetemp=codex_pytest_tmp_cycle_k_k3_run
```

Result: **PASS** (`32` tests passed; no collection failures).

The command intentionally did not enable `--write-failure-dashboard` or `ASHEN_WRITE_FAILURE_DASHBOARD`. A before/after scope check showed no change to `audits/failure_dashboard_latest.md`, confirming the existing artifact logic remains inert on a successful default protected replay run.

## Acceptance Criteria

| Criterion | Result |
|---|---|
| No replay behavior changed | Met: this block adds documentation only. |
| No production code changed | Met: this block adds documentation only. |
| No acceptance policy changed | Met: existing marker-selected CI gate remains unchanged. |
| Failure information inventory completed | Met: visible, hidden, and unavailable signals are mapped above. |
| Artifact design documented | Met: a canonical failure-only Markdown artifact and content contract are specified. |
| Implementation recommendation produced | Met: additive reporting bridge and later failure-only upload are recommended. |
