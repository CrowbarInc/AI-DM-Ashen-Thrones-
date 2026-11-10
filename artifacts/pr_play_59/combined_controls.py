import sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from artifacts.pr_play_59.evaluate import write
from tests.pr_play_59_development import cases
from game.offline_investigation_projection import AuthorizedInvestigation
from game.anchored_investigation_narration import AnchoredInvestigation,DiscoveryAnchor
from game.integrated_investigation_narration import validate_integrated
rows=[]
for c in cases():
 a=c['authority']; outcomes=a.get('authorized_outcomes',[])
 # Trusted synthetic engine projection; no grant is derived from candidate prose.
 view=AuthorizedInvestigation('observed',None,None,(),(),tuple(a.get('observable_scene',[])),' '.join(outcomes))
 contract=AnchoredInvestigation(view,tuple(DiscoveryAnchor(j,'engine_status','observed',t) for j,t in enumerate(outcomes)))
 request={'must_communicate':[],'authorized_consequences':outcomes}
 start=time.perf_counter();result=validate_integrated(contract,request,c['text']);ms=(time.perf_counter()-start)*1000
 rows.append({**c,'actual':result['decision'],'validation':result,'combined_ms':ms})
write('combined_development_results.json',{'rows':rows,'mismatches':[{'id':r['id'],'text':r['text'],'expected':r['expected'],'actual':r['actual']} for r in rows if r['actual']!=r['expected']],'scope':'Synthetic trusted consequence projections; empty mandatory fact list isolates authority behavior. Ordinary runtime request still grants no persistent changes.'})
print(json.dumps([{'id':r['id'],'expected':r['expected'],'actual':r['actual'],'legacy_reasons':r['validation']['legacy'].get('reasons')} for r in rows if r['actual']!=r['expected']],indent=2))
