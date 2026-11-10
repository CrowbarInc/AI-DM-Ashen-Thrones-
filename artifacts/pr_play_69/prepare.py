"""Preserve dirty entry state and exact historical fixture before implementation."""
import sys,json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
if __name__=='__main__':
    assert not (OUT/'baseline.json').exists()
    sources=['game/integrated_investigation_narration.py','game/quarantined_investigation_narration.py','game/api.py','game/player_http_projection.py','static/app.js','docs/NEXT_SESSION.md']
    (OUT/'entry_source').mkdir(exist_ok=True)
    for n in sources:(OUT/'entry_source'/Path(n).name).write_bytes((ROOT/n).read_bytes())
    save('baseline.json',dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),status=subprocess.check_output(['git','status','--short'],text=True),sources={n:sha(ROOT/n) for n in sources},protected={p.relative_to(ROOT).as_posix():sha(p) for r in ['data','artifacts/atgb','artifacts/pr_play_65','artifacts/pr_play_66','artifacts/pr_play_67','artifacts/pr_play_68'] for p in (ROOT/r).rglob('*') if p.is_file() and '__pycache__' not in p.parts}))
    from game import integrated_investigation_narration as i
    old=json.loads((ROOT/'artifacts/pr_play_68/live_results.json').read_text(encoding='utf-8'))['rows']
    row=old[-1];trace=row['trace'];hook=trace['hook_input']
    contract,request=i.outcome_contract(hook)
    audit,composed=i.compose_authoritative(contract,request,trace['raw_provider_text'],i.trusted_disclosure(request))
    save('historical_reproduction.json',dict(source='artifacts/pr_play_68/live_results.json',input=row['input'],hook=hook,candidate=trace['raw_provider_text'],original_trace=trace,replayed_validation=audit,replayed_composition=composed,final_response=row['body']['gm_output']['player_facing_text']))
    save('repeat_before.json',[dict(input=r['input'],trace=r['trace'],response=r['body']['gm_output']['player_facing_text']) for r in old[2:]])
    print(audit['decision'],audit.get('composition_reason'))
