"""Package PR-PLAY-16's blocked preflight. No network or provider execution."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
NOW = datetime.now(timezone.utc)
LOCAL = NOW.astimezone(timezone(timedelta(hours=-5), 'EST'))

def write(name, value):
    (OUT/name).write_text(value if isinstance(value, str) else json.dumps(value, indent=2)+'\n', encoding='utf-8')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

from tools.playtest.runner import child_environment, load_scenario
from game import config
scenario = load_scenario('FiveTurnGameplay')
env = child_environment(OUT/'not_launched', scenario, 'Live', 'success')
safe_config = {
    'credentials_present': bool(env.get('OPENAI_API_KEY', '').strip()),
    'default_model': config.DEFAULT_MODEL_NAME,
    'high_precision_model': config.HIGH_PRECISION_MODEL_NAME,
    'retry_escalation_model': config.RETRY_ESCALATION_MODEL_NAME,
    'request_limit': int(env['ASHEN_PROVIDER_REQUEST_LIMIT']),
    'token_allowances': {k: int(env[f'ASHEN_PROVIDER_{k.upper()}_TOKEN_LIMIT']) for k in ('input', 'output', 'total')},
    'sdk_retries': 0, 'host_retries': 0,
    'startup_probe_skipped': env['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'] == '1',
    'renderer_worker_attestation': None,
    'note': 'Configuration read only. No worker, provider client, renderer execution or request.'
}
write('safe_configuration.json', safe_config)
write('repository_status.txt', git('status', '--short')+'\n')
write('repository.json', {'root': str(ROOT), 'branch': git('branch', '--show-current'), 'revision': git('rev-parse', 'HEAD'),
    'dirty_at_entry': True, 'existing_changes_preserved': True, 'captured_utc': NOW.isoformat()})

network_command = '.\\.venv\\Scripts\\python.exe -c "import socket,json; s=socket.socket(); s.bind((\'127.0.0.1\',0)); s.listen(); c=socket.socket(); result=c.connect_ex(s.getsockname()); print(json.dumps({\'socket_created\':True,\'http_bind_capable\':True,\'loopback_connect_ex\':result})); c.close(); s.close()"'
write('network_probe.json', {
    'evidence_type': 'transcribed actual tool output; not a second probe',
    'tool_chunk_id': 'eb573c', 'shell_exit_code': 0,
    'command': network_command,
    'stdout': {'socket_created': True, 'http_bind_capable': True, 'loopback_connect_ex': 10013},
    'interpretation': 'TCP bind/listen succeeded; loopback connection denied (WSAEACCES). The http_bind_capable label establishes TCP binding only, not HTTP readiness.',
    'http_readiness': 'NOT TESTED', 'provider_requests': 0,
    'socket_cleanup': 'Both probe sockets explicitly closed.'
})
prior = []
for path in (ROOT/'artifacts').rglob('reports/result.json'):
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('mode') == 'Live':
        prior.append({'path': str(path.relative_to(ROOT)), 'timestamp': value.get('timestamp'),
                      'scenario': value.get('scenario', {}).get('id'),
                      'requests': value.get('provider_usage', {}).get('dispatched_requests')})
write('existing_run_inventory.json', {'prior_live_labeled_results': prior,
    'pr_play_16_run_found_before_this_pass': False,
    'method': 'Inspected artifact reports/result.json and searched artifacts, development, handoff and docs for PR-PLAY-16/pr_play_16. Only PR-PLAY-15 next-pass reference found.',
    'caution': 'Prior Live labels include authorization-refusal tests and historical runs. These are not PR-PLAY-16 executions.'})

sources = ['scripts/run_live_playtest.ps1', 'tools/playtest/runner.py', 'tools/playtest/worker.py',
    'tools/playtest/gameplay.py', 'tools/playtest/validate_startup.py',
    'tools/playtest/scenarios/FiveTurnGameplay.json', 'game/opening_presentation_renderer.py',
    'game/provider_budget.py', 'game/model_routing.py', 'game/live_chat_interpretation.py',
    'game/expressive_dialogue.py', 'tests/test_playtest_startup_readiness.py']
for rel in sources:
    target = OUT/'source_snapshots'/rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/rel, target)
for rel in ['PR_PLAY_15_TEST_RESULTS.md', 'PR_PLAY_15_ROOT_CAUSE.md', 'startup_cycles.json']:
    target = OUT/'historical_context'/rel
    target.parent.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'artifacts/pr_play_15'/rel, target)

write('PR_PLAY_16_PREFLIGHT.md', f'''# PR-PLAY-16 Preflight

Verdict: **PREFLIGHT BLOCKED**. Report timestamp: {LOCAL.isoformat()} ({NOW.isoformat()} UTC).

Repository: `{ROOT}`. Branch: `{git('branch', '--show-current')}`. Revision: `{git('rev-parse', 'HEAD')}`.
Working tree was dirty at entry, including game/api.py, game/gm.py, tools/playtest/runner.py and worker.py plus prior artifacts. Existing changes preserved. See repository_status.txt; it also lists this report directory as newly created. No AGENTS.md was found in repository file enumeration or the checked parent directory. No commit or push performed.

Renderer, PR-PLAY-15 ready/http_ready separation, startup diagnostics, FiveTurnGameplay and live launcher exist. No prior PR-PLAY-16 live execution found; see existing_run_inventory.json. Historical PR-PLAY-14/15 are not counted as this pass.

## Environment decision

The actual zero-provider probe in network_probe.json created sockets, bound/listened on IPv4 loopback, then connect_ex returned **10013**. A successful shell exit is not successful networking: connect_ex returns the socket error as data. This establishes local connection denial, despite successful binding. The probe closed both sockets.

Per mission sections 4.2 and 17, stopped before application or scenario startup in this known-incompatible context. No permission escalation or security bypass attempted. Prior PR-PLAY-15 unrestricted successes do not attest current execution permissions. The required single offline application readiness check was **not executed**, because local networking failed its prerequisite. Child-process worker startup/termination, application initialization, HTTP GET /api/state, port release after worker cleanup, ready.json and http_ready.json are unverified for this pass. No worker exists to orphan.

## Configuration and harness inspection

Credentials present (boolean only); all configured model routes resolve to gpt-4.1-mini. No provider probe. Effective limit is six requests; aggregate token ceilings are 200000 input / 20000 output / 220000 total, unchanged. See safe_configuration.json.

Source evidence in source_snapshots/: launcher exposes authorization/capture switches; runner.run_playtest refuses unauthorized Live and uncaptured FiveTurnGameplay, clamps limits, launches an isolated worker, requires HTTP 200 before actions, preserves baseline/opening/after and per-turn snapshots, and cleans its owned worker in finally. child_environment disables SDK and host retries and skips startup probes. Worker checks retry configuration and forbids connectivity probes. provider_budget.admit_request enforces atomic admission and durable dispatch accounting; request owners dispatch through that admission. gm.call_gpt blocks retry_attempt > 0; interpretation and expression each make one request with no model switch. Configured alternate routes are the same model. No provider judge client is in gameplay evaluation. Capture opt-in enables bounded opening response evidence; ordinary-turn native diagnostics/API responses are captured. Raw ordinary completion text availability depends on native captures, not guaranteed by the option alone.

Renderer propagation is supported statically by child environment inheritance and worker diagnostics, but **not verified in an actual PR-PLAY-16 worker**. Flag was not set during the network probe; no permanent environment changes. Bounded timeouts, first-failure/budget stopping and owned-process cleanup are implemented; none were exercised here. Behavioral assurance is limited to source inspection and historical context, not a new integration pass.
''')

write('PR_PLAY_16_LIVE_EXECUTION.md', f'''# PR-PLAY-16 Live execution

**No live scenario invoked.** Preflight stopped on loopback access denial, before any worker/application startup. Report timestamp {LOCAL.isoformat()}; no live execution timestamp exists.

Live invocation count 0; live provider requests 0; synthetic provider requests 0; judge/probe/retry/fallback requests 0. Player turns attempted/completed 0/0. Opening was neither generated nor rejected. No provider HTTP, parsing or semantic validation result exists. No scenario budget was exhausted. No API HTTP request was attempted.

Exact executed network command: see network_probe.json. Other commands were read-only repository/configuration inspection and evidence packaging. No live command was executed. The intended launcher below is recorded for review only, NOT execution evidence:

```powershell
$env:ASHEN_OPENING_RENDERER = '1'
.\\scripts\\run_live_playtest.ps1 -Scenario FiveTurnGameplay -Mode Live -AuthorizeLiveProvider -CaptureResponse
```

Exact stop reason: local loopback connect_ex returned Windows 10013 (access denied); mission requires stopping in a restricted environment. No rerun or automatic recovery attempted. Existing PR-PLAY-15 context is labeled historical_context/ and does not count as current HTTP readiness. No current ready.json, http_ready.json, harness evidence.zip, state snapshots, renderer traces, provider plan or provider responses were generated. They are unavailable, not omitted successes.

Evidence: network_probe.json; safe_configuration.json; repository.json; repository_status.txt; existing_run_inventory.json; source_snapshots/; historical_context/.
''')

write('PR_PLAY_16_GAMEPLAY_REVIEW.md', '''# PR-PLAY-16 Gameplay review

Gameplay verdict: **INCONCLUSIVE**. Attempted turns 0; completed turns 0. Opening assessment A setting grounding / B comprehensibility / C narrative coherence / D player agency / E factual authority: all INCONCLUSIVE. No opening or public catalog/selection plan was generated. Structured presentation is not penalized.

No player action reached a provider. All five planned interactions (observe gate district, ask gate serjeant about missing patrol, examine notice board, pursue patrol leads, try city entry) remain untested. There are no DM responses or NPC exchanges to review.

NPC responsiveness, bounded improvisation, narrative continuity and meaningful progression are unassessed. No before/after campaign state was produced; character, location, inventory, currency, time, quests, relationships, combat, world facts and overlays cannot be compared. No authority violation was observed, but preservation of deterministic authority has not been demonstrated. No player-facing excerpts or hidden world information are published in these reports. Scenario source is developer evidence only.

The earliest barrier is environment/configuration, not opening quality, ordinary-turn validation or gameplay behavior. Prior startup successes cannot establish playability.
''')

write('PR_PLAY_16_PERFORMANCE.md', '''# PR-PLAY-16 Performance

| Metric | Current pass |
|---|---|
| Live / synthetic provider requests | 0 / 0 |
| Successful / failed provider requests | 0 / 0 |
| Input / output / total tokens | 0 / 0 / 0 (no dispatch; no provider usage response) |
| Total provider latency | 0 (no calls) |
| Average / longest provider latency | N/A |
| Live scenario wall-clock duration | N/A; never invoked |
| Network probe tool wall time | 0.611 seconds, includes shell/interpreter overhead |
| Completed player turns | 0 |
| Requests per completed turn | N/A; denominator zero |
| Provider cost | Zero dispatch exposure; no pricing estimate needed |

Preflight inspection and report packaging time are not gameplay latency. No application latency or live harness overhead measurement is available. Interactive usability is INCONCLUSIVE. Six-request budget remains entirely unused; budget feasibility for five turns remains a known scenario limitation, not an observed failure. No performance setting was changed.
''')

write('PR_PLAY_16_FINDINGS.md', '''# PR-PLAY-16 Findings

## Confirmed blocker

Environment/configuration — high confidence. Observed: IPv4 loopback connect_ex returned 10013 after successful socket creation/bind/listen. Expected: loopback connection success (0) before offline HTTP readiness and authorized gameplay. Evidence: network_probe.json, actual tool chunk eb573c. Likely boundary: current sandbox/local networking permissions. Exact OS security component is not established by this pass. PR-PLAY-15 historical_context corroborates the same restriction, but its asyncio stall was not reproduced here.

Recommended narrow investigation: establish an explicitly approved execution context with working loopback access and verify one zero-provider offline /api/state readiness-and-cleanup cycle before considering the still-unexecuted bounded live scenario under external review.

## Confirmed application defects

None established. A networking blocker is not evidence that the application, opening renderer, NPC response system or validators are defective.

## Suspected defects

None supported by current gameplay evidence. Do not infer a new startup deadlock, provider problem or narration defect from connection denial.

## Non-defect limitations

No execution in a known-incompatible context, no escalation, no live invocation, no retries, no judge calls and no gameplay modifications are deliberate constraint compliance. Six requests may not cover all five ordinary actions because interpretation and expression can each consume requests; this is static scenario budget feasibility, not actual budget exhaustion.

## Evidence gaps

Current worker lifecycle, HTTP readiness, renderer propagation, plan compliance, opening publication, setting grounding, NPC responsiveness, continuity, bounded improvisation, consequential state authority, live parsing/validation, token accounting and interactive performance remain untested. Runtime request budget behavior was source-inspected, not re-exercised. No current harness evidence.zip exists. Historical context is clearly segregated. Existing working-tree changes limit attribution to the inspected uncommitted revision.
''')

answers = [
('Did the application establish HTTP readiness?', 'Not tested; stopped before worker startup.'),
('Did the renderer flag reach the live worker?', 'Not verified; no live worker.'),
('Did the provider return a valid opening presentation plan?', 'Not tested; zero requests.'),
('Did the engine publish an accepted opening?', 'No opening execution; acceptance unknown.'),
('Was the opening grounded in campaign/setting information?', 'Inconclusive.'),
('Was the opening coherent and actionable?', 'Inconclusive.'),
('Did any live player turn complete?', 'No.'),
('How many player turns completed?', '0 attempted / 0 completed.'),
('Did NPC interactions function meaningfully?', 'Not tested.'),
('Did narration remain consistent with deterministic state?', 'Not tested.'),
('Were authority violations observed?', 'None observed; authority preservation untested.'),
('Was performance acceptable?', 'Inconclusive; no live latency.'),
('Did the scenario complete or stop early?', 'Never invoked; preflight stopped.'),
('What was the exact stop reason?', 'Loopback connect_ex returned Windows error 10013; local networking restricted.'),
('What is the single highest-priority next step?', 'After external review, use an explicitly approved networking-capable context and verify one zero-provider offline readiness/cleanup cycle before the bounded live scenario.')]
write('PR_PLAY_16_FINAL_VERDICT.md', '# PR-PLAY-16 Final verdict\n\nStatus: **BLOCKED**. Overall: **D — INCONCLUSIVE**.\n\n' + '\n\n'.join(f'{i}. **{q}** {a}' for i, (q,a) in enumerate(answers, 1)) + '\n\nNo implementation changes, commit, push or automatic PR-PLAY-17. Stop and await external review.\n')

# Never package .env, credentials, unrelated historical archives or repository data.
files = [p for p in OUT.rglob('*') if p.is_file() and p.name not in {'archive_verification.json', 'manifest.json'}]
from dotenv import dotenv_values
secret_values = [v for k,v in {**dotenv_values(ROOT/'.env'), **os.environ}.items()
                 if v and len(v)>8 and any(s in k.lower() for s in ('api_key', 'secret', 'password', 'credential', 'access_token', 'auth_token'))]
for p in files:
    raw = p.read_bytes()
    if any(v.encode() in raw for v in secret_values):
        raise RuntimeError('Secret scan blocked packaging; file name withheld')
write('manifest.json', [{'path': str(p.relative_to(OUT)), 'bytes': p.stat().st_size,
                         'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)])
files.append(OUT/'manifest.json')
archive = ROOT/'handoff'/f'CURRENT_REVIEW({LOCAL:%Y%m%d-%H%M%S}).zip'
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, 'pr_play_16/'+p.relative_to(OUT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == len(files)
    for p in files:
        assert z.read('pr_play_16/'+p.relative_to(OUT).as_posix()) == p.read_bytes()
write('archive_verification.json', {'archive': str(archive), 'readable': True, 'crc_test': 'PASS',
    'byte_comparison': 'PASS', 'files': len(files), 'bytes': archive.stat().st_size,
    'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'secret_value_scan': 'PASS'})
print(json.dumps({'archive': str(archive), 'files': len(files), 'status': 'BLOCKED', 'verdict': 'D', 'live_invocations': 0, 'provider_requests': 0}, indent=2))
