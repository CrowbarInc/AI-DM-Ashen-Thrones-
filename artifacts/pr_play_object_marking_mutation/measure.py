"""Small deterministic measurements, with provider and production-write guards."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import statistics
import sys
import time
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ['ASHEN_TEST_EVIDENCE_DIR'] = str(OUT)
from tests.helpers.storage_isolation import install
install(ROOT/'development/tmp/marking_measure')
from game import storage, object_marking
from game.object_instances import ensure_object_instance_identity, inspect_object_identity
from tests.test_object_marking import request
c = {'id':'hero', 'inventory':[{'id':'p','name':'Paper','quantity':1,'usable':False} for _ in range(20)]}
for i in range(20): c = ensure_object_instance_identity(c,i,campaign_run_id='identity-test-campaign',operation_id='measure').character
req = request(c)
def measure(fn, count):
    samples=[]
    for _ in range(count):
        start=time.perf_counter_ns(); fn(); samples.append((time.perf_counter_ns()-start)/1000)
    return {'samples':count,'median_us':statistics.median(samples),'max_us':max(samples)}
result={
 'identity_lookup':measure(lambda:inspect_object_identity(c,0,campaign_run_id='identity-test-campaign'),100),
 'validation_and_staging':measure(lambda:object_marking.prepare_marking(c,req),100),
 'atomic_character_save':measure(lambda:storage.save_character(c),30),
 'fixture_inventory_size':20, 'live_provider_calls':0,'additional_model_calls':0,'prompt_expansion':0,
}
proposal=object_marking.prepare_marking(c,req)
receipt=proposal['character']['object_marking_receipts']['entries'][req['request_id']]
result['receipt_compact_bytes']=len(json.dumps(receipt,separators=(',',':')).encode())
result['first_operation_character_growth_bytes']=len(json.dumps(proposal['character']).encode())-len(json.dumps(c).encode())
result['directory_sync_supported']=storage._sync_directory(storage.DATA_DIR)
(OUT/'performance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
