"""Package the PR-PLAY-34 readiness evidence. Does not launch a worker."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
READINESS = ROOT / 'artifacts' / 'atgb' / 'pr_play_34' / 'readiness'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def write(name, body):
    (OUT / name).write_text(body.strip() + '\n', encoding='utf-8')


def case(letter):
    return json.loads((OUT / 'controls' / f'{letter}.json').read_text(encoding='utf-8'))


def main():
    summary = load('readiness_summary.json')
    controls = {row['control']: row for row in summary['controls']}
    suite = ET.parse(OUT / 'regression.xml').getroot().find('testsuite')
    counts = {key: int(suite.attrib[key]) for key in ('tests', 'failures', 'errors', 'skipped')}
    assert counts['failures'] == counts['errors'] == counts['skipped'] == 0
    assert counts['tests'] == 30
    a, c, d, e, f = (case(letter) for letter in 'ACDEF')
    live_a = a['observation']['live']
    live_e = e['observation']['live']
    child = live_a['children'][0]
    repaired = OUT.parent / 'pr_play_33' / 'source' / 'tools' / 'playtest' / 'runner.py'
    assert sha(ROOT / 'tools' / 'playtest' / 'runner.py') == sha(repaired)
    baseline = json.loads((OUT.parent / 'pr_play_33' / 'baseline_hashes.json').read_text(encoding='utf-8'))
    watched = [rel for rel in baseline if rel.startswith('game/') or rel.startswith('tools/playtest/')]
    drifted = [rel for rel in watched if rel != 'tools/playtest/runner.py'
               and sha(ROOT / rel) != baseline[rel]]
    assert not drifted, drifted
    status = subprocess.check_output(['git', 'status', '--short', '--', 'game', 'tools/playtest'], cwd=ROOT, text=True)
    (OUT / 'preexisting_worktree_status.txt').write_text(status, encoding='utf-8')
    results = summary['control_results']
    assert results == {'A': 'PASS', 'B': 'PASS', 'G': 'PASS', 'C': 'PASS', 'D': 'PASS', 'E': 'PASS', 'F': 'PASS'}
    assert summary['provider_requests'] == 0 and summary['gameplay_turns'] == 0
    assert summary['user_campaign_changed'] is False
    session = a['observation']['session_after']
    before = a['observation']['session_before']
    command = ('.venv/Scripts/python.exe -m pytest tests/test_pr_play_33_process_ownership.py '
               'tests/test_playtest_startup_readiness.py tests/test_pr_play_34_readiness_diagnostics.py '
               '--basetemp=development/tmp/pr_play_34_process --junitxml=artifacts/pr_play_34/regression.xml -ra')
    write('PR_PLAY_34_EXECUTIVE_SUMMARY.md', f'''# PR-PLAY-34 — Offline harness readiness

**Verdict: A — PASS.** The harness is ready for a separately authorized live experiment. PR-PLAY-35 was not started.

PR-PLAY-33 repaired Windows launcher indirection and reached HTTP 200, then stopped. Two diagnostic assertions remained unresolved: an unlabeled `AssertionError` inside the readiness wrapper, and an outer requirement that `session.json` be absent.

This task inspected that run without changing the process-launch repair. The unlabeled failure is the wrapper's zero-child assert. Re-measurement shows the worker's only child is `conhost.exe`. Controller pid, Popen pid, and worker-reported pid agree, and the worker image is the base interpreter. The session-file assert was an incorrect expectation: `GET /api/state` creates a bootstrap session with `campaign_started` false and `turn_counter` 0.

The diagnostic now records each condition separately, writes that record before cleanup, and accepts a bootstrap session while still failing a started campaign, a nonzero turn, gameplay activity, or a provider dispatch. Controls A through G passed on isolated stores. Provider requests and gameplay turns are 0. No gameplay or provider implementation file changed.
''')
    write('PR_PLAY_34_DIAGNOSTIC_ASSERTION.md', f'''# Diagnostic assertion report

## Original failure

`artifacts/pr_play_33/readiness_output.txt` ends at `readiness.py` line 76:

`assert not (run/'data/session.json').exists()`

`reports/result.json` for run `20261102T004939Z-7d36523024d3` records a second, earlier failure: `AssertionError` at stage `application_startup_failure`. That stage is still set while the diagnostic's replacement for `wait_for_http_ready` is running. The wrapper's five asserts had no identifiers, and the process table was not saved. The HTTP poll had already recorded status 200, so the request guard had passed. `ready.json` shows three of the five asserts would have passed: pid 35756 matched, isolation and diagnostics were true, and both retry counts were 0. The two asserts that needed the process table were parent equality and zero children.

## Identified cause

The same wrapper conditions were measured again, separately, on control A before cleanup:

| Identifier | Result | Observed |
| --- | --- | --- |
| H1 ready pid equals Popen pid | PASS | 32792 = 32792 |
| H2 parent equals controller | PASS | 26144 = 26144 |
| H3 worker has no children | FAIL, not a harness gate | one child, `{child['image']}` pid {child['pid']} |
| H4 isolation and diagnostics | PASS | both true |
| H5 retries | PASS | 0 and 0 |

H3 is the assert that raises. `conhost.exe` is a Windows console host, not a second interpreter. The base-interpreter launch from PR-PLAY-33 is intact. Treating every child as a startup failure was an incorrect diagnostic assumption. An interpreter descendant remains a gating failure.

The session assert failed because `load_session` creates `session.json` when `compose_state` serves `GET /api/state`. The saved PR-PLAY-33 session had `turn_counter` 0 and `campaign_started` false. That behavior was left unchanged.

## Correction

`artifacts/pr_play_34/evaluate.py` scores each condition by identifier and records expected value, observed value, evidence, and whether cleanup succeeded. The snapshot is written to `diagnostics/readiness_snapshot.json` before the controller's cleanup. A bootstrap file is allowed. A started campaign, nonzero turn, chat or log activity, gameplay trace, or provider dispatch fails.
''')
    write('PR_PLAY_34_PROCESS_OWNERSHIP.md', f'''# Process ownership

Control A, module worker, captured before cleanup.

| Field | Value |
| --- | --- |
| Controller pid | {live_a['controller_pid']} |
| Controller image | `{live_a['controller_executable']}` |
| Controller created | {live_a['controller_created_utc']} |
| Popen / worker pid | {live_a['popen_pid']} |
| Worker-reported pid | {live_a['reported_pid']} |
| Parent pid | {live_a['parent_pid']} |
| Worker image | `{live_a['worker_executable']}` |
| Base interpreter | `{live_a['base_executable']}` |
| Worker created | {live_a['worker_created_utc']} |
| Child | `{child['image']}` pid {child['pid']}, created {child['created_utc']} |
| Launch | `{' '.join(live_a['launch_command'])}` |
| HTTP | {a['observation']['http_status']} in {a['observation']['startup_seconds']} seconds |
| Shutdown | owned pid {a['observation']['process_cleanup']['pid']}, stopped, exit {a['observation']['process_cleanup']['exit_code']}, {a['observation']['process_cleanup']['shutdown_seconds']} seconds |
| Orphans after cleanup | none |
| Port released | {a['observation']['port_released']} |

Exit code 1 is the controller's owned-handle terminate, which is the harness shutdown action. The controller observed the exit. No orphan remained.

Control E, observer `artifacts/pr_play_32/worker_capture.py`: controller {live_e['controller_pid']}, worker {live_e['popen_pid']}, parent {live_e['parent_pid']}, reported {live_e['reported_pid']}, image `{live_e['worker_executable']}`. HTTP {e['observation']['http_status']} in {e['observation']['startup_seconds']} seconds. Cleanup stopped pid {e['observation']['process_cleanup']['pid']}. Orphans: none.

Control D timed out at {d['observation']['poll_events'][-1]['elapsed_seconds']} seconds against a 0.4 second deadline and then stopped pid {d['observation']['process_cleanup']['pid']}. Control C's worker exited on its own with code {c['observation']['process_cleanup']['exit_code']} before readiness. Control F's worker pid {f['observation']['process_cleanup']['pid']} was the cleaned-up pid; the port holder pid {f['observation']['holder']['pid']} was still alive and still bound to port {f['observation']['holder']['port']}. The holder was a process this diagnostic spawned with the base interpreter, and it was terminated only after that check.
''')
    matrix = '\n'.join(
        f"| {row['control']} | {row['result']} | `{row['run']}` |" for row in summary['controls'])
    write('PR_PLAY_34_CONTROL_MATRIX.md', f'''# Readiness control matrix

| Control | Result | Evidence |
| --- | --- | --- |
{matrix}

| Gate | Result |
| --- | --- |
| Process ownership | PASS |
| Normal startup | PASS |
| HTTP readiness | PASS |
| Normal shutdown | PASS |
| Startup failure cleanup | PASS |
| Timeout cleanup | PASS |
| Observer worker | PASS |
| Occupied-port protection | PASS |
| Bootstrap state integrity | PASS |
| Provider requests | 0 |
| Live gameplay turns | 0 |
| Gameplay code modifications | 0 |
| Relevant regression tests | PASS |

Observer startup is supported through `runner.start_worker(script=...)` and was executed. It is not "not applicable."

Startup failure (C) removed the existing retry-suppression environment flags so the real worker refused to become ready at stage `{c['observation']['worker_failure']['stage']}` (`{c['observation']['worker_failure']['type']}`). No HTTP readiness file was written. Verdict `{c['observation']['verdict']}`.

Timeout (D) used `startup_timeout=0.4`. The poll records `readiness_deadline_expired`. Verdict `{d['observation']['verdict']}`.

Occupied port (F) records stage `{f['observation']['worker_failure']['stage']}` and OS error {f['observation']['worker_failure']['os_error']}. The unrelated holder was not terminated by the harness. The worker image query was empty because that process had already exited; its launch command is the base interpreter.
''')
    write('PR_PLAY_34_BOOTSTRAP_SESSION.md', f'''# Bootstrap session

Control A, isolated store `{a['run']}/data`.

| Observation | Before `GET /api/state` | After `GET /api/state` |
| --- | --- | --- |
| `session.json` exists | {before.get('exists')} | {session.get('exists')} |
| Inside isolated store | — | {session.get('inside_isolated_store')} |
| `campaign_started` | — | {session.get('campaign_started')} |
| `turn_counter` | — | {session.get('turn_counter')} |
| Chat history entries | — | {session.get('chat_history_len')} |
| Session log entries | — | {session.get('log_entries')} |
| Last action debug | — | {session.get('last_action_debug')} |
| Debug trace operations | — | {', '.join(row.get('operation') for row in session.get('debug_traces') or []) or 'none'} |

Gameplay initialization did not occur. The trace `rebuild_active_scene_entities` is recorded and is compose-time scene bookkeeping, not a turn. HTTP requests: {a['observation']['http_requests']}. Provider events: {[row.get('event') for row in a['observation']['provider_events']]}. Scenario steps: {a['observation']['steps']}.

The same unstarted result was observed for the observer worker. Failure, timeout, and occupied-port runs did not create `session.json`.
''')
    write('PR_PLAY_34_REGRESSION.md', f'''# Regression results

Dedicated assertion run, before the readiness controls:

` .venv/Scripts/python.exe -m pytest tests/test_pr_play_34_readiness_diagnostics.py --basetemp=development/tmp/pr_play_34_assert -q --tb=short `

Result: **6 passed**, 0 failed, 0 skipped. No retries.

Focused suite, after the readiness controls:

`{command}`

Result: **{counts['tests']} passed**, {counts['failures']} failed, {counts['errors']} errors, {counts['skipped']} skipped, time {suite.attrib['time']} seconds. No retries. No environment-specific failures. No test was converted to a skip. JUnit: `regression.xml`.

The 30 tests are the 24 PR-PLAY-33 ownership and startup tests plus 6 diagnostics tests for the corrected bootstrap and assertion rules. Gameplay suites were not added.
''')
    write('PR_PLAY_34_CHANGE_MANIFEST.md', '''# Change manifest

No existing gameplay, campaign-generation, narrative-generation, or provider-routing file was modified. `tools/playtest/runner.py` matches the PR-PLAY-33 repaired snapshot byte for byte. Every other `game/` and `tools/playtest/` file matches the PR-PLAY-33 pre-repair hash baseline. Git still shows those paths dirty against HEAD; that dirtiness predates this task and is listed in `preexisting_worktree_status.txt`.

New files:

- `artifacts/pr_play_34/PR_PLAY_34_INSPECTION.md` — phase-1 inspection of the preserved PR-PLAY-33 failure.
- `artifacts/pr_play_34/evaluate.py` — identified assertions. Bootstrap session existence is not a failure; campaign start, turns, gameplay, and provider dispatch are.
- `artifacts/pr_play_34/readiness.py` — offline controls A–G. Writes the process snapshot before controller cleanup. Does not change the shared launcher.
- `artifacts/pr_play_34/package_review.py` — this archive builder. It does not launch a worker.
- `tests/test_pr_play_34_readiness_diagnostics.py` — regression coverage for those assertion rules.
- `artifacts/pr_play_34/controls/` and `artifacts/atgb/pr_play_34/readiness/` — captured control evidence.
- Review reports, `regression.xml`, and `readiness_summary.json`.

The PR-PLAY-33 diagnostic and its failed run were left in place.
''')
    write('PR_PLAY_34_PROVIDER_USAGE.md', f'''# Provider usage

- Provider requests: **{summary['provider_requests']}**.
- Provider tokens: **{summary['provider_tokens']}**.
- Live gameplay turns: **{summary['gameplay_turns']}**.

Successful startups recorded a single `initialized` accounting event and `dispatched_requests` 0. Failure, timeout, and occupied-port runs did not dispatch. The user's campaign fingerprint was unchanged (`user_campaign_changed` {str(summary['user_campaign_changed']).lower()}). No live mode and no campaign, start, or chat POST.
''')
    write('PR_PLAY_34_REMAINING_RISKS.md', '''# Remaining risks

No readiness blocker remains.

Informational:

- Windows attaches `conhost.exe` as a child of the worker. Owned-process termination reaped it. A diagnostic that requires zero children will fail again for that reason.
- The controller's own scenario verdict stays `INCONCLUSIVE` when readiness stops the run before actions, and `BLOCKED` when startup really fails. `INCONCLUSIVE` here means the action loop was not entered.
- Shutdown is terminate on the owned process handle, exit code 1. That is the existing harness action.
- The occupied-port worker exits before a live image query. The launch command still names the base interpreter.
- This pass does not measure live narrative quality or multi-turn state coherence. Those belong to a separate live experiment.
''')
    write('PR_PLAY_34_FINAL_VERDICT.md', '''# PR-PLAY-34 final verdict

**A — PASS.**

Process ownership, startup, HTTP readiness, shutdown, startup-failure cleanup, timeout cleanup, observer startup, occupied-port protection, and bootstrap integrity passed. Provider requests, provider tokens, and gameplay turns are 0. Gameplay and provider implementation files were not modified. The focused regression suite passed 30 tests with no skips and no retries.

The harness is ready for a separately authorized live experiment. PR-PLAY-35 — Five-Turn Live Gameplay Validation — is the appropriate next experiment. It was not executed.
''')
    from dotenv import dotenv_values
    env = {**dotenv_values(ROOT / '.env'), **os.environ}
    hidden = [value.encode() for key, value in env.items() if isinstance(value, str) and len(value) > 8
              and any(part in key.lower() for part in ('key', 'token', 'secret', 'password', 'credential'))]
    excluded = {'archive_path.txt', 'archive_verification.json', 'MANIFEST.json', 'credential_scan.json'}
    included = [path for path in OUT.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.name not in excluded]
    included.append(ROOT / 'tests' / 'test_pr_play_34_readiness_diagnostics.py')
    included.extend(path for path in READINESS.rglob('*') if path.is_file() and path.suffix != '.zip' and '__pycache__' not in path.parts)
    hits = [str(path.relative_to(ROOT)) for path in included if any(secret in path.read_bytes() for secret in hidden)]
    (OUT / 'credential_scan.json').write_text(json.dumps({
        'files_scanned': len(included), 'credential_hits': hits, 'passed': not hits}, indent=2) + '\n', encoding='utf-8')
    assert not hits
    included.append(OUT / 'credential_scan.json')

    def arcname(path):
        if path.is_relative_to(READINESS):
            return 'evidence/readiness/' + path.relative_to(READINESS).as_posix()
        if path.is_relative_to(OUT):
            return path.relative_to(OUT).as_posix()
        return path.relative_to(ROOT).as_posix()

    manifest = {arcname(path): {'bytes': path.stat().st_size, 'sha256': sha(path)} for path in included}
    (OUT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    included.append(OUT / 'MANIFEST.json')
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT / 'handoff' / f'CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as bundle:
        for path in included:
            bundle.write(path, arcname(path))
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        stored = json.loads(bundle.read('MANIFEST.json'))
        assert all(hashlib.sha256(bundle.read(name)).hexdigest() == row['sha256'] for name, row in stored.items())
    (OUT / 'archive_verification.json').write_text(json.dumps({
        'path': str(archive), 'entries': len(included), 'bytes': archive.stat().st_size,
        'sha256': sha(archive), 'testzip': None, 'manifest_hashes_verified': True,
        'verdict': 'A — PASS'}, indent=2) + '\n', encoding='utf-8')
    (OUT / 'archive_path.txt').write_text(str(archive) + '\n', encoding='utf-8')
    print(json.dumps({'archive': str(archive), 'verdict': 'A — PASS', 'tests': counts['tests'],
                      'provider_requests': 0, 'gameplay_turns': 0}))


if __name__ == '__main__':
    main()
