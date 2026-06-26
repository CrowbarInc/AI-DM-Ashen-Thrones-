# Hotspot Compression Watch Process

**Primary metric:** Hotspot Concentration Index (HCI) — CK-GIT Top 5 Share %  
**Scope:** CK watch #1 — cumulative git path touches from `85855df..M`

## Purpose

The Hotspot Compression Watch tracks whether high-touch files continue to dominate maintenance effort or responsibility spreads across smaller modules. Measurements use the **CK-GIT** primary lane per [`hotspot_compression_measurement_standard.md`](hotspot_compression_measurement_standard.md) (v1).

## Trigger conditions

Record a CK measurement when a **significant maintenance cycle** closes:

- audit closeout (CE, CF, CG, CH, etc.)
- extraction block
- governance redistribution
- replay or classification contraction
- comparable multi-file maintenance program

**Exclude** tooling-only commits (generators, docs-only automation) unless explicitly adopted as a measurement anchor. When in doubt, defer until the next qualifying cycle.

## Running the measurement

```powershell
# M = closeout commit for the qualifying cycle (not default HEAD unless intentional)
python tools/ck_hotspot_compression_report.py `
  --measurement-commit <M> `
  --cycle-label "<cycle name>"
```

The tool writes:

| Artifact | Role |
|---|---|
| `artifacts/ck1_hotspot_compression_report.json` | Machine-readable CK-GIT + CK-FI report |
| `artifacts/ck1_hotspot_compression_report.md` | Human-readable report + ledger snippet |

**Required flags for production rows:**

- `--measurement-commit` — named closeout commit `M`
- `--cycle-label` — Measurement Log label (e.g. `CH governance redistribution`)

Optional:

- `--watch-start` — default `85855df` (do not change without standard version bump)
- `--bu-csv` — default `docs/audits/BU_import_fan_in_fan_out.csv`

## Supplementary lanes

1. **CK-FI (Notes only)** — refresh when structural coupling may have changed:
   ```powershell
   python scripts/bu_final_emission_coupling_discovery.py
   ```
   Re-run the CK report to embed updated FI top5/top10/above_T10 in Notes.

2. **Replay context (optional, Notes only)**:
   ```powershell
   python tools/replay_maintenance_metrics.py
   ```

## Updating the watch ledger

1. Open `artifacts/ck1_hotspot_compression_report.md` → **CK Ledger Snippet** section.
2. Copy the fenced markdown block into `docs/audits/CK_hotspot_compression_watch.md`:
   - Append the **Measurement Log row**.
   - On the **first real measurement**, replace baseline placeholders with the **Baseline section** block.
3. Do **not** recompute HCI manually — all numeric fields come from the generator.

## Primary metric

```text
HCI = top5_share_pct   # CK-GIT; standard v1
```

## Readiness states

| State | Meaning |
|---|---|
| `empty_window` | `M == W` or no commits in `REV_RANGE` — valid at watch activation |
| `insufficient_data` | Commits exist but zero population-path touches |
| `measurement_ready` | Non-zero touches; HCI headline populated |

## Materiality (second measurement onward)

Compare the new row to the prior log row per standard v1:

- **Compression:** Top 5 % decreases ≥ 2.0 pp OR files above T_touch decreases ≥ 3
- **Expansion:** Top 5 % increases ≥ 2.0 pp OR new path enters top-3 with ≥ 2 touches

First numeric row: record measurement only; defer compression/expansion events.

## Report fields (machine JSON)

| JSON path | CK use |
|---|---|
| `ck_log_draft` | Measurement Log row |
| `ck_baseline_draft` | Baseline section (first row) |
| `ck_ledger_snippet_md` | Copy-paste markdown for both |
| `ck_git.hci` | HCI headline |
| `ck_git.t_touch` | Threshold (3) |
| `report_provenance.command` | Audit replay |
| `report_provenance.generated_at` | Stability-exempt timestamp |

## Limitations

- Ledger update is manual copy-paste (no auto-writer).
- Qualifying-cycle selection for `M` is operator judgment.
- CK-FI uses on-disk BU CSV unless regenerated first.
- `generated_at` is stability-exempt when comparing metric fields across runs.

## Related artifacts

| Artifact | Role |
|---|---|
| [hotspot_compression_measurement_standard.md](hotspot_compression_measurement_standard.md) | Measurement authority (v1) |
| [CK_hotspot_compression_watch.md](../audits/CK_hotspot_compression_watch.md) | Active HCI ledger |
| [CJ_corrective_cohort_watch.md](../audits/CJ_corrective_cohort_watch.md) | Complementary corrective locality watch |
