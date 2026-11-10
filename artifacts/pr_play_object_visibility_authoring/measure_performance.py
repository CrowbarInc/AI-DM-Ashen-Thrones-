"""Bounded comparable in-memory projections and isolated atomic writer timing."""
from pathlib import Path
import json
import os
import sys
import time
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
for key in ('ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES'):
    os.environ[key]='1'
def guard(event,args):
    if event in ('socket.connect','socket.getaddrinfo'): raise RuntimeError('Networking forbidden in benchmark')
sys.addaudithook(guard)
from game import object_marking as m, object_observation as o, storage
e=json.loads((OUT/'classification_timeline.json').read_text())
c0=e['initial']; c1=e['snapshots'][1]['state']; r1,r2=e['requests'][:2]
a1=m._establish_visibility_authorization(r1); a2=m._establish_visibility_authorization(r2)
def measure(fn,n=100):
    start=time.perf_counter()
    for _ in range(n): result=fn()
    return dict(mean_us=round((time.perf_counter()-start)*1e6/n,3),iterations=n)
def observe(c):
    req=dict(version=1,campaign_run_id=r1['campaign_run_id'],character_id=c['id'],
        instance_id=r1['instance_id'],observer_id='benchmark-observer',scope='established-visual-inspection',categories=['markings'])
    auth=o._establish_observation_authorization(c,req,decision_ref='benchmark',visibility_ref='benchmark',access_ref='benchmark')
    return o.observe_object(c,req,authorization=auth)
target=ROOT/'development/tmp/visibility_authoring_benchmark/character.json'
target.parent.mkdir(parents=True,exist_ok=True)
candidate=m.prepare_visibility(c0,r1,authorization=a1)['character']
result=dict(initial_validation=measure(lambda:m.prepare_visibility(c0,r1,authorization=a1)),
    transition_validation=measure(lambda:m.prepare_visibility(c1,r2,authorization=a2)),
    exact_replay_validation=measure(lambda:m.prepare_visibility(c1,r1,authorization=a1)),
    atomic_persistence=measure(lambda:storage._atomic_save_json(target,candidate),25),
    observation_unclassified=measure(lambda:observe(c0)),observation_visible=measure(lambda:observe(c1)),
    observation_concealed=measure(lambda:observe(e['snapshots'][2]['state'])),
    receipt_bytes_per_classification=[len(json.dumps(r,separators=(',',':')).encode()) for r in e['results']],
    initial_ledger_bytes=len(json.dumps(c0[m.LEDGER]).encode()),
    final_ledger_bytes=len(json.dumps(e['final'][m.LEDGER]).encode()),
    live_provider_calls=0,network_attempts=0,prompt_expansion=0)
assert json.loads(target.read_text())==candidate
(OUT/'performance_refined.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
