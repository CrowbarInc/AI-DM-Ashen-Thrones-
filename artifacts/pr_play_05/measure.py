"""Local structural processing and durable observation overhead, no SDK dispatch."""
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
from types import SimpleNamespace as NS

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from game.gm import _safe_json,_extract_provider_response_text,_generation_response_diagnostic
from game import provider_budget as budget
from tests.test_pr_play_04_opening_integrity import VALID_NARRATION

text=json.dumps({'declared_claims':[],'narration':VALID_NARRATION})
response=NS(output_text=text,status='completed',id='synthetic-overhead',usage=NS(input_tokens=20,output_tokens=10,total_tokens=30))
def baseline():
    return _safe_json(text,require_structured_claims=True)
def observed():
    extracted,details=_extract_provider_response_text(response)
    parsed=_safe_json(extracted,require_structured_claims=True)
    return _generation_response_diagnostic(response,extracted,details,parsed,maximum=600,contract='structured_realization')
def timing(fn,n):
    samples=[]
    for _ in range(n):
        start=time.perf_counter_ns();fn();samples.append((time.perf_counter_ns()-start)/1e6)
    return {'iterations':n,'median_ms':statistics.median(samples),'p95_ms':sorted(samples)[int(n*.95)]}
import os
with tempfile.TemporaryDirectory(dir=ROOT/'development/tmp/pr_play_05') as tmp:
    os.environ['ASHEN_GENERATION_DIAGNOSTICS']='1'
    os.environ['ASHEN_PROVIDER_USAGE_PATH']=str(Path(tmp)/'usage.jsonl')
    record=observed()
    result={'parser_only':timing(baseline,2000),'parser_and_structural_diagnostics':timing(observed,2000),
            'durable_observation':timing(lambda:budget.record_generation_diagnostic({'stage':'provider_response',**record}),100),
            'provider_admissions':budget.snapshot()['requests'],
            'scope':'Synthetic local microbenchmark; excludes SDK, UI, gameplay latency; fsync retained.'}
    assert result['provider_admissions']==0
    (ROOT/'artifacts/pr_play_05/performance.json').write_text(json.dumps(result,indent=2))
