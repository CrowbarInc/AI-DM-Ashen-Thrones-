"""Offline evidence analysis; no provider calls or production edits."""
import json, hashlib, shutil, sys, zipfile
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.playtest.gameplay import document,diff
from game.state_channels import is_author_key
from game import expressive_dialogue as expr
OUT=ROOT/'artifacts/pr_play_26'; RUN=ROOT/'artifacts/atgb/pr_play_26/live'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def report(n,t): (OUT/('PR_PLAY_26_'+n+'.md')).write_text('# PR-PLAY-26 '+n.replace('_',' ').lower()+'\n\n'+t.strip()+'\n',encoding='utf-8')
r=read(OUT/'live_result.json'); usage=r['provider_usage']
opening=next(s for s in r['steps'] if s['path'].startswith('/api/start_campaign'))
t=next(s for s in r['steps'] if s['path'].startswith('/api/chat')); gm=t['response']['gm_output']; meta=gm['metadata']; accepted=meta['accepted_response']; reply=gm['player_facing_text']; action=t['payload']['text']
reason='expression_validation_rejected_unsupported_addition'
write('stop_and_quality_analysis.json',dict(status='PARTIAL',overall_verdict='B',first_answer_quality='PASS',continuity='NOT TESTED',knowledge_transition='NOT TESTED',stop_reason=reason,raw_controller_stop_reason=r['stop_reason'],raw_label_correction='The manual gate used first_response_pass=false to prohibit continuation after validation rejection. That boolean is permission to continue, not answer quality. The published answer PASSES relevance/usefulness/grounding. Native structural classifier does not stop on safely rejected optional expression; section 13 requires the stricter experiment stop.',followup_attempted=False,provider_requests=usage['dispatched_requests'],remaining_requests=2))
rows=[]
for x in usage['records']:
 seq=x['sequence']; resp=read(RUN/f'diagnostics/response_{seq:02}.json')
 rows.append(dict(sequence=seq,purpose=x['purpose'],configured_model=x['configured_model'],returned_model=x['model'],input_tokens=x['input_tokens'],output_tokens=x['output_tokens'],total_tokens=x['total_tokens'],provider_seconds=resp['latency_seconds'],api_seconds=opening['api_latency_seconds'] if seq==1 else t['api_latency_seconds'],api_duration_shared=seq>1,status=x['completion_status'],retries=0))
perf=dict(requests=rows,totals={k:usage[k] for k in ('dispatched_requests','input_tokens','output_tokens','total_tokens')},opening_seconds=opening['api_latency_seconds'],first_interaction_seconds=t['api_latency_seconds'],followup_seconds=None,live_duration_seconds=r['duration_seconds'],offline_duration_seconds=read(OUT/'offline_result.json')['duration_seconds'],duration_scope='Live startup to cleanup, including manual evidence review wait; packaging excluded')
write('performance_measurements.json',perf)
states={n:read(RUN/n/'documents.json') for n in ('initial','baseline','opening','turns/T1/before','turns/T1/after','after')}
normalized={n:{k:document(s,k) for k in s} for n,s in states.items()}
for a,b,n in [('initial','baseline','reset'),('baseline','opening','initialization'),('turns/T1/before','turns/T1/after','interaction')]: write(n+'_state_diff.json',diff(normalized[a],normalized[b]))
b=normalized['turns/T1/before']; a=normalized['turns/T1/after']
checks={k:b.get(k)==a.get(k) for k in b if k not in ('session.json','world.json','combat.json','session_log.jsonl')}
bs,as_=b['session.json'],a['session.json']; bw,aw=b['world.json'],a['world.json']
checks.update({f'session.{k}':bs.get(k)==as_.get(k) for k in ['active_scene_id','current_date','clue_knowledge','lead_registry','flags']})
runtime_changes=diff(bs.get('npc_runtime',{}),as_.get('npc_runtime',{}))
checks['npc_relationships_and_knowledge_unchanged']=all(x['path']=='/tavern_runner/last_interaction_turn' for x in runtime_changes)
write('npc_runtime_diff.json',runtime_changes)
checks.update({f'world.{k}':bw.get(k)==aw.get(k) for k in bw if k not in ('factions','event_log')})
write('state_integrity_checks.json',dict(unchanged_checks=checks,all_unchanged=all(checks.values()),authorized=['turn_counter 1 -> 2','time_pressure 1 -> 2','active interlocutor tavern_runner, engagement, and last_interaction_turn null -> 2','conversation history, telemetry and runtime traces','each faction pressure +1 and agenda_progress +1; Ordo Pyric pressure event'],unauthorized=[],narrative_state_mismatches=[]))
def restricted(v,flag=False):
 if isinstance(v,dict):
  for k,c in v.items(): yield from restricted(c,flag or is_author_key(k))
 elif isinstance(v,list):
  for c in v: yield from restricted(c,flag)
 elif flag and isinstance(v,str) and len(v.strip())>=16: yield v
public=json.dumps([s['response'] for s in r['steps']],ensure_ascii=False)
restricted_values=set(v for s in states.values() for v in restricted(s)); matches=sorted(v for v in restricted_values if v in public)
write('confidentiality_verification.json',dict(restricted_strings_checked=len(restricted_values),matches=matches,classified_runtime_telemetry_matches=[v for v in matches if v==as_.get('_runtime_canonical_ctir_stamp_v1')],hidden_game_fact_matches=[v for v in matches if v!=as_.get('_runtime_canonical_ctir_stamp_v1')],scope='Exact restricted-string scan of all Player HTTP responses plus manual published transcript review; does not prove absence of arbitrary paraphrased leakage',player_only=True,hard_valid=accepted['hard_validation']['hard_valid']))
source='I offer hot stew and rumors.'; candidate="I've got hot stew and rumors to share."
src=expr._content(expr._strip_frame(source)[0],framing=True); cand=expr._content(expr._strip_frame(candidate)[0],framing=True)
write('expression_token_analysis.json',dict(source=source,candidate=candidate,source_tokens=src,candidate_tokens=cand,uncovered_tokens=[x for x in cand if not expr._covered(x,src)],method='Offline inspection using unchanged production tokenizer/coverage helper; no new generation'))
report('PREFLIGHT',"""PASS. Exactly one offline preflight; zero live requests and no campaign initialization. Repository branch/revision and full pre-existing dirty status are in repository_status.json. No AGENTS.md was found in repository or immediate parent directories. Existing changes preserved.

Uses scripts/run_live_playtest.ps1 infrastructure through tools.playtest.runner/worker with an evidence-only bounded controller; no standalone provider client. Production HTTP /api/new_campaign, /api/start_campaign and /api/chat; all calls explicitly Player. Existing FiveTurnGameplay fixture provides storage and worker compatibility; its five-turn action loop is never run.

Configured gpt-4.1-mini, credentials present but not serialized, no alternate model settings. ASHEN_OPENING_RENDERER=1. SDK retries 0, host retries disabled, provider request ceiling 5, no judges/fallback models. Token limits unchanged (200000 input, 20000 output, 220000 total). Production admission accepted five synthetic invocations and refused a sixth without provider contact.

Loopback round-trip, HTTP readiness, Player state 200, snapshot capture, diagnostics and cleanup/port release verified. Privileged reads remain rejected by unchanged resolve_requested_ui_mode, exercised offline for author/debug; no privileged HTTP calls. Readiness credentials_present=false refers to the deliberately disabled offline worker; safe_configuration.json confirms live credentials configured.

PR-PLAY-23 normalization is present in game/local_interaction.py and invoked by conversational_orchestration.py; classify_turn/evaluate preserve structural semantic-stop distinctions. PR-PLAY-25 public_fact_dialogue.select_public_offering is called by dialogue_authority.build_dialogue_authority. Source hashes preserve exact versions. Owned worker termination/wait verifies process cleanup; no graceful ASGI shutdown handshake is claimed.""")
targets=read(RUN/'opening/available_npc_targets.json'); npc=targets['tavern_runner']['row']
report('SCENARIO',f"""Actual opening:

{r['opening']}

Available same-scene NPC catalog: {', '.join(targets)}. Tavern Runner (tavern_runner) selected because explicitly published, addressable in frontier_gate and authoritative, with public offerings and existing patrol_rumor topic. No NPC/topic/state was fabricated.

Public fact: A tavern runner trades hot stew and rumors near the rain barrel.

Existing topic: {json.dumps(npc['topics'])}

Initial action: {action}

Conditional follow-up: only after useful first answer, valid accessible target, no hard stop and at least two requests remaining. If rumors offered, intended question: What sort of rumors have you heard? Actual follow-up: NOT SUBMITTED because expression validation rejected. Two requests remained.""")
report('TRANSCRIPT',f"""Published opening (exact):

{r['opening']}

Player (exact):

{action}

NPC (exact):

{reply}

No follow-up or second response. Relevant public fact: A tavern runner trades hot stew and rumors near the rain barrel. Player mode; location frontier_gate before and after. Full public snapshots and HTTP transcript preserved under live/.""")
report('NPC_PIPELINE',f"""1. Interpretation request 02 receives actual opening/public evidence, returns MOVE(tavern_runner) then ASK(tavern_runner). Raw requests/responses preserve public context and parsed representation.
2. normalize_local_approach traces use authored_same_scene_interaction_preamble, retain ASK and movement_executed=false. normalized_action_from_interpretation preserves explicit target tavern_runner.
3. resolve_social_action executes question; target resolution/authorization uses explicit native NPC and same-scene addressability. Initial authored topic selection has no offerings answer; legacy resolution success_state=failure is not the final answer's quality.
4. build_dialogue_authority trace_018 and select_public_offering trace_019 select scene:frontier_gate:visible:2, reason=authorized, relation=own_offerings, npc_id=tavern_runner. Authorized proposition: {source}. Posture established, directly_answers; no improvisation.
5. select_host_speech produces {reply}. Request 03 supplies the authorized proposition for faithful paraphrase.
6. Expression provider returns {candidate}. trace_024_validate_expression_output.json: adopt=false, unsupported_addition. Offline token analysis preserves the uncovered tokens.
7. Publication uses HOST_FALLBACK, authorization_source={accepted['authorization_source']}, speech_adoption=AUTHORIZED_HOST_SPEECH, hard_valid=true, interaction_completion=true. Final Player answer is relevant, useful, grounded, attributable, natural and authorized: quality PASS on all six criteria. Authority source PUBLIC_FACT; expression fallback is a delivery choice, not generic uncertainty/FALLBACK knowledge.
8. classify_turn reports HTTP/pipeline/action/gameplay complete; evaluate stop=false. This does not override the mission's stricter validator-rejection stop. Root controller withheld follow-up and shut down. See stop_and_quality_analysis.json for correction of its generic raw gate label.

No authored-topic transition was executed. Full observations in live/diagnostics/trace_*; all function inputs and outputs preserved, including disclosure and native diagnostics.""")
report('KNOWLEDGE_TRANSITION',f"""First question: {action}

First answer: {reply}

Actual source PUBLIC_FACT, scene:frontier_gate:visible:2; attributable own_offerings. Final authorized proposition: {source}.

Available authored topic: {json.dumps(npc['topics'])}. It predates the experiment. First-turn traces show availability/disclosure evaluations but no selected offerings topic; these checks are not a follow-up selection.

Intended conditional follow-up: What sort of rumors have you heard? Not submitted: section 13 says stop after validator rejection, and generated expression was rejected unsupported_addition. Published host fallback still passes quality. Budget remaining 2.

Follow-up resolved NPC, selected topic, disclosure authorization, selected propositions and second answer: NOT TESTED. Continuity NOT TESTED. Stored conversation retains tavern_runner identity and delivered offerings, but this is not evidence of successful contextual interpretation. No claim of a successful AUTHORED_TOPIC transition.""")
report('STATE_INTEGRITY',f"""Snapshots: live/initial before reset, live/baseline after the sole /api/new_campaign reset and before opening, live/opening after start, live/turns/T1/before and after, live/after after cleanup. No post-follow-up state exists. Raw snapshots and normalized diffs are preserved.

Initialization publishes the opening and initializes normal scene/turn context. During conversation: turn_counter 1 -> 2, time_pressure 1 -> 2; interlocutor/engagement and history updated. Each faction pressure and agenda_progress advances by one through existing deterministic progression; Ordo Pyric pressure event added. NPC last_interaction_turn changes null -> 2 (game/social.py:3811); relationship values and revealed knowledge remain unchanged. These are normal turn progression, not dialogue-created facts or rewards. See game/world.py:160-172, game/world_progression.py and native CTIR progression evidence.

Location and date unchanged; character/inventory/currency documents, NPC relationships and persistent NPC knowledge, quest/clue/lead state and remaining world facts unchanged. Machine checks all pass: {all(checks.values())}. Full diffs retain runtime and telemetry changes.

Unauthorized mutations: none found. Narrative/state mismatches: none found in published dialogue. It only advertises existing offerings. Hidden-information protection: restricted-string scan results in confidentiality_verification.json; manual transcript review finds no hidden truths/private quest or restricted NPC disclosures. The sole exact match is _runtime_canonical_ctir_stamp_v1 telemetry, not a hidden campaign fact; explicitly classified in the scan evidence. Exact-string detection is a limited check, not a proof against all paraphrases. Diagnostics remain internal evidence.

Owned process stopped and loopback port released; no gameplay source/state was changed to improve results.""")
lines=['| Request | Purpose | Input | Output | Total | Provider seconds | API seconds | Status/retries |','|---|---|---:|---:|---:|---:|---:|---|']
for x in rows: lines.append(f"| {x['sequence']} | {x['purpose']} | {x['input_tokens']} | {x['output_tokens']} | {x['total_tokens']} | {x['provider_seconds']:.3f} | {x['api_seconds']:.3f} | {x['status']}/0 |")
report('PERFORMANCE','\n'.join(lines)+f"\n\nConfigured model gpt-4.1-mini; provider returned gpt-4.1-mini-2025-04-14. Requests 2 and 3 share one API duration; do not add those API values. No follow-up requests.\n\nTotals: {usage['dispatched_requests']} requests; {usage['input_tokens']} input, {usage['output_tokens']} output, {usage['total_tokens']} total tokens. Opening {opening['api_latency_seconds']:.3f}s; first interaction {t['api_latency_seconds']:.3f}s; follow-up N/A. Live experiment {r['duration_seconds']:.3f}s, including manual review wait and cleanup; offline preflight {perf['offline_duration_seconds']:.3f}s, packaging excluded. Retries 0; no fallback/judge requests. No token ceilings increased.")
report('FAILURE_ANALYSIS',f"""First experiment stop boundary: 15, Expression validation. Confidence HIGH. Expected: authorized faithful paraphrase accepted, useful first answer followed by authored-topic test. Actual: provider paraphrase {candidate!r} rejected unsupported_addition; authorized host fallback {reply!r} published successfully. This is a validation rejection of an optional expression, not a failure of public-fact selection or published first-answer relevance.

Evidence: request_03.json, response_03.json, trace_023_request_expression_output.json, trace_024_validate_expression_output.json, expression_token_analysis.json and accepted_response expression_decision=rejected/expression_adoption=HOST_FALLBACK.

Source anchors: game/expressive_dialogue.py:_faithful_reasons (634; unsupported_addition at 657), validate_expression (761), _attempt (893). Raw native structural classifier treats the accepted fallback as completion and does not stop; manual experiment review enforces section 13. Generic raw controller stop_reason first_response_not_pass is a gate-label limitation corrected in stop_and_quality_analysis.json; published answer quality is PASS.

Known history: PR-PLAY-24 also rejected expression for unsupported_addition, but that earlier run lacked offerings authority and published uncertainty. This run fixes the authority symptom live. No test suite was rerun, so no claim of an exact matching known failing test. Smallest next investigation: offline reproduction of this exact authorized proposition/returned paraphrase against lexical coverage, to determine whether rejection is intended or overly strict. No production repair implemented.

No confirmed defect in the first delivered answer; two-turn continuity remains untested because the experiment hard-stop rule fired.""")
answers=[('Campaign initialization','Yes; one reset/new_campaign and one start, no restart'),('Selected NPC','Tavern Runner / tavern_runner'),('First question',action),('First action bound','Yes; local approach normalized to ASK'),('Social resolver executed','Yes'),('Relevant public fact selected','Yes; scene:frontier_gate:visible:2'),('First question answered','Yes'),('First answer useful','Yes, PASS'),('Follow-up submitted','No'),('Follow-up question','None submitted; planned What sort of rumors have you heard?'),('NPC identity preserved','Yes through first response; continuation NOT TESTED'),('Authored NPC topic selected','No relevant first-turn topic; follow-up NOT TESTED'),('Disclosure authorization','Public own-offerings authorized; follow-up NOT TESTED'),('Follow-up answered','NOT TESTED'),('Continuity preserved','NOT TESTED'),('Unsupported consequential claims','None in published answer'),('Authoritative state preserved','Yes; normal progression only'),('Hidden information protected','No disclosure found; exact-scan/manual scope documented'),('Provider requests',str(usage['dispatched_requests'])),('Token consumption',str(usage['total_tokens'])),('First-interaction latency',f"{t['api_latency_seconds']:.3f}s"),('Follow-up latency','N/A'),('Harness stopped appropriately','Yes via manual gate after expression validator rejection; native classifier alone did not flag optional-expression rejection'),('Functional two-turn capability','Not demonstrated by this run; only first turn demonstrated'),('Highest-priority next step','Offline isolate unsupported_addition rejection for exact captured paraphrase before another separately authorized live pass')]
report('FINAL_VERDICT','Status PARTIAL. Overall B â€” partial validation: useful first turn demonstrated; second turn not executed. B here does not imply an observed weak follow-up. A is not supported; no two-turn success claim.\n\n'+'\n\n'.join(f'{i}. **{q}:** {v}' for i,(q,v) in enumerate(answers,1))+'\n\nNo production edits, commits, pushes, retries, extra initializations or judge calls. Stop and await external review.')
# Exact production sources at execution, with original filenames/line numbering.
hashes=read(OUT/'live_source_hashes.json'); after_hash={}
for name,expected in hashes.items():
 src=ROOT/name; after_hash[name]=hashlib.sha256(src.read_bytes()).hexdigest(); dest=OUT/'source_snapshot'/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)
write('source_hashes_after.json',dict(hashes=after_hash,unchanged=hashes==after_hash)); assert hashes==after_hash
for name in ('game/world.py','game/world_progression.py'):
 dest=OUT/'source_snapshot'/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/name,dest)
# Copy bounded isolated run evidence; no unrelated history or credential files.
for mode in ('offline','live'): shutil.copytree(ROOT/'artifacts/atgb/pr_play_26'/mode,OUT/mode,dirs_exist_ok=True)
from dotenv import dotenv_values
import os
cfg={**dotenv_values(ROOT/'.env'),**os.environ}; secrets=[v for k,v in cfg.items() if isinstance(v,str) and len(v)>6 and any(s in k.lower() for s in ('api_key','secret','password','credential','auth_token'))]
files=[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('MANIFEST.json','archive_verification.json','archive_path.txt')]
for p in files:
 data=p.read_bytes()
 assert not any(s.encode() in data for s in secrets), 'Credential detected in evidence'
write('credential_scan.json',dict(files_checked=len(files),configured_secret_matches=0,environment_dump_included=False))
manifest={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
write('MANIFEST.json',manifest)
stamp=datetime.now(ZoneInfo('America/New_York')).strftime('%Y%m%d-%H%M%S'); archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
archive=Path((OUT/'archive_path.txt').read_text()) if (OUT/'archive_path.txt').exists() else archive
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in OUT.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.name not in ('archive_verification.json','archive_path.txt'): z.write(p,'pr_play_26/'+str(p.relative_to(OUT)))
with zipfile.ZipFile(archive) as z: assert z.testzip() is None; count=len(z.namelist())
write('archive_verification.json',dict(path=str(archive),exists=archive.exists(),zip_integrity='PASS',entries=count,bytes=archive.stat().st_size))
(OUT/'archive_path.txt').write_text(str(archive),encoding='utf-8')
print(json.dumps(dict(archive=str(archive),performance=perf,restricted_matches=matches,state_checks_pass=all(checks.values()),source_unchanged=hashes==after_hash)))
