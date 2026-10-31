"""Offline gold-question control against saved source interpretations.

No provider call. Use this entry point, not the frozen general runner's diagnostic
network mode. Only frozen question representations enter this local control.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.pr_eg_r6_r4_r1.run import verify,families,OUT,dump,read
from experiments.pr_eg_r6_r4_r1 import engine as E


def main():
    verify();results=[]
    for f in families():
        c=f['cases'][0];allowed=E.eligible(f['sources'],c['npc'],c['context'])
        if len(allowed)!=len(f['sources']):continue
        q=c['gold_diagnostic'];qr=q['known_roles'];requested=q['requested_roles']
        for arch in 'ABC':
            if arch=='A':
                raw=read(OUT/'calls'/f'results_{c["id"]}_A.json').get('parsed') or {}
                props=[(x['source_id'],E.clean_proposition(x['proposition'])) for x in raw.get('source_propositions',[])]
                facts=[dict(source_id=sid,relationship=p['predicate'],roles=[dict(name=r['name'],value=r['value']) for r in p['roles']],
                            qualifiers=[p[k] for k in ('temporal','spatial') if p[k]]) for sid,p in props if p]
            else:
                facts=[x['fact'] for x in read(OUT/'extractions'/f'{f["family"]}_{arch}.json')['records'] if x['validation']['level']!='REJECTED']
            values=[];qualifiers=[];ids=[];related=False
            for fact in facts:
                roles={r['name']:E.normalize(r['value']) for r in fact['roles']}
                related|=bool(set(roles.values()) & {E.normalize(v) for v in qr.values()})
                if fact['relationship']!=q['relationship']:continue
                if any(roles.get(k)!=E.normalize(v) for k,v in qr.items()):continue
                vals=[r['value'] for r in fact['roles'] if r['name'] in requested]
                if vals:values.extend(vals);qualifiers.extend(fact['qualifiers']);ids.append(fact['source_id'])
            answer=dict(response_class='DIRECT' if values else 'RELATED_NONANSWER' if related else 'UNKNOWN',
                values=list(dict.fromkeys(values)),qualifiers=list(dict.fromkeys(qualifiers)),selected_source_ids=ids)
            results.append(dict(case_id=c['id'],architecture=arch,question_representation=q,answer=answer,
                scores=E.score(c,answer),provider_calls=0,
                limitation='Exact open-relation and named-role unification; no provider paraphrase oracle.'))
    dump(OUT/'gold_diagnostic.json',dict(mode='offline frozen gold-question control',cases=len(results)//3,
        provider_calls=0,network_diagnostic='Not executed: automatic approval review rejected the additional gold metadata payload.',results=results))
    verify();print('Offline diagnostic:',len(results),'arm-cases; no new provider calls')


if __name__=='__main__':main()
