# CI_4 — Hotspot Compression Operational Readiness Discovery

**Date:** 2026-06-26  
**Scope:** Discovery and documentation assessment only. No production code changes. CK log not modified.

---

## 1. Scope

| Field | Value |
|---|---|
| Inspected commit | `85855df` (`85855df00ebdee20a33c0ada447c178bf1f49820`) |
| Inspected branch | `feature/stabilized-foundation` |
| Inspected date | 2026-06-26 |
| CK watch start | `85855df` (2026-06-26) |
| Measurement standard | `docs/processes/hotspot_compression_measurement_standard.md` (v1) |

**Evidence inspected:** operational authority chain (Steps 1–2), read-only CK-GIT/CK-FI dry-run (Step 5), CA11 pattern comparison, repository tool search (no `tools/ck_hotspot_compression_report.py`).

---

## 2. Operator Workflow Outline

End-to-end path from maintenance cycle close to CK ledger update:

1. **Trigger** — A significant maintenance cycle closes (audit closeout, extraction block, governance redistribution, replay/classification contraction, or comparable multi-file program). Identify measurement commit `M` (named closeout commit; default `HEAD` on the watched branch).
2. **Confirm window** — `REV_RANGE = 85855df..M` (cumulative from CK watch start; do not reset).
3. **CK-GIT primary** — Aggregate git path touches per standard v1 (population filters, one touch per commit per path). Compute `top5_share_pct`, `top10_share_pct`, largest hotspot, `files_above_threshold` at `T_touch = 3`. Set `HCI = top5_share_pct`.
4. **CK-FI supplementary** — Run `python scripts/bu_final_emission_coupling_discovery.py`; parse `docs/audits/BU_import_fan_in_fan_out.csv` for FI top5/top10/above_T10. Format Notes: `FI top5=<pct>% top10=<pct>% above_T10=<n>`.
5. **Optional context** — Run `python tools/replay_maintenance_metrics.py` for replay subsystem touch notes (not HCI).
6. **Materiality check** — Compare new row to prior CK log row using standard compression/expansion thresholds (±2.0 pp Top 5, ±3 files above threshold, top-3 entrant rules). **First real row:** no prior row — record measurement only; no compression/expansion event unless comparing informally to activation placeholder.
7. **Update CK ledger** — Manually append one row to `docs/audits/CK_hotspot_compression_watch.md` Measurement Log; update baseline section if first real measurement; optionally append Compression/Expansion Events tables.
8. **Record metadata in Notes** — `std=v1; REV_RANGE=85855df..<M>; total_touches=<n>; <FI notes>; cycle=<label>`.

**Gap:** Step 3 has no committed repository command — operator must implement aggregation ad hoc (see §5).

---

## 3. Artifact Authority Map

| Artifact / field | Authoritative source | Generator / command | Consumer | Single authority? |
|---|---|---|---|---|
| HCI (Top 5 %) | `hotspot_compression_measurement_standard.md` §CK-GIT | **None committed** — ad-hoc `git log` aggregation | CK log | **Partial** — formula yes, tool no |
| Top 10 % | Same | Same | CK log | **Partial** |
| Largest hotspot | Same | Same | CK log | **Partial** |
| Files above threshold | Same (`T_touch = 3`) | Same | CK log | **Partial** |
| CK-FI Notes | Standard §CK-FI | `python scripts/bu_final_emission_coupling_discovery.py` → CSV parse | CK Notes | **Yes** |
| Compression event? | Standard §Compression materiality | Manual judgment vs prior row | CK compression table | **Yes** |
| Expansion event? | Standard §Expansion materiality | Manual judgment vs prior row | CK expansion table | **Yes** |
| Watch ledger | `CK_hotspot_compression_watch.md` | **Manual edit** | Maintainers | **Yes** |
| BU FI CSV | `BU_import_fan_in_fan_out.csv` | `scripts/bu_final_emission_coupling_discovery.py` | CK-FI | **Yes** |
| Replay context (optional) | `artifacts/golden_replay/replay_maintenance_metrics.json` | `python tools/replay_maintenance_metrics.py` | Notes only | **Yes** (optional lane) |
| Top-10 file list (baseline section) | CK baseline placeholders | CK-GIT top-10 paths | CK baseline | **Gap** — not in log columns |

**Is there a committed repo tool for CK-GIT aggregation?** **No.** Standard recipe ends with `git log 85855df..HEAD --name-only --pretty=format:` and comment *"implement via standard aggregator"*.

---

## 4. Operational Readiness Scores

| Dimension | Score (0–3) | Evidence |
|---|---:|---|
| Command reproducibility | **2** | CK-GIT + CK-FI numeric outputs match on double-run when aggregation rules are applied consistently; no committed script |
| Artifact generation | **1** | CK-FI and replay tools emit paths; **CK-GIT has no named output artifact** |
| Documentation completeness | **2** | CK column mapping in standard; top-10 baseline storage ambiguous; aggregator missing |
| Operator consistency | **1** | Two operators may implement CK-GIT filters/dedupe differently without shared tool |
| Trigger clarity | **2** | CK cadence described; no readiness enum like CA11 |
| Materiality clarity | **3** | Thresholds locked in standard v1 |
| Ledger update procedure | **1** | No operator runbook; manual markdown only |
| Failure / empty window | **3** | Empty `85855df..HEAD` documented and verified (zeros) |

**Sum:** 15 / 24  
**Operational Measurement Readiness:** **Partially Ready**

---

## 5. Ambiguity Register

| Check | Pass? | Severity | Notes |
|---|---|---|---|
| CK baseline says threshold `_define at first measurement_` vs standard `T_touch=3` | **Fail** | Minor | Standard wins; CK baseline text stale |
| Recipe references nonexistent aggregator | **Fail** | **Blocker** | No `tools/ck_hotspot_compression_report.py` |
| `W` hardcoded `85855df`; watch reset procedure | **Fail** | Minor | CI_2 closeout requires version bump + baseline reset; no watch-reset runbook |
| `M` selection (HEAD vs closeout commit) | **Partial** | Minor | Standard allows both; operator must record in Notes |
| Top-10 list in baseline but not log columns | **Fail** | Minor | Store in baseline section or Notes — not specified |
| FI Note string format | **Pass** | — | Locked: `FI top5=<pct>% top10=<pct>% above_T10=<n>` |
| Materiality on first real row | **Partial** | Minor | No prior numeric row; events deferred until second measurement |
| PowerShell vs bash recipe | **Partial** | Cosmetic | Recipe uses `powershell` comments; `git log` works in both |

### Manual interpretation items

| Item | Severity |
|---|---|
| Implement CK-GIT aggregation without committed tool | **Blocker** |
| Choose `M` when branch has unpushed commits | Minor |
| Where to persist top-10 path list on first measurement | Minor |
| Whether to run `replay_maintenance_metrics.py` each cycle | Cosmetic |
| Tie-break at equal touch counts (standard says alphabetical path) | Minor — documented |

---

## 6. Operator Dry-Run Results

### 6a. CK-GIT empty window (`85855df..HEAD`)

| Metric | Value |
|---|---:|
| total_touches | 0 |
| top5_share_pct | 0.00 |
| top10_share_pct | 0.00 |
| largest hotspot | (none) |
| files_above_threshold | 0 |
| Double-run match | Yes |

### 6b. Validation window (`5f0ad53..85855df`) — **NOT for CK insertion**

| Metric | Run 1 | Run 2 | Match |
|---|---|---:|---|
| total_touches | 105 | 105 | Yes |
| top5_share_pct | 9.52 | 9.52 | Yes |
| top10_share_pct | 18.10 | 18.10 | Yes |
| largest hotspot | `tests/helpers/failure_dashboard_recurrence.py` (1.90%) | same | Yes |
| files_above_threshold | 0 | 0 | Yes |

Top-10 paths (touch count): `failure_dashboard_recurrence.py` (2), `golden_replay_artifact_manifest.py` (2), `golden_replay_projection.py` (2), five `replay_bug_recurrence*` helpers (2 each), `test_ownership_registry.py` (2), `game/attribution_read_views.py` (1).

### 6c. CK-FI supplementary (existing BU CSV, parse twice)

| Metric | Value | Match on re-parse |
|---|---|---:|
| FI top5_share_pct | 20.79 | Yes |
| FI top10_share_pct | 32.76 | Yes |
| above_T10 | 39 | Yes |
| Notes string | `FI top5=20.79% top10=32.76% above_T10=39` | Yes |

*BU CSV not regenerated in this discovery pass; parse used on-disk snapshot.*

### 6d. Replay context

`artifacts/golden_replay/replay_maintenance_metrics.json` **present** on disk. Optional lane runnable; not required for HCI.

### 6e. Paper row (validation window — do not insert into CK)

| Measurement | Commit | Date | Top 5 % | Top 10 % | Largest Hotspot | Files Above Threshold | Notes |
|---|---|---|---:|---:|---|---:|---|
| VALIDATION ONLY | `85855df` | 2026-06-26 | 9.52 | 18.10 | `tests/helpers/failure_dashboard_recurrence.py` (1.90%) | 0 | `std=v1; REV_RANGE=5f0ad53..85855df; total_touches=105; FI top5=20.79% top10=32.76% above_T10=39; VALIDATION ONLY` |

### Dry-run summary table

| Step | Runnable from docs alone? | Output captured? | Ambiguity? |
|---|---|---|---|
| 5a empty window | Partial — rules yes, tool no | Yes (zeros) | Aggregator implementation |
| 5b validation window | Partial | Yes | Same |
| 5c CK-FI | **Yes** | Yes | Must run BU script first if CSV stale |
| 5d replay context | **Yes** | Yes (artifact exists) | Optional |
| 5e CK row draft | Partial | Yes (paper row) | Top-10 baseline placement |

---

## 7. CA11 Comparison

| CA11 element | CK equivalent | Present? |
|---|---|---|
| Process doc | `hotspot_compression_measurement_standard.md` | **Yes** (measurement standard; not operator runbook) |
| Dedicated CLI tool | `tools/ck_hotspot_compression_report.py` | **No** |
| JSON machine report | `artifacts/ck1_hotspot_compression_report.json` | **No** |
| Markdown human report | `CK_hotspot_compression_watch.md` ledger | **Yes** (manual) |
| Readiness state enum | — | **No** |
| CI / pytest guard | `tests/test_ck_hotspot_compression_report.py` | **No** |

CK has measurement governance (CI_2) but lacks CA11-style **executable self-service**.

---

## 8. Judgments

| Question | Verdict | Evidence |
|---|---|---|
| Can a future maintainer execute HCI workflow using documentation alone? | **Partial** | CK-FI and materiality rules are runnable; CK-GIT requires inventing aggregation |
| Does every required artifact have a single authoritative source? | **Partial** | HCI fields lack committed generator; formulas are authoritative |
| Does manual interpretation remain? | **Yes** | Aggregator implementation, `M` selection, baseline top-10 storage, first-row materiality |
| Is CK ready for its first real measurement cycle? | **Partial** | Procedure is defined; **blocked on CK-GIT tooling or runbook script** for consistent execution |

---

## 9. Recommended CI_4 Closeout Blocks (for Cursor)

1. **`docs/processes/hotspot_compression_watch_process.md`** — Operator runbook (trigger, commands, CK row template, materiality examples, empty-window handling).
2. **`tools/ck_hotspot_compression_report.py`** — Committed CK-GIT + CK-FI aggregator writing `artifacts/ck1_hotspot_compression_report.json` + `.md`.
3. **Update `hotspot_compression_measurement_standard.md`** — Replace “implement via standard aggregator” with tool invocation; fix recipe to reference runbook.
4. **Minor CK doc sync** — Set baseline threshold text to `T_touch = 3`; note top-10 list lives in baseline section on first measurement.
5. **`docs/audits/CI_4_hotspot_compression_operational_readiness_closeout.md`** — Closeout with readiness verdict upgrade path.
6. **`docs/audits/audit_manifest.md`** — Register CI_4 discovery + closeout.
7. **Optional:** `tests/test_ck_hotspot_compression_report.py` — Contract guard for deterministic CK-GIT output on fixed `REV_RANGE`.

---

## 10. Verdict

```text
Operational Measurement Readiness: Partially Ready
CK first real measurement: Partial — blocked on committed CK-GIT aggregator or runbook script
Primary blocker: No committed CK-GIT aggregation tool; standard v1 recipe incomplete for operators
```

---

## 11. Files to Pass Back

### Must pass back
- `CI_4_hotspot_compression_operational_readiness_discovery.md` (this file)
- `docs/processes/hotspot_compression_measurement_standard.md`
- `docs/audits/CK_hotspot_compression_watch.md`
- `docs/audits/CI_2_hotspot_compression_measurement_standard_closeout.md`

### Strongly recommended
- `CI_2_hotspot_compression_measurement_standard_discovery.md`
- `docs/processes/corrective_fix_watch_process.md`
- `tools/corrective_fix_watch.py`
- `scripts/bu_final_emission_coupling_discovery.py`
- `tools/replay_maintenance_metrics.py`

### On disk at discovery
- `docs/audits/BU_import_fan_in_fan_out.csv`
- `artifacts/golden_replay/replay_maintenance_metrics.json`

**CK log:** unchanged — watch activation row remains `pending`.
