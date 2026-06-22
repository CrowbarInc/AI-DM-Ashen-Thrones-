# Owner Drift Hotspot Report

- Advisory only: `true`
- Report only: `true`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py tests/test_bx_speaker_identity_end_to_end_parity.py tests/test_bx_speaker_identity_golden_replay.py tests/test_golden_replay.py tests/test_golden_replay_projection.py tests/test_golden_replay_trend.py tests/test_golden_replay_structural_invariants.py tests/test_speaker_contract_risk.py tests/test_social_interaction_authority.py -q --tb=line`
- Total classifications: `1`

## Top Drift Fields

1. selected_speaker_source
   Count: 1
   Trend: stable

## Top Investigation Targets

1. game/speaker_contract_enforcement.py (1)

## Top Owner Drift Buckets

1. speaker_drift (1)

## Owner Drift Buckets By Field

| Field | Owner Drift Bucket | Count |
|---|---|---:|
| `selected_speaker_source` | `speaker_drift` | `1` |
