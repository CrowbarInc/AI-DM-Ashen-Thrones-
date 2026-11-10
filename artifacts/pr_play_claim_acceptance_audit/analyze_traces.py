import copy, hashlib, json, os, sys, socket
from pathlib import Path
R=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent
sys.path.insert(0,str(R)); os.chdir(R)
os.environ['ASHEN_TEST_EVIDENCE_DIR']=str(O)
for k in ('ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES','ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'): os.environ[k]='1'
network=[]
def guard(event,args):
 if event in ('socket.connect','socket.getaddrinfo'):
  host=args[1][0] if event=='socket.connect' else args[0]
  if host not in ('localhost','::1','127.0.0.1'):
   network.append(str(args)); raise RuntimeError('Audit forbids external network')
sys.addaudithook(guard)
from tests.helpers.storage_isolation import install
install(R/'development/tmp/claim_probe_storage')
from game import immutable_valid_response as ivr
from game import perception_grounding as pg
from game.referenced_surface import classification_from_resolution, render_referenced_surface_inspection_line
from game.gm_resolution_decision import decision_from_resolution, audit_narration_against_decision
from game.consequential_narration_validation import SemanticAuthority, validate_consequential_narration
cases=json.loads((R/'artifacts/pr_play_baseline_provenance/publication_defects.json').read_text())['defects']
events=json.loads((O/'stage_events.json').read_text()); cap=json.loads((O/'http_capture.json').read_text())
out=[]
for c in cases:
 ev=[v for v in events if v['node']==c['nodeid']]; turn=cap[c['nodeid']][0]
 seal=next(v for v in ev if v['function'].endswith('seal_accepted_response')); kwargs=seal['kwargs']; res=kwargs['resolution']
 ck=next(v for v in ev if v['function'].endswith('_unsupported_perception'))['kwargs']; scene=ck['scene']; session=ck['session']; world=ck['world']
 val=next(v for v in ev if v['function'].endswith('validate_generated_response')); classification=classification_from_resolution(res)
 text=render_referenced_surface_inspection_line(classification,scene)
 safe=ivr.safe_nonresolution(kwargs['contract'],resolution=res,player_text=c['request']['text'])
 safecheck=ivr.validate_generated_response(safe,**val['kwargs']) if False else None
 before=copy.deepcopy((scene,session,world,res))
 safecheck=ivr.validate_generated_response(safe,**val['kwargs'])
 neutral=render_referenced_surface_inspection_line({'authority':'unsupported'},scene)
 neutralcheck=ivr.validate_generated_response(neutral,**val['kwargs'])
 check=ivr.validate_generated_response(text,**val['kwargs']); perception=ivr._unsupported_perception(text,**ck)
 gm=ivr.run_preserve_if_valid({'player_facing_text':text,'metadata':{}},regenerate=None,resolution=res,player_text=c['request']['text'],scene=scene,session=session,world=world)
 raw=turn['raw_before_projection'][0]; accepted=(raw.get('gm_output') or {}).get('metadata',{}).get('accepted_response',{})
 if not accepted:
  # Resolution and response captures may hold additional projections; find the matching seal recursively.
  def find(x):
   if isinstance(x,dict):
    if 'accepted_response' in x: return x['accepted_response']
    for v in x.values():
     f=find(v)
     if f: return f
   if isinstance(x,list):
    for v in x:
     f=find(v)
     if f:return f
  accepted=find(turn['raw_before_projection'])
 out.append({'id':c['id'],'nodeid':c['nodeid'],'request':c['request'],'candidate_source':'unchanged fixture local game.api.call_gpt stub via _gm_response','published':turn['response']['gm_output']['player_facing_text'],'resolution':res,'candidate_validation':val['result'],'events':ev,'accepted_response':accepted,'classification':classification,'neutral_existing_template_probe':{'text':neutral,'validation':neutralcheck,'unsupported_perception':ivr._unsupported_perception(neutral,**ck)},'safe_nonresolution_probe':{'text':safe,'validation':safecheck},'renderer_probe':{'text':text,'validation':check,'unsupported_perception':perception,'lifecycle_final':gm,'input_state_unchanged':before==(scene,session,world,res)},'quarantined_gate_probe':validate_consequential_narration(c['published_text'],SemanticAuthority(observable_scene=tuple(scene['scene'].get('visible_facts',[])))),'character_unchanged':turn['before']['character']==turn['after']['character'],'world_npcs_unchanged':turn['before']['world'].get('npcs')==turn['after']['world'].get('npcs'),'state_before_after':{'before':turn['before'],'after':turn['after']}})
(O/'three_case_trace.json').write_text(json.dumps(out,indent=2,default=str))
summary=[]
for row in out:
 summary.append({k:row[k] for k in ('id','request','published','classification','candidate_validation','character_unchanged','world_npcs_unchanged') } | {'neutral_existing_template_probe':row['neutral_existing_template_probe'],'safe_nonresolution_probe':row['safe_nonresolution_probe'],'renderer_text':row['renderer_probe']['text'],'renderer_hard_valid':row['renderer_probe']['validation']['hard_valid'],'renderer_unsupported':row['renderer_probe']['unsupported_perception'],'renderer_final_text':row['renderer_probe']['lifecycle_final']['player_facing_text'],'quarantined_gate':row['quarantined_gate_probe']})
(O/'trace_summary.json').write_text(json.dumps(summary,indent=2))
(O/'probe_integrity.json').write_text(json.dumps({'live_provider_calls':0,'network_attempts_blocked':network,'all_inputs_unchanged':all(r['renderer_probe']['input_state_unchanged'] for r in out)},indent=2))
for r in summary: print(json.dumps(r))

rows=[]
base=out[0]
for category,text in [('sensory','Wind moves through the loft.'),('sensory','A floorboard creaks.'),('sensory','The guard shifts their weight.'),('sensory','A lantern flickers.'),('event_control','A distant bell rings.'),('opinion','The clerk says, "I prefer the morning shift."'),('uncertainty','The clerk says, "I am not sure."'),('followup','The clerk asks, "Which record do you mean?"'),('speculation','Someone may have passed through here.')]:
 val_event=next(v for v in base['events'] if v['function'].endswith('validate_generated_response'))
 kwargs=copy.deepcopy(val_event['kwargs'])
 if category in ('opinion','uncertainty','followup'):
  # No inspector contract is claimed for isolated dialogue-frame probes.
  result=ivr.validate_generated_response(text,resolution={'kind':'social'})
 else: result=ivr.validate_generated_response(text,**kwargs)
 perception_kwargs=next(v for v in base['events'] if v['function'].endswith('_unsupported_perception'))['kwargs']
 unsupported=ivr._unsupported_perception(text,**perception_kwargs) if category not in ('opinion','uncertainty','followup') else None
 rows.append({'category':category,'text':text,'unsupported_perception':unsupported,'validation':result,'probe_scope':'isolated existing validator; dialogue does not prove target resolution'})
(O/'classification_probes.json').write_text(json.dumps(rows,indent=2))
