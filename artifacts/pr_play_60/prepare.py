"""Freeze same-session end-to-end cases before implementation edits."""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_play_60';OUT.mkdir(exist_ok=True)
SOURCES=['game/offline_investigation_projection.py','game/anchored_investigation_narration.py','game/integrated_investigation_narration.py','game/consequential_narration_validation.py','game/mechanical_claims.py','game/mandatory_outcome_coverage.py']
def write(n,v): (OUT/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def hashes(): return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
if __name__=='__main__':
 assert not (OUT/'holdout_manifest.json').exists()
 status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
 write('entry_status.json',{'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':status})
 protected=[p for p in (ROOT/'data').rglob('*') if p.is_file()]+[p for p in (ROOT/'game').glob('*.py')]+[ROOT/'docs/NEXT_SESSION.md']
 write('entry_hashes.json',{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in protected})
 for p in SOURCES:(OUT/(Path(p).stem+'_before.py')).write_bytes((ROOT/p).read_bytes())
 rows=[]
 route='The missing patrol was last seen taking the northwest mud track past the crates.'
 def add(group,text,effects=None,outcomes=(),mandatory=True,expected=None):
  rows.append({'id':f'H{len(rows)+1:02}','group':group,'text':text,'resolution':{'kind':'discover_clue','success':True,'discovered_clues':[route] if mandatory else [],'state_changes':effects or {}},'outcomes':list(outcomes),'mandatory':mandatory,'expected':expected or ('FAIL' if group.startswith('unauthorized') else 'REVIEW_REQUIRED' if group in ('missing','ambiguous') else 'PASS'),'expected_layers':{'semantic':'FAIL' if group.startswith('unauthorized') else 'REVIEW_REQUIRED' if group=='ambiguous' else 'PASS','legacy':'REJECT' if group.startswith('unauthorized') else 'ACCEPT','coverage':'REVIEW_REQUIRED' if group=='missing' else 'PASS'}})
 for item,verb in [('amber token','receive'),('bronze key','acquire'),('sealed letter','obtain'),('iron ring','collect'),('copper charm','receive'),('jade bead','acquire'),('ivory die','obtain'),('opal shard','collect'),('tin badge','receive'),('bone whistle','acquire')]:
  add('authorized_inventory',route+f' You {verb} the {item}.',{'items_added':[{'id':item.replace(' ','_'),'name':item,'quantity':1}]})
 for text in ['You acquire a sapphire.','You find a silver key in your pack.','The guard gives you a sword.','You now possess three gold coins.','You receive two bronze keys.','Mira receives the bronze key.','You receive the bronze key from the ferryman.','You receive the bronze key and a ruby.','You lose the bronze key.','You drink both healing potions.']:
  add('unauthorized_inventory',route+' '+text,{'items_added':['bronze key']} if 'bronze key' in text else {})
 pairs=[('The copper iris swings open.','The copper iris opens.'),('The hatch stands unlocked.','The hatch is unlocked.'),('The aqueduct is now accessible.','The aqueduct becomes accessible.'),('The lens is destroyed.','The lens is destroyed.'),('The lookout falls unconscious.','The lookout is unconscious.'),('The ferryman is now dead.','The ferryman is dead.'),('The courtyard becomes flooded.','The courtyard is flooded.'),('The ward has been broken.','The ward is broken.'),('The shutter closes with a clatter.','The shutter closes.'),('The gangway collapses.','The gangway collapses.')]
 for t,g in pairs:add('authorized_noninventory',route+' '+t,outcomes=[g])
 for t in ['The trapdoor is now unlocked.','The iris is permanently open.','The aqueduct is now accessible.','The crystal lens has been destroyed.','The lookout is now unconscious.','The ferryman is now dead.','You are now poisoned.','The pilgrimage quest is now complete.','The courtyard is now flooded.','The hatch can no longer be closed.']:add('unauthorized_persistent',route+' '+t)
 for t in ['The lantern flickers.','Rain runs down the board.','The bridge creaks.','The guard shifts his weight.','Dust settles.','The hinges groan.','The iris rattles in the wind.','The ward looks old and weathered.','The shutter appears difficult to open.','The gangway seems narrow.']:add('harmless',route+' '+t)
 for t in ['Rain falls.','You study the board.','The patrol followed a muddy path.','The lantern flickers.','You receive the bronze key.']:add('missing',t,{'items_added':['bronze key']} if 'receive' in t else {})
 for t in ['The iris seems to have opened.','The seal may already be broken.','Something about the hatch has changed.','It is now open.','The ward yields.']:add('ambiguous',route+' '+t)
 write('holdout.json',{'cases':rows,'scope':'Complete validators; inventory resolver deltas are synthetic adapter controls, not executed item gameplay. Noninventory grants use historical trusted engine-status controls.'})
 write('holdout_manifest.json',{'sha256':hashlib.sha256((OUT/'holdout.json').read_bytes()).hexdigest(),'count':len(rows),'entry_source_hashes':hashes(),'independence':'Same-session authorship; frozen before implementation, not independent blind evidence.'})
 old=json.loads((ROOT/'artifacts/pr_play_59/combined_positive_preexisting.json').read_text())
 write('d25_original.json',old)
 from game.offline_investigation_projection import AuthorizedInvestigation
 from game.anchored_investigation_narration import AnchoredInvestigation, DiscoveryAnchor
 from game.integrated_investigation_narration import validate_integrated
 view=AuthorizedInvestigation('observed',None,None,(),(),(),'You pick up the key.')
 contract=AnchoredInvestigation(view,(DiscoveryAnchor(0,'engine_status','observed','You pick up the key.'),))
 write('d25_before.json',{'resolution_available':False,'historical_structured_effects':None,'projection':{'kind':'investigate','state_changes':{}},'validation':validate_integrated(contract,{'must_communicate':[]},old['case']['text'])})
 print('Frozen',len(rows),'cases; D25 before FAIL. Historical D25 has text authority only, no structured delta.')
