# CK1 Hotspot Compression Report

> CK-GIT primary measurement for Hotspot Compression Watch #1.

_Primary metric: **hotspot_concentration_index** (HCI = Top 5 Share %)._

## Report Status

- **Generation status:** success
- **Measurement readiness:** measurement_ready
- **Data sufficient for HCI headline:** True
- **Standard version:** 1

## Provenance

- **Command:** `python tools/ck_hotspot_compression_report.py --cycle-label 'CI_8 workflow dry-run'`
- **Generated at:** 2026-06-26T18:40:19Z _(stability-exempt)_

## Measurement Window

- **Watch start (W):** `85855df`
- **Measurement commit (M):** `3709523`
- **Measurement date:** 2026-06-26
- **REV_RANGE:** `85855df..3709523`
- **Commits in window:** 1

## CK-GIT Primary Metrics

- **HCI (Top 5 %):** 100.0
- **Top 5 share %:** 100.0
- **Top 10 share %:** 100.0
- **Total touches:** 2
- **Distinct paths:** 2
- **Largest hotspot:** tests/helpers/ck_hotspot_compression_report.py (50.0%)
- **Files above threshold (T_touch=3):** 0

## Hotspot Rankings (Top 10)

| Rank | Path | Touches | Share % |
|---:|---|---:|---:|
| 1 | `tests/helpers/ck_hotspot_compression_report.py` | 1 | 50.0 |
| 2 | `tests/test_ck_hotspot_compression_report.py` | 1 | 50.0 |

## CK-FI Supplementary (Notes only)

- **Notes string:** `FI top5=20.79% top10=32.76% above_T10=39`
- **FI top 5 share %:** 20.79
- **FI top 10 share %:** 32.76
- **Modules above T_fi=10:** 39
- **Largest FI module:** tests.helpers.replay_fem_read_smoke (5.56%)

## CK Log Draft Row

| Measurement | Commit | Date | Top 5 % | Top 10 % | Largest Hotspot | Files Above Threshold | Notes |
|---|---|---|---:|---:|---|---:|---|
| CI_8 workflow dry-run | `3709523` | 2026-06-26 | 100.0 | 100.0 | tests/helpers/ck_hotspot_compression_report.py (50.0%) | 0 | `std=v1; REV_RANGE=85855df..3709523; total_touches=2; FI top5=20.79% top10=32.76% above_T10=39; cycle=CI_8 workflow dry-run` |

## CK Ledger Snippet

_Copy-paste into `docs/audits/CK_hotspot_compression_watch.md` (Measurement Log + baseline on first row)._

```markdown
<!-- CK ledger snippet — append Measurement Log row; on first measurement replace baseline placeholders -->

### Measurement Log row

| Measurement | Commit | Date | Top 5 % | Top 10 % | Largest Hotspot | Files Above Threshold | Notes |
|---|---|---|---:|---:|---|---:|---|
| CI_8 workflow dry-run | `3709523` | 2026-06-26 | 100.0 | 100.0 | tests/helpers/ck_hotspot_compression_report.py (50.0%) | 0 | `std=v1; REV_RANGE=85855df..3709523; total_touches=2; FI top5=20.79% top10=32.76% above_T10=39; cycle=CI_8 workflow dry-run` |

### Baseline section (first measurement only)

| Baseline field | Value |
|---|---|
| Top 10 most-touched files | tests/helpers/ck_hotspot_compression_report.py (1 touches, 50.0%); tests/test_ck_hotspot_compression_report.py (1 touches, 50.0%) |
| Top 5 touch share (% of repository touches) | 100.0 |
| Top 10 touch share (% of repository touches) | 100.0 |
| Largest single hotspot (file + touch share) | tests/helpers/ck_hotspot_compression_report.py (50.0%) |
| Files above hotspot threshold | 0 |
| Hotspot threshold (touch count) | T_touch=3 |

**HCI headline:** 100.0

```
