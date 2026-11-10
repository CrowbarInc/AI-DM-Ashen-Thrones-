"""One-shot evaluation of the pre-implementation developer-authored holdout."""
import sys,json,hashlib,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
import pytest
from tests.test_pr_play_68_structured_publication import execute,PRINT_CLUE,NOTICE_CLUE
from game.player_http_projection import project_player_response
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
if __name__=='__main__':
    assert not (OUT/'holdout_results.json').exists(),'Holdout must run only once'
    cases=json.loads((OUT/'frozen_holdout.json').read_text());manifest=json.loads((OUT/'frozen_holdout_manifest.json').read_text())
    assert hashlib.sha256((OUT/'frozen_holdout.json').read_bytes()).hexdigest()==manifest['sha256']
    rows=[];save('holdout_results.json',rows)
    for case in cases:
        row={'case':case,'pass':False}
        try:
            group=case['group'];value=case['input'];fault='accepted';raw=None;scene=case['scene']
            if group=='projection':
                sources={'session':{'session':{'gm_notes':['HOLDOUT_SECRET']}},'world':{'world':{'gm_only':{'text':'HOLDOUT_SECRET'}}},'scene':{'scene':{'scene':{'private_notes':'HOLDOUT_SECRET'}}},'unknown':{'new_public_fact':{'text':'HOLDOUT_SECRET'}},'nested':{'character':{'hp':{'text':'HOLDOUT_SECRET'}}}}
                source=sources[value];result=project_player_response(source)
                assert 'HOLDOUT_SECRET' not in json.dumps(result)
                row.update(pass_projection=True,result=result);row['pass']=True
            else:
                if group=='structured':fault=value
                if group=='equivalence':
                    fault=next((v for v in ['empty','timeout','duplicate'] if value.endswith(v)),'rejected' if value.endswith('unsafe') else 'accepted')
                if group in {'safe','unsafe'}:raw=value
                if group=='duplicate':
                    raw={'exact':PRINT_CLUE,'expanded':PRINT_CLUE+' You acquire a silver key.','contradicted':'Three clear prints lead southeast.','historical':NOTICE_CLUE,'atmospheric':'You pause to study the weathered milestone.'}[value]
                outputs=[]
                for path in (['structured','chat'] if group=='equivalence' else ['structured']):
                    with pytest.MonkeyPatch.context() as mp:
                        r=execute(OUT/'holdout_sessions'/case['id']/path,mp,fault=fault,path=path,scene=scene,raw=raw)
                    decision=r['trace']['publication']['decision']
                    outputs.append(r);assert decision==case['expected_optional'],(decision,case['expected_optional'])
                if len(outputs)==2:
                    assert outputs[0]['body']['journal']['discovered_clues']==outputs[1]['body']['journal']['discovered_clues']
                row.update(outputs=outputs);row['pass']=True
        except Exception as exc:row.update(error=repr(exc),traceback=traceback.format_exc())
        rows.append(row);save('holdout_results.json',rows)
    save('holdout_summary.json',dict(cases=len(rows),passed=sum(r['pass'] for r in rows),failed=[r['case']['id'] for r in rows if not r['pass']],developer_authored=True,independent_external_validation=False,one_shot=True))
