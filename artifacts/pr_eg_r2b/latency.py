"""One sequential generation/validation pair for interactive-scale measurement."""
import json,sys,time,statistics
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from experiment import call,contract,deterministic,read,write
from game.config import get_openai_api_key
from game.model_routing import resolve_model_route
from openai import OpenAI
c=next(x for x in read('corpus.json') if x['id']=='paraphrase01');samples=[]
for _ in range(1000):
 start=time.perf_counter();k=contract(c);deterministic(c);samples.append((time.perf_counter()-start)*1000)
client=OpenAI(api_key=get_openai_api_key(),base_url='https://api.openai.com/v1',timeout=45,max_retries=0);model=resolve_model_route(purpose='strict_social').selected_model
start=time.perf_counter();g=call(client,model,'generation',[dict(id='interactive01',contract=k)],'interactive_generation')
v=None
if not g.get('error'):v=call(client,model,'validation',[dict(id='interactive01',contract=k,candidate=g['parsed'][0]['speech'])],'interactive_validation')
write('interactive_latency.json',dict(scope='One isolated synthetic pair, no interpretation, production prompt, HTTP or persistence; not production qualification',local_contract_plus_deterministic_median_ms=statistics.median(samples),local_iterations=1000,sequential_ms=(time.perf_counter()-start)*1000,generation=g,validation=v))
