"""Inspect available response projections and final persisted canonical session."""
import json,sys
from pathlib import Path
H=Path(__file__).parent;sys.path.insert(0,str(H.parents[1]))
from tools.validate_pr_eg_r2c_r1 import diff
live=json.loads((H/'live_qualification.json').read_text());out=[];finals={}
for label,rows in live.items():
 known={}
 for r in rows:
  session=r['result'].get('session');soc=(r['result'].get('resolution') or {}).get('social') or {};reference=r['adoption'].get('authorization_source','') in {'dialogue_authority.reuse_prior_speech','conversational_decision:repeat_delivered_statement','conversational_decision:gm_recall_of_npc_statement'}
  domains=['active_scene_id','visited_scene_ids','flags','inventory','clocks','npc_runtime','scene_runtime','scene_state','runtime_scene_overlays','clue_knowledge','lead_registry']
  exposed={k:session[k] for k in domains if k in session} if isinstance(session,dict) else {}
  old={k:known[k] for k in exposed if k in known};new={k:exposed[k] for k in old}
  changes=diff(old,new);knowledge=[d for d in changes if d['path'].startswith('/clue_knowledge') or d['path'].endswith('/revealed_topics')]
  out.append(dict(conversation=label,turn=r['turn'],session_projection_available=isinstance(session,dict),newly_observed_domains=[k for k in exposed if k not in known],selected_topic=soc.get('topic_revealed'),reference_turn=reference,observed_session_diff=changes,knowledge_diff=knowledge,reference_has_no_observed_new_knowledge=not(reference and knowledge),limitation='Comparison covers exposed response domains only; omitted response fields are not interpreted as state changes.'))
  known.update(exposed)
 p=H/'disposable_state'/('live_'+label)/'data/session.json';saved=json.loads(p.read_text())['payload']
 finals[label]={k:saved.get(k) for k in domains+['conversational_context']}
(H/'session_state_audit.json').write_text(json.dumps(dict(turns=out,final_persisted_sessions=finals),indent=2))
print('reference knowledge failures',[(r['conversation'],r['turn']) for r in out if not r['reference_has_no_observed_new_knowledge']]);print('final clue ids',{label:list(s.get('clue_knowledge') or {}) for label,s in finals.items()})
