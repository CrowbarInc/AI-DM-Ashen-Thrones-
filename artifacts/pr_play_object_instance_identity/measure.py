"""Small local benchmark and machine-readable identity traces; no providers."""
from pathlib import Path
import copy, json, os, statistics, sys, time
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
os.environ['ASHEN_TEST_EVIDENCE_DIR']=str(OUT)
from tests.helpers.storage_isolation import install
install(ROOT/'development/tmp/object_instance_benchmark')
from game import object_instances as obj, storage
legacy={'inventory':[{'id':'dagger','name':'Dagger','quantity':1,'usable':False,'unknown':{'keep':[1,2]}} for _ in range(100)]}
def assign(c,i=0):
    return obj.ensure_object_instance_identity(c,i,campaign_run_id='benchmark',operation_id='explicit')
first=assign(legacy); second=assign(first.character,1)
duplicate=copy.deepcopy(second.character); duplicate['inventory'][1]['instance_id']=first.instance_id
traces={'legacy':obj.inspect_object_identity(legacy,0,campaign_run_id='benchmark').status,
    'first':vars(first),'repeat':vars(assign(first.character)),
    'second_instance_id':second.instance_id,'duplicate':vars(assign(duplicate,2)),
    'input_unchanged':all('instance_id' not in row for row in legacy['inventory'])}
(OUT/'identity_traces.json').write_text(json.dumps(traces,indent=2))
def measure(fn,count=30):
    samples=[]
    for _ in range(count):
        start=time.perf_counter(); fn(); samples.append((time.perf_counter()-start)*1000)
    return {'median_ms':statistics.median(samples),'min_ms':min(samples),'max_ms':max(samples),'samples':count}
measurements={'inventory_rows':100,'assignment':measure(lambda:assign(legacy)),
    'repeat_validation':measure(lambda:assign(first.character)),
    'save_legacy':measure(lambda:storage.save_character(legacy)),
    'save_identity':measure(lambda:storage.save_character(first.character)),
    'legacy_bytes':len(json.dumps(legacy,indent=2).encode()),
    'identity_bytes':len(json.dumps(first.character,indent=2).encode()),'live_provider_calls':0}
(OUT/'performance.json').write_text(json.dumps(measurements,indent=2))
print(json.dumps(measurements,indent=2))
