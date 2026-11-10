"""Exact historical after-repair replay with publication input/output and measured stages."""
import sys,time,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_66 import harness as h
from game import api
from game import integrated_investigation_narration as i,quarantined_investigation_narration as q
from starlette.responses import JSONResponse
h.seed('exact_after',True);h.candidate(h.historical()['full_trace']['raw_provider_text']);timings={};selection=[]
def timed(owner,name,label):
    original=getattr(owner,name)
    def call(*a,**k):
        start=time.perf_counter()
        try:return original(*a,**k)
        finally:timings.setdefault(label,[]).append((time.perf_counter()-start)*1000)
    setattr(owner,name,call)
for owner,name,label in [(api,'_resolve_engine_noncombat_seam','deterministic_resolution_ms'),(i,'trusted_disclosure','trusted_render_ms'),(i,'compose_authoritative','validation_composition_ms'),(q,'prepare_authoritative_publication','publication_prepare_ms'),(q,'verify_authoritative_publication','publication_verify_ms'),(JSONResponse,'render','http_serialization_ms')]:timed(owner,name,label)
original=api._publish_experimental_integrated_narration
def publication(*a,**k):
    inputs=[copy.deepcopy(t) for t in (a[0],a[1],a[2].get('gm_output')) if isinstance(t,dict)]
    start=time.perf_counter()
    try:return original(*a,**k)
    finally:selection.append(dict(input=inputs,output=[copy.deepcopy(t) for t in (a[0],a[1],a[2].get('gm_output')) if isinstance(t,dict)],selection_ms=(time.perf_counter()-start)*1000))
api._publish_experimental_integrated_narration=publication
row=h.post(h.historical()['input']);assert h.historical()['full_trace']['trusted_disclosure'] in row['facing']
h.save('historical_after.json',dict(result=row,publication_helper=selection,timings=timings,provider_latency_ms=0,provider_execution='saved candidate, no request',timing_scope='Nested stage measurements; do not sum as exclusive phases.'))
print('Historical after',row['facing'],timings)
