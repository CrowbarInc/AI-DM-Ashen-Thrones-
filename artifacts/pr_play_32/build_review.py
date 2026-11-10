"""Package the stopped PR-PLAY-32 experiment; never invokes the provider."""
import json, hashlib, zipfile, subprocess, socket, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
RUN=ROOT/'artifacts/atgb/pr_play_32/live'
def read(p):return json.loads(p.read_text())
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2,default=str)+'\n',encoding='utf-8')
def report(name,text):(OUT/('PR_PLAY_32_'+name+'.md')).write_text('# PR-PLAY-32 '+name.replace('_',' ').lower()+'\n\n'+text.strip()+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
fixture=read(OUT/'fixture_verification.json');repo=read(OUT/'repository.json');result=read(OUT/'live_result.json')
ready=read(RUN/'diagnostics/ready.json');poll=[json.loads(s) for s in (RUN/'diagnostics/readiness_poll.jsonl').read_text().splitlines()]
ledger=[json.loads(s) for s in (RUN/'diagnostics/provider_usage.jsonl').read_text().splitlines()]
dispatched=[e for e in ledger if e.get('event')=='dispatched']
assert not dispatched and not list((RUN/'diagnostics').glob('request_*.json'))
assert not (OUT/'live_attempt_authorized_once.json').exists()
assert not result['steps'] and not result['turns']
sources={p:sha(ROOT/p) for p in repo['source_hashes']}
source_check=dict(unchanged=sources==repo['source_hashes'],before=repo['source_hashes'],after=sources)
write('source_integrity.json',source_check);assert source_check['unchanged']
subprocess.run(['git','status','--short'],cwd=ROOT,stdout=(OUT/'git_status_after.txt').open('w'),check=True)
# Read-only OS verification: the attested child and owned launcher have exited.
proc=subprocess.run(['powershell','-NoProfile','-Command',f"Get-Process -Id {ready['pid']},{poll[0]['pid']} -ErrorAction SilentlyContinue | Select-Object Id,ProcessName | ConvertTo-Json"],capture_output=True,text=True)
cleanup=dict(launcher_pid=poll[0]['pid'],attested_pid=ready['pid'],remaining_processes=proc.stdout.strip() or [],controller_cleanup=result['cleanup'])
write('cleanup_verification.json',cleanup)
try:
    with socket.create_connection(('127.0.0.1',ready['port']),timeout=1):port_released=False
except OSError:port_released=True
cleanup['port_released']=port_released;write('cleanup_verification.json',cleanup)
tests=ET.parse(OUT/'preflight_tests.xml').getroot().find('testsuite');recheck=ET.parse(OUT/'preflight_recheck.xml').getroot().find('testsuite')
write('test_summary.json',dict(initial=tests.attrib,recheck=recheck.attrib,interpretation='131 passed, one setup error; affected case passed on one offline recheck; zero assertion failures. No live-provider retries.'))
write('provider_request_ledger.json',dict(requests=[],actual_outbound_requests=0,input_tokens=0,output_tokens=0,total_tokens=0,provider_latency_seconds=0,retries=0,fallback_model_requests=0,ai_judge_calls=0,source='Native ledger contains accounting initialization only; no dispatch wrapper records; controller never reached any HTTP action.'))
write('network_readiness.json',dict(status='FAIL / NOT ESTABLISHED',socket_bound=True,http_reachable=None,reason='Readiness attestation rejected before production HTTP probe',expected_pid=poll[0]['pid'],attested_pid=ready['pid'],port=ready['port']))
write('state_integrity_checks.json',dict(live_campaign_initialized=False,player_actions=0,provider_requests=0,gameplay_evaluation='NOT RUN',runtime_session_created=(RUN/'data/session.json').exists(),fixture_files_unchanged={n:sha(RUN/'data'/n)==v for n,v in fixture['manifest']['files'].items()},source_unchanged=source_check['unchanged'],canonical_campaign_reset=False))
stop='Critical harness readiness failure before production HTTP access: controller PID '+str(poll[0]['pid'])+' differs from ready.json PID '+str(ready['pid'])+'. runner.wait_for_http_ready rejected the attestation with RuntimeError: Isolation attestation mismatch.'
report('PREFLIGHT',f'''
**STOP BEFORE LIVE REQUESTS — preflight did not pass.**

Repository revision: `{repo['revision']}`. Inherited working tree is heavily dirty, including earlier gameplay repairs and historical artifact changes/deletions. Full status is in git_status_before.txt; game/tools source hashes were unchanged during the server attempt (source_integrity.json). No gameplay, campaign content, fixture, commit or push changes made by this pass.

Fixture: `{fixture['identifier']}`, strict verification PASS. Manifest SHA-256 `{fixture['manifest_sha256']}`; source revision `{fixture['manifest']['source_revision']}`. Full file digests in fixture_verification.json. Tavern Runner, patrol_rumor rumor metadata, separate rumor/physical clues, authored patrol exit, Old Milestone and prints interactable are present in the pinned fixture. Isolated copied files match the manifest; no knowledge injected.

Provider: OpenAI Responses, configured gpt-4.1-mini; credentials available (value never printed). All configured routing models resolve to that same model. Existing 45-second provider timeout; 110-second controller action timeout. Native limits 10 requests / 200000 input / 20000 output / 220000 total tokens. SDK retries 0, host retries 0; dispatch observer enforces model and request ceiling. No fallback model or judge requested. No outbound provider connectivity probes.

Opening: ASHEN_OPENING_RENDERER=1; worker attests enabled/selected. No opening generated.

Security/conversation/exploration: 132 focused offline cases selected across purpose routing, response confidentiality, privileged reads and expression recovery. 131 passed; one WinError 5 setup error while replacing test session.json. That isolated case passed on one offline recheck. No assertion failures. Existing PR-PLAY-31 offline integration was inspected, not presented as new live evidence. Native validators/evaluators remain enabled.

Network/harness: {stop} A loopback socket bound, but endpoint reachability was not established. Readiness guard remained enabled; no initialization or action was submitted. Configured provider accounting initialized but never dispatched. Recoverable expression-rejection classification is covered offline; live state/confidentiality evaluation is NOT RUN.

Harness assembly limitations: initial proposed data path was refused by the existing storage guard and corrected to its required artifacts/atgb path before startup. A quoting error in the first artifact-only edit command changed nothing. The corrected launch then failed process attestation. No second worker was launched, no campaign reset, and no readiness guard was bypassed. Stop honored; no live retry. Owned launcher and attested child are absent at cleanup; socket release result: {port_released}.

Decision: FAIL readiness; **D — INCONCLUSIVE** for gameplay. Do not repair or relaunch in this pass.
''')
actions=["I approach the tavern runner and ask what they're offering.",'What sort of rumors have you heard?','I head northwest of the crates to investigate the muddy footprints.','I go to Follow the missing patrol rumor.','I examine the footprints.']
report('SCENARIO','\n\n'.join(f'{i}. "{a}"' for i,a in enumerate(actions,1))+'''

One disposable campaign, one continuous session, production Player HTTP API, configured live provider; maximum ten actual outbound requests, no retries/fallback/judges. Opening reserve 1; planned T1/T2/T3/T4/T5 conservative reserves 2/2/1/1/2 (9 total); next action must fit before submission. Every dispatch counts, including failures. Actual budget decision: preflight STOP, do not submit opening or any action; 10 remain unused.

Expected transitions: accepted opening at frontier_gate with Tavern Runner -> authorized public-fact offerings -> authored patrol_rumor disclosure and persisted muddy_footprints_northwest -> northwest-of-crates destination plus separate investigation purpose -> actionable public-route clarification with no progression -> explicit authored patrol route -> old_milestone with unresolved intention, no physical clue -> prints examination and separate milestone_mud_prints discovery. Ordinary authorized actions advance time by one; clarification advances zero.

Continuation gates require useful authorized answers, persisted rumor clue, actionable patrol-route clarification, correct destination, preserved intention, authorized physical discovery, integrity and confidentiality. Stop on critical preflight failure, opening rejection, wrong target, generic uncertainty, clue absence, incorrect routing, invented travel/evidence, hidden disclosure, integrity failure or insufficient remaining budget. Successful HTTP alone is insufficient. All five actions and a coherent player experience are necessary for verdict A. No action was submitted.
''')
report('LIVE_TRANSCRIPT','**No live transcript exists.** Preflight stopped before /api/new_campaign, /api/start_campaign or /api/chat. Actual published opening: none. Executed player actions: none. Semantic completion: NOT EVALUATED. No mocked or historical dialogue substituted.')
report('CONVERSATION_AUTHORITY','''Live target resolution, public-fact selection, topic discovery, disclosure authorization, expression behavior and clue discovery: NOT OBSERVED. No NPC was contacted. Expected authority chain is public scene offering -> disclosure-authorized authored patrol_rumor -> engine-recorded muddy_footprints_northwest; this remains an expectation, not a live result. Offline expression/public-projection tests and prior PR-PLAY-31 evidence do not establish live continuity.''')
report('ROUTE_AND_INTENTION','''NOT EXECUTED. Expected destination: northwest of the crates; purpose: investigate the muddy footprints; referenced clue: muddy_footprints_northwest. Authored public route: Follow the missing patrol rumor -> old_milestone. No direct equivalence between rumor and milestone evidence is authored. Actual router decision, route candidates/visibility/prerequisites, clarification, selected route, deferred intention and scene transition: unavailable because no action was submitted. No route was forced.''')
report('INVESTIGATION','''NOT EXECUTED. No arrival scene or live examination exists. Fixture contains Old Milestone prints interactable with milestone_mud_prints authored discovery, distinct from muddy_footprints_northwest. No resolver executed, physical clue was not discovered, mutation provenance is unavailable. No target identifier was sent to the provider; no clue identity was merged.''')
report('STATE_INTEGRITY','''No campaign initialized, no before/after gameplay snapshots or turn diffs exist. The isolated bootstrap is preserved under evidence/live/data; state_integrity_checks.json verifies every bootstrap file against the pinned manifest, no runtime session and no submitted mutations. Canonical player campaign was not reset. Relevant game/tools hashes are unchanged. Live character, inventory, currency, conditions, quests, relationships, scene, clock, events, logs and overlays: NOT EVALUATED. No rumor or physical discoveries were injected.

Offline security controls passed, including the one setup-error recheck. Live confidentiality: NOT EVALUATED (no player-facing response). No leakage was observed because no response was produced; this is not a live confidentiality PASS. Internal diagnostics remain under evidence/live/ and are separate from the empty player transcript. No validators disabled.''')
report('DIALOGUE_QUALITY','''No actual opening, dialogue, clarification, travel or examination narration was produced. Each requested quality dimension—conversational relevance, conversational continuity, investigation continuity, clarification quality, travel narration, investigation narration, narrative consistency, agency, pacing, mechanical leakage and overall playability—is **NOT EVALUATED**. PASS/PARTIAL/FAIL cannot be assigned honestly without transcript evidence. Gameplay success and failure are both unestablished; overall experiment verdict D reflects instrumentation, not dialogue quality.''')
report('PERFORMANCE',f'''Actual outbound provider requests: **0/10**. Input/output/total tokens: **0/0/0**. Provider latency: 0 seconds; no per-request entries exist. Production HTTP requests: 0; API latencies and requests/tokens per gameplay turn: not applicable. Server attempt duration including cleanup: {result['duration_seconds']:.3f} seconds. Offline focused suite: {tests.attrib['time']} seconds; isolated recheck: {recheck.attrib['time']} seconds. These are separate timings, not fabricated total live gameplay duration.

Retries: 0 provider, 0 host, 0 SDK. Fallback model calls: 0. AI judges: 0. One offline test recheck is not a provider retry. Budget utilization: 0%; ceiling respected. Ledger evidence records accounting initialization only; no dispatch or usage response exists. Request acceptance/publication and per-request token usage are not applicable. Total experiment wall span, including preparation and report assembly, is recorded in experiment_timing.json. No live sequence duration can be measured.''')
report('FAILURE_ANALYSIS',f'''First failed boundary: **process ownership/isolation attestation during harness readiness**. {stop}

Evidence: live/diagnostics/readiness_poll.jsonl worker_spawned and attestation_mismatch; ready.json reports correctly isolated data path, model, retry settings and renderer but a different PID. execute.py launches sys.executable from .venv; unlike the prior PR-PLAY-29 controller it does not select sys._base_executable. A Windows virtual-environment launcher creating a child interpreter is the likely explanation. This is an evidence-supported inference; process ancestry was not captured, and CIM process inspection was unavailable. The exact fact established is PID mismatch, not corrupted campaign isolation.

Classification: experiment instrumentation/environment, not provider or gameplay. This pass's artifact controller introduced a launcher choice inconsistent with the prior working controller; no new product defect is established. Secondary observations: initial unsafe harness storage location refused; one offline security-test setup hit the previously documented WinError 5 and passed on recheck. Neither is evidence of failed live gameplay.

No provider error, parsing error, wrong target, route defect, clue-authority failure or dialogue defect was observed live. No repairs made. Recommended next investigation: review launcher/process ownership in the harness offline using the prior base-interpreter pattern, retaining strict attestation, before separately authorizing a fresh bounded live attempt. Do not launch PR-PLAY-33 automatically.

Procedural limitations: correct fixture verified and evidence packaged, but required live initialization/transitions were not performed because mandatory preflight failed. This is a completed stop report, not completion of the requested live gameplay validation.''')
answers=[
'No; harness readiness failed.',
'Correct pinned fixture verified and isolated bootstrap copied; no live campaign initialized.',
'Not attempted.', 'Not attempted.', 'Not evaluated live.', 'Not attempted.', 'Not evaluated live.',
'No live discovery; not attempted.', 'Not evaluated.', 'Not evaluated live.', 'Not attempted.',
'No Turn 3 submitted; no progression occurred.', 'Not attempted.', 'Not attempted.', 'Not evaluated live.',
'Not evaluated live.', 'Not attempted.', 'No.', 'No live discovery.',
'Fixture identifiers are distinct; live separation not evaluated.',
'No consequential gameplay mutations submitted; live mutation authority not evaluated.',
'Live evaluator not run; bootstrap hashes pass.', 'Live evaluation not run; offline security checks pass.',
'Not evaluated; no transcript.', 'Not evaluated; no player choices offered.', '0.', '0 input, 0 output, 0 total.',
'No provider retries; one offline test setup recheck.', 'Yes, 0/10.',
'Process PID/isolation attestation before HTTP readiness.',
'No; playable live sequence is unestablished.',
'Investigate Windows launcher/process ownership and readiness offline; do not auto-start PR-PLAY-33 or rerun live.'
]
report('FINAL_VERDICT','**INCONCLUSIVE — D.** Mandatory preflight stop; no campaign or actions executed.\n\n'+ '\n\n'.join(f'{i}. {a}' for i,a in enumerate(answers,1))+'\n\nNo commit, push, gameplay repair, fixture modification, repeated opening, campaign reset, provider retry or subsequent pass. Await external review.')
# Evidence timing uses client timezone for filenames and dates.
# This stopped run occurred after the 2026-11-01 New York DST transition.
client_tz=timezone(timedelta(hours=-5),'America/New_York (EST)')
now=datetime.now(client_tz)
start=datetime.fromtimestamp((OUT/'execute.py').stat().st_ctime,client_tz)
write('experiment_timing.json',dict(preparation_started=start.isoformat(),report_assembled=now.isoformat(),wall_span_seconds=(now-start).total_seconds(),server_attempt_seconds=result['duration_seconds'],note='Preparation span begins at first controller artifact creation; initial request-reading time excluded.'))
# Search only evidence that will be packaged; never serialize credential values.
from dotenv import dotenv_values
import os
env={**dotenv_values(ROOT/'.env'),**os.environ}
secrets=[v for k,v in env.items() if isinstance(v,str) and len(v)>8 and any(s in k.lower() for s in ('key','secret','token','password','credential'))]
included=[p for p in OUT.rglob('*') if p.is_file() and 'live' not in p.relative_to(OUT).parts and '__pycache__' not in p.parts and p.name not in ('archive_path.txt','archive_verification.json','MANIFEST.json','credential_scan.json')]
included+=list(p for p in RUN.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
hits=[str(p.relative_to(ROOT)) for p in included if any(s.encode() in p.read_bytes() for s in secrets)]
write('credential_scan.json',dict(files_scanned=len(included),credential_hits=hits,passed=not hits));assert not hits
included.append(OUT/'credential_scan.json')
manifest={str(p.relative_to(ROOT)):sha(p) for p in included};write('MANIFEST.json',manifest);included.append(OUT/'MANIFEST.json')
archive=ROOT/'handoff'/('CURRENT_REVIEW('+now.strftime('%Y%m%d-%H%M%S')+').zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in included:
        name='evidence/live/'+str(p.relative_to(RUN)).replace('\\','/') if p.is_relative_to(RUN) else str(p.relative_to(OUT)).replace('\\','/')
        z.write(p,name)
with zipfile.ZipFile(archive) as z:
    bad=z.testzip();assert bad is None
    verification=dict(path=str(archive),entries=len(z.namelist()),bytes=archive.stat().st_size,sha256=sha(archive),testzip=bad,readable=True)
write('archive_verification.json',verification);(OUT/'archive_path.txt').write_text(str(archive))
print(json.dumps(verification))
