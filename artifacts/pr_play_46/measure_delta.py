"""Paired offline microbenchmark, with the established provider guard installed."""
import os
os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'] = '1'
os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION'] = '1'
os.environ['ASHEN_DISABLE_EXPRESSION_GENERATION'] = '1'
import sys
import json
import time
import statistics
import importlib.util
from pathlib import Path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
import pytest
from tests.helpers.live_model_guard import install_live_model_guard
from game.immutable_valid_response import validate_generated_response, run_preserve_if_valid
from game import mechanical_claims as current
out = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('old_mechanics', out/'source_before/game/mechanical_claims.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
r = {'kind': 'investigate', 'success': True, 'state_changes': {}}
text = 'Rain taps the shutters. You receive a silver key.'
def measure(fn, n=500):
    fn()
    samples=[]
    for _ in range(n):
        start=time.perf_counter_ns();fn();samples.append(time.perf_counter_ns()-start)
    return {'median_us': statistics.median(samples)/1000, 'p95_us': sorted(samples)[int(n*.95)]/1000, 'iterations': n}
def fallback():
    return run_preserve_if_valid({'player_facing_text': text, 'metadata': {}},
        resolution=r, player_text='I observe.', regenerate=None)
with pytest.MonkeyPatch.context() as guard:
    install_live_model_guard(guard)
    measurements={}
    for phase, audit in [('before',old.audit_mechanical_claims),('after',current.audit_mechanical_claims)]:
        with pytest.MonkeyPatch.context() as m:
            m.setattr(current, 'audit_mechanical_claims', audit)
            measurements[phase]={
                'audit':measure(lambda:audit(text,r)),
                'full_validation':measure(lambda:validate_generated_response(text,resolution=r)),
                'rejection_and_fallback':measure(fallback,200)}
    measurements['median_delta_us']={k:measurements['after'][k]['median_us']-measurements['before'][k]['median_us'] for k in measurements['before']}
measurements['method']='Same input rejected in both versions; sequential local wall-clock microbenchmark, not a latency guarantee. No provider calls.'
(out/'performance_delta.json').write_text(json.dumps(measurements,indent=2)+'\n')
print(json.dumps(measurements,indent=2))
