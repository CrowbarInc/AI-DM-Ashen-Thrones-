# Owner Drift Risk Report

- Advisory only: `true`
- Report only: `true`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py tests/test_co102_live_protected_replay_pipeline.py -q --tb=short`
- Total risk signals: `3`

## High Risk Drift

No drift risk signals in this band.

## Medium Risk Drift

- `fallback_drift` (source=`protected`, frequency=`1`, trend=`stable`)
- `fallback_family` (source=`protected`, frequency=`1`, trend=`stable`)
- `tests/helpers/golden_replay.py` (source=`protected`, frequency=`1`, trend=`stable`)

## Low Risk Drift

No drift risk signals in this band.

## Top Risk Fields

| Rank | Item | Risk |
|---:|---|---|
| 1 | `fallback_family` | `medium` |

## Top Risk Owners

| Rank | Item | Risk |
|---:|---|---|
| 1 | `fallback_drift` | `medium` |

## Top Risk Investigation Targets

| Rank | Item | Risk |
|---:|---|---|
| 1 | `tests/helpers/golden_replay.py` | `medium` |

## Recommended Investigation Order

| Rank | Item | Risk |
|---:|---|---|
| 1 | `tests/helpers/golden_replay.py` | `medium` |

## Stability Ownership

- Stability scorecards aggregated: `0`
- Stability status counts: `{}`
- Owner bucket frequencies: `{'emission_drift': 0, 'fallback_drift': 0, 'lineage_drift': 0, 'ownership_drift': 0, 'projection_drift': 0, 'replay_drift_unclassified': 0, 'route_drift': 0, 'semantic_drift': 0, 'speaker_drift': 0}`

No stability ownership classifications.

## Stability Trends

Not enough stability history.

## Stability Hotspots

No stability hotspots identified.
