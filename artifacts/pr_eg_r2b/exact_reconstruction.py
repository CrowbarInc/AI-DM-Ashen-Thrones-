"""Reproduce exact historical wording; compare matched ordinary ASK state effects."""
import copy,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(R))
os.environ.update(ASHEN_DATA_DIR=str(H/'disposable_state/exact'),ASHEN_DISABLE_PROVIDER_CALLS='1',ASHEN_DISABLE_LIVE_INTERPRETATION='1',ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1')
import pytest
from tests.test_pr_ef_gm_authority import seed_scene,raw_record
from game import api,storage
from game.models import ChatRequest
from game.conversational_continuity import continuity_directive
rows=[]
for mode,speech in [('safe','I prefer the evening.'),('unsafe','I prefer the evening because the guards usually leave the north gate unattended.')]:
 with pytest.MonkeyPatch.context() as mp:
  seed_scene(H/'disposable_state'/('exact_'+mode),mp)
  mp.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0');mp.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
  mp.setattr('game.live_chat_interpretation.request_interpretation',lambda *a,**k:dict(ok=True,sent=False,text=json.dumps(raw_record('NPC',components=[('ASK','sergeant_mara')]))))
  calls=[]
  def narration(*a,**k):
   calls.append(dict(keyword_names=list(k)))
   return dict(player_facing_text=f'Sergeant Mara says, "{speech}"',tags=[],scene_update=None,world_updates=None,debug_notes='R2B exact R2A control')
  mp.setattr(api,'call_gpt',narration)
  before=copy.deepcopy(storage.load_world());sb=copy.deepcopy(storage.load_session())
  response=api.chat(ChatRequest(text='I ask Sergeant Mara, What do you personally enjoy about the evening?',ui_mode='player'))
  sa=storage.load_session();after=storage.load_world();loaded=copy.deepcopy(sa)
  rows.append(dict(mode=mode,candidate=speech,before_world=before,after_world=after,response=response,narration_calls=len(calls),before_context=sb.get('conversational_context'),saved_context=sa.get('conversational_context'),roundtrip_equal=loaded==storage.load_session(),followup=continuity_directive('What did you mean by that?',session=sa,scene=storage.load_active_scene(),world=after)))
result=dict(trials=rows,initial_worlds_equal=rows[0]['before_world']==rows[1]['before_world'],final_worlds_equal=rows[0]['after_world']==rows[1]['after_world'],scope='Local synchronous handler; external interpretation and narration doubled, safety gates and persistence unchanged; no HTTP or fresh generation')
(H/'exact_reconstruction.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
print(json.dumps(dict(final_worlds_equal=result['final_worlds_equal'],trials=[dict(mode=r['mode'],calls=r['narration_calls'],delivered=r['response']['gm_output']['player_facing_text']) for r in rows])))
