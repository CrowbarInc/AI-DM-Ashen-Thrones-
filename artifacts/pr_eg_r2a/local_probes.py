"""Exercise existing host seams with disposable fixtures. Never import historical executable scripts."""
import copy, hashlib, json, os, sys, time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(R))
os.environ.update(ASHEN_DATA_DIR=str(H/'disposable_state'),ASHEN_DISABLE_PROVIDER_CALLS='1',ASHEN_DISABLE_LIVE_INTERPRETATION='1',ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1')
def write(n,x): (H/n).write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
rows=json.loads((H/'corpus.json').read_text(encoding='utf-8'))
from game.dialogue_authority import build_dialogue_authority
from game.immutable_valid_response import validate_generated_response,run_preserve_if_valid
from game.gm_resolution_decision import build_gm_resolution_decision
from experiments.pr_dq.world import build_disposable_world
from game.social import apply_authored_knowledge_realization_to_gm
built=build_disposable_world();scene=built['scenes']['waystation_courtyard'];world=built['world']
capture=json.loads((R/'artifacts/pr_eg_r2/production_captures_offline.json').read_text(encoding='utf-8'))[0]
def fixture(c):
 ctx=c['authorized_context'];personal=c['context_id']=='personal'
 social=dict(npc_id='sergeant_mara',npc_name='Sergeant Mara',target_resolved=True,reply_plan_kind='harmless_subjective_response_permitted' if personal else 'genuine_uncertainty',incidental_subjective_allowed=personal,npc_speech_authority='claim_only' if personal else 'none',objective_world_fact_authority='none',durable_state_mutation_allowed=False)
 facts=ctx['facts']
 if facts:
  social.update(topic_revealed=dict(id=facts[0]['id'],text=facts[0]['text']),reply_plan_kind='authoritative_answer_available')
 authority=build_dialogue_authority(c['player_question'],npc=dict(id='sergeant_mara',name='Sergeant Mara',role='guard'),social=social)
 social['dialogue_authority']=authority
 contract=copy.deepcopy(capture['resolution']['metadata']['resolution_contract']);contract.update(raw_input=c['player_question'],contract_id='r2a_'+c['id'])
 resolution=dict(kind='social_exchange',prompt=c['player_question'],requires_check=False,social=social,metadata=dict(resolution_contract=contract,ordinary_contract_established=True,selected_resolver='social'))
 decision=build_gm_resolution_decision(resolution=resolution,scene=scene,world=world,session={});decision=decision.as_dict() if hasattr(decision,'as_dict') else decision
 resolution['metadata']['gm_resolution_decision']=decision
 return social,contract,resolution,decision
checks=[]
for c in rows:
 social,contract,resolution,decision=fixture(c);text=c['candidate']
 if not text.startswith('Sergeant Mara'):text=f'Sergeant Mara says, "{text}"'
 start=time.perf_counter();before=copy.deepcopy((scene,world,resolution))
 result=validate_generated_response(text,contract=contract,decision=decision,player_text=c['player_question'],resolution=resolution,authored_corpus=' '.join(f['text'] for f in c['authorized_context']['facts']),present_addressee='Sergeant Mara')
 checks.append(dict(id=c['id'],expected=c['expected'],risk=c['risk'],text=text,result=result,latency_ms=(time.perf_counter()-start)*1000,inputs_unchanged=before==(scene,world,resolution),scope='direct production hard validator; synthetic resolution, no complete turn'))
write('existing_validator.json',checks)
probe_ids=['paraphrase01','incidental01','commitment01','expansion01','mixed01','hidden01','incidental02']
adoption=[]
for cid in probe_ids:
 c=next(x for x in rows if x['id']==cid);social,contract,resolution,decision=fixture(c)
 text=f'Sergeant Mara says, "{c["candidate"]}"';gm=dict(player_facing_text=text,tags=[],scene_update=None,world_updates=None,metadata={})
 before=copy.deepcopy((scene,world,resolution))
 sealed=run_preserve_if_valid(copy.deepcopy(gm),regenerate=None,resolution=resolution,player_text=c['player_question'],scene=scene,world=world,session={},authored_corpus=' '.join(f['text'] for f in c['authorized_context']['facts']),present_addressee='Sergeant Mara')
 after=apply_authored_knowledge_realization_to_gm(copy.deepcopy(sealed),player_text=c['player_question'],resolution=resolution,scene=scene,world=world,session={})
 adoption.append(dict(id=cid,candidate=text,sealed=sealed,after_realization=after,identical_after_preseal=text==sealed.get('player_facing_text'),identical_after_realization=text==after.get('player_facing_text'),inputs_unchanged=before==(scene,world,resolution),scope='ordered existing preseal and authored-realization helpers; no HTTP/final gate or delivered persistence'))
write('adoption_partial.json',adoption)
# Complete synchronous chat handler with ONLY external interpretation/narration seams doubled.
import pytest
from tests.test_pr_ef_gm_authority import seed_scene,raw_record
from game import storage,api
from game.models import ChatRequest
from game.conversational_continuity import record_delivered_exchange,continuity_directive
from game.dialogue_authority import remember_dialogue_commitment
full=[]
for cid in probe_ids:
 c=next(x for x in rows if x['id']==cid)
 with pytest.MonkeyPatch.context() as mp:
  seed_scene(H/'disposable_state'/cid,mp)
  # Restore only provider eligibility, using known existing test seams; no validators patched.
  mp.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0');mp.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
  mp.setattr('game.live_chat_interpretation.request_interpretation',lambda *a,**k:dict(ok=True,sent=False,text=json.dumps(raw_record('NPC',components=[('ASK','sergeant_mara')]))))
  calls=[];candidate=f'Sergeant Mara says, "{c["candidate"]}"'
  def narration(*a,**k):
   calls.append(dict(args_count=len(a),keyword_names=list(k)))
   return dict(player_facing_text=candidate,tags=[],scene_update=None,world_updates=None,debug_notes='R2A synthetic candidate via narration seam')
  mp.setattr(api,'call_gpt',narration)
  session_before=copy.deepcopy(storage.load_session());world_before=copy.deepcopy(storage.load_world())
  try:
   response=api.chat(ChatRequest(text='I ask Sergeant Mara, '+c['player_question'],ui_mode='player'))
   session_after=storage.load_session();delivered=(response.get('gm_output') or {}).get('player_facing_text')
   full.append(dict(id=cid,offered_candidate=candidate,candidate_requested=bool(calls),narration_calls=len(calls),delivered=delivered,identical=delivered==candidate,response=response,world_changed=storage.load_world()!=world_before,turn_before=session_before.get('turn_counter'),turn_after=session_after.get('turn_counter'),delivered_exchanges=session_after.get('conversational_context',{}).get('delivered_exchanges'),scope='synchronous production chat function; external wire doubles, no HTTP transport, no fresh narration, resolver retains actual fixture authority (not corpus labels)'))
  except Exception as e:full.append(dict(id=cid,error=repr(e),narration_calls=len(calls)))
write('adoption_chat.json',full)
# Exact seeded historical overwrite recheck plus save/load. Seeding recorders is not generation adoption.
with pytest.MonkeyPatch.context() as mp:
 seed_scene(H/'disposable_state'/'continuity',mp)
 session=storage.load_session();scene=storage.load_active_scene();world=storage.load_world()
 session['interaction_context']=dict(active_interaction_kind='social',active_interaction_target_id='sergeant_mara')
 q='Do you prefer the morning or the evening?';line='Sergeant Mara says, "I prefer the evening."'
 social=dict(npc_id='sergeant_mara',npc_name='Sergeant Mara',target_resolved=True,reply_plan_kind='harmless_subjective_response_permitted',incidental_subjective_allowed=True)
 social['dialogue_authority']=build_dialogue_authority(q,npc=dict(id='sergeant_mara',name='Sergeant Mara'),social=social)
 remember_dialogue_commitment(session,social=social,player_text=q,line=line,turn=1)
 record_delivered_exchange(session,player_text=q,delivered_text=line,social=social,scene_id='waystation_courtyard',turn=1)
 before_world=copy.deepcopy(storage.load_world());storage.save_session(session);loaded=storage.load_session()
 result=dict(roundtrip_equal=loaded.get('conversational_context')==session.get('conversational_context'),recorders_world_unchanged=before_world==storage.load_world(),seeded_context=loaded.get('conversational_context'))
 follow='Why do you prefer the evening?';result['directive']=continuity_directive(follow,session=loaded,scene=scene,world=world)
 def no_provider(*a,**k):raise AssertionError('Unexpected provider request')
 mp.setattr(api,'call_gpt',no_provider)
 try:result['response']=api.chat(ChatRequest(text=follow,ui_mode='player'));result['saved_after']=storage.load_session().get('conversational_context')
 except Exception as e:result['error']=repr(e)
 write('continuity_recheck.json',result)
before=json.loads((H/'protected_before.json').read_text());after={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in before}
write('source_integrity.json',dict(protected_files=len(before),changed=[p for p in before if before[p]!=after[p]],hashes=after))
print(json.dumps(dict(existing_validator_cases=len(checks),partial_probes=len(adoption),chat_probes=len(full),protected_changed=[p for p in before if before[p]!=after[p]])))
