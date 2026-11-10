"""Seal and independently inspect the exact timestamped review export."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
RP='development/campaigns/product_realization/pr_play_adjacent_regression_recovery/'
AP='artifacts/pr_play_adjacent_regression_recovery/'
# This audit's client date is 2026-11-08, when New York is EST (UTC-05:00).
# The Windows venv has no IANA tzdata; no dependency installation is needed.
CLIENT_ZONE=timezone(timedelta(hours=-5), 'America/New_York EST')
stamp=datetime.now(CLIENT_ZONE).strftime('%Y%m%d-%H%M%S')
archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
assert not archive.exists()
shutil.copyfile(ROOT/'handoff/CURRENT_REVIEW.zip', archive)
sha=lambda b:hashlib.sha256(b).hexdigest()
digest=sha(archive.read_bytes())
reports=['SUMMARY.md','HANDOFF_RECOVERY.md','FAILURE_INVENTORY.md','BASELINE_RECONSTRUCTION.md',
         'CONTRACT_ANALYSIS.md','TARGETED_REPAIR_VERIFICATION.md','NEXT_STEP_DECISION.md','INTEGRITY.md']
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names=z.namelist()
    summary=z.read('CURRENT_REVIEW.md').decode('utf-8')
    nextsession=z.read('support/docs/NEXT_SESSION.md').decode('utf-8')
    assert 'Adjacent Regression Reconciliation' in summary and 'Verified Recovery' in summary
    assert 'Adjacent Regression Reconciliation recovery' in nextsession.splitlines()[0]
    assert 'B — Conditional acceptance' in summary and 'A/PASS' in summary
    required=['support/'+RP+n for n in reports]+['support/'+AP+'classification_matrix.json',
               'support/'+AP+'http_capture.json','support/'+AP+'recovery_junit.xml','support/docs/NEXT_SESSION.md']
    assert all(n in names for n in required)
    manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
    assert not manifest['omitted_artifacts']
    matrix=json.loads(z.read('support/'+AP+'classification_matrix.json'))
    assert len(matrix['failures'])==12 and matrix['totals']=={'A':0,'B':0,'C':9,'D':0,'E':3}
    assert len({r['test'] for r in matrix['failures']})==12
    provenance=[]
    for row in manifest['included_files']:
        data=z.read(row['bundle_path'])
        if row.get('sha256'):
            assert sha(data)==row['sha256'],row['bundle_path']
        if row.get('canonical_source_path'):
            source=ROOT/row['canonical_source_path']
            assert data==source.read_bytes(),row['canonical_source_path']
            provenance.append(row['canonical_source_path'])
    # The generator writes text files using Windows CRLF, but renders ZIP text as LF.
    assert summary.replace('\r\n','\n')==(ROOT/'handoff/CURRENT_REVIEW.md').read_text(encoding='utf-8')
    assert manifest==json.loads((ROOT/'handoff/REVIEW_MANIFEST.json').read_text(encoding='utf-8'))
    assert z.read('support/docs/NEXT_SESSION.md')==(ROOT/'docs/NEXT_SESSION.md').read_bytes()

old_hashes={p.name:sha(p.read_bytes()) for p in [ROOT/'handoff/CURRENT_REVIEW(20261108-172122).zip',
                                            ROOT/'handoff/CURRENT_REVIEW(20261108-174500).zip']}
assert digest not in old_hashes.values()
assert digest==sha((ROOT/'handoff/CURRENT_REVIEW.zip').read_bytes())
with zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW(20261108-174500).zip') as old:
    historical=old.read('support/docs/NEXT_SESSION.md').decode('utf-8').replace('\r\n','\n')
assert nextsession.replace('\r\n','\n').endswith(historical)
entry=json.loads((OUT/'entry_hashes.json').read_text())
changed=[p for p,h in entry.items() if not (ROOT/p).exists() or sha((ROOT/p).read_bytes())!=h]
assert not changed
verification={'verdict':'PASS','milestone':'pr_play_adjacent_regression',
    'checked_at':datetime.now(CLIENT_ZONE).isoformat(),
    'archive_path':str(archive),'archive_sha256':digest,'archive_bytes':archive.stat().st_size,
    'members':names,'member_count':len(names),'required_reports':reports,
    'classification_rows':12,'classification_totals':matrix['totals'],
    'internal_current_review_head':summary[:1200],'packaged_next_session_head':nextsession[:1700],
    'canonical_files_byte_verified':provenance,'stable_triplet_matches_archive':True,
    'generated_text_comparison':'Normalized Windows CRLF/LF; manifest JSON compared structurally. Canonical files compared byte-for-byte.',
    'previous_archive_hashes':old_hashes,'different_from_previous_packages':True,
    'historical_handoff_entries_preserved':True,'protected_files_unchanged':len(entry),
    'live_provider_calls':0,'packaging_tests_rerun':False}
(OUT/'archive_verification.json').write_text(json.dumps(verification,indent=2))
(OUT/'archive_contents.txt').write_text('\n'.join(names)+'\n')
(OUT/'archive_sha256.txt').write_text(digest+'  '+str(archive)+'\n')
(OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
created=[str(p.relative_to(ROOT)) for folder in (OUT,ROOT/RP) for p in folder.rglob('*') if p.is_file()]
created += [str(p.relative_to(ROOT)) for p in (ROOT/'handoff').glob('CURRENT_REVIEW(*).zip')
            if sha(p.read_bytes())==digest]
created += [AP+'files_created.json']
(OUT/'files_created.json').write_text(json.dumps({'created':sorted(created),'updated':[
    'docs/NEXT_SESSION.md','handoff/CURRENT_REVIEW.md','handoff/REVIEW_MANIFEST.json','handoff/CURRENT_REVIEW.zip']},indent=2))
print(json.dumps({k:verification[k] for k in ['verdict','archive_path','archive_sha256','member_count',
    'classification_rows','protected_files_unchanged']},indent=2))
