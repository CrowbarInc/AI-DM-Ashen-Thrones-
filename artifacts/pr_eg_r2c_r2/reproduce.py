from pathlib import Path
import sys,json,copy
sys.path.insert(0,str(Path.cwd()))
import pytest
from fastapi.testclient import TestClient
from tests.test_pr_ef_gm_authority import seed_scene
from game import storage
from game.api import app
h=Path('artifacts/pr_eg_r2c_r2')
old=json.loads(Path('artifacts/pr_eg_r2c_r1/live_qualification.json').read_text())['primary'][6]
def find(v,k):
 if isinstance(v,dict):
  if k in v:return v[k]
  for x in v.values():
   r=find(x,k)
   if r is not None:return r
 if isinstance(v,list):
  for x in v:
   r=find(x,k)
   if r is not None:return r
raw=find(old['result'],'raw_interpretation')
(h/'historical_interpretation.json').write_text(raw)
if '--baseline' in sys.argv:
 import game.player_interpretation_bridge as bridge, game.live_chat_interpretation as live
 for module in [bridge,live]:
  exec(compile((h/'before_sources/game'/Path(module.__file__).name).read_text(),module.__file__,'exec'),module.__dict__)
 import game.api as api
 api.interpret_production_turn=live.interpret_production_turn
 api.normalized_action_from_interpretation=bridge.normalized_action_from_interpretation
with pytest.MonkeyPatch.context() as mp:
 seed_scene(h/'reproduction_state',mp)
 w=storage.load_world();next(n for n in w['npcs'] if n['id']=='sergeant_mara').setdefault('topics',[]).append(dict(id='night_watch',text='Guards watch the north gate throughout the night.'));storage.save_world(w)
 mp.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0');mp.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
 calls=[]
 def wire(*a,**k):calls.append('interpretation');return dict(ok=True,sent=False,text=raw)
 mp.setattr('game.live_chat_interpretation.request_interpretation',wire)
 before=copy.deepcopy(storage.load_world());sb=copy.deepcopy(storage.load_session())
 result=TestClient(app).post('/api/chat?ui_mode=player',json=dict(text=old['player'],ui_mode='player')).json()
 (h/('after_reproduction.json' if '--after' in sys.argv else 'before_reproduction.json')).write_text(json.dumps(dict(evidence_class='recorded-provider output injected at wire; real HTTP/resolvers',player=old['player'],raw=json.loads(raw),result=result,world_before=before,world_after=storage.load_world(),session_before=sb,session_after=storage.load_session(),wire_calls=calls),indent=2,default=str))
 print(result.get('gm_output',{}).get('player_facing_text'));print(json.dumps(result.get('resolution',{}),default=str)[:1000])
