# Replay CI Promotion

## Change Summary

Cycle K Block K2 promotes the protected golden replay lane from documented acceptance policy to an enforced CI check.

The protected replay declaration remains in `docs/testing/protected_replay_manifest.md`. This block changes only CI wiring and documentation:

- Adds a required marker-selected golden replay pytest step to `.github/workflows/convergence-checks.yml`.
- Updates `docs/convergence_ci_inventory.md` to list protected replay as a hard-fail CI check.
- Updates `tests/README_TESTS.md` to state the acceptance purpose, failure meaning, and developer reproduction command.

No replay scenario, assertion, fixture, production module, or content-lint behavior is changed.

## Workflow Changes

### Existing CI Audit

| Workflow / Job | Existing Hard-Fail Checks | Existing Informational Checks | Existing Pytest Points |
|---|---|---|---|
| `.github/workflows/convergence-checks.yml` / `convergence-checks` | Evaluator convergence closeout; evaluator boundary slice; FE-C2 boundary; gate convergence closeout; validation coverage audit guards; test ownership registry; strict validation-layer, final-emission, and validation-coverage audits. | Architecture summary; realization layer; realization provenance; C1 narration seam; UI mode separation, each with `continue-on-error: true`. | Six hard-fail pytest steps before this block. |
| `.github/workflows/content-lint.yml` / `content-lint` | Planner convergence static audit; test ownership registry; report summarization/upload after observational lint. | Content lint Phase 1 uses `continue-on-error: true`; optional warning gate is disabled with `if: false`. | `python -m pytest tests/test_ownership_registry.py -q`. |

### Smallest Safe Insertion Point

Protected replay is inserted in the existing `convergence-checks` job, directly under the established `# --- Hard-fail (blocking) ---` section after dependency installation and before the existing convergence pytest slices.

This is the smallest safe insertion point because it:

- Reuses the workflow already responsible for required validation checks.
- Reuses its Python/dependency installation exactly as configured.
- Does not add duplicate setup time in a separate job.
- Does not alter planner/content-lint ownership or any existing validation command.

Added step:

```yaml
- name: Pytest - protected golden replay acceptance
  run: python -m pytest -m golden_replay -q
```

## Replay Command

Required CI command:

```bash
python -m pytest -m golden_replay -q
```

The marker-based invocation is deliberate. `pytest.ini` registers `golden_replay`, and future protected replay modules may join that marker-selected acceptance lane without a subsequent workflow command edit.

## Failure Semantics

Protected replay is a blocking CI condition.

- The added step does not set `continue-on-error: true`.
- Pytest returns a nonzero exit code when a collected golden replay test fails or cannot run.
- GitHub Actions propagates a nonzero `run:` step exit code as a failed step and failed `convergence-checks` job.
- A failing protected replay lane therefore blocks repository acceptance in the same manner as the existing required convergence pytest checks.

The current `golden_replay` marker includes the protected scenarios and co-located golden replay support-contract tests already present in `tests/test_golden_replay.py`. This block does not change that collection boundary.

## Developer Reproduction

Run the same marker-selected command from the repository root:

```bash
python -m pytest -m golden_replay -q
```

On Windows/Codex where `python` is not on `PATH`, the equivalent established local form is:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -m golden_replay -q
```

A failure means an acceptance-protected replay scenario or currently co-located golden replay contract check has failed. Scenario ownership and per-scenario reproduction commands are documented in `docs/testing/protected_replay_manifest.md`.

## Validation

Static validation performed for this block:

- Confirmed `golden_replay` is registered in `pytest.ini`.
- Confirmed the workflow uses `python -m pytest -m golden_replay -q`.
- Confirmed the new workflow step has no `continue-on-error` override.
- Confirmed `.github/workflows/content-lint.yml` is not changed by this block.
- Collected the marker-selected replay lane locally to confirm that the command resolves collected tests (`32` collected).
- Ran the promoted marker-selected replay command locally; it completed successfully (`exit code 0`, `[100%]`).
- Inspected the added YAML step structure and ran `git diff --check`; the new mapping is a standard sibling `name`/`run` step under the existing `steps` list and the patch has no whitespace errors.

No YAML parser package is installed in the available repo/bundled runtimes, so no parser-backed workflow validation was available locally. These checks and the local pytest run are not a claim that GitHub Actions has run.

## Remaining Replay Promotion Work

- **K3 Failure Artifact Ergonomics**: make required replay failures produce immediately useful CI artifacts/reproduction detail.
- **K4 Drift Threshold Policy**: decide which existing drift/lineage metrics should become bounded acceptance policy.
- **K5 Longitudinal Replay Decision**: decide whether a game-level scenario-spine or N1 longitudinal lane should become an additional required replay gate.
