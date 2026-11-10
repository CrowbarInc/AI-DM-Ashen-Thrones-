"""PR67 disposable browser procedure, with complete request/response evidence."""
import sys,time,json,copy,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from artifacts.pr_play_67 import http_harness as h
OUT=Path(__file__).resolve().parent;h.OUT=OUT
phase=sys.argv[1] if len(sys.argv)>1 else 'before'
from game import api,storage
from game import quarantined_investigation_narration as q
rows=[]
@api.app.middleware('http')
async def capture(request,call_next):
    start=time.perf_counter();raw=await request.body();before=h.snapshot()
    response=await call_next(request)
    body=b''.join([chunk async for chunk in response.body_iterator])
    from starlette.responses import Response
    row=dict(method=request.method,path=request.url.path,request=raw.decode(),status=response.status_code,body=body.decode(),http_ms=(time.perf_counter()-start)*1000,authority_before=before,authority_after=h.snapshot(),trace=copy.deepcopy(q.evidence_records()[-1:]))
    rows.append(row);(OUT/f'browser_{phase}_network.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    return Response(body,status_code=response.status_code,headers=dict(response.headers),media_type=response.media_type)
with h.seed('browser_'+phase,True),h.server() as request:
    import inspect
    port=inspect.getclosurevars(request).nonlocals['port']
    (OUT/f'browser_{phase}_target.json').write_text(json.dumps({'url':f'http://127.0.0.1:{port}/'}))
    print(f'http://127.0.0.1:{port}/',flush=True)
    for _ in range(6000):
        if (OUT/f'browser_{phase}_stop').exists():break
        time.sleep(.1)
