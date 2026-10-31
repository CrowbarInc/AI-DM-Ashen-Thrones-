# Owner Drift Risk Report

- Advisory only: `true`
- Report only: `true`
- Command: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\.venv\Lib\site-packages\pytest\__main__.py -m golden_replay -q --tb=short -o addopts=--basetemp=development/tmp/maintenance_golden --junitxml=development/tmp/github_checkpoint/golden_after.xml`
- Total risk signals: `3`

## High Risk Drift

No drift risk signals in this band.

## Medium Risk Drift

- `game/output_sanitizer.py` (source=`protected`, frequency=`1`, trend=`stable`)
- `scaffold_leakage` (source=`protected`, frequency=`1`, trend=`stable`)

## Low Risk Drift

- `semantic_drift` (source=`supporting`, frequency=`1`, trend=`stable`)

## Top Risk Fields

| Rank | Item | Risk |
|---:|---|---|
| 1 | `scaffold_leakage` | `medium` |

## Top Risk Owners

| Rank | Item | Risk |
|---:|---|---|
| 1 | `semantic_drift` | `low` |

## Top Risk Investigation Targets

| Rank | Item | Risk |
|---:|---|---|
| 1 | `game/output_sanitizer.py` | `medium` |

## Recommended Investigation Order

| Rank | Item | Risk |
|---:|---|---|
| 1 | `game/output_sanitizer.py` | `medium` |

## Stability Ownership

- Stability scorecards aggregated: `0`
- Stability status counts: `{}`
- Owner bucket frequencies: `{'emission_drift': 0, 'fallback_drift': 0, 'lineage_drift': 0, 'ownership_drift': 0, 'projection_drift': 0, 'replay_drift_unclassified': 0, 'route_drift': 0, 'semantic_drift': 0, 'speaker_drift': 0}`

No stability ownership classifications.

## Stability Trends

Not enough stability history.

## Stability Hotspots

No stability hotspots identified.
