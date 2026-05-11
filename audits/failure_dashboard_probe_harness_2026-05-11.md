# Failure Dashboard Probe Harness - 2026-05-11

## Controlled Cases Added

- Wrong speaker -> `speaker`
- Forced fallback source -> `fallback`
- Sanitizer leakage -> `sanitizer`
- Unexpected response-type repair -> `emission`
- Missing route metadata with raw absent -> `route`
- Missing route metadata with raw present -> `projection`
- Semantic mutation -> `semantic_mutation`
- Unknown post-gate mutation -> `emission` with `emission.post_gate_mutation_unknown` evidence

## Opt-In Mechanism

- Marker: `failure_dashboard_probe`
- Direct file run: `tests/test_failure_dashboard_controlled_failures.py`
- Optional environment override for full-suite collection: `ASHEN_RUN_FAILURE_DASHBOARD_PROBES=1`

Normal full-suite runs skip these probes unless one of those opt-in paths is used.

## Generated Artifact

- Sample probe dashboard: `audits/failure_dashboard_probe_sample.md`
- Latest dashboard can be generated from probes with:

```powershell
python -m pytest -m failure_dashboard_probe -q --write-failure-dashboard
```

## Verification Commands

```powershell
python -m pytest tests/test_failure_classifier.py -q
python -m pytest tests/test_golden_replay.py -q
python -m pytest -m golden_replay -q
python -m pytest tests/test_failure_dashboard_controlled_failures.py -q
python -m pytest -m failure_dashboard_probe -q
python -m pytest -m failure_dashboard_probe -q --write-failure-dashboard
```

Local shell note: `python` is not on PATH in this workspace, so the bundled Codex runtime Python was used for equivalent commands.

## Normal Replay Status

Normal golden replay remains passing. The controlled failures are synthetic replay-shaped probes and do not change the real golden replay baseline or runtime behavior.
