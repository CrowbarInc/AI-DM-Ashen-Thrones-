# Hotspot Compression Measurement Standard

**Version:** 1  
**Created:** 2026-06-26  
**Cycle:** CI_2  
**Watch:** [`docs/audits/CK_hotspot_compression_watch.md`](../audits/CK_hotspot_compression_watch.md)  
**Discovery:** [`CI_2_hotspot_compression_measurement_standard_discovery.md`](../../CI_2_hotspot_compression_measurement_standard_discovery.md)  
**Closeout:** [`docs/audits/CI_2_hotspot_compression_measurement_standard_closeout.md`](../audits/CI_2_hotspot_compression_measurement_standard_closeout.md)

---

## Purpose

Standardize how **CK Hotspot Compression Watch** measurements are produced so **HCI** values remain directly comparable across maintenance cycles.

**Primary metric (CK headline):** Hotspot Concentration Index (HCI)  
**Process metric:** Hotspot Measurement Consistency

---

## Dual-Lane Model

| Lane | ID | Role | Drives HCI? |
|---|---|---|---|
| Git path touch | **CK-GIT** | Primary | **Yes** |
| AST module fan-in | **CK-FI** | Supplementary | **No** — Notes / event evidence only |

**Rule:** Never mix CK-GIT and CK-FI numerators in one HCI headline.

---

## CK-GIT Primary Definitions

### Watch anchors

| Symbol | Value |
|---|---|
| `W` | `85855df` — CK watch start commit |
| `M` | Measurement commit (HEAD or named closeout) |
| `REV_RANGE` | `W..M` (git revisions reachable from `M` but not from `W`) |

### Population

Include `.py` paths under `game/`, `tests/`, `scripts/`.

Exclude paths under `artifacts/`, `codex_pytest_tmp/`, `docs/audits/`, `.pytest_cache/`, and any path ending in `.bak`.

### Touch count

For each commit in `REV_RANGE`, increment `touch[path]` once per changed population path.

```text
total_touches = sum(touch.values())
```

### Ranking

Sort by descending `touch[path]`, tie-break ascending path (lexicographic).

### Concentration

```text
top5_share_pct  = round(100 * sum(touch[p] for p in ranked[:5]) / total_touches, 2)   # if total_touches > 0 else 0.00
top10_share_pct = round(100 * sum(touch[p] for p in ranked[:10]) / total_touches, 2)  # if total_touches > 0 else 0.00
```

### Largest hotspot

Path with max `touch[path]`; report as `path (share_pct%)`.

### Threshold

**T_touch = 3** — `files_above_threshold` = count of paths where `touch[path] >= 3`.

### HCI headline (v1)

```text
HCI = top5_share_pct
```

Bump `baseline_version` in this document before changing the HCI formula.

### Empty window

When `M == W` or no commits in `REV_RANGE`, all metrics are zero/empty. This is valid at watch activation.

---

## CK-FI Supplementary Definitions

Run at measurement commit `M`:

```powershell
python scripts/bu_final_emission_coupling_discovery.py
```

Read `docs/audits/BU_import_fan_in_fan_out.csv`:

- Ranking unit: **module** (`fan_in_total`)
- **T_fi = 10** — count modules with `fan_in_total >= 10`
- Compute `fi_top5_share_pct`, `fi_top10_share_pct` using same concentration formulas as CK-GIT but with FI weights

Record in CK **Notes**:

```text
FI top5=<pct>% top10=<pct>% above_T10=<n>
```

AST rules and exclusions: `docs/audits/BU_post_bj_fan_in_fan_out_validation.md`.

---

## CK Column Mapping

| CK column | Source |
|---|---|
| Commit | short hash of `M` |
| Date | commit date of `M` |
| Top 5 % | CK-GIT `top5_share_pct` |
| Top 10 % | CK-GIT `top10_share_pct` |
| Largest Hotspot | CK-GIT largest path + share |
| Files Above Threshold | CK-GIT count at T_touch=3 |
| Notes | `REV_RANGE`, `total_touches`, CK-FI summary, cycle label |

---

## Measurement Recipe

```powershell
# Set M to the qualifying maintenance closeout commit (not necessarily HEAD)
git rev-parse --short <M>

# 1. Primary CK-GIT + CK-FI report (authoritative)
python tools/ck_hotspot_compression_report.py --measurement-commit <M> --cycle-label "<cycle>"

# 2. Supplementary FI refresh (when structural coupling may have changed)
python scripts/bu_final_emission_coupling_discovery.py
# Re-run step 1 if BU CSV was regenerated

# 3. Optional context (Notes only)
python tools/replay_maintenance_metrics.py
```

Operator procedure: [`hotspot_compression_watch_process.md`](hotspot_compression_watch_process.md)

Outputs: `artifacts/ck1_hotspot_compression_report.json`, `artifacts/ck1_hotspot_compression_report.md`

---

## Repeatability Rules

| Component | Stable? | Exempt fields |
|---|---|---|
| CK-GIT aggregation at fixed `M` | Yes | — |
| CK-FI parse from fixed CSV | Yes | — |
| `bu_final_emission_coupling_discovery.py` output | Yes (fixed tree) | — |
| `bv17_hotspot_reassessment.py` JSON | Partial | `generated_at` |
| `replay_maintenance_metrics.py` JSON | Partial | `generated_at` / report timestamps |
| `test_audit.py` full inventory | Partial | `summary.generated_utc` |

Compare metric fields only; ignore timestamp metadata when verifying repeatability.

---

## Compression / Expansion Materiality

Record CK compression event when **any**:

- Top 5 % decreases by ≥ **2.0** percentage points vs prior row
- Files above T_touch decreases by ≥ **3**

Record CK expansion event when **any**:

- Top 5 % increases by ≥ **2.0** percentage points vs prior row
- A new path enters top-3 with ≥ **2** touches in cumulative window

---

## Non-Goals

- CK does **not** use BR category-filtered touches as HCI primary.
- CK does **not** use BV17 JSON as authority (reference only).
- CK does **not** use replay 30/60/90d windows as HCI primary.
- CK does **not** backfill pre-`85855df` history.
- LOC rankings (BO) are context only, not HCI.

---

## Related Artifacts

| Artifact | Role |
|---|---|
| [CK_hotspot_compression_watch.md](../audits/CK_hotspot_compression_watch.md) | Active watch ledger |
| [CJ_corrective_cohort_watch.md](../audits/CJ_corrective_cohort_watch.md) | Corrective locality complement |
| [BU_post_bj_fan_in_fan_out_validation.md](../audits/BU_post_bj_fan_in_fan_out_validation.md) | CK-FI methodology |
