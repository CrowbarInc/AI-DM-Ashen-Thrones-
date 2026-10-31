"""Post-selection robustness measurements, no prompt tuning and no stopped-C calls."""
import copy,importlib.util,json,time,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[1]))
spec=importlib.util.spec_from_file_location('r2a_experiment',H/'experiment.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
e.verify();rows=e.read('corpus.json')
ids=['borderline01','borderline04','borderline10','commitment01','commitment04','commitment08']
e.write('supplement_plan.json',dict(ids=ids,scope='B development-only annotation repeatability and one-candidate latency, plus deterministic forged provenance. C remains stopped.',trials=['B_repeat_1','B_repeat_2','B_single_1','B_single_2']))
from game.config import get_openai_api_key
from game.model_routing import resolve_model_route
from openai import OpenAI
client=OpenAI(api_key=get_openai_api_key(),base_url='https://api.openai.com/v1',timeout=45,max_retries=0)
model=resolve_model_route(purpose='strict_social').selected_model
for n in [1,2]:
 row=e.call('B',[next(c for c in rows if c['id']==i) for i in ids],client,model,f'B_repeat_{n}')
 if row.get('error'):break
else:
 for n in [1,2]:
  row=e.call('B',[next(c for c in rows if c['id']=='commitment08')],client,model,f'B_single_{n}')
  if row.get('error'):break
forged=[]
for cid in ['expansion01','mixed02','contradiction01','hidden01','paraphrase01']:
 c=next(x for x in rows if x['id']==cid)
 envelope=dict(speech=c['candidate'],claims=[dict(text=c['candidate'],source_id='F1',incidental=True,commitment=False,uncertain=False)])
 forged.append(dict(id=cid,envelope=envelope,result=e.structured(c,envelope),expected=c['expected']))
e.write('forged_provenance.json',forged)
timings={}
for kind in ['A','B']:
 vals=[]
 for c in rows:
  start=time.perf_counter_ns()
  for _ in range(100):
   if kind=='A':e.deterministic(c)
   else:e.structured(c,dict(speech=c['candidate'],claims=[dict(source_id=None)]))
  vals.append((time.perf_counter_ns()-start)/100/1e6)
 timings[kind]=dict(per_candidate_ms=vals,scope='100 hot repeated local checks per case; excludes structured generation/network and cold imports')
e.write('local_timing.json',timings)
