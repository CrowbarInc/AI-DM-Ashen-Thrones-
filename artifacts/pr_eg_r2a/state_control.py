"""Matched ordinary ASK world mutation control, no semantic validator retuning."""
import copy,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[1]))
os.environ.update(ASHEN_DATA_DIR=str(H/'disposable_state'/'control'),ASHEN_DISABLE_PROVIDER_CALLS='1',ASHEN_DISABLE_LIVE_INTERPRETATION='1',ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1')
import pytest
from tests.test_pr_ef_gm_authority import seed_scene,raw_record
from game import api,storage
from game.models import ChatRequest
results=[]
for mode,speech in [('safe','I prefer the evening.'),('unsafe','I prefer the evening because the guards usually leave the north gate unattended.')]:
 with pytest.MonkeyPatch.context() as mp:
  seed_scene(H/'disposable_state'/('control_'+mode),mp)
  mp.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0');mp.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
  mp.setattr('game.live_chat_interpretation.request_interpretation',lambda *a,**k:dict(ok=True,sent=False,text=json.dumps(raw_record('NPC',components=[('ASK','sergeant_mara')]))))
  mp.setattr(api,'call_gpt',lambda *a,**k:dict(player_facing_text=f'Sergeant Mara says, "{speech}"',tags=[],scene_update=None,world_updates=None,debug_notes='R2A matched control'))
  before=copy.deepcopy(storage.load_world());response=api.chat(ChatRequest(text='I ask Sergeant Mara, What do you personally enjoy about the evening?',ui_mode='player'))
  results.append(dict(mode=mode,before_world=before,after_world=storage.load_world(),delivered=response['gm_output']['player_facing_text'],turn=storage.load_session().get('turn_counter'),commitments=storage.load_session().get('conversational_context')))
result=dict(trials=results,initial_worlds_equal=results[0]['before_world']==results[1]['before_world'],final_worlds_equal=results[0]['after_world']==results[1]['after_world'],scope='Matched synchronous production handler, external wire doubles, actual resolver/tick/guards/save; no HTTP or fresh generation.')
(H/'state_control.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='trials'}))
