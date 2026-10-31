"""Audit final provider conversations, provenance, canonical domains and exact test identities."""
from pathlib import Path
import json,sys,hashlib,statistics,collections,xml.etree.ElementTree as ET
H=Path(__file__).parent;R=H.parents[1];sys.path.insert(0,str(R))
from game.conversational_continuity import _best_exchange,_gm_quote

def write(n,v):(H/n).write_text(json.dumps(v,indent=2,default=str),encoding='utf-8')
def read(n):return json.loads((H/n).read_text())
def junit(n):
 return {x.attrib['classname']+'::'+x.attrib['name']:'failed' if x.find('failure') is not None else 'error' if x.find('error') is not None else 'skipped' if x.find('skipped') is not None else 'passed' for x in ET.parse(H/n).iter('testcase')}
a,b=junit('baseline.xml'),junit('final.xml')
comparison=dict(baseline_counts=dict(collections.Counter(a.values())),final_counts=dict(collections.Counter(b.values())),baseline_failures=[k for k,v in a.items() if v!='passed'],final_failures=[k for k,v in b.items() if v!='passed'],new_failures=[k for k,v in b.items() if v!='passed' and a.get(k)=='passed'],resolved=[k for k,v in a.items() if v!='passed' and b.get(k)=='passed'],lost_baseline_passes=[k for k,v in a.items() if v=='passed' and b.get(k)!='passed'],new_tests=[k for k in b if k not in a],changed_expectations=['test_subject_unknown_does_not_clear_unknown_addressee_or_secondary_move: normalization now retains all annotations until engine evidence is available; provider subject alone cannot clear distant kingdom.'])
write('regression_comparison.json',comparison)
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in read('qualification_source_hashes.json').items())
live=read('live_qualification.json');audit=[];state=[];grounding=[]
def find(v,k):
 if isinstance(v,dict):
  if k in v:return v[k]
  for x in v.values():
   y=find(x,k)
   if y is not None:return y
 if isinstance(v,list):
  for x in v:
   y=find(x,k)
   if y is not None:return y
for label,rows in live.items():
 nid='warden_rell' if label=='primary' else 'keeper_nara'
 direct={1:'street',7:'night_watch',12:'night_watch',14:'street'} if label=='primary' else {1:'night_watch',6:'street',10:'street'}
 repeats={2:1,3:1,5:4,8:7,11:10,16:4} if label=='primary' else {2:1,5:4,7:6,9:8}
 for row in rows:
  n=row['turn'];res=row['result'].get('resolution')or{};soc=res.get('social')or{};ac=row['adoption'];history=row['history_after'];before=row['history_before']or[]
  checks=dict(http_ok=row['http_status']==200,runner_checks_pass=not row['failures'],adopted_equals_delivered=bool(ac) and ac.get('text')==row['text'],history_equals_delivered=bool(history)and history[-1]['delivered_text']==row['text'],storage_roundtrip=not row['save_load']or row['save_load']['context_equal'])
  checks['no_unexpected_world_changes']=all(d['path'].startswith(('/factions','/event_log')) or (d['path'].startswith('/world_state/flags/faction_')and d['path'].endswith('_agenda_advanced')) for d in row['world_diff'])
  checks['canonical_domains_stable']=all(row['session_before'].get(k)==row['session_after'].get(k)for k in ['inventory','party','pc','active_scene_id','visited_scene_ids'])
  if n in direct:
   topic=direct[n];checks['selected_owned_topic']=(soc.get('topic_revealed')or{}).get('id')==topic
   checks['speaker_correct']=soc.get('npc_id')==nid
   checks['adoption_source_matches']=ac.get('authorization_source')=='social.topic_revealed:'+topic
  if n in repeats:
   earlier=rows[repeats[n]-1];checks['faithful_restatement']=row['text']==earlier['text']
   checks['no_new_knowledge_on_repeat']=row['session_before'].get('clue_knowledge')==row['session_after'].get('clue_knowledge')
  if row['expected']=='clarification':
   checks['resolver_bypassed']=res.get('metadata',{}).get('resolver_invoked')is False
   checks['gm_clarification_ownership']=history[-1]['ownership']=='gm'
   checks['no_npc_disclosure']=not soc.get('topic_revealed')
   if (label=='primary'and n==11)or(label=='secondary'and n==9):
    checks['pending_preserved']=row['session_before']['conversational_context'].get('pending_clarification')==row['session_after']['conversational_context'].get('pending_clarification')
  if row['expected']=='uncertainty':
   checks['no_authored_disclosure']=not soc.get('topic_revealed')
   checks['knowledge_not_reference_ambiguity']=bool(soc)and(soc.get('dialogue_authority')or{}).get('knowledge_posture')in {'unknown','unestablished','withheld','partial'}
  if row['player'].startswith('GM,'):
   found=_best_exchange(row['player'],before)
   checks['exact_delivered_source']=isinstance(found,dict)and row['text']==_gm_quote(found)
   checks['speaker_specific_recall']=isinstance(found,dict)and found['speaker_id']==nid
   checks['gm_ownership']=history[-1]['ownership']=='gm'
  audit.append(dict(conversation=label,turn=n,checks=checks,passed=all(checks.values()),adoption=ac,authority=soc.get('dialogue_authority')))
  state.append(dict(conversation=label,turn=n,world_diff=row['world_diff'],session_diff=row['session_diff'],commitment_diff=row['commitment_diff'],checks={k:v for k,v in checks.items()if any(x in k for x in ['world','canonical','knowledge','pending','history'])}))
  raw=find(row['result'],'raw_interpretation');parsed=json.loads(raw)if raw else None
  grounding.append(dict(conversation=label,turn=n,player=row['player'],raw_interpretation=parsed,unresolved_annotations=(parsed or{}).get('references',{}).get('unresolved_references'),reconciliation=find(row['result'],'reference_reconciliation'),selected_handler=res.get('kind'),resolver_invoked=res.get('metadata',{}).get('resolver_invoked'),selected_addressee=soc.get('npc_id'),selected_subject=(soc.get('dialogue_authority')or{}).get('topic_grounding'),adoption_source=ac.get('authorization_source')))
write('live_semantic_audit.json',audit);write('state_audit.json',state);write('grounding_trace.json',grounding)
metrics={}
for label,rows in [*live.items(),('combined',[r for rows in live.values()for r in rows])]:
 totals={f:sum(r['calls'][f] for r in rows) for f in ['provider_calls','interpretation_calls','narration_calls','retry_calls','input_tokens','output_tokens']}
 metrics[label]=dict(turns=len(rows),**totals,calls_per_turn=totals['provider_calls']/len(rows),input_tokens_per_turn=totals['input_tokens']/len(rows),output_tokens_per_turn=totals['output_tokens']/len(rows),average_latency_ms=statistics.mean(r['elapsed_ms']for r in rows),maximum_latency_ms=max(r['elapsed_ms']for r in rows),high_cost_outliers=sorted([dict(turn=r['turn'],latency_ms=r['elapsed_ms'],calls=r['calls']['provider_calls'],input_tokens=r['calls']['input_tokens'])for r in rows],key=lambda r:r['latency_ms'],reverse=True)[:3])
write('performance.json',metrics)
usage=[json.loads(l)for l in(H/'final_literal_qualified_live_usage.jsonl').read_text().splitlines()if l.strip()]
write('final_provider_usage.json',usage)
# All attempts are retained and reported separately from final qualification.
allusage=[]
for name in ['live_usage.jsonl','final_live_usage.jsonl','qualification_live_usage.jsonl','final_qualified_live_usage.jsonl','final_literal_qualified_live_usage.jsonl']:
 allusage += [json.loads(l)for l in(H/name).read_text().splitlines()if l.strip()]
write('development_provider_cost.json',dict(records=len(allusage),input_tokens=sum(r.get('input_tokens')or 0 for r in allusage),output_tokens=sum(r.get('output_tokens')or 0 for r in allusage)))
for label,rows in live.items():
 lines=['# Final fresh-provider '+label+' conversation','Evidence: actual production /api/chat; configured provider route. Full raw interpretations, responses, pre/post states and call records are in live_qualification.json.']
 for r in rows:lines.extend([f"\n## Turn {r['turn']}",f"Player: {r['player']}",f"Delivered: {r['text']}",f"Handler: {(r['result'].get('resolution')or{}).get('kind')}; adoption source: {r['adoption'].get('authorization_source')}; provider calls: {r['calls']['provider_calls']}; failures: {r['failures']}."])
 (H/(label+'_transcript.md')).write_text('\n\n'.join(lines),encoding='utf-8')
focused={k:v for k,v in b.items()if 'test_pr_eg_r2c_r2_reference_eligibility' in k}
write('targeted_results.json',focused)
gates={
 '1_grounded_eligibility':all(x['passed']for x in audit)and all(v=='passed'for v in focused.values()),
 '2_genuine_ambiguity':all(x['checks'].get('resolver_bypassed',True)for x in audit),
 '3_addressee_authority':all(x['checks'].get('speaker_correct',True)for x in audit)and all(x['passed']for x in read('adversarial_annotations.json')),
 '4_subject_authority':all(v=='passed'for v in focused.values()),
 '5_authorized_disclosure':all(x['checks'].get('selected_owned_topic',True)for x in audit),
 '6_knowledge_distinction':all(x['checks'].get('knowledge_not_reference_ambiguity',True)for x in audit),
 '7_continuity':all(x['checks'].get('faithful_restatement',True)and x['checks'].get('pending_preserved',True)for x in audit)and all(x['passed']for x in read('predecessor_holdout_results.json')),
 '8_information_integrity':all(v=='passed'for k,v in b.items()if 'test_pr_eg_r2c_speech_adoption' in k),
 '9_regression':not comparison['new_failures']and not comparison['lost_baseline_passes'],
 '10_fresh_provider':len(live['primary'])>=15 and len(live['secondary'])>=12 and all(x['passed']for x in audit),
 '11_performance':metrics['combined']['narration_calls']==0 and metrics['combined']['retry_calls']==0,
}
write('acceptance_gates.json',gates)
print('AUDIT failures',[(x['conversation'],x['turn'],[k for k,v in x['checks'].items()if not v])for x in audit if not x['passed']])
print('GATES',gates);print('PERFORMANCE',metrics['combined']);print('REGRESSION',comparison['baseline_counts'],comparison['final_counts'],comparison['new_failures'])
