"""Freeze eight additional paraphrases; never edit an exposed corpus."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.pr_eg_r6_r4.corpus import cases
from experiments.pr_eg_r6_r4.run import OUT,safe_run,verify


def main():
    verify();path=OUT/'paraphrases.json'
    if not path.exists():
        forms=[('who has custody of the {item}?','has custody of'),
               ('in whose care is the {item}?','care'),
               ('who is the custodian of the {item}?','custodian'),
               ('who has the {item} in safekeeping?','safekeeping'),
               ('who is entrusted with keeping the {item}?','keeping'),
               ('who holds the {item} for safekeeping?','holds'),
               ('who has charge of the {item}?','charge'),
               ('who is keeping the {item} safe?','keeping')]
        chosen=[]
        for i,c in enumerate(c for c in cases() if c['family']=='direct_exact'):
            c=deepcopy(c);cid=f'paraphrase_supplement-{i:02}';c.update(id=cid,partition='paraphrase_supplement',family='paraphrase_supplement',tags=['paraphrase'])
            item=c['queries'][0]['roles'][0]['value'];form,witness=forms[i]
            c['question']='Vesper, '+form.format(item=item);c['queries'][0]['predicate_evidence']=witness
            for j,s in enumerate(c['sources']):s.update(id=cid+f':s{j}',context=cid)
            chosen.append(c)
        path.write_text(json.dumps(chosen,indent=2),encoding='utf-8')
        (OUT/'paraphrase_freeze.json').write_text(json.dumps(dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),note='Separately frozen before calls; primary corpus untouched; diagnostic follow-on, not untouched core holdout. Explicit paraphrase total now sixteen.'),indent=2))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==json.loads((OUT/'paraphrase_freeze.json').read_text())['sha256']
    output=OUT/'paraphrase_results.jsonl';done=set()
    if output.exists():done={(r['case_id'],r['architecture']) for r in map(json.loads,output.read_text(encoding='utf-8').splitlines())}
    work=[(c,a) for c in json.loads(path.read_text()) for a in 'ABC' if (c['id'],a) not in done]
    with output.open('a',encoding='utf-8') as out,ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(lambda pair:safe_run(*pair),work):out.write(json.dumps(r)+'\n');out.flush();print(r['case_id']+' '+r['architecture'],flush=True)


if __name__=='__main__':main()
