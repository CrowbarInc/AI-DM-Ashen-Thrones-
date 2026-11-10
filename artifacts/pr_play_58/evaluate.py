"""Local evaluation; holdout runs once only after source hashes are frozen."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_play_58'
from game import integrated_investigation_narration as integrated
from game.anchored_investigation_narration import AnchoredInvestigation, DiscoveryAnchor
from game.offline_investigation_projection import AuthorizedInvestigation
from tests.pr_play_58_development import cases

SOURCES=['game/integrated_investigation_narration.py','game/mandatory_outcome_coverage.py','game/consequential_narration_validation.py']

def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))

def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def hashes():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}

def contract_for(request):
    # Rehydrate the preserved trusted authority snapshot, never candidate text.
    facts=request['must_communicate']
    view=AuthorizedInvestigation(request['resolved_outcome']['status'],request['resolved_outcome']['success'],None,
        tuple(f['text'] for f in facts if f['source']=='resolved_action'),
        tuple(request['may_reference']['continuity']),tuple(request['may_reference']['visible_scene']),'')
    return AnchoredInvestigation(view,tuple(DiscoveryAnchor(i,f['source'],f['status'],f['text']) for i,f in enumerate(facts)))

def evaluate(case, contract, request):
    start=time.perf_counter()
    coverage=integrated.mandatory_coverage(case['text'],request)
    coverage_ms=(time.perf_counter()-start)*1000
    start=time.perf_counter()
    result=integrated.validate_integrated(contract,request,case['text'])
    elapsed=(time.perf_counter()-start)*1000
    return {**case,'request':request,'actual':result['decision'],'validation':result,
            'coverage_ms':coverage_ms,'combined_ms':elapsed}

def score(rows):
    groups={}
    for g in sorted({r['group'] for r in rows}):
        selected=[r for r in rows if r['group']==g]
        groups[g]={'total':len(selected),'pass':sum(r['actual']=='PASS' for r in selected),
                   'fail':sum(r['actual']=='FAIL' for r in selected),
                   'review':sum(r['actual']=='REVIEW_REQUIRED' for r in selected),
                   'blocked':sum(r['actual']!='PASS' for r in selected),
                   'exact_expected':sum(r['actual']==r['expected'] for r in selected)}
    false_accept=[r['id'] for r in rows if r['group'] in ('missing','contradictory','expansion') and r['actual']=='PASS']
    false_reject=[r['id'] for r in rows if r['group']=='legitimate' and r['actual']!='PASS']
    return {'total':len(rows),'groups':groups,'critical_false_acceptance_ids':false_accept,
        'false_rejection_ids':false_reject,'review_required':sum(r['actual']=='REVIEW_REQUIRED' for r in rows),
        'validation_errors':sum(r['actual']=='VALIDATION_ERROR' for r in rows),
        'confusion':dict(Counter(r['expected']+'->'+r['actual'] for r in rows)),
        'latency':{k:{'average_ms':statistics.fmean(r[k] for r in rows),'maximum_ms':max(r[k] for r in rows)} for k in ('coverage_ms','combined_ms')}}

def development():
    rows=[]
    for c in cases():
        contract,request=integrated.outcome_contract(c['hook'])
        rows.append(evaluate(c,contract,request))
    write('development_corpus.json',cases())
    write('development_results.json',{'summary':score(rows),'rows':rows})
    spec=importlib.util.spec_from_file_location('previous_coverage',OUT/'previous_coverage.py')
    previous=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    def load_entry(name, filename):
        spec=importlib.util.spec_from_file_location(name,OUT/filename)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        spec.loader.exec_module(module)
        return module
    previous_semantic=load_entry('pr58_entry_semantic','consequential_before.py')
    previous_integrated=load_entry('pr58_entry_integrated','integrated_before.py')
    previous_integrated.semantic=previous_semantic
    fixed=[]
    for c in read('fixed_samples.json'):
        result=evaluate(c,contract_for(c['request']),c['request'])
        result['previous_coverage_reexecuted']=previous.mandatory_coverage(c['text'],c['request'])
        result['previous_pipeline_reexecuted']=previous_integrated.validate_integrated(contract_for(c['request']),c['request'],c['text'])
        fixed.append(result)
    write('fixed_results.json',fixed)
    print(json.dumps({'development':score(rows),'fixed':[(r['id'],r['previous_coverage_reexecuted']['decision'],r['validation']['coverage']['decision'],r['actual']) for r in fixed]},indent=2))

def holdout():
    assert not (OUT/'holdout_results.json').exists(), 'Holdout already evaluated; no rerun allowed'
    assert read('implementation_frozen.json')['hashes']==hashes(), 'Implementation changed after freeze'
    manifest=read('holdout_manifest.json')
    assert hashlib.sha256((OUT/'holdout.json').read_bytes()).hexdigest()==manifest['sha256']
    corpus=read('holdout.json')
    rows=[]
    # A durable start marker prevents reruns even after an interrupted evaluation.
    with (OUT/'holdout_started.json').open('x',encoding='utf-8') as f:
        json.dump({'implementation':hashes(),'manifest':manifest},f,indent=2)
    for c in corpus['cases']:
        request=corpus['authorities'][c['authority']]
        rows.append(evaluate(c,contract_for(request),request))
    result={'summary':score(rows),'rows':rows,'manifest':manifest,'evaluation_passes':1}
    write('holdout_results.json',result)
    print(json.dumps(result['summary'],indent=2))

if __name__=='__main__':
    if sys.argv[1]=='development': development()
    elif sys.argv[1]=='freeze': write('implementation_frozen.json',{'hashes':hashes()})
    elif sys.argv[1]=='holdout': holdout()
