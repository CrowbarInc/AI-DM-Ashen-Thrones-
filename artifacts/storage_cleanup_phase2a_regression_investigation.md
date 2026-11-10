# Ashen Thrones — Storage Cleanup Phase 2A Regression Investigation

Status: **investigation only.** No application code, test expectations, or fixtures were edited. No cleanup commit was created. Nothing was pushed. The staged deletions were not restored. Phase 2B was not started.

Date: October 31, 2026. Repository: `C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm`.

## 1. Executive summary

The three clarification failures are present on the original commit, with the historical pytest directories still on disk. The same three failures, with the same expected and actual lines, occur on the post-cleanup working tree. They do not read any directory removed in Phase 2A.

`test_targeted_reference_matrix` case T05 **passed** on both the original commit and the post-cleanup tree when given a fresh pytest temporary directory. The `PermissionError` reported in Phase 2A was not reproduced. That result is not a cleanup regression.

`artifacts/pr_eg_r4_r1/replay_state/data/session.json` is still the only unstaged tracked modification in the active tree. On the isolated baseline, `test_original_failure_frozen_production_finalization` rewrites that file. Two runs changed only `saved_at`, `payload.last_saved_at`, and `integrity.payload_sha256`. Every other field matches `HEAD`, and the active file matches that same stripped document. The timestamps are not deterministic. The rest of the document is.

Recommendation: **PASS WITH CAVEATS.** The staged deletion scope is not the cause of these results. A later commit may contain those deletions only. It must not include `session.json`. This investigation did not create that commit. C01–C03 remain failing tests. They are pre-existing, and they were not repaired.

| Test | Baseline | Post-cleanup | Classification | Confidence |
| --- | --- | --- | --- | --- |
| `test_independent_clarification_holdout[C01]` | Failed | Failed, same line | Pre-existing regression | High |
| `test_independent_clarification_holdout[C02]` | Failed | Failed, same line | Pre-existing regression | High |
| `test_independent_clarification_holdout[C03]` | Failed | Failed, same line | Pre-existing regression | High |
| `test_targeted_reference_matrix[T05-...]` | Passed | Passed | Environmental / test harness. Original `PermissionError` not reproduced | Medium for the original error's trigger; high that cleanup did not cause a T05 failure |

## 2. Original Git state

Checked before any worktree or test run, and again after the runs.

| Item | Observed |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `c16d922865b7182d47b87d27ec633f9308f1ef4c` |
| Tracking line | `feature/product-realization...origin/feature/product-realization` with no ahead/behind count |
| Staged deletions | 31,886 |
| Staged additions, modifications, or other non-deletions | 0 |
| Manifest paths missing from the staged deletion set | 0 |
| Staged paths missing from the manifest | 0 |
| Manifest logical bytes | 523,570,476 |
| Unstaged tracked file | `artifacts/pr_eg_r4_r1/replay_state/data/session.json` only |
| Untracked files preserved | the five storage-cleanup reports and the Phase 2A manifest listed in the Phase 2A report |

`git diff --cached --shortstat` remained `31886 files changed, 10552219 deletions(-)`.

The current working-tree SHA-256 of the unstaged session file, raw bytes, is `14d635e9944fd264ffc72198ca0967591706028ea0ca71aea70ada868566a30d` (817 bytes). It was the same after the post-cleanup test run. `HEAD` still has blob `340748fe9e0da555507bf7c81c2b83488a96d9d3`.

Git diff of that file, unchanged by this investigation:

```diff
-  "saved_at": "2026-10-18T16:34:22.613229Z",
+  "saved_at": "2026-10-31T20:54:32.536508Z",
-    "last_saved_at": "2026-10-18T16:34:22.613229Z",
+    "last_saved_at": "2026-10-31T20:54:32.536508Z",
-    "payload_sha256": "3c77d68a8a110114b537b457ba23c5437d6a829c95276e80ebe54001d6dd90e0",
+    "payload_sha256": "2935611bd3a747e38171a62f4404899e35600945c6b755caf72f0302ba54f131",
```

`canonicalization` stays `json/sort_keys,separators`. `hash` stays `sha256`. No other lines differ. The file was not restored.

This state matches the Phase 2A report. The investigation did not stop for a discrepancy.

## 3. Baseline worktree construction

A first `git worktree add` used a long path beside the project. Checkout reached the files and then failed:

`unable to create file artifacts/pr_eg_r6_r4_r1/focused_tmp/test_bundle_only_self_containe0/extracted/support/artifacts/validation_evidence/retrospective_playability/evidence_manifest.json: Filename too long`

That path is 165 characters. Combined with the long parent directory, it exceeded the classic Windows path limit. Git did not register the worktree. The partial directory was not present afterward. The active index was unchanged: 31,886 staged deletions, and the same unstaged session file.

The baseline that was used is a detached worktree:

`C:\p2a_c16d922`

Command: `git -c core.longpaths=true worktree add --detach C:\p2a_c16d922 c16d922865b7182d47b87d27ec633f9308f1ef4c`

`-c` applied to that command only. `git config --local --get core.longpaths` is unset. The active working tree was not checked out, reset, or switched.

| Check | Result |
| --- | --- |
| Commit | `c16d922865b7182d47b87d27ec633f9308f1ef4c` |
| Branch | detached HEAD |
| Tracked status before tests | clean |
| Tree entries | 75,403 |
| Manifest paths present as files | 31,886 of 31,886 |
| Manifest blob mismatches | 0 |
| Same paths still present in the active tree | 0 |
| Other worktrees | none. The active repo remained the only other worktree |

`core.autocrlf` is `true`. 6,037 checked-out files are larger on disk than the manifest's logical blob sizes. Sampled files whose sizes already matched the manifest also matched its SHA-256, including the long `evidence_manifest.json`. Git status was clean, and every manifest blob id matched `HEAD`. The size gap is CRLF expansion, not a copy of the deleted working tree.

Historical pytest directories are present, with the same file counts as the Phase 2A scope table:

| Directory | Files |
| --- | ---: |
| `artifacts/pr_eg_r4_r1/tmp_baseline` | 2,363 |
| `artifacts/pr_eg_r2c_r2/final_tmp` | 2,327 |
| `artifacts/pr_bt_selective_epistemic_guidance/pytest_basetemp` | 393 |
| `artifacts/pr_ck_resolver_selection/pytest_basetemp` | 88 |
| `artifacts/pr_eg_r2/pytest_local` | 261 |
| `artifacts/pr_cf_regression_triage/pytest_representative` | 8 |

## 4. Test environment and interpreter

Both runs used the active project's virtual environment. No environment was created. No package was installed or upgraded.

| Item | Value |
| --- | --- |
| Interpreter | `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\.venv\Scripts\python.exe` |
| Python | 3.12.0 |
| pytest | 9.1.1 |
| pluggy | 1.6.0 |
| plugin | anyio 4.14.2 |

Environment set for every run:

- `ASHEN_DISABLE_PROVIDER_CALLS=1`
- `ASHEN_DISABLE_LIVE_INTERPRETATION=1`
- `ASHEN_DISABLE_EXPRESSION_GENERATION=1`
- `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1`
- `ASHEN_PROVIDER_REQUEST_LIMIT=0`

`tests/conftest.py` also forces the live-interpretation and expression flags, and its autouse fixture installs the live-model guard.

A process-local socket guard was installed before pytest started. It allows `127.0.0.1`, `::1`, `localhost`, and empty bind addresses, so a Windows `socketpair` to loopback is allowed. Other `connect`, `connect_ex`, `create_connection`, and `getaddrinfo` targets raise. It does not block `socket.socket` construction. Every run recorded **0 blocked attempts**, which means the test process did not attempt a non-loopback connection. No provider call was made.

`pytest.ini` sets `--basetemp=development/tmp/pytest`. That option was overridden. Each run used its own directory outside both trees:

| Run | `--basetemp` | cwd |
| --- | --- | --- |
| Baseline four tests | `C:\p2a_pytest_baseline` | `C:\p2a_c16d922` |
| Post-cleanup four tests | `C:\p2a_pytest_postclean` | active repository |
| Baseline replay, first | `C:\p2a_pytest_replay1` | `C:\p2a_c16d922` |
| Baseline replay, second | `C:\p2a_pytest_replay2` | `C:\p2a_c16d922` |

The post-cleanup four tests were run in the active tree. On the baseline, those four tests left `git status` clean and did not change the hashes of `session.json`, the clarification fixtures, `game/conversational_continuity.py`, or `data/session.json`. The active-tree run left the pre-existing session hash unchanged. The test that writes the tracked replay session was not run in the active tree.

`game/conversational_continuity.py` SHA-256 is `b08b968c59d52cdc351e97209d73176a1c5e3f091f8fe413e2854088e474badd` in both trees.

## 5. Exact test selections

Module: `tests/test_pr_eg_r2c_r2_reference_eligibility.py`.

Node ids:

- `test_independent_clarification_holdout[C01]`
- `test_independent_clarification_holdout[C02]`
- `test_independent_clarification_holdout[C03]`
- `test_targeted_reference_matrix[T05-I ask Sergeant Mara about that place.-annotations4-sergeant_mara-ASK-remaining4]`

The T05 id is pytest's generated id. The parameters are `id='T05'`, question `I ask Sergeant Mara about that place.`, annotations `['that place']`, target `sergeant_mara`, operation `ASK`, remaining `['that place']`.

### C01–C03

Parameters come from `artifacts/pr_eg_r2c_r2/clarification_holdouts.json`. The test checks that file's SHA-256 against `artifacts/pr_eg_r2c_r2/clarification_freeze.json`. Those files were not in the deletion manifest. Both trees still have them. Holdout SHA-256 `060febf1918370228b1b30f5a398ffad5fe6059a17378c24a45275b575d9fe6b`. Freeze SHA-256 `9091b3bf9538a05e1aaea0196907e9805935038145cba810df2830e3920909f4`.

| Case | Question | Expected line |
| --- | --- | --- |
| C01 | Can you repeat that? | Which sailor do you mean: Fenn or Rook? |
| C02 | What did you mean by that? | Which library do you mean? |
| C03 | Say that again in simpler words. | Which tower are you asking about? |

There is no `tmp_path` fixture. The test builds an in-memory session: an NPC line, `Harbormaster Lis says, "The old quay is open."` (the name changes per case), then a GM-owned delivery of the expected clarification line. It sets `last_gm_exchange` to category `CLARIFY` in scene `harbor`, and `pending_clarification` to `ambiguous_addressee` / `pending`. It calls `continuity_directive` with `scene={'id': 'harbor'}` and `world={'npcs': []}`. It expects `action == 'clarify'`, `owner == 'gm'`, and `line` equal to the holdout line. It also expects the session object to be unchanged.

### T05

Fixture `scene` calls `seed_scene(tmp_path, monkeypatch)`, which calls `_patch_storage`. That redirects `storage.SESSION_PATH` and the other data paths under pytest's `tmp_path`. The test then reconciles the annotation `that place` and expects it to remain unresolved. It does not use `TestClient`.

The only `session.json` written by this case was under the external basetemp:

- `C:\p2a_pytest_baseline\test_targeted_reference_matrix0\data\session.json`
- `C:\p2a_pytest_postclean\test_targeted_reference_matrix0\data\session.json`

### Replay test, separate from the four

`tests/test_pr_eg_r4_r1_delivery_integrity.py::test_original_failure_frozen_production_finalization`

It accepts `tmp_path` and does not pass it anywhere. It calls `tools.qualify_pr_eg_r4_r1.replay('test_repaired_reproduction.json')`. `replay()` calls `seed_scene` on `artifacts/pr_eg_r4_r1/replay_state`, then `save_session`. `save_session` sets `last_saved_at` and rewrites the integrity hash. This is a tracked path. It is not one of the deleted pytest directories.

## 6. Baseline results

Cwd `C:\p2a_c16d922`. Wall time 1.772 seconds. Pytest reported 1.59 seconds. Exit code 1.

- C01 failed
- C02 failed
- C03 failed
- T05 passed

Tracked status afterward: clean. The hashes in section 4 did not change.

C01 actual line:

`Harbormaster Lis is not here, so I will not speak to Harbormaster Lis from this place. When you last spoke, Harbormaster Lis said: "The old quay is open." Nothing new has been established since that conversation. Do you want that recalled as it stands, or are you speaking to someone here?`

C02 and C03 are the same sentence with `Scholar Om` and `Sentry Nao`. `action` was already `clarify`. The assertion failed on `line`.

No exception. No `PermissionError`.

## 7. Post-cleanup results

Cwd: the active repository, with the 31,886 files absent. Wall time 3.329 seconds. Pytest reported 3.13 seconds. Exit code 1.

- C01 failed
- C02 failed
- C03 failed
- T05 passed

The failure text for the three cases matches the baseline text in section 6. The only summary difference is duration.

Hashes after the run, all unchanged from before it:

| File | SHA-256 |
| --- | --- |
| `artifacts/pr_eg_r4_r1/replay_state/data/session.json` | `14d635e9944fd264ffc72198ca0967591706028ea0ca71aea70ada868566a30d` |
| `artifacts/pr_eg_r2c_r2/clarification_holdouts.json` | `060febf1918370228b1b30f5a398ffad5fe6059a17378c24a45275b575d9fe6b` |
| `artifacts/pr_eg_r2c_r2/clarification_freeze.json` | `9091b3bf9538a05e1aaea0196907e9805935038145cba810df2830e3920909f4` |
| `game/conversational_continuity.py` | `b08b968c59d52cdc351e97209d73176a1c5e3f091f8fe413e2854088e474badd` |
| `data/session.json` | `91042e3b0d1c0fbc9f47b56be8d9468a61030658e5493338626a723a6882c2ef` |

`data/session.json` is not reported by `git diff`. A fresh checkout's raw hash differs (`2c0573b3...`) because `core.autocrlf` is true. That is line-ending bytes, and git does not treat the active file as modified.

## 8. Side-by-side comparison

| Question | Baseline fails? | Post-cleanup fails? | Messages identical? | Expected and actual identical across runs? | Environmental difference? | Reads a deleted directory? | Modifies tracked evidence? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | Yes | Yes | Yes | Yes. Expected holdout line. Actual absent-NPC line | No. Duration differed (1.59s vs 3.13s). Assertions did not | No | No |
| C02 | Yes | Yes | Yes | Yes | No | No | No |
| C03 | Yes | Yes | Yes | Yes | No | No | No |
| T05 | No, passed | No, passed | Both passed. No assertion diff | Not applicable. The expected remaining annotation is `['that place']`, and the test passed | The Phase 2A `PermissionError` did not recur with a fresh basetemp | No. Writes stayed in the external basetemp | No |

## 9. Root-cause assessment for C01–C03

Observed, not only inferred:

A read-only reconstruction imported `continuity_directive` from the baseline tree and built the same in-memory session the test builds. The session was not mutated. For each case the directive reason was `absent_npc_reference`. The returned line is the absent-NPC sentence above, which is the text of `_absent_line`.

`delivered_exchanges` contained two rows:

1. NPC row, speaker `speaker`, kept by `historical_disclosure_permitted`.
2. GM clarification row, `speaker_id` empty, ownership `gm`, **not kept**.

For the GM row, `is_host_operation` and `is_bounded_expression` were both false. The spoken text was the holdout line (`Which sailor do you mean: Fenn or Rook?`, and the C02/C03 equivalents). `_HOST_OPERATION_LINE` matches phrases such as `which statement` or `which person`. It does not match `which sailor`, `which library`, or `which tower`. `_BOUNDED_LINE` does not match them either. With an empty `speaker_id`, the other recall branch in `historical_disclosure_permitted` does not keep the row.

`continuity_directive` then sets `latest` from the filtered rows. `latest` is the NPC disclosure, not the GM clarification. The short-circuit that would repeat `last_gm_exchange.response` requires `latest.ownership == 'gm'` and `latest.delivered_text == last_gm_exchange.response`. That condition is false. The question still matches `_REPEAT` (C01, C03) or `_MEANING` (C02). The selected exchange is the earlier NPC line. The world has no NPCs, so the speaker is absent, and the function returns `_absent_line` with reason `absent_npc_reference`.

That code path is in the pre-cleanup tree. The continuity file hash matches the active tree. The holdout files were not deleted. The same failure occurs whether or not the 31,886 pytest files exist.

Classification: **pre-existing regression.** Confidence: **high.**

This investigation did not change `game/conversational_continuity.py` or the holdout files.

## 10. Root-cause assessment for T05

On a fresh basetemp, T05 passed in the original tree and in the post-cleanup tree. It did not raise. It did not leave a tracked diff.

Phase 2A reported a `PermissionError` while replacing `session.json` inside an isolated basetemp that a previous run had already used, and said that this was not a missing deleted store. This investigation did not find that traceback on disk under `development/tmp`, and it did not run again against that old directory. Pytest removes a reused `--basetemp` at session start, so pointing a new run at the old directory would have deleted Phase 2A scratch. That was not done.

What was observed is narrower: with a new temporary directory, T05 passes on both repository states. The original `PermissionError` was not reproduced here. Nothing in the result depends on a removed directory. `seed_scene` writes the session only after `_patch_storage` points `SESSION_PATH` at `tmp_path`.

Classification: **environmental / test harness.** Confidence that cleanup introduced a T05 failure: **low; the fresh runs contradict that.** Confidence in the precise original trigger (directory reuse versus a transient Windows file lock): **medium**, because this investigation did not recreate the `PermissionError`.

## 11. Session.json mutation investigation

The active file was not restored and was not overwritten.

On the baseline only, `test_original_failure_frozen_production_finalization` was run twice.

| Run | Exit | Seconds | `saved_at` and `last_saved_at` | `payload_sha256` |
| --- | --- | ---: | --- | --- |
| HEAD | — | — | `2026-10-18T16:34:22.613229Z` | `3c77d68a8a110114b537b457ba23c5437d6a829c95276e80ebe54001d6dd90e0` |
| Active tree, left untouched | — | — | `2026-10-31T20:54:32.536508Z` | `2935611bd3a747e38171a62f4404899e35600945c6b755caf72f0302ba54f131` |
| Baseline run 1 | 0 | 1.770 | `2026-10-31T21:08:34.650742Z` | `9f5289a761d160225693b8fe22ab4edf2cd04def1e33891ecbbcdd9b2b2322c4` |
| Baseline run 2 | 0 | 1.732 | `2026-10-31T21:09:22.840473Z` | `4fc5428b0c7366b575a53de93f7240866062cf33d7888e729eca83f031fde130` |

After stripping `saved_at`, `payload.last_saved_at`, and `integrity.payload_sha256`, HEAD, both baseline runs, and the active file are equal. The two runs do not share a timestamp. The test passed both times. A hash walk of `artifacts/pr_eg_r4_r1/replay_state` and `test_repaired_reproduction.json` showed only `replay_state/data/session.json` changed. `git diff --stat` was `1 file changed, 3 insertions(+), 3 deletions(-)`.

Answers:

1. Yes. At the pre-cleanup commit, this test modifies `artifacts/pr_eg_r4_r1/replay_state/data/session.json`.
2. The timestamps and the integrity hash are not deterministic. Every other field is stable across two runs and matches HEAD.
3. Yes. The diff is those two timestamps and `payload_sha256`.
4. No other session fields changed.
5. Yes. The behavior is on commit `c16d922`, with the deleted directories still present. It predates Phase 2A.
6. Not with the current test. `tmp_path` is unused. `replay()` always seeds `artifacts/pr_eg_r4_r1/replay_state`. An isolated data directory would require a change to that test or to `replay()`, which was not made.

The active modification is the same shape as these test runs: same three fields, same stripped document, timestamp `2026-10-31T20:54:32.536508Z` from the earlier Phase 2A validation. That is test output, not a separate edit to scene, inventory, flags, or campaign progress.

Safe resolution, not performed: from the active repository, restore only the worktree copy of that one path, for example `git restore --worktree -- artifacts/pr_eg_r4_r1/replay_state/data/session.json`. That does not unstage the 31,886 deletions. Do not use `git reset --hard`. Do not stage this file into the cleanup commit. If there is any doubt that the 20:54:32 timestamp was intentional, leave the file unstaged and out of the commit. The evidence here supports treating it as disposable test output.

The baseline worktree now contains run 2's session file. That dirty state was kept. See section 13.

## 12. Deleted-file dependency findings

None of the four tests read a Phase 2A directory.

- C01–C03 fail the same way when those directories exist and when they do not. A missing input would have been `FileNotFoundError`, not the same assertion.
- Their inputs are the in-memory session plus the two clarification JSON files, which are still in both trees.
- T05 passed without the deleted directories. Its session write was under `C:\p2a_pytest_postclean`, not under `artifacts/`.
- Searches of `tests/` for the removed directory names hit the clarification fixture load, not a pytest basetemp path.
- `replay()` writes `artifacts/pr_eg_r4_r1/replay_state`. That directory was not in the deletion scope. The qualification helper's `--basetemp=artifacts/pr_eg_r4_r1/tmp_{label}` path is in `regression()`, which this test does not call.

`game/`, `tests/`, `tools/`, `data/`, `experiments/`, `scripts/`, and `docs/` have no unstaged diff in the active repository.

## 13. Preservation verification

Active repository after the investigation:

| Check | Result |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `c16d922865b7182d47b87d27ec633f9308f1ef4c` |
| Staged deletions | 31,886 |
| Other staged changes | none |
| Unstaged tracked file | `artifacts/pr_eg_r4_r1/replay_state/data/session.json` only |
| That file's SHA-256 | `14d635e9944fd264ffc72198ca0967591706028ea0ca71aea70ada868566a30d` |
| That file's timestamp | `2026-10-31T20:54:32.536508Z` |
| Application source, ATGB baselines, golden replay fixtures, PR-PLAY evidence, canonical `data/` | no tracked diff |
| Untracked audit reports and manifest | still untracked, not staged |
| Commit | none created |
| Push | none |
| Provider calls | none. Socket guard recorded 0 non-loopback attempts |
| `git config` | not modified |

The comparison worktree `C:\p2a_c16d922` is dirty in one tracked file, `artifacts/pr_eg_r4_r1/replay_state/data/session.json`, from the second baseline replay. It was not force-removed. No other tracked path there is modified. Git garbage collection was not run.

External scratch, outside the repository: `C:\p2a_inv\` (logs and the two baseline session copies) and `C:\p2a_pytest_baseline`, `C:\p2a_pytest_postclean`, `C:\p2a_pytest_replay1`, `C:\p2a_pytest_replay2`.

Ignored `.pytest_cache/` in the active tree may have been updated by the post-cleanup pytest process. It is not tracked.

## 14. Outstanding risks

- C01–C03 fail on current source. Repairing `continuity_directive` or the holdout expectation is out of scope for storage cleanup. A cleanup commit does not make those tests pass.
- The full 193-test Phase 2A selection was not re-run. Only the four reported failures, plus the one replay test on the baseline, were executed.
- T05's original `PermissionError` was not recreated. A later suite that reuses `development/tmp/phase2a_pytest` or `development/tmp/pytest` could hit a Windows file-lock or basetemp-reuse error again. That is independent of the deleted trees.
- `test_original_failure_frozen_production_finalization` will dirty `replay_state/data/session.json` whenever it runs in a checkout. A cleanup commit should not pick up that dirt.
- Phase 2A already noted that `artifacts/pr_eg_r5/baseline.json` hashes include `tmp_*` paths, and that those verification scripts are already stale against `game/`, `data/`, and `tests/`. Those scripts were not run.

## 15. Cleanup authorization recommendation

**PASS WITH CAVEATS.**

The staged deletions are not responsible for C01–C03 or for a T05 failure. No deleted file is required by these tests. The deletion set remains the Phase 2A manifest: 31,886 files, 523,570,476 logical bytes, and nothing else staged.

Caveats that must travel with any later commit:

- C01–C03 are pre-existing failures. Do not describe the suite as green.
- Do not stage or commit `artifacts/pr_eg_r4_r1/replay_state/data/session.json`.
- Do not treat an unreproduced T05 `PermissionError` as evidence that a removed directory is required.
- Do not repair conversational continuity as part of this cleanup.

This investigation does not authorize an automatic commit. No commit was created.

## Per-test record

### C01

- Baseline: failed. Actual line is the Harbormaster Lis absent-NPC sentence. Reason `absent_npc_reference`.
- Post-cleanup: failed with the same expected and actual lines.
- Classification: pre-existing regression.
- Confidence: high.

### C02

- Baseline: failed. Actual line is the Scholar Om absent-NPC sentence. Reason `absent_npc_reference`.
- Post-cleanup: failed with the same lines.
- Classification: pre-existing regression.
- Confidence: high.

### C03

- Baseline: failed. Actual line is the Sentry Nao absent-NPC sentence. Reason `absent_npc_reference`.
- Post-cleanup: failed with the same lines.
- Classification: pre-existing regression.
- Confidence: high.

### T05

- Baseline: passed in `C:\p2a_pytest_baseline`.
- Post-cleanup: passed in `C:\p2a_pytest_postclean`.
- Relevant failure details: no failure in these runs. Phase 2A's `PermissionError` was not reproduced.
- Classification: environmental / test harness.
- Confidence: high that both repository states pass on a fresh temporary directory. Medium that directory reuse was the original trigger, because that error was not recreated here.
