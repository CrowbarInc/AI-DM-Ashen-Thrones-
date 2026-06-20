# BR Bug-Fix Locality Measurement Discovery

## Executive summary

This report classifies all **235** commits available through `3f5ee0c` (2026-06-20) using commit subjects and changed paths. The observed median for commits classified as true `bug_fix` is **9 files** and **5 production files**. By comparison, `refactor_architecture` commits have a median of **16 files**.

The history contains **137** architecture/refactor or governance/observability commits. These include planned architecture cycles, decomposition, ownership/gate/replay cleanup, scorecard/reporting, and governance instrumentation. They should not be pooled with corrective commits when measuring bug-fix locality. The prior 17.5-file figure is therefore plausibly contaminated by planned program work; this history supports replacing it with the category-specific bug-fix baseline below.

## Methodology

- Source data: full `git log`, one `git diff-tree --root --name-only -r` path inventory per commit, commit dates, subjects, and changed filenames.
- Unit of analysis: one commit. Merge commits and subjects without a defensible primary intent are excluded into `mixed_or_unclear`.
- `production`: paths not assigned to tests or documentation/tooling. This includes runtime code, static UI, and runtime data.
- `test`: `tests/`, `test_*`, `*_test.py`, pytest cache/coverage paths, and tracked `codex_pytest_tmp*` artifacts.
- `docs/tooling`: `docs/`, `audits/`, `tools/`, `.github/`, `artifacts/`, Markdown/text artifacts, and root build/test configuration files.
- Medians use commit-level file counts and the conventional midpoint average for even-sized sets. Renames are counted from Git's changed-path output, not line churn.
- Raw files touched deliberately include tracked pytest temporary artifacts because they are present in Git history. Those paths count as tests, not production; this prevents repository pollution from inflating production-file locality.
- Classification precedence: merge/explicit mixed intent; governance/observability signals; architecture/refactor signals; path-only docs/tests; explicit corrective signals; feature/behavioral-contract signals; otherwise human review. This keeps planned test decomposition and replay-governance cycles in their program-work cohorts.
- This is an evidence-based heuristic classification, not an assertion that every subject perfectly describes author intent. The CSV preserves the row-level rationale for audit and correction.

## Category definitions

| Category | Primary intent |
|---|---|
| `bug_fix` | Explicitly corrective work: fix, repair, recover, restore, preserve, guard, prevent, or stabilize a defect. |
| `refactor_architecture` | Planned consolidation, decomposition, extraction, ownership/boundary changes, cleanup, compression, or architectural restructuring. |
| `governance_observability` | Audits, telemetry, dashboards, replay governance, validation infrastructure, instrumentation, and recurrence reporting. |
| `feature_work` | New product capabilities, systems, models, layers, frameworks, or behavioral contracts without an explicit defect claim. |
| `test_only` | Test paths (and optionally support docs/tooling) changed with no production path. |
| `docs_only` | Documentation, audit artifacts, or tooling/config only; no production or test path. |
| `mixed_or_unclear` | Merge, explicitly mixed work, or insufficient evidence for one primary intent. |

## Median files touched by category

| Category | Commits | Median files touched |
|---|---:|---:|
| `bug_fix` | 11 | 9 |
| `refactor_architecture` | 101 | 16 |
| `governance_observability` | 36 | 16 |
| `feature_work` | 44 | 14 |
| `test_only` | 11 | 7 |
| `docs_only` | 2 | 1.5 |
| `mixed_or_unclear` | 30 | 9 |

## Median production files touched by category

| Category | Commits | Median production files touched |
|---|---:|---:|
| `bug_fix` | 11 | 5 |
| `refactor_architecture` | 101 | 3 |
| `governance_observability` | 36 | 1 |
| `feature_work` | 44 | 7.5 |
| `test_only` | 11 | 0 |
| `docs_only` | 2 | 0 |
| `mixed_or_unclear` | 30 | 5 |

## Top 10 largest bug_fix commits

| SHA | Date | Files | Production | Tests | Docs/tooling | Subject |
|---|---|---:|---:|---:|---:|---|
| `5cb8444` | 2026-04-26 | 538 | 2 | 536 | 0 | Recover mixed investigation question routing |
| `f487f4d` | 2026-04-26 | 216 | 5 | 211 | 0 | Guard rich scene openings from post-gate shortening |
| `f3fa4b1` | 2026-04-26 | 52 | 6 | 46 | 0 | Preserve player chat in replayed logs |
| `ceecc57` | 2026-04-16 | 20 | 12 | 6 | 2 | Opening Scene Repair |
| `6351b33` | 2026-04-25 | 16 | 12 | 4 | 0 | Preserve curated opening facts through fallback |
| `6a402d2` | 2026-05-20 | 9 | 3 | 5 | 1 | config: lazy-load OpenAI API key for import-safe tests |
| `9e83820` | 2026-04-26 | 7 | 6 | 1 | 0 | Preserve journal openings through selector fallback |
| `2013258` | 2026-04-25 | 7 | 5 | 2 | 0 | Restrict journal seed facts to perceptual opening content |
| `09863c6` | 2026-03-21 | 7 | 7 | 0 | 0 | Fix dialogue/adjudication routing and remove scaffold text leakage; improve follow-up response handling |
| `1b3b3ee` | 2026-04-26 | 5 | 4 | 1 | 0 | Preserve valid scene openings before deterministic fallback |

## Top 10 largest refactor_architecture commits

| SHA | Date | Files | Production | Tests | Docs/tooling | Subject |
|---|---|---:|---:|---:|---:|---|
| `6dcccd8` | 2026-04-28 | 1407 | 1 | 1163 | 243 | Post-GM adoption gateway fenced |
| `29da646` | 2026-05-04 | 267 | 2 | 6 | 259 | Adoption Gateway (Finalized) |
| `43bdb8b` | 2026-04-26 | 195 | 4 | 191 | 0 | Collapse start_campaign onto canonical gm_output |
| `11ff282` | 2026-06-16 | 92 | 35 | 57 | 0 | BJ: Final Emission Gate Responsibility Extraction |
| `8195287` | 2026-06-04 | 64 | 2 | 52 | 10 | AS: Downstream Dependency Reduction |
| `4782a71` | 2026-04-20 | 63 | 16 | 46 | 1 | Public vs Debug vs Author State Separation |
| `0fa3dd2` | 2026-04-08 | 51 | 30 | 21 | 0 | Context Separation Rules |
| `fde6598` | 2026-06-10 | 45 | 0 | 44 | 1 | BD: Gate Dependency Compression |
| `b54b311` | 2026-05-31 | 45 | 7 | 33 | 5 | Close Cycle AB fallback topology collapse |
| `335926e` | 2026-04-22 | 42 | 15 | 21 | 6 | Final Emission Ownership Convergence |

## Ambiguous/mixed commits needing human review

| SHA | Date | Files | Subject | Reason |
|---|---|---:|---|---|
| `8d2da99` | 2026-03-19 | 90 | Initial commit | Broad or generic subject does not identify one primary change intent. |
| `5e0bfe0` | 2026-03-19 | 6 | Rule Priority Hierarchy, Typed Uncertainty Resolution, Single-failure targeted retries, & Validator-voice policy cleanup | Subject enumerates several distinct behavioral and cleanup intents. |
| `7e65d92` | 2026-03-19 | 9 | Context-anchored uncertainty renderer, Remove reusable generic uncertainty templates, Contextual lead selection, Prevent uncertainty override of known facts, & Upgrade scene momentum into interaction pressure | Subject enumerates several distinct behavioral and cleanup intents. |
| `682ee69` | 2026-03-21 | 3 | Guantlet v0.2.0 | Commit message and path mix do not establish a reliable primary category. |
| `78bf027` | 2026-03-22 | 7 | Imperative & Advisory Tone Kill | Commit message and path mix do not establish a reliable primary category. |
| `08088a9` | 2026-03-24 | 14 | Bootstrapping & Role Inconsistency | Commit message and path mix do not establish a reliable primary category. |
| `3110993` | 2026-03-25 | 9 | Social Target Resolution & Addressable Actions | Commit message and path mix do not establish a reliable primary category. |
| `49b51d0` | 2026-03-26 | 14 | Consolidation Post-Testing | Broad or generic subject does not identify one primary change intent. |
| `7ed2156` | 2026-03-28 | 32 | Social Follow-Up Tweaks | Broad or generic subject does not identify one primary change intent. |
| `60434a7` | 2026-03-28 | 3 | Phase 0 Closing Passes | Broad or generic subject does not identify one primary change intent. |
| `b62d11c` | 2026-03-28 | 4 | Phase 0 Finishing Touches | Broad or generic subject does not identify one primary change intent. |
| `845e3f7` | 2026-03-29 | 7 | Stage 0 FINAL Updates | Broad or generic subject does not identify one primary change intent. |
| `498d86f` | 2026-03-29 | 0 | merge branch 'feature/transcript-gauntlet-ltc-slice' | Merge commit; primary intent cannot be assigned from changed paths. |
| `926828d` | 2026-03-29 | 1 | Transition Rules & Invariants | Commit message and path mix do not establish a reliable primary category. |
| `de815e6` | 2026-03-29 | 9 | Relationship & Future-Proofing Fields | Commit message and path mix do not establish a reliable primary category. |
| `96c925f` | 2026-03-31 | 3 | Integrating Discovery into Authoritative Lead Creation | Commit message and path mix do not establish a reliable primary category. |
| `9f8e217` | 2026-04-07 | 7 | Answer Completeness Rules | Commit message and path mix do not establish a reliable primary category. |
| `90880fb` | 2026-04-08 | 25 | Scene State Anchoring | Commit message and path mix do not establish a reliable primary category. |
| `9ac6549` | 2026-04-09 | 14 | Interaction Continuity Rules | Commit message and path mix do not establish a reliable primary category. |
| `fe0f30f` | 2026-04-11 | 31 | Transcript-Based Regression Tests & Bug Fixing | Subject explicitly combines regression-test work and bug fixing. |
| `d73627d` | 2026-04-15 | 6 | Focused Polish Pass | Broad or generic subject does not identify one primary change intent. |
| `ce0340d` | 2026-04-22 | 14 | Role-Based Narrative Composition | Commit message and path mix do not establish a reliable primary category. |
| `2d79bae` | 2026-04-24 | 9 | Scenario-Spine Expansion | Commit message and path mix do not establish a reliable primary category. |
| `d6bad74` | 2026-04-25 | 5 | Enforce curated opening facts in fallback | Commit message and path mix do not establish a reliable primary category. |
| `4d3d71a` | 2026-04-25 | 13 | Clean scene canon and lock opening fact sources | Commit message and path mix do not establish a reliable primary category. |
| `b0cfd07` | 2026-04-26 | 5 | Refine opening scene narration contract | Commit message and path mix do not establish a reliable primary category. |
| `c6e63b0` | 2026-04-26 | 7 | Refresh session snapshot and opening scene details | Commit message and path mix do not establish a reliable primary category. |
| `f6a4c6f` | 2026-04-26 | 135 | Promote upstream prepared scene openings before final gate | Commit message and path mix do not establish a reliable primary category. |
| `773cbe0` | 2026-04-26 | 26 | Promote accepted scene opening candidates | Commit message and path mix do not establish a reliable primary category. |
| `53165bb` | 2026-04-26 | 93 | UI & Freeform Investigation (I) | Commit message and path mix do not establish a reliable primary category. |

## Contamination findings

The dominant contamination signatures are explicit and concentrated: `Architecture Audit` sequences; `Cycle` programs; consolidation/decomposition/extraction; ownership and authority compression; final-emission gate contraction; replay schema, harness, and golden-replay consolidation; test inventory compression; maintenance-locality promotion; and telemetry, recurrence, dashboard, and runtime-incidence instrumentation.

These commits are legitimate engineering work, but their file fan-out measures planned system change rather than the locality of responding to a defect. BR locality should report them as separate cohorts and should never use their pooled median as the bug-fix baseline.

A separate historical contamination is visible inside the raw bug-fix cohort: commits `f487f4d`, `f3fa4b1`, and `5cb8444` include large tracked `codex_pytest_tmp*` trees. Their raw files-touched values are retained as Git evidence, while the production-file metric isolates the actual product footprint. This is why BR should publish both medians.

## Recommendation for next BR implementation step

Proceed with BR using **9 files per bug-fix commit** and **5 production files per bug-fix commit** as the historical baseline, while retaining the CSV as the auditable source. Before turning this into a durable scorecard, have a human review the ambiguous table and a small stratified sample of the largest classified commits. Then automate the same mutually exclusive cohorts for future commits and publish both median and sample size; do not recombine architecture/governance cycles with bug fixes.

## Machine-readable evidence

The complete commit-level classification, file counts, and classification notes are in `docs/reports/BR_commit_classification.csv`.
