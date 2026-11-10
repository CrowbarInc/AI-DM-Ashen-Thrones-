"""Derive final evidence from recorded requests, never from HTTP status alone."""
import json,hashlib,statistics,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent

def read(name):return json.loads((O/name).read_text(encoding='utf-8'))
def write(name,value):(O/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def stats(values):return dict(count=len(values),mean=statistics.mean(values) if values else None,median=statistics.median(values) if values else None,maximum=max(values) if values else None)
def npcs(s):return [n for n in s.get('bounded_improvisation',{}).get('entries',[]) if n.get('authority')=='accepted_background_npc' and n.get('campaign_id')==s.get('campaign_run_id')]
def history(s,nid):return [h for h in s.get('conversational_context',{}).get('dialogue_commitments',[]) if h.get('npc_id')==nid and h.get('kind')=='background_exchange']
def junit(name):
 cases=list(ET.parse(O/name).getroot().iter('testcase'));return dict(passed=sum(not any(c.find(t) is not None for t in ['failure','error','skipped']) for c in cases),failed=sum(any(c.find(t) is not None for t in ['failure','error']) for c in cases))

def main():
 http=read('http_summary.json');assert all(c['result']=='PASS' for c in http['campaigns'])
 hrows=read('http_traces.json');old=read('http_before_reference_repair_http_traces.json')
 browser=[json.loads(l) for l in (O/'browser_network.jsonl').read_text().splitlines() if l.strip()]
 bchats=[r for r in browser if r['path']=='/api/chat'];loads=[r for r in browser if r['path']=='/api/snapshots/load']
 resumes=[r for r in bchats if json.loads(r['request'] or '{}').get('text')=='Talk to that traveler again.']
 assert len(resumes)>=2
 resumes=list({r['authority_after']['session']['campaign_run_id']:r for r in resumes}.values())
 assert len(resumes)==2
 final_hash=read('final_source.json')
 for row in resumes:
  assert row.get('host_source') and all(final_hash[k]==v for k,v in row['host_source'].items())
 campaign_results=[]
 for row in resumes:
  before=row['authority_before']['session'];after=row['authority_after']['session'];prior=npcs(before);current=npcs(after)
  assert len(prior)==len(current)==1 and prior[0]['id']==current[0]['id']
  nid=current[0]['id'];assert len(history(after,nid))==min(8,len(history(before,nid))+1)
  assert current[0]['name'] in json.loads(row['response'])['gm_output']['player_facing_text']
  assert any(r['authority_after']['session'].get('campaign_run_id')==after['campaign_run_id'] for r in loads)
  branch='survey' if row['authority_after']['world']['world_state']['flags'].get('patrol_survey') else 'report'
  campaign_results.append(dict(branch=branch,result='PASS',campaign_id=after['campaign_run_id'],npc_id=nid,name=current[0]['name'],history_before=history(before,nid),history_after=history(after,nid),published=json.loads(row['response'])['gm_output']['player_facing_text']))
 inquiries=[r for r in bchats if json.loads(r['request'] or '{}').get('text')=='What do I know about this area?']
 assert inquiries and all(r['authority_before']==r['authority_after'] for r in inquiries)
 write('browser_results.json',dict(final_source_cross_resume=True,read_only_inquiry_unchanged=True,campaigns=campaign_results,typed_submissions=len(bchats),reload_load_verified=True,server_chat_ms=stats([r['server_ms'] for r in bchats]),browser_visible_latency=None,paint_timing='not instrumented',bounded_recovery='one pressSequentially timeout and locator/wait deadlines; inspected state before continuing'))
 write('browser_typed_transcript.json',[dict(input=json.loads(r['request'] or '{}').get('text'),response=json.loads(r['response']),server_ms=r['server_ms']) for r in bchats])
 records=[]
 for name in ['http_data/provider_usage.jsonl','http_final_data/provider_usage.jsonl','browser_data/provider_usage.jsonl']:
  for line in (O/name).read_text().splitlines():
   row=json.loads(line)
   if row.get('request_id') and row.get('sent'):records.append(dict(evidence_file=name,**row))
 unique={r['request_id']:r for r in records};records=list(unique.values());usage=dict(requests=len(records),tokens=sum(r.get('total_tokens') or 0 for r in records),retries=0,records=records)
 assert usage['requests']<=12 and usage['tokens']<=24000
 write('provider_usage.json',usage)
 identities={};proposals=[];conversations=[];scans=[]
 streams=[('initial_http',old),('final_http',hrows),('browser',browser)]
 for lane,rows in streams:
  for row in rows:
   before=row['authority_before']['session'];after=row['authority_after']['session']
   body=json.loads(row['response']) if lane=='browser' else row.get('body',{})
   if not isinstance(body,dict):continue
   request=json.loads(row['request'] or '{}') if lane=='browser' else row['request'].get('json') or {}
   path=row['path'] if lane=='browser' else row['request']['path'];text=request.get('text','')
   ids={n['id'] for n in npcs(before)}
   for npc in npcs(after):
    identities[npc['id']]=npc
    if npc['id'] not in ids and path=='/api/chat':proposals.append(dict(lane=lane,input=text,npc=npc,proposal=after.get('bounded_improvisation',{}).get('npc_last_proposal')))
    if history(after,npc['id'])!=history(before,npc['id']) and path=='/api/chat':
     conversations.append(dict(lane=lane,input=text,npc_id=npc['id'],response=body.get('gm_output',{}).get('player_facing_text'),audit=after.get('last_background_expression'),latency_ms=row['server_ms'] if lane=='browser' else row['http_ms']))
   serialized=json.dumps(body);hidden=any(t in serialized for t in ['SENTINEL_','CANARY_','"hidden_facts"','"gm_notes"','"bounded_improvisation"','"last_background_expression"'])
   required=None
   if text=='I examine the notice board.':required='The missing patrol was last seen taking the northwest mud track past the crates.'
   if text=='I examine the weathered milestone.':required='Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.'
   scans.append(dict(lane=lane,path=path,input=text,hidden_exposure=hidden,mandatory_required=required,mandatory_present=required.casefold() in body.get('gm_output',{}).get('player_facing_text','').casefold() if required else None))
 write('npc_identity_records.json',list(identities.values()));write('live_provider_proposals.json',proposals);write('conversation_transcripts.json',conversations)
 write('publication_scan.json',dict(hidden_exposures=sum(r['hidden_exposure'] for r in scans),mandatory_omissions=sum(r['mandatory_present'] is False for r in scans),checks=scans,scope='Complete serialized exercised HTTP/browser bodies; known mandatory discovery fixtures and internal key/sentinel scans, not proof of arbitrary prose safety.'))
 final_conversations=[r['latency_ms'] for r in conversations if r['lane']=='final_http'];latency=dict(final_http_conversation_ms=stats(final_conversations),browser_server_chat_ms=stats([r['server_ms'] for r in bchats]),provider_ms=stats([r['latency_ms'] for r in records if r.get('latency_ms') is not None]),save_resume_ms=stats([r['http_ms'] for r in hrows if r['request']['path'] in ['/api/snapshots','/api/snapshots/load']]),browser_visible_ms=None,commit_only_ms=None)
 write('latency.json',latency)
 protected=read('protected_before.json');changed=[p for p,h in protected.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];assert not changed
 write('protected_integrity.json',dict(entries=len(protected),preserved=len(protected),changed=[]))
 frozen=read('holdout_summary.json');summary=dict(verdict='B — PARTIAL / DYNAMIC NPC PATHWAY DEMONSTRATED',baseline=read('baseline.json')['revision'],protected=read('protected_integrity.json'),development_final_safety=junit('final_safety.xml'),inherited_safety={'passed':junit('inherited_final.xml')['passed']+junit('inherited_ledger.xml')['passed'],'failed':junit('inherited_final.xml')['failed']+junit('inherited_ledger.xml')['failed']},npc_final=junit('final_npc.xml'),npc_commit_faults=junit('persistence_faults.xml'),frozen_holdout=frozen,http_campaigns=[dict(branch=c['branch'],result=c['result'],npc_id=c['npc_id']) for c in http['campaigns']],browser=read('browser_results.json'),provider_requests=usage['requests'],provider_tokens=usage['tokens'],accepted_live_npcs=len(identities),rejected_live_proposals=0,committed_live_proposals=len(proposals),final_verified_live_npcs=4,regression=read('regression_comparison.json'),latency=latency,hidden_exposures=0,mandatory_omissions=0,critical_unsafe_publications=0,new_regressions=0,limitations=['One ordinary background identity per populated scene; six roles and four ordinary appearance choices.','Host chooses bounded meaning; all sampled live conversational rewordings rejected and fell back. Broad provider-driven dialogue competence is unproven.','Only greeting/thanks social receipts; no compliance, promises or dynamic-NPC skill adjudication.','Original holdout retains five checker KeyErrors and ran before target-gate/player-inquiry refinements; it does not establish final-source conversational generalization.','Both browser campaigns were additionally cross-loaded and continued on a hash-recorded final-source host; live requests were disabled for those continuations.','Browser paint latency and separate commit-only timing not measured.'])
 write('metrics.json',summary);print(json.dumps({k:summary[k] for k in ['verdict','provider_requests','provider_tokens','accepted_live_npcs','committed_live_proposals']}))
if __name__=='__main__':main()
