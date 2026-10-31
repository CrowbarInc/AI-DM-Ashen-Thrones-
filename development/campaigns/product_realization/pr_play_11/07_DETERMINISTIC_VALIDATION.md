# 07 — Deterministic Validation

PR-PLAY-11 · 2026-10-30 America/New_York · evidence_scope: structural_only.

Actual commands, executable paths, basetemps, exits and durations: regression_runs.json. Entry point: `.venv/Scripts/python.exe -m tools.validate_pr_play_11`; successful outer invocation uses the base Python312 interpreter with repository/.venv site-packages in PYTHONPATH to avoid Windows launcher issues. Every lane executes pytest with explicit selected files, -q --tb=short and JUnit output. Test live-model guard prohibits real SDK construction except explicit synthetic stubs. No live test or connectivity probe ran.

| Lane | Passed | Failures | Errors |
|---|---|---|---|
| harness | 35 | 0 | 0 |
| gameplay | 33 | 0 | 0 |
| rules_persistence | 53 | 0 | 0 |
| conversation | 35 | 0 | 0 |
| provider | 88 | 1 | 0 |
| diagnostics | 81 | 0 | 0 |
| structured | 60 | 1 | 0 |
| opening | 23 | 3 | 0 |
| world | 123 | 0 | 0 |
| export_atgb | 55 | 1 | 0 |
| overlay | 88 | 0 | 0 |
| hidden_faction | 78 | 0 | 0 |
| claim_authority | 126 | 8 | 0 |
| entry_claim_authority | 104 | 8 | 0 |

Actual current-source total: **878 passing executions / 14 failures**. The same PR10 lanes retain **752 passing / six failures**. The added claim/provenance selection contributes **126 passing / eight additional failures**; all eight reproduce against saved entry GM source (separate entry comparison: 104 passing / eight failures, excluded from the current-source total). Exact failure IDs and comparison are in failure_classification.json. One additional failure is an existing test incompatibility with the deterministic live-model guard; remaining added failures concern old claim/investigation behavior. They are not repaired here. No relevant new regression remains. Initial sandbox child/localhost attempts did not yield usable results and were interrupted; completed localhost-capable run supplies authoritative results. A transient Windows atomic-replace PermissionError passes on rerun. Initial prompt placement after the user message broke seven transport-fixture assumptions; moving the instruction before the user payload restores all diagnostics. Initial results are preserved under initial_regression/.

The first exploratory baseline test also had a mistaken expected structured subject and raised StopIteration; correcting the evidence lookup exposed that actual scene claims have empty identities. That test-authoring error was not a product regression; original baseline XML is retained. Counts are overlapping executions, not unique tests. No acceptance tests were weakened.

| Case | Result | Evidence / limits |
|---|---|---|
| C1 | PASS | before_repair_replay.json; baseline.xml: historical production replay returned 422 |
| C2 | PASS | Historical unchanged JSON remains 422 after guidance; conservative_generation.json returns 200 with source sentence |
| C3 | PASS | Both PR-PLAY-08 and 09 unchanged parsed captures replay with 200 |
| C4 | PASS | C4.json: valid claim with source reference |
| C5 | PASS_WITH_CONTRACT_CLARIFICATION | C5.json: unsupported fact without evidence rejected; source ID is not mandatory if authored text matches |
| C6 | PASS_WITH_CONTRACT_CLARIFICATION | C6.json: nonexistent ID plus unsupported text rejected; source_id_fallback.json proves invalid ID alone is not fatal with exact authored evidence |
| C7 | PASS | C7.json: contradictory authored claim rejected |
| C8 | PASS | C8.json: existing authored environmental realization accepted |
| C9 | PASS | C9.json: sensory incidental accepted; hidden_faction regression includes bounded proposal acceptance/promotion controls |
| C10 | PASS | C10.json: unauthorized action outcome rejected |
| C11 | PASS | C11.json: unauthorized mechanical/resource decision rejected |
| C12 | PASS | C12.json: unauthorized consequential gate/faction change rejected |
| C13 | PASS | C13.json and narrative-authority/hidden regressions |
| C14 | PASS | C14.json: established authored provenance requested in proposal rejected |
| C15 | PASS | C15.json: exact authored text with empty premises and no source ID accepted |
| C16 | PASS | C16.json and mixed-opening endpoint rollback/retry test |
| C17 | PASS | C17.json: both invalid declaration IDs captured |
| C18 | PASS | Historical endpoint replay before==after gameplay snapshot; PR04 rollback controls |
| C19 | PASS | Accepted endpoint replay advances one turn/log; PR04 exactly-once controls |
| C20 | PASS | Mixed-opening test fails without progression then succeeds on explicit new Start |
| C21 | PASS | Accepted historical replay repeat returns 409 and no extra transport dispatch |
| C22 | PASS | PR04 and PR10 concurrent endpoint tests pass in diagnostics/overlay lanes |
| C23 | PARTIAL_EVIDENCE_LIMIT | Original capture bytes hashed and copied unchanged; parsed JSON equal. Original provider wire bytes and original request payload were not captured; cannot claim byte-exact transport replay. |
| C24 | PASS | Pytest live-model guard, SDK synthetic transport, H15/G23 external socket refusal controls |
| C25 | PASS | Existing nested decision audit plus declaration_analysis.json and lexical_failure.json identify accepted declarations and sole narration rule |
| C26 | PASS | Explicit export selection, no environment dumps, configured-secret scan and ZIP scan |
| C27 | PASS | Overlay lane including O1-O15, production replay, rollback and concurrency |
| C28 | PASS_WITH_EXISTING_LIMIT | Gameplay HTTP synthetic pipeline proceeds past opening through T1-T4 and safely skips T5 at unchanged six-request ceiling; no all-five completion claim |

No full-suite, rendered UI, live reliability, semantic gameplay-quality, ATGB score or independent held-out generalization claim. Matrix probes are synthetic positive/negative controls. Historical captures are runtime-discovered evidence; replay is deterministic. C23 is explicitly partial, not fabricated wire fidelity. C5/C6 reflect the actual matching contract rather than imposing a nonexistent mandatory-ID rule. Normal data and frozen baseline hashes are checked at exit; prior fixed evidence sinks restored after regression.
