import json,sys,time,statistics,hashlib
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_play_59'
from game import consequential_narration_validation as s
from game.persistent_consequence_claims import validate_persistent,assertions
from artifacts.pr_play_58.evaluate import contract_for
from game.integrated_investigation_narration import validate_integrated
from tests.pr_play_59_development import cases

def write(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def read(n): return json.loads((OUT/n).read_text(encoding='utf-8'))
def hashes(): return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['game/persistent_consequence_claims.py','game/consequential_narration_validation.py','game/integrated_investigation_narration.py','game/mandatory_outcome_coverage.py']}
def evaluate(c):
 a=s.SemanticAuthority(**{k:tuple(v) if isinstance(v,list) else v for k,v in c['authority'].items()})
 start=time.perf_counter();validate_persistent(c['text'],a);persistent_ms=(time.perf_counter()-start)*1000
 start=time.perf_counter();result=s.validate_consequential_narration(c['text'],a);combined_ms=(time.perf_counter()-start)*1000
 return {**c,'actual':result['decision'],'validation':result,'frames':[vars(f) for f in assertions(c['text'])],'persistent_ms':persistent_ms,'semantic_ms':combined_ms}
def score(rows):
 return {'total':len(rows),'groups':{g:{'total':len(rr:=[r for r in rows if r['group']==g]),'exact_expected':sum(r['actual']==r['expected'] for r in rr),'blocked':sum(r['actual']!='PASS' for r in rr),'pass':sum(r['actual']=='PASS' for r in rr)} for g in sorted({r['group'] for r in rows})},'critical_false_acceptance_ids':[r['id'] for r in rows if r['group']=='unauthorized' and r['actual']=='PASS'],'false_rejection_ids':[r['id'] for r in rows if r['expected']=='PASS' and r['actual']!='PASS'],'review_required':sum(r['actual']=='REVIEW_REQUIRED' for r in rows),'validation_errors':sum(r['actual']=='VALIDATION_ERROR' for r in rows),'confusion':dict(Counter(r['expected']+'->'+r['actual'] for r in rows)),'latency':{k:{'average_ms':statistics.fmean(r[k] for r in rows),'maximum_ms':max(r[k] for r in rows)} for k in ['persistent_ms','semantic_ms']}}
def run(label,corpus):
 rows=[evaluate(c) for c in corpus]; result={'summary':score(rows),'rows':rows};write(label+'_results.json',result);print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':
 if sys.argv[1]=='development':
  write('development_corpus.json',cases());run('development',cases())
 elif sys.argv[1]=='freeze':write('implementation_frozen.json',hashes())
 elif sys.argv[1]=='holdout':
  assert read('implementation_frozen.json')==hashes()
  assert hashlib.sha256((OUT/'holdout.json').read_bytes()).hexdigest()==read('holdout_manifest.json')['sha256']
  with (OUT/'holdout_started.json').open('x') as f:json.dump(hashes(),f)
  run('holdout',read('holdout.json')['cases'])
