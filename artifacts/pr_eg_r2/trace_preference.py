"""Exact ordinary follow-up trace with seeded delivered preference, no model doubles."""
import os,sys,json,copy
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
os.environ['ASHEN_DATA_DIR']=str(HERE/'disposable_state'/'trace')
os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION']='1'
import pytest
from tests.test_pr_ef_gm_authority import seed_scene
from game import storage,api
from game.models import ChatRequest
from game.dialogue_authority import build_dialogue_authority,remember_dialogue_commitment
from game.conversational_continuity import record_delivered_exchange,continuity_directive
with pytest.MonkeyPatch.context() as mp:
 seed_scene(HERE/'disposable_state'/'trace',mp)
 session=storage.load_session(); world=storage.load_world(); scene=storage.load_active_scene()
 session['interaction_context']={'active_interaction_kind':'social','active_interaction_target_id':'sergeant_mara'}
 question='Do you prefer the morning or the evening?'
 social={'npc_id':'sergeant_mara','npc_name':'Sergeant Mara','target_resolved':True,
  'reply_plan_kind':'harmless_subjective_response_permitted','incidental_subjective_allowed':True}
 social['dialogue_authority']=build_dialogue_authority(question,npc={'id':'sergeant_mara','name':'Sergeant Mara'},social=social)
 line='Sergeant Mara says, "I prefer the evening."'
 remember_dialogue_commitment(session,social=social,player_text=question,line=line,turn=1)
 record_delivered_exchange(session,player_text=question,delivered_text=line,social=social,scene_id='waystation_courtyard',turn=1)
 storage.save_session(session)
 q='Why do you prefer the evening?'
 directive=continuity_directive(q,session=session,scene=scene,world=world)
 before=copy.deepcopy(session); world_before=copy.deepcopy(world)
 calls=[]
 def prohibited(*a,**k):
  calls.append(k); raise AssertionError('Unexpected provider call in exact preference follow-up')
 mp.setattr(api,'call_gpt',prohibited)
 try:
  response=api.chat(ChatRequest(text=q,ui_mode='player'))
  result={'directive':directive,'response':response,'world_unchanged':storage.load_world()==world_before,
   'turn_before':before.get('turn_counter'),'turn_after':storage.load_session().get('turn_counter'),
   'session_after':storage.load_session(),'narration_calls':len(calls)}
 except Exception as exc: result={'directive':directive,'error':str(exc),'calls':calls}
 (HERE/'exact_preference_trace.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
 print(json.dumps({'directive':directive,'text':((result.get('response') or {}).get('gm_output') or {}).get('player_facing_text'),
  'narration_calls':result.get('narration_calls'),'error':result.get('error')}))
