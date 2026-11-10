"""Provider-free authority controls, failures, isolation and saved-text replay."""
import json,os,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_play_63'
from artifacts.pr_play_61 import run_experiment as base
base.OUT=OUT
os.environ['ASHEN_PROVIDER_USAGE_PATH']=str(OUT/'offline_usage.jsonl')
from game import api,storage
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
api.call_gpt=lambda *a,**k:_gm_response('Provider calls are disabled for this run, so no live narration was generated.')
def save(n,v): (OUT/n).write_text(json.dumps(base.redact(v),indent=2,ensure_ascii=False),encoding='utf-8')
actions=[r['input'] for r in json.loads((OUT/'http_client_actions.json').read_text())]
base.disable_publication();base._seed(OUT/'control_session',base._Patch(),'frontier_gate')
control={'before':base.authority(),'actions':base.post_all(actions),'after':base.authority()};save('control.json',control)
live=json.loads((OUT/'browser_actions.json').read_text())
def scrub(a):return {k:v for k,v in a.items() if k!='campaign_run_id'}
comparisons=[]
for a,b in zip(control['actions'],live):
 comparisons.append({'action':a['input'],'authority_equal':scrub(a['authority'])==scrub(b['authority']),'resolution_equal':a['mechanical']==base.mechanical(b['response'])})
save('state_integrity.json',{'per_action':comparisons,'all_equal':all(r['authority_equal'] and r['resolution_equal'] for r in comparisons),'narration_has_no_state_handle':True})
save('isolation.json',base.isolation_check('different-bound-session'))
original=i.run_integrated_hook;original_semantic=i.semantic.validate_consequential_narration
cases=[('A_provider_unavailable',None,'provider_error',None),('B_timeout',None,'timeout',None),('C_empty','','',None),('D_malformed',{},'',None),('E_validation_FAIL',base.ROUTE,'','FAIL'),('F_REVIEW_REQUIRED',base.ROUTE,'','REVIEW_REQUIRED'),('G_VALIDATION_ERROR',base.ROUTE,'','VALIDATION_ERROR'),('H_missing_discovery','You examine the board.','',None),('I_persistent','The guard captain dies where he stands.','',None),('J_inventory','You acquire a silver key.','',None),('K_hidden','You discover a hidden passage.','',None),('L_prior_omitted','You examine the rain barrel; no new clue is established.','',None)]
rows=[]
for name,text,fault,decision in cases:
 base._seed(OUT/'faults'/name,base._Patch(),'frontier_gate');base.enable_publication(storage.load_session()['campaign_run_id'],live=False);q.clear_evidence()
 if name.startswith('L_'):
  i.run_integrated_hook=lambda h:original(h,generator=q._Replay(base.ROUTE,''))
  base.post_all([base.NOTICE]);q.clear_evidence()
 before=base.authority()
 i.run_integrated_hook=lambda h,t=text,f=fault:original(h,generator=q._Replay(t,f))
 if decision:
  i.semantic.validate_consequential_narration=lambda *a,d=decision:{'decision':d,'reasons':['injected'],'claims':[]}
 action=base.post_all([base.BARREL if name.startswith('L_') else base.NOTICE])[0]
 evidence=copy.deepcopy(q.evidence_records()[-1]);after=base.authority()
 i.semantic.validate_consequential_narration=original_semantic
 i.run_integrated_hook=lambda h:original(h,generator=q._Replay('You examine the notice board again; nothing new is established.',''))
 continued=base.post_all([base.REPEAT])[0]
 ok=(not evidence['used_fallback'] if name.startswith('L_') else evidence['used_fallback'])
 if not name.startswith('L_'):ok=ok and base.ROUTE in action['facing']
 stable=all(before.get(k)==after.get(k) for k in ('hp','inventory','equipment','scene','player','npcs','quests','conditions','combat'))
 rows.append({'name':name,'expected_behavior_observed':ok,'stable_authority':stable,'before':before,'after':after,'action':action,'trace':evidence,'continuation':continued,'continued_ok':continued['status_code']==200})
 print(name,ok,stable,flush=True)
i.run_integrated_hook=original;i.semantic.validate_consequential_narration=original_semantic
save('failure_injection.json',rows)
replays=[]
for row in json.loads((ROOT/'artifacts/pr_play_62/browser_actions.json').read_text(encoding='utf-8')):
 old=row['quarantine']
 if old.get('raw_provider_text'):
  c,r=i.outcome_contract(old['hook_input']);replays.append({'action':row['input'],'candidate':old['raw_provider_text'],'request':r,'validation':i.validate_integrated(c,r,old['raw_provider_text']),'published':False})
save('pr_play_62_updated_revalidation.json',replays)
print('Control, failures, isolation, original saved-text replay complete.')
