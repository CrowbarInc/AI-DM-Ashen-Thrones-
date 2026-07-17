# CJ — Corrective Cohort Watch #3

**Status:** Active  
**Type:** Rolling Evidence Collection  
**Scope:** Documentation and evidence only. No production code changes.

**Purpose:** Maintain a rolling watch for future real corrective fixes so that the next corrective cohort can be established immediately once sufficient evidence exists.

**Watch boundary:** All new work after the [CI closeout](CI_corrective_cohort_validation_2_closeout.md). Historical commits before this watch start are out of scope — do not backfill.

---

## Watch State

| Field | Value |
|---|---|
| Watch start commit | `85855df` (`85855df00ebdee20a33c0ada447c178bf1f49820`) |
| Watch start date | 2026-06-26 |
| Current branch | `feature/stabilized-foundation` |
| Inspected range | `85855df..HEAD` (exclusive of watch start; first qualifying row is the first commit **after** `85855df`) |
| Prior authority | [CI Corrective Cohort Validation #2 Closeout](CI_corrective_cohort_validation_2_closeout.md) — null cohort |

---

## Inherited Baseline (CA4 / CI Authority)

Frozen baseline values retained unchanged from CI closeout. CJ compares future qualifying fixes against these medians.

| Metric | Value |
|---|---:|
| Effective median | 7 files touched |
| Production median | 2.5 files touched |
| Test median | 2 files touched |

**Authority artifacts:** `docs/baselines/ca_corrective_locality_baseline.json`, `docs/audits/CA_corrective_change_locality_cohort.csv`

---

## Qualification Rules

A fix **qualifies** only if it:

- corrects an actual failing behavior
- fixes a regression
- resolves a runtime bug
- fixes a contract mismatch
- fixes a projection failure
- fixes a classification error
- resolves a recurrence issue

A fix **does not qualify** if it is:

- documentation only
- governance redistribution
- audit work
- decomposition
- refactoring
- fixture-only
- tooling-only
- generated artifact updates

Qualification requires a discrete fix boundary separable from broad program work. When in doubt, record the commit in the watch table with `Qualified? = No` and document the exclusion reason in **Notes**.

---

## Qualifying Fix Record Schema

For each future qualifying fix (`Qualified? = Yes`), record:

| Field | Description |
|---|---|
| Commit hash | Full or short hash |
| Short description | One-line fix summary |
| Recurrence related | Yes / No |
| Total files touched | Raw Git changed-path count |
| Production files | Paths under `game/` or `static/` |
| Test files | Paths under `tests/` |
| Fixture files | Golden replay, dashboard fixtures, data snapshots |
| Docs / tooling files | `docs/`, `tools/`, `scripts/`, `.github/` |
| Locality | **Localized** (concentrated in one repair surface) or **Distributed** (multi-area fanout) |

Populate the watch table columns **Total Files**, **Production**, **Test**, **Fixture**, and **Docs** from the file-touch breakdown above.

---

## Watch Table

_Only commits after `85855df` on the watched branch. Initially empty._

| Date | Commit | Fix Summary | Qualified? | Total Files | Production | Test | Fixture | Docs | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| | | | | | | | | | |

---

## Running Statistics

Updated when qualifying fixes are recorded. Placeholders at watch activation:

| Metric | Current value | Baseline (CA4) | Delta |
|---|---:|---:|---|
| Qualifying fixes collected | 0 | 10 (historical cohort) | — |
| Current median files touched | N/A | 7.0 | pending |
| Current production median | N/A | 2.5 | pending |
| Current test median | N/A | 2.0 | pending |

**Comparison against frozen baseline:** Pending — insufficient qualifying fixes (0 collected; entry threshold not met).

---

## Entry Threshold

CJ must **not** be converted into a formal corrective cohort until either:

1. **At least 8 qualifying corrective fixes** have accumulated in the watch table, or
2. **Enough evidence exists** to produce statistically meaningful locality measurements (sample size and distribution reviewed explicitly before promotion).

Until the entry threshold is met, CJ remains active rolling evidence collection only. Promotion to a locked cohort requires a separate closeout cycle with frozen CSV/JSON authority artifacts.

---

## Related Artifacts

| Artifact | Role |
|---|---|
| [CI_corrective_cohort_validation_2_closeout.md](CI_corrective_cohort_validation_2_closeout.md) | Watch boundary authority (null cohort closeout) |
| [CA_program_closeout.md](CA_program_closeout.md) | CA program operational context |
| [docs/baselines/ca_corrective_locality_baseline.json](../baselines/ca_corrective_locality_baseline.json) | Frozen baseline medians |
| [docs/processes/corrective_fix_watch_process.md](../processes/corrective_fix_watch_process.md) | CA11 machine watch process (complementary; CJ is human evidence ledger) |
