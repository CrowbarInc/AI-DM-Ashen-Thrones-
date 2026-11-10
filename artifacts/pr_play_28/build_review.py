import pathlib,json,difflib,hashlib,re,zipfile,datetime
p=pathlib.Path('artifacts/pr_play_28')
production=['game/social.py','data/world.json','data/validation/atgb/baselines/frontier-gate-v1/world.json','data/validation/atgb/baselines/frontier-gate-v1/manifest.json','tools/atgb/baseline.py','tools/playtest/gameplay.py','tools/playtest/overlays.py','tools/playtest/social_overlay_authority.py']
files=production+['tests/test_pr_play_28_topic_authority.py','tests/test_pr_play_28_baseline_reproduction.py']
for name in files:
 q=p/'source_snapshot'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(pathlib.Path(name).read_bytes())
 base=p/'source_before'/name
 old=base.read_text(encoding='utf-8') if base.exists() else ''
 q=p/'source_diffs'/pathlib.Path(name).with_suffix(pathlib.Path(name).suffix+'.diff');q.parent.mkdir(parents=True,exist_ok=True)
 q.write_text(''.join(difflib.unified_diff(old.splitlines(True),pathlib.Path(name).read_text(encoding='utf-8').splitlines(True),fromfile='before/'+name if base.exists() else '/dev/null',tofile='after/'+name)),encoding='utf-8')
patterns=[r'sk-(?:proj-|svcacct-)[A-Za-z0-9_-]{20,}',r'AKIA[0-9A-Z]{16}',r'Bearer\s+[A-Za-z0-9_\-.]{32,}']
candidates=[f for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name not in {'MANIFEST.json','archive_verification.json','archive_path.txt','credential_scan.json'}]
hits=[]
for f in candidates:
 text=f.read_text(encoding='utf-8',errors='ignore')
 if any(re.search(pattern,text) for pattern in patterns):hits.append(f.relative_to(p).as_posix())
(p/'credential_scan.json').write_text(json.dumps(dict(files_scanned=len(candidates),suspected_secret_files=hits,scope='Selected evidence/source only; .env, credentials, auth files, unrelated repository artifacts excluded'),indent=2),encoding='utf-8')
assert not hits,hits
# Manifest of selected, reviewable payload; self and archive verification excluded.
candidates.append(p/'credential_scan.json')
manifest=[dict(path=f.relative_to(p).as_posix(),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in candidates]
(p/'MANIFEST.json').write_text(json.dumps(dict(files=manifest,live_provider_requests=0),indent=2),encoding='utf-8')
now=datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=-5)))
archive=pathlib.Path('handoff')/('CURRENT_REVIEW('+now.strftime('%Y%m%d-%H%M%S')+').zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in candidates+[p/'MANIFEST.json']:z.write(f,'pr_play_28/'+f.relative_to(p).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert all('pr_play_28/'+r['path'] in z.namelist() for r in manifest)
 for r in manifest:assert hashlib.sha256(z.read('pr_play_28/'+r['path'])).hexdigest()==r['sha256']
 verification=dict(path=str(archive.resolve()),members=len(z.infolist()),crc_ok=True,sha256_all_manifest_entries_match=True,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
(p/'archive_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8');(p/'archive_path.txt').write_text(str(archive.resolve()),encoding='utf-8')
print(json.dumps(verification,indent=2))
