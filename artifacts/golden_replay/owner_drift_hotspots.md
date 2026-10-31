# Owner Drift Hotspot Report

- Advisory only: `true`
- Report only: `true`
- Command: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\.venv\Lib\site-packages\pytest\__main__.py -m golden_replay -q --tb=short -o addopts=--basetemp=development/tmp/maintenance_golden --junitxml=development/tmp/github_checkpoint/golden_after.xml`
- Total classifications: `1`

## Top Drift Fields

1. scaffold_leakage
   Count: 1
   Trend: stable

## Top Investigation Targets

1. game/output_sanitizer.py (1)

## Top Owner Drift Buckets

1. semantic_drift (1)

## Owner Drift Buckets By Field

| Field | Owner Drift Bucket | Count |
|---|---|---:|
| `scaffold_leakage` | `semantic_drift` | `1` |
