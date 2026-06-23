# BX Speaker Identity End-to-End Parity — Closeout

Date: 2026-06-22

## Status

BX is **closed**. Guard-matrix speaker identity parity is locked by four protected golden replay scenarios, Speaker Contract Risk gates, registry enumeration, and trend-window speaker parity field normalization. No runtime behavior was changed in BX6.

## Protected cases (BX5 / BX6 registry)

Mechanical authority: `tests/helpers/protected_replay_registry.py::bx_speaker_parity_corpus()`

| Scenario ID | Test | Matrix case |
|---|---|---|
| `bx5_guard_role_alias_guard_captain` | `test_bx5_protected_golden_role_alias_guard_to_guard_captain` | Role alias `guard` → canonical `guard_captain` |
| `bx5_guard_canonical_guard_captain` | `test_bx5_protected_golden_canonical_guard_captain` | Canonical ID `guard_captain` |
| `bx5_guard_gate_guard_distinct` | `test_bx5_protected_golden_gate_guard_distinct_from_guard_captain` | Distinct `gate_guard` must not collapse to captain |
| `bx5_guard_ambiguous_multi_guard` | `test_bx5_protected_golden_ambiguous_guard_no_false_parity` | Ambiguous multi-guard roster |

Reproduction:

```powershell
python -m pytest -m bx_speaker_parity -q
python -m pytest tests/test_bx_speaker_identity_golden_replay.py -q
```

The `bx_speaker_parity` marker selects the BX protected module. The BW `golden_replay` marker remains limited to the six short structural scenarios and is intentionally separate.

## Locked replay fields

Protected expectation helpers in `tests/helpers/golden_replay.py`:

- `protected_bx_resolved_speaker_parity_expectation(expected_speaker_id)`
- `protected_bx_ambiguous_guard_parity_expectation()`

Authoritative field paths (also in `tests/helpers/bx_guard_speaker_parity.py`):

**Resolved cases**

- `selected_speaker_id` == expected canonical ID
- `selected_speaker_source` present
- `speaker_projection_parity.status` == `aligned`
- `speaker_projection_parity.selected_speaker_id` == expected ID
- `speaker_projection_parity.final_observed_speaker_id` == expected ID
- `speaker_projection_parity.final_observed_status` == `resolved`
- `final_speaker_observation.status` == `resolved`
- `final_speaker_observation.canonical_speaker_id` == expected ID

**Ambiguous multi-guard**

- `selected_speaker_id` == `None`
- `selected_speaker_source` == `None`
- `speaker_projection_parity.status` == `final_ambiguous`
- `speaker_projection_parity.selected_speaker_id` == `None`
- `speaker_projection_parity.final_observed_speaker_id` == `None`
- `speaker_projection_parity.final_observed_status` == `ambiguous`
- `final_speaker_observation.status` == `ambiguous`
- `final_speaker_observation.canonical_speaker_id` == `None`

## Risk thresholds

Speaker Contract Risk gates (BT/BX5 family reporting):

| Case | `risk.S` | `risk.total` | `band` | Parity status |
|---|---:|---:|---|---|
| Resolved guard matrix | `0` | `<= 19` | `low` | `aligned` |
| Ambiguous multi-guard | `>= 20` | `> 19` | `guarded` / `elevated` / `high` | not `aligned` |

Family/trend reporting includes parity fields: `speaker_projection_parity_status`, `replay_selected_speaker_id`, `replay_selected_speaker_source`, `final_observed_speaker_id`, `final_observed_status`, `text_parity`, `attribution_score`.

## Registry and trend wiring (BX6)

- **Registry:** four BX cases registered as `PROTECTED` with category `BX_SPEAKER_PARITY_PROTECTED` in `tests/helpers/protected_replay_registry.py`.
- **BW corpus unchanged:** `protected_replay_corpus()` still enumerates exactly six short structural scenarios for Golden Transcript Drift trend windows.
- **Trend speaker dimension:** `tests/helpers/golden_replay_trend.py::normalize_trend_observation` already projects speaker parity subfields (`speaker_projection_parity_status`, `final_observed_speaker_id`, `final_speaker_observation_status`) for drift comparison when observations include them.
- **Trend discoverability:** `tests/helpers/golden_replay_trend.py::bx_speaker_parity_corpus_scenario_ids()` re-exports registry scenario IDs without adding BX execution to the BW trend window harness.

## Remaining known limitations

1. **No global `guard` alias table.** Role `guard` resolves per scene roster only; distinct actors such as `gate_guard` and `guard_captain` must not be collapsed globally.
2. **BW trend window does not execute BX scenarios.** BX uses gate→replay lifecycle fixtures (`tests/helpers/bx_guard_speaker_parity.py`), not `run_golden_replay` seed specs. Registry wiring is for discoverability and validation, not BW repeat-run automation.
3. **Enforcement vs routing alias policy** (BX4 convergence) remains scene-roster-bound; dialogue-plan declared pregate labels are a separate lane.
4. **Exact prose identity** is not a default protected gate; structural speaker parity and risk bands are the acceptance locks.
5. **Late post-speaker mutation** can still alter text after speaker validation; BX locks gate→replay projection parity for the guard matrix, not all terminal layers.

## Validation bundle

```powershell
python -m pytest tests/test_bx_speaker_identity_golden_replay.py -q
python -m pytest tests/test_golden_replay_trend.py tests/test_speaker_contract_risk.py -q
python -m pytest tests/test_protected_replay_registry.py -q
python -m pytest tests/test_golden_replay_helper_contracts.py -k bx -q
git diff --check
```

## Confirmation

BX speaker identity end-to-end parity is fully closed: protected cases A–D are registered, helper contracts and risk thresholds are locked, BW runtime/trend behavior is unchanged, and the guard-matrix parity corpus is enumerated for maintenance discoverability.
