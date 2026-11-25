# AT-FG-01 — Storage and Artifact Governance Audit

Inventory date 2026-11-21 in America/New_York. Scope is the Ashen Thrones checkout at Git HEAD `6e59c070` and the explicitly identified adjacent stores. The checkout has one registered worktree.

## 1. Executive summary

**Verdict — Material placement and retention gaps confirmed.** The checkout contains **34.50 GB (32.13 GiB)** across **3,862,003 regular files**. The largest top-level consumers are `development/` (18.82 GB), `artifacts/` (11.37 GB) and `.git/` (3.54 GB). `development/tmp/` alone holds 12.60 GB. JSON and JSONL account for 27.30 GB, about 79.1% of measured bytes. Repeated isolated test stores and retained raw regression evidence drive the growth. The project generated review archives through competing scripts, so the stable review set lagged the session handoff.

**Recovery estimate** — 0.30 GB in the initial cache and aged-scratch screening pool, with a 13.88 GB gross ceiling across all named scratch, caches and the alternate environment. Actual recovery depends on path-level protection, age, reuse and allocation checks. Start with the 0.30 GB pool and extend into runner scratch only after checking active runs and references. The two confirmed misplaced published ZIPs and their sidecar are separate from this estimate. The smallest enforcement path is one policy in the existing review standard and placement and dry-run retention modes in the existing exporter.

## 2. Storage breakdown

| Git partition | Present files | Apparent bytes | Size |
| --- | --- | --- | --- |
| ignored | 3,395,902 | 12,828,970,944 | 12.83 GB |
| untracked nonignored | 322,711 | 11,402,095,021 | 11.40 GB |
| tracked working tree | 101,003 | 6,725,480,349 | 6.73 GB |
| git metadata | 42,387 | 3,544,994,953 | 3.54 GB |

The Git index names 101,054 distinct paths. 51 had no regular file at inventory time. Status partitions use index membership first, then the repository’s ignore patterns. The inspected checkout had no effective extra nested ignore files outside already ignored trees, no configured global excludes file or default global ignore file, and a comment-only Git info exclude. Repository arguments and representative Git ignore results were checked separately. The inventory used file metadata, skipped link and junction traversal, found no such links and recorded no enumeration failures. It counts file bytes once per pathname. NTFS cluster rounding, resident files, compression, hardlink sharing and directory metadata mean allocated space and freed bytes can differ. This was a point-in-time walk of a working tree with concurrent development.

Three relevant adjacent stores are outside the checkout total. The named archive store holds 4 ZIPs and 140,346,974 bytes. Three Ashen Thrones progress ZIPs add 70,578,025 bytes. Ashen Thrones Planning adds 34 files and 3,384,921 bytes. Together these add 214,309,920 apparent bytes to the related estate, for **34.72 GB**. Other sibling contents are excluded.

An independent Windows list-only traversal reproduced the `development/tmp/` count of 3,374,014 files and 12,599,909,312 bytes with zero enumeration failures.

### Storage by artifact category

| Category | Files | Apparent size |
| --- | --- | --- |
| Test or development scratch trees | 3,498,807 | 13.73 GB |
| Other generated artifacts | 287,859 | 9.73 GB |
| Milestone evidence trees | 12,933 | 6.27 GB |
| Git metadata and object history | 42,387 | 3.54 GB |
| Review exports and review manifests | 693 | 927.72 MB |
| Python environments (all copies) | 11,539 | 112.40 MB |
| Python/test caches and bytecode | 2,794 | 95.18 MB |
| Handoff history, reports and audits | 112 | 36.85 MB |
| Source, fixtures, docs and configuration | 2,238 | 34.54 MB |
| Development reports, scripts and static evidence | 2,359 | 9.51 MB |
| AT-OPT artifacts or reports (protected this audit) | 131 | 1.88 MB |
| Campaign data and runtime state | 151 | 1.43 MB |

The category rows partition the full checkout. Categories reflect path and file roles and can contain mixed protection classes. The rankings below are inclusive subtree totals, so parent and child rows overlap. The archive and evidence census uses separate indicators and does not add to these totals.

### Archives, evidence and handoffs

| Inventory indicator | Count | Apparent size |
| --- | --- | --- |
| All standalone archives outside Git and environments | 766 | 1042.99 MB |
| Review/report archive subset | 246 | 910.41 MB |
| Timestamped CURRENT_REVIEW ZIP subset | 35 | 444.69 MB |
| Other evidence archive subset | 508 | 120.37 MB |
| Named evidence directories, outermost literal evidence component per path | 4,391 | 6345.69 MB |
| Standard validation evidence packets, manifest plus summary | 16 | 3.95 MB |
| Archived report text in development/archive, docs/archive, handoff/history and history | 149 | 32.57 MB |
| Review summary and archive components, excluding manifests and checksums | 479 | 915.65 MB |
| Standalone REVIEW_MANIFEST.json files | 219 | 13.20 MB |
| Standalone NEXT_SESSION documents | 34 | 2.12 MB |
The named evidence directories contain 17,063 files. Archive indicators use suffix and path metadata. Other evidence archives exclude the review/report archive subset. The directory and archive counts can describe the same evidence in separate containers. Summary, manifest and ZIP counts represent files. A delivery can contain all three.

### Git storage

`.git/objects/` accounts for 3.15 GB. Git reported 42,053 loose objects and 36 packs containing 48,215 objects. The loose file census measured 2,777,721,380 bytes. The two largest Cursor search index files under `.git/cursor/crepe/` add 382.45 MB. They are editor-owned data whose active dependency has not been established. The three largest loose objects lack a path association in the local refs/reflogs surveyed. The unfiltered Git blob ID of the 175,696,637-byte `initial_diff.patch` matches the 143,503,824-byte loose object shown below. The patch begins with two historical review-ZIP diffs. Git objects and the internal editor index remain outside the working-tree recovery estimate.

### Largest 20 directories

| Rank | Directory | Files | Apparent size |
| --- | --- | --- | --- |
| 1 | `development` | 3,385,938 | 18816.92 MB |
| 2 | `development/tmp` | 3,374,014 | 12599.91 MB |
| 3 | `artifacts` | 417,679 | 11370.74 MB |
| 4 | `development/campaigns` | 11,785 | 6216.36 MB |
| 5 | `development/campaigns/product_realization` | 11,681 | 6214.46 MB |
| 6 | `.git` | 42,387 | 3544.99 MB |
| 7 | `development/tmp/scene-scope-regression` | 998,452 | 3490.13 MB |
| 8 | `.git/objects` | 42,338 | 3147.58 MB |
| 9 | `artifacts/atgb` | 25,988 | 1248.91 MB |
| 10 | `artifacts/atgb/automated_playtests` | 22,939 | 1115.80 MB |
| 11 | `development/campaigns/product_realization/pr_play_movement_intent_routing_integrity` | 1,322 | 975.34 MB |
| 12 | `development/campaigns/product_realization/pr_play_movement_intent_routing_integrity/evidence` | 1,282 | 975.17 MB |
| 13 | `development/campaigns/product_realization/pr_play_purpose_tail_destination_binding_integrity` | 624 | 804.80 MB |
| 14 | `artifacts/pr_play_72v` | 20,945 | 796.81 MB |
| 15 | `artifacts/pr_play_75` | 25,322 | 747.53 MB |
| 16 | `development/campaigns/product_realization/pr_play_pending_intention_clarification_recovery_integrity` | 688 | 737.88 MB |
| 17 | `development/campaigns/product_realization/pr_play_pending_intention_clarification_recovery_integrity/evidence` | 643 | 737.56 MB |
| 18 | `development/campaigns/product_realization/pr_play_compound_movement_social_admission_integrity` | 676 | 717.04 MB |
| 19 | `development/campaigns/product_realization/pr_play_compound_movement_social_admission_integrity/evidence` | 639 | 716.94 MB |
| 20 | `development/campaigns/product_realization/pr_play_disjunctive_destination_admission_integrity` | 666 | 716.93 MB |

### Largest 30 individual files

| Rank | File | Git class | Apparent size |
| --- | --- | --- | --- |
| 1 | `.git/objects/b0/7deac1f54871556581ffc5be9f0a508387ea88` | git metadata | 371.12 MB |
| 2 | `.git/cursor/crepe/6e59c070dcf522594c915ab39b61e198f56c3e28/postings.bin` | git metadata | 309.27 MB |
| 3 | `.git/objects/pack/pack-fd736d0b1a30867536dcbd075fcdc5a9825a779a.pack` | git metadata | 252.41 MB |
| 4 | `artifacts/pr_play_ruleset_equipment_policy_foundation/initial_diff.patch` | untracked nonignored | 175.70 MB |
| 5 | `.git/objects/ad/400a9de6c869542c1c3bf5de8084f362c1e096` | git metadata | 148.25 MB |
| 6 | `.git/objects/26/07b217201ef1fb3d08f7e65acba1e9911a0d03` | git metadata | 143.50 MB |
| 7 | `handoff/CURRENT_REVIEW(20261120-222708).zip` | untracked nonignored | 102.27 MB |
| 8 | `development/campaigns/product_realization/pr_play_purpose_tail_destination_binding_integrity/CURRENT_REVIEW(20261121-184924).zip` | untracked nonignored | 87.90 MB |
| 9 | `artifacts/pr_play_75/review_evidence/browser_network.json` | tracked working tree | 75.00 MB |
| 10 | `.git/cursor/crepe/6e59c070dcf522594c915ab39b61e198f56c3e28/index.bin` | git metadata | 73.18 MB |
| 11 | `development/tmp/git_sync/inventory.json` | ignored | 68.50 MB |
| 12 | `artifacts/pr_play_73/holdout_network.jsonl` | tracked working tree | 57.40 MB |
| 13 | `artifacts/pr_play_72/holdout_network.jsonl` | tracked working tree | 54.98 MB |
| 14 | `handoff/CURRENT_REVIEW(20261120-205634).zip` | untracked nonignored | 54.95 MB |
| 15 | `artifacts/pr_play_66/holdout_results.json` | tracked working tree | 53.91 MB |
| 16 | `artifacts/pr_play_72v/holdout_network.jsonl` | tracked working tree | 49.69 MB |
| 17 | `.git/objects/d3/fea82e517035d86e2993d7cb58868a769da5be` | git metadata | 47.79 MB |
| 18 | `artifacts/pr_play_authored_topic_retrieval/http_matrix.json` | untracked nonignored | 46.42 MB |
| 19 | `artifacts/pr_play_75/browser_network.jsonl` | tracked working tree | 44.36 MB |
| 20 | `handoff/CURRENT_REVIEW(20261121-125137).zip` | untracked nonignored | 42.03 MB |
| 21 | `artifacts/pr_play_75/http_traces.json` | tracked working tree | 40.53 MB |
| 22 | `artifacts/pr_play_75/review_evidence/http_traces.json` | tracked working tree | 40.46 MB |
| 23 | `artifacts/pr_play_71/browser_network.jsonl` | tracked working tree | 40.14 MB |
| 24 | `artifacts/pr_eg_r2c_r2/qualification_before_irrelevant_annotation_fix/live_qualification.json` | tracked working tree | 39.76 MB |
| 25 | `artifacts/pr_eg_r2c_r2/live_qualification.json` | tracked working tree | 39.56 MB |
| 26 | `artifacts/pr_play_ordinary_semantic_admission/state_comparisons.json` | untracked nonignored | 38.96 MB |
| 27 | `handoff/CURRENT_REVIEW(20261120-172513).zip` | untracked nonignored | 38.54 MB |
| 28 | `artifacts/pr_play_72v/http_traces.json` | tracked working tree | 38.51 MB |
| 29 | `artifacts/pr_play_grounded_information_ownership/http_matrix.json` | untracked nonignored | 38.40 MB |
| 30 | `artifacts/pr_play_broad_gameplay_evaluation/raw_records.jsonl` | untracked nonignored | 38.00 MB |

### Storage by file extension

| Extension | Files | Bytes | Extension | Files | Bytes | Extension | Files | Bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.json` | 3,629,283 | 20,230,445,976 | `.before` | 11 | 1,128,988 | `.bsd` | 6 | 8,064 |
| `.jsonl` | 100,539 | 7,072,682,322 | `.html` | 8 | 654,491 | `.ini` | 4 | 7,476 |
| None | 43,278 | 2,854,699,455 | `.gif` | 2 | 630,957 | `.bat` | 5 | 3,132 |
| `.py` | 65,746 | 1,853,878,479 | `.js` | 16 | 541,811 | `.fish` | 1 | 3,132 |
| `.zip` | 761 | 1,036,907,923 | `.nul` | 1 | 323,625 | `.nu` | 1 | 2,817 |
| `.bin` | 2 | 382,450,284 | `.jpg` | 4 | 304,946 | `.7ghpoqe7` | 1 | 2,615 |
| `.pack` | 36 | 313,490,333 | `.rev` | 36 | 194,732 | `.sha256` | 23 | 2,562 |
| `.txt` | 1,907 | 183,794,795 | `.docx` | 4 | 162,966 | `.mit` | 2 | 2,092 |
| `.patch` | 35 | 177,267,706 | `.pyi` | 6 | 116,644 | `.sh` | 2 | 1,892 |
| `.pyc` | 8,104 | 133,685,340 | `.28808` | 2 | 97,397 | `.typed` | 101 | 1,142 |
| `.xml` | 2,277 | 74,042,845 | `.apache` | 6 | 61,044 | `.mdc` | 1 | 1,140 |
| `.md` | 7,306 | 71,080,912 | `.ps1` | 14 | 52,379 | `.y9sglq_0` | 1 | 1,050 |
| `.pdf` | 5 | 29,398,459 | `.5104` | 1 | 38,543 | `.cfg` | 2 | 863 |
| `.pyd` | 16 | 22,108,160 | `.sample` | 14 | 25,827 | `.tag` | 3 | 573 |
| `.diff` | 120 | 18,560,168 | `.apache2` | 2 | 22,716 | `.example` | 1 | 519 |
| `.png` | 105 | 12,107,019 | `.css` | 5 | 22,670 | `.iml` | 1 | 416 |
| `.exe` | 59 | 7,127,440 | `.cjs` | 6 | 20,454 | `.tmpl` | 2 | 356 |
| `.log` | 1,972 | 7,017,389 | `.rst` | 2 | 18,616 | `.pth` | 2 | 169 |
| `.gz` | 5 | 6,086,512 | `.1` | 2 | 15,119 | `.0` | 1 | 41 |
| `.z` | 1 | 2,940,807 | `.12828` | 1 | 13,922 | `.pid` | 4 | 20 |
| `.bak` | 12 | 2,491,188 | `.tmp` | 1 | 9,107 | `.4nunnn3n` | 1 | 0 |
| `.csv` | 75 | 1,872,171 | `.9sn0u6ub` | 1 | 9,021 | `.ih71e7ew` | 1 | 0 |
| `.pem` | 6 | 1,494,044 | `.13488` | 1 | 8,783 | `.lock` | 1 | 0 |
| `.idx` | 36 | 1,388,612 | `.yml` | 2 | 8,099 | `.virtualenv` | 2 | 0 |

## 3. Misplaced artifact findings

| Pattern | Expected and actual locations | Evidence and cause | Recommended correction |
| --- | --- | --- | --- |
| **Two confirmed misplaced published ZIPs and one sidecar** | Expected stable files under `handoff/`, approved history under `handoff/history/<campaign-id>/`. Actual files in the `pr_play_purpose_tail_destination_binding_integrity` and `pr_play_fresh_live_foundational_capability_validation` campaign report directories. | The first packager sets `ROOT` to its own directory and hardcodes `ARCHIVE = ROOT / …`. The second correctly resolves the repository root, deliberately writes its primary ZIP and checksum under `REPORT`, then copies them into `handoff/`. The session handoff directly links both campaign ZIPs. This is deliberate output code independent of the executing shell’s CWD. | Direct both publishers to the shared exporter. Validate and update current pointers before consolidating either file. |
| **21 timestamped ZIPs directly under handoff** | The location is the review area. The stable and historical naming contracts instead use `CURRENT_REVIEW.zip` and per-campaign `REVIEW.zip`. The dated files total 351.04 MB. | Multiple milestone scripts hardcode `handoff/CURRENT_REVIEW(<timestamp>).zip`. The stable Markdown still declares the 2026-11-18 *Extended live continuity validation* campaign while `docs/NEXT_SESSION.md` points to the 2026-11-21 foundational run. | Publish the stable set as one verified generation. Keep approved history by campaign. |
| **Staging and evidence copies resemble published handoffs** | Expected stage under `development/tmp/` or explicit evidence metadata. The broader screen found 198 `CURRENT_REVIEW*` files outside `handoff/`, 97 `REVIEW_MANIFEST.json` files outside `handoff/`, and 33 `NEXT_SESSION.md` copies outside `docs/`. Together with the 21 dated handoff ZIPs, the four disjoint screening groups account for **349 files**. | Existing packagers explicitly build under `review_export`, archive prior reviews, or save frozen source snapshots. The screen includes intentionally preserved fixtures, AT-OPT material, and ignored scratch. Several copies use an authorized historical role. The 349 figure is a placement screen. The confirmed published wrong-location count is two ZIPs plus one sidecar. | Distinguish staging, snapshots and publication in the manifest. Enforce path placement only for new published outputs and default temporary staging to the existing scratch tree. |
| **Raw evidence beside campaign reports and legacy root reports** | Generated artifacts belong in `artifacts/<topic>/`. Recent milestones retain large `development/campaigns/product_realization/<milestone>/evidence/` trees. A filename screen found 51 legacy-pattern root report/JSON files (0.94 MB). No published review ZIP was present at root. | Current milestone runners explicitly bind output to `REPORT / "evidence"`. Two root review ZIP paths are recorded in HEAD and absent from the worktree. Root report names include older material. The audit establishes current path drift for new evidence and leaves provenance of individual older root reports open. | Apply the approved placement policy to future writers. Preserve live references before deciding what to do with prior output. |

There is no literal `Campaign/Product_Realization/` path in this checkout. The equivalent active lane is `development/campaigns/product_realization/`. The shared exporter’s explicit relative `--output-dir` can still resolve from the caller’s CWD because it is accepted as a path and used directly. That is a possible drift mechanism. The two traced campaign cases use fixed script-relative targets and establish a separate cause. The rules were already in effect when those archives were produced. Copy retention and the stale stable review demonstrate missing publication validation without requiring an assumption about agent intent. [Purpose-tail packager](../campaigns/product_realization/pr_play_purpose_tail_destination_binding_integrity/_package_review.py#L7) · [Foundational live packager](../campaigns/product_realization/pr_play_fresh_live_foundational_capability_validation/package_review.py#L37) · [Session handoff](../../docs/NEXT_SESSION.md) · [Stable review](../../handoff/CURRENT_REVIEW.md)

### Duplication and regeneration

- **Confirmed review duplicate.** Both `CURRENT_REVIEW(20261121-194840).zip` copies are 4,121,947 bytes with the same SHA-256 and distinct file identities. The campaign pointer remains active. In **HEAD**, 58 groups of equal ZIP blob IDs represent 75 extra paths and 235,701,613 logical bytes of duplicate ZIP content. Those historical path counts overlap absent paths and saved history, so they are not current recoverable bytes. The inspected newer archives have different contents and sizes.
- **Raw output and workspaces.** The named evidence census includes prior acceptance reruns, state snapshots and distinct before/after comparisons. For example, T11 movement, compound admission, disjunctive admission, and purpose-tail packages contain their own regression summaries and provenance. The two sampled `pr_play_47_workspace` and `pr_play_49_workspace` trees contain requirements and scene files identical to the current checkout, alongside historical source that differs from the current version. Each copied checkout needs a restore and dependency check before it can serve as a replacement for another. `development/tmp/scene-scope-regression/` alone has 999 immediate run roots and 998,452 files (3.49 GB). The runner creates a separate `mkdtemp` and pytest base directory for each partition and supplies no matching cleanup. This explains why retained scratch grows even when Git ignores it. [Partition runner](../campaigns/product_realization/pr_play_current_scene_evidence_scope_integrity/run_regression_partitions.py#L82)
- **Captures and traces.** Outside Git and the environments, filename indicators identify 1,292 state/snapshot files (653.48 MB), 1,144 provider/payload files (43.91 MB), and 109 media or HAR files (12.41 MB). Large browser/network JSON and JSONL are separate from the media indicator. Similar captures may reflect different worlds, provider calls or failure conditions. The oldest raw provider output may be the sole original and cannot be recreated exactly by rerunning an evaluation.
- **Nested backups.** The inspected current review ZIPs held no nested ZIPs. The adjacent checkpoint ZIP has 14 nested archives and 2,663 environment entries. The first playable-slice backup includes 1,305 Git entries and 11,401 environment entries. These are metadata observations from ZIP central directories without extraction. They document backup breadth and do not establish safe deletion.

### Existing authority and enforcement

| Artifact owner | Current rule and existing mechanism |
| --- | --- |
| Runtime, specifications, fixtures and tools | Runtime stays with `game/`, `data/` and `static/`. Standing governance lives in `docs/`, canonical inputs in `data/validation/`, tests in `tests/`, and reusable producers in `tools/` or `scripts/`. |
| Session orientation | `docs/NEXT_SESSION.md` is the sole canonical session handoff. It has 27 current-milestone headings and 563 lines in this snapshot because prior handoffs were repeatedly appended. This conflicts with its required concise orientation role. |
| Review delivery | Stable `handoff/CURRENT_REVIEW.md`, `handoff/REVIEW_MANIFEST.json`, `handoff/CURRENT_REVIEW.zip`, with optional `handoff/history/<campaign-id>/REVIEW.*`. The standard builder resolves its default from its own source location. It uses explicit sources, item exclusions, SHA-256 deduplication inside each export, a default 5 MiB input limit and a 20 MiB bundle warning. It copies to per-campaign history by default and has `--no-history`. It has no cross-run expiry or publication-path guard on its explicit `--output-dir` override. |
| Reports and evidence | Campaign reports belong in their `development/campaigns/` lane. Housekeeping reports belong in `development/reports/`. Generated evidence belongs in `artifacts/<topic>/`. Standard validation packets contain `evidence_summary.md` and `evidence_manifest.json` with canonical references. Protected replay already has CF6 importance, regeneration, producer and consumer inventories. Frozen BW/BZ trend fixtures are protected despite their location under `artifacts/`. |
| Scratch, caches and local environments | The Constitution and `pytest.ini` put disposable agent/pytest output under `development/tmp/`. Ignore rules also cover environment folders, bytecode and selected legacy test prefixes. Names such as `basetemp_*` and `tmp_runs` in arbitrary artifact trees have no universal ignore rule. Ignore policy affects Git discovery and does not provide expiry or dependency checks. |
| Current enforcement | CI checks the protected replay manifest and existing ownership inventories. It uploads protected-replay diagnostics on failure and content lint output separately. Neither workflow enforces repository-wide generated-file placement, output budgets or local expiry. `tools/build_validation_cleanup.py` builds a JUnit-based cleanup ledger. It is unrelated to filesystem cleanup. The prior manual storage cleanup removed 31,886 tracked pytest-store files (523,570,476 logical bytes) in `e86fd451`, and `9f6a0088` removed the tracked obsolete environment after an external archive. Neither operations model became a general retention tool. |

The working Constitution records a 2026-11-13 amendment on ruleset independence. The 2026-09-20 repository organization introduced the placement rule, and the 2026-10-18 governance adoption retained the standard review destination. The only repository Cursor rule found governs player-facing OC text. No applicable `AGENTS.md` or separate repository Codex placement instructions were found in the inspected root, ancestors, or tracked index. The old review-handoff inventory describes the pre-automation state. The active Constitution and review standard agree on placement. [Constitution](../../docs/DEVELOPMENT_CONSTITUTION.md#repository-file-placement-and-generated-artifacts) · [Review standard](../../docs/review_handoff_standard.md#stable-location) · [Organization decision](REPOSITORY_ORGANIZATION_runtime_development_archive_boundaries.md) · [Amendment adoption](constitution_amendment_adoption_progress_and_benchmark_governance.md) · [CF6](../../docs/audits/CF6_generated_projection_artifact_governance.md) · [CI](../../.github/workflows/convergence-checks.yml) · [Builder](../../tools/build_review_handoff.py)

## 4. Cleanup candidates

| Scope | Files | Apparent bytes | Risk and reference status | Proposed treatment |
| --- | --- | --- | --- | --- |
| Caches and bytecode outside environments | 2,794 | 95,180,953 | Low after confirming owners are idle. Named AT-OPT matches and tracked files excluded. | Regenerate on demand. Start here. |
| Aged scratch screening subset | 24,385 | 206,193,505 | Medium. Entire matched scratch root last changed before 2026-11-07 UTC. Check active references and evidence first. | Inventory owner and keeper, then approve per path. |
| All named scratch, inclusive of aged subset | 3,498,807 | 13,731,066,165 | Medium to high. Includes recent runs, supplemental validation and copied stores. No blanket dependency clearance. | Process by stopped producer and validated run. Start with aged subset and then split development/tmp by owning run. |
| Alternate Python 3.9 environment | 5,390 | 49,494,117 | Medium. Live helper defaults to .venv (Python 3.12). External editor or shell use of venv/ remains unresolved. | Confirm interpreter dependencies and reproducibility before retirement. |
| Byte-identical active review twin | 1 | 4,121,947 | High while referenced by the current handoff. A verified distinct-file survivor exists. | Consolidate after authorized pointer change and survivor verification. Excluded from estimates above. |
| Cursor index and Git loose objects | Separate scope | See Git storage | High. Editor and Git ownership and reachability differ from artifact expiry. | Preserve in the file-cleanup batch. |

Initial screened bytes are 301,374,458 (cache plus the aged subset). The broad 13,875,741,235-byte ceiling is the sum of all named scratch, caches and the alternate environment, with the aged subset counted once. The ceiling includes recent and potentially protected material. Coverage is conservative for the initial batch because grouping at the first scratch component treats the recently updated `development/tmp/` tree as one age unit. Split it by producer and run during the approved candidate review to find older candidates safely. The existing `.venv-broken/` tree contributed no regular file bytes at inventory time.

### Provisional protection classes

- **P0 — Protected.** Source, configuration, canonical handoffs and governance, campaign data, live saves, fixture inputs and frozen replay baselines. Some authoritative files live in generated-looking trees.
- **P1 — Active.** Current review or campaign evidence, the two active handoff pointers involved in the duplicate, open issue reproductions, sole provider captures and provenance. All ongoing AT-OPT work and its dependencies remain pinned.
- **P2 — Historical.** Superseded exports, completed milestone reports, approved archive snapshots and settled replay exhibits. Distinct successful reruns may retain required regression identities or counterfactual evidence.
- **P3 — Disposable candidates.** Rebuildable caches, expired scratch with no dependents, regenerable successful-run diagnostics and copies confirmed redundant against a verified survivor. Age, filename and Git status are screening signals. A reference, unclear provenance or an active job keeps a candidate out of cleanup.

## 5. Proposed retention policy

| Class | Retention and protection |
| --- | --- |
| P0 | Indefinite. Any removal or relocation requires a separate source or fixture decision, compatibility checks and explicit approval. |
| P1 | Pin until the investigation is resolved and the owner removes the pin. Allow at least 30 days after sign-off before recategorizing. Preserve unique raw provider evidence, unresolved failures, recipes, input state, exact replay fixtures and their manifests for as long as the claim relies on them. |
| P2 | Keep milestone summaries, manifests, source pointers and selected decisive evidence indefinitely. Keep the stable current export and up to two recent full review exports per active track for 90 days. An archival or external-review pin extends retention. Preserve personally reviewed or nonregenerable records regardless of age. |
| P3 | Allow 7 days for ordinary abandoned run scratch and bytecode after the producer is inactive, 14 days for successful local test diagnostics, and 30 days for disposable screenshots, browser captures and normalized snapshots once their owning summaries are verified. A proven redundant copy can enter a cleanup plan sooner once the keeper and every pointer are verified. |

Apply the longest requirement when classifications overlap. Count age from successful completion or explicit release of a pin. A missing owner, uncertain dynamic reference, active run or failed restore check blocks expiry. Reproducible offline output still needs its fixture, invocation and source revision. Exact live provider output is singular evidence even if a fresh call could be made.

## 6. Proposed enforcement design

Put the short placement, protection and retention rules in the existing review handoff standard, using the Constitution’s existing delegation. Extend `tools/build_review_handoff.py` with one shared placement check and a read-only retention plan mode. Keep the existing manifest as the provenance record. Use a small optional pin list in the existing configuration format for active paths and expiry exceptions. Resolve all paths against the Git root. Reject escapes or reparse-point traversal, and allow temporary export paths explicitly under the existing scratch tree.

Route existing packagers through this entry point. Give both agent environments the same block-completion command. Require a validated stable review set and optional approved history entry. Check that the session pointer, manifest and emitted archive agree. Validate changed paths and new exports during block completion and, if approved, on the relevant CI diff. Keep checks cheap by using metadata and existing manifest digests. Hash only suspected duplicates before disposal. Print the dry-run candidate list with owner, reason, scope and protected survivor to stdout. Keep the reviewed deletion list separate from the validator’s routine output.

## 7. Implementation plan

**AT-FG-02 — Controlled cleanup.** Freeze a candidate list and ask the owner to reconfirm the active AT-OPT and PR-PLAY pins. Validate references in tests, tools, manifests, handoffs and known editor/task configuration. Start with rebuildable caches and old ignored scratch with a verified generation path. Where a historical store carries unique evidence, verify an approved archival copy and restore before any removal. Keep current review duplicates and tracked historical artifacts in a separate approval batch. Record measured before/after apparent and allocated space for the exact approved paths.

**AT-FG-03 — Permanent governance enforcement.** Approve the policy in the existing standard. Add the two modes to the existing exporter, route a representative independent packager through it, add focused path and pin tests, and enable the cheap changed-path check after a dry-run baseline. Adopt the same invocation in Cursor and Codex completion instructions if authorized. Extend producer coverage by existing owner and scope. Preserve historical manifests and links during transition.

## 8. Authorization boundary

The authorized audit deliverable is this one report. AT-FG-02 requires explicit approval for the concrete path list and each operation type: deleting files, moving or renaming them, compressing into an archive, copying to another store, replacing a current ZIP or manifest, restoring a preserved copy for validation, and rewriting references or handoff pointers. Tracked-path/index changes, commits, pushes, and Git object maintenance each require separate authorization. History rewriting is outside the proposed cleanup.

AT-FG-03 requires approval to edit policy, agent instructions, Git ignores, the exporter, producers, tests or workflows, add pins or change their retention, enable a check or scheduled action, and publish or regenerate outputs. Existing files and ongoing AT-OPT work were left in place. No cleanup or enforcement was executed.
