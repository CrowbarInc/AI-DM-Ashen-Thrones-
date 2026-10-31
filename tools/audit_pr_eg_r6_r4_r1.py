"""Read-only predecessor audit and local security experiments for this cycle."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.pr_eg_r6_r4_r1 import engine as E
from experiments.pr_eg_r6_r4_r1.run import OUT,dump,sha,read,verify,families


def historical():
    inventory=[];examples=[]
    cycles=['pr_eg_r6_r2','pr_eg_r6_r2_r1','pr_eg_r6_r2_r2','pr_eg_r6_r3','pr_eg_r6_r3_r1','pr_eg_r6_r4']
    # Re-open original files referenced by the predecessor audit, do not merely
    # inherit its scorer's causal conclusions.
    selection=[json.loads(l) for l in (ROOT/'artifacts/pr_eg_r6_r4/historical_raw_examples.jsonl').read_text(encoding='utf-8').splitlines()]
    for cycle in cycles:
        base=ROOT/'artifacts'/cycle
        paths=[p for p in base.rglob('*.jsonl') if p.stat().st_size and 'test_tmp' not in p.as_posix()]
        for p in paths:
            inventory.append(dict(cycle=cycle,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
        chosen=[x for x in selection if x['cycle']==cycle][:3]
        for x in chosen:
            p=ROOT/x['path'];lines=p.read_text(encoding='utf-8').splitlines()
            raw=json.loads(lines[x['line']-1]);plan=raw.get('plan') or raw.get('normalized') or {}
            examples.append(dict(cycle=cycle,path=x['path'],line=x['line'],sha256=sha(p),raw=raw,
                observation=dict(question=raw.get('player') or raw.get('utterance'),
                    response_class=plan.get('response_kind') or plan.get('response_class'),
                    source_propositions_present=bool(plan.get('source_propositions')),
                    reason=plan.get('reason') or plan.get('validation_reason')),
                causal_status='Hypothesis only: selected-source output does not establish source availability or semantic correctness.'))
    # Current predecessor: show actual query plus source proposition and scored
    # normalization for one success and two failures, not only aggregate percentages.
    for p in (ROOT/'artifacts/pr_eg_r6_r4/primary.jsonl',ROOT/'artifacts/pr_eg_r6_r4/secondary.jsonl'):
        count=0
        for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
            r=json.loads(line)
            if p.name=='primary.jsonl' and (r.get('architecture')!='C' or r.get('scores',{}).get('answer_success')):continue
            examples.append(dict(cycle='pr_eg_r6_r4',path=p.relative_to(ROOT).as_posix(),line=n,sha256=sha(p),raw=r,
                observation='Raw contract/coverage result; gold-question primary and actual-question secondary are distinct.',
                causal_status='No independent human adjudication.'))
            count+=1
            if count==2:break
    dump(OUT/'historical_inventory.json',inventory)
    (OUT/'historical_examples.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in examples),encoding='utf-8')
    return dict(files=len(inventory),examples=len(examples),cycles=cycles)


def security():
    from tests.test_pr_eg_r6_r4_r1_alignment import fact,source
    s=source();f=fact();results=[]
    for name,field,value in [('restricted_password','disclosure','secret'),('private_knowledge','knowledge_status','unknown'),
                             ('foreign_npc','npc','other'),('foreign_conversation','context','foreign'),
                             ('historical_speech_laundering','provenance','verified_history')]:
        bad=dict(s);bad[field]=value
        payload=E.public_sources(E.eligible([bad],s['npc'],s['context']))
        results.append(dict(name=name,passed=payload==[],input_excluded=True,provider_calls=0))
    for name,changes in [('forged_source_id',dict(source_id='forged')),('fabricated_span',dict(evidence_span='invented')),
                         ('forged_authority',dict(provenance='world_fact')),('fabricated_argument',dict(roles=[dict(name='keeper',value='king',evidence='surveyor')]))]:
        bad=deepcopy(f);bad.update(changes);v=E.validate(bad,[s],'C')
        results.append(dict(name=name,passed=v['level']=='REJECTED',validation=v,provider_calls=0))
    bad=deepcopy(f);bad['roles'][0]['name']='object';bad['roles'][1]['name']='keeper'
    v=E.validate(bad,[s],'C')
    results.append(dict(name='anchored_role_swap_remains_unverified',passed=v['level']=='SOURCE_ANCHORED' and v['semantic_support']=='unestablished',validation=v,provider_calls=0))
    # Every possible provenance label remains host-owned. No provider value is
    # copied into canonical state; source-anchored is not a new authority level.
    for provenance in ('world_source','host_operation','bounded_expression','verified_history'):
        bad=deepcopy(f);bad['provenance']=provenance
        v=E.validate(bad,[s],'C')
        results.append(dict(name='authority_inheritance_'+provenance,
            passed=(v['level']=='SOURCE_ANCHORED' if provenance=='world_source' else v['level']=='REJECTED'),validation=v,provider_calls=0))
    dump(OUT/'security_results.json',dict(kind='deterministic synthetic boundary experiments; not provider qualification',
        passed=sum(x['passed'] for x in results),total=len(results),experiments=results))


def payload_audit():
    results=[]
    fs={f['family']:f for f in families()}
    for p in sorted((OUT/'calls').glob('*.json')):
        r=read(p);req=r['request'];user=json.loads(req['input'][1]['content'])
        # Primary inputs must contain no oracle fields anywhere.
        forbidden_keys={'expected','gold_diagnostic','gold_question_diagnostic','supported_claims','forbidden'}
        def keys(v):
            if isinstance(v,dict):return set(v)|set().union(*(keys(x) for x in v.values()))
            if isinstance(v,list):return set().union(*(keys(x) for x in v))
            return set()
        oracle=bool(keys(user)&forbidden_keys) if not p.name.startswith('diagnostic_') else False
        blob=json.dumps(user,ensure_ascii=False)
        # Source prose absent by full exact match, including player-supplied
        # guesses; restricted values are synthetic canaries, not credentials.
        unavailable=[s['text'] for f in fs.values() for s in f['sources'] if not E.eligible([s],f['cases'][0]['npc'],'experiment')]
        leaks=[text for text in unavailable if text in blob]
        results.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),oracle_leak=oracle,
            unavailable_source_leak=bool(leaks),provider_success=bool(r.get('parsed')),error=r.get('error')))
    dump(OUT/'payload_audit.json',dict(calls=len(results),oracle_leaks=sum(r['oracle_leak'] for r in results),
        unavailable_source_leaks=sum(r['unavailable_source_leak'] for r in results),records=results))


if __name__=='__main__':
    verify();print(historical());security();payload_audit();verify()
