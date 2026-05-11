# Failure Dashboard Contract Lock - 2026-05-11

## Added

- Contract registry: `tests/failure_classification_contract.py`
- Row validation helper: `validate_failure_classification_row(...)`
- Contract tests: `tests/test_failure_classification_contract.py`
- Dashboard renderer validation before markdown emission

## Drift Now Prevented

- Unknown failure categories.
- Unknown primary or secondary owners.
- Unknown severities.
- Unknown replay tags unless explicitly prefixed as experimental.
- Missing required classification fields.
- Empty investigation targets.
- Accidental removal of key dashboard markdown diagnostics such as owner, severity, replay tags, and evidence.
- Classifier owner/category constants drifting away from the audit/schema docs without a visible test failure.

## Intentionally Flexible

- `expected` and `actual` values remain flexible because they reflect replay-specific observations.
- `reason` text remains compact and deterministic but is not snapshot-locked.
- Experimental replay tags are allowed with the `experimental:` prefix so future probes can be staged deliberately.
- The audit-doc consistency test is intentionally light; it verifies coverage of taxonomy terms without line-by-line markdown parsing.

## Verification

```powershell
python -m pytest tests/test_failure_classifier.py -q
python -m pytest tests/test_failure_classification_contract.py -q
python -m pytest tests/test_failure_dashboard_controlled_failures.py -q
python -m pytest tests/test_golden_replay.py -q
python -m pytest -m golden_replay -q
python -m pytest -m failure_dashboard_probe -q
```

Local shell note: `python` is not on PATH in this workspace, so the bundled Codex runtime Python was used for equivalent commands.
