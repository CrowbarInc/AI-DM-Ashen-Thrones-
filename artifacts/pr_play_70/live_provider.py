"""Bounded shadow provider experiment; candidates cannot reach publication/state."""
import sys,os,json,copy,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
from game import quarantined_investigation_narration as q
from game.config import get_openai_api_key
from game.provider_budget import snapshot
assert not (OUT/'live_provider_results.json').exists(),'No regeneration'
for k,v in {'ASHEN_PROVIDER_USAGE_PATH':str(OUT/'provider_usage.jsonl'),'ASHEN_PROVIDER_REQUEST_LIMIT':'6','ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT':'12000','ASHEN_PROVIDER_INPUT_TOKEN_LIMIT':'10000','ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT':'2000','ASHEN_PLAYTEST_DISABLE_SDK_RETRIES':'1','ASHEN_DISABLE_EXPRESSION_GENERATION':'0'}.items():os.environ[k]=v
q.reset_live_budget();rows=[]
if get_openai_api_key():
 for branch in ['survey','report']:
  source=json.loads((OUT/f'http_{branch}.json').read_text())
  selected=[r for r in source if r['request']['path']=='/api/action' and r['body'].get('gm_output',{}).get('player_facing_text','').startswith(('You commit','You record','The watch receives'))]
  for r in selected:
   trusted=r['body']['gm_output']['player_facing_text'];action=r['request']['json']['intent'];gen=q._LivePrelude(action)
   start=time.perf_counter();error=None
   try:raw=gen.generate({'selected_branch':branch,'trusted_outcome':trusted,'allowed_additions':'Nonconsequential atmosphere only; do not repeat or change the outcome.'})
   except Exception as exc:raw=None;error=type(exc).__name__
   row=dict(branch=branch,action=action,raw_candidate=raw,authoritative_outcome=trusted,final_response=trusted,provider=q._live_metadata(gen),validation_decision='NOT_ADMITTED',publication_decision='trusted_deterministic',fallback_reason='authored_consequence_provider_free_policy',total_ms=(time.perf_counter()-start)*1000,error=error)
   rows.append(row);(OUT/'live_provider_results.json').write_text(json.dumps(dict(rows=rows,provider=snapshot(),mode='shadow_only_no_AI_publication'),indent=2))
else:(OUT/'live_provider_results.json').write_text(json.dumps({'rows':[],'blocker':'Configured credential unavailable','requests':0}))
