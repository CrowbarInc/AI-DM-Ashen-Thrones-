"""One-shot frozen holdout evaluation after implementation freeze."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_play_63'
from game import integrated_investigation_narration as i
p=OUT/'frozen_holdout.json';manifest=json.loads((OUT/'frozen_holdout_manifest.json').read_text())
assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['sha256']
assert not (OUT/'holdout_results.json').exists(),'Frozen holdout must not rerun'
freeze={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['game/integrated_investigation_narration.py','game/consequential_narration_validation.py','game/mandatory_outcome_coverage.py']}
(OUT/'implementation_freeze.json').write_text(json.dumps(freeze,indent=2))
rows=[]
for case in json.loads(p.read_text()):
 c,r=i.outcome_contract(case['hook']);a=i.validate_integrated(c,r,case['candidate'])
 mandatory=[f['text'] for f in r['must_communicate']]
 fallback=i.action_fallback(c,case['hook']);publication='candidate' if a['decision']=='PASS' else 'fallback'
 rows.append({'id':case['id'],'group':case['group'],'expected_decision':case['expected_decision'],'actual_decision':a['decision'],'matches':a['decision']==case['expected_decision'] and mandatory==case['expected_mandatory_texts'] and publication==case['expected_publication'],'request':r,'validation':a,'publication':publication,'published':case['candidate'] if publication=='candidate' else fallback,'fallback_validation':i.validate_integrated(c,r,fallback)})
result={'cases':len(rows),'matched':sum(r['matches'] for r in rows),'critical_false_acceptances':[r['id'] for r in rows if r['expected_decision']!='PASS' and r['actual_decision']=='PASS'],'rows':rows,'implementation_hashes':freeze,'manifest_hash':manifest['sha256'],'executions':1}
(OUT/'holdout_results.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','implementation_hashes']}))
