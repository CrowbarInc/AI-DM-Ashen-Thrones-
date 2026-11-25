# AT-FG-03A — Temporary execution lifecycle repair

**Disposition: PARTIAL.** The scene-scope partition runner and default pytest lifecycle were repaired. Older campaign-specific runners that own explicit pytest bases and retained replay output remain open. This milestone is an implementation repair for validation infrastructure. It makes no gameplay-quality claim.

## Baseline and authorities

- Branch `feature/product-realization`, HEAD `6e59c070dcf522594c915ab39b61e198f56c3e28`. The initial working tree already contained modified game, test and document sources, missing review archives, and extensive untracked evidence and campaign source. The scene-scope runner itself was present as an untracked campaign script. No restoration, checkout, commit or push was performed.
- Read the Development Constitution, Review Handoff Standard, session and stable review pointers, AT-FG-01 audit, AT-FG-02A candidate manifest and AT-FG-02A-EXEC report. A standalone verification report was not found. The manifest and execution report include the prior verification findings.
- AT-OPT-06 is the numbered optimization closeout. Protected references include `artifacts/at_opt_01` through `at_opt_06`, `artifacts/pr_play_79df3/protected_entry.json`, AT-OPT tests, and related campaign reports. The current PR-PLAY pointer names the fresh foundational capability validation, whose report and newest review archives were pinned alongside the previous purpose-tail campaign and reconciled live state.
- Process-name inspection returned no visible test runner at entry. Higher-detail Windows CIM process inspection was denied by the runtime, so host-wide process ownership was not verified. Recent repository-local workspaces were inventoried by top-level directory mtime. Their runtime state and historical status were treated as protected.
- AT-FG-02A-EXEC recovered 16,246,229 apparent bytes from 409 authorized files. That prior result is separate from this repair. The existing stable review predates the current PR-PLAY session pointer.

## Producer inventory and root cause

The [producer manifest](AT-FG-03A_PRODUCER_MANIFEST.json) records paths, lifecycles, consumers, risk, and disposition for each producer family. The investigation searched the checkout's pytest config, tests, development runners, tools, shell entry points and AT-OPT evidence scripts for temporary allocation, explicit pytest bases, recursive cleanup, subprocesses and evidence writers.

| Producer | What the checkout does | Disposition |
| --- | --- | --- |
| Scene-scope partitions | Allocates a unique root for every partition, gives pytest an explicit child base and collects diagnostics into scratch. The original runner has no matching cleanup. Downstream PR-PLAY workers reuse the same function. | Fixed at the shared worker. |
| Default pytest and test storage | Defaults to one shared path that pytest recursively recreates. The configured persistence helper also opens a separate OS-temp test store without cleanup. | One private workspace per session, with repository-controlled teardown. |
| Older PR-PLAY wrappers and lane tools | Allocate explicit timestamped or fixed pytest bases and own distinct JUnit, diagnostic and frozen-comparison paths. | Deferred. Some consume the retained scratch, and fixed output tools can republish prior evidence. |
| Live PR-PLAY campaign harnesses | Keep session state used by integrity and continuity checks under named paths in `development/tmp/`. | Protected active or historical investigation data. |
| Standalone replays | Some use context managers already. Other `run-*` roots contain retained acceptance matrices and state traces. | Preserve published outputs and classify dependencies before migrating older writers. |
| AT-OPT and ATGB | AT-OPT holdout source retains a manual OS-temp root. ATGB can retain caller-specified stores and suppresses implicit cleanup errors. | Preserve AT-OPT evidence. Defer separate ATGB ownership and early-failure checks. |
| Legacy OS-temp scripts and tests | Continuation probes and several local provider-usage tests allocate OS-temp directories directly. | Deferred. Local test writers can be next candidates for `tmp_path`. |

The earliest faulty decision was allocating disposable scratch in a per-partition directory without giving the allocating worker a termination path. In the baseline the scene-scope parent held 999 immediate directories. Stable partition-name stems recur across the historical roots, and later PR-PLAY orchestration repeatedly invokes the same allocator. Git ignore rules hid this storage from ordinary status output. Default pytest additionally exposed an independent cross-run deletion risk through its fixed base. Required fixture *copies* and scratch state are execution-owned. Canonical fixture inputs, campaign saves, raw diagnostic bundles, replay records, and milestone review artifacts have separate owners.

## Implemented lifecycle

- Scene-scope creates one exact `mkdtemp` root per worker. Pytest places both its fixtures and the isolated persistence store inside it. The numbered XML slot is reserved exclusively, so the same partition cannot race or overwrite prior evidence. New dry reruns can point the runner at a fresh campaign partition directory with `--output-dir`.
- Numbered JUnit and partition metadata retain their established filenames and selection semantics. Tests that write to `ASHEN_TEST_EVIDENCE_DIR` write into a per-worker directory adjacent to those reports. Partition metadata records the directory name. After readable JUnit and JSON are available, the worker removes its exact workspace. Failed tests still contribute results to the historical merge contract. The recorded pytest exit code remains 1 for assertion failure, and the historical orchestration exit is 0 for mergeable results.
- A pytest interruption that reaches normal report publication logs the retained evidence paths and removes scratch. If execution aborts or reports cannot be published, the runner reports the original scratch path and retains it for diagnosis. A cleanup error emits the failing path and propagates an error. A process kill, native crash or OS shutdown can bypass cleanup entirely. There is no automatic stale-directory sweep.
- Standalone pytest creates a unique default base and fixture store. A successful session removes its own workspace after session finish hooks complete. A failed or interrupted standalone session retains its workspace and reports the path. Explicit `--basetemp` remains the calling tool's responsibility. Caller-managed partition workspaces are never removed by pytest.
- Neither test assertion/selection nor production gameplay code changed. Campaign files are cloned into workspace-local storage through the existing isolation guard. One worker's teardown never scans sibling workspaces.

## Files and validation

Modified `pytest.ini`, `tests/conftest.py`, and `development/campaigns/product_realization/pr_play_current_scene_evidence_scope_integrity/run_regression_partitions.py`. The constitutional session note adds an AT-FG-03A pointer while retaining the previous PR-PLAY orientation. New reports are stored under `development/reports/`, validation and review input under `artifacts/at_fg_03a/`, and the review under `handoff/history/at_fg_03a/`.

The [scoped source diff](../../artifacts/at_fg_03a/lifecycle-source.diff) compares tracked files to HEAD and the existing untracked runner to its inspected pre-edit text. Validation used the checkout's Python 3.12.0 and pytest 9.1.1 with bytecode writing disabled.

| Scope | Command / evidence | Result |
| --- | --- | --- |
| Established scene-scope worker | `python <scene runner> posture 0 --output-dir <fresh validation folder>` | 17 passed, 68 deselected. JUnit, partition metadata and the recorded production digests were published. |
| Focused existing regressions | `python -m pytest tests/test_current_scene_evidence_scope.py tests/test_atomic_character_save.py tests/test_at_opt_02_retreat_and_budget.py tests/test_review_handoff.py -p no:cacheprovider -q --tb=short` | 128 passed. One existing Starlette TestClient deprecation warning. |
| Deterministic lifecycle probes | `python artifacts/at_fg_03a/validate-lifecycle.py` | Six successful runs, two controlled assertion failures, one controlled interruption, overlapping runs for each owner and an exclusive-slot collision check. |
| Source diff check | `git --no-optional-locks diff --check -- pytest.ini tests/conftest.py docs/NEXT_SESSION.md` | Passed. Git emitted the existing LF-to-CRLF notice for the session file. |

The synthetic validator uses a bounded single test, explicit output routes, local fixtures, and subprocess handshakes. Two initial probe setups encountered collection errors from a synthetic node ID and a race from placing the probe input beneath a changing scratch directory. Both attempts were captured. The corrected validator uses pytest's relative node ID and an input under the milestone artifact directory. The established suite continued through the actual partition entry point throughout. No live model campaigns, full repository suite or historical replay republishing were required.

### Success, failure, repetition and overlap

For each producer, three clean runs created a unique workspace and collectively used 201 files. All six successful synthetic workspaces were absent at exit. The established posture partition also removed its own workspace after 17 selected identities passed with zero network attempts and stable production hashes. Its expected and observed identity sets match.

The controlled partition assertion failure wrote a JUnit failure, JSON with pytest status 1, and a diagnostic trace. The worker reported the paths and removed scratch. The controlled `KeyboardInterrupt` wrote its trace and reports with pytest status 2, returned worker status 1 and removed scratch. The standalone assertion failure returned status 1 and reported its retained 67-file workspace. The validation driver captured its JUnit and trace, measured the failed workspace, and removed that one probe-owned directory.

Both producers ran with two simultaneous workers. One completed and removed its scratch while the peer's sentinel and workspace remained readable. Both later disposed of their own successful roots. A duplicate worker targeting the same numbered partition evidence slot was rejected while the owner remained live. Concurrent use of identical explicitly supplied standalone bases remains caller-owned.

| Synthetic probe family | Successful runs | Failed runs | Interrupted runs | Workspaces created | Scratch files observed during tests | Scratch files at worker exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Scene-scope partition | 3 | 1 | 1 | 5 | 335 | 0 |
| Standalone pytest | 3 | 1 | 0 | 4 | 268 | 67 |
| Total | 6 | 2 | 1 | 9 | 603 | 67 |

The measurements count files present at the test checkpoint, including fixture copies. Transient individual files between checkpoints and established-suite peak size were not counted. Evidence copied into the persistent review inputs is linked from the [probe measurements](../../artifacts/at_fg_03a/probes/results.json).

## Storage before and after

Historical sizes are apparent file bytes. Allocated bytes for disposable synthetic workspaces are the per-file Windows allocation values, measured through file handles. These values exclude directory metadata. Published evidence is measured separately from scratch. No historical deletion or storage savings were authorized.

| Metric | Before | After |
| --- | ---: | ---: |
| Total `development/tmp/` apparent bytes | 12,599,909,312 | 12,599,909,312 |
| Total `development/tmp/` files | 3,374,014 | 3,374,014 |
| Scene-scope apparent storage | 3,490.13 MB from AT-FG-01 | 3,490,133,782 bytes |
| Scene-scope files | 998,452 | 998,452 |
| Scene-scope immediate roots | 999 | 999 |
| Synthetic workspace allocation at test checkpoint | 0 | 526,400 allocated bytes across 9 roots and 603 files |
| Synthetic scratch retained by producer at exit | 0 | 58,488 allocated bytes and 67 files from the one failed standalone session |
| Synthetic scratch retained after validation teardown | 0 | 0 directories, 0 files, 0 allocated bytes |
| Synthetic persistent diagnostic/JUnit/metadata payload | 0 | 23 files, 8,443 apparent bytes, 31,248 allocated bytes at the publication checkpoint |

The read-only total Robocopy census matched the earlier audit with zero enumeration failures. The live scene exact-byte attempt overlapped validation, so the before column uses the audit's rounded value. The after census used a single no-reparse traversal after all milestone scratch had been removed. Its total directory count including the root was 272,617, matching the before Robocopy enumeration. Matching totals and root counts do not establish a full-tree content comparison. The after census records reproducible metadata digests for future governance comparisons. [Baseline](../../artifacts/at_fg_03a/storage-before.json) · [After census](../../artifacts/at_fg_03a/storage-after.json)

Successful future runs of the repaired producers should retain zero disposable roots. Published per-partition XML, JSON and test-authored evidence still grow with intended evidence creation. Standalone failures and aborted publication retain the diagnostic data described above.

## Protected artifact verification

The protected-path check matched membership and SHA-256 for 20,389 files, including canonical `data/`, AT-OPT reports and artifacts, active PR-PLAY reports and evidence, current review files, the reconciled live-state store, and unrelated pre-existing tracked modifications. HEAD and the Git index digest matched. With the named task paths excluded, full porcelain status matched 34 unrelated modified paths, 51 missing tracked paths, and 322,713 untracked file records. The pre-existing `docs/NEXT_SESSION.md` modification is outside those 34 paths. Its scoped insertion preserved all pre-existing file bytes. Status snapshots are retained under the milestone artifact directory. [Integrity comparison](../../artifacts/at_fg_03a/integrity-comparison.json) · [Session note comparison](../../artifacts/at_fg_03a/session-note-integrity.json)

The lifecycle code only removes the unique path returned by that execution's allocator. No directory-wide cleanup, historical move, compression, pruning, or age policy ran. The canonical review generator was directed to fresh staging and published in this milestone's new canonical history location. The previously published stable Markdown, manifest and ZIP were preserved.

## Remaining risks and next milestone

Standalone failed sessions retain one entire workspace each. Repeated failures require review of those diagnostics. Forced termination and loss of the evidence destination can leave unique directories behind. Explicit bases remain at the discretion of the caller, and older PR-PLAY wrappers still create their own persistent scratch. The scene partition runner's normal output is campaign evidence. An arbitrary output under the protected `artifacts/` tree can encounter the existing test storage audit guard because numbered reports and the diagnostic directory are siblings. The validation copy into the milestone artifact directory occurs after the worker exits.

Recommend a separately authorized **AT-FG-03B** to migrate remaining explicit-base PR-PLAY wrappers and diagnose ATGB cleanup failures using fresh outputs. A separate historical inventory must map owners and evidence dependencies for the 12.60 GB backlog, including the 3.49 GB scene-scope area, before anyone proposes an exact cleanup allowlist. Stop here for review.
