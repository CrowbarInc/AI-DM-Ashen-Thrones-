"""Current production seams, synthetic contracts, disposable storage. No safety hooks replaced."""
import copy,hashlib,json,os,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(R));sys.path.insert(0,str(H))
os.environ.update(ASHEN_DATA_DIR=str(H/'disposable_state/local'),ASHEN_DISABLE_PROVIDER_CALLS='1',ASHEN_DISABLE_LIVE_INTERPRETATION='1',ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1')
from experiment import contract as speech_contract,deterministic
def read(n):return json.loads((H/n).read_text(encoding='utf-8'))
def write(n,x):(H/n).write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
from game.dialogue_authority import build_dialogue_authority
from game.immutable_valid_response import validate_generated_response,run_preserve_if_valid
from game.gm_resolution_decision import build_gm_resolution_decision
from experiments.pr_dq.world import build_disposable_world
built=build_disposable_world();scene=built['scenes']['waystation_courtyard'];world=built['world']
capture=json.loads((R/'artifacts/pr_eg_r2/production_captures_offline.json').read_text())[0]
def fixture(c):
 personal=c['context_id']=='personal';facts=c['authorized_context']['facts']
 social=dict(npc_id='sergeant_mara',npc_name='Sergeant Mara',target_resolved=True,reply_plan_kind='harmless_subjective_response_permitted' if personal else 'genuine_uncertainty',incidental_subjective_allowed=personal,npc_speech_authority='claim_only' if personal else 'none',objective_world_fact_authority='none',durable_state_mutation_allowed=False)
 if facts:social.update(topic_revealed=dict(id=facts[0]['id'],text=facts[0]['text']),reply_plan_kind='authoritative_answer_available')
 social['dialogue_authority']=build_dialogue_authority(c['player_question'],npc=dict(id='sergeant_mara',name='Sergeant Mara'),social=social)
 con=copy.deepcopy(capture['resolution']['metadata']['resolution_contract']);con.update(raw_input=c['player_question'],contract_id='r2b:'+c['id'])
 res=dict(kind='social_exchange',prompt=c['player_question'],requires_check=False,social=social,metadata=dict(resolution_contract=con,ordinary_contract_established=True,selected_resolver='social'))
 decision=build_gm_resolution_decision(resolution=res,scene=scene,world=world,session={});decision=decision.as_dict() if hasattr(decision,'as_dict') else decision
 res['metadata']['gm_resolution_decision']=decision
 return con,res,decision
local=[]
for c in read('corpus.json')+read('supplement.json'):
 con,res,decision=fixture(c);text=c['candidate']
 if not text.startswith('Sergeant Mara'):text=f'Sergeant Mara says, "{text}"'
 args=dict(contract=con,decision=decision,player_text=c['player_question'],resolution=res,authored_corpus=' '.join(f['text'] for f in c['authorized_context']['facts']),present_addressee='Sergeant Mara')
 start=time.perf_counter();a=validate_generated_response(text,**args)
 # Experimental adapter passes contract data through existing structures; no invented validator support.
 adapted=copy.deepcopy(res);adapted['metadata']['authorized_speech_contract']=speech_contract(c)
 b=validate_generated_response(text,**{**args,'resolution':adapted})
 local.append(dict(id=c['id'],split=c['split'],category=c['category'],risk=c['risk'],expected=c['expected'],A=a,B=b,C=deterministic(c),latency_ms=(time.perf_counter()-start)*1000))
write('local_validation.json',local)
import pytest
from tests.test_pr_ef_gm_authority import seed_scene,raw_record
from game import storage,api
from game.models import ChatRequest
from game.conversational_continuity import continuity_directive
def diff(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  return [r for k in sorted(set(a)|set(b)) for r in diff(a.get(k),b.get(k),path+'/'+str(k))]
 return [] if a==b else [dict(path=path,before=a,after=b)]
probes=[]
for c in read('supplement.json'):
 with pytest.MonkeyPatch.context() as mp:
  seed_scene(H/'disposable_state'/c['id'],mp)
  if c['id']=='E':
   w=storage.load_world()
   for npc in w['npcs']:
    if npc['id']=='sergeant_mara':npc['topics']=[dict(id='night_watch',text=c['candidate'])]
   storage.save_world(w)
  mp.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0');mp.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
  mp.setattr('game.live_chat_interpretation.request_interpretation',lambda *a,**k:dict(ok=True,sent=False,text=json.dumps(raw_record('NPC',components=[('ASK','sergeant_mara')]))))
  calls=[];candidate=f'Sergeant Mara says, "{c["candidate"]}"'
  def narration(*a,**k):
   calls.append(dict(args_count=len(a),keyword_names=list(k)))
   return dict(player_facing_text=candidate,tags=[],scene_update=None,world_updates=None,debug_notes='R2B controlled narration seam')
  mp.setattr(api,'call_gpt',narration)
  before=copy.deepcopy(storage.load_world());sb=copy.deepcopy(storage.load_session())
  try:
   response=api.chat(ChatRequest(text='I ask Sergeant Mara, '+c['player_question'],ui_mode='player'))
   sa=storage.load_session();after=storage.load_world();res=response.get('resolution') or {};soc=res.get('social') or {};meta=res.get('metadata') or {};rc=meta.get('resolution_contract') or {}
   topic=soc.get('topic_revealed') or {}
   # Observational composition from actual handler outputs. Never injected into production.
   packet=dict(interaction_id=rc.get('contract_id'),authorization=(rc.get('construction') or {}).get('conversational_authorization'),speaker_id=soc.get('npc_id'),question=c['player_question'],evidence=[dict(source='resolution.social.topic_revealed',id=topic.get('id'),text=topic.get('clue_text') or topic.get('text'))] if topic else [],dialogue_authority=soc.get('dialogue_authority'),resolver_owned=True)
   con,synth,dec=fixture(c)
   validation=validate_generated_response(candidate,contract=rc or con,decision=meta.get('gm_resolution_decision') or dec,player_text=c['player_question'],resolution=res or synth,authored_corpus=topic.get('text',''),present_addressee='Sergeant Mara')
   ctx=sa.get('conversational_context',{});delivered=response.get('gm_output',{}).get('player_facing_text')
   probes.append(dict(id=c['id'],expected=c['expected'],speech_contract=speech_contract(c),actual_resolver_packet=packet,candidate=candidate,validation=validation,final_response=delivered,identical=delivered==candidate,delivered_history=ctx.get('delivered_exchanges'),world_diff=diff(before,after),commitment_diff=diff(sb.get('conversational_context',{}).get('dialogue_commitments'),ctx.get('dialogue_commitments')),narration_calls=len(calls),external_network_calls=0,response=response,world_before_sha256=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),world_after_sha256=hashlib.sha256(json.dumps(after,sort_keys=True).encode()).hexdigest(),followup_directive=continuity_directive('What did you mean by that?',session=sa,scene=storage.load_active_scene(),world=after)))
  except Exception as e:probes.append(dict(id=c['id'],error=repr(e),narration_calls=len(calls)))
write('adoption_probes.json',probes)
before=read('protected_before.json');write('source_integrity.json',dict(protected_files=len(before),changed=[p for p,h in before.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]))
print(json.dumps(dict(local_cases=len(local),handler_probes=len(probes),errors=[p for p in probes if 'error' in p])))
