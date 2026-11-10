"""Capture entry state and freeze developer-authored holdout before repair."""
import copy, hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_play_64'
from game import integrated_investigation_narration as i
from tests.test_pr_play_57_integrated_narration import hook, ROUTE
def save(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if (OUT/'baseline.json').exists():raise SystemExit('Entry evidence already captured')
save('baseline.json',{'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--short'],text=True),'protected_hashes':{p.as_posix():sha(p) for root in ['data','artifacts/atgb'] for p in (ROOT/root).rglob('*') if p.is_file()},'known_failures':json.loads((ROOT/'artifacts/pr_play_63/regression_summary_final.json').read_text())})
(OUT/'entry_source').mkdir(exist_ok=True)
for n in ['consequential_narration_validation','integrated_investigation_narration','mandatory_outcome_coverage']:
 (OUT/'entry_source'/f'{n}.py').write_bytes((ROOT/'game'/f'{n}.py').read_bytes())
for index,name in [(1,'historical'),(5,'gate')]:
 original=json.loads((ROOT/f'artifacts/pr_play_63/quarantine_evidence/pr_play_63_browser-{index:03}.json').read_text())
 c,r=i.outcome_contract(original['hook_input']);v=i.validate_integrated(c,r,original['raw_provider_text'])
 save(name+'_before.json',{'original':original,'request':r,'validation':v})
 print(name,v['decision'],v['semantic']['claims'])
rows=[]
def add(group,h,t,expected):
 c,r=i.outcome_contract(h)
 rows.append({'id':f'H{len(rows)+1:02}','group':group,'hook':h,'candidate':t,'expected_decision':expected,'expected_mandatory_texts':[f['text'] for f in r['must_communicate']],'expected_coverage':'PASS','expected_publication':'candidate' if expected=='PASS' else 'fallback'})
body=ROUTE[0].lower()+ROUTE[1:]
wrappers=['You learn that ','You read that ','You recognize that ','You realize that ','You understand that ','You study the notice board and learn that ','You examine the notice and read that ','Studying the notice reveals that ','The notice reveals that ','The notice records that ']
for w in wrappers:add('authorized_discovery',hook(),w+body,'PASS')
for extra in ['You discover a second patrol route.','You discover a hidden cache of weapons.','You learn that the gate is permanently open.','You discover the patrol was murdered.','You take the notice from the board.','You discover a red ribbon beneath the board.','The guard captain dies where he stands.','The missing patrol was last seen taking the southeast mud track past the crates.','You learn that the missing patrol was last seen taking the northwest mud track past the crates and a second patrol route.','You read that the missing patrol was last seen taking the northwest mud track past the crates and a hidden weapons cache.']:
 add('unauthorized_expansion',hook(),ROUTE+' '+extra,'FAIL')
for t in ['You take a careful look around the gate; no new clue is established.','You take a closer look at the gate; no new clue is established.','You take note of the gate; no new clue is established.','You examine the gate; no new clue is established.','You take a careful look and you take the iron key; no new clue is established.']:
 add('observation',hook(kind='investigate',clues=[]),t,'FAIL' if 'iron key' in t else 'PASS')
for t in ['You take the iron key.','You take the key and examine it.','You take the gate\'s key.','You acquire a silver compass.','You pocket the notice.']:
 add('item_acquisition',hook(),ROUTE+' '+t,'FAIL')
for k in range(5):
 t='No new clue is established.'+(' '+wrappers[k]+body if k%2 else '')
 add('prior_context',hook(kind='investigate',clues=[],known=(ROUTE,)),t,'PASS')
for k in range(5):
 missing=k in (1,3)
 add('mandatory',hook(known=(ROUTE,)),'You examine the notice board.' if missing else wrappers[k]+body,'REVIEW_REQUIRED' if missing else 'PASS')
for row in rows:
 if row['expected_decision']=='REVIEW_REQUIRED':row['expected_coverage']='REVIEW_REQUIRED'
save('frozen_holdout.json',rows)
save('frozen_holdout_manifest.json',{'cases':len(rows),'sha256':sha(OUT/'frozen_holdout.json'),'frozen_before_implementation':True,'distribution':{g:sum(r['group']==g for r in rows) for g in sorted({r['group'] for r in rows})},'limitations':'Developer-authored, not independent blind validation. Single execution after source freeze. No tuning against results.'})
