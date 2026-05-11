# Cycle Track B Closure

## Status

Complete with caveats.

The Failure Classification Dashboard is operational, deterministic, replay-side, contract-locked, and validated against both passing golden replay and controlled known-bad probes. Remaining caveats are observability limits in existing metadata, not blockers for using the dashboard.

## What was built

- Replay-side failure classifier.
- Deterministic category, owner, severity, and investigation-target routing.
- Precision evidence fields for emission sublayers, repair kind, mutation source, missing-source kind, and sanitizer evidence.
- Markdown dashboard report builder.
- Opt-in latest artifact generation via `--write-failure-dashboard` or `ASHEN_WRITE_FAILURE_DASHBOARD=1`.
- Golden replay integration that attaches classification rows additively.
- Controlled known-bad probe harness behind `failure_dashboard_probe`.
- Probe sample artifact.
- Contract registry and row validation.
- Contract tests and light dashboard shape locks.
- README documentation and audit trail.

## What is now protected

- Categories cannot drift silently.
- Owners cannot drift silently.
- Severities cannot drift silently.
- Replay tags cannot drift silently unless explicitly experimental.
- Required classification fields cannot disappear silently.
- Dashboard markdown cannot silently lose key diagnostic columns.
- Controlled known-bad cases protect expected classification behavior.
- Normal golden replay remains isolated from intentionally failing probes.

## How to use it

Run normal golden replay:

```powershell
python -m pytest -m golden_replay -q
```

Generate the latest passing replay dashboard:

```powershell
python -m pytest -m golden_replay -q --write-failure-dashboard
```

Run controlled known-bad probes:

```powershell
python -m pytest -m failure_dashboard_probe -q
```

Generate a dashboard from known-bad probes:

```powershell
python -m pytest -m failure_dashboard_probe -q --write-failure-dashboard
```

Update the taxonomy by editing `tests/failure_classification_contract.py`, then update classifier rules and contract tests together.

## Verification

Final verification run:

- `tests/test_failure_classifier.py`: 24 passed.
- `tests/test_failure_classification_contract.py`: 11 passed.
- `tests/test_failure_dashboard_controlled_failures.py`: 9 passed.
- `tests/test_golden_replay.py`: 12 passed.
- `python -m pytest -m golden_replay -q`: 12 passed.
- `python -m pytest -m failure_dashboard_probe -q`: 9 passed.
- `python -m pytest -m golden_replay -q --write-failure-dashboard`: 12 passed.
- `python -m pytest -m failure_dashboard_probe -q --write-failure-dashboard`: 9 passed.

Final artifact state:

- `audits/failure_dashboard_latest.md` says `No replay failures classified.`
- `audits/failure_dashboard_probe_sample.md` contains known-bad classified rows.

## Remaining caveats

- Final-emission sublayer attribution remains bounded by existing metadata.
- Sanitizer run summaries are only visible when existing sanitizer context/debug metadata reaches replay payloads.
- Raw-present versus runtime-missing diagnostics are deterministic but limited to replay-visible raw and normalized surfaces.
- Evaluator/report alignment is not yet a first-class dashboard lane.
- The dashboard is intentionally not a live runtime monitor, repair system, evaluator, or AI judge.

## Recommended next cycle

Proceed to final-emission sublayer telemetry cleanup if the next priority is sharper mutation locality. That work should focus on making existing FEM/stage-diff sublayer stamps more consistent without changing behavior.

Secondary candidates:

- Sanitizer projection hardening, to make sanitizer run summaries consistently visible in replay rows.
- Evaluator/report alignment, to fold advisory evaluator output into the same report shape without making it policy.
- The next planned cycle track, if dashboard locality is sufficient for current debugging needs.
