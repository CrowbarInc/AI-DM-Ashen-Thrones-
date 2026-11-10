"""Saved exact replay and single-execution frozen holdout, after implementation freeze."""
import copy, hashlib, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
os.environ[q.PUBLICATION_ENV]='1'
sources=['game/integrated_investigation_narration.py','game/quarantined_investigation_narration.py']
if '--holdout' in sys.argv:
    assert not (OUT/'holdout_results.json').exists(),'One-shot already executed'
    p=OUT/'frozen_holdout.json';m=json.loads((OUT/'frozen_holdout_manifest.json').read_text())
    assert hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
    save('implementation_freeze.json',{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sources})
    os.environ[i.DISCLOSURE_ENV]='1';rows=[]
    for case in json.loads(p.read_text()):
        h=copy.deepcopy(case['hook']);before=copy.deepcopy(h)
        row=i.run_integrated_hook(h,generator=q._Replay(case['candidate'],case['fault']))
        c,r=i.outcome_contract(h);v=i.validate_integrated(c,r,row['assembled'])
        pub='fallback' if row['used_fallback'] else 'ai'
        rows.append(dict(case,result=row,final_validation=v,state_unchanged=h==before,
            actual_publication=pub,matches=pub==case['expected_publication'] and v['decision']=='PASS' and h==before))
    result=dict(cases=len(rows),matched=sum(r['matches'] for r in rows),executions=1,
        critical_false_acceptances=[r['id'] for r in rows if r['group'] in ('unauthorized','contradiction') and r['actual_publication']=='ai'],
        false_rejections=[r['id'] for r in rows if r['expected_publication']=='ai' and r['actual_publication']!='ai'],
        mandatory_omissions=[r['id'] for r in rows if r['final_validation']['coverage']['decision']!='PASS'],
        state_integrity_failures=[r['id'] for r in rows if not r['state_unchanged']],rows=rows)
    save('holdout_results.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
else:
    original_path=ROOT/'artifacts/pr_play_64/quarantine_evidence/pr_play_64_live-001.json'
    original=json.loads(original_path.read_text(encoding='utf-8'))
    text=original['raw_provider_text']
    assert text=='You study the notice board carefully and discover that the missing patrol was last seen taking the northwest mud track past the crates.'
    h=original['hook_input'];rows={}
    for mode in ['legacy','authoritative']:
        os.environ[i.DISCLOSURE_ENV]='1' if mode=='authoritative' else ''
        row=i.run_integrated_hook(h,generator=q._Replay(text,''));rows[mode]=row
    save('exact_pr_play_64_replay.json',dict(candidate=text,hook=h,state_before=h,state_after=h,results=rows,
        original_source=original_path.relative_to(ROOT).as_posix(),original_sha256=hashlib.sha256(original_path.read_bytes()).hexdigest()))
    print({k:r['diagnostic'] for k,r in rows.items()})
