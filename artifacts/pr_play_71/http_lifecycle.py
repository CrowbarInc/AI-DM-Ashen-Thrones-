import sys,json,copy,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import pytest
from artifacts.pr_play_67 import http_harness as h
from tests.test_pr_play_71_lifecycle import configure,byid,flags
from game import storage
OUT=Path(__file__).resolve().parent
rows=[];summaries=[]
with pytest.MonkeyPatch.context() as mp:
 configure(OUT/'http_data',mp)
 with h.server() as request:
  def call(path,payload=None):
   before=h.snapshot();r=request(path,payload);r.update(authority_before=before,authority_after=h.snapshot());rows.append(r)
   (OUT/'http_traces.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
   assert r['status']==200 and not r['hidden_exposures'],r
   return r['body']
  saves={}
  for branch in ['survey','report']:
   created=call('/api/new_campaign',{});identity=created['campaign_run_id']
   started=call('/api/start_campaign',{});assert started['session']['campaign_started']
   for text in ['I examine the notice board.','I follow the missing patrol rumor.','I examine the weathered milestone.']:
    call('/api/chat',{'text':text})
   def act(aid):
    a=byid(aid);return call('/api/action',{'action_type':'exploration','intent':a['label'],'exploration_action':{'id':aid,'label':a['label'],'type':'custom'}})
   act('patrol_'+branch)
   if branch=='report':call('/api/chat',{'text':'I return to Cinderwatch Gate.'})
   follow='patrol_record_survey' if branch=='survey' else 'patrol_warn_watch';act(follow)
   committed=copy.deepcopy(flags())
   saved=call('/api/snapshots',{'label':'HTTP '+branch})['snapshot']['id'];saves[branch]=(saved,identity,committed)
   call('/api/snapshots/load',{'snapshot_id':saved});assert flags()==committed
   act(follow);act('patrol_'+('report' if branch=='survey' else 'survey'));assert flags()==committed
   call('/api/chat',{'text':'I examine the mud prints.' if branch=='survey' else 'I examine the notice board.'});assert flags()==committed
   summaries.append(dict(branch=branch,campaign_run_id=identity,session_id=storage.load_session()['session_id'],snapshot_id=saved,flags=committed,resumed=True,continued=True))
  for branch,(saved,identity,committed) in saves.items():
   call('/api/snapshots/load',{'snapshot_id':saved});assert storage.load_session()['campaign_run_id']==identity and flags()==committed
  assert summaries[0]['campaign_run_id']!=summaries[1]['campaign_run_id']
(OUT/'http_summary.json').write_text(json.dumps(dict(campaigns=summaries,requests=len(rows),gameplay_actions=sum(r['request']['path'] in ['/api/action','/api/chat'] for r in rows),mean_ms=sum(r['http_ms'] for r in rows)/len(rows),max_ms=max(r['http_ms'] for r in rows),hidden_exposures=sum(bool(r['hidden_exposures']) for r in rows),provider='offline fixture; live configured provider tested separately in browser'),indent=2))
