# Corrective Change Review Process

**Primary metric:** Files Touched Per Fix  
**Scope:** Human review intake for future corrective-fix cohorts (CA5+)

## Purpose

This process collects keyword-nominated commits from git history, routes them through a review queue, and promotes only evidence-reviewed rows into a future CA cohort. Keyword matches nominate commits for review; they never auto-qualify a fix.

## Qualification rules

A commit may be promoted into a future corrective cohort only when all mandatory conditions hold:

1. **Concrete defect response** — subject, body, audit, test failure, or matching diff/test shows behavior that was wrong, failing, missing, leaked, shortened, misrouted, or unsafe.
2. **Repair action** — at least one production/runtime source file under `game/` or `static/` changes.
3. **Primary intent is corrective** — the repair is the dominant purpose; planned architecture, extraction, governance, or feature delivery is excluded unless the defect boundary is separable and evidenced.
4. **Reviewable boundary** — the commit is not a merge and repair fanout can be attributed honestly.
5. **Confidence** — assign `high` or `medium` before cohort promotion; `low` rows stay out of the primary cohort.

## Exclusion rules

Reject or exclude when any of the following apply:

- Snapshot/data-only changes with no production source repair or regression lock (see frozen control `EX-01`).
- Docs-only, test-only, tooling-only, or metric-only commits.
- Feature, governance, or architecture work without a separable defect repair.
- Merge commits or unreviewably mixed intent.
- Keyword nomination alone without defect and repair evidence.

## Review workflow

1. **Generate inventory** — run `python tools/corrective_change_candidate_inventory.py`.
   - Discovers commits after the CA4 baseline end date (`2026-05-20` by default).
   - Excludes hashes already present in the frozen CA1 cohort CSV.
   - Writes `artifacts/ca5_candidate_inventory.json` and `.md`.
2. **Inspect candidates** — use the inventory table and path counts (files, production, tests, generated).
3. **Review queue** — update `docs/audits/ca_review_queue.csv` for each candidate:
   - Set `reviewed=true` when human review is complete.
   - Set `qualifies=true|false`, `confidence`, `defect_statement`, and `repair_family` for qualifying decisions.
   - Record rationale in `notes`.
4. **Re-run intake** — regenerating the inventory merges new candidates into the queue without duplicating existing `commit_hash` rows or overwriting completed reviews.
5. **Promote reviewed rows** — when enough reviewed qualifying commits exist, assemble a new cohort CSV using the CA1 schema in a separate CA cycle. Do not mutate the frozen baseline cohort or CA4 baseline JSON.

## Promotion into future cohorts

Promotion steps for a second cohort:

1. Export reviewed rows where `reviewed=true` and `qualifies=true`.
2. Assign new `cohort_id` values continuing the CA sequence.
3. Populate full CA1 authority columns, including path-bucket counts validated by CA2.
4. Run CA3 measurement on the new cohort.
5. Compare against CA4 only in a dedicated comparison cycle — not during CA5 intake.

## Artifacts and sources

| Artifact | Role |
|---|---|
| `artifacts/ca5_candidate_inventory.json` | Machine-readable candidate inventory |
| `artifacts/ca5_candidate_inventory.md` | Human review table and checklists |
| `docs/audits/ca_review_queue.csv` | Reviewed-candidate workflow state |
| `artifacts/ca5_intake_pipeline_report.md` | Intake run statistics and validation |
| `docs/audits/CA_corrective_change_locality_cohort.csv` | Frozen historical cohort authority (read-only) |
| `docs/baselines/ca_corrective_locality_baseline.json` | Frozen CA4 baseline (read-only) |

## Discovery keywords (default)

`fix`, `bug`, `repair`, `restore`, `prevent`, `preserve`, `guard`, `regression`, `fallback`, `routing`, `replay`, `mutation`

Override with repeated `--keyword` flags on the intake tool when needed.

## Limitations

- Keyword discovery is broad; most candidates will be program work rather than genuine corrective fixes.
- Intake does not join recurrence history or compute trend deltas against CA4.
- Path counts depend on CA2 Git collection and local repository history.
