"""Two live supported HTTP application actions, control, failures and isolation."""
import copy,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_play_64'
from artifacts.pr_play_61 import run_experiment as base
base.OUT=OUT
os.environ['ASHEN_PROVIDER_USAGE_PATH']=str(OUT/'provider_usage.jsonl')
os.environ['ASHEN_PROVIDER_REQUEST_LIMIT']='4'
os.environ['ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT']='8000'
os.environ['ASHEN_PROVIDER_INPUT_TOKEN_LIMIT']='6500'
os.environ['ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT']='1500'
from game import api,storage
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
from game.provider_budget import snapshot
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
api.call_gpt=lambda *a,**k:_gm_response('Provider calls are disabled for this run, so no live narration was generated.')
def save(n,v):(OUT/n).write_text(json.dumps(base.redact(v),indent=2,ensure_ascii=False),encoding='utf-8')
def state():
 return {'authority':base.authority(),'session':storage.load_session(),'character':storage.load_character()}
actions=[base.NOTICE,base.BARREL,base.REPEAT]
original=i.run_integrated_hook;semantic=i.semantic.validate_consequential_narration
base.disable_publication();base._seed(OUT/'control_session',base._Patch(),'frontier_gate')
control={'initial':state(),'actions':base.post_all(actions),'final':state()};save('control.json',control)
base._seed(OUT/'live_session',base._Patch(),'frontier_gate');initial=state()
present=base.key_present();base.enable_publication(storage.load_session()['campaign_run_id'],live=present)
q.reset_live_budget();q.clear_evidence();os.environ[q.LABEL_ENV]='pr_play_64_live'
live=[];states=[initial]
for text in actions[:2]:
 row=base.post_all([text])[0];row['full_trace']=copy.deepcopy(q.evidence_records()[-1]) if q.evidence_records() else None
 live.append(row);states.append(state());save('gameplay_actions.json',live)
 print('live',text,row['published_marker'],row['quarantine']['decision'] if row['quarantine'] else None,flush=True)
provider_snapshot=snapshot();save('provider_snapshot.json',provider_snapshot)
# Provider-free fallback in the same usable session, followed by state capture.
os.environ[q.LIVE_ENV]='';i.run_integrated_hook=lambda h:original(h,generator=q._Replay(None,'timeout'))
row=base.post_all([actions[2]])[0];row['full_trace']=copy.deepcopy(q.evidence_records()[-1]);live.append(row);states.append(state())
i.run_integrated_hook=original
save('gameplay_actions.json',live);save('state_snapshots.json',states)
def scrub(a):return {k:v for k,v in a.items() if k!='campaign_run_id'}
equal=[{'action':a['input'],'authority_equal':scrub(a['authority'])==scrub(b['authority']),'resolution_equal':a['mechanical']==b['mechanical']} for a,b in zip(control['actions'],live)]
save('state_integrity.json',{'per_action':equal,'all_equal':all(r['authority_equal'] and r['resolution_equal'] for r in equal)})
save('live_summary.json',{'provider_available':present,'pathway':'FastAPI TestClient HTTP application route /api/chat?ui_mode=player; no browser or external TCP listener','gameplay_actions':len(live),'live_actions':2,'live_provider_requests':sum(int((r['quarantine'] or {}).get('provider_requests') or 0) for r in live),'validated_ai':sum((r['quarantine'] or {}).get('decision')=='PASS' and int((r['quarantine'] or {}).get('provider_requests') or 0)>0 for r in live),'published_ai':sum(r['published_marker']=='published' for r in live),'fallbacks':sum(bool((r['quarantine'] or {}).get('used_fallback')) for r in live),'http_latency_ms':[r['http_ms'] for r in live]})
save('isolation.json',base.isolation_check('different-bound-session'))
# Each fault is injected through the supported application publication pathway.
faults=[('provider_unavailable',None,'provider_error',None),('timeout',None,'timeout',None),('empty','','',None),('malformed',{},'',None),('validation_FAIL',base.ROUTE,'','FAIL'),('REVIEW_REQUIRED',base.ROUTE,'','REVIEW_REQUIRED'),('VALIDATION_ERROR',base.ROUTE,'','VALIDATION_ERROR'),('unauthorized_discovery',base.ROUTE+' You discover a second patrol route.','',None),('persistent_consequence',base.ROUTE+' The guard captain dies where he stands.','',None),('item_acquisition',base.ROUTE+' You take the iron key.','',None),('missing_disclosure','You examine the board.','',None),('hidden_disclosure',base.ROUTE+' CANARY_HIDDEN_DESTINATION is behind the gate.','',None)]
rows=[]
for name,text,fault,decision in faults:
 base._seed(OUT/'faults'/name,base._Patch(),'frontier_gate');base.enable_publication(storage.load_session()['campaign_run_id'],live=False);q.clear_evidence()
 before=state();i.run_integrated_hook=lambda h,t=text,f=fault:original(h,generator=q._Replay(t,f))
 if decision:i.semantic.validate_consequential_narration=lambda *a,d=decision:{'decision':d,'reasons':['injected'],'claims':[]}
 row=base.post_all([base.NOTICE])[0];trace=copy.deepcopy(q.evidence_records()[-1]);after=state()
 i.semantic.validate_consequential_narration=semantic
 c,r=i.outcome_contract(trace['hook_input']);fallback_validation=i.validate_integrated(c,r,row['facing'])
 stable=all(before['authority'].get(k)==after['authority'].get(k) for k in ('hp','inventory','equipment','scene','player','npcs','quests','conditions','combat'))
 # Compare the full bounded authority and resolver output with the disabled control.
 equal_control=scrub(after['authority'])==scrub(control['actions'][0]['authority']) and row['mechanical']==control['actions'][0]['mechanical']
 i.run_integrated_hook=lambda h:original(h,generator=q._Replay('You examine the notice board again; nothing new is established.',''))
 continuation=base.post_all([base.REPEAT])[0]
 rows.append({'name':name,'before':before,'after':after,'action':row,'trace':trace,'fallback_validation':fallback_validation,'mandatory_preserved':base.ROUTE in row['facing'],'stable_authority':stable,'equal_disabled_control':equal_control,'continuation':continuation,'passed':bool(trace['used_fallback']) and fallback_validation['decision']=='PASS' and stable and equal_control and base.ROUTE in row['facing'] and continuation['status_code']==200})
 print('fault',name,rows[-1]['passed'],flush=True)
i.run_integrated_hook=original;i.semantic.validate_consequential_narration=semantic
base.disable_publication();save('failure_injection.json',rows)
print('Complete',flush=True)
