# Protected Replay Failure Report

## Run Summary

- Status: `failed`
- Command: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\.venv\Lib\site-packages\pytest\__main__.py -m golden_replay -q --tb=short -o addopts=--basetemp=development/tmp/maintenance_golden --junitxml=development/tmp/github_checkpoint/golden_after.xml`
- Generated at: `2026-10-18T16:31:34Z`
- Artifact location: `artifacts/golden_replay/replay_failure_report.md`
- Classified failures: `1`

## Failure Locator

| Scenario | Source Path | Branch | Turn Index | Turn ID | Failed Invariant | Test Node |
|---|---|---|---:|---|---|---|
| sanitizer_scaffold_leakage | none | none | 0 | none | scaffold_leakage: exact value mismatch | tests/test_golden_replay_structural_invariants.py::test_golden_replay_sanitizer_scaffold_leakage_structural_invariants |

## Failure Table

| Scenario | Test Node | Turn | Failed Invariant | Drift Type | Expected | Actual | Category | Severity | Primary Owner | Secondary Owner | Investigate First | Owner Drift Bucket |
|---|---|---:|---|---|---|---|---|---|---|---|---|---|
| sanitizer_scaffold_leakage | tests/test_golden_replay_structural_invariants.py::test_golden_replay_sanitizer_scaffold_leakage_structural_invariants | 0 | scaffold_leakage: exact value mismatch | semantic_drift | False | True | sanitizer | critical | sanitizer | emission | game/output_sanitizer.py | semantic_drift |

## Classification Summary

- Categories: `sanitizer` (1)
- Primary owners: `sanitizer` (1)


## Owner Drift Breakdown

```
semantic_drift .................. 1
```

## Fallback Summary

| Scenario | Final Source | Fallback Family | Temporal Frame | Opening Authorship | Opening Owner | Sealed Owner | Sanitizer Empty Owner |
|---|---|---|---|---|---|---|---|
| sanitizer_scaffold_leakage | none | none | none | none | unknown-ambiguous | none | none |

## Sanitizer Summary

| Scenario | Mode | Changed | Dropped | Empty Fallback | Empty Owner | Legacy Rewrite | Strict Social Owner |
|---|---|---:|---:|---|---|---|---|
| sanitizer_scaffold_leakage | none | none | none | none | none | none | none |
## Reproduce Locally

### Focused failing tests

```bash
python -m pytest tests/test_golden_replay_structural_invariants.py::test_golden_replay_sanitizer_scaffold_leakage_structural_invariants -q --tb=short
```

### Protected replay lane

```bash
python -m pytest -m golden_replay -q --tb=short
```
