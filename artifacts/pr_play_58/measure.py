"""Warm local latency on fixed samples only. Never reruns holdout."""
import importlib.util
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from evaluate import contract_for, read, write, integrated, hashes

assert hashes()==read('implementation_frozen.json')['hashes']
samples=read('fixed_samples.json')
prepared=[(r,contract_for(r['request'])) for r in samples]
for r,c in prepared:
    integrated.validate_integrated(c,r['request'],r['text'])
def run(operation):
    times=[]
    for _ in range(100):
        for r,c in prepared:
            start=time.perf_counter()
            operation(r,c)
            times.append((time.perf_counter()-start)*1000)
    return {'count':len(times),'average_ms':statistics.fmean(times),'maximum_ms':max(times),'median_ms':statistics.median(times)}
spec=importlib.util.spec_from_file_location('pr58_previous',ROOT/'artifacts/pr_play_58/previous_coverage.py')
previous=importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
result={'previous_coverage':run(lambda r,c:previous.mandatory_coverage(r['text'],r['request'])),
        'updated_coverage':run(lambda r,c:integrated.mandatory_coverage(r['text'],r['request'])),
        'combined':run(lambda r,c:integrated.validate_integrated(c,r['request'],r['text'])),
        'provider_requests':0,'provider_tokens':0,'method':'800 warmed invocations per timing series, fixed samples only; wall clock, no tracemalloc during latency.'}
peaks={}
for name,operation in [('previous',previous.mandatory_coverage),('updated',integrated.mandatory_coverage)]:
    tracemalloc.start()
    for r,c in prepared: operation(r['text'],r['request'])
    current,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peaks[name]={'current_bytes':current,'peak_bytes':peak}
result['memory']=peaks
result['memory']['scope']='Sequential eight-sample coverage allocation peaks; not process RSS or persistent-state overhead.'
write('performance.json',result)
print(json.dumps(result,indent=2))
