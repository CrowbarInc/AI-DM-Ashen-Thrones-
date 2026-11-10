"""Disposable real HTTP and browser host reusing PR67 transport and PR66 setup."""
import sys,json,copy,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
from artifacts.pr_play_67 import http_harness as h
h.OUT=OUT
from game import api,storage,authored_consequences as c
from game import integrated_investigation_narration as i,quarantined_investigation_narration as q

def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def configure(mp):
 mp.setenv(c.GATE,'1');mp.setenv(c.SESSION,storage.load_session()['campaign_run_id'])
 original=i.run_integrated_hook
 mp.setattr(i,'run_integrated_hook',lambda hook,**kw:original(hook,generator=q._Replay('', '')))
def action(a):return dict(action_type='exploration',intent=a['label'],exploration_action={k:v for k,v in a.items() if k not in ['consequence','conditions']})
def byid(aid):return next(a for arr in json.loads(c.FIXTURE.read_text()).values() for a in arr if a['id']==aid)
def available(body):return [a['id'] for a in body.get('public_state',body).get('ui',{}).get('affordances',[])]

def run_http():
 allrows=[]
 for branch in ['survey','report']:
  with h.seed('http_'+branch,True) as mp,h.server() as request:
   configure(mp);rows=[]
   def call(path,payload=None):
    before=h.snapshot();r=request(path,payload);r.update(authority_before=before,authority_after=h.snapshot());rows.append(r);save('http_'+branch+'.json',rows)
    assert r['status']==200 and not r['hidden_exposures'],r
    return r['body']
   call('/api/state')
   call('/api/chat',{'text':'I examine the notice board.'})
   call('/api/chat',{'text':'I follow the missing patrol rumor.'})
   state=call('/api/chat',{'text':'I examine the weathered milestone.'})
   assert {'patrol_survey','patrol_report'} <= set(available(state))
   choice=byid('patrol_'+branch);opposite=byid('patrol_report' if branch=='survey' else 'patrol_survey')
   state=call('/api/action',action(choice));assert state['gm_output']['player_facing_text']==choice['consequence']['text']
   committed=copy.deepcopy(storage.load_world()['world_state']['flags'])
   for a in [choice,opposite]:
    call('/api/action',action(a));assert storage.load_world()['world_state']['flags']==committed
   if branch=='report':call('/api/chat',{'text':'I return to Cinderwatch Gate.'})
   follow=byid('patrol_record_survey' if branch=='survey' else 'patrol_warn_watch')
   assert follow['id'] in available(call('/api/state'))
   state=call('/api/action',action(follow));assert state['gm_output']['player_facing_text']==follow['consequence']['text']
   persisted=copy.deepcopy(storage.load_world()['world_state']['flags'])
   saved=call('/api/snapshots',{'label':'PR70 branch persistence'})
   call('/api/snapshots/load',{'snapshot_id':saved['snapshot']['id']})
   assert storage.load_world()['world_state']['flags']==persisted
   call('/api/action',action(follow));assert storage.load_world()['world_state']['flags']==persisted
   call('/api/chat',{'text':'I examine the notice board.' if branch=='report' else 'I examine the mud prints.'})
   assert storage.load_world()['world_state']['flags']==persisted
   allrows.extend(rows)
 save('http_summary.json',dict(requests=len(allrows),gameplay_actions=sum(r['request']['path'] in ['/api/action','/api/chat'] for r in allrows),hidden_exposures=sum(bool(r['hidden_exposures']) for r in allrows),average_ms=sum(r['http_ms'] for r in allrows)/len(allrows),maximum_ms=max(r['http_ms'] for r in allrows)))

def browser(branch):
 from starlette.responses import Response
 rows=[]
 @api.app.middleware('http')
 async def capture(request,call_next):
  start=time.perf_counter();raw=await request.body();before=h.snapshot()
  response=await call_next(request);body=b''.join([chunk async for chunk in response.body_iterator])
  if request.url.path.startswith('/api/'):
   row=dict(path=request.url.path,method=request.method,request=raw.decode(),status=response.status_code,body=body.decode(),authority_before=before,authority_after=h.snapshot(),http_ms=(time.perf_counter()-start)*1000)
   rows.append(row);save('browser_'+branch+'_network.json',rows)
  return Response(body,status_code=response.status_code,headers=dict(response.headers),media_type=response.media_type)
 with h.seed('browser_'+branch,True) as mp,h.server() as request:
  configure(mp)
  import inspect
  port=inspect.getclosurevars(request).nonlocals['port'];save('browser_target.json',dict(branch=branch,url=f'http://127.0.0.1:{port}/'))
  print(f'http://127.0.0.1:{port}/',flush=True)
  while not (OUT/('browser_'+branch+'_stop')).exists():time.sleep(.2)
if __name__=='__main__':
 if len(sys.argv)>1:browser(sys.argv[1])
 else:run_http()
