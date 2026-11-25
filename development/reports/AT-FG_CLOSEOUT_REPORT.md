# Ashen Thrones filesystem governance closeout

**FILESYSTEM GOVERNANCE CLOSED.** AT-FG-07 finished **PARTIAL / ACCEPTED / CLOSED** with integrity PASS. Historical artifact and campaign consolidation had already closed with AT-FG-06-EXEC.

## Objective and milestones

Reduce disposable storage and file-count pressure while preserving active gameplay state, review history, and regression evidence. AT-FG-01 established the storage baseline. AT-FG-02A removed confirmed caches. AT-FG-02B inventoried and verified existing scratch, followed by the separately recorded pilots. AT-FG-03A and AT-FG-03B added producer-scoped lifecycle cleanup. AT-FG-03B-R1 traced and corrected the ownership failure. AT-FG-04 completed the verified TMP population and audited historical artifact and campaign candidates. AT-FG-05 archived or removed qualified history, with R1 reconciling interruption, R1B validating the continuation, and R2 executing it. AT-FG-06 consolidated additional fully covered historical evidence and accepted the protected and unsupported residual. AT-FG-07 closed the remaining practical TMP scope and documented retention.

## Cumulative accounting

| Accepted accounting boundary | Apparent bytes | Files removed |
| --- | ---: | ---: |
| AT-FG-02A | 16,246,229 | 409 |
| AT-FG-02B Pilot A | 0 | 0 |
| AT-FG-02B Pilot B | 499,915,051 | 149,706 |
| AT-FG-04 remainder | 3,671,945,277 | 1,113,200 |
| AT-FG-05 original execution, reconciled | 344,409 | 54 |
| AT-FG-05 R2 incremental execution | 2,231,559,339 | 71,550 |
| AT-FG-06-EXEC net of retained archives, index and durable evidence | 1,565,286,999 | 3,477 |
| Prior comparable reported basis | 7,985,297,304 | 1,338,396 |
| AT-FG-07 verified TMP removal | 312,862,520 | 54,955 |
| Cumulative before AT-FG-07 governance overhead | 8,298,159,824 | 1,393,351 |

The prior subtotal reproduces the reported approximately 7.985 GB basis. It uses documented ledger removal for the TMP and AT-FG-05 phases and the authoritative net figure for AT-FG-06. The 54 original AT-FG-05 removals include the interrupted target and are counted once. The three unauthorized AT-FG-03B directory removals and their 27 files are excluded from accepted recovery. Directory-only Pilot A contributes zero bytes and zero files. The final net apparent figure after new governance overhead and exact package costs is recorded in the [review verification receipt](../../handoff/history/at_fg_07/REVIEW_VERIFICATION.json). These accounting totals are distinct from measured whole-volume free-space movement.

## TMP result and retained storage

AT-FG-07 accounted for 335,438,056 allocated bytes removed and measured a volume free-space change of +90,636,288 bytes over execution. TMP holds 8,407,115,386 apparent bytes, 9,502,380,168 allocated bytes, 2,064,871 files, and 204,886 directories. The largest remaining allocated concentrations are `compound_guard`, `pr_play_cross_scene_recall_routing_integrity`, `scene-scope-regression`, `inventory_binding`, `ordinary_admission`. The machine-readable accounting also ranks by file count and nested concentration.

**Intentionally retained** material includes active campaign stores, regression and holdout evidence, supported archives, original reports, record-bearing governance workspaces, and the PR-PLAY-47 and PR-PLAY-49 protected TMP trees. **Ambiguous material** includes the preserved diagnostic scene-scope roots, rejected atomic-temp cases, and mixed gameplay scratch with unestablished provenance or use. **Proportionality retention** covers remaining low-yield candidates and workspaces that would need extended classification or additional engineering. The residual is accepted.

## Preservation and incident lessons

AT-FG-07 produced zero unauthorized deletions. Git integrity, protected TMP root identity and census, and targeted historical and regression evidence checks passed. AT-FG-03B-R1 established that an operator's wildcard selected three pre-existing social-reconciliation directories during validation cleanup. Those 27 files remain an unrecovered historical loss. Process ownership must be established with creation records or equivalent positive evidence. Final candidate lists must bind exact paths, verify parents and exclusions, and record actual verified absence.

The standing [artifact retention policy](../../docs/ARTIFACT_RETENTION_POLICY.md) governs producer-owned temporary output, investigation evidence, historical evidence, and review packages. The [TMP final report](AT-FG-07_FINAL_REPORT.md) details execution. The [next-session handoff](../../docs/NEXT_SESSION.md) resumes the separately authorized PR-PLAY / ATGB gameplay objective after the closed AT-OPT-06 sequence. It preserves the inherited PR-PLAY-72V failures and the recent NPC-grounding finding.
