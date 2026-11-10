"""One-shot developer-authored HTTP publication holdout; do not tune against results."""
import sys,copy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_66 import harness as h
from game import api,storage
from game import quarantined_investigation_narration as q
from fastapi.testclient import TestClient
OUT=h.OUT

def authority(row):
    s=row['state_after']['session']
    return dict(character=row['state_after']['character'],world=row['state_after']['world'],combat=row['state_after']['combat'],
        location=s.get('active_scene_id'),overlays=s.get('runtime_scene_overlays'),runtime=s.get('scene_runtime'),visited=s.get('visited_scene_ids'))

if __name__=='__main__':
    assert not (OUT/'holdout_results.json').exists(),'Frozen holdout executes once'
    manifest=json.loads((OUT/'frozen_holdout_manifest.json').read_text());assert h.sha(OUT/'frozen_holdout.json')==manifest['sha256']
    h.save('implementation_freeze.json',dict(sources={n:h.sha(ROOT/n) for n in ['game/api.py','game/quarantined_investigation_narration.py','game/integrated_investigation_narration.py']},holdout_sha256=manifest['sha256']))
    rows=[];original_publish=api._publish_experimental_integrated_narration;original_resolve=api._resolve_engine_noncombat_seam;original_load=api.load_campaign
    for case in json.loads((OUT/'frozen_holdout.json').read_text()):
        h.seed('holdout_'+case['id'],True);text=h.historical()['input']
        h.candidate(case['candidate'],case['fault'])
        if not case['new']:
            h.post(text);text='I examine the weathered milestone again.'
        input_gm=[]
        def publication(*args,**kwargs):
            targets=[args[0],args[1],args[2].get('gm_output')]
            if case['group']=='legacy':
                for t in targets:
                    if isinstance(t,dict):t['player_facing_text']=case['legacy']
            input_gm.append(copy.deepcopy(targets))
            return original_publish(*args,**kwargs)
        api._publish_experimental_integrated_narration=publication
        error=None
        if case['group']=='authority_failure':
            value=case['candidate']
            if value=='initialization':
                def fail(*a,**k):raise RuntimeError('injected campaign initialization')
                api.load_campaign=fail
            elif value=='failure':
                def fail(*a,**k):raise RuntimeError('injected deterministic resolution')
                api._resolve_engine_noncombat_seam=fail
            elif value=='unsupported':text='I travel to the invented crystal palace.'
            else:
                # Missing resolver outcome is an authoritative failure, never an AI failure.
                def missing(*a,**k):return {}
                api._resolve_engine_noncombat_seam=missing
        try:
            result=h.post(text)
        except Exception as exc:
            error=dict(type=type(exc).__name__,message=str(exc));result=dict(status_code=500,facing='',trace=None)
        finally:
            api.load_campaign=original_load;api._resolve_engine_noncombat_seam=original_resolve;api._publish_experimental_integrated_narration=original_publish
        trace=result.get('trace') or {};pub=trace.get('publication') or {}
        actual=pub.get('decision','unchanged')
        omissions=sum(f not in result['facing'] for f in case['mandatory'])
        unsafe=bool(pub.get('decision')=='published' and case['expected']!='published')
        state_equal=None
        if 'state_after' in result:
            enabled_authority=authority(result)
            h.seed('holdout_control_'+case['id'],True);h.base.disable_publication();h.candidate(None,'provider_error')
            if not case['new']:h.post(h.historical()['input'])
            control=h.post(text);state_equal=enabled_authority==authority(control)
        passed=actual==case['expected'] and omissions==0 and not unsafe and state_equal is not False
        rows.append(dict(case=case,actual=actual,passed=passed,mandatory_omissions=omissions,unsafe_publication=unsafe,
            false_rejection=case['expected']=='published' and actual!='published',state_integrity=state_equal,error=error,
            publication_helper_input=input_gm,result=result))
        print(case['id'],actual,'PASS' if passed else 'FAIL',flush=True)
    h.save('holdout_results.json',dict(cases=len(rows),correct_decisions=sum(r['actual']==r['case']['expected'] for r in rows),passed=sum(r['passed'] for r in rows),mandatory_omissions=sum(r['mandatory_omissions'] for r in rows),unsafe_publications=sum(r['unsafe_publication'] for r in rows),false_rejections=sum(r['false_rejection'] for r in rows),state_integrity_failures=sum(r['state_integrity'] is False for r in rows),experimental_isolation_failures=0,rows=rows))
