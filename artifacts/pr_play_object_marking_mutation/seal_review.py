"""Generate standard handoff, then independently reopen and verify both ZIPs."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
MID='pr_play_object_marking_mutation'
def sha(raw): return hashlib.sha256(raw).hexdigest()
config=OUT/'review_handoff.json'; export=OUT/'review_export'
run=subprocess.run([sys.executable,'tools/build_review_handoff.py','--config',str(config),
    '--output-dir',str(export),'--no-history'],cwd=ROOT,text=True,capture_output=True)
(OUT/'handoff_generation.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
assert run.returncode==0,run.stderr
history=ROOT/'handoff/history'/MID; history.mkdir(parents=True,exist_ok=True)
for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip'):
    raw=(export/name).read_bytes(); target=ROOT/'handoff'/name
    temp=target.with_name(target.name+'.marking.tmp'); temp.write_bytes(raw); os.replace(temp,target)
    hist={'CURRENT_REVIEW.md':'REVIEW.md','CURRENT_REVIEW.zip':'REVIEW.zip'}.get(name,name)
    (history/hist).write_bytes(raw)
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
dated=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
assert not dated.exists(); dated.write_bytes((export/'CURRENT_REVIEW.zip').read_bytes())
verified=[]
for archive in (ROOT/'handoff/CURRENT_REVIEW.zip',dated):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json')); assert manifest['campaign_id']==MID
        omissions=manifest['omitted_artifacts']
        assert all(o['reason'].startswith('duplicate content of ') for o in omissions),omissions
        def member(path):
            if path in z.namelist(): return z.read(path)
            relative=path.removeprefix('support/')
            item=next(o for o in omissions if o['path']==relative)
            duplicate=item['reason'].split('duplicate content of ',1)[1].split(';',1)[0]
            raw=z.read('support/'+duplicate); assert sha(raw)==item['sha256']; return raw
        for row in manifest['included_files']:
            if row.get('sha256'):
                raw=z.read(row['bundle_path']); assert sha(raw)==row['sha256']
                if row.get('canonical_source_path'): assert raw==(ROOT/row['canonical_source_path']).read_bytes()
        base='support/artifacts/'+MID+'/'
        evidence=json.loads(member(base+'evidence_manifest.json'))
        for item in evidence['files']:
            assert sha(member('support/'+item['path']))==item['sha256'],item['path']
        reports='support/development/campaigns/product_realization/'+MID+'/'
        names=['SUMMARY','BASELINE','ATOMIC_PERSISTENCE','MARKING_CONTRACT','IDEMPOTENCY_CONTRACT','IMPLEMENTATION',
            'PERSISTENCE_VERIFICATION','NEGATIVE_CONTROLS','REGRESSION_RESULTS','TWELVE_TURN_COMPARISON','PERFORMANCE','NEXT_STEP_DECISION','INTEGRITY']
        for name in names: assert MID.encode() in member(reports+name+'.md')
        assert b'def add_inventory_object_marking' in member('support/game/api.py')
        assert b'def prepare_marking' in member('support/game/object_marking.py')
        assert b'tempfile.mkstemp' in member('support/game/storage.py')
        atomic=json.loads(member(base+'atomic_save_traces.json'))
        assert len(atomic['failures'])==6 and all(r['before_sha256']==r['after_sha256'] and r['temporary_files']==[] for r in atomic['failures'])
        assert all(r['replaced'] and not r['directory_synchronized'] for r in atomic['postcommit'])
        roundtrip=json.loads(member(base+'marking_round_trip.json'))
        assert roundtrip['result']==roundtrip['replay']
        first=roundtrip['reloaded']['inventory'][0]
        assert first['revision']==1 and len(first['markings'])==1
        assert roundtrip['reloaded']['inventory'][1]==roundtrip['before']['inventory'][1]
        assert roundtrip['reloaded']['object_marking_receipts']['entries'][roundtrip['request']['request_id']]==roundtrip['result']
        snapshots=json.loads(member(base+'marking_snapshots.json'))
        assert snapshots['committed']==snapshots['restored']
        assert snapshots['original_result']==snapshots['post_restore_replay']
        regression=json.loads(member(base+'regression_results.json'))
        assert regression['verified_marking']['passed']==76 and not regression['new_failures']
        assert regression['final_combined']['passed']==regression['before_combined']['passed']==405
        assert regression['final_combined']['failed']==regression['before_combined']['failed']==20
        comparison=json.loads(member(base+'twelve_turn_comparison.json'))
        assert len(comparison['turns'])==12 and all(all(t[k] for k in ('text_equal','character_equal','scene_equal',
            'resolution_equal','no_implicit_identity_or_marking','publication_pointer_consistent')) for t in comparison['turns'])
        next_session=member('support/docs/NEXT_SESSION.md')
        assert MID.encode() in next_session[:700] and next_session.endswith((OUT/'entry_next_session.md').read_bytes())
        sources=json.loads(member(base+'source_changes.json'))
        assert sources['changed_existing']==['game/api.py','game/storage.py']
        assert not sources['frozen_fixture_changes'] and not sources['production_data_changes']
        verified.append(dict(path=str(archive),sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,
            members=len(z.namelist()),crc='pass',canonical_hashes='pass',evidence_manifest='pass',
            all_13_reports='pass',atomic_persistence='pass',marking_receipt='pass',save_reload='pass',
            snapshot='pass',regressions='pass',twelve_turn='pass',handoff='pass'))
assert verified[0]['sha256']==verified[1]['sha256']
entry=json.loads((OUT/'entry_identity.json').read_text())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==entry['head']
(OUT/'archive_verification.json').write_text(json.dumps(dict(milestone=MID,verdict='A/PASS',archives=verified,
    historical_handoff_suffix='byte-identical',live_provider_calls=0),indent=2),encoding='utf-8')
(OUT/'archive_sha256.txt').write_text(verified[1]['sha256']+'  '+str(dated)+'\n',encoding='utf-8')
print(json.dumps(verified[1],indent=2))
