# CK — Hotspot Compression Watch #1

**Status:** Active  
**Type:** Longitudinal Maintenance Metric  
**Scope:** Documentation and evidence only. No production code changes.

**Purpose:** Track whether the highest-touch files continue to dominate development effort or whether responsibility is gradually spreading across smaller, more localized modules.

**Primary metric:** Hotspot Concentration Index (HCI) — **CK-GIT** lane per [`docs/processes/hotspot_compression_measurement_standard.md`](../processes/hotspot_compression_measurement_standard.md): `HCI = Top 5 Share %` of cumulative git path touches (`85855df..M`).

**Watch boundary:** Begins at current repository state (`85855df`). No historical backfill. Record future measurements only at each significant maintenance cycle.

---

## Watch Metadata

| Field | Value |
|---|---|
| Watch start commit | `85855df` (`85855df00ebdee20a33c0ada447c178bf1f49820`) |
| Watch start date | 2026-06-26 |
| Current branch | `feature/stabilized-foundation` |
| Measurement cadence | Every significant maintenance cycle (audit closeout, extraction block, governance redistribution, replay/classification contraction, or comparable multi-file maintenance program) |
| Inspected range | `85855df..HEAD` (future measurements only) |

---

## Current Baseline (Placeholders)

Initial baseline fields are reserved at watch activation. **Do not backfill pre-watch history.** Populate on the first scheduled measurement row.

| Baseline field | Value at watch start |
|---|---|
| Top 10 most-touched files | _pending first measurement_ |
| Top 5 touch share (% of repository touches) | _pending_ |
| Top 10 touch share (% of repository touches) | _pending_ |
| Largest single hotspot (file + touch share) | _pending_ |
| Files above hotspot threshold | _pending_ |
| Hotspot threshold (touch count) | T_touch = 3 (per measurement standard v1) |

**HCI headline:** _pending first measurement_

---

## Measurement Log

_Add one row per measurement window. Do not insert historical pre-watch values._

| Measurement | Commit | Date | Top 5 % | Top 10 % | Largest Hotspot | Files Above Threshold | Notes |
|---|---|---|---:|---:|---|---:|---|
| Watch activation | `85855df` | 2026-06-26 | pending | pending | pending | pending | Baseline placeholders only; no pre-watch backfill |

---

## Compression Events

Record whenever maintenance **substantially reduces** hotspot concentration (lower Top 5/10 %, smaller largest hotspot, or fewer files above threshold).

| Date | Audit / cycle | Affected subsystem | Previous hotspot | Distribution improvement | Estimated burden reduction | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |

**Fields to capture per event:**

- **Affected subsystem** — e.g. governance, replay, fallback, classification, ownership registry
- **Previous hotspot** — dominant file or module before compression
- **Resulting distribution improvement** — Top 5/10 % delta, new largest hotspot, threshold population change
- **Audit responsible** — CE, CF, CG, CH, etc.
- **Estimated reduction in maintenance burden** — qualitative (low / medium / high) or brief rationale

---

## Expansion Events

Record whenever work **increases** hotspot concentration.

| Date | Audit / cycle | Cause category | New or growing hotspot | Concentration impact | Notes |
|---|---|---|---|---|---|
| | | | | | |

**Cause categories (use one or more):**

- new central registries
- shared helper growth
- ownership concentration
- replay concentration
- synchronization hubs
- taxonomy expansion

---

## Interpretation Guide

### Improving

- Top 5 concentration **decreases**
- Largest hotspot **shrinks** (lower touch share and/or LOC/FI)
- Responsibility becomes **more distributed** (more files share maintenance load; fewer modules above threshold)
- Average maintenance locality **improves** (see [CJ corrective cohort watch](CJ_corrective_cohort_watch.md) when qualifying fixes exist)

### Neutral

- Top 5 / Top 10 concentration remains **approximately stable** (± small drift within measurement noise)
- Largest hotspot unchanged; threshold population flat
- Redistribution without net concentration change (coupling moves, not spreads)

### Worsening

- Top files consume **increasing** percentages of repository edits
- **New central maintenance hubs** emerge (new top-10 entrants, rising FI/touch share, megastructure growth)
- Files above hotspot threshold **increase**

---

## Measurement Procedure (Future Rows)

**Authoritative procedure:** [`docs/processes/hotspot_compression_measurement_standard.md`](../processes/hotspot_compression_measurement_standard.md) (CI_2 adopted, version 1).  
**Operator runbook:** [`docs/processes/hotspot_compression_watch_process.md`](../processes/hotspot_compression_watch_process.md) (CI_8).

When recording a new measurement:

1. Run `python tools/ck_hotspot_compression_report.py --measurement-commit <M> --cycle-label "<cycle>"`.
2. Copy the **CK Ledger Snippet** from `artifacts/ck1_hotspot_compression_report.md` into this ledger.
3. Set **HCI headline** = Top 5 % from `ck_git.hci` (already in snippet on first row).
4. If materiality thresholds in the standard are met, add a **Compression Events** or **Expansion Events** row.
5. Record standard version (`1`) and `total_touches` in **Notes** (included in generator output).

Do not use import fan-in, BV17 JSON, or replay-only touch windows as HCI primary sources.

---

## Related Artifacts

| Artifact | Role |
|---|---|
| [hotspot_compression_measurement_standard.md](../processes/hotspot_compression_measurement_standard.md) | **Authoritative** CK measurement procedure (CI_2 adopted) |
| [hotspot_compression_watch_process.md](../processes/hotspot_compression_watch_process.md) | **Operator runbook** (CI_8) |
| [artifacts/ck1_hotspot_compression_report.json](../../artifacts/ck1_hotspot_compression_report.json) | Generated CK-GIT + CK-FI machine report |
| [artifacts/ck1_hotspot_compression_report.md](../../artifacts/ck1_hotspot_compression_report.md) | Generated report + ledger snippet |
| [CI_2_hotspot_compression_measurement_standard_closeout.md](CI_2_hotspot_compression_measurement_standard_closeout.md) | CI_2 governance closeout |
| [CJ_corrective_cohort_watch.md](CJ_corrective_cohort_watch.md) | Complementary corrective-fix locality watch |
| [CI_corrective_cohort_validation_2_closeout.md](CI_corrective_cohort_validation_2_closeout.md) | Prior corrective cohort authority |
| `docs/audits/BU_import_fan_in_fan_out.csv` | CK-FI supplementary lane input |
| `artifacts/bv17_hotspot_analysis.json` | Historical reference only (not CK authority) |
