# CI_2 — Hotspot Compression Measurement Standard Discovery

**Date:** 2026-06-26  
**Scope:** Discovery and documentation only. No production code changes.  
**Upstream watch:** `docs/audits/CK_hotspot_compression_watch.md` (Active; baseline placeholders pending)

---

## 1. Scope

| Field | Value |
|---|---|
| Inspected commit | `85855df` (`85855df00ebdee20a33c0ada447c178bf1f49820`) |
| Inspected branch | `feature/stabilized-foundation` |
| Inspected date | 2026-06-26 |
| CK watch start | `85855df` (2026-06-26) |
| Constraint | CK measurement log not backfilled; CI_2 locks procedure only |

**Commands / evidence inspected:**

- `git rev-parse HEAD`, `git branch --show-current`, `git log -1 --date=short`
- Read: `docs/audits/CK_hotspot_compression_watch.md`
- Read: `scripts/bu_final_emission_coupling_discovery.py`, `docs/audits/BU_post_bj_fan_in_fan_out_validation.md`
- Read: `docs/audits/BU_import_fan_in_fan_out.csv` (on-disk snapshot)
- Read: `artifacts/bv17_hotspot_analysis.json`, `docs/audits/BV17_concentration_rankings.md`
- Read: `tests/helpers/bug_fix_locality_metric.py`, `docs/BRL2_bug_fix_locality_regression_guard.md`
- Read: `tools/replay_maintenance_metrics.py`, `docs/audits/discovery/BO_hotspot_inventory.md`, `artifacts/bo_maintenance_audit.json`
- Read-only dry-run: FI parse (twice) and git-touch aggregation (twice) via inline Python (no artifact writes)

---

## 2. CK Field Requirements

Extracted from `CK_hotspot_compression_watch.md`:

| CK field | CK intent | Ambiguity before CI_2 |
|---|---|---|
| Top 10 most-touched files | Ranked hotspot list | **Ambiguous:** file path vs module; touch vs fan-in |
| Top 5 % | Concentration headline | **Ambiguous:** % of touches vs % of import FI |
| Top 10 % | Concentration headline | Same as Top 5 % |
| Largest hotspot | Dominant file/module + weight | **Ambiguous:** path vs module name |
| Files above threshold | Hotspot population count | **Ambiguous:** threshold undefined (touch vs FI) |
| Measurement log columns | Longitudinal HCI ledger | Needs locked window + formula |
| Compression / expansion triggers | Material concentration change | Needs materiality rule (recommend ±2 pp Top 5 or ±1 pp Top 10) |

**CI_2 resolution:** CK-primary uses **git path touches** (file paths). Supplementary lane uses **AST module fan-in** (Lane A). Do not mix numerators in one HCI headline.

---

## 3. Measurement Lane Inventory

### Lane A — AST import fan-in (BU / BV17)

| Attribute | Value |
|---|---|
| Population | All Python modules under `game/`, `tests/`, `scripts/` |
| Ranking unit | **Module** (dotted name) |
| Weight | `fan_in_total` = unique importer files (AST direct import/call) |
| Time window | **Static snapshot** at measurement commit |
| Commands | `python scripts/bu_final_emission_coupling_discovery.py`; optional `python tools/bv17_hotspot_reassessment.py` |
| Outputs | `docs/audits/BU_import_fan_in_fan_out.csv`, `artifacts/bv17_hotspot_analysis.json` |
| Exclusions | Dynamic imports, monkeypatch strings, same-file calls (per BU validation doc) |
| Comparability risks | Module splits/merges change FI without edit churn; renames change module keys; BV17 JSON includes `generated_at` timestamp |

**BV17 JSON note:** `concentration.top5_share` exists; **`top10_share` is not emitted** — must derive from rankings.

### Lane B — Git path touch (BR / BRL1)

| Attribute | Value |
|---|---|
| Population | Paths touched by commits in `docs/reports/BR_commit_classification.csv` |
| Ranking unit | **File path** |
| Weight | Per-commit path touch count (one per commit per path) |
| Time window | Classification CSV history (not CK watch window by default) |
| Commands | `tests/helpers/bug_fix_locality_metric.py` → `build_hotspot_analysis()` |
| Outputs | `artifacts/bug_fix_locality_report.md`, BRL2 guard report |
| Formula | `top5_share_pct = round(100 * sum(top5 touches) / total_touches, 2)` |
| Comparability risks | **Not repository-wide** — category-filtered; bug_fix top-5 share (3.98%) measures maintenance subset only |

### Lane C — Subsystem git touch (CE1 replay)

| Attribute | Value |
|---|---|
| Population | Replay helper/test patterns (`REPLAY_HELPER_PATTERNS`, `REPLAY_TEST_PATTERNS`) |
| Ranking unit | **File path** |
| Weight | `git log --since=N days ago` commit count per file |
| Time window | 30 / 60 / 90 days |
| Command | `python tools/replay_maintenance_metrics.py` |
| Outputs | `artifacts/golden_replay/replay_maintenance_metrics.json` |
| Comparability risks | Rolling window length drift; replay scope only |

### Lane D — LOC + static inventory (BO)

| Attribute | Value |
|---|---|
| Population | All repo Python files |
| Ranking unit | **File path** by LOC |
| Weight | Line count; static fan-in where available |
| Time window | Static (`artifacts/bo_maintenance_audit.json`, dated 2026-06-17) |
| Comparability risks | LOC ≠ edit churn; stale vs current tree |

### Lane E — Test inventory hubs (AQ)

| Attribute | Value |
|---|---|
| Population | Test modules in inventory |
| Ranking unit | Module / file cluster |
| Weight | Import-hub fan-in from full diagnostic |
| Command | `py -3 tools/test_audit.py --full` → `artifacts/test_inventory_full.json` |
| Committed slim JSON | `tests/test_inventory_governance.json` — **no** `import_hub_modules` (requires full diagnostic) |
| Comparability risks | Schema/version fields; governance-only subset |

---

## 4. Lane Comparison Matrix

| Lane | Population | Ranking unit | Numerator | Denominator | Time window | Top-5? | Top-10? | Threshold? | CK-primary? |
|---|---|---|---|---|---|---|---|---|---|
| A FI | `game/`, `tests/`, `scripts/` modules | module | sum FI of top N | total FI | static snapshot | Yes | Yes (derive) | Yes (`FI ≥ T`) | **Supplementary** |
| B git touch | BR-classified commits | file path | sum touches top N | total touches | CSV history | Yes | Yes (derive) | Yes | No (subset only) |
| C replay git | replay patterns | file path | commit count / file | total replay touches | 30/60/90d | Yes | Yes | Yes | No (subsystem) |
| D LOC | all `.py` | file path | LOC rank | total LOC | static | No (different metric) | No | Yes (LOC tiers) | No |
| E test hubs | test inventory | module cluster | hub FI | helper FI total | static | Partial | Partial | Partial | No |

---

## 5. Canonical CK Procedure Recommendation

### Dual-lane standard (frozen roles)

| Role | Lane | CK mapping |
|---|---|---|
| **Primary HCI** | **Git path touch (CK-GIT)** — new locked procedure derived from Lane B mechanics, whole-repo scope | Top 5 %, Top 10 %, largest hotspot, files above threshold, top-10 list |
| **Supplementary** | **Lane A FI** — BU CSV at measurement commit | CK **Notes** column + compression/expansion evidence only |

**Rationale for CK-GIT primary:**

1. Matches CK language: "repository touches," "highest-touch **files**," maintenance **effort** spread.
2. Window `85855df..<measurement_commit>` aligns with CK watch boundary (no pre-watch backfill).
3. Repeatable with read-only `git log` (proven below).
4. Lane A alone measures **import coupling**, not edit concentration — wrong numerator for CK intent.

**Explicit prohibition:** `HCI` headline must not blend git-touch % with FI %.

---

## 6. Locked Definitions (CK Measurement Standard v1)

Full normative copy: `docs/processes/hotspot_compression_measurement_standard.md`

### 6a. Hotspot population (CK-GIT primary)

Include paths that:

- end with `.py`
- start with `game/`, `tests/`, or `scripts/`

Exclude paths that:

- start with `artifacts/`, `codex_pytest_tmp/`, `docs/audits/`, `.pytest_cache/`
- end with `.bak`

### 6b. Touch count

For measurement commit `M` and watch start `W`:

```text
REV_RANGE = W..M   # git: revisions reachable from M but not from W (exclusive of W)
```

For each commit in `REV_RANGE`, for each population path in `git log REV_RANGE --name-only --pretty=format:`:

```text
touch[path] += 1   # at most once per commit per path
total_touches = sum(touch.values())
```

### 6c. Hotspot thresholds

| Threshold | Role | CK column |
|---|---|---|
| **T_touch = 3** | Primary gate for "Files Above Threshold" | Files Above Threshold |
| **T_fi = 10** | Supplementary structural hub count | Notes only |

### 6d. Top 5 / Top 10 concentration

```text
ranked = sort hotspots by (-touch[path], path)   # tie-break: alphabetical path ascending
top5_share_pct  = round(100 * sum(touch[p] for p in top 5) / total_touches, 2)
top10_share_pct = round(100 * sum(touch[p] for p in top 10) / total_touches, 2)
```

If `total_touches == 0`, all percentages are `0.00` and lists are empty (valid at watch activation).

### 6e. Largest hotspot

File path with maximum `touch[path]`; report `path (share_pct%)` where `share_pct = round(100 * touch[path] / total_touches, 2)`.

### 6f. HCI headline

```text
HCI = top5_share_pct   # CK-GIT primary; baseline_version 1
```

Change only with `baseline_version` bump in the standard doc.

### 6g. Measurement window

```text
W = 85855df  (CK watch start commit)
M = HEAD at measurement time (or named closeout commit)
REV_RANGE = W..M
```

Cadence: one row per **significant maintenance cycle** closeout commit (not nightly). Window grows cumulatively from watch start — **do not** reset window between cycles (cumulative watch).

**Materiality for compression/expansion events:**

- Compression: Top 5 % decreases by ≥ **2.0** pp OR files above T_touch decreases by ≥ **3**
- Expansion: Top 5 % increases by ≥ **2.0** pp OR new path enters top-3 with ≥ **2** touches in window

### 6h. Supplementary FI (Lane A)

At same commit `M`:

```text
python scripts/bu_final_emission_coupling_discovery.py
# Read docs/audits/BU_import_fan_in_fan_out.csv
fi_top5_share_pct  = round(100 * sum(fan_in_total top 5 modules) / sum(all fan_in_total), 2)
fi_top10_share_pct = round(100 * sum(fan_in_total top 10 modules) / sum(all fan_in_total), 2)
files_above_T_fi   = count(modules where fan_in_total >= 10)
```

Record in CK **Notes** as: `FI top5=X% top10=Y% above_T10=Z`.

---

## 7. Repeatability Dry-Run

Procedure executed twice on same commit without workspace writes.

### 7a. CK-GIT primary (`85855df..HEAD` at watch activation)

| Field | Run 1 | Run 2 | Match? |
|---|---|---:|---|
| top5_share_pct | 0.00 | 0.00 | Yes |
| top10_share_pct | 0.00 | 0.00 | Yes |
| largest hotspot | (none) | (none) | Yes |
| files_above_threshold (T_touch=3) | 0 | 0 | Yes |
| top-10 ranking order | [] | [] | Yes |

**Expected:** Watch start equals HEAD → empty window → zero metrics. First meaningful CK row occurs after the next post-`85855df` maintenance commit.

### 7b. Methodology validation window only (`5f0ad53..85855df` — **not CK baseline**)

Proves aggregation logic is stable; do not insert into CK log.

| Field | Run 1 | Run 2 | Match? |
|---|---|---:|---|
| top5_share_pct | 9.52 | 9.52 | Yes |
| top10_share_pct | 18.10 | 18.10 | Yes |
| largest hotspot | `tests/test_ownership_registry.py` (1.90%) | same | Yes |
| files_above_threshold (T_touch=3) | 0 | 0 | Yes |
| total_touches | 105 | 105 | Yes |
| distinct_paths | 96 | 96 | Yes |

### 7c. FI supplementary parse (existing BU CSV, read twice)

| Field | Run 1 | Run 2 | Match? |
|---|---|---:|---|
| top5_share_pct | 20.79 | 20.79 | Yes |
| top10_share_pct | 32.76 | 32.76 | Yes |
| largest hotspot | `tests.helpers.replay_fem_read_smoke` (5.56%) | same | Yes |
| files_above_T_fi (≥10) | 39 | 39 | Yes |
| top-10 module order | stable | stable | Yes |

**Note:** On-disk BU CSV (`total_fi=1044`, 236 modules) differs from frozen BV17 JSON (`total_fi=1109`, 230 modules, 2026-06-21) — expected repository drift; CK uses **fresh BU CSV at measurement commit**, not BV17 JSON.

### Hotspot Measurement Consistency verdict

**STABLE_WITH_EXEMPT_FIELDS**

- CK-GIT aggregation is deterministic (git log is stable at fixed commit).
- FI parse from fixed CSV is deterministic.
- Generators with timestamps (`bv17_hotspot_analysis.json` `generated_at`, `replay_maintenance_metrics.json`, `test_audit` `generated_utc`) are **stability-exempt** — compare metric fields only.
- BU CSV regeneration is deterministic for a fixed tree (AST-only; no timestamp columns in CSV).

---

## 8. Drift Risk Assessment

| Question | Verdict | Mitigation |
|---|---|---|
| Future HCI comparable if only maintenance code changes? | **Yes** | Fixed REV_RANGE rule + locked formulas |
| File moves/renames break touch continuity? | **Mitigated** | Cumulative window; optional `--follow` deferred to v2; document rename events in Notes |
| Module splits change FI without burden change? | **Yes (FI lane)** | FI supplementary only; do not drive HCI |
| Cycles comparable if window length varies? | **Mitigated** | Cumulative window from `85855df`; each row reports `M` commit |
| BV17 JSON alone satisfies CK? | **No** | Missing top10_share; module not file; static not touch; stale |
| BR classification required for repo-wide touches? | **No** | CK-GIT uses raw `git log` path aggregation |

---

## 9. CK Measurement Recipe

```powershell
# Variables
# W = 85855df (watch start)
# M = current HEAD or named closeout commit

# 1. Primary CK-GIT touches (read-only)
git log 85855df..HEAD --name-only --pretty=format: |
  python -c "<CK touch aggregator per standard doc>"

# 2. Supplementary FI snapshot (regenerates audit CSV; read-only for production code)
python scripts/bu_final_emission_coupling_discovery.py
# Parse docs/audits/BU_import_fan_in_fan_out.csv → FI top5/top10/above_T10 for Notes

# 3. Optional subsystem context (Notes only)
python tools/replay_maintenance_metrics.py
```

### CK column mapping

| CK column | Source |
|---|---|
| Commit | `M` short hash |
| Date | `git log -1 --format=%ad M` |
| Top 5 % | CK-GIT `top5_share_pct` |
| Top 10 % | CK-GIT `top10_share_pct` |
| Largest Hotspot | CK-GIT `largest path (share%)` |
| Files Above Threshold | CK-GIT count `touch >= 3` |
| Notes | `REV_RANGE`; total_touches; FI supplementary; cycle label |

---

## 10. Proposed Standard Doc

**Path:** `docs/processes/hotspot_compression_measurement_standard.md`  
**Status:** Drafted (version 1) in this CI_2 pass.

---

## 11. Judgments

| Judgment | Verdict | Evidence |
|---|---|---|
| Measurement methodology can be stabilized | **Yes** | CK-GIT + supplementary FI dual-lane locked above |
| Future HCI values will remain comparable | **Yes** | Deterministic dry-run; cumulative window; versioned HCI formula |
| Maintenance cycles comparable without methodological drift | **Partial** | Comparable if same standard v1 and cumulative window; rename/split events need Notes discipline |

---

## 12. CK / Standard Amendments Recommended (do not apply in CI_2)

1. Replace CK §Measurement Procedure ambiguous "import fan-in and/or git touch" with link to `docs/processes/hotspot_compression_measurement_standard.md`.
2. Lock `T_touch=3` and `HCI = top5_share_pct` in CK baseline section when first measurement row is recorded.
3. Clarify cumulative window `85855df..M` in CK metadata (currently says future-only, which is correct).

**CK log status:** Watch activation row remains `pending` — not backfilled.

---

## 13. Files to Pass Back

### Must pass back
- `CI_2_hotspot_compression_measurement_standard_discovery.md` (this file)
- `docs/processes/hotspot_compression_measurement_standard.md`
- `docs/audits/CK_hotspot_compression_watch.md`

### Strongly recommended
- `docs/audits/BU_post_bj_fan_in_fan_out_validation.md`
- `docs/audits/BU_import_fan_in_fan_out.csv`
- `artifacts/bv17_hotspot_analysis.json`
- `tests/helpers/bug_fix_locality_metric.py`
- `tools/replay_maintenance_metrics.py`
