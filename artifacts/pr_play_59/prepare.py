import json, hashlib, subprocess, sys
from pathlib import Path
ROOT=Path.cwd(); OUT=ROOT/'artifacts/pr_play_59'
sys.path.insert(0,str(ROOT))
from artifacts.pr_play_58.evaluate import contract_for
from game.integrated_investigation_narration import validate_integrated

def write(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
write('entry_status.json',{'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--porcelain'],text=True)})
write('entry_hashes.json',{p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for d in ['data','game','static','experiments'] for p in Path(d).rglob('*') if p.is_file() and '__pycache__' not in p.parts})
for name in ['consequential_narration_validation','integrated_investigation_narration']:
 (OUT/(name+'_before.py')).write_bytes((ROOT/'game'/ (name+'.py')).read_bytes())
old=json.loads((ROOT/'artifacts/pr_play_58/holdout.json').read_text(encoding='utf-8'))
c=next(c for c in old['cases'] if c['id']=='H41'); req=old['authorities'][c['authority']]
write('h41_original.json',{'source':'artifacts/pr_play_58/holdout.json','case':c,'request':req})
write('h41_before.json',validate_integrated(contract_for(req),req,c['text']))
rows=[]
def add(group,text,outcomes=(),scene=(),**authority):
 rows.append({'id':f'H{len(rows)+1:02}','group':group,'text':text,'authority':{'authorized_outcomes':outcomes,'observable_scene':scene,**authority},'expected':'FAIL' if group=='unauthorized' else 'REVIEW_REQUIRED' if group=='ambiguous' else 'PASS','expected_classification':group})
for t in ['The copper iris has been opened.','The trapdoor is now unlocked.','The aqueduct is now accessible.','The crystal lens has been destroyed.','The lookout is now unconscious.','The ferryman is now dead.','You are now poisoned.','You pick up the opal and place it in your pack.','The pilgrimage quest is now complete.','The courtyard is now flooded.','The ward is permanently broken.','The sluice will remain open from now on.','The west shutter opens.','The portal opens and the seal breaks.','The hatch can no longer be closed.']:
 add('unauthorized',t,('The east shutter opens.',) if 'west' in t else ('The portal opens.',) if 'portal' in t else ('The sluice opens temporarily.',) if 'sluice' in t else ())
for text,outcome in [('The copper iris swings open.','The copper iris opens.'),('The trapdoor stands unlocked.','The trapdoor is unlocked.'),('The aqueduct is now accessible.','The aqueduct becomes accessible.'),('The crystal lens is destroyed.','The crystal lens is destroyed.'),('The lookout falls unconscious.','The lookout is unconscious.'),('The ferryman is now dead.','The ferryman is dead.'),('The courtyard becomes flooded.','The courtyard is flooded.'),('The ward has been broken.','The ward is broken.'),('The shutter closes with a clatter.','The shutter closes.'),('The gangway gives way and falls into the ravine.','The gangway collapses.')]: add('authorized',text,(outcome,))
for t in ['The copper iris rattles in the wind.','Rain runs down the trapdoor.','The aqueduct creaks beneath your feet.','The lookout shifts his weight.','Dust settles on the courtyard.','The hinges groan.','The lantern flickers.','The ward looks old and weathered.','The shutter appears difficult to open.','The gangway seems narrow.']: add('harmless',t)
for g,t in [('negated','The iris does not open.'),('negated','The hatch remains closed.'),('negated','The lens has not been destroyed.'),('hypothetical','The ward might break.'),('hypothetical','If you repair it, the iris will open.'),('hypothetical','The shutter could be unlocked.'),('attempted','You try to open the trapdoor.'),('attempted','You attempt to break the seal.'),('attempted','You try to pick up the opal.'),('negated','The guard does not become unconscious.')]: add(g,t)
for t in ['The iris seems to have opened.','The seal may already be broken.','Something about the hatch has changed.','It is now open.','The ward yields.']: add('ambiguous',t)
write('holdout.json',{'cases':rows})
write('holdout_manifest.json',{'sha256':hashlib.sha256((OUT/'holdout.json').read_bytes()).hexdigest(),'cases':len(rows),'groups':{g:sum(r['group']==g for r in rows) for g in {r['group'] for r in rows}},'frozen_before_implementation':True,'independence':'Same-session author; frozen before edits. Not independent blind validation.','entry_implementation_sha256':hashlib.sha256((ROOT/'game/consequential_narration_validation.py').read_bytes()).hexdigest()})
print('H41 before:',json.loads((OUT/'h41_before.json').read_text())['decision'],'; frozen cases:',len(rows))
