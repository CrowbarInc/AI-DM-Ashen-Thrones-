# Corrective Fix Watch Process

**Primary metric:** Corrective Fix Emergence Rate  
**Scope:** CA11 watch activation for post-baseline corrective-fix detection (CA11+)

## Purpose

The corrective fix watch monitors `docs/audits/ca_review_queue.csv` for newly reviewed commits that qualify under CA1 standards but are not already present in the frozen CA1 cohort authority file. When enough new qualifying fixes accumulate, the repository can justify **CA12 — Post-Baseline Corrective Locality Comparison** against the frozen CA4 baseline.

## Trigger conditions

A commit enters the watch as a **detected qualifying fix** when all of the following hold:

1. **`reviewed=true`** in `docs/audits/ca_review_queue.csv`
2. **`qualifies=true`** after human review against CA1 mandatory conditions
3. **`commit_hash` is not present** in `docs/audits/CA_corrective_change_locality_cohort.csv` (duplicate suppression against the frozen CA1 cohort, including exclusion controls such as `EX-01`)

Keyword nomination alone never triggers the watch. Program, governance, and instrumentation commits remain excluded until a reviewer promotes them with explicit CA1 evidence.

## Running the watch

```bash
python tools/corrective_fix_watch.py
```

The tool writes:

| Artifact | Role |
|---|---|
| `artifacts/ca11_corrective_fix_watch_report.md` | Human-readable watch summary |
| `artifacts/ca11_corrective_fix_watch_report.json` | Machine-readable watch state |

Inputs (read-only):

- `docs/baselines/ca_corrective_locality_baseline.json`
- `docs/audits/ca_review_queue.csv`
- `artifacts/ca10_corrective_prevention_effectiveness_report.json`

## Primary metric

**Corrective fix emergence rate**

```text
new_qualifying_fixes / reviewed_candidates
```

Where:

- **new_qualifying_fixes** — detected qualifying fixes after CA1 duplicate suppression
- **reviewed_candidates** — queue rows with `reviewed=true`

## Readiness thresholds

Cohort readiness for CA12 is derived from **new qualifying fix count** only:

| New qualifying fixes | Readiness state | Meaning |
|---:|---|---|
| 0 | `no_new_fixes` | Watch active; no post-baseline CA1-qualifying evidence yet |
| 1–4 | `insufficient_sample` | Fixes emerging; sample below CA12 comparison threshold |
| 5+ | `comparison_ready` | Enough evidence to justify CA12 locality comparison against CA4 |

The watch does not modify the CA4 baseline JSON, mutate the frozen CA1 cohort CSV, compute trend windows, join recurrence history, or forecast future fix rates.

## Report fields

Each CA11 run reports:

- **Qualifying fixes detected** — new CA1-qualifying commits outside the frozen cohort
- **Qualifying fixes pending** — queue rows awaiting review completion or a `qualifies` decision
- **Total reviewed candidates** — completed reviews in the queue
- **Current emergence rate** — primary metric for the run
- **Cohort readiness assessment** — `no_new_fixes`, `insufficient_sample`, or `comparison_ready`

## Promotion into future CA cohorts

When the watch detects qualifying fixes:

1. **Do not mutate** `docs/audits/CA_corrective_change_locality_cohort.csv` or `docs/baselines/ca_corrective_locality_baseline.json`.
2. Export detected rows from the review queue with full CA1 authority columns (including CA2 path-bucket counts).
3. Assign new `cohort_id` values in a separate post-baseline cohort CSV (for example `docs/audits/CA_post_baseline_cohort.csv`).
4. Run CA3 measurement on the promoted cohort when path accounting is complete.
5. Proceed to **CA12** only when readiness state is `comparison_ready` (five or more new qualifying fixes).

## Relationship to CA10

CA10 documents that structural programs may absorb corrective work upstream of CA1 qualification. CA11 remains the authoritative trigger for when explicit, CA1-qualifying fixes have emerged in sufficient quantity to compare post-baseline locality against the CA4 baseline.

## Limitations

- The watch depends on accurate human review in `ca_review_queue.csv`.
- Duplicate suppression uses CA1 cohort commit hashes only; post-baseline cohort promotion is a separate CA cycle.
- Emergence rate declines as the reviewed-candidate denominator grows even when new fixes appear slowly.
- CA11 does not auto-promote queue rows into any cohort CSV.
