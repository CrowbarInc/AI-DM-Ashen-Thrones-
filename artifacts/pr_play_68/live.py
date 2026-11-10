"""One bounded real-provider sequence over actual TCP; never regenerated."""
import os,sys,json,copy,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
from artifacts.pr_play_67 import http_harness as h
h.OUT=OUT
from game import api,storage,expressive_dialogue
from game import integrated_investigation_narration as i,quarantined_investigation_narration as q
from game.provider_budget import snapshot
from tests.test_pr_play_68_structured_publication import action_payload
from game.config import get_openai_api_key
import openai
real_client=openai.OpenAI;real_hook=i.run_integrated_hook
assert not (OUT/'live_results.json').exists(),'Live sequence cannot be repeated'
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
os.environ['ASHEN_PROVIDER_USAGE_PATH']=str(OUT/'provider_usage.jsonl')
os.environ['ASHEN_PROVIDER_REQUEST_LIMIT']='6'
os.environ['ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT']='12000'
os.environ['ASHEN_PROVIDER_INPUT_TOKEN_LIMIT']='10000'
os.environ['ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT']='2000'
os.environ['ASHEN_PLAYTEST_DISABLE_SDK_RETRIES']='1'
q.reset_live_budget()
rows=[]
if not get_openai_api_key():
    save('live_results.json',dict(blocker='Configured provider credential unavailable',rows=[],provider_requests=0));raise SystemExit()
with h.seed('live_session',True) as mp,h.server() as request:
    mp.setattr(openai,'OpenAI',real_client);mp.setattr(i,'run_integrated_hook',real_hook)
    mp.setenv(q.LIVE_ENV,'1');mp.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION','0')
    actions=[('structured','I examine the notice board.'),('chat','I follow the missing patrol rumor.'),('structured','I examine the weathered milestone.'),('structured','I examine the weathered milestone again.'),('chat','I examine the mud prints.')]
    for path,text in actions:
        before=h.snapshot();q.clear_evidence()
        payload=action_payload(text,'notice board' if 'notice board' in text else 'weathered milestone') if path=='structured' else {'text':text}
        r=request('/api/action' if path=='structured' else '/api/chat',payload)
        r.update(input=text,authority_before=before,authority_after=h.snapshot(),trace=copy.deepcopy(q.evidence_records()[-1]) if q.evidence_records() else {})
        rows.append(r);save('live_results.json',dict(rows=rows,provider=snapshot()))
        trace=r['trace'];facing=(r.get('body',{}).get('gm_output') or {}).get('player_facing_text','')
        mandatory=(trace.get('authorized_outcome_contract') or {}).get('must_communicate',[])
        print(text,trace.get('provider_requests'),(trace.get('publication') or {}).get('decision'),flush=True)
        if r['hidden_exposures'] or any(f['text'] not in facing for f in mandatory):
            save('live_critical_stop.json',{'input':text,'reason':'hidden exposure or missing mandatory disclosure'});break
save('provider_snapshot.json',snapshot())
