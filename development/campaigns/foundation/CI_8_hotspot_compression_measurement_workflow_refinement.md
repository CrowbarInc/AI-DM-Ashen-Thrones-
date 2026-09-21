# CI_8 — Hotspot Compression Measurement Workflow Refinement

**Date:** 2026-06-26  
**Scope:** Workflow refinement — documentation, provenance, ledger snippet. No production code changes. CK watch ledger **not** modified.  
**Primary metric:** Measurement Workflow Completeness

---

## Scope

| Field | Value |
|---|---|
| Upstream | CI_5 (generator), CI_6 (operational readiness), CI_7 (integration validation) |
| Inspected commit (M) | `3709523` (HEAD at dry-run) |
| REV_RANGE | `85855df..3709523` |
| Generator run | **Yes** — `CI_8 workflow dry-run` |
| CK log updated | **No** |

**Dry-run command:**

```powershell
python tools/ck_hotspot_compression_report.py --measurement-commit HEAD --cycle-label "CI_8 workflow dry-run"
```

---

## Manual Step Inventory

| Step | Current method | Authoritative source | Manual interpretation? | Standardizable? | CI_8 action |
|---|---|---|---|---|---|
| Trigger / cadence | Operator judgment | CK watch + runbook | Yes | Defer | **Documented** in runbook (exclude tooling-only commits) |
| Choose measurement commit M | CLI `--measurement-commit` | Operator + git | Yes | Defer | **Documented** — named closeout, not default HEAD |
| Run CK-GIT generator | CLI | `tools/ck_hotspot_compression_report.py` | No | Yes | **Exists**; recipe updated |
| Regenerate BU CSV (CK-FI) | Optional CLI | `scripts/bu_final_emission_coupling_discovery.py` | Yes (when needed) | Document | **Documented** in runbook |
| Optional replay context | Optional CLI | `tools/replay_maintenance_metrics.py` | Yes | Document | **Documented** in runbook |
| Record cycle label | CLI `--cycle-label` | `ck_log_draft.measurement` | No if flag passed | Yes | **Documented** as required for production |
| Copy Measurement Log row | Copy-paste snippet | `ck_ledger_snippet_md` | No | Yes | **Implemented** |
| Update baseline (first row) | Copy-paste snippet | `ck_baseline_draft` in snippet | No | Yes | **Implemented** |
| Compression/expansion judgment | Manual vs prior row | Standard v1 materiality | Yes | Defer | **Documented** (N/A first row) |
| Append to CK watch ledger | Manual markdown edit | `CK_hotspot_compression_watch.md` | No (paste only) | Partial | **Snippet** removes field assembly |

---

## CI_7 Gap Resolution Matrix

| CI_7 gap | CI_8 action | Status |
|---|---|---|
| No operator runbook | Created `docs/processes/hotspot_compression_watch_process.md` | **Resolved** |
| Standard recipe placeholder aggregator | Updated §Measurement Recipe to cite CLI | **Resolved** |
| No argv in `report_provenance` | Added `command`, `generated_at`, paths | **Resolved** |
| No baseline draft in report | Added `ck_baseline_draft` | **Resolved** |
| No ledger-ready snippet | Added `ck_ledger_snippet_md` + MD section | **Resolved** |
| `--cycle-label` required | Runbook marks required for production rows | **Resolved** (documented) |
| CK baseline threshold text stale | Synced to `T_touch = 3` | **Resolved** |
| Manual ledger copy | Snippet copy-paste (no auto-writer) | **Standardized** |
| Qualifying-cycle selection for M | Runbook guidance; defer enforcement | **Deferred** |

---

## Provenance Assessment

| Field | Required? | Before CI_8 | After CI_8 |
|---|---|---|---|
| `generator` | Yes | Present | Present |
| `helper` | Yes | Present | Present |
| `command` | Yes | **Missing** | **Present** in JSON + MD §Provenance |
| `generated_at` | Optional (stability-exempt) | Missing | Present |
| `bu_csv_path` | Yes | Partial (ck_fi only) | Present in provenance |
| `output_json` / `output_md` | Yes | Missing | Present |
| W / M full hashes | Yes | `measurement_window` | Unchanged |
| `schema_version` | Yes | 1 | **2** (baseline + snippet + provenance) |

**Audit replay:** Sufficient — `report_provenance.command` + `measurement_window` fully determine reproducible inputs.

---

## Ledger Integration Assessment

| Artifact | Role | Status |
|---|---|---|
| `ck_log_draft` | Measurement Log columns | Existing; unchanged contract |
| `ck_baseline_draft` | Baseline section values | **New** — machine-readable |
| `ck_ledger_snippet_md` | Copy-paste markdown block | **New** — human-ready |
| MD §CK Ledger Snippet | Fenced snippet in report | **New** |

Production row can be recorded by copying one fenced block — **no manual HCI calculation or field assembly**.

---

## Documentation Assessment

| Item | Before | After |
|---|---|---|
| `hotspot_compression_watch_process.md` | Missing | **Created** |
| Standard §Measurement Recipe | Placeholder git log | **CLI citation** |
| CK watch procedure | Standard link only | **Runbook + snippet + artifact links** |
| CK baseline T_touch text | Stale | **Synced** (`T_touch = 3`) |
| `audit_manifest.md` CI_7/CI_8 | Partial | **Updated** |

---

## Workflow Dry-Run Results

| Field | Value |
|---|---|
| Command | `python tools/ck_hotspot_compression_report.py --measurement-commit HEAD --cycle-label 'CI_8 workflow dry-run'` |
| JSON | `artifacts/ck1_hotspot_compression_report.json` |
| Markdown | `artifacts/ck1_hotspot_compression_report.md` (84 lines) |
| HCI | 100.0 |
| Top 5 / Top 10 | 100.0% / 100.0% |
| Readiness | `measurement_ready` |
| Snippet present | Yes |
| Sufficient for production row | **Yes** (paste snippet; CI_5 commit is tooling — defer ledger insert per cadence) |

---

## Completeness Scores

| Dimension | Before (CI_7) | After (CI_8) |
|---|---:|---:|
| Workflow documentation | 2 | **3** |
| Command / provenance capture | 1 | **3** |
| Artifact → ledger mapping | 2 | **3** |
| Baseline integration | 1 | **3** |
| Operator ergonomics | 2 | **3** |
| Cross-operator reproducibility | 3 | **3** |
| Institutional-knowledge dependence | 2 | **3** |
| **Total** | **13 / 21** | **21 / 21** |

---

## Recommended Follow-On Blocks

| Block | Scope | Priority |
|---|---|---|
| *(none required)* | Routine CK measurements can proceed | — |
| Optional CI_9 | Auto-ledger writer (if manual paste becomes burden) | Low / defer |
| Optional | Enforce `--cycle-label` required in CLI (exit 1 if missing) | Low |

---

## Measurement Workflow Completeness Verdict

**Ready**

All CI_7 notes resolved or explicitly deferred. Operators can perform CK measurements using runbook + generator + ledger snippet without institutional knowledge of aggregation rules.

---

## Files Changed

| File | Change |
|---|---|
| `tests/helpers/ck_hotspot_compression_report.py` | `ck_baseline_draft`, `ck_ledger_snippet_md`, provenance enrichment, schema v2 |
| `tools/ck_hotspot_compression_report.py` | `format_invocation_command`, pass provenance to writer |
| `tests/test_ck_hotspot_compression_report.py` | Baseline + provenance + snippet tests |
| `docs/processes/hotspot_compression_watch_process.md` | **New** operator runbook |
| `docs/processes/hotspot_compression_measurement_standard.md` | Recipe cites CLI |
| `docs/audits/CK_hotspot_compression_watch.md` | T_touch sync, runbook links, snippet procedure |
| `docs/audits/audit_manifest.md` | CI_7, CI_8 entries |
| `artifacts/ck1_hotspot_compression_report.json` | Regenerated (dry-run) |
| `artifacts/ck1_hotspot_compression_report.md` | Regenerated (dry-run) |

---

## Files to Pass Back

- `CI_8_hotspot_compression_measurement_workflow_refinement.md` (this file)
- `docs/processes/hotspot_compression_watch_process.md`
- `artifacts/ck1_hotspot_compression_report.json`
- `artifacts/ck1_hotspot_compression_report.md`

**CK log:** unchanged — watch activation row remains `pending`.
