"""Package PR-PLAY-33 observations without launching a worker or provider."""
from datetime import datetime, timedelta, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from investigate import processes, hashes, save

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def report(name, body):
    (OUT/f'PR_PLAY_33_{name}.md').write_text(body.strip()+'\n', encoding='utf-8')

def main():
    runs = list((ROOT/'artifacts/atgb/pr_play_33/readiness').iterdir())
    assert len(runs) == 1, 'No readiness retry authorized after failure'
    run = runs[0]
    ready = json.loads((run/'diagnostics/ready.json').read_text())
    result = json.loads((run/'reports/result.json').read_text())
    usage = json.loads((run/'diagnostics/budget_snapshot.json').read_text())
    session = json.loads((run/'data/session.json').read_text())['payload']
    table = processes()
    owned = ready['pid']
    remaining = [r for r in table.values() if r['pid'] == owned or r['parent_pid'] == owned]
    assert not remaining and result['process_cleanup']['stopped']
    with socket.socket() as probe:
        probe.settimeout(1)
        assert probe.connect_ex(('127.0.0.1', ready['port'])) != 0
    with socket.socket() as released:
        released.bind(('127.0.0.1', ready['port']))
    assert usage['dispatched_requests'] == usage['total_tokens'] == 0
    assert not result['steps'] and session['turn_counter'] == 0 and not session.get('campaign_started')
    save('readiness_failure_analysis.json', dict(
        readiness_attempts=1, retries=0, controller_started=True, worker_started=True,
        pid=owned, ownership_verified=True, isolation_verified=ready['isolation_verified'],
        http_status=200, startup_seconds=json.loads((run/'diagnostics/http_ready.json').read_text())['startup_seconds'],
        cleanup=result['process_cleanup'], remaining_owned_processes=remaining, port_released=True,
        campaign_post_requests=0, gameplay_turns=session['turn_counter'], campaign_started=False,
        bootstrap_session_created=True, provider_requests=usage['dispatched_requests'],
        provider_tokens=usage['total_tokens'], readiness_diagnostic_pass=False,
        controller_failure=result['failure'], controller_verdict=result['verdict'],
        failure='Controller caught AssertionError in diagnostic wait wrapper after successful HTTP readiness; exact assertion unavailable because snapshot was not persisted. Outer diagnostic then asserted session.json absence, but bootstrap session is present at turn zero.',
        unrun=['observer-worker readiness', 'occupied-port failure cleanup for module worker', 'occupied-port failure cleanup for observer worker'],
        verdict='B — PARTIAL', instruction='Stop honored: no readiness rerun; no live gameplay.'))
    baseline = json.loads((OUT/'baseline_hashes.json').read_text())
    after = hashes()
    changed = [p for p, h in baseline.items() if after.get(p) != h]
    assert set(changed) == {'tools/playtest/runner.py', 'artifacts/pr_play_32/execute.py'}, changed
    assert not any(p.startswith('game/') for p in changed)
    save('source_integrity.json', dict(baseline_files=len(baseline), changed_existing_files=changed,
        gameplay_code_unchanged=True, prior_evidence_other_than_repaired_controller_unchanged=True,
        original_controller_preserved='evidence_before/execute_pr_play_32.py',
        original_controller_sha256=sha(OUT/'evidence_before/execute_pr_play_32.py'),
        original_matches_baseline=sha(OUT/'evidence_before/execute_pr_play_32.py') == baseline['artifacts/pr_play_32/execute.py']))
    assert sha(OUT/'evidence_before/execute_pr_play_32.py') == baseline['artifacts/pr_play_32/execute.py']
    suite = ET.parse(OUT/'process_tests.xml').getroot().find('testsuite')
    assert int(suite.attrib['failures']) == int(suite.attrib['errors']) == 0
    save('test_summary.json', dict(command='.venv/Scripts/python.exe -m pytest tests/test_pr_play_33_process_ownership.py tests/test_playtest_startup_readiness.py --basetemp=development/tmp/pr_play_33_process --junitxml=artifacts/pr_play_33/process_tests.xml -ra',
        tests=int(suite.attrib['tests']), failures=0, errors=0, skipped=int(suite.attrib['skipped']),
        initial_result='24 passed', retries=0, environment_failures=0,
        reproduction_command='.venv/Scripts/python.exe artifacts/pr_play_33/investigate.py',
        reproduction_cases=4, reproduction_failures=0,
        readiness_command='.venv/Scripts/python.exe artifacts/pr_play_33/readiness.py',
        readiness_initial_exit_code=1, readiness_attempts=1, readiness_retries=0,
        readiness_failure='Controller caught post-readiness diagnostic AssertionError (exact assertion unresolved), then outer diagnostic required session.json absence',
        readiness_cases_completed=0, readiness_cases_unrun=3,
        provider_requests=0, input_tokens=0, output_tokens=0, total_tokens=0, live_gameplay_turns=0))
    report('EXECUTIVE_SUMMARY', '''# PR-PLAY-33 — Harness process ownership investigation and repair

**Verdict: B — PARTIAL. Root cause classification: A — Windows virtual-environment process indirection.**

Toolhelp32 process snapshots establish that the same .venv Python used by PR-PLAY-32 spawns an interpreter child. Popen owns the redirector, while os.getpid() reports the child. The direct base interpreter has no intermediate worker process. The controller and worker PID APIs were correct; the strict guard correctly refused the launch topology.

Repair: extract the existing shared controller's base-interpreter launch policy into runner.start_worker; route both the shared runner and PR-PLAY-32 observer controller through it. Preserve package visibility, environment safety settings, strict PID/path/isolation attestation, deadlines and existing handle-based cleanup. Fail before spawning when the expected interpreter is unavailable. No gameplay, campaign initialization or provider routing code changed.

24 focused offline tests passed, no failures, errors, skips or retries. Four stdlib-only process reproductions passed. The first actual harness readiness attempt reached HTTP 200 with matching PID and isolation, then the controller caught an AssertionError in the diagnostic wait wrapper and cleaned up with zero provider usage. The wrapper did not persist its native snapshot, so its exact failed assertion is unresolved. The outer diagnostic then failed because it incorrectly required session.json to be absent; GET /api/state leaves a bootstrap session at turn zero with campaign_started false. Per mission instructions the harness was stopped without a readiness retry. Observer-worker readiness and occupied-port cleanup controls were not executed. Full readiness is therefore NOT certified.

Provider requests: 0. Input/output/total provider tokens: 0/0/0. Live gameplay turns: 0. Campaign initialization/start/chat POSTs: 0. Bootstrap state loading did occur in the isolated readiness store. No live experiment, credentials-required launch or next PR initiated. Await review.''')
    report('ROOT_CAUSE', '''# Evidence reconstruction and root cause

Phase 1 was read-only for existing code. Sources inspected: PR-PLAY-31 final verdict, test history and manifest; PR-PLAY-32 execute.py, worker_capture.py, readiness_poll.jsonl, ready.json, cleanup verification, failure analysis and preflight logs; PR-PLAY-29 execute_validation.py and shared runner/worker; existing startup tests and isolation guards. PR-PLAY-31 repaired purpose routing and explicitly retained seven historical test failures; it did not introduce process-launch machinery. PR-PLAY-32's focused suite initially had one WinError 5 setup error, then its isolated recheck passed. Those historical outcomes are not counted as PR-PLAY-33 tests.

PR-PLAY-29 execute_validation.py lines 52–53 and 122 selected sys._base_executable and included repository plus site-packages in PYTHONPATH. The existing shared runner used the same policy. PR-PLAY-32 instead passed sys.executable directly to Popen with shell disabled (the default), and ran an observation script which eventually calls runpy.run_module('tools.playtest.worker'). No script-created subprocess or exec/replacement exists in that observer. The worker writes os.getpid() to ready.json. The controller obtains expected PID from Popen.pid and requires exact equality, the expected resolved data directory and isolation_verified before any HTTP probe. stop_owned terminates/waits/kills only its Popen handle; it never kills a PID from an untrusted attestation.

Original expected PID 31692 versus reported PID 18644 is preserved in original evidence. Original processes have exited, so their historical ancestry cannot be reconstructed retrospectively. The conclusion is supported by reproducing the identical executable selection in the same environment and independently observing the Windows parent relationships, rather than merely comparing PID values.

Controlled reproduction (investigate.py) imports only stdlib, no game/SDK/network libraries and no credentials. Its workers write PID, parent PID, executable and base executable, then wait for stdin. Toolhelp32 snapshots are captured while the processes are alive. Both normal exit and controller termination are compared for each executable. OpenProcess retains the observed worker handle before termination, allowing verification/cleanup without a reused-PID risk. All four runs exited and left no observed processes. No diagnostic descendant termination was needed; this observation does not imply that redirector termination is safe in every environment.

Observed normal redirector chain: controller 18652 → Popen redirector 19976 → worker 30512, independently corroborated by worker parent_pid=19976. Direct base chain: controller 18652 → worker/Popen 32904. Termination controls show the same respective topologies. Full executable paths, parent chains, exit codes and cleanup results are in process_reproduction.json.

Classification A is established for the reproduced failure mechanism. No evidence supports incorrect PID capture/reporting, gameplay failure or a defective ownership guard. The smallest reusable correction restores the known working direct-interpreter topology for custom observation workers instead of accepting mismatches or adding permissive ancestry rules. The historical controller's pre-repair bytes are preserved and match the investigation baseline; its old review archive/manifest remain historical pre-repair evidence.''')
    report('CHANGE_MANIFEST', '''# Change manifest

Existing files modified:

- tools/playtest/runner.py: extract existing direct-base-interpreter Popen construction into start_worker with optional observer script, preserve child environment without mutating caller settings, add fail-closed interpreter availability check, use the helper in the ordinary runner.
- artifacts/pr_play_32/execute.py: replace its single direct sys.executable Popen call with runner.start_worker using the same worker_capture.py target. This controller was NOT executed. Its original bytes are preserved under evidence_before/execute_pr_play_32.py; the original PR-PLAY-32 archive is retained.

New regression file: tests/test_pr_play_33_process_ownership.py (14 tests). Covers both module/script launch configuration, retained package and provider restrictions, missing base interpreter, controller adoption without importing live code, real direct-worker parent/PID ownership, cooperative normal exit, nonzero startup failure, timeout, termination/reaping, PID/path/isolation rejection before HTTP, and terminate-to-kill fallback through the owned handle. Existing test_playtest_startup_readiness.py contributes ten tests including stale attestation, deadline, startup exit and HTTP readiness behavior.

New artifacts/pr_play_33/: stdlib reproduction, readiness diagnostic, package builder, unchanged pre-repair source copies, hash baseline, raw process/pytest/readiness evidence, review reports, source snapshots, patches, manifests and archive verification. The readiness diagnostic is preserved exactly as executed, including its unpersisted post-readiness snapshot and failed session-absence assertion; it has not been silently corrected or retried.

New artifacts/atgb/pr_play_33/readiness/: exactly one isolated startup attempt and its normal controller evidence. No unrelated existing files changed, as checked against baseline_hashes.json across game/tools/tests and prior PR-PLAY-29/31/32 evidence. Temporary pytest files under development/tmp/pr_play_33_process are disposable test outputs and excluded from the review archive. Existing dirty worktree changes predated this task and were left intact.''')
    report('TEST_RESULTS', '''# Verification

Command: `.venv/Scripts/python.exe -m pytest tests/test_pr_play_33_process_ownership.py tests/test_playtest_startup_readiness.py --basetemp=development/tmp/pr_play_33_process --junitxml=artifacts/pr_play_33/process_tests.xml -ra`

Result: **24 passed**, 0 failed, 0 errors, 0 skipped. No retries or environment failures. Raw output and JUnit XML included. Tests remain offline; real small probe workers use no application/provider imports. Provider restriction preservation is checked in the child environment; PID/path/isolation mismatches are refused before HTTP.

Command: `.venv/Scripts/python.exe artifacts/pr_play_33/investigate.py`

Result: four process topology/exit/cleanup cases passed, with native Windows ancestry evidence and no remaining observed processes. No provider credentials, network or gameplay initialization.

Command: `.venv/Scripts/python.exe artifacts/pr_play_33/readiness.py`

Initial and final result: **exit 1, diagnostic AssertionError**, no retry. The actual module worker completed strict PID/isolation attestation and HTTP readiness (200). The controller then caught an AssertionError inside the diagnostic wait wrapper (native parent/child and safety checks); the exact assertion is unavailable because the snapshot was not persisted. It exported BLOCKED/application_startup_failure and completed owned-process cleanup. The outer diagnostic then asserted absence of session.json; isolated bootstrap session exists with turn_counter=0 and campaign_started=false. Both failures are disclosed. Of four planned controls, the first failed and the other three were never attempted. Its evidence is retained, with no failure hidden by retries. No planned controlled KeyboardInterrupt occurred, and no gameplay action loop was entered. The raw controller verdict must not be presented as a successful readiness matrix or gameplay verdict.

No full gameplay, opening-generation or PR-PLAY-32 live-focused suite was run. Those would exceed the zero-provider/no-gameplay scope. No provider requests or tokens were consumed by this investigation. Assistant/tool orchestration token use is separate and not measured by the application ledger.''')
    report('PROCESS_OWNERSHIP', f'''# Process ownership and offline readiness

Before: process_reproduction.json demonstrates controller → redirector → worker for sys.executable, and controller → owned worker for sys._base_executable. The legacy strict guard would reject the former, correctly. Normal and forced shutdown cases leave no observed worker/redirector processes.

After: the single actual offline module worker was PID **{owned}**. readiness_poll.jsonl and ready.json agree with Popen.pid; HTTP readiness was 200 in {json.loads((run/'diagnostics/http_ready.json').read_text())['startup_seconds']} seconds. Worker data directory was isolated under {run.relative_to(ROOT).as_posix()}/data; diagnostics active, both retry counts zero, placeholder credentials, synthetic SDK transport with external socket denial, and ASHEN_DISABLE_PROVIDER_CALLS=1 supplied by the diagnostic. No POST was permitted by its request wrapper. A subsequent wrapper assertion was caught by the controller before its first scenario action; normal finally cleanup ran. The intended KeyboardInterrupt was never reached.

Cleanup: {json.dumps(result['process_cleanup'])}. A post-failure native process snapshot shows no remaining owned PID or children. The loopback port is closed and bindable. The application ledger records initialization only; dispatched_requests=0, input/output/total_tokens=0. Bootstrap session turn_counter=0, campaign_started=false. No initialization/start/chat POSTs or live turns occurred.

Readiness diagnostic: FAILED. The controller first recorded an AssertionError in the wait wrapper after HTTP readiness. Its native snapshot was never saved, so parent/child diagnostic validation cannot be claimed and the exact failed assertion is unresolved. The outer diagnostic then failed the session-file-absence assertion. No retry. Observer worker and occupied-port controls NOT RUN; failure cleanup has unit/stdlib coverage, but its full application control is incomplete. Full offline readiness is not certified. A bootstrap session is not evidence of campaign initialization or a gameplay turn.

Next diagnostic for separate review: persist the native process snapshot before asserting, label each parent/child/safety assertion to establish which one failed, and replace the session-file-absence assumption with checks of zero campaign POSTs, turn_counter=0, campaign_started=false and zero accounting dispatches. Then run the module/observer readiness and occupied-port controls. Do not run the historical live controller, initialize a campaign or make provider requests as part of that diagnostic.''')
    report('PROVIDER_USAGE', '''# Provider usage

- Provider requests: **0**.
- Input tokens: **0**; output tokens: **0**; total provider tokens: **0**.
- Live gameplay turns: **0**; campaign initialization/start/chat POSTs: **0**.
- Provider/SDK/host retries: **0**. Readiness retries: **0**.

Evidence: isolated diagnostics/provider_usage.jsonl contains accounting initialization only; budget_snapshot.json has zero dispatches, zero tokens and no attempt records. Deterministic mode uses placeholder credentials, synthetic transport and external socket denial; diagnostic additionally forbids provider admission and every non-state HTTP request. Stdlib process reproductions and regression probe workers import no provider SDK. Gameplay source hashes are unchanged. Actual loading/saving of bootstrap session data by the state endpoint is disclosed; turn zero and campaign_started=false are verified. No live gameplay experiment or subsequent PR was initiated.''')
    report('FINAL_VERDICT', '''# PR-PLAY-33 final verdict

**B — PARTIAL.** Root cause **A — Windows virtual-environment process indirection** established; minimal shared-launch correction implemented; all 24 focused tests pass. Four independent process reproductions establish actual ancestry and successful cleanup. Strict PID/path/isolation guard, provider restrictions and timeouts are preserved.

The single application readiness attempt reached HTTP 200 with strict ownership and isolation verification, then the diagnostic wait wrapper raised AssertionError. The exact assertion is unresolved because its native snapshot was not saved. The controller cleaned up without remaining owned processes; the outer diagnostic then failed its overly strict session-file-absence assertion. Both failures are preserved. Stop-on-readiness-failure was honored: no retry and no remaining readiness controls launched. Observer-worker and occupied-port controls remain unverified, so PASS is not awarded.

Provider requests/tokens: 0/0. Live gameplay turns: 0. Gameplay code unchanged. Remaining blockers: identify the post-readiness wrapper assertion with persisted native evidence, correct the bootstrap-session expectation, and complete the remaining offline readiness controls after review. No PR-PLAY-34, live gameplay, campaign initialization/start/chat requests, commit or push. Stop after packaging and await review.''')
    sources = ['tools/playtest/runner.py', 'artifacts/pr_play_32/execute.py',
               'artifacts/pr_play_32/worker_capture.py', 'tests/test_pr_play_33_process_ownership.py',
               'tests/test_playtest_startup_readiness.py']
    for rel in sources:
        dest = OUT/'source'/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/rel, dest)
    for original, current, name in [('runner.py', 'tools/playtest/runner.py', 'runner.patch'),
            ('execute_pr_play_32.py', 'artifacts/pr_play_32/execute.py', 'controller.patch')]:
        diff = difflib.unified_diff((OUT/'evidence_before'/original).read_text().splitlines(True),
            (ROOT/current).read_text().splitlines(True), fromfile='before/'+current, tofile='after/'+current)
        (OUT/name).write_text(''.join(diff), encoding='utf-8')
    original_evidence = ['artifacts/pr_play_32/network_readiness.json',
        'artifacts/pr_play_32/cleanup_verification.json', 'artifacts/pr_play_32/PR_PLAY_32_FAILURE_ANALYSIS.md',
        'artifacts/atgb/pr_play_32/live/diagnostics/ready.json',
        'artifacts/atgb/pr_play_32/live/diagnostics/readiness_poll.jsonl',
        'artifacts/pr_play_29/execute_validation.py', 'artifacts/pr_play_31/PR_PLAY_31_FINAL_VERDICT.md']
    for rel in original_evidence:
        dest = OUT/'prior_evidence'/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/rel, dest)
    save('repository.json', dict(revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        worktree_previously_dirty=True, gameplay_edits_by_this_task=False))
    (OUT/'git_status_after.txt').write_bytes(subprocess.check_output(['git', 'status', '--short'], cwd=ROOT))
    # Scan known credential values without printing or serializing any value.
    from dotenv import dotenv_values
    env = {**dotenv_values(ROOT/'.env'), **os.environ}
    secrets = [v.encode() for k, v in env.items() if isinstance(v, str) and len(v)>8
               and any(part in k.lower() for part in ('key', 'token', 'secret', 'password', 'credential'))]
    excluded = {'archive_path.txt', 'archive_verification.json', 'MANIFEST.json', 'credential_scan.json'}
    included = [p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded]
    included += [p for p in run.rglob('*') if p.is_file() and p.suffix != '.zip' and '__pycache__' not in p.parts]
    hits = [str(p.relative_to(ROOT)) for p in included if any(s in p.read_bytes() for s in secrets)]
    save('credential_scan.json', dict(files_scanned=len(included), credential_hits=hits, passed=not hits))
    assert not hits
    included.append(OUT/'credential_scan.json')
    def name(p):
        return 'evidence/readiness/'+p.relative_to(run).as_posix() if p.is_relative_to(run) else p.relative_to(OUT).as_posix()
    save('MANIFEST.json', {name(p): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in included})
    included.append(OUT/'MANIFEST.json')
    now = datetime.now(timezone(timedelta(hours=-5), 'America/New_York EST'))
    archive = ROOT/'handoff'/f'CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for p in included:
            z.write(p, name(p))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest = json.loads(z.read('MANIFEST.json'))
        assert all(hashlib.sha256(z.read(n)).hexdigest() == row['sha256'] for n, row in manifest.items())
    save('archive_verification.json', dict(path=str(archive), entries=len(included), bytes=archive.stat().st_size,
        sha256=sha(archive), testzip=None, manifest_hashes_verified=True, verdict='B — PARTIAL'))
    (OUT/'archive_path.txt').write_text(str(archive)+'\n', encoding='utf-8')
    print(json.dumps(dict(archive=str(archive), verdict='B — PARTIAL', tests=24, provider_requests=0)))

if __name__ == '__main__':
    main()
