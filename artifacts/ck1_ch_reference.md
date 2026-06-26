# CK1 Hotspot Compression Report

> CK-GIT primary measurement for Hotspot Compression Watch #1.

_Primary metric: **hotspot_concentration_index** (HCI = Top 5 Share %)._

## Report Status

- **Generation status:** success
- **Measurement readiness:** measurement_ready
- **Data sufficient for HCI headline:** True
- **Standard version:** 1

## Provenance

- **Command:** `python tools/ck_hotspot_compression_report.py --watch-start 5f0ad53 --measurement-commit 85855df --cycle-label 'CJ3 CH reference (non-authoritative)' --output-md 'artifacts\ck1_ch_reference.md' --output-json 'artifacts\ck1_ch_reference.json'`
- **Generated at:** 2026-06-26T19:52:38Z _(stability-exempt)_

## Measurement Window

- **Watch start (W):** `5f0ad53`
- **Measurement commit (M):** `85855df`
- **Measurement date:** 2026-06-26
- **REV_RANGE:** `5f0ad53..85855df`
- **Commits in window:** 7

## CK-GIT Primary Metrics

- **HCI (Top 5 %):** 9.52
- **Top 5 share %:** 9.52
- **Top 10 share %:** 18.1
- **Total touches:** 105
- **Distinct paths:** 96
- **Largest hotspot:** tests/helpers/failure_dashboard_recurrence.py (1.9%)
- **Files above threshold (T_touch=3):** 0

## Hotspot Rankings (Top 10)

| Rank | Path | Touches | Share % |
|---:|---|---:|---:|
| 1 | `tests/helpers/failure_dashboard_recurrence.py` | 2 | 1.9 |
| 2 | `tests/helpers/golden_replay_artifact_manifest.py` | 2 | 1.9 |
| 3 | `tests/helpers/golden_replay_projection.py` | 2 | 1.9 |
| 4 | `tests/helpers/replay_bug_recurrence.py` | 2 | 1.9 |
| 5 | `tests/helpers/replay_bug_recurrence_events.py` | 2 | 1.9 |
| 6 | `tests/helpers/replay_bug_recurrence_history.py` | 2 | 1.9 |
| 7 | `tests/helpers/replay_bug_recurrence_serialization.py` | 2 | 1.9 |
| 8 | `tests/helpers/replay_bug_recurrence_statistics.py` | 2 | 1.9 |
| 9 | `tests/test_ownership_registry.py` | 2 | 1.9 |
| 10 | `game/attribution_read_views.py` | 1 | 0.95 |

## CK-FI Supplementary (Notes only)

- **Notes string:** `FI top5=20.79% top10=32.76% above_T10=39`
- **FI top 5 share %:** 20.79
- **FI top 10 share %:** 32.76
- **Modules above T_fi=10:** 39
- **Largest FI module:** tests.helpers.replay_fem_read_smoke (5.56%)

## CK Log Draft Row

| Measurement | Commit | Date | Top 5 % | Top 10 % | Largest Hotspot | Files Above Threshold | Notes |
|---|---|---|---:|---:|---|---:|---|
| CJ3 CH reference (non-authoritative) | `85855df` | 2026-06-26 | 9.52 | 18.1 | tests/helpers/failure_dashboard_recurrence.py (1.9%) | 0 | `std=v1; REV_RANGE=5f0ad53..85855df; total_touches=105; FI top5=20.79% top10=32.76% above_T10=39; cycle=CJ3 CH reference (non-authoritative)` |

## CK Ledger Snippet

_Copy-paste into `docs/audits/CK_hotspot_compression_watch.md` (Measurement Log + baseline on first row)._

```markdown
<!-- CK ledger snippet — append Measurement Log row; on first measurement replace baseline placeholders -->

### Measurement Log row

| Measurement | Commit | Date | Top 5 % | Top 10 % | Largest Hotspot | Files Above Threshold | Notes |
|---|---|---|---:|---:|---|---:|---|
| CJ3 CH reference (non-authoritative) | `85855df` | 2026-06-26 | 9.52 | 18.1 | tests/helpers/failure_dashboard_recurrence.py (1.9%) | 0 | `std=v1; REV_RANGE=5f0ad53..85855df; total_touches=105; FI top5=20.79% top10=32.76% above_T10=39; cycle=CJ3 CH reference (non-authoritative)` |

### Baseline section (first measurement only)

| Baseline field | Value |
|---|---|
| Top 10 most-touched files | tests/helpers/failure_dashboard_recurrence.py (2 touches, 1.9%); tests/helpers/golden_replay_artifact_manifest.py (2 touches, 1.9%); tests/helpers/golden_replay_projection.py (2 touches, 1.9%); tests/helpers/replay_bug_recurrence.py (2 touches, 1.9%); tests/helpers/replay_bug_recurrence_events.py (2 touches, 1.9%); tests/helpers/replay_bug_recurrence_history.py (2 touches, 1.9%); tests/helpers/replay_bug_recurrence_serialization.py (2 touches, 1.9%); tests/helpers/replay_bug_recurrence_statistics.py (2 touches, 1.9%); tests/test_ownership_registry.py (2 touches, 1.9%); game/attribution_read_views.py (1 touches, 0.95%) |
| Top 5 touch share (% of repository touches) | 9.52 |
| Top 10 touch share (% of repository touches) | 18.1 |
| Largest single hotspot (file + touch share) | tests/helpers/failure_dashboard_recurrence.py (1.9%) |
| Files above hotspot threshold | 0 |
| Hotspot threshold (touch count) | T_touch=3 |

**HCI headline:** 9.52

```
