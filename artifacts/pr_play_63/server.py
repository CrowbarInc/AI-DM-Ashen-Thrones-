"""Disposable real HTTP application for five UI-originated actions only."""
import json, os, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from artifacts.pr_play_61 import run_experiment as base
OUT=ROOT/'artifacts/pr_play_63'
base.OUT=OUT
os.environ['ASHEN_PROVIDER_USAGE_PATH']=str(OUT/'provider_usage.jsonl')
os.environ['ASHEN_INTEGRATED_REPEAT_FAST_PATH']='1'
from game import api, storage
from game import quarantined_investigation_narration as q
from game.provider_budget import snapshot
base.disable_publication()
def save(name,data):
 (OUT/name).write_text(json.dumps(base.redact(data),indent=2,ensure_ascii=False),encoding='utf-8')
save('before_initialization.json',{'disposable_directory_exists':(OUT/'browser_session/data').exists(),'canonical_data_not_used':True})
base._seed(OUT/'browser_session',base._Patch(),'frontier_gate')
save('after_initialization.json',base.authority())
base.enable_publication(storage.load_session()['campaign_run_id'],live=base.key_present())
os.environ[q.LABEL_ENV]='pr_play_63_browser'
os.environ[q.EVIDENCE_ENV]=str(OUT/'quarantine_evidence')
q.reset_live_budget(); q.clear_evidence()
save('server_config.json',{'key_present':base.key_present(),'session_id':storage.load_session()['campaign_run_id'],'live_narration':'TESTED' if base.key_present() else 'NOT TESTED','flags':{k:os.environ.get(k) for k in [q.GATE_ENV,q.MODE_ENV,q.PUBLICATION_ENV,q.PUBLICATION_SESSION_ENV,q.LIVE_ENV,'ASHEN_INTEGRATED_REPEAT_FAST_PATH']},'max_ui_actions':5})
timings={}
for attr,key in [('_resolve_engine_noncombat_seam','resolution_ms'),('_publish_experimental_integrated_narration','publication_assembly_ms')]:
 original=getattr(api,attr)
 def wrap(*args,_fn=original,_key=key,**kwargs):
  start=time.perf_counter()
  try:return _fn(*args,**kwargs)
  finally:timings[_key]=round((time.perf_counter()-start)*1000,3)
 setattr(api,attr,wrap)
rows=[]
class Capture:
 def __init__(self,app):self.app=app
 async def __call__(self,scope,receive,send):
  if scope['type']!='http' or scope['path']!='/api/chat':
   return await self.app(scope,receive,send)
  if len(rows)>=5:
   await send({'type':'http.response.start','status':429,'headers':[]})
   return await send({'type':'http.response.body','body':b'Five-action experiment complete'})
  started=time.perf_counter(); incoming=[]; outgoing=[]; status=None
  before=base.authority(); timings.clear()
  async def recv():
   msg=await receive()
   if msg['type']=='http.request':incoming.append(msg.get('body',b''))
   return msg
  async def emit(msg):
   nonlocal status
   if msg['type']=='http.response.start':status=msg['status']
   if msg['type']=='http.response.body':outgoing.append(msg.get('body',b''))
   await send(msg)
  await self.app(scope,recv,emit)
  elapsed=round((time.perf_counter()-started)*1000,3)
  body=json.loads(b''.join(outgoing)); request=json.loads(b''.join(incoming))
  evidence=q.evidence_records()[-1] if q.evidence_records() else {}
  row={'input':request.get('text'),'status_code':status,'http_server_ms':elapsed,'timings':dict(timings),'before':before,'authority':base.authority(),'response':body,'quarantine':evidence,'published':base.facing(body),'candidate_words':len(str(evidence.get('raw_provider_text') or '').split()),'published_words':len(base.facing(body).split())}
  rows.append(row)
  save('browser_actions.json',rows)
  save('provider_snapshot.json',snapshot())
  save('final_session.json',storage.load_session())
  save(f'state_{len(rows):02}.json',storage.load_session())
  save('final_authority.json',base.authority())
app=Capture(api.app)
if __name__=='__main__':
 import uvicorn
 uvicorn.run(app,host='127.0.0.1',port=8763,log_level='warning')
