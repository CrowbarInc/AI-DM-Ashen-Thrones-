"""Evidence analysis and packaging only; no application/provider execution."""
import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
LIVE = ROOT/'artifacts/atgb/automated_playtests/20261101T153625Z-02fc6545bc28'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
r = read(LIVE/'reports/result.json')
offline = read(OUT/'offline_readiness.json')
events = [json.loads(line) for line in (LIVE/'diagnostics/provider_usage.jsonl').read_text().splitlines()]
completion = next(e for e in events if e['event'] == 'completed')
diagnostic = next(e for e in events if e.get('stage') == 'provider_response')
capture = read(next((LIVE/'opening_response_evidence').glob('*.json')))

def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
def report(name, text):
    (OUT/name).write_text(text.strip()+'\n', encoding='utf-8')

# Read-only verification that the owned live worker released its port.
port = r['environment_verification']['application']['port']
with socket.socket() as probe:
    probe.settimeout(1)
    refused = probe.connect_ex(('127.0.0.1', port)) != 0
with socket.socket() as released:
    released.bind(('127.0.0.1', port))
save('live_cleanup.json', {'cleanup': r['process_cleanup'], 'port': port,
    'connection_refused': refused, 'port_rebind_succeeded': True})
request = {'request_number': 1, 'purpose': 'Campaign opening / scene_opening (ledger: primary_turn)',
    'live': True, 'synthetic': False, 'configured_model': completion['configured_model'],
    'returned_model': completion['model'], 'provider_http_status': None,
    'provider_http_status_note': 'Not persisted by native capture; SDK returned completed response. Do not infer exact HTTP code.',
    'application_http_status': 422, 'json_parsing': True, 'plan_validation': False,
    'rejection_reason': 'arbitrary_narration_field', 'semantic_validation': 'candidate_rejected: structured_contract_failure; application safe_nonresolution',
    'accepted': False, 'published': False, **{k: completion[k] for k in ('attempt_id','input_tokens','output_tokens','total_tokens','latency_ms','completion_status')},
    'selected_catalog_identifiers': None, 'selected_catalog_identifiers_note': 'Response has no selected_entries plan; declaration IDs are not plan selections.'}
save('request_review.json', [request])
save('opening_evidence_index.json', {'initial_campaign': 'live_run/baseline/persistent/campaign.json',
    'post_initialization_state': 'live_run/baseline/documents.json',
    'after_opening_attempt': 'live_run/opening/documents.json', 'final_state': 'live_run/after/documents.json',
    'pre_initialization_state': 'No distinct pre-reset runtime snapshot; pinned bootstrap data and isolation provenance preserved in live_run/data/.atgb-isolated.',
    'public_catalog': 'Exact request payload/catalog not captured; do not reconstruct as observed evidence.',
    'provider_plan': 'Absent; bounded parsed response capture is a legacy narration envelope.',
    'engine_rendered_opening': 'None: presentation plan rejected before successful rendering.',
    'validation': 'live_run/diagnostics/provider_usage.jsonl',
    'player_facing_opening': 'None published; HTTP 422 error only.',
    'renderer_trace': 'Worker ready.json attests enabled; provider diagnostic attests opening_presentation contract. No successful render trace exists.'})

from tools.playtest.analysis import normalized_document
from tools.playtest.gameplay import diff
before, after = (read(LIVE/f'{phase}/documents.json') for phase in ('baseline','after'))
normalized = lambda docs: {k: normalized_document(k,v)[0] for k,v in docs.items()}
changes = diff(normalized(before), normalized(after))
save('state_review.json', {'comparison': r['state_comparison'], 'all_normalized_changes': changes,
    'review': {'location': 'frontier_gate unchanged', 'inventory_currency': 'character.json unchanged',
    'time': 'Day 1; turn delta 0', 'quests_relationships_world_facts': 'world.json unchanged; no overlay changes',
    'combat': 'Only harness-classified bookkeeping changes; see normalized diff',
    'published_unsupported_consequential_narration': 'None: no narration published',
    'scope': 'Rejected opening only; ordinary-turn authority untested'}})

report('PR_PLAY_17_PREFLIGHT.md', '''# PR-PLAY-17 Preflight

**PASS for execution qualification.** Current session: Workspace Write, network access enabled, auto_review approval policy; Windows PowerShell and Python 3.12.0 in the repository venv. Workspace writes empirically verified by these artifacts. No escalation required. These are effective session instructions, not an inference from a configuration file. See environment.json.

One IPv4 127.0.0.1 TCP test passed listener creation, bind/listen, client connect, bidirectional payload exchange, close and port rebind. Zero provider calls. See loopback.json. This verifies local TCP; outbound provider connectivity was established later by the one authorized live request, without probes.

One actual offline worker startup cycle passed: HTTP GET /api/state 200 in 1.875 seconds; http_ready.json generated; isolated worker PID 32340 terminated and port 52724 released. Journal contains initialization only, zero dispatches and zero player actions. The PR-PLAY-15 stop-at-readiness controlled KeyboardInterrupt intentionally produces a BLOCKED/incomplete scenario report; it is not a failed readiness check. See offline_readiness.json and offline_run/diagnostics/.

An earlier evidence-driver invocation was rejected before worker creation because I chose artifacts/pr_play_17 as the isolated store root. The harness correctly requires artifacts/atgb or development/tmp. This invocation mistake was corrected without changing safeguards; initial_invocation_readiness.json and initial_rejected_invocation/ preserve it. It was not a startup cycle or live attempt. No worker startup was retried after failure.

Provider configuration: credentials present (boolean only); default, high-precision and escalation routes all gpt-4.1-mini. Request ceiling 6; aggregate input/output/total ceilings 200000/20000/220000. Existing opening output allowance 3000. SDK retries 0, host retries 0; no fallback, judges or provider probes. No settings changed.

ASHEN_OPENING_RENDERER=1 was scoped to execution processes. Both offline and actual live workers attest enabled/selected in ready.json. Live capture enabled. Live worker HTTP readiness also passed in 1.938 seconds. No permanent configuration/environment changes. See safe_configuration.json and live_run/diagnostics/ready.json.
''')
report('PR_PLAY_17_LIVE_EXECUTION.md', r'''# PR-PLAY-17 Live Execution

Executed once in PowerShell, with scoped renderer flag and restoration in finally:

```powershell
$previousRenderer = $env:ASHEN_OPENING_RENDERER
try {
    $env:ASHEN_OPENING_RENDERER = '1'
    .\scripts\run_live_playtest.ps1 -Scenario FiveTurnGameplay -Mode Live -AuthorizeLiveProvider -CaptureResponse *>&1 | Tee-Object -FilePath artifacts/pr_play_17/live_console.txt
} finally { $env:ASHEN_OPENING_RENDERER = $previousRenderer }
```

The launcher's parameter contract was read before execution. Run ID: 20261101T153625Z-02fc6545bc28. Live invocations **1**, actual dispatched provider requests **1**, completed provider transports **1**. No synthetic live results. New Campaign returned 200; baseline capture succeeded. Start Campaign returned **422**, opening_failure_reason **arbitrary_narration_field**. Opening rejected; zero commits. Player turns attempted **0**, completed **0**, T1–T5 skipped. No rerun or repairs.

Earliest decisive failure: **Opening presentation-plan compliance**, a provider response format failure. Response was parseable JSON but contained narration/player_facing_text and declared_claims rather than selected_entries. Native diagnostic classification missing_structured_envelope is broader than the specific renderer rejection. Candidate then failed structured_contract_failure; application safe_nonresolution did not become an accepted opening. This is not a provider connection failure or budget exhaustion. Application refused publication and preserved state. Underlying cause of model noncompliance is not established.

See request_review.json, live_run/reports/result.json, live_run/diagnostics/provider_usage.jsonl and live_run/opening_response_evidence/. Exact provider HTTP status was not persisted; application 422 is not the provider HTTP status. Cleanup stopped owned PID 32648; independent port rebind passed (live_cleanup.json). Original harness evidence/evidence.zip preserved.
''')
report('PR_PLAY_17_GAMEPLAY_REVIEW.md', '''# PR-PLAY-17 Gameplay Review

**Technical result: opening prerequisite failed. Gameplay quality: not established.** No accepted engine opening and no ordinary player interaction occurred.

The pinned starting state places Galinor at frontier_gate on Day 1, turn 0, campaign_started=false. Public campaign context is grim political intrigue in a struggling frontier city. Baseline campaign, scene and world snapshots are reviewer evidence and can contain GM-only information; they are not player-facing excerpts.

The rejected provider candidate locates the scene at Cinderwatch's eastern gate and describes rain, crowded arrivals, guards, notices and possible social contacts. As an unpublished candidate it has a coherent scene and implicit opportunities, but this cannot establish accepted-opening quality or fidelity to the authorized public catalog. No structured-format penalty is applied: the failure is the wrong contract, not structured presentation. Exact outgoing catalog is absent from native evidence. No full candidate prose is reproduced in player-facing excerpts.

T1 observation, T2 serjeant conversation, T3 notice-board examination, T4 patrol investigation and T5 entry attempt were all skipped at the opening prerequisite. Their planned inputs are preserved in live_run/configuration/scenario.json; none has a pre-turn state, response, accepted/rejected mutation or narration because none was attempted. NPC responsiveness, later continuity, new information, changed circumstances, consequences and meaningful progression are untested.

The rejected response includes one incidental environmental improvisation proposal. It was not accepted or published; this does not demonstrate ordinary-turn improvisation. No evidence establishes a consequential fabricated outcome. Rejection for narration fields is not evidence that every candidate detail violates authority.

State review: no unexpected gameplay mutations or overlay changes; location frontier_gate, Day 1 and turn 0 preserved, campaign not started, log delta 0. Character inventory/currency and world facts unchanged. Session/combat bookkeeping changes are detailed in state_review.json. No accepted quest, NPC relationship or combat progression. No published narration exists to contradict state. Authority guard held for this rejected opening; ordinary-turn integrity remains untested.
''')
report('PR_PLAY_17_PERFORMANCE.md', '''# PR-PLAY-17 Performance

| Metric | Observed |
|---|---:|
| Live dispatched requests | 1 / 6 ceiling |
| Successful provider transport/completion | 1 |
| Failed provider transport | 0 |
| Accepted gameplay responses | 0 |
| Contract-rejected responses | 1 |
| Input tokens | 26,986 |
| Output tokens | 2,050 |
| Total tokens | 29,036 |
| Total provider latency | 14.189359 s |
| Average request latency | 14.189359 s |
| Longest request latency | 14.189359 s |
| Harness wall-clock execution | 18.906 s |
| Completed player turns | 0 |
| Requests per completed turn | Undefined (zero denominator) |

The provider completed without output truncation; opening allowance remained 3000. Aggregate ceilings unchanged at input/output/total 200000/20000/220000. Five request admissions remained unused; no budget exhaustion. No retries, fallback, judges or probes. Token/latency evidence comes from native completed ledger record, not synthetic estimates; see request_review.json and live_run/diagnostics/provider_usage.jsonl.

One opening response took about 14.2 seconds at the provider and failed publication. This is a noticeable wait, and did not deliver a usable interactive result. Ordinary-turn latency and steady-state interactive suitability cannot be assessed from this one failed opening. No reliable current pricing was consulted; monetary cost not estimated. Harness wall time excludes qualification, review and archive construction.
''')
report('PR_PLAY_17_FINDINGS.md', '''# PR-PLAY-17 Findings

## Confirmed defects

The live opening integration produced an incompatible response: parseable legacy narration envelope instead of opening_presentation selected_entries. Native rejection arbitrary_narration_field, structured validation false, HTTP 422 and zero opening commits confirm a blocker to gameplay in this run. This is an observed opening-contract failure; it does not establish that renderer implementation or validators are defective. The guard correctly rejected the candidate. No deterministic authority breach was observed.

## Suspected defects

Competing legacy narration/schema instructions or incomplete provider contract alignment may explain the legacy envelope. This is a hypothesis only. Exact outgoing request messages/schema are not preserved here, and no causal reproduction was attempted.

## Non-defect limitations

Six requests cannot guarantee five ordinary turns; no exhaustion occurred. Structured presentation is acceptable. Loopback and readiness passed; prior network denial was not reproduced. Application's skipped-upstream-preflight banner is intentional harness configuration, not proof that the actual captured production request was synthetic. Offline controlled unwind is expected. The initial evidence-driver isolation-root mistake was rejected safely and corrected before worker startup.

## Evidence gaps

Exact provider HTTP status, raw outgoing messages, authorized catalog index and complete raw provider wire text are not captured. Bounded parsed candidate is present and untruncated. No selected catalog identifiers, accepted render trace, player-facing opening or ordinary-turn snapshots exist because opening failed. Pre-reset runtime snapshot was not separately captured; post-reset baseline and pinned provenance exist. Browser UI was not tested. Single-run evidence does not establish failure frequency or prompt root cause.

## Recommended investigations

Inspect the actual opening request's combined message instructions and response-format/schema selection against the opening_presentation contract, using offline evidence first. Preserve exact outgoing catalog/schema metadata in any separately authorized follow-up. Do not relax validation to accept arbitrary prose. No repair or further execution was performed in this pass.
''')
report('PR_PLAY_17_FINAL_VERDICT.md', '''# PR-PLAY-17 Final Verdict

**Status: BLOCKED. Overall verdict: C — BLOCKED BY CONFIRMED DEFECT.** The confirmed defect is observed opening-contract noncompliance in the live integration; its underlying implementation/prompt cause is not established.

1. Environment qualification passed: effective Workspace Write networking, successful local TCP exchange; outbound provider transport subsequently succeeded.
2. HTTP readiness succeeded offline and live; offline /api/state 200 in 1.875 s, live in 1.938 s.
3. Live provider returned a valid opening plan: **No**. JSON parsed but plan contract failed.
4. Engine published an accepted opening: **No**; HTTP 422, no commit.
5. Opening coherent/actionable: no accepted opening to assess; unpublished candidate is scene-coherent with implicit opportunities.
6. Any live player turn complete: **No**.
7. Turns completed: **0**, attempted **0**.
8. Meaningful NPC interactions: not tested.
9. Narration consistent with deterministic state: no published narration; rejected-opening state preserved. Ordinary turns untested.
10. Authority violations observed: **No**; fail-closed rejection worked.
11. Performance acceptable: not established for gameplay. One request 14.189 s; execution 18.906 s; no playable result.
12. Stop reason: opening presentation-plan compliance failure, arbitrary_narration_field (harness structured_envelope_failure).
13. Highest-priority next step: inspect opening request instruction/schema alignment to determine why GPT-4.1 mini returned the legacy narration envelope instead of selected_entries.

One live invocation, one provider request, zero retries/judges/probes/reruns. No application edits, commits or push. Evidence packaged for external review. Stop here; PR-PLAY-18 not begun.
''')

snapshot_files = ['scripts/run_live_playtest.ps1','tools/playtest/runner.py','tools/playtest/worker.py',
    'tools/playtest/validate_startup.py','tools/playtest/gameplay.py','tools/playtest/scenarios/FiveTurnGameplay.json',
    'game/gm.py','game/api.py','game/opening_presentation_renderer.py','game/provider_budget.py',
    'game/config.py','tools/atgb/isolation.py','docs/state_authority_model.md']
for name in snapshot_files:
    dest = OUT/'source_snapshots'/name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/name, dest)
(OUT/'repository_status.txt').write_text(subprocess.check_output(['git','status','--short'], cwd=ROOT, text=True), encoding='utf-8')
save('repository.json', r['repository'])

# Package only current-pass files. Never include .env or credential configuration.
from dotenv import dotenv_values
secret_values = {v for k,v in {**dotenv_values(ROOT/'.env'), **os.environ}.items()
    if v and len(v)>8 and any(marker in k.lower() for marker in ('api_key','secret','password','credential','access_token','auth_token'))}
def check_bytes(data, label):
    for value in secret_values:
        if value.encode() in data:
            raise RuntimeError('Credential value found in '+label)
    if data.startswith(b'PK\x03\x04'):
        with zipfile.ZipFile(io.BytesIO(data)) as nested:
            assert nested.testzip() is None
            for name in nested.namelist():
                check_bytes(nested.read(name), label+'!'+name)

# Current user date is after the 2026-11-01 New York DST fallback (UTC-05).
stamp = datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
archive = ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
files = []
for base, prefix in [(OUT, 'pr_play_17'), (LIVE,'pr_play_17/live_run'),
                     (Path(offline['run']), 'pr_play_17/offline_run')]:
    for p in sorted(base.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or p.name in {'archive_verification.json','archive_path.txt','manifest.json'}:
            continue
        rel = p.relative_to(base)
        if base == OUT and rel.parts[0] == 'offline_startup':
            name = 'pr_play_17/initial_rejected_invocation/'+'/'.join(rel.parts[1:])
        else:
            name = prefix+'/'+rel.as_posix()
        data = p.read_bytes()
        check_bytes(data, name)
        files.append((p,name,data))
manifest = [{'path': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for _,name,data in files]
save('manifest.json', manifest)
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for _,name,data in files:
        z.writestr(name,data)
    z.write(OUT/'manifest.json','pr_play_17/manifest.json')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for entry in manifest:
        assert hashlib.sha256(z.read(entry['path'])).hexdigest() == entry['sha256']
    for required in ['PREFLIGHT','LIVE_EXECUTION','GAMEPLAY_REVIEW','PERFORMANCE','FINDINGS','FINAL_VERDICT']:
        assert f'pr_play_17/PR_PLAY_17_{required}.md' in z.namelist()
verification = {'archive': str(archive.resolve()), 'readable': True, 'crc_test': 'PASS',
    'sha256_manifest_test': 'PASS', 'entries': len(manifest)+1, 'bytes': archive.stat().st_size,
    'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'credential_value_scan': 'PASS including nested archives',
    'scope': 'Current pass, native live/offline harness evidence and relevant source snapshots only'}
save('archive_verification.json', verification)
(OUT/'archive_path.txt').write_text(str(archive.resolve())+'\n',encoding='utf-8')
print(json.dumps(verification, indent=2))
