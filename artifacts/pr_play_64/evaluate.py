"""Development evidence, historical replay and one-shot frozen holdout."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_play_64'
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
os.environ[q.PUBLICATION_ENV]='1'
if '--holdout' not in sys.argv:
 from tests.pr_play_64_development import cases,evaluate
 rows=[evaluate(c) for c in cases()];save('development_results.json',rows)
 for name in ['historical','gate']:
  d=json.loads((OUT/(name+'_before.json')).read_text());o=d['original'];c,r=i.outcome_contract(o['hook_input'])
  save(name+'_after.json',{'candidate':o['raw_provider_text'],'hook':o['hook_input'],'request':r,'validation':i.validate_integrated(c,r,o['raw_provider_text']),'result':i.run_integrated_hook(o['hook_input'],generator=q._Replay(o['raw_provider_text'],''))})
 print(json.dumps({'development_cases':len(rows),'matched':sum(r['matches'] for r in rows),'failures':[{k:r[k] for k in ['id','actual','expected','validation']} for r in rows if not r['matches']]}))
else:
 assert not (OUT/'holdout_results.json').exists(),'One-shot holdout already executed'
 p=OUT/'frozen_holdout.json';m=json.loads((OUT/'frozen_holdout_manifest.json').read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
 freeze={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['game/consequential_narration_validation.py','game/integrated_investigation_narration.py','game/mechanical_claims.py','game/mandatory_outcome_coverage.py']}
 save('implementation_freeze.json',freeze);rows=[]
 for case in json.loads(p.read_text()):
  c,r=i.outcome_contract(case['hook']);v=i.validate_integrated(c,r,case['candidate']);pub='candidate' if v['decision']=='PASS' else 'fallback'
  fallback=i.action_fallback(c,case['hook']);fv=i.validate_integrated(c,r,fallback)
  rows.append(dict(case,request=r,validation=v,actual=v['decision'],publication=pub,published=case['candidate'] if pub=='candidate' else fallback,fallback_validation=fv,matches=v['decision']==case['expected_decision'] and v['coverage']['decision']==case['expected_coverage'] and pub==case['expected_publication'] and [f['text'] for f in r['must_communicate']]==case['expected_mandatory_texts'] and fv['decision']=='PASS'))
 result={'cases':len(rows),'matched':sum(r['matches'] for r in rows),'false_acceptances':[r['id'] for r in rows if r['expected_decision']!='PASS' and r['actual']=='PASS'],'false_rejections':[r['id'] for r in rows if r['expected_decision']=='PASS' and r['actual']!='PASS'],'rows':rows,'executions':1,'hash':m['sha256']}
 save('holdout_results.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
