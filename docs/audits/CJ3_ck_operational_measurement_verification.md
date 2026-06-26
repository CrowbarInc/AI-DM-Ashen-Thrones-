# CJ3 — CK Operational Measurement Verification

**Date:** 2026-06-26  
**Scope:** Measurement and documentation only. No production code changes.  
**Primary metric:** Hotspot Measurement Readiness  
**Baseline infrastructure:** CI_1–CI_9 closeout chain; CK watch activated at `85855df`

---

## Workflow Executed

The normal CK workflow was executed per [`docs/processes/hotspot_compression_watch_process.md`](../processes/hotspot_compression_watch_process.md) and [`docs/processes/hotspot_compression_measurement_standard.md`](../processes/hotspot_compression_measurement_standard.md) (v1).

### Commands

```powershell
# 1. Primary CK-GIT + CK-FI report (authoritative workflow step)
python tools/ck_hotspot_compression_report.py `
  --measurement-commit 1f3899b `
  --cycle-label "CJ3 operational verification"

# 2. Empty-window verification (watch start M == W)
python tools/ck_hotspot_compression_report.py `
  --measurement-commit 85855df `
  --cycle-label "CJ3 empty window check"

# 3. Repeatability verification (fixed M, separate output paths)
python tools/ck_hotspot_compression_report.py `
  --measurement-commit 1f3899b `
  --cycle-label "CJ3 repeat A" `
  --output-json artifacts/ck1_repeat_a.json `
  --output-md artifacts/ck1_repeat_a.md

python tools/ck_hotspot_compression_report.py `
  --measurement-commit 1f3899b `
  --cycle-label "CJ3 repeat B" `
  --output-json artifacts/ck1_repeat_b.json `
  --output-md artifacts/ck1_repeat_b.md

# 4. Optional supplementary FI refresh (standard recipe step 2)
python scripts/bu_final_emission_coupling_discovery.py

# 5. Contract verification
python -m pytest tests/test_ck_hotspot_compression_report.py -q --tb=short

# 6. Non-authoritative reference — CH governance window (validation window from CI_6/CI_2)
python tools/ck_hotspot_compression_report.py `
  --watch-start 5f0ad53 `
  --measurement-commit 85855df `
  --cycle-label "CJ3 CH reference (non-authoritative)" `
  --output-json artifacts/ck1_ch_reference.json `
  --output-md artifacts/ck1_ch_reference.md
```

### Outputs

| Step | Exit code | Runtime | Readiness | HCI | Total touches |
|---|---:|---:|---|---:|---:|
| Primary (`1f3899b`) | 0 | ~0.4–1.0 s | `measurement_ready` | 100.0 | 4 |
| Empty window (`85855df`) | 0 | ~0.8 s | `empty_window` | 0.0 | 0 |
| Repeat A / B | 0 | ~0.7 s each | `measurement_ready` | 100.0 | 4 |
| BU FI refresh | 0 | ~11.1 s | — | — | — |
| CH reference (`5f0ad53..85855df`) | 0 | ~1.0 s | `measurement_ready` | 9.52 | 105 |
| Pytest contract | 0 | ~2.7 s | — | — | — |

### Artifacts

| Artifact | Role | Updated by CJ3? |
|---|---|---|
| `artifacts/ck1_hotspot_compression_report.json` | Primary machine report | **Yes** — `M=1f3899b` |
| `artifacts/ck1_hotspot_compression_report.md` | Human report + ledger snippet | **Yes** |
| `artifacts/ck1_repeat_a.json` / `.md` | Repeatability evidence | **Yes** (verification only) |
| `artifacts/ck1_repeat_b.json` / `.md` | Repeatability evidence | **Yes** (verification only) |
| `artifacts/ck1_ch_reference.json` / `.md` | CH-window reference (not CK log row) | **Yes** (verification only) |
| `docs/audits/CK_hotspot_compression_watch.md` | Active HCI ledger | **No** — ledger append deferred (by design) |
| `docs/audits/BU_import_fan_in_fan_out.csv` | CK-FI input | Refreshed by BU script |

### Manual steps required (as documented)

1. Select qualifying measurement commit `M` and `--cycle-label` (operator judgment).
2. Run generator CLI (automatic).
3. Optionally refresh BU CSV before re-run when structural coupling may have changed (~11 s).
4. Copy **CK Ledger Snippet** from `artifacts/ck1_hotspot_compression_report.md` into `CK_hotspot_compression_watch.md`.
5. On first production row, replace baseline placeholders using snippet baseline block.
6. Compare materiality vs prior row for compression/expansion events (N/A until second production row).

**CJ3 did not perform step 4–5** — verification only; watch ledger remains at activation placeholders per CI_9 first-production rules.

---

## Operational Assessment

### Infrastructure reviewed

| Component | Location | Status |
|---|---|---|
| CK-GIT generator CLI | `tools/ck_hotspot_compression_report.py` | Committed, functional |
| Aggregation helper | `tests/helpers/ck_hotspot_compression_report.py` | Committed, pytest-guarded |
| Measurement standard v1 | `docs/processes/hotspot_compression_measurement_standard.md` | Adopted (CI_2) |
| Operator runbook | `docs/processes/hotspot_compression_watch_process.md` | Present (CI_8) |
| Active watch ledger | `docs/audits/CK_hotspot_compression_watch.md` | Active; baseline pending |
| Contract tests | `tests/test_ck_hotspot_compression_report.py` | 12 tests, all passing |
| CI closeout chain | CI_6, CI_8, CI_9 | Ready for routine use |

### Per-stage assessment

| Workflow stage | Automation | Reliability | Repeatability |
|---|---|---|---|
| Trigger / qualifying-cycle selection | **Manual** | High (runbook rules clear) | Operator-dependent |
| Choose `M` + `--cycle-label` | **Manual** | High with explicit flags | Recorded in `ck_log_draft.notes` |
| CK-GIT report generation | **Automatic** | High | **Deterministic** at fixed `M` (verified) |
| CK-FI parse from BU CSV | **Automatic** | High | **Deterministic** at fixed CSV (verified) |
| BU CSV regeneration | **Mostly Automatic** | High (~11 s) | Stable on fixed tree per standard |
| Optional replay metrics | **Manual** (optional) | Not exercised in CJ3 | Partial per standard |
| Ledger snippet generation | **Automatic** | High | Deterministic text from metrics |
| Ledger append to watch doc | **Manual** | High (copy-paste) | No auto-writer by design |
| Compression/expansion judgment | **Manual** | High (thresholds locked in standard) | N/A until ≥2 production rows |
| Contract pytest guard | **Automatic** | High | Locks validation window + empty window |

### Verification checklist

| Check | Result |
|---|---|
| Hotspot report generation succeeds | **Pass** |
| Watch reports update correctly | **Pass** (generator outputs valid snippet; ledger file intentionally unchanged) |
| Historical measurements remain readable | **Pass** — CI_6 validation window (`5f0ad53..85855df`) reproduces HCI 9.52 / 105 touches; pytest locks values |
| Prior measurements preserved | **Pass** — git history + pytest contract; artifact overwrite is expected for `ck1_*` canonical paths |
| Repeated execution deterministic | **Pass** — `ck1_repeat_a.json` and `ck1_repeat_b.json` identical CK-GIT/CK-FI metrics |

---

## Measurement Results

### Official watch window (`85855df..1f3899b`)

Post-watch commits: CI tooling only (`3709523`, `1bc28f7`, `1f3899b`). Per CI_9, this window is **not** suitable for the first production CK baseline row (tooling-only exclusion).

| Metric | Value |
|---|---:|
| HCI (Top 5 %) | 100.0 |
| Top 10 % | 100.0 |
| Total touches | 4 |
| Distinct paths | 2 |
| Files above T_touch=3 | 0 |
| Largest hotspot | `tests/helpers/ck_hotspot_compression_report.py` (50.0%) |

**CK-GIT rankings (complete):**

| Rank | Path | Touches | Share % |
|---:|---|---:|---:|
| 1 | `tests/helpers/ck_hotspot_compression_report.py` | 2 | 50.0 |
| 2 | `tests/test_ck_hotspot_compression_report.py` | 2 | 50.0 |

**CK-FI supplementary (unchanged after BU refresh):** `FI top5=20.79% top10=32.76% above_T10=39`

| Rank | Module | Fan-in | Share % |
|---:|---|---:|---:|
| 1 | `tests.helpers.replay_fem_read_smoke` | 58 | 5.56 |
| 2 | `game.final_emission_text_formatting` | 52 | 4.98 |
| 3 | `tests.helpers.gate_orchestration_smoke` | 41 | 3.93 |
| 4 | `game.final_emission_gate` | 34 | 3.26 |
| 5 | `game.final_emission_visibility_fallback` | 32 | 3.07 |

### Reference window — CH governance (`5f0ad53..85855df`, non-authoritative)

Used for consistency cross-check against CD/CE/CF/CG/CH audit findings. Matches CI_6 locked validation values.

| Metric | Value |
|---|---:|
| HCI | 9.52 |
| Top 10 % | 18.10 |
| Total touches | 105 |
| Files above T_touch=3 | 0 |
| Largest hotspot | `tests/helpers/failure_dashboard_recurrence.py` (1.9%) |

**Top-10 touch ties at 1.9% (2 touches each):** failure-dashboard recurrence family, `golden_replay_projection.py`, replay recurrence helpers, `tests/test_ownership_registry.py`.

### Notable movement

| Observation | Assessment |
|---|---|
| Official window dominated by CK generator files | **Expected** — only CI_5/CI_8/CI tooling commits post-watch |
| CH reference shows **low concentration** (HCI 9.52%) | **Consistent** with CH spreading governance across extracted helpers rather than one file absorbing all touches |
| `test_ownership_registry.py` at 1.9% in CH window, not top-1 | **Consistent** with CH12 — registry still large (5,093 LOC) but git touches distributed across dashboard/recurrence/projection helpers |
| CK-FI top modules unchanged | **Consistent** with CD/CH hub analysis (`replay_fem_read_smoke`, `gate_orchestration_smoke`, FEM modules) |
| CJ1/CJ2 corrective work | **Not yet in git window** — uncommitted; no CK movement from CJ fixes |

**No surprising hotspot movement.** CK-FI structural rankings align with prior audit hub tables; CK-GIT official window reflects tooling commits only, not maintenance regression.

### Consistency with prior audits

| Audit | CK alignment |
|---|---|
| **CD** — ownership registry as coordination hub | CK-FI: `replay_fem_read_smoke` + `gate_orchestration_smoke` top test hubs; CH window includes `test_ownership_registry.py` in top-10 ties |
| **CE** — golden replay / projection concentration | CH window: `golden_replay_projection.py` in top-10 ties at 2 touches |
| **CF** — projection responsibility split | Low per-file git concentration in CH window; no single projection monolith dominates touches |
| **CG** — classification / recurrence dashboard fanout | CH window: `failure_dashboard_recurrence.py` rank #1 at 1.9% |
| **CH** — governance hub redistribution | CH reference HCI 9.52% confirms distributed touch pattern post-redistribution |
| **CI** — CK tooling operational | Official window correctly shows only CK generator/test touches |
| **CJ1/CJ2** — registry failure locality fix | CJ2 production touch is 1 file; not yet measurable in CK-GIT until committed |

---

## Manual Burden

| Manual step | Required every measurement? | Estimated effort |
|---|---|---|
| Qualifying-cycle / `M` selection | Yes | 1–2 min judgment |
| `--cycle-label` naming | Yes | <1 min |
| Generator CLI invocation | No (single command) | <1 min |
| BU CSV refresh | Only when FI coupling may have changed | ~11 s + re-run |
| Ledger snippet copy-paste | Yes | 2–3 min |
| Baseline placeholder replacement | First production row only | 2–3 min |
| Materiality event recording | Second row onward | 1–2 min |

**Overall manual burden estimate: Moderate**

- Core HCI math is fully automatic.
- Two persistent manual steps remain: **`M` selection** and **ledger append**.
- Optional BU refresh adds occasional ~11 s when FI snapshot must be current.

---

## Process Improvements

Small operational improvements only (no CK redesign):

1. **Provenance completeness** — When `--measurement-commit` is passed explicitly, always echo it in `report_provenance.command` (currently omitted when value equals resolved short hash but HEAD default omits flag entirely). Aids audit replay without changing metrics.

2. **First-row operator note** — Add one sentence to the runbook clarifying that `W=85855df` excludes the CH closeout itself from cumulative touches; first production row awaits the next qualifying maintenance closeout **after** watch activation.

3. **Dated verification artifacts** — For operational audits, write to `artifacts/ck1_hotspot_compression_report_<date>.json` when preserving a point-in-time snapshot matters; canonical `ck1_*` overwrite is correct for routine use but erases prior CLI output.

4. **Ledger append checklist** — Single checkbox in runbook: “snippet pasted + HCI headline synced” to reduce missed baseline replacement on first row.

No changes recommended to HCI formula, watch anchor, population filters, or dual-lane model.

---

## Foundation Assessment

**Does CK now function as routine maintenance infrastructure?**

**Yes, with one operational caveat.**

Evidence:

- End-to-end generator workflow completes in **under 1 second** for CK-GIT aggregation.
- **12/12** contract tests pass, including locked validation window (`HCI=9.52`, `total_touches=105`) and empty-window behavior.
- **Deterministic** double-run at fixed `M` confirmed.
- Operator runbook, measurement standard v1, ledger snippet, and provenance fields are all present and aligned (CI_9 workflow completeness **21/21**).
- CK-FI supplementary lane parses BU CSV without manual HCI calculation.

**Caveat:** The watch ledger has **no production measurement row yet** — only activation placeholders. CI tooling commits in `85855df..HEAD` are correctly excluded from first baseline per CI_9. CK is **operationally ready** but **not yet exercised on a qualifying maintenance closeout** in production ledger terms.

CK should be run at the next qualifying closeout (e.g., when CJ1 corrective work lands as a discrete commit, or the next extraction/governance block completes).

---

## Recommendation

| Rating | **Good** |
|---|---|

**Rationale:**

- Infrastructure is **production-ready**: generator, tests, standard, runbook, and deterministic execution all verified live.
- Manual burden is **moderate** but bounded (M selection + ledger paste); no ad-hoc HCI math remains.
- Measurement consistency with CD–CH audit findings is **confirmed** via CK-FI and CH reference window.
- Rating is not **Excellent** because: (1) watch ledger still has pending baseline placeholders, (2) official watch window contains only tooling commits so routine cadence is proven but not yet recorded in the ledger, (3) ledger append remains manual.

**Path to Excellent:** Record first production row at next qualifying maintenance closeout using the documented snippet workflow without deviation.

---

## Test Results

### Commands

```text
python -m pytest tests/test_ck_hotspot_compression_report.py -q --tb=short
```

### Results

| Suite | Outcome |
|---|---|
| `tests/test_ck_hotspot_compression_report.py` | **12 passed** (~2.7 s) |

Included guards: synthetic aggregation, validation window (`5f0ad53..85855df`), empty watch window (`85855df..85855df`), provenance + ledger snippet schema v2.

---

## Completion Criteria

| Criterion | Status |
|---|---|
| CK workflow executed successfully | ✅ |
| Operational burden measured | ✅ Moderate |
| Measurement consistency verified | ✅ Deterministic + aligned with CD–CH |
| Remaining manual work identified | ✅ M selection, ledger paste, optional BU refresh |
| Report completed | ✅ This document |
