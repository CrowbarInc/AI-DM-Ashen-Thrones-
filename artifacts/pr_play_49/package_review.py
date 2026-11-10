"""Create the established review archive, preserve predecessor, verify hashes."""
import os
os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'] = '1'
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'artifacts/pr_play_49'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def main():
    summary = json.loads((OUT/'summary.json').read_text())
    assert summary['provider_requests']==0 and not summary['new_regressions']
    manifest = json.loads((OUT/'source_change_manifest.json').read_text())
    for name, row in manifest.items():
        assert sha(ROOT/name)==row['sha256']
        dest = OUT/'source_after'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    supporting = [
        'artifacts/pr_play_48/PR_PLAY_48_REPORT.md', 'artifacts/pr_play_48/source_map.json',
        'artifacts/pr_play_48/source_reviewed/game/controlled_investigation_renderer.py',
        'artifacts/pr_play_47/PR_PLAY_47_REPORT.md', 'artifacts/pr_play_47/expressive_range.json',
        'artifacts/pr_play_47/evidence_stress.json', 'artifacts/pr_play_47/summary.json',
        'artifacts/pr_play_43/live_result.json',
        'game/exploration.py','game/authorized_information.py','game/mechanical_claims.py',
        'game/narration_authorization.py','game/immutable_valid_response.py',
        'game/api_turn_support.py','game/prompt_context.py','game/gm.py',
        'game/dialogue_authority.py','game/api.py','game/models.py',
        'tests/conftest.py','tests/helpers/live_model_guard.py',
        'tests/test_pr_play_47_controlled_renderer.py',
    ]
    for name in supporting:
        dest = OUT/'supporting'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    dump('supporting_inventory.json', {n:{'sha256':sha(ROOT/n),'bytes':(ROOT/n).stat().st_size} for n in supporting})
    # Values are compared locally, never printed or exported. Prevent accidental
    # credential inclusion in source snapshots and raw test logs.
    credentials = []
    for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line or line.lstrip().startswith('#'): continue
        key,value = line.split('=',1)
        value = value.strip().strip('\"\'')
        if len(value)>8 and any(k in key.lower() for k in ('key','secret','token','password')):
            credentials.append(value.encode())
    excluded = {'MANIFEST.json','archive_verification.json','archive_path.txt','credential_scan.json'}
    paths = [p for p in OUT.rglob('*') if p.is_file() and
             not set(p.relative_to(OUT).parts)&{'predecessor','__pycache__'} and
             not (p.parent==OUT and p.name in excluded)]
    hits = [p.relative_to(OUT).as_posix() for p in paths if any(c in p.read_bytes() for c in credentials)]
    assert not hits, 'Credential match: packaging stopped'
    dump('credential_scan.json', {'passed':True,'files_scanned':len(paths),'hits':[]})
    paths.append(OUT/'credential_scan.json')
    dump('MANIFEST.json', {p.relative_to(OUT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths})
    paths.append(OUT/'MANIFEST.json')
    # New York is EST on the client task date, November 2, 2026.
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT/'handoff'/f'CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip'
    report = (OUT/'PR_PLAY_49_REPORT.md').read_bytes()
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in paths: z.write(p,p.relative_to(OUT).as_posix())
        z.writestr('CURRENT_REVIEW.md', report)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v['sha256']
                   for k,v in json.loads(z.read('MANIFEST.json')).items())
    for name,content in [('CURRENT_REVIEW.zip',archive.read_bytes()),('CURRENT_REVIEW.md',report)]:
        pending = ROOT/'handoff'/('PR_PLAY_49_pending_'+name)
        pending.write_bytes(content)
        pending.replace(ROOT/'handoff'/name)
    dump('archive_verification.json', {'archive':str(archive),'sha256':sha(archive),
          'stable_archive':str(ROOT/'handoff/CURRENT_REVIEW.zip'),
          'stable_archive_matches':sha(archive)==sha(ROOT/'handoff/CURRENT_REVIEW.zip'),
          'crc_valid':True,'manifest_hashes_valid':True,'entries':len(paths)+1,
          'bytes':archive.stat().st_size})
    (OUT/'archive_path.txt').write_text(str(archive)+'\n')
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'entries':len(paths)+1},indent=2))


if __name__=='__main__': main()
