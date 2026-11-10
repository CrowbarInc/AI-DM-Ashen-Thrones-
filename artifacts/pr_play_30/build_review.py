"""Package PR-PLAY-30 observations only; never invokes gameplay or a provider."""
import hashlib,json,os,shutil,socket,subprocess,zipfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
import sys
sys.path.insert(0,str(ROOT))
from tools.atgb.baseline import load_baseline,digest
from game.state_channels import is_author_key
from game.world import advance_world_tick
from dotenv import dotenv_values
OUT=Path(__file__).parent
def save(n,x): (OUT/n).write_text(json.dumps(x,indent=2,default=str)+'\n',encoding='utf-8')
def report(n,s): (OUT/('PR_PLAY_30_'+n+'.md')).write_text(s.strip()+'\n',encoding='utf-8')
run=json.loads((OUT/'offline_run.json').read_text());rows=run['turns']
opening=json.loads((OUT/'opening.json').read_text())
revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
status=subprocess.check_output(['git','status','--short'],text=True)
(OUT/'git_status_after.txt').write_text(status,encoding='utf-8')
(OUT/'git_status_inherited.txt').write_text('\n'.join(s for s in status.splitlines() if 'pr_play_30' not in s)+'\n',encoding='utf-8')
base,manifest=load_baseline(ROOT)
fixture=dict(identifier='frontier-gate-v1',manifest_sha256=digest(base/'manifest.json'),source_revision=manifest['source_revision'],files={n:digest(base/n) for n in manifest['files']},strict_verification=True)
save('fixture_verification.json',fixture)
for name in ['manifest.json',*manifest['files']]:
 d=OUT/'verified_fixture'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/name,d)
previous=json.loads(Path('artifacts/pr_play_29/source_hashes_after.json').read_text())
hashes={p:digest(ROOT/p) for p in previous}
changed=[p for p in previous if previous[p]!=hashes[p]]
save('source_hash_verification.json',dict(reference='PR-PLAY-29 source_hashes_after.json',paths_checked=len(previous),changed=changed,sha256=hashes,commits=0,pushes=0))
assert not changed,changed
config={**dotenv_values(ROOT/'.env'),**os.environ}
safe={k:config.get(k) for k in ['MODEL_NAME','DEFAULT_MODEL_NAME','HIGH_PRECISION_MODEL_NAME','RETRY_ESCALATION_MODEL_NAME','ENABLE_MODEL_ROUTING']}
save('safe_configuration.json',dict(provider='OpenAI Responses',model_configuration=safe,credentials_present=bool(config.get('OPENAI_API_KEY')),opening_renderer='ASHEN_OPENING_RENDERER=1 in harness',live_requests=0,live_gate='NO-GO',external_network='Not probed: offline gate failed',production_api='FastAPI TestClient HTTP 200 for opening and three actions',budget_ceiling=7,retries=0,fallback_models=0,ai_judges=0))
with socket.socket() as s:
 s.bind(('127.0.0.1',0));s.listen(1)
 with socket.create_connection(s.getsockname(),timeout=2) as c:
  other,_=s.accept()
  with other:c.sendall(b'PR-PLAY-30');assert other.recv(32)==b'PR-PLAY-30'
save('network_readiness.json',dict(loopback_exchange=True,external_provider_connectivity='Not tested; no live experiment justified',production_api_in_process=True))
sources={
 'game/conversational_orchestration.py':[(1000,1018),(1056,1064),(1110,1180),(1298,1345),(1485,1556)],
 'game/player_interpretation_bridge.py':[(1,80),(230,258),(287,310)],
 'game/local_interaction.py':[(1,82)],
 'game/live_chat_interpretation.py':[(300,325),(390,413)],
 'game/exploration.py':[(170,214),(291,345),(410,478),(1080,1160)],
 'game/skill_checks.py':[(170,222)],
 'game/storage.py':[(615,641),(873,922)],
 'game/clues.py':[(398,430)],
}
excerpts=[]
for p,ranges in sources.items():
 lines=(ROOT/p).read_text(encoding='utf-8').splitlines()
 for lo,hi in ranges:excerpts.append(dict(file=p,start=lo,end=min(hi,len(lines)),lines=[f'{i+1}: {lines[i]}' for i in range(lo-1,min(hi,len(lines)))]))
save('source_excerpts.json',excerpts)
for n in ['PR_PLAY_29_TRANSCRIPT.md','PR_PLAY_29_KNOWLEDGE_TRANSITION.md','PR_PLAY_29_CLUE_AUTHORITY.md']:
 d=OUT/'prior_evidence'/n;d.parent.mkdir(exist_ok=True);shutil.copyfile(Path('artifacts/pr_play_29')/n,d)
integrity=[]
for r in rows:
 b,a=r['before'],r['after'];i=r['turn']
 stable={k:b[k]==a[k] for k in ['character','campaign','combat','conditions']}
 expected=json.loads(json.dumps(b['world']))
 if i<3:advance_world_tick(expected,b['campaign'])
 world_match=a['world']==expected
 if i==2:
  actual=json.loads(json.dumps(a['world']));ae=actual.pop('event_log');ee=expected.pop('event_log')
  world_match=actual==expected and ae[:len(ee)]==ee and len(ae[len(ee):])==2
  added=ae[len(ee):]
 else:added=[]
 delta=a['session']['turn_counter']-b['session']['turn_counter']
 pressure=a['session']['clocks']['time_pressure']-b['session']['clocks']['time_pressure']
 check=dict(turn=i,stable_roots=stable,world_tick_and_authorized_events=world_match,added_world_events=added,turn_delta=delta,time_pressure_delta=pressure,active_scene=a['session']['active_scene_id'],overlay_comparison=r['evaluation']['overlay_comparison'],unauthorized_state_findings=[f for f in r['evaluation']['findings'] if f['category'] in ['unauthorized_state_mutation','hidden_information_disclosure']],changed_session_roots=[k for k in set(b['session'])|set(a['session']) if b['session'].get(k)!=a['session'].get(k)])
 check['pass']=all(stable.values()) and world_match and delta==pressure==(1 if i<3 else 0) and not check['unauthorized_state_findings']
 integrity.append(check)
assert all(x['pass'] for x in integrity)
save('state_integrity_checks.json',integrity)
hidden=[]
for p in (base/'scenes').glob('*.json'):hidden+=json.loads(p.read_text())['scene'].get('hidden_facts',[])
public=[opening['response'],*[r['response'] for r in rows]]
leaks=[]
for i,response in enumerate(public):
 raw=json.dumps(response)
 for h in hidden:
  if h in raw:leaks.append(dict(response=i,kind='exact_authored_hidden_fact'))
 def walk(x,path=''):
  if isinstance(x,dict):
   for k,v in x.items():
    if is_author_key(k):leaks.append(dict(response=i,kind='author_key',path=path+'/'+k))
    walk(v,path+'/'+k)
  elif isinstance(x,list):
   for j,v in enumerate(x):walk(v,path+'/'+str(j))
 walk(response)
save('confidentiality_verification.json',dict(pass_=not leaks,findings=leaks,public_responses=4,authored_hidden_values=len(hidden),security_controls_passed=29,manual_prose_review='No protected facts in opening or three published responses; exact scan is bounded, not a paraphrase proof.'))
assert not leaks,leaks
for r in rows:
 save(f'T{r["turn"]}_state_diff.json',r['state_diff'])
 save(f'T{r["turn"]}_evaluation.json',r['evaluation'])
save('semantic_stop.json',dict(turn=3,classification=rows[2]['classification'],decision=rows[2]['internal']['resolution']['metadata']['conversational_decision'],interpreter_invoked=False,resolver_invoked=False,narration_provider_invoked=False,subsequent_scenario_actions=0,live_go=False))
elapsed=run['elapsed_seconds'];times={f'T{r["turn"]}':r['latency_seconds'] for r in rows}
save('performance.json',dict(offline_elapsed_seconds=elapsed,opening_seconds=opening['latency_seconds'],action_seconds=times,live_requests=0,live_tokens=0,retries=0,fallback_models=0,ai_judges=0,mocked_interpretation_requests=2,mocked_opening_requests=len(opening['mock_requests']),mocked_expression_requests=len(run['expressions']),mock_tokens='Synthetic helper usage; not provider billing',budget_ceiling=7,budget_compliant=True))
common='Evidence: offline_run.json (complete public/internal turns, interpreter prompts, before/after snapshots and diffs), source_excerpts.json (numbered implementation excerpts), verified_fixture/ (strictly verified authored files).'
report('PREFLIGHT',f'''# PR-PLAY-30 preflight
Revision: {revision}. Inherited dirty working tree retained; git_status_inherited.txt records all entries excluding this pass. No commit/push. All {len(previous)} PR-PLAY-29 source/content hashes remain unchanged (source_hash_verification.json). Status capture was made after the observation harness; prior-pass hashes provide the independent implementation baseline.

Fixture: frontier-gate-v1; source revision {manifest['source_revision']}. Manifest SHA256 {fixture['manifest_sha256']}; world SHA256 {fixture['files']['world.json']}. Strict manifest and seven-file validation passed. All relevant scene digests are in fixture_verification.json.

Provider/model: OpenAI Responses; configured {safe.get('MODEL_NAME')}; safe_configuration.json records routing names and credential-presence boolean only. Harness selects ASHEN_OPENING_RENDERER=1. Zero actual provider dispatches. Mock SDK and interpretation/expression surfaces only. Host/SDK retry-disable settings installed by existing test fixture; fallback-model and judge calls zero. No model configuration changed.

API: unchanged production FastAPI endpoints available through TestClient; opening and all three ordinary submissions HTTP 200. Loopback socket exchange passed. External provider/network availability not probed because offline gate failed. No external readiness claim.

Security: 29/29 current confidentiality and privileged-read controls pass. Player mode only. Ordinary evaluator runs for each turn with authoritative snapshots; no integrity/confidentiality findings. The investigation's semantic failure is preserved, not waived.

Harness: verified authored fixture files copied into test-isolated storage after existing campaign-reset fixture creates runtime. No invented session/clue snapshot; opening and both conversation turns execute through production API. Turn 1/2 interpretation outputs are replayed from actual PR-PLAY-29 responses 02/04. The public offering expression and renderer plan are mocked; Turn 2 authored topic uses engine speech. PR-PLAY-29 capability reproduced offline.

Harness launch initially omitted tests.conftest and failed before gameplay because production_call_gpt was not captured. Loading that existing plugin corrected harness setup. No provider retry or implementation change. Correct command: `.venv/Scripts/python.exe -m pytest -p tests.conftest artifacts/pr_play_30/test_validation.py --basetemp=development/tmp/pr_play_30_run2 -q`.

Live budget readiness: ceiling seven, zero used. NO-GO at offline semantic gate; no live controller launched. No need to install or exercise a live seven-request admission guard when no live request is authorized by the gate.
''')
report('WORLD_AUDIT','''# PR-PLAY-30 world audit
The actual frozen campaign contains a related destination and physical prints. It does not establish that the runner's exact clue id is that physical target.

| Source | Identifier | Meaning / rules |
|---|---|---|
| verified_fixture/world.json | cinderwatch | Frontier city settlement; no local coordinates. |
| verified_fixture/scenes/frontier_gate.json | frontier_gate | Cinderwatch Gate District/eastern gate. Active social scene. |
| verified_fixture/world.json | tavern_runner / patrol_rumor | Same-scene NPC; public topic, discovery_categories=[rumor]; no skill or prerequisite. |
| same topic | muddy_footprints_northwest | Clue id attached to hearsay: “The runner heard the patrol vanished near muddy footprints northwest of the crates.” |
| frontier_gate discoverable_clues | notice_patrol_route | “The missing patrol was last seen taking the northwest mud track past the crates.” Discovered by notice_board investigation. |
| frontier_gate interactables | notice_board | Only authored physical investigation target in current scene; reveals notice_patrol_route. |
| frontier_gate exits | market_quarter / old_milestone | Labels “Enter Cinderwatch” / “Follow the missing patrol rumor”; ordinary scene topology, not coordinates. |
| old_milestone | prints / milestone | Existing physical investigation targets. prints aliases: footprints, mud, track, mud track, northwest track. Both reveal milestone_mud_prints. |
| old_milestone discoverable_clues | milestone_mud_prints | “Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.” |

Crates are mentioned only in topic/notice text; no crate object, coordinate, addressable landmark or local-area record. No footprint object in frontier_gate. Northwest is a relative description plus an authored mud-track destination at old_milestone. No authored foreign-key mapping from muddy_footprints_northwest to prints/milestone_mud_prints. No evidence allows equating them automatically.

Old Milestone visible facts explicitly show overlapping prints fading into scrub. Its sole exit returns to frontier_gate. Market Quarter returns to frontier_gate (see full scene). No added locations or content. world.clues is empty in fixture; clue knowledge is created through disclosure.

Footprint classification: exact rumor id = authored disclosure clue + discovered information/lead + narrative relative-location reference; NOT a local physical object, scene feature, destination, or interaction target. Separate destination prints = authored physical scene target and visible environmental evidence, with a distinct discoverable clue id. Distinguish the two.

Movement between scenes is supported by existing exits. No general coordinate/local-access solver. Same-scene approach normalization accepts tightly constrained matching ASK/INSPECT preambles and explicitly executes no movement; it cannot grant access to remote environmental evidence. A staged travel then inspection is plausible existing gameplay, but was not executed after the decisive stop and does not validate the required one-action investigation.
'''+common)
report('CLUE_CONTINUITY','''# PR-PLAY-30 clue continuity
PR-PLAY-29 and the offline reproduction disclose: “Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates.” Topic patrol_rumor authorizes clue muddy_footprints_northwest.

After Turn 2 session.clue_knowledge.muddy_footprints_northwest has state=discovered, source_scene=frontier_gate, presentation=explicit and the authored hearsay text. It remains byte-equivalent in Turn 3's before/after session. Overlay discovered clues, NPC topic memory, delivered conversation and lead_registry are preserved in offline_run.json. An actionable minimum exit lead minlead_exit_frontier_gate_old_milestone is also created; this names the existing rumor-following exit, not a footprint physical mapping.

HEARD_ABOUT: represented by disclosed topic and discovered clue text; no separate hearsay lifecycle. KNOWS_LOCATION: relative text only, plus separate exit lead. CAN_REACH: authored exits support scene transition, no local solver. CAN_SEE: current authored visible facts/interactables; old_milestone prints are remote until transition. CAN_EXAMINE: resolver matches current-scene interactables. EXAMINED: scene_runtime searched_targets / resolved interactables are separate from clue_knowledge. Discovery alone does not establish physical examination. No new persistent fields introduced.

Interpreter input is built from current visible catalog, two recent player-visible log turns, PUBLIC answer evidence and conversation ownership context (live_chat_interpretation.py:300-325,390-413). Thus prior disclosure can be available as speech context; the action bridge still requires a valid current target. It does not turn clue knowledge into inspectable entities. Actual Turn 3 never invokes interpreter: deterministic movement routing declines first. Referential comprehension by a model on Turn 3 is NOT TESTED.

The existing investigation resolver receives scene/session/world and can use existing knowledge/search state, but matches authored active-scene interactables for physical clue discovery. No mapping from disclosed id to prints is authored. Path established: NPC disclosure → persisted knowledge and exit lead. First missing link for exact action: relative clue reference → valid spatial destination/current target. The downstream remote prints mechanic exists, but was not invoked.
'''+common)
report('FEASIBILITY','''# PR-PLAY-30 feasibility
Exact candidate: “I head northwest of the crates to investigate the muddy footprints.”

Classification: UNSUPPORTED as a complete one-action investigation from frontier_gate. Related staged exploration is CONDITIONALLY FEASIBLE at the content level: follow the existing missing-patrol-rumor exit, arrive at old_milestone, then inspect its authored prints. That requires a prior scene transition and does not establish an authored identity relation between the rumor clue and milestone clue.

There is no current-scene footprint target/local crate area and no general local movement solver. Current footprint visibility/access cannot be inferred from having heard a rumor. old_milestone prints have a bounded authorized examination outcome with no configured skill check, but are not present in the current target catalog.

No alternative selected. “I look around the crates…” still lacks a current target. “Follow the missing patrol rumor” tests travel alone, not the same investigation. Using hidden destination ids or skipping the trip would change the test. No live wording substitution justified.

Offline decision: reconstruct the established conversation, then perform one conservative negative-boundary API submission of the exact candidate; stop after decisive semantic failure. The candidate is not represented as an authorized successful action. Its configured mock interpretation supplies no invented target and is never consumed.

Offline acceptance gate FAILED: no target, eligibility, resolver or meaningful investigation result. State authority/confidentiality passed. Live NO-GO; zero requests. Do not repair or continue to another scenario during this pass.
''')
transcript=['# PR-PLAY-30 offline transcript','All provider behavior is mocked. Production API routing, authority, resolution and publication are real. No live output below.','## Mocked opening',opening['response']['gm_output']['player_facing_text']]
for r in rows:transcript += [f'## Turn {r["turn"]}',f'Player: {r["player"]}',f'Published: {r["response"]["gm_output"]["player_facing_text"]}',f'HTTP {r["status"]}; gameplay_completed={r["classification"]["gameplay_completed"]}; stop={r["classification"]["stop"]}; turn counter {r["before"]["session"]["turn_counter"]} → {r["after"]["session"]["turn_counter"]}.']
transcript+=['Turn 3: conversational_decline / destination_not_established. No interpretation request/response, action decomposition, exploration resolver, roll, or narration-provider result exists. The harness-configured unused mock must not be reported as actual interpretation. No further scenario action submitted. Full raw evidence: offline_run.json; semantic_stop.json.']
report('OFFLINE_TRANSCRIPT','\n\n'.join(transcript))
report('INVESTIGATION_PIPELINE','''# PR-PLAY-30 investigation pipeline
Actual trace: POST /api/chat → deterministic conversation/movement routing → destination_not_established → conversational_decline → player publication. No interpreter or exploration resolver executed.

The router's _destination_phrase takes the last matching destination preposition and does not split an infinitive purpose clause. For this text it extracts “investigate the muddy footprints” after “to”. _INSPECT_CUE_RE includes inspect/examine/look at/check/study/read, but not investigate. Movement recognition therefore treats the purpose as a destination and the exit matcher finds no match. Source evidence: conversational_orchestration.py:1060,1162-1174,1298-1330,1487-1502.

| Boundary | Observed |
|---|---|
| Interpretation | Provider skipped; live_chat_interpretation=null. |
| Decomposition/referent | Not performed; configured two-component mock unused. |
| Spatial grounding | Decline: destination_not_established. No crate area or local footprint target. |
| Target selection | None. |
| Eligibility/resolver | resolver_invoked=false, gameplay_parser_invoked=false. |
| Skill/check | None; remote print interactable has no configured check. |
| Deterministic outcome | No attempted exploration; kind=conversational_decline, success=false. |
| State/time | turn_counter 3→3; time_pressure 3→3; world unchanged; clue retained. |
| Narration | Deterministic decline: “You want to reach investigate the muddy footprints, but that is not an established destination from here. You stay where you are.” |
| Integrity/confidentiality | Pass for observed limited effects. |
| Semantic | action_or_compound_rejection; gameplay_completed=false; stop=true. |

First failed execution boundary: spatial grounding in deterministic movement routing, before provider interpretation. Two causes must remain separate: (1) existing routing defect captures purpose as destination; (2) absent authored exact-clue-to-current-target/local-area mapping. Fixing the regex alone does not authorize travel or evidence identity.

Existing legitimate downstream trace (source inspection only): INSPECT current target → bridge investigate action → classify_referenced_surface → match authored interactable → check eligibility/already searched → should_trigger_check (no config, no roll) → discover_clue milestone_mud_prints → existing overlay/clue/search persistence → normal turn tick → grounded narration. Not executed or claimed as validated here.
''')
report('LIVE_TRANSCRIPT','''# PR-PLAY-30 live transcript
NOT EXECUTED. Offline investigation gate failed with destination_not_established before interpreter/resolver. No live campaign, opening, turns, tokens or retries. No live reproduction of PR-PLAY-29. Seven-request ceiling respected: 0/7. No actual live player-facing transcript exists.
''')
report('STATE_INTEGRITY','''# PR-PLAY-30 state integrity
PASS for observed opening/conversation/decline scope; this is not investigation success. Complete snapshots are in opening.json and offline_run.json; per-turn diffs and evaluations are separate T1/T2/T3 JSON files. state_integrity_checks.json records reconstructed world ticks and source-bound social event additions.

Turn 1/2 ordinary evaluators have no findings; overlay_comparison passes. Character (including inventory/currency), campaign/quest state, combat, conditions remain unchanged. World mutations match advance_world_tick; Turn 2 additionally adds exactly two authorized social events. Rumor/topic discovery, lead registry and overlay updates have existing source authorization. No unsupported rewards, NPC relationship edits, physical evidence or location creation.

Turn 3 preserves world, character, campaign, combat, conditions, active scene, clue knowledge, lead state, overlays, search state and turn/time counters. Session changes are confined to conversation context, interaction context, scene_state context and last_saved_at. The decline clears active interlocutor, records delivered response/context and appends a log entry. It does not claim examination. turn_counter and time_pressure stay 3; world tick does not advance.

Confidentiality: all four player API responses scanned against exact authored hidden facts and protected author keys; no matches. Native evaluator reports no hidden disclosure. 29/29 response/privileged-read regression controls pass. Manual prose review finds no protected leakage. Exact matching alone does not prove absence of arbitrary paraphrases. Full internal diagnostic evidence is intentionally separate from player transcript.
''')
report('PERFORMANCE',f'''# PR-PLAY-30 performance
Offline application run: {elapsed:.3f}s; opening {opening['latency_seconds']:.3f}s. Actions: {json.dumps(times)} seconds. These are local mocked timings, not live-provider pacing estimates.

Actual live-provider requests 0; input/output/total billed tokens 0/0/0; per-request live usage not applicable; retries 0; fallback models 0; AI judges 0. Budget 0/7, compliant. Mocked opening requests {len(opening['mock_requests'])}, interpretation requests 2, expression requests {len(run['expressions'])}. Turn 3 has zero of each. Mock helpers contain synthetic token values; they are not actual provider usage.

Offline scenario test passed (meaning expected boundary behavior observed); 29 security controls passed. Initial harness setup error occurred before gameplay; subsequent offline run is not a provider retry. No repeated scenario after decisive semantic stop. performance.json holds machine-readable measurements.
''')
experience=[('Information continuity','PASS','Disclosed clue survives Turn 3 unchanged.'),('Referential understanding','NOT TESTED','Turn 3 interpreter never invoked; router does not ground footprints.'),('Spatial coherence','PARTIAL','No teleport/invented access, but route binds purpose as destination.'),('Mechanical resolution','FAIL','No exploration resolver or examination.'),('Consequential consistency','PASS','No time/world/reward change on decline; conversation effects authorized.'),('Narrative clarity','FAIL','“reach investigate the muddy footprints” exposes parser error; no useful route offered.'),('Agency','PARTIAL','Existing rumor-following exit and notice board remain, but decline supplies no actionable guidance.'),('Pacing','PARTIAL','Mocked local response is fast; live latency not tested.'),('Artificial boundaries','FAIL','Natural purpose phrase becomes an invalid internal destination.'),('Overall playability','FAIL','Conversation works; exact natural continuation does not execute.')]
save('player_experience.json',[dict(capability=a,score=b,evidence=c) for a,b,c in experience])
report('PLAYER_EXPERIENCE','# PR-PLAY-30 player experience\n\n| Capability | Score | Evidence |\n|---|---|---|\n'+'\n'.join('| '+' | '.join(x)+' |' for x in experience))
report('FAILURE_ANALYSIS','''# PR-PLAY-30 failure analysis
First failed execution boundary: deterministic spatial/destination grounding, before provider interpretation. Native decision reason=destination_not_established, kind=conversational_decline, resolver_invoked=false, gameplay_parser_invoked=false, zero provider calls. HTTP 200 is transport success only. Native semantic evaluator correctly stops on action_or_compound_rejection; no harness classification repair required.

Existing capability defect: purpose text after “to” is extracted as a destination; “investigate” is absent from this router's inspection cues. This is reproducible independently of provider behavior because Turn 3 never invokes the configured mock interpreter. Secondary effect: awkward deterministic text and active NPC context cleared; legitimate clue persists, but play cannot proceed naturally in the requested action.

Missing content/representation: exact rumor clue has no physical target or authored location pointer; crates are prose only. Related old_milestone prints do exist under a distinct clue. This is not a blanket absence of environmental investigation. It is not permissible to equate the prints, invent local geometry, or silently switch to unrelated notice-board examination.

Provider failure: not implicated/tested on investigation. Authority rejection: preserves world boundaries, but not a fully actionable VALID BLOCK because response neither resolves nor offers a supported next step. Result classification: ENGINE FAILURE at pre-interpretation routing for understood natural-purpose wording, plus UNSUPPORTED CONTENT for immediate local footprint inspection. No claim that a fully authorized exact investigation was denied: its physical mapping is missing.

A targeted follow-up is warranted: audit/repair clue-directed exploration intent grounding so destination and purpose remain separate and the system offers only existing authored routes when exact physical mapping is absent. Add no world content as an incidental parser fix. PR-PLAY-31 is a recommendation only; no repair started.
''')
answers=[
'Yes: tavern_runner/patrol_rumor in verified world.',
'Yes: muddy_footprints_northwest on authored topic.',
'No for that exact id; separate prints target exists at old_milestone.',
'Relative northwest-of-crates text only; related northwest destination exists without exact identity mapping.',
'No addressable crate landmark; prose reference only.',
'Authored exit reaches old_milestone; exact local footprint area not represented; transition not executed.',
'Bounded same-scene inspection yes; general local movement/access solver no.',
'Yes for authored active-scene interactables; remote prints are not current targets.',
'No check configured on existing milestone/prints; no roll performed.',
'Remote milestone_mud_prints text is authored; exact immediate action has no authorized investigation outcome.',
'Yes, discovered clue persists after disclosure and declined action.',
'Interpreter design includes two recent visible turns/public speech; actual Turn 3 invocation skipped.',
'Not resolved in this run; provider referential comprehension not tested.',
'No current footprint target selected or exact authored clue-to-target mapping.',
'Not on this action: exploration resolver never invoked.',
'Correctly no time advancement for declined action; turn/time_pressure 3→3.',
'Yes within observed scope: conversation/context/log only for decline; prior social effects validated.',
'Useful conversation narration; investigation publishes awkward non-actionable decline.',
'Starting-state reconstruction passes; investigation acceptance gate fails.',
'No; offline gate failed.',
'No.',
'Not applicable.',
'Zero actual provider requests.',
'Zero provider retries.',
'Yes, 0/7.',
'Yes for observed state changes; no successful investigation claimed.',
'Yes for bounded exact/projection scan, manual prose review and 29 regression controls.',
'Spatial/destination grounding in deterministic router; purpose mistaken for destination.',
'Grounding natural clue-directed exploration to existing route/current target without promoting hearsay to physical access.',
'Target destination/purpose separation and authority-preserving route/target handoff; validate with this exact repro. Do not invent missing world structure.'
]
report('FINAL_VERDICT','# PR-PLAY-30 final verdict\n\nStatus: BLOCKED for requested gameplay; procedural validation complete. Overall C — BLOCKED BY CONTENT OR ENGINE. Exact-action feasibility UNSUPPORTED. Related staged content conditionally feasible, unvalidated. No repairs, content edits, commit, push or PR-PLAY-31 execution.\n\n'+'\n\n'.join(f'{i}. {a}' for i,a in enumerate(answers,1))+'\n\nStop for external review.\n')
save('final_summary.json',dict(status='BLOCKED',procedural_completion=True,overall_verdict='C',feasibility='UNSUPPORTED exact one-action investigation',conversation_reproduced=True,live_executed=False,live_requests=0,retries=0,first_failed_boundary='deterministic spatial/destination grounding before provider interpretation',source_unchanged=True,state_integrity=True,confidentiality=True))
# Credential values are used only for local boolean scan, never exported.
secrets=[str(v) for k,v in config.items() if v and len(str(v))>=12 and any(w in k.lower() for w in ['api_key','token','secret','password'])]
findings=[]
files=[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
for p in files:
 raw=p.read_bytes()
 if any(v.encode() in raw for v in secrets):findings.append(str(p.relative_to(OUT)))
save('credential_scan.json',dict(pass_=not findings,files_scanned=len(files),findings=findings,secret_values_exported=False))
assert not findings,findings
inventory={str(p.relative_to(OUT)).replace('\\','/'):digest(p) for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['MANIFEST.json','archive_verification.json','archive_path.txt']}
save('MANIFEST.json',dict(revision=revision,files=inventory))
stamp=subprocess.check_output(['powershell','-NoProfile','-Command',"[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMdd-HHmmss')"],text=True).strip()
archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
archive.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in OUT.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.name not in ['archive_verification.json','archive_path.txt']:z.write(p,'pr_play_30/'+str(p.relative_to(OUT)).replace('\\','/'))
with zipfile.ZipFile(archive) as z:
 bad=z.testzip();assert bad is None
 assert all('pr_play_30/'+p in z.namelist() for p in inventory)
 count=len(z.namelist())
save('archive_verification.json',dict(path=str(archive),exists=archive.exists(),size_bytes=archive.stat().st_size,entries=count,testzip=bad,sha256=digest(archive),manifest_files_verified=len(inventory)))
(OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
print(json.dumps(dict(archive=str(archive),entries=count,source_paths_unchanged=len(previous),state_integrity=True,confidentiality=True)))
