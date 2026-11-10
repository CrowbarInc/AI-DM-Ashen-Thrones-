from pathlib import Path
import json,difflib,hashlib,zipfile
from datetime import datetime,timezone,timedelta
ROOT=Path.cwd(); OUT=ROOT/'artifacts/pr_play_15'
cycles=json.loads((OUT/'startup_cycles.json').read_text())
old=ROOT/'artifacts/atgb/automated_playtests/20261101T150418Z-2c4a2a1e0fe1'
def report(name,text): (OUT/name).write_text(text.strip()+'\n',encoding='utf-8')
report('PR_PLAY_15_STARTUP_TIMELINE.md', '''# PR-PLAY-14 startup timeline

All absolute times below are UTC on November 1, 2026 (subtract five hours for EST). Filesystem timestamps are metadata observations, not fabricated application events. Original evidence was reviewed before source edits.

| Event | Time / relative order | Evidence | Observed result | Confidence |
|---|---|---|---|---|
| Launcher invoked | 15:04:18.2213858 | artifacts/pr_play_14/invocation.json | One authorized Live invocation; renderer flag set to 1 | High |
| Controller run record initialized | 15:04:18.754898 | original reports/result.json timestamp | FiveTurnGameplay, Live | High |
| Worker created | After preflight, before log creation; exact OS creation unavailable | runner.py Popen ordering; cleanup PID 2368 | Actual base interpreter launched, combined stdout/stderr piped | High ordering; exact time unavailable |
| Application log opened | 15:04:20.4798834 | original application.log CreationTimeUtc | Zero bytes throughout run | High metadata |
| Socket bound/listening | Before configuration attestation; exact time unavailable | worker.py source ordering; ready.json port 50501 | IPv4 127.0.0.1; OS listen occurs before app imports | High source order; no runtime event timestamp |
| Configuration/accounting initialized | 15:04:22.365378 | original provider_usage.jsonl initialized event | No admission/dispatch/completion events followed | High |
| Renderer configuration recorded | By readiness file creation | original ready.json | enabled/selected, retries 0, six requests, token ceilings 200000/20000/220000 | High; no renderer invocation established |
| ready.json created | 15:04:22.3694176 | original ready.json CreationTimeUtc and LastWriteTimeUtc | Configuration/isolation attestation; does not prove HTTP service | High metadata |
| HTTP server initialization attempted | After ready.json; exact location/time unrecorded | source calls uvicorn after file write | No uvicorn log, failure file, or successful HTTP response | High source ordering; runtime progress unknown |
| First HTTP readiness request | After attestation read; precise time unavailable | controller source; final TimeoutError | Outcome detail discarded by old polling loop | High source ordering; individual outcome unknown |
| Subsequent polling attempts | Until deadline; count/timestamps unavailable | controller source | No successful HTTP 200; individual errors unknown | High absence of success; count unknown |
| Deadline expired | About 30 seconds after controller started polling; exact wall time unavailable | result failure TimeoutError; configured startup 30s | application_startup_failure; no scenario actions | High |
| Worker terminated | After timeout, before final result | process_cleanup in result and execution_log | PID 2368 stopped, exit code 1; not evidence of spontaneous crash | High ordering |
| Cleanup/report complete | Result elapsed 31.312s; result file last write 15:04:50.5963282 | result.json and filesystem metadata | Owned worker reaped, evidence exported; no gameplay | High; elapsed excludes final export |

Historical first/last poll timing, actual initialization stack, HTTP status and connection errors cannot be recovered. The PR-PLAY-15 reproduction supplies new evidence, not retroactive timestamps.
''')
report('PR_PLAY_15_ROOT_CAUSE.md', '''# Root cause and architecture

## Finding

Confirmed in this execution environment, high confidence: the restricted Windows sandbox denies local TCP connections (WinError 10013). Python 3.12 asyncio's ProactorEventLoop stalls in socket.socketpair -> accept while constructing its internal loopback self-pipe, before uvicorn can log server startup or execute the ASGI lifespan. The controller independently receives local connection access denial. Increasing the readiness timeout cannot repair this boundary.

The same provider-stubbed diagnostic reaches /api/state HTTP 200 outside that sandbox. Five independent startup/shutdown cycles then pass outside it. Historical PR-PLAY-14 attribution is strongly supported but not proven: its logs discarded exactly the needed transport detail and contain no stack. No application startup-order defect is established.

## Evidence and investigation

1. Read PR-PLAY-14 preflight, execution/final reports, invocation, configuration, original result, ready file, empty application log, initialized-only provider journal and cleanup record before edits.
2. An initial diagnostic output location was refused by the existing isolation guard before worker creation; corrected it to artifacts/atgb without weakening the guard.
3. Initial actual startup reproduction (initial_timeout.json) ran the existing deterministic worker and stopped before any scenario action. Every captured readiness request failed with URLError/WinError 10013; worker timed out after configuration attestation.
4. Added phase events and one bounded eight-second stack capture. stack_reproduction.json references the run containing startup_stack.log: the worker is blocked inside socketpair accept, called from asyncio Proactor loop construction. Events end at server_run_entered. No ASGI initialization event or uvicorn log occurs.
5. Repeated the same startup-only question with sandbox restrictions lifted (unrestricted_comparison.json): HTTP 200, no scenario actions or provider dispatch. This changes the execution context, not the application architecture.
6. Final sandbox check (repaired_sandbox_failure.json) now terminates promptly with PermissionError; readiness_poll.jsonl records access_denied/os_error 10013 and cleanup succeeds.

## Startup path and lifecycle

scripts/run_live_playtest.ps1 selects the venv Python (bundled fallback), sets repository PYTHONPATH and invokes tools.playtest.runner. runner.run_playtest validates authorization/scenario, dependencies and pinned fixture, prepares a fresh isolated store, then launches the base interpreter directly to avoid a Windows venv redirector PID. Popen owns that single worker, disables a visible console, and captures stdout plus stderr into a capped, redacted application.log through a drain thread. process.poll detects early exits each polling iteration; stop_owned terminates, waits, then kills on bounded timeout. No server subprocess or reload process is spawned. This is ownership-specific cleanup, not a general descendant-tree terminator.

worker.main binds AF_INET 127.0.0.1 to the requested port (0 selects an OS-assigned free port) and calls listen before game imports. A conflict fails at bind; an existing listener is neither reused nor killed. Configuration, isolation, accounting and retry controls initialize; ready.json is written before uvicorn.Server.run. Uvicorn must then construct its event loop, initialize FastAPI's lifespan (ensure_data_files_exist and skipped upstream preflight logging), and begin servicing /api/state. The GET does not require new_campaign or start_campaign. All successful cycles exercised that real production endpoint on the isolated bootstrap store.

ready.json means configuration/isolation initialized, plus a prebound listening socket. It does not mean ASGI or HTTP ready. Old and new controllers require /api/state HTTP 200; no premature-ready acceptance defect was found. Added phase/time fields retain all original keys, and http_ready.json independently records endpoint success. Existing ready.json consumers (runner and tests) retain their contract.

The startup timer starts after Popen and log-thread creation. It covers worker imports/configuration, uvicorn/event-loop/lifespan initialization and HTTP polling. It excludes earlier preflight and fixture copying, which have their own cap. Requests ignore machine proxies; controller and worker both use IPv4 loopback. Poll requests are capped at one second and remaining deadline. A monotonic deadline remains 30 seconds; late HTTP success is not accepted. Failed HTTP JSON responses retain status in polling evidence; non-JSON payloads are recorded as invalid_response because the shared request parser rejects them. Bodies and arbitrary exception strings are excluded.

## Alternatives

| Hypothesis | Evidence / conclusion |
|---|---|
| Premature ready file incorrectly accepted | Rejected: controller always performs HTTP polling; file semantics needed clarification only |
| Historical port conflict | Strongly disfavored: bind precedes historical ready file; controlled occupied-port test produces OSError 10048 and no ready file |
| IPv4/IPv6/proxy mismatch | Rejected in reproduction: both sides use 127.0.0.1; proxy handling explicitly bypassed |
| Slow game initialization or application deadlock | Not supported: stack is before ASGI lifespan, and unrestricted startup is under two seconds in five cycles |
| Worker exited unnoticed | Not observed historically; original controller polls process state; new regression verifies early exit detection |
| Polling discarded evidence | Confirmed: old loop caught connection/parse exceptions and discarded them; fixed with safe structured metadata and fail-fast access denial |
| Provider issue | Rejected for startup reproduction: provider transport stubbed, probes forbidden; five cycles additionally disable provider admission and record zero dispatches |
| Sandbox/network restriction | Confirmed now by WinError 10013, socketpair stack and successful unrestricted comparison; probable historical cause, not directly provable |

Relevant source locations: runner.py stop_owned (~154), wait_for_http_ready (~169), Popen/readiness invocation (~378); worker.py main (~121), ready.json (~164), ASGI wrapper (~173), server run (~196), exception diagnostic (~205); game/api.py lifespan (~297). Review source_snapshots and the task-specific diffs for exact packaged lines.
''')
report('PR_PLAY_15_REPAIR_REPORT.md', '''# Repair report

Files modified by this pass:

- tools/playtest/runner.py: extracted bounded readiness polling; persists UTC/elapsed events, worker PID, URL/status, safe error type and OS code. Distinguishes refused connection, timeout, access denial, invalid response, endpoint status, worker exit, stale attestation and deadline expiration. Access denial fails immediately. Records a separate http_ready.json only after timely HTTP 200. Adds shutdown duration to cleanup metadata.
- tools/playtest/worker.py: phase events for binding, configuration, uvicorn and ASGI startup; additive phase/time on ready.json; one bounded stack watchdog (eight seconds), canceled on an HTTP request or server exit; failure diagnostic retains safe stage and OS code. ASGI response schemas are unchanged.
- tests/test_playtest_startup_readiness.py: ten offline regressions for these observed diagnostics and readiness boundaries.
- tools/playtest/validate_startup.py: reusable five-cycle offline startup-only validator and occupied-port control, using existing controller/worker and isolated stores. Provider admission is explicitly prohibited in addition to the existing synthetic SDK and external socket denial. It unwinds with a controlled KeyboardInterrupt immediately after readiness to exercise normal cleanup/export without sending campaign requests.

Before: sandbox loopback denial looked like an unexplained 30-second startup timeout; configuration attestation was the last useful evidence. After: denial is immediately observable as access_denied/os_error 10013, server progress and bounded stacks are preserved, and successful HTTP readiness is independently attested. No application architecture repair was justified. The environmental correction for successful validation was running with authorized local loopback access outside the restricted sandbox, not modifying asyncio or bypassing provider safeguards.

Compatibility: PowerShell CLI, scenario modes, old ready.json keys, isolation checks, retry/request/token ceilings and default 30-second timeout remain. New artifacts and cleanup metadata are additive. Full preexisting user modifications are retained; runner_before.py and worker_before.py capture the dirty sources at task entry, and changes_from_task_start.patch excludes prior work. No commits/pushes.

Preservation verification: configuration_preservation.json confirms byte-for-byte equality with PR-PLAY-14 snapshots for game/api.py, game/gm.py, game/config.py, provider budget/model routing, opening renderer, FiveTurnGameplay scenario and PowerShell entry point. No gameplay/narration changes, provider model/budget changes, schema changes, semantic-validator relaxation or provider calls were introduced.

Limitations: local-loopback permissions must be available for the future run. The old historical trace remains incomplete. Existing Windows cleanup forcibly terminates the owned worker (normal observed exit code 1), not a graceful ASGI shutdown; process exit, port release and collected per-request budget snapshots are verified. Cleanup owns a single direct interpreter and is not a general process-tree supervisor. Invalid non-JSON HTTP responses are distinguishable as invalid_response, but their status is not retained by the shared JSON request parser. No speculative changes address these separate limitations.
''')
rows='\n'.join(f"| {i+1} | {c['pid']} | {c['port']} | {c['http']['startup_seconds']:.3f} | {c['cleanup']['shutdown_seconds']:.3f} | 200 | stopped / released | 0 |" for i,c in enumerate(cycles['cycles']))
report('PR_PLAY_15_TEST_RESULTS.md', f'''# Test results

Focused: **10 passed, 0 failed, 0 skipped, 0 errors** (focused_tests.txt/.xml).
Existing relevant suite: **26 passed, 0 failed, 0 skipped, 0 errors** (existing_tests.txt/.xml). Includes success, deadline cleanup, interruption, occupied port, unauthorized Live refusal, external socket denial, redaction, evidence integrity and ScriptedObservation offline execution. Its provider dispatch counters represent synthetic SDK calls; no real provider requests or tokens were consumed. This suite intentionally exercises synthetic campaign actions; startup-cycle validation does not.

Commands (PowerShell, repository root):

```powershell
.venv/Scripts/python.exe -m pytest tests/test_playtest_startup_readiness.py -q -o addopts= --junitxml=artifacts/pr_play_15/focused_tests.xml
.venv/Scripts/python.exe -m pytest tests/test_automated_playtest.py -q -o addopts= --junitxml=artifacts/pr_play_15/existing_tests.xml
$env:ASHEN_OPENING_RENDERER='1'
.venv/Scripts/python.exe -m tools.playtest.validate_startup
```

The integration commands ran with authorized local loopback access outside the sandbox. The focused tests use deterministic mocked transport/clock and require no network.

## Five consecutive final offline cycles

| Cycle | PID | IPv4 port | Startup seconds | Shutdown seconds | HTTP | Cleanup | Dispatches |
|---|---|---|---|---|---|---|---|
{rows}

startup_cycles.json records OS process creation UTC, HTTP response UTC, PID/port, durations, renderer attestation and limits. Each cycle uses a fresh pinned isolated store and OS-assigned port. Readiness deadline is unchanged at 30s. Every cycle returns HTTP 200 from the real /api/state endpoint, stops its worker, confirms no remaining connection, and successfully binds the released port. All five completed. Native scenario reports say INCONCLUSIVE/interrupted_execution because the validator intentionally unwinds before gameplay; they are not relabeled gameplay passes. The validator's independent lifecycle assertions establish startup success.

## Failure controls

Occupied port: worker fails at socket_binding with OSError 10048; controller records worker_exited, exits in {cycles['failure_control']['elapsed_seconds']:.3f}s, reaps worker (exit 2), and leaves original listener intact. No ready file is emitted, no campaign requests occur, no provider dispatch occurs.

Restricted sandbox: final check reports PermissionError; readiness_poll.jsonl preserves access_denied/10013, cleanup stopped PID 4460 in 0.031s; controller elapsed 3.610s including preflight. It no longer waits the full deadline. Initial unrepaired sandbox attempts remain preserved (initial_timeout.json and stack_reproduction.json), along with the successful unrestricted comparison.

Focused regressions cover HTTP 503 followed by 200, worker exit, stale PID attestation, connection refusal, request timeout, access denial, invalid response, absent attestation/deadline, late success rejection and transient attestation parse retry. Real success/cleanup/bind failure are covered by the lifecycle validator and existing suite.

An initial validation-driver monkeypatch of subprocess.Popen caused an import TypeError before worker creation; corrected the driver to inspect the actual process at the readiness hook. validation_driver_preflight_error.txt and its failed run are retained. This diagnostic-driver failure is not counted among the five final cycles. The first diagnostic output-root rejection similarly occurred before worker launch and did not weaken isolation.

Provider verification: five cycles = **0 admissions/dispatches**, initialized-only durable journals and budget snapshots show dispatched_requests=0; bind control exits before accounting and dispatch code; initial comparisons performed GET only using synthetic transport. No probes, live gameplay, live requests or provider tokens. final_process_check.json verifies all nine attested investigation worker PIDs are absent. Bind-failure PID 23364 is separately reaped in its result. No unresolved test failures. git diff --check passed for scoped files.
''')
report('PR_PLAY_15_READINESS_ASSESSMENT.md', '''# Readiness assessment

| Question | Assessment |
|---|---|
| Worker reliably starts? | Yes: five consecutive fresh offline cycles, actual base interpreter owned directly |
| HTTP server reliably binds? | Yes with permitted local loopback: five isolated ports; occupied-port control fails visibly |
| /api/state reliably responds? | Yes: real production endpoint HTTP 200 in all five cycles, before campaign actions |
| Startup failures observable? | Yes: poll events with status/error/OS code, worker phase and safe failure metadata; bounded stack if startup stalls |
| Readiness signals accurate? | Yes: ready.json explicitly means configuration initialized; separate http_ready.json means HTTP 200; controller never accepts file alone |
| Startup timeout appropriate? | Yes for measured environment: all five below two seconds, 30-second cap unchanged. Access denial fails immediately. No arbitrary startup delays added |
| Cleanup works? | Yes: owned worker reaped and port rebind verified five times; bind control preserved unrelated listener. This establishes forced process cleanup, not graceful ASGI shutdown |
| Provider calls prevented? | Yes: SDK stub + external socket denial in deterministic workers, placeholder credentials, skipped/forbidden probes; cycle validator additionally prohibits provider admission. Zero real requests and zero startup-cycle dispatches |
| Ready for authorized live replay? | Yes for infrastructure, when launched with local loopback permitted and following a separate explicit live authorization. This pass does not authorize or execute it |

Renderer selected throughout five cycles; model, provider limits, retries, output allowance, production application and scenario are unchanged from the PR-PLAY-14 snapshots (configuration_preservation.json). Evidence capture/export was readable in all cycles. No extra provider calls were added. Gameplay quality, opening acceptance under a real model and five-turn behavior remain unvalidated.

Do not repeat the old live command inside a context that prohibits localhost TCP. Review the access_denied diagnostic first if permissions differ. The exact historical cause cannot be proven retrospectively; the equivalent environment failure is now reproduced, isolated, visible and bounded.
''')
report('PR_PLAY_15_FINAL_VERDICT.md', '''# PR-PLAY-15 final verdict

**PASS — A: READY FOR CONTROLLED LIVE VALIDATION (infrastructure only).**

Confirmed: sandbox local-TCP denial stalls Windows asyncio self-pipe construction before uvicorn/ASGI startup and denies controller HTTP connections. Removing that restriction yields HTTP readiness. Historical PR-PLAY-14 attribution is probable, not certain, because the original controller discarded transport detail. No independent application initialization defect was demonstrated.

Repairs: safe readiness polling diagnostics and fail-fast access denial, distinct HTTP-success artifact, additive configuration readiness semantics, worker phase/stack/failure evidence and measured cleanup. The 30-second startup cap and provider/gameplay configuration remain unchanged.

Validation: 10 focused tests and 26 existing relevant tests passed with no failures/skips/errors. Five consecutive offline startup/HTTP/shutdown/port-release cycles passed with zero provider dispatches. Controlled bind failure and restricted-sandbox denial were correctly identified and cleaned up. No real provider requests, tokens, gameplay live run, commit or push occurred.

Remaining risks: future execution still needs permitted loopback; historical transport evidence is irretrievable; Windows termination is forced rather than a graceful lifespan shutdown; real-model gameplay quality is unvalidated. Existing unrelated dirty-worktree changes were preserved.

Single recommended next step: external review of this archive, then separately authorize a controlled PR-PLAY-14 replay in an execution context that permits local TCP. Do not begin PR-PLAY-16 automatically.
''')
# Task-specific diff against the already-dirty files, never attribute prior changes to this pass.
parts=[]
for f in ['runner','worker']:
    before=(OUT/f'{f}_before.py').read_text().splitlines(keepends=True)
    after=(ROOT/f'tools/playtest/{f}.py').read_text().splitlines(keepends=True)
    parts.extend(difflib.unified_diff(before,after,fromfile=f'a/tools/playtest/{f}.py',tofile=f'b/tools/playtest/{f}.py'))
for f in ['tools/playtest/validate_startup.py','tests/test_playtest_startup_readiness.py']:
    parts.extend(difflib.unified_diff([], (ROOT/f).read_text().splitlines(keepends=True),fromfile='/dev/null',tofile='b/'+f))
(OUT/'changes_from_task_start.patch').write_text(''.join(parts),encoding='utf-8')
# Only related evidence, no .env, campaign data, unrelated historic packages or credentials.
selected={}
def add(path,arc): selected[arc]=path
for p in OUT.rglob('*'):
    if p.is_file() and p.suffix not in {'.zip','.pyc'} and p.name not in {'archive_path.txt','archive_verification.json'}:
        add(p,'artifacts/pr_play_15/'+p.relative_to(OUT).as_posix())
for p in (ROOT/'artifacts/atgb/pr_play_15').rglob('*'):
    if p.is_file() and p.relative_to(ROOT/'artifacts/atgb/pr_play_15').parts[2] in {'configuration','diagnostics','reports'}:
        add(p,p.relative_to(ROOT).as_posix())
for relative in ['configuration/run.json','configuration/scenario.json','diagnostics/ready.json','diagnostics/application.log','diagnostics/provider_usage.jsonl','diagnostics/execution_log.json','reports/result.json','reports/SUMMARY.md']:
    add(old/relative,'prior_pr_play_14/harness/'+relative)
for name in ['PR_PLAY_14_PREFLIGHT.md','PR_PLAY_14_LIVE_EXECUTION.md','PR_PLAY_14_FINAL_VERDICT.md','invocation.json','preflight_configuration.json','launcher_output.txt']:
    add(ROOT/'artifacts/pr_play_14'/name,'prior_pr_play_14/'+name)
for f in ['tools/playtest/runner.py','tools/playtest/worker.py','tools/playtest/validate_startup.py','tests/test_playtest_startup_readiness.py','scripts/run_live_playtest.ps1','tools/atgb/isolation.py','tools/playtest/scenarios/FiveTurnGameplay.json']:
    add(ROOT/f,'source_snapshots/'+f)
metadata={}
for rel in ['diagnostics/ready.json','diagnostics/application.log','reports/result.json']:
    p=old/rel; s=p.stat()
    metadata[rel]={'creation_time_utc':datetime.fromtimestamp(s.st_ctime,timezone.utc).isoformat(),'last_write_utc':datetime.fromtimestamp(s.st_mtime,timezone.utc).isoformat(),'bytes':s.st_size}
report('historical_file_metadata.json',json.dumps(metadata,indent=2))
add(OUT/'historical_file_metadata.json','artifacts/pr_play_15/historical_file_metadata.json')
manifest={'campaign':'PR-PLAY-15','verdict':'A','provider_real_requests':0,'files':[{'path':arc,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for arc,p in sorted(selected.items())]}
report('archive_manifest.json',json.dumps(manifest,indent=2))
# Self-hash intentionally excluded.
selected['artifacts/pr_play_15/archive_manifest.json']=OUT/'archive_manifest.json'
name='CURRENT_REVIEW('+datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')+').zip'
archive=ROOT/'handoff'/name
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for arc,p in sorted(selected.items()): z.write(p,arc)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for row in manifest['files']: assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
verification={'archive':str(archive),'readable':True,'crc_ok':True,'manifest_hashes_verified':True,'files':len(selected),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
report('archive_path.txt',str(archive)); report('archive_verification.json',json.dumps(verification,indent=2))
print(json.dumps(verification,indent=2))
