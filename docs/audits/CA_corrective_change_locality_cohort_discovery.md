# CA Corrective Change Locality Cohort Discovery

**Date:** 2026-06-22  
**Scope:** Discovery only; no metric or production-code implementation.

## 1. Executive summary

This repository can identify genuine corrective fixes locally, but commit-subject keywords are only a candidate generator. The strongest evidence is the combination of: (1) an explicit defect statement in the subject/body or a contemporaneous failure report, (2) a production/runtime source change, and (3) a test, replay, audit, or CI failure that describes the repaired behavior. Git contains the full local path history needed to count files per commit.

The existing BR inventory already labels 11 of 235 commits as `bug_fix`. Manual diff review supports **10 genuine corrective fixes** and rejects one row (`2b293b2`) because it changes only three mutable runtime snapshots and supplies no source repair or regression lock. This is enough for an initial 8-12 commit CA cohort. The cohort is historical (2026-03-21 through 2026-05-20); BV1A reports no new bug-fix commit after BI in its comparison window, so CA should not claim a current trend yet.

Raw files touched is badly distorted in three commits by accidentally tracked `codex_pytest_tmp*` output: 210, 44, and 534 generated files respectively. CA should preserve raw Git fanout as the primary metric, but always publish production-source, test-source, fixture/data, docs, tooling, and generated-artifact counts beside it. Otherwise “Files Touched Per Fix” measures repository pollution more than repair locality.

No existing artifact reliably joins a corrective commit to a recurrence key or replay failure event. The opening/fallback commits form an evident repeated repair family, and several contain regression tests, but this is **relationship evidence**, not proof that a recorded failure recurred. BQ recurrence history is useful as a future optional join; it is not currently populated or commit-linked.

## 2. Existing reusable files and artifacts

| File/artifact | Reusable evidence | Limitation for CA |
|---|---|---|
| `docs/reports/BR_commit_classification.csv` | 235-commit inventory with subject, date, category, raw files, production, tests, and docs/tooling counts | `bug_fix` is keyword-led; production includes runtime data; docs and tooling are combined |
| `docs/reports/BR_bug_fix_locality_measurement.md` | Category definitions, methodology, 11-row candidate list, medians | Treats all 11 as fixes and retains polluted raw fanout without a generated bucket |
| `tests/helpers/bug_fix_locality_metric.py` | CSV loader, Git changed-path lookup, percentile/locality/hotspot calculations | Frozen BR baseline; only three path buckets; should be factored or imported carefully rather than copied |
| `tools/bug_fix_locality_report.py` | Existing CLI/report entry point for BRL1 | Produces category-level BR report, not an evidence-reviewed corrective cohort |
| `tests/test_bug_fix_locality_metric.py` and `tests/test_bug_fix_locality_regression_guard.py` | Existing metric contract and guard patterns | Protect BR semantics, not the proposed CA definition |
| `docs/audits/BV1A_bug_fix_commit_inventory.md` and `artifacts/bv1a_analysis.json` | Rechecks the BR bug-fix inventory and post-BI history | Still inherits BR classifications; reports no post-BI corrective sample |
| `audits/cycle_f_maintenance_drag_recon_20260517.md` | Earlier commit fanout, hotspots, and likely failure families | Counts tracked temp output as artifact/test fanout and mixes all change types |
| `audits/cycle_f_source_fanout_refinement_20260518.md` | Better distinction between true source and runtime data snapshots | Good model for CA path buckets, but not a corrective-only cohort |
| `audits/cycle_f_final_gate_hotspot_touch_budget_20260518.md` | Explicit regression-lock/fallback evidence for `1b3b3ee`, `9e83820`, and `6351b33` | Narrative audit, not machine-readable linkage |
| `docs/reports/openai_api_key_lazy_config_fix_20260520.md` | Concrete CI failure chain, changed files, and passing regression slices for `6a402d2` | Only one commit has this level of direct failure documentation |
| `docs/audits/BQ_recurrence_history_discovery.md` | Maps replay, runtime-lineage, and fallback recurrence infrastructure | Finds no implemented Regression Recurrence Rate and no cross-run commit linkage |
| `artifacts/golden_replay/bug_recurrence_history.json` / `.md` | Intended bug-class recurrence store | Current history is not a dependable commit-to-fix join; BQ documents the population gap |
| `artifacts/golden_replay/replay_failure_report.md` | Concrete protected replay failure with speaker/fallback/mutation evidence and reproduction command | Current 2026-06-22 failure is later than this cohort and contains no repairing commit hash |
| `tools/backfill_bug_recurrence_history.py`, `tools/bv8a_recurrence_history_regeneration.py` | Backfill/regeneration patterns for recurrence evidence | Operate on replay recurrence events, not Git corrective changes |

Git itself is the authoritative change-history source. `git log --date=short --pretty=...`, `git diff-tree --root --no-commit-id --name-only -r <sha>`, and `git show <sha>` work locally and are sufficient for subject/date, exact changed paths, and diff review. Commit bodies are generally identical to their short subjects and rarely contain issue IDs, failing test names, or recurrence keys.

## 3. Proposed genuine-corrective-fix definition

A commit qualifies only when all mandatory conditions hold:

1. **Concrete defect response:** evidence identifies behavior that was wrong, failing, missing, leaked, shortened, misrouted, or unsafe. An explicit failure report is best; a precise corrective subject plus a matching diff/test is acceptable.
2. **Repair action:** at least one production/runtime source file changes. Fixture-only, snapshot-only, docs-only, metric-only, tooling-only, and test-only commits do not qualify.
3. **Primary intent is corrective:** the repair is the dominant purpose of the commit. Planned decomposition, extraction, consolidation, ownership compression, architecture cleanup, cycle delivery, and new capability work are excluded unless a concrete defect and its repair boundary can be separated and evidenced.
4. **Reviewable boundary:** the commit is not a merge and is not so mixed that the repair fanout cannot be attributed honestly.

Supporting evidence raises confidence but is not mandatory for old commits: a regression test added/changed in the same commit; a named failing test or CI report; a replay/fallback/audit row; or a clear earlier/later same-family repair. Words such as `fix`, `repair`, `restore`, `preserve`, `guard`, and `prevent` nominate a commit for review but never qualify it alone.

Recommended confidence values are `high` (concrete failure plus lock), `medium` (precise corrective intent and matching source/test diff), and `low` (subject/diff inference only). Only high and medium rows should enter the primary cohort.

## 4. Candidate cohort

Counts below are recomputed from Git with the classification rule in section 5. `Total` is raw Git changed paths; `Gen` is accidentally tracked `codex_pytest_tmp*` output and remains included in `Total`.

| ID | Commit / date | Title | Qualifies | Total | Prod | Test | Docs | Tools | Fixture | Gen | Evidence and relationship |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| CA-01 | `09863c6` / 2026-03-21 | Fix dialogue/adjudication routing and remove scaffold text leakage | Yes, medium | 7 | 4 | 0 | 0 | 0 | 3 | 0 | Precise routing/leakage repair in adjudication/API/GM/prompt source; no same-commit regression lock or recurrence record |
| CA-02 | `ceecc57` / 2026-04-16 | Opening Scene Repair | Yes, medium | 20 | 8 | 6 | 2 | 0 | 4 | 0 | Source repair plus opening/start-campaign regression suites; begins repeated opening/fallback family |
| CA-03 | `6351b33` / 2026-04-25 | Preserve curated opening facts through fallback | Yes, high | 16 | 9 | 4 | 0 | 0 | 3 | 0 | Fallback repair with tests; Cycle F explicitly calls out regression-lock evidence; repeated opening/fallback family |
| CA-04 | `2013258` / 2026-04-25 | Restrict journal seed facts to perceptual opening content | Yes, high | 7 | 2 | 2 | 0 | 0 | 3 | 0 | Adds targeted tests rejecting private/inference facts; repeated opening/fallback content failure family |
| EX-01 | `2b293b2` / 2026-04-25 | Restore journal seed facts as opening source | **No** | 3 | 0 | 0 | 0 | 0 | 3 | 0 | Snapshot/data-only commit; no source repair, test, audit, or replay evidence. Keep as an exclusion control |
| CA-05 | `9e83820` / 2026-04-26 | Preserve journal openings through selector fallback | Yes, high | 7 | 3 | 1 | 0 | 0 | 3 | 0 | API/gate/prompt repair plus start-campaign test; Cycle F identifies opening-selector fallback evidence |
| CA-06 | `1b3b3ee` / 2026-04-26 | Preserve valid scene openings before deterministic fallback | Yes, high | 5 | 1 | 1 | 0 | 0 | 3 | 0 | Direct regression test ensures valid opening is not replaced; Cycle F labels it a regression lock |
| CA-07 | `f487f4d` / 2026-04-26 | Guard rich scene openings from post-gate shortening | Yes, high | 216 | 2 | 1 | 0 | 0 | 3 | 210 | Targeted start-campaign regression forces a shortening mutation and asserts restoration; fallback/mutation link. Raw total is polluted |
| CA-08 | `f3fa4b1` / 2026-04-26 | Preserve player chat in replayed logs | Yes, high | 52 | 2 | 2 | 0 | 0 | 4 | 44 | Frontend/backend replay-log regression tests; replay relationship, but not protected-replay recurrence. Raw total is polluted |
| CA-09 | `5cb8444` / 2026-04-26 | Recover mixed investigation question routing | Yes, high | 538 | 2 | 2 | 0 | 0 | 0 | 534 | Parser and shared-pipeline regression tests for misrouted mixed investigation questions; routing link. Raw total is polluted |
| CA-10 | `6a402d2` / 2026-05-20 | Lazy-load OpenAI API key for import-safe tests | Yes, high | 9 | 3 | 5 | 1 | 0 | 0 | 0 | Direct CI collection failure report and validated focused/CI test slices; no replay/recurrence link |

The primary cohort therefore has 10 fixes. Six (`CA-02` through `CA-07`) are related to the same broad opening/fallback repair area, but the repository does not record whether the same recurrence key returned. CA must expose both `repair_family` and `recurrence_evidence_status`; it must not translate same-area sequential repairs into “recurrence=true.” No candidate has a demonstrated speaker-parity failure link. `CA-07` has mutation/fallback evidence, `CA-08` replay-log evidence, and `CA-09` routing evidence.

## 5. Production-file classification rule

Use mutually exclusive, ordered path buckets:

| Bucket | Rule and examples |
|---|---|
| `production_runtime_source` | Executable product code under `game/` and `static/`, plus any future root/application package explicitly registered as runtime source |
| `tests` | Authored tests and test helpers under `tests/`; do **not** put `codex_pytest_tmp*` here |
| `docs_reports` | `docs/`, `audits/`, Markdown reports, and human-authored report definitions |
| `scripts_tools` | `tools/`, `scripts/`, `.github/`, and build/CI/config utilities; distinguish metric/report tooling from product runtime |
| `fixtures_data` | `data/`, committed fixture directories, snapshots, and scenario inputs; these can affect behavior but are not production source |
| `generated_artifacts` | `artifacts/`, `codex_pytest_tmp*`, caches, coverage output, and generated inventories/reports |
| `unclassified` | Any unmatched path; fail validation or require an explicit reviewed mapping before cohort publication |

Renames should count as one logical touched path when Git reports a rename record; additions/deletions each count once. Submodules and merge commits should be excluded from the first implementation. `production_files_touched` means only `production_runtime_source`. Publish `behavioral_files_touched = production_runtime_source + fixtures_data` as a secondary field if useful, without relabeling data snapshots as source.

## 6. Proposed metric schema

The cohort source should be reviewed, versioned data rather than inferred afresh on every run. Minimum row schema:

| Field | Purpose |
|---|---|
| `cohort_id`, `source_type`, `commit_hash`, `date`, `title` | Stable identity and Git provenance |
| `qualifies`, `qualification_reason`, `confidence`, `reviewed_at` | Human-reviewed corrective classification |
| `defect_statement`, `repair_family` | Concrete wrong behavior and cross-commit family |
| `total_files_touched` | Raw Git changed-path count: primary “Files Touched Per Fix” value |
| `production_files_touched`, `test_files_touched`, `docs_files_touched`, `tooling_files_touched`, `fixture_files_touched`, `generated_files_touched`, `unclassified_files_touched` | Auditable decomposition of total fanout |
| `effective_files_touched` | Raw total minus generated artifacts; secondary diagnostic, never a silent replacement for raw total |
| `recurrence_evidence_status`, `recurrence_key_or_source` | `confirmed`, `related_family_only`, `none`, or `unknown`, with source |
| `replay_or_regression_link` | Test node/path, failure report, audit row, or reproduction command |
| `failure_modes` | Controlled tags such as `fallback`, `replay`, `speaker`, `mutation`, `routing`, `ci_import` |

Report cohort size, median, P75, P90, max, and individual rows for both raw total and effective total; median production and test files; percent with a same-commit regression lock; percent with confirmed recurrence evidence; and family concentration. With only 10 rows, show the complete distribution and do not claim trend significance. The metric should fail closed on missing commits, duplicate hashes, count mismatch, or unclassified paths.

## 7. Recommended implementation plan

1. **CA1 - Reviewed cohort authority.** Promote the draft CSV to the reviewed schema, retain `EX-01` as an exclusion test, use full hashes, and record evidence paths. No automatic keyword may set `qualifies=true`.
2. **CA2 - Path classifier and Git collector.** Add `tools/corrective_change_locality.py`. Reuse BR's subprocess/path-normalization and distribution ideas, but implement the seven CA buckets. Consider extracting only genuinely shared Git/stat helpers later; do not change BR's frozen baseline during CA.
3. **CA3 - Deterministic report.** Write machine output to `artifacts/ca_corrective_change_locality.json` and human output to `artifacts/ca_corrective_change_locality_report.md`. Keep this discovery document and reviewed CSV under `docs/audits/`.
4. **CA4 - Contract tests.** Add `tests/test_corrective_change_locality.py` covering path buckets, `codex_pytest_tmp*` separation, rename/count behavior, exclusion of fixture-only `2b293b2`, duplicate/missing commit failures, and known counts for the 10-row cohort.
5. **CA5 - Optional evidence join.** Read BQ recurrence and protected replay failure artifacts through a small adapter only when they expose a stable commit/source identifier. Until then, emit `unknown`/`related_family_only`; do not manufacture joins from dates or cycle labels.
6. **CA6 - Future window.** After 8-12 newly reviewed corrective commits exist, compare a new cohort with this historical baseline. BV1A's zero post-BI bug-fix sample makes a present-day before/after claim premature.

BR machinery should be reused for concepts and possibly small read-only helpers, not as CA's cohort authority. BQ machinery should remain the recurrence authority; CA should consume a future stable join rather than duplicate recurrence aggregation.

Primary risks are sparse clean corrective history, squash/mixed commits hiding fix boundaries, mutable snapshots inflating behavioral fanout, tracked temp trees dominating raw totals, and ambiguous links between repairs and recurrence events. A second risk is cohort concentration: six of ten fixes concern opening/fallback behavior, so the baseline describes this repository's observed fixes, not a balanced taxonomy of defects.

## 8. Exact files to pass back for external implementation review

Pass these files as the smallest useful planning packet:

1. `docs/audits/CA_corrective_change_locality_cohort_discovery.md`
2. `docs/audits/CA_corrective_change_locality_candidates.csv`
3. `docs/reports/BR_commit_classification.csv`
4. `docs/reports/BR_bug_fix_locality_measurement.md`
5. `tests/helpers/bug_fix_locality_metric.py`
6. `tools/bug_fix_locality_report.py`
7. `tests/test_bug_fix_locality_metric.py`
8. `docs/audits/BV1A_bug_fix_commit_inventory.md`
9. `audits/cycle_f_source_fanout_refinement_20260518.md`
10. `audits/cycle_f_final_gate_hotspot_touch_budget_20260518.md`
11. `docs/audits/BQ_recurrence_history_discovery.md`
12. `docs/reports/openai_api_key_lazy_config_fix_20260520.md`

If recurrence integration is in scope, also pass `tests/helpers/replay_bug_recurrence.py`, `tools/backfill_bug_recurrence_history.py`, `artifacts/golden_replay/bug_recurrence_history.json`, and `artifacts/golden_replay/replay_failure_report.md`. External review also needs the Git objects for the 11 hashes in the CSV; file snapshots alone cannot reproduce changed-path counts or validate intent.
