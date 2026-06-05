# Protected Replay Failure Report

## Run Summary

- Status: `failed`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py tests/test_final_emission_boundary_no_semantic_repair.py tests/test_golden_replay.py -q`
- Generated at: `2026-06-04T22:31:59Z`
- Artifact location: `artifacts/golden_replay/replay_failure_report.md`
- Classified failures: `1`

## Failure Locator

| Scenario | Source Path | Branch | Turn Index | Turn ID | Failed Invariant | Test Node |
|---|---|---|---:|---|---|---|
| vocative_override_after_prior_continuity | none | none | 1 | none | selected_speaker_id: exact value mismatch | tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants |

## Failure Table

| Scenario | Test Node | Turn | Failed Invariant | Drift Type | Expected | Actual | Category | Severity | Primary Owner | Secondary Owner | Investigate First |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| vocative_override_after_prior_continuity | tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants | 1 | selected_speaker_id: exact value mismatch | structural_drift | guard | guard_captain | projection | medium | projection | none | tests/helpers/golden_replay.py |

## Classification Summary

- Categories: `projection` (1)
- Primary owners: `projection` (1)

## Fallback Summary

| Scenario | Final Source | Fallback Family | Temporal Frame | Opening Authorship | Opening Owner | Sealed Owner | Sanitizer Empty Owner |
|---|---|---|---|---|---|---|---|
| vocative_override_after_prior_continuity | anti_reset_local_continuation_fallback | gate_terminal_repair | none | none | unknown-ambiguous | sealed-gate | none |

## Sanitizer Summary

| Scenario | Mode | Changed | Dropped | Empty Fallback | Empty Owner | Legacy Rewrite | Strict Social Owner |
|---|---|---:|---:|---|---|---|---|
| vocative_override_after_prior_continuity | <object object at 0x0000023D9A0F4130> | none | none | none | none | False | none |

## Runtime Lineage Summary

- **Total lineage events:** 4
- **Fallback selected:** 1
- **Speaker repair:** 0
- **Mutation:** 2
- **Gate outcome:** 1
- **Top recurring recurrence keys:** _(none)_
- **Top fallback kinds:** `visibility_or_scene_replacement` (1)
- **Top fallback authorship sources:** _(none)_
- **Top fallback owner buckets:** _(none)_
- **Top fallback selection owners:** _(none)_
- **Top fallback content owners:** _(none)_
- **Top repair kinds:** _(none)_
- **Top mutation kinds:** `fallback_mutation` (1); `response_type_repair_mutation` (1)
- **Top gate paths:** `visibility_or_scene_replaced` (1)

## Reproduce Locally

### Focused failing tests

```bash
python -m pytest tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants -q --tb=short
```

### Protected replay lane

```bash
python -m pytest -m golden_replay -q --tb=short
```
