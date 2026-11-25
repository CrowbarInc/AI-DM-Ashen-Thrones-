# AT-FG-07 final TMP cleanup report

**Verdict PARTIAL / ACCEPTED / CLOSED. Integrity PASS.** The run verified the removal of 54,955 files and 5,332 directories. Every verified deletion belonged to the frozen manifest and was inside `development/tmp/`. Unauthorized deletions were **0**.

## Fresh storage accounting

| Measure | Before | After | Verified removed |
| --- | ---: | ---: | ---: |
| Apparent file bytes | 8,719,977,906 | 8,407,115,386 | 312,862,520 |
| Allocated file bytes | 9,837,818,224 | 9,502,380,168 | 335,438,056 |
| Regular files | 2,119,826 | 2,064,871 | 54,955 |
| Directories | 210,218 | 204,886 | 5,332 |

Volume free space changed from 376,930,959,360 to 377,021,595,648 bytes over the deletion window, a measured change of **+90,636,288 bytes**. Apparent bytes are file lengths. Allocated bytes are NTFS file allocations and exclude directory metadata. The free-space change reflects all activity on the volume. The pre- and post-censuses reconciled to the ledger across 30,480 total, top-level, and nested groups. 0 unsupported entries were excluded from the ordinary-object census and left alone. A fresh whole-checkout census was omitted to keep the closeout proportional. The scope ledger and the measured governance overhead in the review receipt account for this milestone's repository footprint.

## Eligible and skipped targets

The frozen manifest included 1,219 non-overlapping exact roots and individual files. It covered 1,103 pytest trees from documented PR-PLAY-77, PR-PLAY-78 and PR-PLAY-78A runs, 112 marked R1B synthetic fixtures, and 4 Python bytecode files. The prior AT-FG-04 closeout accounted for the previously verified AT-FG-02B cleanup population. The producer-declared test roots and retained diagnostics supported treating their ordinary copied state as scratch. The PR-PLAY-78A review input `regression_results.json` and neighboring logs and JUnit files were excluded. The R1B harness's marker and synthetic layout established provenance. Case names alone could not qualify an object.

Before deletion, the run verified the repository and TMP identities, current tracked-file exclusion, dependencies, protection records, activity, parent chains, exact membership, file hashes, and supported NTFS objects. The established AT-FG-05 no-follow handle verifier rechecked identity and verified absence twice. Its ledger recorded durable intent before disposition. Final target states were {'DELETED-VERIFIED': 1219}. Preflight retained 25 inspected candidates with nonstandard output, protection or dependency concerns, or unsupported objects. Exact reasons are in the assessment.

Manifest SHA-256 `d88e71553b782fdcb51d4ab7679aa5626a27465e828f85bb8b328a0905c4c083`. The digest covers the compressed manifest bytes and binds exact nested membership, identities, metadata, hashes, and protection and dependency checks. The compact ledger identifies verified sets by manifest index.

## Major populations remaining

| TMP top-level path | Allocated bytes | Apparent bytes | Files |
| --- | ---: | ---: | ---: |
| `compound_guard` | 272,243,008 | 234,065,012 | 86,570 |
| `pr_play_cross_scene_recall_routing_integrity` | 252,731,128 | 212,015,106 | 89,440 |
| `scene-scope-regression` | 250,904,240 | 167,107,813 | 128,059 |
| `inventory_binding` | 232,095,216 | 198,167,516 | 68,576 |
| `ordinary_admission` | 207,977,408 | 180,934,033 | 54,311 |
| `campaign_ruleset_binding` | 166,286,056 | 130,278,556 | 79,852 |
| `pr_play_49_workspace` | 162,839,368 | 154,000,730 | 4,578 |
| `pr_play_47_workspace` | 160,143,024 | 151,592,986 | 4,446 |

- **Intentional retention.** Social reconciliation, live campaign stores, PR-PLAY-47 and PR-PLAY-49 protected workspaces, prior governance records, retained archives, active state, and regression and review dependencies. Recent governance scratch that carries execution records, including the R2 journal and review inputs, stays with its evidence.
- **Ambiguous retention.** Prior scene-scope diagnostic roots, atomic-temp exceptions, mixed runner and campaign trees such as compound_guard, inventory_binding and ordinary_admission, nonstandard pytest outputs, and scratch whose origin or downstream use could not be established through targeted inspection.
- **Proportionality retention.** Other isolated workspaces, empty producer parents, and low-yield diagnostics remained where broader proof or a different deletion mechanism would have taken disproportionate time. The report does not classify these as eligible targets.

## Integrity and review

Git branch, HEAD, raw index, staging, and pre-existing tracked status and modifications matched across execution. No pre-existing untracked Git path disappeared. The retained evidence check covered 92 anchors. Nine exact live campaign and AT-OPT roots matched their AT-FG-06 identities, metadata and content digests. Protected TMP roots retained their identities and reconciled census counts. The run used prior protection evidence and exact deletion scope to preserve campaign, regression, archive and governance records. This was a focused integrity check. Gameplay tests and live providers were unused.

The intentional changes are the retention policy, the prepended next-session handoff, this report and the workstream closeout, the compact evidence under `artifacts/at_fg_07/`, and the historical review package. The prior handoff bytes remain embedded after the new section. The governance evidence is available under [AT-FG-07](../../artifacts/at_fg_07/). The [review package](../../handoff/history/at_fg_07/REVIEW.zip) includes its provenance manifest and the [verification receipt](../../handoff/history/at_fg_07/REVIEW_VERIFICATION.json) accounts for packaging overhead.
