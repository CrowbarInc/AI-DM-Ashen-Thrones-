"""Actual localhost TCP gameplay; provider-free saved-candidate experiment."""
import sys,json,copy,threading,socket,time,urllib.request,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_66 import harness as h
from game import api,storage
from game import quarantined_investigation_narration as q
import uvicorn
OUT=h.OUT
h.seed('tcp_gameplay');actions=['I examine the notice board.','I follow the missing patrol rumor.','I examine the weathered milestone.','I examine the weathered milestone again.','I examine the weathered milestone.']
constructed=[];event=threading.Event();serialize=[]
from starlette.responses import JSONResponse
original_render=JSONResponse.render

def render(self,content):
    start=time.perf_counter()
    try:return original_render(self,content)
    finally:serialize.append((time.perf_counter()-start)*1000)
JSONResponse.render=render
async def app(scope,receive,send):
    parts=[];start=time.perf_counter()
    async def capture(message):
        if message['type']=='http.response.body':parts.append(message.get('body',b''))
        await send(message)
    try:await api.app(scope,receive,capture)
    finally:
        if scope['type']=='http':
            constructed.append(dict(path=scope.get('path'),body=b''.join(parts).decode(),elapsed_ms=(time.perf_counter()-start)*1000));event.set()
sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
server=uvicorn.Server(uvicorn.Config(app,log_level='error',lifespan='off'))
thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
for _ in range(200):
    if server.started:break
    time.sleep(.025)
assert server.started
rows=[]
try:
    for index,text in enumerate(actions):
        raw='You examine the notice board.' if index==0 else h.historical()['full_trace']['raw_provider_text'] if index==2 else ''
        h.candidate(raw,'provider_error' if index==4 else '')
        q.clear_evidence();before=dict(session=storage.load_session(),character=storage.load_character(),world=storage.load_world(),combat=storage.load_combat())
        start=time.perf_counter();request=urllib.request.Request(f'http://127.0.0.1:{port}/api/chat?ui_mode=player',data=json.dumps({'text':text}).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=45) as response:body=json.load(response);status=response.status
        elapsed=(time.perf_counter()-start)*1000;trace=copy.deepcopy(q.evidence_records()[-1]) if q.evidence_records() else None
        facing=body['gm_output']['player_facing_text']
        if trace and trace.get('eligible'):
            assert all(f['text'] in facing for f in trace['authorized_outcome_contract']['must_communicate'])
        rows.append(dict(request={'path':request.full_url,'json':{'text':text}},status=status,body=body,facing=facing,
            trace=trace,state_before=before,state_after=dict(session=storage.load_session(),character=storage.load_character(),world=storage.load_world(),combat=storage.load_combat()),http_ms=elapsed))
        h.save('http_gameplay.json',rows)
    assert rows[1]['state_after']['session']['active_scene_id']=='old_milestone'
    assert h.historical()['full_trace']['trusted_disclosure'] in rows[2]['facing']
    # Send a complete request then disconnect before reading any response.
    h.candidate(None,'provider_error');q.clear_evidence();event.clear();prior=len(constructed)
    payload=json.dumps({'text':'I examine the weathered milestone again.'}).encode()
    connection=socket.create_connection(('127.0.0.1',port));connection.sendall(f'POST /api/chat?ui_mode=player HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: {len(payload)}\r\nConnection: close\r\n\r\n'.encode()+payload);connection.close()
    assert event.wait(20)
    trace=copy.deepcopy(q.evidence_records()[-1])
    h.save('client_interruption.json',dict(client_received='not_claimed',server_constructed=len(constructed)>prior,construction=constructed[-1],trace=trace))
    h.save('latency.json',dict(http_ms=[r['http_ms'] for r in rows],average_ms=statistics.mean(r['http_ms'] for r in rows),maximum_ms=max(r['http_ms'] for r in rows),http_serialization_ms=serialize,comparison='Provider-free saved candidate TCP sequence is not comparable to PR65 live TestClient timings.'))
    h.save('provider_usage.json',dict(live_requests=0,total_tokens=0,reason='Live provider experiment secondary; exact saved PR65 candidate and controlled errors used. No connectivity probe or live retry.',accepted=sum((r['trace'] or {}).get('publication',{}).get('decision')=='published' for r in rows),published=sum((r['trace'] or {}).get('publication',{}).get('decision')=='published' for r in rows),fallbacks=sum((r['trace'] or {}).get('publication',{}).get('decision')=='fallback' for r in rows)))
    print('TCP gameplay',len(rows),'PASS', [r['facing'] for r in rows])
finally:
    server.should_exit=True;thread.join(10)
