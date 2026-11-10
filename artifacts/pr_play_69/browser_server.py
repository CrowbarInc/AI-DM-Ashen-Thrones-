"""One browser-originated live sequence; isolated state, capped provider usage."""
import sys,time,json,copy,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
from artifacts.pr_play_67 import http_harness as h
h.OUT=OUT
from game import api,storage
from game import quarantined_investigation_narration as q,integrated_investigation_narration as i
from game.provider_budget import snapshot
from game.config import get_openai_api_key
import openai
real_client=openai.OpenAI;real_hook=i.run_integrated_hook
assert not (OUT/'browser_network.json').exists(),'No regeneration'
assert get_openai_api_key(),'Configured provider unavailable'
for key,value in {'ASHEN_PROVIDER_USAGE_PATH':str(OUT/'provider_usage.jsonl'),
    'ASHEN_PROVIDER_REQUEST_LIMIT':'6','ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT':'12000',
    'ASHEN_PROVIDER_INPUT_TOKEN_LIMIT':'10000','ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT':'4000',
    'ASHEN_PLAYTEST_DISABLE_SDK_RETRIES':'1'}.items():os.environ[key]=value
q.reset_live_budget();rows=[]
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
@api.app.middleware('http')
async def capture(request,call_next):
    start=time.perf_counter();raw=await request.body();before=h.snapshot();q.clear_evidence()
    response=await call_next(request)
    body=b''.join([chunk async for chunk in response.body_iterator])
    from starlette.responses import Response
    row=dict(method=request.method,path=request.url.path,request=raw.decode(),status=response.status_code,
        body=body.decode(),http_ms=(time.perf_counter()-start)*1000,
        authority_before=before,authority_after=h.snapshot(),trace=copy.deepcopy(q.evidence_records()[-1:]))
    if request.url.path.startswith('/api/'):
        rows.append(row);save('browser_network.json',rows);save('provider_snapshot.json',snapshot())
    if request.url.path in {'/api/action','/api/chat'}:
        parsed=json.loads(body);facing=(parsed.get('gm_output') or {}).get('player_facing_text','')
        mandatory=[f['text'] for t in row['trace'] for f in t.get('authorized_outcome_contract',{}).get('must_communicate',[])]
        if h.scan(parsed) or any(f not in facing for f in mandatory):
            os.environ[q.PUBLICATION_ENV]='0';save('critical_stop.json',dict(reason='leak or omitted disclosure',path=request.url.path))
    return Response(body,status_code=response.status_code,headers=dict(response.headers),media_type=response.media_type)
with h.seed('browser_session',True) as mp,h.server() as request:
    # Override the inherited harness adapter; no production workaround for _Replay.
    mp.setattr(openai,'OpenAI',real_client);mp.setattr(i,'run_integrated_hook',real_hook)
    mp.setenv(q.LIVE_ENV,'1');mp.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION','0')
    import inspect
    port=inspect.getclosurevars(request).nonlocals['port']
    save('browser_target.json',dict(url=f'http://127.0.0.1:{port}/'))
    print(f'http://127.0.0.1:{port}/',flush=True)
    for _ in range(18000):
        if (OUT/'browser_stop').exists():break
        time.sleep(.1)
