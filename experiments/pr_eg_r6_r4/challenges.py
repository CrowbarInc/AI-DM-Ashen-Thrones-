"""Separately frozen coverage probes; not used to tune the core experiment."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from experiments.pr_eg_r6_r4.corpus import proposition as prop
from experiments.pr_eg_r6_r4.run import OUT, safe_run, verify


def challenges():
    cases=[]
    def add(cid,question,q,text,f,label,bindings,tags,extras=()):
        source=dict(id=cid+':s0',context=cid,npc='vesper',provenance='world_source',disclosure='public',
                    knowledge_status='known',epistemic=f['epistemic'],text=text,facts=[f])
        sources=[source]
        for i in extras:
            sources.insert(0,dict(source,id=cid+f':d{i}',text=f'The porter polishes token {i}.',facts=[prop('polish',{'agent':'porter','object':f'token {i}'},evidence='polishes')]))
        cases.append(dict(id=cid,partition='supplemental',family=cid,question='Vesper, '+question,queries=[q],
            sources=sources,npc='vesper',ambiguity=False,tags=tags,expected=dict(response_class=label,
            relevance=True,sufficiency={'DIRECT':'complete','PARTIAL':'partial'}.get(label,'none'),bindings=bindings,forbidden_claims=[])))
    pairs=[('loan','lender','borrower','Who lent the jade cup to Brin?','Cala lent the jade cup to Brin.','lent'),
           ('own','owner','borrower','Who owns the cup Brin borrowed?','Cala owns the cup Brin borrowed.','owns'),
           ('guard','guard','protected_party','Who guards Brin at the lodge?','Cala guards Brin at the lodge.','guards'),
           ('buy','buyer','seller','Who bought the lamp from Brin?','Cala bought the lamp from Brin.','bought'),
           ('owe','debtor','creditor','Who owes Brin six coins?','Cala owes Brin six coins.','owes'),
           ('appoint','appointer','appointee','Who appointed Brin to the guild?','Cala appointed Brin to the guild.','appointed'),
           ('precede','predecessor','successor','Who preceded Brin in the chair?','Cala preceded Brin in the chair.','preceded'),
           ('vouch','voucher','beneficiary','Who vouches for Brin?','Cala vouches for Brin.','vouches')]
    for pred,r1,r2,question,text,verb in pairs:
        f=prop(pred,{r1:'Cala',r2:'Brin'},evidence=verb)
        q=prop(pred,{r2:'Brin'},r1,evidence=verb if verb in question else pred)
        # Exact question witnesses are explicitly authored, independent of outputs.
        if pred=='loan':q['predicate_evidence']='lent'
        if pred=='own':q['predicate_evidence']='owns'
        add(pred+'_direct',question,q,text,f,'DIRECT',{r1:'Cala'},['multi_role','institutional'])
        reverse_questions={
            'loan':('Who did Brin lend the jade cup to?','lend'),
            'own':('Who borrowed the cup Brin owns?','owns'),
            'guard':('Who does Brin guard at the lodge?','guard'),
            'buy':('Who did Brin buy the lamp from?','buy'),
            'owe':('Who does Brin owe six coins to?','owe'),
            'appoint':('Who did Brin appoint to the guild?','appoint'),
            'precede':('Who did Brin precede in the chair?','precede'),
            'vouch':('Who does Brin vouch for?','vouch')}
        rq,rv=reverse_questions[pred]
        reverse=prop(pred,{r1:'Brin'},r2,evidence=rv)
        add(pred+'_reverse',rq,reverse,text,f,'RELATED_NONANSWER',{},['multi_role','role_reversal'])
    # Use fresh names and a relation absent from the core corpus.
    q=prop('illuminate',{'object':'vault'},'agent',evidence='illuminates')
    f=prop('illuminate',{'object':'vault','agent':'phosphor moss'},evidence='illuminates')
    add('spatial_match','what illuminates the vault below the stair?',q|{'spatial':'below the stair'},
        'Phosphor moss illuminates the vault below the stair.',f|{'spatial':'below the stair'},'DIRECT',{'agent':'phosphor moss'},['spatial','open_world'])
    add('spatial_mismatch','what illuminates the vault above the stair?',q|{'spatial':'above the stair'},
        'Phosphor moss illuminates the vault below the stair.',f|{'spatial':'below the stair'},'RELATED_NONANSWER',{},['spatial'])
    for kind,text in [('possibility','Phosphor moss may illuminate the vault.'),
                      ('conditional','If watered, phosphor moss illuminates the vault.'),
                      ('approximation','Approximately ten lanterns illuminate the vault.'),
                      ('uncertainty','Possibly phosphor moss illuminates the vault.')]:
        value='ten lanterns' if kind=='approximation' else 'phosphor moss'
        fact=prop('illuminate',{'object':'vault','agent':value},evidence='illuminate' if kind in {'possibility','approximation'} else 'illuminates',epistemic=kind)
        add('qualifier_'+kind,'what illuminates the vault?',q,text,fact,'PARTIAL',{'agent':value},['qualifier',kind])
    nf=f|{'negated':True}
    add('negative_answer','what does not illuminate the vault?',q|{'negated':True,'predicate_evidence':'illuminate'},
        'Phosphor moss does not illuminate the vault.',nf|{'predicate_evidence':'illuminate'},'DIRECT',{'agent':'phosphor moss'},['negation'])
    for n in (1,4,12,32):
        add(f'scaling_{n:02}','what illuminates the vault?',q,'Phosphor moss illuminates the vault.',f,'DIRECT',{'agent':'phosphor moss'},['scaling'],range(n-1))
    return cases


def main():
    verify();path=OUT/'supplemental.json'
    if not path.exists():
        path.write_text(json.dumps(challenges(),indent=2),encoding='utf-8')
        (OUT/'supplemental_freeze.json').write_text(json.dumps(dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            note='Frozen separately before supplemental calls; no primary labels or adapters changed. Secondary diagnostic coverage, excluded from core decision metrics.'),indent=2))
    frozen=json.loads((OUT/'supplemental_freeze.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==frozen['sha256']
    output=OUT/'supplemental_results.jsonl';done=set()
    if output.exists():done={(r['case_id'],r['architecture']) for r in map(json.loads,output.read_text(encoding='utf-8').splitlines())}
    work=[(c,a) for c in json.loads(path.read_text()) for a in 'ABC' if (c['id'],a) not in done]
    with output.open('a',encoding='utf-8') as out,ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(lambda pair:safe_run(*pair),work):
            out.write(json.dumps(r,ensure_ascii=False)+'\n');out.flush()
            print(r['case_id']+' '+r['architecture'],flush=True)


if __name__=='__main__':main()
