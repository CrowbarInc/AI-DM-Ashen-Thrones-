"""Derive inspectable offline evidence; no model or network operations."""
import os,sys,json,hashlib,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
O=R/'artifacts/pr_play_03'
def write(name,obj): (O/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
zpath=R/'artifacts/pr_play_02/manual-20261026-201939.zip'
with zipfile.ZipFile(zpath) as z:
    inventory={'zip_path':str(zpath.relative_to(R)),'zip_sha256':sha(zpath.read_bytes()),'members':[{'path':n,'bytes':len(z.read(n)),'sha256':sha(z.read(n))} for n in z.namelist() if not n.endswith('/')]}
    get=lambda n:json.loads(z.read('manual-20261026-201939/data/'+n))
    session=get('session.json')['payload']; world=get('world.json')
    log=json.loads(z.read('manual-20261026-201939/data/session_log.jsonl').decode().splitlines()[0])
    ledger=[json.loads(v) for v in z.read('manual-20261026-201939/provider_usage.jsonl').decode().splitlines()]
    (O/'historical_provider_usage.jsonl').write_bytes(z.read('manual-20261026-201939/provider_usage.jsonl'))
write('historical_inventory.json',inventory)
trace=next(t for t in session['debug_traces'] if t.get('source')=='start_campaign')
m=log['gm_output']['metadata']
write('historical_excerpt.json',{'source':inventory['zip_path'],'timestamp':log['timestamp'],'player_input':log['player_input'],'request':log['request'],
 'resolution':log['resolution'],'player_facing_text':log['gm_output']['player_facing_text'],'tags':log['gm_output']['tags'],
 'debug_notes':log['gm_output']['debug_notes'],'metadata':{k:m[k] for k in ['output_form','structured_contract_reason','provider_response_contract','narration_provider_calls','narration_retry_count','live_resolution_mode','accepted_response','hard_validation_attempt_1','decision_review']},
 'state':{k:session[k] for k in ['campaign_started','turn_counter','active_scene_id','clocks']},'factions':world['factions'],'world_event_log':world.get('event_log'),
 'latency_ms':trace['latency_ms'],'performance':trace['performance'],'log_meta':log['log_meta']})
from game.gm import _safe_json
parser_inputs={'valid':json.dumps({'declared_claims':[],'narration':'Rain falls by the gate.'}),
 'fenced':'```json\n'+json.dumps({'declared_claims':[],'narration':'Rain falls by the gate.'})+'\n```',
 'plain':'You stand beside the gate in the rain.','truncated_declarations':'{"declared_claims": [',
 'narration_only':'{"narration":"Rain falls by the gate."}',
 'valid_embedded_in_prose':'Here is the response: {"declared_claims":[],"narration":"Rain falls by the gate."}'}
parser=[]
for name,text in parser_inputs.items():
 g=_safe_json(text,require_structured_claims=True);parser.append({'case':name,'input':text,'output':g})
write('parser_controls.json',parser)
rs=json.loads((O/'reproduction_outputs.json').read_text());checks=[]
def check(name,condition):
 assert condition,name
 checks.append({'check':name,'passed':True})
by={r['case']:r for r in rs}
for name in ['missing_envelope','historical_seed_missing']:
 r=by[name];g=r['response']['gm_output'];md=g['metadata']
 check(name+': exact historical failure sentence',g['player_facing_text']==log['gm_output']['player_facing_text'])
 check(name+': structured rejection',md['structured_contract_reason']=='missing_structured_envelope')
 check(name+': empty repair',g['fallback_kind']=='nonsocial_empty_resolution_repair')
 check(name+': default information mode',md['live_resolution_mode']['reason_codes']==['default_existing_resolution'])
 check(name+': safe seal',md['accepted_response']['provenance']=='safe_nonresolution')
 check(name+': misleading success state',r['after']['campaign_started'] is True and r['after']['turn_counter']==1 and r['after']['clocks']['time_pressure']==1)
r=by['valid_structured'];g=r['response']['gm_output']
check('valid: exact provider narration delivered',g['player_facing_text']==json.loads(r['input'])['narration'])
check('valid: initial generation seal',g['metadata']['accepted_response']['provenance']=='initial_generation')
for r in rs:
 if r['case']=='pipeline_exception':continue
 check(r['case']+': one SDK mock call',r['sdk_mock_calls']==1)
 check(r['case']+': repeat blocked without state change',r['repeated_start']['status_code']==409 and r['repeated_start']['state']==r['after'] and r['repeated_start']['calls_after']==1)
r=by['pipeline_exception']
check('pipeline exception: turn rolled back only',r['after']['turn_counter']==0 and r['after']['campaign_started'] is False and r['after']['clocks']['time_pressure']==1)
check('pipeline exception: repeat pressure advances',r['repeated_pipeline_failure']['clocks']['time_pressure']==2)
check('pipeline exception: repeat faction pressure advances',r['repeated_pipeline_failure']['world']['factions'][0]['pressure']==r['before']['world']['factions'][0]['pressure']+2)
write('deterministic_checks.json',{'scope':'structural host behavior and exact output comparison; no repair-effect claim','checks':checks,'passed':len(checks)})
captures=json.loads((O/'historical_seed_missing_requests.json').read_text());kw=captures[0]['kwargs'];msgs=kw['input'];payload=json.loads(msgs[1]['content'])
write('performance_analysis.json',{'original_ledger_completed':ledger[-1],'original_latency_ms':trace['latency_ms'],
 'warning':'completion_status is host accounting status, NOT provider status or finish_reason',
 'offline_reconstructed_request':{'api_fields':list(kw),'max_output_tokens':kw.get('max_output_tokens'),'system_chars':len(msgs[0]['content']),
 'payload_chars':len(msgs[1]['content']),'top_level_char_contributors':sorted([{'key':k,'chars':len(json.dumps(v,ensure_ascii=False))} for k,v in payload.items()],key=lambda d:-d['chars'])},
 'original_request_retained':False,'original_raw_response_retained':False,'provider_finish_reason_retained':False})
sources={'game/api.py':[(2466,2540),(2800,2868),(3161,3250),(3497,3569),(3650,3754),(3800,3968),(4215,4290),(4404,4510),(4690,4750),(5054,5092),(5710,5752),(5790,5868),(5927,6120),(6138,6378)],
 'game/gm.py':[(202,290),(3796,3988),(4154,4175),(4786,4817),(5055,5321)],
 'game/structured_player_output.py':[(1,112)],'game/live_resolution.py':[(384,490),(642,713)],
 'game/resolution_contract.py':[(1328,1341),(1380,1415)],'game/immutable_valid_response.py':[(800,818),(974,1034),(1057,1070),(1620,1754),(1975,2090)],
 'game/gm_retry.py':[(2511,2610)],'game/final_emission_gate.py':[(79,106)],'game/final_emission_validators.py':[(312,331)],
 'game/api_turn_support.py':[(665,686)],'game/provider_budget.py':[(42,82),(214,255)],'game/world.py':[(258,367)],
 'game/storage.py':[(221,305),(375,399)],'game/campaign_reset.py':[(1,70)],'static/app.js':[(649,681)],
 'game/gm_resolution_decision.py':[(4755,4830)],'game/opening_scene_realization.py':[(540,568)],
 'game/interaction_completion.py':[(419,429)],'game/response_type_gating.py':[(223,306)]}
ex=[];index=[]
for f,ranges in sources.items():
 p=R/f;lines=p.read_text(encoding='utf-8').splitlines();index.append({'path':f,'sha256':sha(p.read_bytes()),'ranges':ranges})
 for a,b in ranges:
  ex.append('\n### '+f+f':{a}-{b}\n\n```text\n'+'\n'.join(f'{i+1}: {line}' for i,line in enumerate(lines[a-1:b],a-1))+'\n```\n')
(O/'source_excerpts.md').write_text('# Current source evidence (numbered, read only)\n'+''.join(ex),encoding='utf-8');write('source_index.json',index)
print('Deterministic checks:',len(checks),'PASS; source boundaries:',len(index))
print(json.dumps(json.loads((O/'performance_analysis.json').read_text())['offline_reconstructed_request'],indent=2)[:2300])
