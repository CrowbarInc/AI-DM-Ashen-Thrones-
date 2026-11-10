"""Publish the fresh review triplet and independently verify its dated archive."""
import hashlib, json, os, shutil, subprocess, zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
ID='pr_play_baseline_provenance'; RP='development/campaigns/product_realization/'+ID+'/'
AP='artifacts/'+ID+'/'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
export=OUT/'review_export'
# Replacing the generated stable ZIP via an adjacent temporary file avoids an
# observed Windows in-place truncate error; prior dated archives remain intact.
for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip'):
    temp=ROOT/'handoff'/('pr_play_baseline_provenance_'+name+'.tmp')
    shutil.copyfile(export/name,temp)
    os.replace(temp,ROOT/'handoff'/name)
stamp=datetime.now(timezone(timedelta(hours=-5),'America/New_York EST')).strftime('%Y%m%d-%H%M%S')
archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
assert not archive.exists()
shutil.copyfile(ROOT/'handoff/CURRENT_REVIEW.zip',archive)
reports=['SUMMARY.md','PROVENANCE_SEARCH.md','HISTORICAL_ATTRIBUTION.md','CURRENT_BASELINE.md','SOURCE_MANIFEST.md','PUBLICATION_AUTHORITY_RISK.md','BASELINE_PROCEDURE.md','NEXT_STEP_DECISION.md','INTEGRITY.md']
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names=z.namelist(); summary=z.read('CURRENT_REVIEW.md').decode('utf-8')
    assert 'Identifier: `'+ID+'`' in summary
    assert '333 passed, 23 failed' in summary
    assert all('support/'+RP+n in names for n in reports)
    manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
    assert manifest['campaign']['id']==ID if isinstance(manifest.get('campaign'),dict) else ID in str(manifest)
    omissions=manifest['omitted_artifacts']
    assert all(r['reason'].startswith('duplicate content of ') for r in omissions),omissions
    checked=[]
    for row in manifest['included_files']:
        data=z.read(row['bundle_path'])
        if row.get('sha256'): assert hashlib.sha256(data).hexdigest()==row['sha256'],row['bundle_path']
        if row.get('canonical_source_path'):
            source=ROOT/row['canonical_source_path']; assert data==source.read_bytes(),str(source)
            checked.append(row['canonical_source_path'])
    current=z.read('support/docs/NEXT_SESSION.md')
    assert current==(ROOT/'docs/NEXT_SESSION.md').read_bytes()
    assert current.startswith(b'# NEXT_SESSION') and b'Baseline Provenance Closure' in current.splitlines()[0]
    assert current.endswith((OUT/'entry_next_session.md').read_bytes())
    source=json.loads(z.read('support/'+AP+'source_manifest.json'))
    results=json.loads(z.read('support/'+AP+'test_results.json'))
    assert results['source_manifest_identity']==source['manifest_identity_sha256']
    assert sum(r['counts']['tests'] for r in results['runs'])==356
    assert sum(r['counts']['passed'] for r in results['runs'])==333
    assert results['same_original_twelve'] is True
    history=json.loads(z.read('support/'+AP+'historical_attribution.json'))
    assert history['stopping_condition']=='B' and len(history['defects'])==3
    assert all(r['historical_classification']=='Historical origin unresolved — closed' for r in history['defects'])
    assert summary.replace('\r\n','\n')==(ROOT/'handoff/CURRENT_REVIEW.md').read_text(encoding='utf-8')
    assert manifest==read(ROOT/'handoff/REVIEW_MANIFEST.json')
assert sha(archive)==sha(ROOT/'handoff/CURRENT_REVIEW.zip')
with zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW.zip') as z: assert z.testzip() is None and z.namelist()==names
unchanged=[p for p,h in source['files'].items() if (ROOT/p).is_file() and sha(ROOT/p)==h]
assert len(unchanged)==len(source['files'])
oldarchives=read(OUT/'historical_archives.json')
for row in oldarchives:
    if row['path']!='handoff/CURRENT_REVIEW.zip': assert sha(ROOT/row['path'])==row['sha256'],row['path']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
assert head==source['head'] and branch==source['branch']
verification={'verdict':'PASS','milestone':ID,'archive_path':str(archive),'archive_sha256':sha(archive),'member_count':len(names),
 'archive_bytes':archive.stat().st_size,'reports_verified':reports,'canonical_files_byte_verified':checked,
 'stable_triplet_matches':True,'historical_handoff_entries_preserved':True,'source_manifest_files_unchanged':len(unchanged),
 'prior_archives_preserved':len(oldarchives)-1,'intentional_duplicate_omissions':omissions,
 'baseline_unique_tests':356,'baseline_passed':333,'baseline_failed':23,'followup_attempts':4,
 'historical_attribution_closed':True,'live_provider_calls':0,
 'snapshot_sha256':sha(OUT/'current_source_snapshot.zip'),
 'stable_zip_write_recovery':'Generator in-place truncate returned OSError EINVAL. Fresh complete export synchronized with adjacent temporary files and os.replace, then both ZIPs independently opened and byte-verified.',
 'seal_location':'External post-seal evidence; archive includes validation protocol and this verifier, not a circular self-hash.'}
(OUT/'archive_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
(OUT/'archive_contents.txt').write_text('\n'.join(names)+'\n',encoding='utf-8')
(OUT/'archive_sha256.txt').write_text(sha(archive)+'  '+str(archive)+'\n',encoding='utf-8')
(OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short','--untracked-files=all'],cwd=ROOT))
created=[p.relative_to(ROOT).as_posix() for folder in (OUT,ROOT/RP) for p in folder.rglob('*') if p.is_file()]
created += [archive.relative_to(ROOT).as_posix(),AP+'files_created.json']
(OUT/'files_created.json').write_text(json.dumps({'created':sorted(set(created)),'updated':['docs/NEXT_SESSION.md','handoff/CURRENT_REVIEW.md','handoff/REVIEW_MANIFEST.json','handoff/CURRENT_REVIEW.zip']},indent=2),encoding='utf-8')
print(json.dumps({k:verification[k] for k in ['verdict','archive_path','archive_sha256','member_count','source_manifest_files_unchanged','baseline_unique_tests']},indent=2))
