"""Complete-pipeline traces, immutable input checks and latency; no provider."""
import copy, hashlib, json, statistics, sys, time
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_60.prepare import OUT, write, hashes
from game import integrated_investigation_narration as i, anchored_investigation_narration as a
from game import consequential_narration_validation as s
from game import quarantined_investigation_narration as q
from game.persistent_consequence_claims import validate_persistent
from game.resolution_contract import contract_mapping_from_resolution
from game.immutable_valid_response import validate_generated_response
from tests.test_pr_play_57_integrated_narration import ROUTE,hook

def run(c):
 h=hook();h['resolution']=copy.deepcopy(c['resolution'])
 before=copy.deepcopy(h)
 start=time.perf_counter();contract,req=i.outcome_contract(h);projection_ms=(time.perf_counter()-start)*1000
 if c.get('outcomes'):
  contract=replace(contract,anchors=contract.anchors+tuple(a.DiscoveryAnchor(100+j,'engine_status','observed',t) for j,t in enumerate(c['outcomes'])))
  req['authorized_consequences']=c['outcomes']
 # Disclosure-free synthetic controls do not claim a new investigation status.
 if not c.get('mandatory',True):req['must_communicate']=[f for f in req['must_communicate'] if f['source']=='inventory_effect']
 authority=s.authority_from_anchored(contract);r=a._resolution(contract)
 timings={};individual={}
 for name,fn in [('legacy',lambda:validate_generated_response(c['text'],resolution=r,contract=contract_mapping_from_resolution(r))),('persistent',lambda:validate_persistent(c['text'],authority)),('semantic',lambda:s.validate_consequential_narration(c['text'],authority)),('coverage',lambda:i.mandatory_coverage(c['text'],req)),('combined',lambda:i.validate_integrated(contract,req,c['text']))]:
  start=time.perf_counter();individual[name]=fn();timings[name]=(time.perf_counter()-start)*1000
 assert h==before, 'Authoritative input divergence'
 return {**c,'context':req,'contract':asdict(contract),'validation_projection':r,'legacy_contract':contract_mapping_from_resolution(r),'semantic_authority':asdict(authority),'individual':individual,'actual':individual['combined']['decision'],'state_unchanged':True,'timings_ms':{'projection':projection_ms,**timings}}

def score(rows):
 return {'total':len(rows),'matched':sum(r['expected']==r['actual'] for r in rows),'confusion':dict(Counter(r['expected']+'->'+r['actual'] for r in rows)),'critical_false_acceptance_ids':[r['id'] for r in rows if r['expected']!='PASS' and r['actual']=='PASS'],'false_rejection_ids':[r['id'] for r in rows if r['expected']=='PASS' and r['actual']!='PASS'],'review_required':sum(r['actual']=='REVIEW_REQUIRED' for r in rows),'groups':{g:dict(Counter(r['actual'] for r in rows if r['group']==g)) for g in sorted({r['group'] for r in rows})},'latency':{k:{'average_ms':statistics.fmean(r['timings_ms'][k] for r in rows),'maximum_ms':max(r['timings_ms'][k] for r in rows)} for k in rows[0]['timings_ms']}}

def development_cases():
 rows=[]
 def add(group,text,effects=None,mandatory=True,expected='PASS',**kw):
  rows.append({'id':f'D{len(rows)+1:02}','group':group,'text':(ROUTE+' ' if mandatory and group!='missing' else '')+text,'resolution':{'kind':'discover_clue','success':True,'discovered_clues':[ROUTE] if mandatory else [],'state_changes':effects or {}},'mandatory':mandatory,'expected':expected,**kw})
 for text in ['You pick up the key and place it in your pack.','You retrieve the iron key and place it in your pack.','The iron key is yours now.','You take possession of the iron key.','You acquire the iron key.','You receive the iron key.']:
  add('authorized_inventory',text,{'items_added':['key' if 'the key' in text else 'iron key']})
 add('authorized_quantity','You receive three iron keys.',{'items_added':[{'id':'iron_key','name':'iron key','quantity':3}]})
 add('authorized_removal','You lose the iron key.',{'items_removed':['iron key']})
 for t in ['You receive a silver key.','You acquire two iron keys.','Mira receives the iron key.','You receive the iron key from the guard.','The guard gives you the iron key.','You receive the iron key and a ruby.','You drink the healing potion.','You hand over the iron key.','You equip the iron key.']:
  add('unauthorized_inventory',t,{'items_added':['iron key']},expected='FAIL')
 for t in ['You find a silver key in your pack.','You acquire a healing potion.','The guard gives you a sword.','You now possess three gold coins.']:
  add('unauthorized_inventory',t,expected='FAIL')
 for t in ['You might acquire the iron key.','You try to pick up the iron key.','You do not acquire the iron key.']:add('nonactual',t)
 for t in ['The gate is now permanently open.','The guard is now incapacitated.','The quest is now complete.']:add('unauthorized_persistent',t,expected='FAIL')
 for t in ['The lantern flickers.','Dust settles on the board.','The guard shifts his weight.']:add('harmless',t)
 add('missing','Rain falls.',expected='REVIEW_REQUIRED')
 add('contradiction','Your investigation fails.',expected='FAIL')
 add('ambiguous','Something about the mechanism has changed.',expected='REVIEW_REQUIRED')
 add('authorized_noninventory','The gate swings open.',outcomes=['The gate opens.'])
 return rows

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='development':
  cases=development_cases();write('development_corpus.json',cases)
 elif mode=='holdout':
  assert not (OUT/'holdout_started.json').exists(),'One execution only'
  assert json.loads((OUT/'implementation_frozen.json').read_text())==hashes()
  manifest=json.loads((OUT/'holdout_manifest.json').read_text());assert manifest['sha256']==hashlib.sha256((OUT/'holdout.json').read_bytes()).hexdigest()
  write('holdout_started.json',{'source_hashes':hashes(),'execution_count':1})
  cases=json.loads((OUT/'holdout.json').read_text())['cases']
 else:raise ValueError(mode)
 rows=[run(c) for c in cases];summary=score(rows);write(mode+'_results.json',{'summary':summary,'rows':rows});print(json.dumps(summary,indent=2))
