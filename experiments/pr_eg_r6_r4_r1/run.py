"""Immutable-input, resumable real-provider experiment. All writes are artifacts."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from experiments.pr_eg_r6_r4_r1 import engine as E
from experiments.pr_eg_r6_r4_r1.corpus import build
OUT=ROOT/'artifacts/pr_eg_r6_r4_r1'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def protected():
    return {p.relative_to(ROOT).as_posix():sha(p) for folder in ('game','data') for p in (ROOT/folder).rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}


def freeze():
    OUT.mkdir(exist_ok=True)
    if (OUT/'freeze.json').exists(): verify(); return
    for folder in ('calls','extractions','results','diagnostic'):(OUT/folder).mkdir(exist_ok=True)
    corpus=build()
    for part in ('development','validation','holdout'):
        dump(OUT/(part+'.json'),[f for f in corpus if f['partition']==part])
    from game.config import DEFAULT_MODEL_NAME
    dump(OUT/'baseline.json',dict(commit=git('rev-parse','HEAD'),branch=git('branch','--show-current'),
        log=git('log','-4','--oneline'),model=DEFAULT_MODEL_NAME,temperature=0,max_output_tokens=1800,
        retries=0,production_hashes=protected(),started_at=datetime.now(timezone.utc).isoformat()))
    (OUT/'baseline_status.txt').write_text(git('status','--short'),encoding='utf-8')
    paths=list((ROOT/'experiments/pr_eg_r6_r4_r1').glob('*.py'))+[ROOT/'experiments/pr_eg_r6_r4_r1/CONTRACT.md']
    paths += [OUT/(x+'.json') for x in ('development','validation','holdout')]
    paths += [ROOT/p for p in ('game/semantic_correspondence.py','game/semantic_operations.py','game/unified_semantic_planning.py','game/dialogue_authority.py')]
    dump(OUT/'freeze.json',dict(created_at=datetime.now(timezone.utc).isoformat(),hashes={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
        cases=sum(len(f['cases']) for f in corpus),families=len(corpus),policy='No amendments or tuning after freeze.'))
    dump(OUT/'adjudication_packet.json',dict(status='pending independent human review',
        instructions='Review source authority, entailment, role direction, answer class, allowed values and qualifiers. Record disagreement separately; do not edit frozen labels.',
        cases=[dict(family=f['family'],category=f['category'],sources=f['sources'],case=f['cases'][0],reviewer=None,decision=None) for f in corpus]))
    print('Frozen',sum(len(f['cases']) for f in corpus),'cases,',len(corpus),'families',flush=True)


def verify():
    for p,h in read(OUT/'freeze.json')['hashes'].items():
        if sha(ROOT/p)!=h: raise RuntimeError('Frozen input changed: '+p)
    if protected()!=read(OUT/'baseline.json')['production_hashes']: raise RuntimeError('Production state/code changed')


def families(): return sum([read(OUT/(p+'.json')) for p in ('development','validation','holdout')],[])


def extract(f,arch):
    dest=OUT/'extractions'/f'{f["family"]}_{arch}.json'
    if dest.exists(): return read(dest)
    allowed=E.eligible(f['sources'],f['cases'][0]['npc'],'experiment')
    if allowed:
        call=E.invoke(E.EXTRACT_PROMPT,dict(sources=E.public_sources(allowed)),E.EXTRACT_SCHEMA,'source_extract_v1',OUT/'calls'/f'extract_{f["family"]}_{arch}.json')
        records=E.validate_extraction(call['parsed'],allowed,arch) if call['parsed'] else []
    else:call=None;records=[]
    record=dict(family=f['family'],architecture=arch,source_ids=[s['id'] for s in allowed],records=records,
        provider_call=bool(allowed),error=call.get('error') if call else None,semantic_support='unestablished')
    dump(dest,record)
    return record


def history(case):
    # Same inert visible context across all arms. Never a fact or authority source.
    if int(case['id'][-1])%2==0:return []
    return [dict(speaker='player',player='We discuss travel plans, weather, meals and lodging. '*30,
                 delivered='No factual claim about the present question is established. '*20,relationship='') for _ in range(4)]


def run_case(f,case,arch,diagnostic=False):
    folder='diagnostic' if diagnostic else 'results'
    dest=OUT/folder/f'{case["id"]}_{arch}.json'
    if dest.exists(): return read(dest)
    allowed=E.eligible(f['sources'],case['npc'],case['context'])
    facts=[];extraction_hash=None
    if arch=='A':
        from game.unified_semantic_planning import _proposal_schema
        body=E.baseline_body(case,allowed,history(case));prompt=E.baseline_prompt();schema=_proposal_schema()
        if diagnostic:body['gold_question_diagnostic']=case['gold_diagnostic']
    else:
        ext=extract(f,arch)
        extraction_hash=sha(OUT/'extractions'/f'{f["family"]}_{arch}.json')
        facts=[r['fact'] for r in ext['records'] if r['validation']['level']!='REJECTED']
        body=dict(question=case['question'],npc=case['npc'],facts=facts,recent_dialogue=history(case))
        if diagnostic:body['gold_question_diagnostic']=case['gold_diagnostic']
        prompt=E.ALIGN_PROMPT;schema=E.ANSWER_SCHEMA
    call=E.invoke(prompt,body,schema,'baseline_plan_v1' if arch=='A' else 'alignment_v1',OUT/'calls'/f'{folder}_{case["id"]}_{arch}.json')
    if call.get('parsed'):
        answer=E.baseline_result(case,allowed,call['parsed']) if arch=='A' else call['parsed']
    else:
        answer=dict(response_class='UNKNOWN',values=[],qualifiers=[],selected_source_ids=[],selected_fact_ids=[],answered_arguments=[],missing_arguments=[],conflict=False,reason='provider_failure')
    gate=E.candidate_gate(answer,facts,allowed) if arch!='A' else dict(delivery_authorized=False,canonical=False,candidate_eligible=None,reasons=['baseline_diagnostic_only'])
    r=dict(case_id=case['id'],family=f['family'],partition=case['partition'],architecture=arch,
        diagnostic=diagnostic,context='long' if history(case) else 'short',extraction_hash=extraction_hash,
        answer=answer,gate=gate,scores=E.score(case,answer),provider_error=call.get('error'))
    dump(dest,r)
    return r


def run(workers,part=None,diagnostic=False):
    verify();fs=[f for f in families() if not part or f['partition']==part]
    if not diagnostic:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for r in pool.map(lambda pair:extract(*pair),[(f,a) for f in fs for a in 'BC']):
                print('extraction',r['family'],r['architecture'],r['error'],flush=True)
    todo=[(f,c,a,diagnostic) for f in fs for c in (f['cases'][:1] if diagnostic else f['cases']) for a in 'ABC']
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(run_case,*args) for args in todo]
        for n,future in enumerate(as_completed(futures),1):
            r=future.result()
            if n%15==0 or r['provider_error']:print(n,'/',len(todo),r['case_id'],r['architecture'],r['provider_error'],flush=True)
    verify()
    dump(OUT/'production_integrity.json',dict(unchanged=True,checked_at=datetime.now(timezone.utc).isoformat(),paths=len(protected())))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','verify','run','diagnostic'])
    parser.add_argument('--workers',type=int,default=8);parser.add_argument('--partition',choices=['development','validation','holdout'])
    args=parser.parse_args()
    if args.action=='freeze':freeze()
    elif args.action=='verify':verify();print('Frozen hashes and production unchanged')
    else:run(args.workers,args.partition,args.action=='diagnostic')
