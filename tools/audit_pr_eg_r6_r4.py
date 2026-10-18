"""Read raw predecessor evidence; preserve exact records and source file hashes."""
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/pr_eg_r6_r4'


def main():
    inventory=[];examples=[];counts={}
    for cycle in ['pr_eg_r6_r2','pr_eg_r6_r2_r1','pr_eg_r6_r2_r2','pr_eg_r6_r3','pr_eg_r6_r3_r1']:
        per_cycle=[]
        for p in sorted((ROOT/'artifacts'/cycle).rglob('*.jsonl')):
            if not any(s in p.name for s in ('turn','case','trace')):continue
            inventory.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
            seen=set()
            for line_no,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
                try:r=json.loads(line)
                except ValueError:continue
                plan=r.get('plan') or r.get('normalized') or {};plan=plan if isinstance(plan,dict) else {}
                reason=plan.get('reason') or plan.get('validation_reason') or ''
                cls=plan.get('response_kind') or plan.get('response_class') or ''
                kind='unknown' if cls=='unknown' or reason=='no_relevant_source' else 'partial' if cls=='partial' else 'role' if 'role' in str(reason) else 'restricted' if cls in {'refusal','restricted'} else ''
                if not kind:continue
                key=f'{cycle}:{kind}';counts[key]=counts.get(key,0)+1
                if kind in seen:continue
                seen.add(kind)
                if sum(x['kind']==kind for x in per_cycle)>=2:continue
                # Earliest causal failures are hypotheses until request/evidence
                # has been independently inspected, never inferred from UNKNOWN alone.
                missing=bool(plan.get('request_proposition')) and not plan.get('source_propositions')
                cause='E02' if missing else 'E07' if kind=='partial' else 'E12' if kind=='restricted' else 'UNDETERMINED'
                per_cycle.append(dict(cycle=cycle,kind=kind,path=p.relative_to(ROOT).as_posix(),line=line_no,
                    earliest_causal_hypothesis=cause,certainty='triage; selected-source output alone cannot establish world evidence',raw=r))
        examples.extend(per_cycle)
    (OUT/'historical_raw_examples.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in examples),encoding='utf-8')
    (OUT/'historical_inventory.json').write_text(json.dumps(dict(files=inventory,record_counts=counts,examples=len(examples)),indent=2),encoding='utf-8')
    print(json.dumps(dict(files=len(inventory),examples=len(examples))))
    for x in examples:
        r=x['raw'];p=r.get('plan') or r.get('normalized') or {}
        print(json.dumps(dict(cycle=x['cycle'],kind=x['kind'],player=r.get('player') or r.get('utterance'),answer=(r.get('text') or '')[:160],reason=p.get('reason') or p.get('validation_reason'),source_count=len(p.get('source_propositions',[])),path=x['path'],line=x['line']),ensure_ascii=True))


if __name__=='__main__':main()
