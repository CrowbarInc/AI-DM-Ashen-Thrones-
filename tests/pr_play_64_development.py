"""Development fixtures; frozen holdout is separate and never imported here."""
import copy, json
from pathlib import Path
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
from tests.test_pr_play_57_integrated_narration import hook, ROUTE
OUT=Path(__file__).resolve().parents[1]/'artifacts/pr_play_64'
def cases():
 rows=[]
 def add(name,text,expected='PASS',h=None,fault=''):
  rows.append({'id':f'D{len(rows)+1:02}','name':name,'hook':hook() if h is None else h,'candidate':text,'expected':expected,'fault':fault})
 historical=json.loads((OUT/'historical_before.json').read_text())['original']
 gate=json.loads((OUT/'gate_before.json').read_text())['original']
 body=ROUTE[0].lower()+ROUTE[1:]
 add('exact historical',historical['raw_provider_text'],h=historical['hook_input'])
 for word in ['learn','read']:
  add(word,'You '+word+' that '+body)
 add('study','You study the notice board and learn that '+body)
 add('recognize','You recognize that '+body)
 add('reveals','Studying the notice reveals that '+body)
 add('reordered','Past the crates, the missing patrol was last seen taking the northwest mud track.')
 for name,text in [('additional','You discover a blue ribbon.'),('second route','You discover a second patrol route.'),('cache','The notice reveals a hidden cache of weapons.'),('death','You discover the patrol was murdered.'),('gate','You learn that the gate is permanently open.'),('mixed expansion','You learn that '+body[:-1]+' and a hidden cache of weapons.')]:
  add(name,ROUTE+' '+text,'FAIL')
 add('atmosphere','Rain falls. You learn that '+body)
 prior=hook(kind='investigate',clues=[],known=(ROUTE,))
 add('prior referenced','No new clue is established. You learn that '+body,h=prior)
 add('prior omitted','You examine the barrel; no new clue is established.',h=prior)
 add('new omitted','You examine the notice board.','REVIEW_REQUIRED')
 add('hidden identifier',ROUTE+' CANARY_HIDDEN_DESTINATION is behind the gate.','FAIL')
 add('exact gate',gate['raw_provider_text'],h=gate['hook_input'])
 add('observation','You take a careful look; no new clue is established.',h=hook(kind='investigate',clues=[]))
 add('physical acquisition',ROUTE+' You take the iron key.','FAIL')
 inventory=hook();inventory['resolution']['state_changes']={'items_added':['iron key']}
 c,r=i.outcome_contract(inventory)
 add('structured inventory',i.action_fallback(c,inventory),h=inventory)
 add('observation plus item',ROUTE+' You take a careful look and you take the key and examine it.','FAIL')
 add('ambiguous acquisition',ROUTE+' The cache yields.','REVIEW_REQUIRED')
 add('repeat','You examine it again; nothing new is established.',h=hook(kind='already_searched',success=False,clues=[],known=(ROUTE,)))
 follow=copy.deepcopy(prior);follow['player_text']='What did the notice say about the patrol?'
 add('known followup','No new clue is established. You read that '+body,h=follow)
 add('provider failure',None,'VALIDATION_ERROR',fault='provider_error')
 add('validation fallback',ROUTE+' You acquire a ruby.','FAIL')
 add('rejection state integrity',ROUTE+' The gate is permanently open.','FAIL')
 add('detached no authority','No new clue is established. You learn that '+body,'FAIL',h=hook(kind='investigate',clues=[]))
 return rows

def evaluate(case):
 h=copy.deepcopy(case['hook']);before=copy.deepcopy(h)
 c,r=i.outcome_contract(h)
 result=i.run_integrated_hook(h,generator=q._Replay(case['candidate'],case['fault']))
 actual=result['validation'].get('decision',result.get('diagnostic'))
 return dict(case,request=r,actual=actual,matches=actual==case['expected'],state_unchanged=h==before,
             validation=result['validation'],claims=(result['validation'].get('semantic') or {}).get('claims',[]),
             result=result,fallback_validation=i.validate_integrated(c,r,i.action_fallback(c,h)))
