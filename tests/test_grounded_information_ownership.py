"""HTTP possession authority, relevance, follow-up and nonexecution evidence."""
import copy
import json
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from game import storage
from game.api import app
from game.integrated_play import _LANES
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import seed_gate, CANARIES
from tests.test_ordinary_semantic_admission import state

@pytest.mark.parametrize('case,text,inventory,expected,disposition', [
 ('known','Do I have my spellbook?',None,'Spellbook','ANSWERABLE'),
 ('carrying','Am I carrying a spellbook?',None,'Spellbook','ANSWERABLE'),
 ('unknown','Am I carrying a lantern?',None,'cannot establish','UNKNOWN'),
 ('empty','Do I have a lantern?',[],'cannot establish','UNKNOWN'),
 ('zero','Do I have a lantern?',[{'id':'lantern','name':'Lantern','quantity':0}],'records no','ABSENT'),
 ('missing_quantity','Do I have a lantern?',[{'id':'lantern','name':'Lantern'}],'cannot establish','UNKNOWN'),
 ('ambiguous','Do I have a lantern?',[{'id':'lantern','name':'Lantern','quantity':1},{'id':'other','name':'Lantern','quantity':1}],'Which inventory item','AMBIGUOUS'),
 ('holding','What am I holding?',None,'held in your hands','UNKNOWN'),
 ('unbound','Do I still have it?',None,'Which inventory item','AMBIGUOUS'),
 ('private','Do I have a spellbook?',[{'id':'spellbook','name':'Spellbook','quantity':1,'secret':'CANARY_GM_NOTE','markings':['CANARY_UNDISCOVERED_CLUE']}],'Spellbook','ANSWERABLE'),
])
def test_http_possession(tmp_path,monkeypatch,case,text,inventory,expected,disposition):
 seed_gate(tmp_path,monkeypatch);_LANES.clear()
 for k in ('ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES'):monkeypatch.setenv(k,'1')
 if inventory is not None:
  c=storage.load_character();c['inventory']=inventory;storage.save_character(c)
 before=state();n=len(snapshot()['records'])
 with TestClient(app) as client:
  first=client.post('/api/chat?ui_mode=player',json={'text':text,'client_request_id':case})
  duplicate=client.post('/api/chat?ui_mode=player',json={'text':text,'client_request_id':case})
 after=state();visible=first.json()['gm_output']['player_facing_text'];decision=storage.load_log()[-1]['resolution']['metadata']['conversational_decision']
 checks={'http':first.status_code==duplicate.status_code==200,'duplicate':first.json()==duplicate.json(),'relevance':expected in visible,'disposition':decision['authorization']['information_disposition']==disposition,'disclosure':all(c not in visible for c in CANARIES),'providers':len(snapshot()['records'])==n}
 checks.update({k:before[k]==after[k] for k in ('character','world','scene','combat')})
 checks.update({k:before['session'].get(k)==after['session'].get(k) for k in ('turn_counter','clocks','scene_state','active_scene_id','last_publication')})
 out=os.environ.get('ASHEN_INFORMATION_EVIDENCE')
 if out:
  p=Path(out);p.mkdir(parents=True,exist_ok=True);(p/(case+'.json')).write_text(json.dumps({'request':text,'before':before,'after':after,'decision':decision,'response':first.json(),'assertions':checks,'provider_calls':len(snapshot()['records'])-n},indent=2))
 assert all(checks.values()),(checks,visible)


def test_followup_revalidates_current_inventory(tmp_path,monkeypatch):
 seed_gate(tmp_path,monkeypatch);_LANES.clear()
 for k in ('ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES'):monkeypatch.setenv(k,'1')
 providers_before=len(snapshot()['records'])
 with TestClient(app) as client:
  first=client.post('/api/chat?ui_mode=player',json={'text':'Do I have my spellbook?','client_request_id':'first'})
  providers_middle=len(snapshot()['records'])
  c=storage.load_character();c['inventory'][0]['quantity']=0;storage.save_character(c)
  before=state()
  second=client.post('/api/chat?ui_mode=player',json={'text':'Do I still have it?','client_request_id':'follow'})
 after=state();visible=second.json()['gm_output']['player_facing_text']
 assert len(snapshot()['records'])==providers_before
 assert 'Spellbook' in visible and 'records no' in visible,visible
 assert all(before[k]==after[k] for k in ('character','world','scene','combat'))
 assert before['session']['turn_counter']==after['session']['turn_counter']
 out=os.environ.get('ASHEN_INFORMATION_EVIDENCE')
 if out:(Path(out)/'followup.json').write_text(json.dumps({'request':'Do I still have it?','before':before,'after':after,'response':second.json(),'initial_response':first.json(),'decision':storage.load_log()[-1]['resolution']['metadata']['conversational_decision'],'provider_calls_by_request':[providers_middle-providers_before,len(snapshot()['records'])-providers_middle],'assertions':{'current_quantity_retrieved':True,'same_subject':True,'zero_providers':len(snapshot()['records'])==providers_before}},indent=2))

@pytest.mark.parametrize('text',['I take a lantern.','Do I have a lantern? I light it.','Do I have a lantern and a rope?','Gate Guard, do I have a lantern?'])
def test_possession_does_not_claim_actions_or_addressed_speech(text):
 from game.conversational_orchestration import _inventory_information_decision
 assert _inventory_information_decision(text,character={'inventory':[]},session={},scene={},log=[]) is None
