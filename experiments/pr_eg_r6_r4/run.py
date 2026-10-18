"""Freeze, run and score an isolated comparison; resumable without duplicate calls."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_eg_r6_r4'
from experiments.pr_eg_r6_r4.corpus import cases
from experiments.pr_eg_r6_r4 import engine


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def freeze():
    if (OUT/'freeze.json').exists():verify();return
    for part in ('development','validation','holdout'):
        write(part+'.json',[c for c in cases() if c['partition']==part])
    paths=list((ROOT/'experiments/pr_eg_r6_r4').glob('*.py'))+[ROOT/'experiments/pr_eg_r6_r4/CONTRACT.md']
    paths += list(OUT.glob('development.json'))+list(OUT.glob('validation.json'))+list(OUT.glob('holdout.json'))
    paths += [ROOT/'game/semantic_correspondence.py',ROOT/'game/semantic_operations.py',ROOT/'game/unified_semantic_planning.py',ROOT/'game/dialogue_authority.py']
    write('freeze.json',dict(created_at=datetime.now(timezone.utc).isoformat(),hashes={p.relative_to(ROOT).as_posix():sha(p) for p in paths}))


def verify():
    amendments=read('adapter_correction.json')['new_hashes'] if (OUT/'adapter_correction.json').exists() else {}
    for p,h in read('freeze.json')['hashes'].items():
        if sha(ROOT/p)!=amendments.get(p,h):raise RuntimeError('Frozen input/code changed: '+p)


def scoring(case,r):
    e=case['expected'];a=r['result'];positive=a['response_class'] in {'DIRECT','PARTIAL'}
    allowed={s['id'] for s in engine.eligible(case)}
    expected_positive=e['response_class'] in {'DIRECT','PARTIAL'}
    binding_ok=a['bindings']==e['bindings']
    authorization=set(a['selected_source_ids'])<=allowed
    forbidden=any(str(v) in json.dumps(a['bindings']) for v in e['forbidden_claims'])
    # A selected source's epistemic/temporal/negative values must survive output.
    qualifier_ok=all(any(all(f[k]==q[k] for k in q) for s in engine.eligible(case) for f in s['facts']) for q in a['qualifiers'])
    if 'unstructured' in case['tags'] and positive:qualifier_ok=not any(q['epistemic']!='npc_knowledge' for q in a['qualifiers'])
    class_ok=a['response_class']==e['response_class']
    role_ok=binding_ok and (not expected_positive or bool(a['selected_source_ids']))
    success=class_ok and binding_ok and qualifier_ok and authorization and not forbidden
    if r.get('error'):cause='E03'
    elif not authorization:cause='E12'
    elif forbidden:cause='E10'
    elif not binding_ok and positive:cause='E04'
    elif e['response_class']=='DIRECT' and a['response_class']=='PARTIAL':cause='E08'
    elif not class_ok and a['response_class']=='DIRECT':cause='E09'
    elif not class_ok and a['rejections']:cause='E14'
    elif not success:cause='E07' if positive else 'E02'
    else:cause=''
    return dict(class_correct=class_ok,relevance_correct=a['relevance']==e['relevance'],
        sufficiency_correct=a['sufficiency']==e['sufficiency'],bindings_correct=binding_ok,
        roles_correct=role_ok,qualifiers_correct=qualifier_ok,authorization_correct=authorization and not forbidden,
        false_acceptance=positive and (not expected_positive or not binding_ok or not qualifier_ok),
        false_rejection=expected_positive and not positive,answer_success=success,earliest_failure=cause)


def safe_run(c,arch,queries=None,raw_plan=None):
    t=time.perf_counter()
    try:r=engine.run(c,arch,queries=queries,raw_plan=raw_plan)
    except Exception as exc:
        r=dict(case_id=c['id'],architecture=arch,partition=c['partition'],calls=int(arch!='B'),
               error=type(exc).__name__,raw='',usage={},latency_ms=(time.perf_counter()-t)*1000,
               result=engine.result(c,arch,[],queries))
    r['scores']=scoring(c,r)
    return r


def primary(workers,limit=None):
    verify();corpus=sum([read(p+'.json') for p in ('development','validation','holdout')],[])
    path=OUT/'primary.jsonl';existing=[]
    if path.exists():existing=[json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
    done={(r['case_id'],r['architecture']) for r in existing}
    todo=[(c,a) for c in corpus for a in 'ABC' if (c['id'],a) not in done]
    if limit:todo=todo[:limit]
    with path.open('a',encoding='utf-8') as out,ThreadPoolExecutor(max_workers=workers) as pool:
        pending={pool.submit(safe_run,c,a):(c,a) for c,a in todo}
        for k,f in enumerate(as_completed(pending),1):
            r=f.result();out.write(json.dumps(r,ensure_ascii=False)+'\n');out.flush()
            if k%12==0 or r.get('error'):print(json.dumps({'completed':len(done)+k,'total':len(corpus)*3,'case':r['case_id'],'arch':r['architecture'],'error':r.get('error')}),flush=True)
    verify()


def secondary(workers):
    verify();path=OUT/'secondary.jsonl';done=set()
    if path.exists():done={json.loads(l)['case_id'] for l in path.read_text(encoding='utf-8').splitlines()}
    corpus=[c for c in read('holdout.json') if c['id'].endswith('-07') and c['id'] not in done]
    def task(c):
        from game.unified_semantic_planning import _invoke_provider,authorize_information_turn
        body=engine.payload(c);body.pop('gold_question_interpretations')
        try:
            raw,usage=_invoke_provider(body);p=json.loads(raw)
            q=p.get('request_proposition');q=engine.clean_proposition(q)
            if not q:raise ValueError('invalid production interpretation')
            a=safe_run(c,'A',queries=[q],raw_plan=p)
            a.update(raw=raw,usage=usage,calls=1,prompt=body)
            world={'npcs':[dict(engine.npc(c),name='Vesper',location='yard')]}
            native=authorize_information_turn(player_text=c['question'],session={},world=world,
                scene={'scene':{'id':'yard','addressables':[{'id':'vesper','name':'Vesper','kind':'npc'}]}},proposal=p)
            variant=deepcopy(c);variant['queries']=[q]
            rows=[a,safe_run(c,'B',queries=[q]),safe_run(variant,'C',queries=[q])]
            return dict(case_id=c['id'],actual_query=q,results=rows,native_production=native)
        except Exception as exc:return dict(case_id=c['id'],error=type(exc).__name__)
    with path.open('a',encoding='utf-8') as out,ThreadPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(task,corpus):out.write(json.dumps(r,ensure_ascii=False,default=str)+'\n');out.flush();print('secondary '+r['case_id'],flush=True)
    verify()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','primary','secondary','verify']);parser.add_argument('--workers',type=int,default=6);parser.add_argument('--limit',type=int)
    args=parser.parse_args();OUT.mkdir(exist_ok=True)
    if args.action=='freeze':freeze()
    elif args.action=='verify':verify()
    elif args.action=='primary':primary(args.workers,args.limit)
    else:secondary(args.workers)
