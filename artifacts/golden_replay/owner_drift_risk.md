# Owner Drift Risk Report

- Advisory only: `true`
- Report only: `true`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py tests/test_bx_speaker_identity_end_to_end_parity.py tests/test_bx_speaker_identity_golden_replay.py tests/test_golden_replay.py tests/test_golden_replay_projection.py tests/test_golden_replay_trend.py tests/test_golden_replay_structural_invariants.py tests/test_speaker_contract_risk.py tests/test_social_interaction_authority.py -q --tb=line`
- Total risk signals: `3`

## High Risk Drift

No drift risk signals in this band.

## Medium Risk Drift

- `speaker_drift` (source=`protected`, frequency=`1`, trend=`stable`)

## Low Risk Drift

- `game/speaker_contract_enforcement.py` (source=`advisory`, frequency=`1`, trend=`stable`)
- `selected_speaker_source` (source=`advisory`, frequency=`1`, trend=`stable`)

## Top Risk Fields

| Rank | Item | Risk |
|---:|---|---|
| 1 | `selected_speaker_source` | `low` |

## Top Risk Owners

| Rank | Item | Risk |
|---:|---|---|
| 1 | `speaker_drift` | `medium` |

## Top Risk Investigation Targets

| Rank | Item | Risk |
|---:|---|---|
| 1 | `game/speaker_contract_enforcement.py` | `low` |

## Recommended Investigation Order

| Rank | Item | Risk |
|---:|---|---|
| 1 | `game/speaker_contract_enforcement.py` | `low` |

## Stability Ownership

- Stability scorecards aggregated: `0`
- Stability status counts: `{}`
- Owner bucket frequencies: `{'emission_drift': 0, 'fallback_drift': 0, 'lineage_drift': 0, 'ownership_drift': 0, 'projection_drift': 0, 'replay_drift_unclassified': 0, 'route_drift': 0, 'semantic_drift': 0, 'speaker_drift': 0}`

No stability ownership classifications.

## Stability Trends

Not enough stability history.

## Stability Hotspots

No stability hotspots identified.
