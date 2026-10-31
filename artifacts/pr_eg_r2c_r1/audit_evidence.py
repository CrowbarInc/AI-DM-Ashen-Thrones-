"""Audit evidence without changing the frozen implementation or any test expectation."""
import json,sys,copy,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
H=Path(__file__).parent;R=H.parents[1];sys.path.insert(0,str(R))
from game.conversational_continuity import _best_exchange,_gm_quote
live=json.loads((H/'live_qualification.json').read_text());audit=[];state=[]
for label,rows in live.items():
 nid='sergeant_mara' if label=='primary' else 'corporal_bren'
 direct={1:'street',7:'night_watch',13:'street'} if label=='primary' else {1:'night_watch',6:'street'}
 repeats={2:1,3:1,5:4,8:7,15:4} if label=='primary' else {2:1,5:4,7:6}
 for row in rows:
  checks={};soc=(row['result'].get('resolution') or {}).get('social') or {};ac=row['adoption'];text=row['text'];history=row['history_after'];before=row['history_before'] or []
  checks['http_ok']=row['http_status']==200
  checks['adopted_equals_delivered']=not ac or ac.get('text')==text
  checks['history_equals_delivery']=bool(history) and history[-1]['delivered_text']==text
  checks['no_unexpected_world_changes']=all(d['path'].startswith(('/factions','/event_log')) or (d['path'].startswith('/world_state/flags/faction_') and d['path'].endswith('_agenda_advanced')) for d in row['world_diff'])
  checks['storage_roundtrip']=not row['save_load'] or row['save_load']['context_equal']
  if row['turn'] in direct:
   topic=direct[row['turn']];checks['selected_authored_topic']=(soc.get('topic_revealed') or {}).get('id')==topic
   checks['speaker_knowledge_ownership']=soc.get('npc_id')==nid
   checks['adoption_source_matches']=ac.get('authorization_source')=='social.topic_revealed:'+topic
  if row['turn'] in repeats:
   earlier=rows[repeats[row['turn']]-1];checks['faithful_restatement']=text==earlier['text']
   checks['history_speaker_correct']=history[-1]['speaker_id']==nid
  if row['player'].startswith('GM,'):
   found=_best_exchange(row['player'],before)
   checks['exact_delivered_source']=isinstance(found,dict) and text==_gm_quote(found)
   checks['historical_speaker']=isinstance(found,dict) and found['speaker_id']==nid
   checks['gm_ownership']=history[-1]['ownership']=='gm'
  audit.append(dict(conversation=label,turn=row['turn'],checks=checks,passed=all(checks.values()),selected_topic=(soc.get('topic_revealed') or {}).get('id'),authority=soc.get('dialogue_authority'),adoption=ac))
  state.append(dict(conversation=label,turn=row['turn'],world_diff=row['world_diff'],commitment_diff=row['commitment_diff'],save_load=row['save_load'],history_speakers=[r['speaker_id'] for r in history],adoption_source=ac.get('authorization_source')))
(H/'live_semantic_audit.json').write_text(json.dumps(audit,indent=2));(H/'state_audit.json').write_text(json.dumps(state,indent=2))
print('semantic audited turns',len(audit),'failed',[(r['conversation'],r['turn'],r['checks']) for r in audit if not r['passed']])
print('canonical changes',len([d for r in state for d in r['world_diff']]),'all passive',all(r['checks']['no_unexpected_world_changes'] for r in audit))
