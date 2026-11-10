"""Create fresh standard exports and independently reopen every packaged claim."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
MID='pr_play_object_marking_disclosure_policy'
def sha(raw): return hashlib.sha256(raw).hexdigest()

export=OUT/'review_export'
run=subprocess.run([sys.executable,'tools/build_review_handoff.py','--config',str(OUT/'review_handoff.json'),
    '--output-dir',str(export),'--no-history'],cwd=ROOT,text=True,capture_output=True)
(OUT/'handoff_generation.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
assert run.returncode==0,run.stderr
history=ROOT/'handoff/history'/MID
history.mkdir(parents=True,exist_ok=True)
for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip'):
    raw=(export/name).read_bytes(); target=ROOT/'handoff'/name
    temp=target.with_name(target.name+'.disclosure.tmp')
    temp.write_bytes(raw); os.replace(temp,target)
    hist={'CURRENT_REVIEW.md':'REVIEW.md','CURRENT_REVIEW.zip':'REVIEW.zip'}.get(name,name)
    (history/hist).write_bytes(raw)
stamp=datetime.now(ZoneInfo('America/New_York')).strftime('%Y%m%d-%H%M%S')
dated=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
assert not dated.exists()
dated.write_bytes((export/'CURRENT_REVIEW.zip').read_bytes())
verified=[]
for archive in (ROOT/'handoff/CURRENT_REVIEW.zip',dated):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
        assert manifest['campaign_id']==MID
        omissions=manifest['omitted_artifacts']
        assert all(o['reason'].startswith('duplicate content of ') for o in omissions),omissions
        def member(path):
            if path in z.namelist(): return z.read(path)
            relative=path.removeprefix('support/')
            item=next(o for o in omissions if o['path']==relative)
            duplicate=item['reason'].split('duplicate content of ',1)[1].split(';',1)[0]
            raw=z.read('support/'+duplicate)
            assert sha(raw)==item['sha256']
            return raw
        for row in manifest['included_files']:
            if row.get('sha256'):
                raw=z.read(row['bundle_path']); assert sha(raw)==row['sha256']
                if row.get('canonical_source_path'):
                    assert raw==(ROOT/row['canonical_source_path']).read_bytes()
        base='support/artifacts/'+MID+'/'
        def evidence(name): return json.loads(member(base+name))
        for row in evidence('evidence_manifest.json')['files']:
            assert sha(member('support/'+row['path']))==row['sha256'],row['path']
        reports='support/development/campaigns/product_realization/'+MID+'/'
        names=('SUMMARY','BASELINE','DISCLOSURE_OWNERSHIP','OBSERVATION_CONTRACT','MARKING_VISIBILITY',
            'INFORMATION_BOUNDARY','IMPLEMENTATION','READ_ONLY_VERIFICATION','PERSISTENCE_VERIFICATION',
            'NEGATIVE_CONTROLS','RULESET_PORTABILITY','REGRESSION_RESULTS','TWELVE_TURN_COMPARISON',
            'PERFORMANCE','NEXT_STEP_DECISION','INTEGRITY')
        for name in names: assert MID.encode() in member(reports+name+'.md')
        contract=member(reports+'OBSERVATION_CONTRACT.md')
        assert all(v in contract for v in (b'known_absent',b'unknown',b'_ObservationAuthorization',b'state'))
        source=member('support/game/object_observation.py')
        assert all(v in source for v in (b'def observe_object',b'def _project_markings',b'_PROJECTORS'))
        assert b'from game.storage' not in source
        assert evidence('information_leakage.json')['leaks']==[]
        assert evidence('noninterference.json')['hidden_variants_equal']
        absence=evidence('absence_semantics.json')
        assert absence['partial']['properties'][0]['knowledge']=='unknown'
        assert absence['complete']['properties'][0]['knowledge']=='known_absent'
        purity=evidence('read_only.json')
        assert purity['state_equal'] and purity['disk_equal'] and purity['before_hash']==purity['after_hash']
        timeline=evidence('observation_timeline.json')
        assert timeline['current_result']==timeline['reloaded_result']
        def contents(r): return [v['content'] for v in r['properties'][0]['values']]
        assert contents(timeline['before_result'])==['mark A','mark B']
        assert contents(timeline['current_result'])==['mark B']
        assert [contents(s['result']) for s in timeline['snapshots']]==[[],['mark A','mark B'],['mark B']]
        values=[]
        for name in ('pf1e@1','rules_light@1','scifi@1'):
            row=evidence('observation_portability_'+name+'.json')
            assert row['before']==row['after']; values.append(row['result']['properties'])
        assert values[0]==values[1]==values[2]
        regression=evidence('regression_results.json')
        assert not regression['new_failures'] and not regression['newly_passing']
        assert regression['verified_observation']['passed']==88
        for name in ('combined','inspection','marking','identity','inventory_snapshot','preservation'):
            assert regression['before_'+name]['passed']==regression['after_'+name]['passed']
            assert set(regression['before_'+name]['failures'])==set(regression['after_'+name]['failures'])
        assert regression['reference_visibility']['execution']['feature_absent_control']
        assert not regression['reference_visibility']['execution']['observation_imported']
        assert not regression['supplemental_new_failures']
        comparison=evidence('twelve_turn_comparison.json')
        flags=('text_equal','character_equal','scene_equal','resolution_equal','no_implicit_identity_or_marking','publication_pointer_consistent')
        assert len(comparison['turns'])==12 and all(all(t[k] for k in flags) for t in comparison['turns'])
        handoff=member('support/docs/NEXT_SESSION.md')
        assert MID.encode() in handoff[:700] and handoff.endswith((OUT/'entry_next_session.md').read_bytes())
        changes=evidence('source_changes.json')
        assert changes['changed_existing']==[]
        assert changes['added']==['game/object_observation.py','tests/test_object_observation.py']
        assert not changes['frozen_fixture_changes'] and not changes['production_data_changes']
        before=evidence('before_manifest.json'); after=evidence('after_manifest.json')
        assert all(after[p]==digest and sha((ROOT/p).read_bytes())==digest for p,digest in before.items())
        assert all(sha((ROOT/p).read_bytes())==digest for p,digest in after.items())
        assert MID.encode() in z.read('CURRENT_REVIEW.md')
        verified.append(dict(path=str(archive),sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,
            members=len(z.namelist()),crc='pass',canonical_hashes='pass',evidence_manifest='pass',all_16_reports='pass',
            observation_contract='pass',hidden_state='pass',read_only='pass',save_reload='pass',snapshots='pass',
            portability='pass',regression='pass',twelve_turn='pass',handoff='pass',source_manifests='pass'))
assert verified[0]['sha256']==verified[1]['sha256']
entry=json.loads((OUT/'entry_identity.json').read_text(encoding='utf-8-sig'))
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==entry['head']
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()==entry['branch']
(OUT/'archive_verification.json').write_text(json.dumps(dict(milestone=MID,verdict='A/PASS',archives=verified,
    historical_handoff_suffix='byte-identical',live_provider_calls=0),indent=2),encoding='utf-8')
(OUT/'archive_sha256.txt').write_text(verified[1]['sha256']+'  '+str(dated)+'\n',encoding='utf-8')
print(json.dumps(verified[1],indent=2))
