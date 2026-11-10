"""Small isolated measurements; no provider calls or normal campaign seeding."""
import sys,os,json,time,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));O=Path(__file__).parent
from tests.helpers.storage_isolation import install
install(O/'performance_data');os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
import pytest
from fastapi.testclient import TestClient
from game import api,bounded_improvisation as b
from tests.test_pr_play_71_lifecycle import configure,create,start,chat
from tests.test_pr_play_75_dynamic_npcs import context,proposal

def stats(a):return dict(count=len(a),mean=statistics.mean(a),median=statistics.median(a),maximum=max(a))
s,sc,w=context();timings=[]
for i in range(100):
 t=time.perf_counter();result=b.validate_npc_proposal(proposal(),session=s,scene=sc,world=w);assert result['accepted'];timings.append((time.perf_counter()-t)*1000)
rows=[]
with pytest.MonkeyPatch.context() as mp:
 configure(O/'performance_data',mp)
 with TestClient(api.app) as cl:
  create(cl);start(cl)
  for i in range(3):
   t=time.perf_counter();out=chat(cl,'I talk to Tavern Runner.');rows.append(dict(input='I talk to Tavern Runner.',response=out,latency_ms=(time.perf_counter()-t)*1000))
(O/'performance_supplement.json').write_text(json.dumps(dict(validation_ms=stats(timings),authored_npc_ms=stats([r['latency_ms'] for r in rows]),authored_interactions=rows,provider_requests=0,scope='Validator microbenchmark and ordinary authored NPC path with offline opening/narration fixture; not live authored dialogue.'),indent=2),encoding='utf-8')
print('Measured',len(rows),'authored interactions and',len(timings),'validations')
