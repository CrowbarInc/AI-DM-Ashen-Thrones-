import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import pytest
from fastapi.testclient import TestClient
from game import api,storage
from tests.test_pr_eg_r2c_r2_reference_eligibility import record,FACT,Q
from tests.test_pr_ef_gm_authority import seed_scene
h=Path('artifacts/pr_eg_r2c_r2')
with pytest.MonkeyPatch.context() as mp:
 seed_scene(h/'clarification_probe_state',mp)
 w=storage.load_world();m=next(n for n in w['npcs'] if n['id']=='sergeant_mara');m['topics'].append(dict(id='night_watch',text=FACT));w['npcs'].append(dict(id='bren',name='Corporal Bren',location=m['location']));storage.save_world(w)
 mp.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0');mp.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
 mp.setattr('game.live_chat_interpretation.request_interpretation',lambda *a,**k:dict(ok=True,sent=False,text=json.dumps(record())))
 rows=[]
 for q in [Q,'I ask one of them about the north gate.','Can you repeat that?']:
  res=TestClient(api.app).post('/api/chat?ui_mode=player',json=dict(text=q,ui_mode='player')).json()
  rows.append(dict(player=q,result=res,context=storage.load_session().get('conversational_context')))
  print(q,res['gm_output']['player_facing_text'])
 (h/'clarification_probe.json').write_text(json.dumps(rows,indent=2,default=str))
