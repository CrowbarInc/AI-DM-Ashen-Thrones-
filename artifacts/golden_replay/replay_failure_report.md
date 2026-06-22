# Protected Replay Failure Report

## Run Summary

- Status: `failed`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py tests/test_bx_speaker_identity_end_to_end_parity.py tests/test_bx_speaker_identity_golden_replay.py tests/test_golden_replay.py tests/test_golden_replay_projection.py tests/test_golden_replay_trend.py tests/test_golden_replay_structural_invariants.py tests/test_speaker_contract_risk.py tests/test_social_interaction_authority.py -q --tb=line`
- Generated at: `2026-06-22T21:39:03Z`
- Artifact location: `artifacts/golden_replay/replay_failure_report.md`
- Classified failures: `1`

## Failure Locator

| Scenario | Source Path | Branch | Turn Index | Turn ID | Failed Invariant | Test Node |
|---|---|---|---:|---|---|---|
| bx5_guard_ambiguous_multi_guard | none | none | 0 | none | selected_speaker_source: required field absent | tests/test_bx_speaker_identity_golden_replay.py::test_bx5_protected_golden_ambiguous_guard_no_false_parity |

## Failure Table

| Scenario | Test Node | Turn | Failed Invariant | Drift Type | Expected | Actual | Category | Severity | Primary Owner | Secondary Owner | Investigate First | Owner Drift Bucket |
|---|---|---:|---|---|---|---|---|---|---|---|---|---|
| bx5_guard_ambiguous_multi_guard | tests/test_bx_speaker_identity_golden_replay.py::test_bx5_protected_golden_ambiguous_guard_no_false_parity | 0 | selected_speaker_source: required field absent | structural_drift | present non-empty value | none | speaker | high | speaker | emission | game/speaker_contract_enforcement.py | speaker_drift |

## Classification Summary

- Categories: `speaker` (1)
- Primary owners: `speaker` (1)


## Owner Drift Breakdown

```
speaker_drift .................. 1
```

## Fallback Summary

| Scenario | Final Source | Fallback Family | Temporal Frame | Opening Authorship | Opening Owner | Sealed Owner | Sanitizer Empty Owner |
|---|---|---|---|---|---|---|---|
| bx5_guard_ambiguous_multi_guard | minimal_social_emergency_fallback | strict_social_deterministic_fallback | none | none | strict-social | strict-social-sealed | none |

## Sanitizer Summary

| Scenario | Mode | Changed | Dropped | Empty Fallback | Empty Owner | Legacy Rewrite | Strict Social Owner |
|---|---|---:|---:|---|---|---|---|
| bx5_guard_ambiguous_multi_guard | <object object at 0x000001598FB74170> | none | none | none | none | False | none |

## Runtime Lineage Summary

- **Total lineage events:** 4
- **Fallback selected:** 1
- **Speaker repair:** 0
- **Mutation:** 2
- **Gate outcome:** 1
- **Top recurring recurrence keys:** _(none)_
- **Top fallback kinds:** `minimal_social_emergency_fallback` (1)
- **Top fallback authorship sources:** _(none)_
- **Top fallback owner buckets:** _(none)_
- **Top fallback selection owners:** `game.final_emission_gate` (1)
- **Top fallback content owners:** `game.social_exchange_emission` (1)
- **Top repair kinds:** _(none)_
- **Top mutation kinds:** `fallback_mutation` (1); `response_type_repair_mutation` (1)
- **Top gate paths:** `strict_social_emergency` (1)

## Reproduce Locally

### Focused failing tests

```bash
python -m pytest tests/test_bx_speaker_identity_golden_replay.py::test_bx5_protected_golden_ambiguous_guard_no_false_parity -q --tb=short
```

### Protected replay lane

```bash
python -m pytest -m golden_replay -q --tb=short
```
