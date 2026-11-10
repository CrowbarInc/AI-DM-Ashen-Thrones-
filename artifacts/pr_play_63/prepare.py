import json,hashlib,subprocess,sys
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_play_63';OUT.mkdir(exist_ok=True)
from tests.test_pr_play_57_integrated_narration import hook,ROUTE
from game import integrated_investigation_narration as i

def save(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').rglob('*') if p.is_file()}
save('baseline.json',{'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--short'],text=True),'protected_hashes':protected,'source_hash':hashlib.sha256((ROOT/'game/integrated_investigation_narration.py').read_bytes()).hexdigest()})
history=json.loads((ROOT/'artifacts/pr_play_62/browser_actions.json').read_text(encoding='utf-8'))
save('pr_play_62_reconstruction.json',history)
rows=[]
def add(group,h,text,decision,mandatory):
 rows.append({'id':f'H{len(rows)+1:02}','group':group,'hook':h,'candidate':text,'expected_decision':decision,'expected_mandatory_texts':mandatory,'expected_publication':'candidate' if decision=='PASS' else 'fallback'})
status='No new clue is established by this examination.'
repeat='The examination adds nothing new to what you already know.'
for k in range(10):
 h=hook(known=(ROUTE,) if k%2 else ())
 add('new',h,ROUTE if k<5 else 'You examine the notice board.', 'PASS' if k<5 else 'REVIEW_REQUIRED',[ROUTE])
for k in range(10):
 h=hook(kind='investigate',clues=[],known=(ROUTE,));h['player_text']='I examine the rain barrel.'
 add('prior',h,'You examine the rain barrel; no new clue is established.'+(' '+ROUTE if k%2 else ''),'PASS',[status])
for k in range(5):
 add('repeat',hook(kind='already_searched',success=False,clues=[],known=(ROUTE,)),'You examine the notice board again; nothing new is established.','PASS',[repeat])
for k in range(5):
 # Resolver reselecting a fact makes it mandatory, even if also in post-state known.
 add('followup',hook(known=(ROUTE,)),ROUTE,'PASS',[ROUTE])
for k,text in enumerate(['You discover a silver key beneath the board.','You find a hidden passage.','You discover a red ribbon beneath the barrel.','You acquire a silver key.','The patrol took the southeast road.']):
 add('hidden',hook(kind='investigate',clues=[],known=(ROUTE,)),text,'FAIL',[status])
for k in range(5):
 h=hook(known=('Deep footprints mark the mud, but their number, origin, and direction remain unclear.',))
 add('mixed',h,ROUTE if k<3 else 'You examine the notice board.','PASS' if k<3 else 'REVIEW_REQUIRED',[ROUTE])
save('frozen_holdout.json',rows)
save('frozen_holdout_manifest.json',{'cases':40,'sha256':hashlib.sha256((OUT/'frozen_holdout.json').read_bytes()).hexdigest(),'frozen_before_implementation':True,'source_fixtures':['tests/test_pr_play_57_integrated_narration.py','artifacts/pr_play_62/browser_actions.json'],'limitations':'Same-session authored holdout; repeated shapes are boundary controls, not independent blind generalization. Run exactly once after source freeze.'})
replay=[]
for row in history:
 q=row['quarantine'];h=q.get('hook_input')
 if h and q.get('raw_provider_text'):
  c,r=i.outcome_contract(h);replay.append({'action':row['input'],'candidate':q['raw_provider_text'],'request':r,'validation':i.validate_integrated(c,r,q['raw_provider_text'])})
save('entry_revalidation.json',replay)
print('Baseline, original traces, entry revalidation and 40-case holdout frozen.')
