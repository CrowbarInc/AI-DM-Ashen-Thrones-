# Cycle G Tracked Runtime Snapshot Churn Recon

Date: 2026-05-19

Scope: confirmation and churn documentation only. No production code or tests were changed for this recon.

## Full-Suite Result

Requested normal command:

```powershell
python -m pytest
```

In this Codex shell, `python` is not on `PATH`, so the command failed before pytest startup:

```text
python : The term 'python' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

Equivalent repo pytest invocation used for confirmation, preserving `pytest.ini` behavior including repo-local `--basetemp=codex_pytest_tmp`:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest
```

Result:

```text
4143 passed, 35 skipped in 59.18s
```

Raw output:

- `audits/cycle_g_block4_full_suite_confirmation_20260519.txt`

## Changed Tracked Runtime Files

After the successful full-suite run, `git status --short` showed these tracked runtime files as modified:

- `data/combat.json`
- `data/session.json`
- `data/session_log.jsonl`
- `data/world.json`

Observed diff shape:

- `data/combat.json`: `saved_at` timestamp changed.
- `data/session.json`: `saved_at`, `turn_counter`, `time_pressure`, scene/runtime/memory/debug fields, and persisted turn transcript/debug payload content changed.
- `data/session_log.jsonl`: appended one session-log row.
- `data/world.json`: faction `pressure` and `agenda_progress` values advanced.

The changed files were restored after capturing this audit evidence so runtime snapshot churn was not left in the worktree.

## Likely Test Source

No single exact source was proven in this block.

Best-effort guess: the churn is likely from full-suite tests that call `game.api.chat(...)` / campaign flow against default storage paths rather than fully isolated temp storage. The diff content includes a live-looking `"I look around."` chat turn on `old_milestone`, clock/world progression, and session log append. Candidate areas worth inspecting in a narrow follow-up include transcript/gauntlet and mixed-state recovery tests that import `chat` directly:

- `tests/test_transcript_gauntlet_campaign_cleanliness.py`
- `tests/test_mixed_state_recovery_regressions.py`
- any helper wrapping `game.api.chat` without `patch_transcript_storage(...)` or equivalent storage path isolation

This is a hygiene issue only; it did not affect suite pass/fail after Cycle G Blocks 1-3.

## Recommended Next Block

**Cycle G Block 5 — Runtime Snapshot Churn Isolation**

Scope summary: identify the specific test or helper that writes to committed `data/combat.json`, `data/session.json`, `data/session_log.jsonl`, and `data/world.json`; add the narrowest test-only storage isolation or cleanup fixture. Do not alter production persistence behavior and do not broad-refactor shared fixtures unless the culprit is a common helper.

## Closeout Note

Cycle G’s original failing-test goals are clean: the full suite is green. The only remaining risk is post-run worktree cleanliness from tracked runtime snapshot churn.
