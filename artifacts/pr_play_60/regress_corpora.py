"""Replay preserved corpora read-only into PR60 evidence."""
import json,sys
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_60.prepare import write
from artifacts.pr_play_59.evaluate import evaluate as eval59, score as score59
from artifacts.pr_play_58.evaluate import contract_for, evaluate as eval58, score as score58
from tests.pr_play_59_development import cases as cases59
from tests.pr_play_58_development import cases as cases58
from tests.pr_play_55_evaluate import score_holdout,score_development,score_previous
from game import integrated_investigation_narration as i
from game.offline_investigation_projection import AuthorizedInvestigation
from game.anchored_investigation_narration import AnchoredInvestigation,DiscoveryAnchor,_resolution
def read(c,n):return json.loads((ROOT/f'artifacts/pr_play_{c}/{n}.json').read_text(encoding='utf-8'))
result={}
for label,corpus in [('development',cases59()),('holdout',read(59,'holdout')['cases'])]:
 rows=[eval59(c) for c in corpus]
 combined=[]
 for c in corpus:
  grants=c['authority'];outcomes=grants.get('authorized_outcomes',[])
  v=AuthorizedInvestigation('observed',None,None,(),(),tuple(grants.get('observable_scene',[])),' '.join(outcomes))
  contract=AnchoredInvestigation(v,tuple(DiscoveryAnchor(j,'engine_status','observed',t) for j,t in enumerate(outcomes)))
  val=i.validate_integrated(contract,{'must_communicate':[],'authorized_consequences':outcomes},c['text'])
  combined.append({**c,'actual':val['decision'],'validation':val})
 result[label]={'targeted':{'summary':score59(rows),'rows':rows},'combined':{'matched':sum(r['expected']==r['actual'] for r in combined),'total':len(combined),'rows':combined}}
write('pr59_regression.json',result)
result={}
for label,corpus in [('fixed',read(58,'fixed_samples')),('development',cases58()),('holdout',read(58,'holdout')['cases'])]:
 rows=[]
 for c in corpus:
  if label=='development':contract,request=i.outcome_contract(c['hook'])
  else:
   request=c['request'] if label=='fixed' else read(58,'holdout')['authorities'][c['authority']]
   contract=contract_for(request)
  rows.append(eval58(c,contract,request))
 old=read(59,'pr58_regression')[label]['rows'];previous={r['id']:r['actual'] for r in old}
 result[label]={'rows':rows,'changes_since_pr59':[{'id':r['id'],'before':previous[r['id']],'after':r['actual']} for r in rows if r['actual']!=previous[r['id']]]}
write('pr58_regression.json',result)
h=read(59,'h41_original');write('h41_after.json',i.validate_integrated(contract_for(h['request']),h['request'],h['case']['text']))
write('pr55_regression.json',{'holdout':score_holdout(),'development':score_development(),'previous':score_previous()})
d=read(60,'d25_original');v=AuthorizedInvestigation('observed',None,None,(),(),(),'You pick up the key.')
c=AnchoredInvestigation(v,(DiscoveryAnchor(0,'engine_status','observed','You pick up the key.'),))
req={'must_communicate':[]}
historical=i.validate_integrated(c,req,d['case']['text'])
explicit=replace(c,outcome=replace(v,inventory_effects_json=json.dumps({'items_added':['key']})))
write('d25_after.json',{'historical_exact':historical,'historical_projection':_resolution(c),'explicit_delta_control':i.validate_integrated(explicit,req,d['case']['text']),'explicit_projection':_resolution(explicit),'limitation':'Original historical fixture has no resolver record/delta. Explicit-delta control is separately labeled, never inferred by runtime from prose.'})
print('PR59 targeted and combined, PR58, PR57 samples, H41, D25 and PR55 replayed read-only.')
