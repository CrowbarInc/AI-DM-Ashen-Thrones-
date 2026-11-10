"""Generate standard review, publish fresh exports, independently reopen claims."""
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
MID='pr_play_object_visibility_authoring'
def sha(raw): return hashlib.sha256(raw).hexdigest()
export=OUT/'review_export'
run=subprocess.run([sys.executable,'tools/build_review_handoff.py','--config',str(OUT/'review_handoff.json'),
    '--output-dir',str(export),'--no-history'],cwd=ROOT,text=True,capture_output=True)
(OUT/'handoff_generation.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
assert run.returncode==0,(run.stdout,run.stderr)
history=ROOT/'handoff/history'/MID
history.mkdir(parents=True,exist_ok=True)
for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip'):
    raw=(export/name).read_bytes(); target=ROOT/'handoff'/name
    temp=target.with_name(target.name+'.visibility.tmp')
    temp.write_bytes(raw); os.replace(temp,target)
    hist={'CURRENT_REVIEW.md':'REVIEW.md','CURRENT_REVIEW.zip':'REVIEW.zip'}.get(name,name)
    (history/hist).write_bytes(raw)
stamp=datetime.now(ZoneInfo('America/New_York')).strftime('%Y%m%d-%H%M%S')
dated=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
assert not dated.exists()
dated.write_bytes((export/'CURRENT_REVIEW.zip').read_bytes())
verified=[]
for archive in (ROOT/'handoff/CURRENT_REVIEW.zip',history/'REVIEW.zip',dated):
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
                if row.get('canonical_source_path'): assert raw==(ROOT/row['canonical_source_path']).read_bytes()
        base='support/artifacts/'+MID+'/'
        def evidence(name): return json.loads(member(base+name))
        for row in evidence('evidence_manifest.json')['files']:
            assert sha(member('support/'+row['path']))==row['sha256'],row['path']
        reports='support/development/campaigns/product_realization/'+MID+'/'
        names=('SUMMARY','BASELINE','VISIBILITY_CONTRACT','AUTHORITY_INTEGRATION','IDEMPOTENCY_VERIFICATION',
            'OBSERVATION_INTEGRATION','PERSISTENCE_VERIFICATION','NEGATIVE_CONTROLS','RULESET_PORTABILITY',
            'REGRESSION_RESULTS','TWELVE_TURN_COMPARISON','PERFORMANCE','T06_INTEGRATION_MAP','NEXT_STEP_DECISION','INTEGRITY')
        for name in names: assert MID.encode() in member(reports+name+'.md')
        assert all(v in member(reports+'VISIBILITY_CONTRACT.md') for v in (b'visible',b'concealed',b'restricted',b'no_change'))
        assert b'_VisibilityAuthorization' in member(reports+'AUTHORITY_INTEGRATION.md')
        assert b'prepare_visibility' in member('support/game/object_marking.py')
        assert b'trusted_visibility_operation_required' in member('support/game/api.py')
        timeline=evidence('classification_timeline.json'); states=timeline['snapshots']
        assert [s['state']['inventory'][0]['revision'] for s in states]==[1,2,3,4]
        assert [s['receipt_count'] for s in states]==[1,2,3,4]
        assert [len(s['observation']['properties'][0]['values']) for s in states]==[0,1,0,1]
        ids={s['state']['inventory'][0]['instance_id'] for s in states}; assert len(ids)==1
        assert all(s['state']['inventory'][0]['markings']==timeline['initial']['inventory'][0]['markings'] for s in states)
        assert timeline['leakage']['leaks']==[]
        assert evidence('no_change_and_restricted.json')['no_change']['status']=='no_change'
        assert evidence('ambiguous_reconciliation.json')['no_duplicate']
        for stage in ('serialization','create','partial_write','flush','sync','replace','ambiguous'):
            f=evidence('classification_failure_'+stage+'.json'); assert f['unchanged'] and f['receipt_atomic']
        for fault in ('insert','change','drop','rebind','duplicate'): assert evidence('http_bypass_'+fault+'.json')['rejected']
        for name in ('pf1e@1','rules_light@1','scifi@1'):
            p=evidence('visibility_portability_'+name+'.json'); e=p['extension']; c=p['state']
            assert c['extensions']==c['inventory'][0]['extensions']==c['inventory'][0]['markings'][0]['extensions']==e
        r=evidence('regression_results.json')
        assert not r['combined_new_failures'] and not r['visibility_new_failures']
        assert r['evidence_authoring']['failed']==r['evidence_authoring']['errors']==0
        assert r['evidence_authoring']['passed']>=93
        assert evidence('client_writer_serialization.json')['classification_preserved']
        for group in ('observation','inspection','marking','identity','inventory_snapshot','preservation','combined','visibility'):
            assert set(r['before_'+group]['failures'])==set(r['after_'+group]['failures'])
            assert r['before_'+group]['passed']==r['after_'+group]['passed']
        comparison=evidence('twelve_turn_comparison.json')
        flags=('text_equal','character_equal','scene_equal','resolution_equal','no_implicit_identity_or_marking','publication_pointer_consistent')
        assert len(comparison['turns'])==12 and all(all(t[k] for k in flags) for t in comparison['turns'])
        mapping=evidence('t06_source_map.json')['stages']; assert len(mapping)==14
        assert all(x['source'] and x['status'] for x in mapping)
        handoff=member('support/docs/NEXT_SESSION.md')
        assert MID.encode() in handoff[:700] and handoff.endswith((OUT/'entry_next_session.md').read_bytes())
        changes=evidence('source_changes.json')
        assert changes['changed_existing']==['game/api.py','game/object_marking.py']
        assert changes['frozen_fixture_changes']==changes['production_data_changes']==[]
        verified.append(dict(path=archive.relative_to(ROOT).as_posix(),sha256=sha(archive.read_bytes()),
            bytes=archive.stat().st_size,crc=True,canonical_hashes=True,evidence_hashes=True,
            classification=True,authority=True,idempotency=True,observation=True,persistence=True,
            snapshots=True,regression=True,twelve_turns=True,t06_map=True,handoff=True))
write=lambda name,value:(OUT/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
write('archive_verification.json',dict(milestone=MID,verified=verified,live_provider_calls=0))
(OUT/'archive_sha256.txt').write_text(verified[-1]['sha256']+'  '+str(dated)+'\n',encoding='utf-8')
print(json.dumps(verified[-1],indent=2))

