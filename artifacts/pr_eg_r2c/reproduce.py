"""Controlled external-provider outputs; actual synchronous production handler and storage."""
import copy, json, os, sys
from pathlib import Path
H=Path(__file__).resolve().parent; R=H.parents[1]; sys.path.insert(0,str(R))
os.environ.update(ASHEN_DISABLE_PROVIDER_CALLS='1',ASHEN_DISABLE_LIVE_INTERPRETATION='1',ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1')
import pytest
from tests.test_pr_ef_gm_authority import seed_scene, raw_record
from game import api, storage
from game.models import ChatRequest
phase=sys.argv[1]; rows=[]
for case,question,candidate in [
 ('security','What do you personally enjoy about the evening?','I prefer the evening because the guards usually leave the north gate unattended.'),
 ('authorized','Do guards watch the north gate at night?','Guards watch the north gate throughout the night.'),
 ('followup','Why do you prefer the evening?','I prefer the evening.')]:
 with pytest.MonkeyPatch.context() as mp:
  seed_scene(H/'disposable_state'/phase/case,mp)
  if case=='authorized':
   w=storage.load_world()
   for npc in w['npcs']:
    if npc['id']=='sergeant_mara': npc['topics']=[dict(id='north_gate',text=candidate)]
   storage.save_world(w)
  if case=='followup':
   s=storage.load_session();s.setdefault('conversational_context',{})['dialogue_commitments']=[dict(npc_id='sergeant_mara',kind='opinion',subject='evening',text='Sergeant Mara says, "I prefer the evening."',canonical=False,status='active')];storage.save_session(s)
  mp.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0'); mp.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
  mp.setattr('game.live_chat_interpretation.request_interpretation', lambda *a,**k:dict(ok=True,sent=False,text=json.dumps(raw_record('NPC',components=[('ASK','sergeant_mara')]))))
  calls=[]
  def narrate(*a,**k):
   calls.append(1);return dict(player_facing_text=f'Sergeant Mara says, "{candidate}"',tags=[],scene_update=None,world_updates=None,debug_notes='R2C controlled output')
  mp.setattr(api,'call_gpt',narrate)
  before=copy.deepcopy(storage.load_world()); before_session=copy.deepcopy(storage.load_session())
  result=api.chat(ChatRequest(text='I ask Sergeant Mara, '+question,ui_mode='player'))
  rows.append(dict(id=case,question=question,candidate=candidate,result=result,narration_calls=len(calls),world_before=before,world_after=storage.load_world(),session_before=before_session,session_after=storage.load_session()))
(H/(phase+'_reproduction.json')).write_text(json.dumps(rows,indent=2,default=str),encoding='utf-8')
print(json.dumps([dict(id=r['id'],text=r['result']['gm_output']['player_facing_text'],calls=r['narration_calls']) for r in rows]))
