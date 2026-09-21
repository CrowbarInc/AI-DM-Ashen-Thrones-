# CI_7 — First Measurement Integration Validation

**Date:** 2026-06-26  
**Scope:** Discovery and integration validation only. No production code changes. CK watch ledger **not** modified.  
**Primary metric:** Measurement Integration Consistency

---

## Scope

| Field | Value |
|---|---|
| Inspected branch | `feature/stabilized-foundation` |
| Watch start (W) | `85855df` (`85855df00ebdee20a33c0ada447c178bf1f49820`) |
| Measurement commit (M) | `3709523` (`37095232a3a0f09096ac5654c0059ca53cde0a56`) |
| REV_RANGE | `85855df..3709523` |
| Commits in window | 1 (`3709523` — CI_5 CK-GIT report generator) |
| CK generator run | **Yes** — deterministic `--measurement-commit 3709523` |
| Watch ledger updated | **No** — integration mapping only (dry-run) |

**Validation context:** One post-watch commit exists (CI_5 tooling). CK cadence defines measurements at **significant maintenance cycle** closeouts; CI_7 validates **field mapping and artifact consistency**, not whether CI_5 qualifies as the first ledger row. The permanent watch log remains at watch-activation placeholders.

**Command executed:**

```powershell
python tools/ck_hotspot_compression_report.py --measurement-commit 3709523 --cycle-label "CI_7 integration validation"
```

---

## Tooling Status

| Item | Status |
|---|---|
| CK report generator exists | **Yes** |
| CLI entry point | `tools/ck_hotspot_compression_report.py` |
| Calculation helper | `tests/helpers/ck_hotspot_compression_report.py` |
| Contract tests | `tests/test_ck_hotspot_compression_report.py` (10 passed) |
| Generator run | **Success** — exit 0; artifacts written |
| Blocker for CI_5 | **None** — CI_5 delivered before CI_7 |

---

## Artifact Inventory

| Artifact | Path | Role | Generated or Existing? | Status |
|---|---|---|---|---|
| CK-GIT report generator (CLI) | `tools/ck_hotspot_compression_report.py` | Operator entry point | Existing (CI_5) | Active |
| CK-GIT report helper | `tests/helpers/ck_hotspot_compression_report.py` | Aggregation, JSON/MD writer | Existing (CI_5) | Active |
| Contract tests | `tests/test_ck_hotspot_compression_report.py` | Determinism guard | Existing (CI_5) | Passing |
| Machine report | `artifacts/ck1_hotspot_compression_report.json` | Authoritative CK-GIT + CK-FI payload | **Generated** (CI_7 run) | Current |
| Human report | `artifacts/ck1_hotspot_compression_report.md` | Review + CK log draft table | **Generated** (CI_7 run) | Current |
| Watch ledger | `docs/audits/CK_hotspot_compression_watch.md` | Longitudinal HCI ledger | Existing | Unchanged |
| Measurement standard | `docs/processes/hotspot_compression_measurement_standard.md` | Threshold + formula authority | Existing | v1 |
| CK-FI input | `docs/audits/BU_import_fan_in_fan_out.csv` | Supplementary FI lane | Existing (on-disk) | Parsed |
| Operational closeout | `CI_6_hotspot_compression_operational_readiness_closeout.md` | Readiness verdict | Existing | Closed |

---

## Watch Field Source Map

### Measurement Log columns (`CK_hotspot_compression_watch.md` §Measurement Log)

| Watch Field | Authoritative Source | Source Path / JSON Path / Section | Value Observed | Manual Interpretation Needed? | Notes |
|---|---|---|---|---|---|
| Measurement | Generated CK JSON | `ck_log_draft.measurement` | `CI_7 integration validation` | **Yes** — requires `--cycle-label` CLI flag | Defaults to `scheduled measurement` without flag |
| Commit | Generated CK JSON | `ck_log_draft.commit` / `measurement_window.measurement_commit` | `3709523` | No | From `--measurement-commit` or HEAD |
| Date | Generated CK JSON | `ck_log_draft.date` / `measurement_window.measurement_date` | `2026-06-26` | No | Git commit date of M |
| Top 5 % | Generated CK JSON | `ck_log_draft.top_5_pct` / `ck_git.top5_share_pct` | `100.0` | No | HCI primary |
| Top 10 % | Generated CK JSON | `ck_log_draft.top_10_pct` / `ck_git.top10_share_pct` | `100.0` | No | |
| Largest Hotspot | Generated CK JSON | `ck_log_draft.largest_hotspot` / `ck_git.largest_hotspot.display` | `tests/helpers/ck_hotspot_compression_report.py (50.0%)` | No | |
| Files Above Threshold | Generated CK JSON | `ck_log_draft.files_above_threshold` / `ck_git.files_above_threshold` | `0` | No | T_touch gate |
| Notes | Generated CK JSON | `ck_log_draft.notes` | `std=v1; REV_RANGE=85855df..3709523; total_touches=2; FI top5=20.79% top10=32.76% above_T10=39; cycle=CI_7 integration validation` | No | Includes CK-FI supplementary |

### Baseline section fields (populate on first real measurement row)

| Watch Field | Authoritative Source | Source Path / JSON Path / Section | Value Observed | Manual Interpretation Needed? | Notes |
|---|---|---|---|---|---|
| Top 10 most-touched files | Generated CK JSON | `ck_git.top_10_paths` / `ck_git.hotspot_rankings` | 2 paths (see ranking summary) | **No** for values; **Yes** for markdown formatting | Not emitted in `ck_log_draft`; copy from JSON |
| Top 5 touch share | Generated CK JSON | `ck_git.top5_share_pct` | `100.0` | No | Same as HCI |
| Top 10 touch share | Generated CK JSON | `ck_git.top10_share_pct` | `100.0` | No | |
| Largest single hotspot | Generated CK JSON | `ck_git.largest_hotspot.display` | `tests/helpers/ck_hotspot_compression_report.py (50.0%)` | No | |
| Files above hotspot threshold | Generated CK JSON | `ck_git.files_above_threshold` | `0` | No | |
| Hotspot threshold | Measurement standard + JSON | `docs/processes/hotspot_compression_measurement_standard.md` §T_touch; `ck_git.t_touch` | `3` | No | CK baseline text still says `_define at first measurement_`; standard wins |
| HCI headline | Generated CK JSON | `ck_git.hci` / `ck_log_draft.hci` | `100.0` | No | `HCI = top5_share_pct` per standard v1 |

### Governance / readiness fields (not CK log columns; traceability)

| Field | Authoritative Source | Source Path | Value Observed | Manual Interpretation? | Notes |
|---|---|---|---|---|---|
| generation_status | Generated CK JSON | `generation_status` | `success` | No | |
| measurement_readiness | Generated CK JSON | `measurement_readiness` | `measurement_ready` | No | Enum: `empty_window` / `insufficient_data` / `measurement_ready` |
| data_sufficient | Generated CK JSON | `data_sufficient` | `true` | No | |
| standard_version | Generated CK JSON | `standard_version` | `1` | No | |
| T_touch | Generated CK JSON + standard | `ck_git.t_touch` | `3` | No | |
| T_fi (Notes only) | Generated CK JSON + standard | `ck_fi.t_fi` | `10` | No | Supplementary |
| REV_RANGE | Generated CK JSON | `measurement_window.rev_range` | `85855df..3709523` | No | |
| Generator identity | Generated CK JSON | `report_provenance.generator` | `tools/ck_hotspot_compression_report.py` | No | Actual argv **not** stored (see Traceability) |

### Compression / Expansion events

| Watch Field | Authoritative Source | Manual Interpretation? | Notes |
|---|---|---|---|
| Compression Events row | Operator vs prior log row | **Yes** | Standard materiality rules; **N/A** for first numeric row |
| Expansion Events row | Operator vs prior log row | **Yes** | Same; deferred until second measurement |

### Proposed watch log row (dry-run — **not inserted**)

| Measurement | Commit | Date | Top 5 % | Top 10 % | Largest Hotspot | Files Above Threshold | Notes |
|---|---|---|---:|---:|---|---:|---|
| CI_7 integration validation | `3709523` | 2026-06-26 | 100.0 | 100.0 | `tests/helpers/ck_hotspot_compression_report.py (50.0%)` | 0 | `std=v1; REV_RANGE=85855df..3709523; total_touches=2; FI top5=20.79% top10=32.76% above_T10=39; cycle=CI_7 integration validation` |

---

## Measurement Values

| Metric | Value |
|---|---:|
| **HCI (Top 5 %)** | 100.0 |
| **Top 5 concentration** | 100.0% |
| **Top 10 concentration** | 100.0% |
| **Total touches** | 2 |
| **Distinct paths** | 2 |
| **Files above T_touch=3** | 0 |
| **T_touch** | 3 |
| **T_fi (Notes)** | 10 |
| **measurement_readiness** | `measurement_ready` |
| **generation_status** | `success` |

**Hotspot ranking summary** (deterministic: desc touches, asc path tie-break):

| Rank | Path | Touches | Share % |
|---:|---|---:|---:|
| 1 | `tests/helpers/ck_hotspot_compression_report.py` | 1 | 50.0 |
| 2 | `tests/test_ck_hotspot_compression_report.py` | 1 | 50.0 |

**Measurement window:** `85855df..3709523` (1 commit)

**Generator command:**

```powershell
python tools/ck_hotspot_compression_report.py --measurement-commit 3709523 --cycle-label "CI_7 integration validation"
```

---

## Artifact Consistency Findings

JSON and Markdown are rendered from the **same in-memory report dict** in `write_ck_hotspot_compression_report()` — no separate calculation paths.

| Field | JSON | Markdown | Match? |
|---|---|---|:---:|
| HCI | `ck_git.hci` = 100.0 | §CK-GIT Primary Metrics | Yes |
| Top 5 % | `ck_git.top5_share_pct` = 100.0 | §CK-GIT Primary Metrics | Yes |
| Top 10 % | `ck_git.top10_share_pct` = 100.0 | §CK-GIT Primary Metrics | Yes |
| T_touch | `ck_git.t_touch` = 3 | §CK-GIT Primary Metrics | Yes |
| Largest hotspot | `ck_git.largest_hotspot.display` | §CK-GIT + draft row | Yes |
| Rankings (2 rows) | `ck_git.hotspot_rankings` | §Hotspot Rankings table | Yes |
| Readiness | `measurement_ready` | §Report Status | Yes |
| REV_RANGE | `85855df..3709523` | §Measurement Window | Yes |
| M commit | `3709523` | §Measurement Window + draft row | Yes |
| CK log draft row | `ck_log_draft.*` | §CK Log Draft Row table | Yes |
| CK-FI Notes fragment | embedded in `ck_log_draft.notes` | draft row Notes column | Yes |

**Internal consistency:** `ck_log_draft.hci` == `ck_git.hci` == `ck_git.top5_share_pct` == `ck_log_draft.top_5_pct` (100.0). Threshold fields consistent across JSON and standard v1.

**Sorting / tie-break:** Equal touch counts (1 each); `tests/helpers/...` ranks before `tests/test_...` (lexicographic ascending path). Deterministic.

**Discrepancies:** None observed between JSON and Markdown for the CI_7 run.

---

## Traceability Findings

| Trace link | Present? | Evidence |
|---|---|---|
| Commit/range inspected | **Yes** | `measurement_window.rev_range`, `watch_start_commit`, `measurement_commit` |
| Generator command | **Partial** | Command recorded in this report; **not** persisted in JSON `report_provenance` |
| Generated JSON artifact | **Yes** | `artifacts/ck1_hotspot_compression_report.json` |
| Generated Markdown artifact | **Yes** | `artifacts/ck1_hotspot_compression_report.md` |
| Threshold source | **Yes** | `ck_git.t_touch` (= standard v1 `T_touch=3`); `ck_fi.t_fi` (= 10) |
| Watch-entry field mapping | **Yes** | `ck_log_draft` maps 1:1 to Measurement Log columns |
| Baseline field mapping | **Partial** | Values in `ck_git.*`; no dedicated baseline block in report |
| pytest regression anchor | **Yes** | Validation window `5f0ad53..85855df` locked in tests |

**Traceability gap:** JSON `report_provenance` records generator **module path** but not the **invocation argv** (e.g. `--measurement-commit`, `--cycle-label`). Future audits must rely on operator notes or external run logs for exact command replay. Not blocking — values are fully determined by M + W + repo state.

**Repeatability:** Re-running the same command on the same commit produces identical numeric output (verified in CI_6 double-run).

---

## Integration Readiness

**Verdict: `ready_with_notes`**

**Why not `blocked`:** CK-GIT generator exists; all Measurement Log columns have a single authoritative JSON source (`ck_log_draft` / `ck_git`); JSON and Markdown are synchronized; thresholds are populated consistently; no missing tool, schema, or contract.

**Why not plain `ready`:**

1. **Measurement label** requires operator to pass `--cycle-label` — otherwise defaults to `scheduled measurement`.
2. **Baseline section** (Top 10 file list, HCI headline block) is not auto-rendered into a ledger-ready markdown fragment — operator copies from `ck_git.top_10_paths` and concentration fields.
3. **Ledger update** remains manual markdown edit — no committed auto-update workflow (by design in CI_6).
4. **Qualifying cycle selection** for M is operator policy (CK cadence); tool does not enforce "significant maintenance cycle" vs tooling commit.
5. **Command argv** not stored in generated JSON — minor traceability note.

None of these are blocking for integrating the **first post-watch maintenance measurement** once a qualifying cycle closes.

---

## Gaps / Blockers

| Gap | Classification | Exact detail |
|---|---|---|
| `--cycle-label` required for meaningful Measurement column | **Note** | Default: `ck_log_draft.measurement` = `"scheduled measurement"` |
| Baseline Top-10 list not in `ck_log_draft` | **Note** | Source: `ck_git.top_10_paths` — single authority, extra copy step |
| No argv in `report_provenance` | **Note** | Missing field: `report_provenance.command` or equivalent |
| CK baseline threshold text stale | **Note** | `CK_hotspot_compression_watch.md` line 38 vs standard `T_touch=3` |
| Standard recipe still references placeholder aggregator | **Note** | `hotspot_compression_measurement_standard.md` §Measurement Recipe |
| No automated ledger writer | **Note** | Expected; manual append per CI_6 |
| Compression/expansion on first row | **Note** | N/A until second measurement per standard |

**Blocking items:** **None**

---

## Measurement Integration Consistency Verdict

| Criterion | Result |
|---|---|
| Generated report traceable to commit/range + command | **Pass** (command in audit trail; range in JSON) |
| Every watch log field has one authoritative source | **Pass** (with baseline fields from `ck_git`, not `ck_log_draft`) |
| Ledger updatable without manual HCI interpretation | **Pass** (numeric fields copy directly; label + baseline formatting need operator input) |
| JSON / Markdown synchronized | **Pass** |
| Governance / threshold fields consistent | **Pass** |
| Blockers reduced to exact items | **Pass** — no blockers; notes listed above |

---

## Files to Pass Back

### Must pass back (if reviewing integration)
- `CI_7_first_measurement_integration_validation.md` (this file)
- `artifacts/ck1_hotspot_compression_report.json`
- `artifacts/ck1_hotspot_compression_report.md`
- `docs/audits/CK_hotspot_compression_watch.md`

### Strongly recommended
- `tools/ck_hotspot_compression_report.py`
- `tests/helpers/ck_hotspot_compression_report.py`
- `tests/test_ck_hotspot_compression_report.py`
- `docs/processes/hotspot_compression_measurement_standard.md`
- `CI_6_hotspot_compression_operational_readiness_closeout.md`

**CK log:** unchanged — watch activation row remains `pending`.
