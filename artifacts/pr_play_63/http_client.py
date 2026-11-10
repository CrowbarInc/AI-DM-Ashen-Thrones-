import json,time,urllib.request
from pathlib import Path
OUT=Path('artifacts/pr_play_63');base='http://127.0.0.1:8763'
checks={}
for path in ['/','/static/app.js','/api/state?ui_mode=player']:
 with urllib.request.urlopen(base+path,timeout=15) as r:
  body=r.read();checks[path]={'status':r.status,'bytes':len(body),'content_type':r.headers.get('Content-Type')}
(OUT/'http_frontend_reachability.json').write_text(json.dumps(checks,indent=2))
rows=[]
actions=['I examine the notice board.','I examine the rain barrel.','I examine the notice board again.','I examine the notice board for the patrol route.','I look around the gate.']
for text in actions:
 start=time.perf_counter()
 req=urllib.request.Request(base+'/api/chat?ui_mode=player',data=json.dumps({'text':text}).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=55) as r: body=json.load(r);status=r.status
 gm=body.get('gm_output') or {}
 rows.append({'input':text,'status_code':status,'http_client_ms':round((time.perf_counter()-start)*1000,3),'facing':gm.get('player_facing_text'),'marker':(gm.get('metadata') or {}).get('experimental_integrated_narration')})
 (OUT/'http_client_actions.json').write_text(json.dumps(rows,indent=2))
 print(json.dumps(rows[-1]),flush=True)
