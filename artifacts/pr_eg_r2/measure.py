"""Measure retained synthetic production prompts at the same explicit provider."""
import json,os,sys,time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
load_dotenv(ROOT/'.env')
client=OpenAI(api_key=os.environ['OPENAI_API_KEY'],base_url='https://api.openai.com/v1',timeout=30,max_retries=0)
captures=json.loads((HERE/'production_captures_offline.json').read_text(encoding='utf-8'))

GROUPS={
 'B_dialogue_instructions':['instructions','dialogue_social_plan','bounded_improvisation','narration_obligations','interlocutor_lead_behavior_hints'],
 'D_identity':['speaker_selection','active_interlocutor','social_context'],
 'E_knowledge':['clues','known_answer_hint'],
 'F_history':['recent_log','selected_conversational_memory','interaction_continuity','turn_summary','active_topic_anchor','follow_up_pressure','lead_context','interlocutor_lead_context'],
 'G_resolver':['mechanical_resolution','resolution_contract','gm_resolution_decision','decision_facing_answer_recipe','turn_packet'],
 'H_validation':['response_policy','narration_visibility','scene_state_anchor_contract','first_mention_contract','discoverable_hinting','player_expression_contract','referent_tracking','referent_clause_prompt_hints','uncertainty_hint'],
 'C_simulation':['transition','narrative_plan','opening_narration_obligations','opening_scene_realization','opening_inputs_are_curated','opening_selector_source_used','opening_selector_selected_facts','opening_curated_facts','scene_advancement','session','character','combat','world_state','world','world_progression_summary','campaign','scene'],
}

def split(payload):
 assigned=set(); groups={}
 for name,keys in GROUPS.items():
  groups[name]={k:payload[k] for k in keys if k in payload}; assigned.update(groups[name])
 groups['K_other']={k:v for k,v in payload.items() if k not in assigned}
 return groups

def count(text):
 return client.responses.input_tokens.count(model='gpt-4.1-mini',input=text).input_tokens

rows=[]
for i,cap in enumerate(captures[:2]):
 messages=cap['messages']; payload=json.loads(messages[1]['content'])
 row={'index':i,'capture_type':'production build_messages, scripted interpreter and narration, disposable seeded fixture',
  'system_characters':len(messages[0]['content']),'payload_characters':len(messages[1]['content']),
  'top_level_characters':{k:len(json.dumps({k:v},ensure_ascii=False)) for k,v in payload.items()},
  'groups':{}}
 try:
  response=client.responses.create(model='gpt-4.1-mini',input=messages,max_output_tokens=700)
  row['fresh_generation']={'raw_output':response.output_text,'model':response.model,'usage':response.usage.model_dump()}
 except Exception as exc:
  row['fresh_generation']={'error':type(exc).__name__,'message':str(exc)[:250]}
 # Provider token-count endpoint has message framing; measure and subtract empty-string control.
 try:
  row['empty_string_control']=count('')
  row['system_standalone_input_tokens']=count(messages[0]['content'])
  row['system_content_tokens']=row['system_standalone_input_tokens']-row['empty_string_control']
  for name,data in split(payload).items():
   text=json.dumps(data,ensure_ascii=False)
   n=count(text)
   row['groups'][name]={'keys':list(data),'characters':len(text),'standalone_input_tokens':n,
    'content_tokens_after_control':n-row['empty_string_control']}
   print(json.dumps({'capture':i,'group':name,'count':n}),flush=True)
 except Exception as exc:
  row['count_error']={'type':type(exc).__name__,'message':str(exc)[:250]}
 rows.append(row)
 (HERE/'prompt_attribution.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
