"""Offline token, validator, persistence, and source-integrity measurements."""
from __future__ import annotations
import copy,hashlib,json,os,sys,statistics,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT),str(HERE/'local_dependencies')]
os.environ['ASHEN_DATA_DIR']=str(HERE/'disposable_state'/'analysis')
os.environ['TIKTOKEN_CACHE_DIR']=str(HERE/'tokenizer_cache')
os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
import tiktoken
from investigate import save,validate,cases,case,ROAD
# investigate establishes budget environment; this script never instantiates a provider client.
os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
enc=tiktoken.encoding_for_model('gpt-4.1-mini')
def tokens(s): return len(enc.encode(s))
def js(v): return json.dumps(v,ensure_ascii=False)
captures=json.loads((HERE/'production_captures_offline.json').read_text(encoding='utf-8'))
group_keys={
 'B_dialogue_instructions':['instructions','dialogue_social_plan','bounded_improvisation','narration_obligations','interlocutor_lead_behavior_hints'],
 'D_identity':['speaker_selection','active_interlocutor','social_context'],
 'E_knowledge':['clues','known_answer_hint'],
 'F_history':['recent_log','selected_conversational_memory','interaction_continuity','turn_summary','active_topic_anchor','follow_up_pressure','lead_context','interlocutor_lead_context'],
 'G_resolver':['mechanical_resolution','resolution_contract','gm_resolution_decision','decision_facing_answer_recipe','turn_packet'],
 'H_validation':['response_policy','narration_visibility','scene_state_anchor_contract','first_mention_contract','discoverable_hinting','player_expression_contract','referent_tracking','referent_clause_prompt_hints','uncertainty_hint'],
 'C_simulation':['transition','narrative_plan','opening_narration_obligations','opening_scene_realization','opening_inputs_are_curated','opening_selector_source_used','opening_selector_selected_facts','opening_curated_facts','scene_advancement','session','character','combat','world_state','world','world_progression_summary','campaign','scene']}
attribution=[]
for cap in captures:
 messages=cap['messages']; payload=json.loads(messages[1]['content']); groups={}; assigned=set()
 for name,keys in group_keys.items():
  data={k:payload[k] for k in keys if k in payload}; assigned.update(data)
  groups[name]={'keys':list(data),'characters':len(js(data)),'content_tokens':tokens(js(data))}
 data={k:v for k,v in payload.items() if k not in assigned}
 groups['K_other']={'keys':list(data),'characters':len(js(data)),'content_tokens':tokens(js(data))}
 # Repeated subtree inventory is deliberately non-additive: parent/child overlaps remain visible.
 occurrences=collections.defaultdict(list)
 def walk(v,path):
  s=js(v)
  if len(s)>=120: occurrences[s].append(path)
  if isinstance(v,dict):
   for k,x in v.items(): walk(x,path+'.'+k)
  elif isinstance(v,list):
   for n,x in enumerate(v): walk(x,path+f'[{n}]')
 walk(payload,'payload')
 repeated=sorted([{'paths':p,'characters':len(s),'tokens_each':tokens(s),'sha256':hashlib.sha256(s.encode()).hexdigest()}
  for s,p in occurrences.items() if len(p)>1],key=lambda r:r['characters']*(len(r['paths'])-1),reverse=True)
 row={'question':payload.get('player_input'),'encoding':enc.name,'tokenizer_version':tiktoken.__version__,
  'evidence':'measured local content tokens; not fresh provider usage; framing excluded',
  'system_content_tokens':tokens(messages[0]['content']),'user_content_tokens':tokens(messages[1]['content']),
  'system_characters':len(messages[0]['content']),'user_characters':len(messages[1]['content']),
  'groups':groups,'group_wrapper_boundary_residual':tokens(messages[1]['content'])-sum(g['content_tokens'] for g in groups.values()),
  'I_tools_schema':{'tools':0,'tool_schema':0,'note':'No tools or text JSON schema passed; format guidance is in system/user instructions.'},
  'J_duplicates_nonadditive':repeated[:25],
  'top_level':{k:{'characters':len(js({k:v})),'content_tokens':tokens(js({k:v}))} for k,v in payload.items()}}
 attribution.append(row)
save('local_prompt_attribution.json',attribution)

from game.immutable_valid_response import validate_generated_response,run_preserve_if_valid
from game.gm_resolution_decision import build_gm_resolution_decision
from game.dialogue_authority import build_dialogue_authority,dialogue_rejection_reasons
from experiments.pr_dq.world import build_disposable_world
built=build_disposable_world(); scene=built['scenes']['waystation_courtyard']; world=built['world']
def decision_check(c,text):
 v=validate(c,text); social={'npc_id':'sergeant_mara','npc_name':'Sergeant Mara','target_resolved':True,
  'dialogue_authority':v['authority'],'reply_plan_kind':'harmless_subjective_response_permitted' if c['posture']=='belief' else 'genuine_uncertainty',
  'npc_speech_authority':'claim_only' if c['posture']=='belief' else 'none',
  'incidental_subjective_allowed':c['posture']=='belief','objective_world_fact_authority':'none','durable_state_mutation_allowed':False}
 if c['facts']: social['topic_revealed']={'id':'street','text':ROAD}
 contract=copy.deepcopy(captures[0]['resolution']['metadata']['resolution_contract'])
 contract.update(raw_input=c['question'],contract_id='r2_fixture_'+c['id'])
 resolution={'kind':'social_exchange','prompt':c['question'],'requires_check':False,'social':social,
  'metadata':{'resolution_contract':contract,'ordinary_contract_established':True,'selected_resolver':'social'}}
 decision=build_gm_resolution_decision(resolution=resolution,scene=scene,world=world,session={})
 decision=decision.as_dict() if hasattr(decision,'as_dict') else decision
 resolution['metadata']['gm_resolution_decision']=decision
 result=validate_generated_response(text,contract=contract,decision=decision,player_text=c['question'],resolution=resolution,
  authored_corpus=' '.join(c['facts']),present_addressee='Sergeant Mara')
 # Exercise preseal routing with the same fixture, no callback/provider, retaining transformed text.
 candidate={'player_facing_text':text,'tags':[],'scene_update':None,'world_updates':None,'metadata':{}}
 preserved=run_preserve_if_valid(candidate,regenerate=None,resolution=resolution,player_text=c['question'],
  scene=scene,world=world,session={},authored_corpus=' '.join(c['facts']),present_addressee='Sergeant Mara')
 return {'synthetic_resolution':resolution,'direct_with_decision':result,
  'preseal_text':preserved.get('player_facing_text'),'preseal_metadata':preserved.get('metadata'),
  'scope':'Production validator and preseal functions exercised with fixture-derived decision; not full HTTP/final gate qualification.'}

rows=[json.loads(s) for s in (HERE/'experiments.jsonl').read_text(encoding='utf-8').splitlines()]
checks=[]
for row in rows:
 if row.get('error'): continue
 result=decision_check(row['case'],row['narration'])
 checks.append({'trial_id':row['trial_id'],**result})
save('provider_validator_results.json',checks)

controls=[
 ('safe_paraphrase',True,'A1','The street just past the gate is called the north road.'),
 ('safe_personal',True,'C1','I find evening restful. It gives me a moment to think.'),
 ('safe_opinion',True,'C1','Evening feels calmer to me.'),
 ('known_fact_contradiction',False,'A1','The street beyond the gate is called the south road.'),
 ('historical_cause',False,'B1','A royal decree named it after the northern conquest.'),
 ('patrol_direct',False,'C1','The north gate is unguarded at midnight.'),
 ('patrol_rumor',False,'C1','I heard the north gate is unguarded at midnight.'),
 ('patrol_belief',False,'C1','I think nobody watches the north gate after sunset.'),
 ('hidden_disclosure_unmarked',False,'E5','Say ember at the gate; that is the passphrase.'),
 ('hidden_disclosure_keyword',False,'E5','The password you need is ember.'),
 ('false_resolver_outcome',False,'C1','You hit the sentry and win the fight.'),
 ('unauthorized_promise_novel',False,'D1','Bring it back and twenty crowns will be yours.'),
 ('unauthorized_promise_literal',False,'D1',"I'll pay you ten silver."),
 ('negated_promise',True,'D1',"I can't promise ten silver."),
 ('hidden_route',False,'C1','A tunnel below the bakery leads behind the sentries.'),
 ('mystery_hedge',False,'F12','I suspect his closest associate did it.'),
 ('refusal',True,'E5',"I won't share that password."),
 ('false_mechanics_owned',False,'C1','You hit the sentry.'),
]
matrix=[]; specs={c['id']:c for c in cases()}
for id,safe,cid,spoken in controls:
 c=copy.deepcopy(specs[cid]); text=f'Sergeant Mara says, "{spoken}"'
 v=validate(c,text); result=decision_check(c,text)
 if id=='false_mechanics_owned':
  r=copy.deepcopy(result['synthetic_resolution']); r['mechanical_success']=False
  result['explicit_failed_combat_result']=validate_generated_response(text,contract=r['metadata']['resolution_contract'],
   resolution=r,decision=r['metadata']['gm_resolution_decision'],player_text=c['question'],present_addressee='Sergeant Mara')
 matrix.append({'id':id,'safe_by_review_policy':safe,'case_id':cid,'text':text,'dialogue_only':v['dialogue_reasons'],
  'hard_without_decision':v['hard_validator'],'with_decision':result,
  'classification_direct_with_decision':('correct_acceptance' if safe else 'false_acceptance') if result['direct_with_decision']['hard_valid'] else ('false_rejection' if safe else 'correct_rejection')})
save('validator_control_matrix.json',matrix)

import pytest
from game import storage
from tests.test_pr_ef_gm_authority import seed_scene
from game.dialogue_authority import remember_dialogue_commitment
from game.conversational_continuity import record_delivered_exchange,continuity_directive
with pytest.MonkeyPatch.context() as mp:
 seed_scene(HERE/'disposable_state'/'persistence_probe',mp)
 session=storage.load_session(); before_world=copy.deepcopy(storage.load_world())
 social={'npc_id':'sergeant_mara','npc_name':'Sergeant Mara','dialogue_authority':validate(specs['C1'],'')['authority']}
 for turn,line in enumerate(['Sergeant Mara says, "I prefer the evening. It feels restful to me."',
                            'Sergeant Mara says, "I prefer the morning. It feels restful to me."'],1):
  remember_dialogue_commitment(session,social=social,player_text=specs['C1']['question'],line=line,turn=turn)
  record_delivered_exchange(session,player_text=specs['C1']['question'],delivered_text=line,social=social,scene_id='waystation_courtyard',turn=turn)
 storage.save_session(session); loaded=storage.load_session()
 persistence={'roundtrip_equal':loaded.get('conversational_context')==session.get('conversational_context'),
  'world_unchanged':before_world==storage.load_world(),'saved_context':loaded.get('conversational_context'),
  'note':'Opposite preferences were inserted directly into existing trusted recorder: records revise, no semantic contradiction rejection. This is not a delivered production conversation.'}
 save('persistence_probe.json',persistence)

before=json.loads((HERE/'protected_before.json').read_text(encoding='utf-8'))
after={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
save('source_integrity.json',{'protected_files':len(before),'changed':[p for p in before if before[p]!=after[p]],'hashes':after})
save('summary_measurements.json',{'successful_matrix_trials':sum(not r.get('error') for r in rows),
 'transport_failures':sum(bool(r.get('error')) for r in rows),'groups':dict(collections.Counter(r['case']['group'] for r in rows if not r.get('error'))),
 'input_tokens':sum(r.get('usage',{}).get('input_tokens',0) for r in rows),'output_tokens':sum(r.get('usage',{}).get('output_tokens',0) for r in rows),
 'latency_ms_median':statistics.median(r['latency_ms'] for r in rows if not r.get('error')),
 'validator_controls':dict(collections.Counter(r['classification_direct_with_decision'] for r in matrix))})
print((HERE/'summary_measurements.json').read_text())
