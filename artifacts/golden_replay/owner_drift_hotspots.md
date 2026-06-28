# Owner Drift Hotspot Report

- Advisory only: `true`
- Report only: `true`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py tests/test_co102_live_protected_replay_pipeline.py -q --tb=short`
- Total classifications: `1`

## Top Drift Fields

1. fallback_family
   Count: 1
   Trend: stable

## Top Investigation Targets

1. tests/helpers/golden_replay.py (1)

## Top Owner Drift Buckets

1. fallback_drift (1)

## Owner Drift Buckets By Field

| Field | Owner Drift Bucket | Count |
|---|---|---:|
| `fallback_family` | `fallback_drift` | `1` |
