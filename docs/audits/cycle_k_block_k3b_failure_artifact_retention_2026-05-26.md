# Protected Replay Failure Artifact Retention

## Workflow Change

Block K3B preserves the canonical K3A replay failure report when the required protected replay CI step fails. It changes CI artifact retention and documentation only; replay execution, scenario expectations, classification policy, and production behavior are unchanged.

Updated workflow:

```text
.github/workflows/convergence-checks.yml
```

The existing blocking replay step retains its command and now has a stable step id:

```yaml
- name: Pytest - protected golden replay acceptance
  id: protected_replay
  run: python -m pytest -m golden_replay -q
```

Immediately after that step, the workflow now includes:

```yaml
- name: Upload protected replay failure report
  if: failure() && steps.protected_replay.outcome == 'failure'
  uses: actions/upload-artifact@v4
  with:
    name: protected-replay-failure-report
    path: artifacts/golden_replay/replay_failure_report.md
    if-no-files-found: warn
```

## Artifact Pattern Audit

| Workflow | Existing Artifact Use | Retention Convention | K3B Reuse |
|---|---|---|---|
| `.github/workflows/content-lint.yml` | Uploads `artifacts/content_lint/ci_report.json` | `actions/upload-artifact@v4`, stable artifact name, `if-no-files-found: warn` | Reused action version, stable name, and missing-file warning behavior. |
| `.github/workflows/convergence-checks.yml` before K3B | No artifact upload | None | Added the first failure-only diagnostic upload for this workflow. |

No prior failure-only upload condition was present in the inspected workflows. K3B therefore scopes upload to the specific replay step outcome rather than using a broad job-failure condition.

## Artifact Path

Artifact display name in GitHub Actions:

```text
protected-replay-failure-report
```

Uploaded file path:

```text
artifacts/golden_replay/replay_failure_report.md
```

This path exactly matches the canonical writer introduced by K3A in `tests/helpers/failure_dashboard_report.py`.

## Artifact Behavior

| Situation | Replay Step Status | Upload Step Behavior | Workflow Acceptance Result |
|---|---|---|---|
| Protected replay passes | Success | Skipped | Continues to later required checks. |
| Protected replay fails and report exists | Failure | Uploads `protected-replay-failure-report` | Remains failed because the replay step failed. |
| Protected replay fails and report is absent | Failure | Runs and warns through `if-no-files-found: warn` | Remains failed because the replay step failed. |
| An earlier setup/install step fails | Replay did not fail | Upload does not run because `steps.protected_replay.outcome == 'failure'` is false | Original failing step determines workflow status. |

The upload step cannot make replay advisory. The `python -m pytest -m golden_replay -q` step still has no `continue-on-error`, and its nonzero exit code remains a hard-fail acceptance outcome.

## Documentation Updates

| File | Documentation Added |
|---|---|
| `docs/convergence_ci_inventory.md` | Artifact name, path, failure-only behavior, missing-file warning behavior, and marker-wide reproduction command. |
| `tests/README_TESTS.md` | Developer-facing retrieval description alongside protected replay commands. |

Developer reproduction:

```bash
python -m pytest -m golden_replay -q
```

When a failure occurs in Actions, download the `protected-replay-failure-report` artifact from the failed `convergence-checks` workflow run and inspect `replay_failure_report.md`.

## Validation

Static validation for this block verifies:

- the protected replay command remains `python -m pytest -m golden_replay -q`;
- the replay step has no `continue-on-error`;
- the upload uses `actions/upload-artifact@v4`;
- the upload condition requires `steps.protected_replay.outcome == 'failure'`;
- the artifact path is identical to K3A's `PROTECTED_REPLAY_FAILURE_REPORT_PATH`;
- missing artifact output is warning-only through `if-no-files-found: warn`;
- documentation names the same stable artifact and reproduction command.

Validation performed:

```powershell
rg -n "Pytest - protected golden replay acceptance|id: protected_replay|python -m pytest -m golden_replay -q|Upload protected replay failure report|steps\.protected_replay\.outcome == 'failure'|actions/upload-artifact@v4|protected-replay-failure-report|artifacts/golden_replay/replay_failure_report.md|if-no-files-found: warn|continue-on-error" .github/workflows/convergence-checks.yml
rg -n "PROTECTED_REPLAY_FAILURE_REPORT_PATH|artifacts/golden_replay/replay_failure_report.md" tests/helpers/failure_dashboard_report.py
git diff --check
```

Result: **PASS** for structural/path/scope checks.

A parser-backed YAML validation attempt was made with the available Python environment, but `PyYAML` is not installed (`ModuleNotFoundError: No module named 'yaml'`). No GitHub Actions execution or parser-backed workflow validation is claimed for this local CI wiring change.

## Remaining Replay Work

- K4 Drift Threshold Policy: define how structured replay drift should be interpreted over time.
- K5 Longitudinal Replay Decision: decide trend retention and longitudinal acceptance policy.

## Acceptance Criteria

| Criterion | Result |
|---|---|
| Replay failure artifact uploaded | Met: failure-only upload step targets the K3A report. |
| Upload occurs only on replay failure | Met: condition is keyed to `steps.protected_replay.outcome == 'failure'`. |
| Replay remains hard-fail | Met: the marker-selected pytest step is unchanged and has no error suppression. |
| No replay behavior changes | Met: only CI/documentation files are changed by K3B. |
| No acceptance changes | Met: diagnostics are retained after the existing blocking outcome. |
| Documentation updated | Met: CI inventory and test guide document retrieval and reproduction. |
