# Protected Replay Failure Report

## Run Summary

- Status: `failed`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py tests/test_co102_live_protected_replay_pipeline.py -q --tb=short`
- Generated at: `2026-06-28T10:45:45Z`
- Artifact location: `artifacts/golden_replay/replay_failure_report.md`
- Classified failures: `1`

## Failure Locator

| Scenario | Source Path | Branch | Turn Index | Turn ID | Failed Invariant | Test Node |
|---|---|---|---:|---|---|---|
| wrong_speaker_strict_social_emission | none | none | 0 | none | fallback_family: unexpected unavailable field | tests/test_co102_live_protected_replay_pipeline.py::test_co102_live_protected_replay_records_session_failure_artifacts |

## Failure Table

| Scenario | Test Node | Turn | Failed Invariant | Drift Type | Expected | Actual | Category | Severity | Primary Owner | Secondary Owner | Investigate First | Owner Drift Bucket |
|---|---|---:|---|---|---|---|---|---|---|---|---|---|
| wrong_speaker_strict_social_emission | tests/test_co102_live_protected_replay_pipeline.py::test_co102_live_protected_replay_records_session_failure_artifacts | 0 | fallback_family: unexpected unavailable field | structural_drift | available or explicitly allowed unavailable; allowed=[] | none | projection | medium | projection | none | tests/helpers/golden_replay.py | fallback_drift |

## Classification Summary

- Categories: `projection` (1)
- Primary owners: `projection` (1)


## Owner Drift Breakdown

```
fallback_drift .................. 1
```

## Fallback Summary

| Scenario | Final Source | Fallback Family | Temporal Frame | Opening Authorship | Opening Owner | Sealed Owner | Sanitizer Empty Owner |
|---|---|---|---|---|---|---|---|
| wrong_speaker_strict_social_emission | normalized_social_candidate | none | none | none | unknown-ambiguous | none | none |

## Sanitizer Summary

| Scenario | Mode | Changed | Dropped | Empty Fallback | Empty Owner | Legacy Rewrite | Strict Social Owner |
|---|---|---:|---:|---|---|---|---|
| wrong_speaker_strict_social_emission | <object object at 0x000001F3D35703F0> | none | none | none | none | False | none |

## Runtime Lineage Summary

- **Total lineage events:** 2
- **Fallback selected:** 0
- **Speaker repair:** 0
- **Mutation:** 1
- **Gate outcome:** 1
- **Top recurring recurrence keys:** _(none)_
- **Top fallback kinds:** _(none)_
- **Top fallback authorship sources:** _(none)_
- **Top fallback owner buckets:** _(none)_
- **Top fallback selection owners:** _(none)_
- **Top fallback content owners:** _(none)_
- **Top repair kinds:** _(none)_
- **Top mutation kinds:** `final_emission_mutation` (1)
- **Top gate paths:** `strict_social_accept` (1)

## Reproduce Locally

### Focused failing tests

```bash
python -m pytest tests/test_co102_live_protected_replay_pipeline.py::test_co102_live_protected_replay_records_session_failure_artifacts -q --tb=short
```

### Protected replay lane

```bash
python -m pytest -m golden_replay -q --tb=short
```
