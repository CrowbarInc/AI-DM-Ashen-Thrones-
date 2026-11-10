import sys,json,os
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_play_63'
from artifacts.pr_play_61 import run_experiment as b
b.OUT=OUT
from game import storage,api
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
api.call_gpt=lambda *a,**k:_gm_response('Provider calls are disabled for this run, so no live narration was generated.')
b._seed(OUT/'different_player',b._Patch(),'frontier_gate')
c=storage.load_character();c['id']='pr63_other_player';storage._save_json(storage.CHARACTER_PATH,c)
b.enable_publication(storage.load_session()['campaign_run_id'],live=False)
original=i.run_integrated_hook;i.run_integrated_hook=lambda h:original(h,generator=q._Replay('You examine the rain barrel; no new clue is established.',''))
q.clear_evidence();rows=b.post_all([b.BARREL]);trace=q.evidence_records()[-1]
result={'authority':b.authority(),'action':rows[0],'trace':trace,'no_prior_route_in_context':b.ROUTE not in json.dumps(trace.get('authorized_outcome_contract')),'fresh_player_id':c['id']}
(OUT/'different_player_isolation.json').write_text(json.dumps(result,indent=2));print(result['no_prior_route_in_context'])
