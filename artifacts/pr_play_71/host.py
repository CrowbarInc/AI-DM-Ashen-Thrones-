"""Normal application host, isolated bootstrap copies; no seeded runtime or provider mocks."""
import sys, os, json, shutil, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
DATA=OUT/'normal_data'
if not DATA.exists():
    DATA.mkdir()
    for name in ['campaign.json','character.json','world.json','conditions.json']:
        shutil.copy2(ROOT/'data'/name,DATA/name)
    shutil.copytree(ROOT/'data/scenes',DATA/'scenes')
os.environ['ASHEN_DATA_DIR']=str(DATA)
os.environ['ASHEN_PROVIDER_USAGE_PATH']=str(OUT/('provider_usage_'+str(os.getpid())+'.jsonl'))
os.environ['ASHEN_EXPERIMENTAL_BRANCHING']='1'
os.environ['ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS']='1'
os.environ['ASHEN_DISABLE_PROVIDER_RETRIES']='1'
os.environ['ASHEN_PLAYTEST_DISABLE_SDK_RETRIES']='1'
from game import api,storage
from starlette.responses import Response
import uvicorn
def snapshot():
    return {n:getattr(storage,'load_'+n)() for n in ['session','world','character','combat']}
@api.app.middleware('http')
async def capture(request,call_next):
    start=time.perf_counter(); raw=await request.body()
    before=snapshot() if request.url.path.startswith('/api/') else None
    response=await call_next(request)
    body=b''.join([chunk async for chunk in response.body_iterator])
    if before is not None:
        row=dict(path=request.url.path,method=request.method,request=raw.decode(),status=response.status_code,body=body.decode(),authority_before=before,authority_after=snapshot(),server_ms=(time.perf_counter()-start)*1000)
        with (OUT/'browser_network.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    return Response(body,status_code=response.status_code,headers=dict(response.headers),media_type=response.media_type)
if __name__=='__main__':uvicorn.run(api.app,host='127.0.0.1',port=8071,log_level='info')
