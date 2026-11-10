"""Replay prior corpora into a new evidence directory; originals are never rewritten."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_59.evaluate import write
from artifacts.pr_play_58.evaluate import contract_for,evaluate,score
from game.integrated_investigation_narration import outcome_contract
from tests.pr_play_58_development import cases
from tests.pr_play_55_evaluate import score_holdout,score_development,score_previous
P=ROOT/'artifacts/pr_play_58'
def read(n):return json.loads((P/n).read_text(encoding='utf-8'))
result={}
for label,corpus in [('fixed',read('fixed_samples.json')),('development',cases()),('holdout',read('holdout.json')['cases'])]:
 rows=[]
 for c in corpus:
  if label=='development':contract,req=outcome_contract(c['hook'])
  else:
   req=c['request'] if label=='fixed' else read('holdout.json')['authorities'][c['authority']]
   contract=contract_for(req)
  rows.append(evaluate(c,contract,req))
 old=read('fixed_results.json') if label=='fixed' else read(label+'_results.json')['rows']
 previous={r['id']:r['actual'] for r in old}
 result[label]={'summary':score(rows),'rows':rows,'classification_changes':[{'id':r['id'],'before':previous[r['id']],'after':r['actual']} for r in rows if r['actual']!=previous[r['id']]]} if label!='fixed' else {'rows':rows,'classification_changes':[{'id':r['id'],'before':previous[r['id']],'after':r['actual']} for r in rows if r['actual']!=previous[r['id']]]}
write('pr58_regression.json',result)
write('pr55_regression.json',{'holdout':score_holdout(),'development':score_development(),'previous':score_previous()})
h=json.loads((ROOT/'artifacts/pr_play_59/h41_original.json').read_text(encoding='utf-8'))
from game.integrated_investigation_narration import validate_integrated
write('h41_after.json',validate_integrated(contract_for(h['request']),h['request'],h['case']['text']))
print({k:v.get('classification_changes') for k,v in result.items()})
