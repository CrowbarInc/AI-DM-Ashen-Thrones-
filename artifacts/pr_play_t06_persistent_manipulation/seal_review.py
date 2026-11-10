"""Reopen and verify a fresh standard review archive; leave its hash external."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
ID='pr_play_t06_persistent_manipulation'
AP='support/artifacts/'+ID+'/'
sha=lambda data:hashlib.sha256(data).hexdigest()
read=lambda name:json.loads((OUT/name).read_text(encoding='utf-8'))
identity=read('entry_identity.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==identity['head']
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==identity['branch']
assert not read('source_changes.json')['changed']
assert not read('source_changes.json')['frozen_changes']
assert all(sha((ROOT/path).read_bytes())==digest for path,digest in read('after_manifest.json').items())
# Client New York offset for this 2026-11-09 cycle; Windows lacks tzdata here.
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
stable=ROOT/'handoff/CURRENT_REVIEW.zip'
archive=ROOT/'handoff'/('CURRENT_REVIEW('+stamp+').zip')
assert not archive.exists()
shutil.copyfile(stable,archive)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
    assert manifest['campaign_id']==ID
    summary=z.read('CURRENT_REVIEW.md').decode('utf-8')
    assert 'BLOCKED' in summary and ID in summary
    hashes=0
    for row in manifest['included_files']:
        data=z.read(row['bundle_path'])
        if row.get('sha256'): assert sha(data)==row['sha256']
        if row.get('canonical_source_path'):
            assert data==(ROOT/row['canonical_source_path']).read_bytes()
            hashes+=1
    assert all(o['reason'].startswith('duplicate content of ') for o in manifest['omitted_artifacts'])
    for row in json.loads(z.read(AP+'evidence_manifest.json'))['entries']:
        assert sha((ROOT/row['path']).read_bytes())==row['sha256']
        member='support/'+row['path']
        if member in z.namelist(): assert sha(z.read(member))==row['sha256']
        else: assert any(o.get('sha256')==row['sha256'] for o in manifest['omitted_artifacts'])
    t=json.loads(z.read(AP+'before_t06.json')); f=json.loads(z.read(AP+'final_t06.json'))
    assert t['request']==f['request']
    assert t['visible']==f['visible']=='That part is not supported here. It was not carried out.'
    for turn in (t,f):
        accepted=turn['log']['gm_output']['metadata']['accepted_response']
        payload={k:v for k,v in accepted.items() if k not in {'integrity_digest','skipped_mutators'}}
        raw=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
        assert sha(raw)==accepted['integrity_digest']
        assert accepted['immutable'] and accepted['hard_validation']['hard_valid']
        assert accepted['text']==turn['visible']
        assert turn['before']['character']==turn['after']['character']
        assert turn['before']['world']==turn['after']['world']
        assert turn['before']['scene']==turn['after']['scene']
    persistence=json.loads(z.read(AP+'persistence_results.json'))
    assert persistence['implemented_modification_roundtrip']=='not_available_blocked'
    assert persistence['refused_action_snapshot_restore_retry']=='passed'
    regressions=json.loads(z.read(AP+'test_results.json'))
    assert regressions['baseline']['tests']==regressions['after']['tests']==425
    assert regressions['focused']['passed']==6
    assert not regressions['new_failure_identities']
    assert not json.loads(z.read(AP+'twelve_turn_comparison.json'))['changed_turns']
    handoff=z.read('support/docs/NEXT_SESSION.md')
    assert handoff==(ROOT/'docs/NEXT_SESSION.md').read_bytes()
    assert handoff.endswith((OUT/'entry_next_session.md').read_bytes())
    assert z.read(AP+'production.diff')==b''
    assert not any('/.git/' in n or '/.env' in n or n.endswith('.zip') for n in z.namelist())
with zipfile.ZipFile(stable) as z:
    assert z.testzip() is None
assert stable.read_bytes()==archive.read_bytes()
result={'status':'PASS','milestone':ID,'verdict':'BLOCKED','archive_path':str(archive),
        'sha256':sha(archive.read_bytes()),'crc_verified':True,'canonical_hashes_verified':hashes,
        'stable_dated_equal':True,'t06_before_after_verified':True,'accepted_digests_verified':True,
        'blocked_persistence_status_verified':True,'regression_results_verified':True,
        'source_and_evidence_manifests_verified':True,'historical_handoff_suffix_preserved':True,
        'production_files_changed':[],'frozen_changes':[],'live_provider_calls':0}
(OUT/'archive_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(OUT/'archive_sha256.txt').write_text(str(archive)+'\nSHA-256: '+result['sha256']+'\n',encoding='utf-8')
(OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
print(json.dumps(result,indent=2))
