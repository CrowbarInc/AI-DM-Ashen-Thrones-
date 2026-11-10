"""One-shot fresh developer-authored holdout, sealed before final evaluation."""
import sys,json,hashlib,copy,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def freeze():
    assert not (OUT/'frozen_holdout.json').exists()
    rows=[]
    for target in ['copper marker','river stones','worn sign','cart ruts']:
        for raw in [f'You inspect the {target}.',f'You pause to study the {target}.',
            f'You give the {target} your attention.',f'Your attention returns to the {target}.',
            f'You look more closely at the {target}.']:
            rows.append(dict(target=target,raw=raw,expected='PASS',group='frame'))
        for tail in ['The patrol fled east.','You gain a jeweled crown.','The bridge is permanently destroyed.',
                     'The guards leave their posts.','A secret tunnel opens.']:
            rows.append(dict(target=target,raw=f'You inspect the {target}. '+tail,expected='reject',group='mixed'))
    for flag in ['hidden','visible','requires','locked','reveal_requires','wrong_id','wrong_scene','failed']:
        rows.append(dict(group='provenance',flag=flag,expected='reject'))
    for fault in ['accepted','timeout','unavailable','empty','malformed','FAIL','REVIEW_REQUIRED','VALIDATION_ERROR','duplicate','inventory','persistent','hidden']:
        rows.append(dict(group='http',fault=fault,expected='published' if fault=='accepted' else 'fallback'))
    for n,row in enumerate(rows):row.update(id=f'H{n+1:02}',expected_disclosure='all current-action facts verbatim, once',expected_state='no presentation mutation; one resolver operation')
    save('frozen_holdout.json',rows);save('frozen_holdout_manifest.json',dict(cases=len(rows),sha256=sha(OUT/'frozen_holdout.json'),developer_authored=True,independent_external_validation=False))
def run():
    import pytest
    from game import integrated_investigation_narration as i,quarantined_investigation_narration as q
    from tests.test_pr_play_69_target_references import historical_hook,evaluate
    from tests.test_pr_play_68_structured_publication import execute
    manifest=json.loads((OUT/'frozen_holdout_manifest.json').read_text())
    assert sha(OUT/'frozen_holdout.json')==manifest['sha256']
    assert not (OUT/'holdout_results.json').exists()
    frozen=json.loads((OUT/'implementation_freeze.json').read_text())
    assert all(sha(ROOT/n)==v for n,v in frozen.items())
    results=[];save('holdout_results.json',results)
    for case in json.loads((OUT/'frozen_holdout.json').read_text()):
        row=dict(case=case,passed=False)
        try:
            if case['group']=='http':
                with pytest.MonkeyPatch.context() as mp:r=execute(OUT/'holdout_sessions'/case['id'],mp,fault=case['fault'])
                assert r['trace']['publication']['decision']==case['expected']
                row.update(result=r)
            else:
                hook=historical_hook()
                scene={'scene':{'visible_facts':['A copper marker stands here.'],
                    'interactables':[{'id':'prints','label':case.get('target','copper marker')}]}}
                action=f"I examine the {case.get('target','copper marker')}."
                resolution=copy.deepcopy(hook['resolution'])
                if case['group']=='provenance':
                    flag=case['flag']
                    if flag=='wrong_id':scene['scene']['interactables'][0]['id']='elsewhere'
                    elif flag=='wrong_scene':scene={'scene':{'visible_facts':[]}}
                    elif flag=='failed':resolution['success']=False
                    else:scene['scene']['interactables'][0][flag]=False if flag=='visible' else True
                    # No exact-public fallback for synthetic absent resolver targets.
                    scene['scene']['visible_facts']=[]
                hook=q.build_hook_input(resolution=resolution,scene=scene,known_clue_texts=[],player_text=action)
                audit,text=evaluate(case.get('raw','You examine the copper marker.'),hook)
                assert (audit['decision']=='PASS')==(case['expected']=='PASS')
                row.update(validation=audit,final=text,hook=hook)
            row['passed']=True
        except Exception as exc:row.update(error=repr(exc),traceback=traceback.format_exc())
        results.append(row);save('holdout_results.json',results)
    save('holdout_summary.json',dict(cases=len(results),passed=sum(r['passed'] for r in results),failed=[r['case']['id'] for r in results if not r['passed']],one_shot=True,developer_authored=True))
if __name__=='__main__':freeze() if sys.argv[-1]=='freeze' else run()
