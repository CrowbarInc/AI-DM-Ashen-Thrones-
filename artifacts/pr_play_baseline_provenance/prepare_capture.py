"""Bounded read-only provenance inventory and current source identity capture."""
import hashlib, json, os, subprocess, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
os.chdir(ROOT)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8',errors='replace')
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
protected={}
for folder in ('game','tests','data','static','prompts'):
    if (ROOT/folder).exists():
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and not p.name.startswith('.env'):
                protected[p.relative_to(ROOT).as_posix()]=sha(p)
configs=[p for pattern in ('requirements*.txt','pyproject.toml','pytest.ini','setup.cfg','setup.py') for p in ROOT.glob(pattern)]
for p in configs: protected[p.relative_to(ROOT).as_posix()]=sha(p)
status=git('status','--porcelain=v1','--untracked-files=all')
(OUT/'entry_git_status.txt').write_text(status,encoding='utf-8')
(OUT/'entry_next_session.md').write_bytes((ROOT/'docs/NEXT_SESSION.md').read_bytes())
write('source_manifest.json',{'milestone':'pr_play_baseline_provenance','captured_at_utc':datetime.now(timezone.utc).isoformat(),
 'branch':git('branch','--show-current').strip(),'head':git('rev-parse','HEAD').strip(),
 'worktree':'dirty; full paths and status in entry_git_status.txt','files':protected,
 'configuration_paths':[p.relative_to(ROOT).as_posix() for p in configs],
 'python':sys.version,'executable':sys.executable,
 'manifest_identity_sha256':hashlib.sha256(json.dumps(protected,sort_keys=True).encode()).hexdigest(),
 'exclusions':['environment files','credentials','bytecode','VCS internals','virtual environments'],
 'scope':'all game/tests/data/static/prompts files plus root dependency and pytest configurations; hashes only for data'})
deps=subprocess.run([sys.executable,'-m','pip','list','--format=json'],capture_output=True,text=True)
(OUT/'dependency_versions.json').write_text(deps.stdout or '[]',encoding='utf-8')
# Preserve the complete executable source/test set as evidence, without local environment values.
with zipfile.ZipFile(OUT/'current_source_snapshot.zip','w',zipfile.ZIP_DEFLATED) as z:
    for path in protected:
        if path.startswith(('game/','tests/','static/','prompts/')) or path in [p.relative_to(ROOT).as_posix() for p in configs]: z.write(ROOT/path,path)
archives=set((ROOT/'handoff').glob('*.zip'))
for topic in ('at_opt_06','pr_play_post_opt','pr_play_post_npc','pr_play_adjacent_regression','pr_play_adjacent_regression_recovery'):
    archives.update((ROOT/'artifacts'/topic).glob('*.zip'))
    archives.update((ROOT/'handoff/history'/topic).glob('*.zip'))
archive_rows=[]
relevant=['game/conversational_orchestration.py','game/conversational_continuity.py','game/intent_parser.py','game/referenced_surface.py','game/perception_grounding.py','game/immutable_valid_response.py','game/api.py','tests/test_referenced_surface_grounding_inspection_resolution.py']
for p in sorted(archives):
    with zipfile.ZipFile(p) as z:
        names=z.namelist()
        selected={f:[n for n in names if n==f or n.endswith('/'+f)] for f in relevant}
        summary=next((n for n in names if n=='CURRENT_REVIEW.md' or n=='REVIEW.md'),None)
        row={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'member_count':len(names),
          'summary_head':z.read(summary).decode('utf-8',errors='replace')[:700] if summary else None,
          'required_source_members':selected,'source_member_hashes':{n:hashlib.sha256(z.read(n)).hexdigest() for ns in selected.values() for n in ns},
          'has_complete_relevant_set':all(selected.values())}
        archive_rows.append(row)
write('historical_archives.json',archive_rows)
commands=[('refs',['show-ref']),('log',['log','-12','--format=%H %aI %s']),('reflog',['reflog','--all','--format=%H %gD %gs']),('stashes',['stash','list']),('unreachable',['fsck','--full','--no-reflogs','--unreachable'])]
records={}
for name,args in commands:
    result=subprocess.run(['git',*args],capture_output=True,text=True,cwd=ROOT)
    records[name]={'command':['git',*args],'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
write('git_provenance.json',records)
# Explicitly named predecessor snapshot only; no user-directory traversal.
temp=Path(os.environ['TEMP'])/'pr_play_adj_audit'
locals_found=[]
if temp.exists():
    for p in temp.iterdir():
        locals_found.append({'path':str(p),'kind':'directory' if p.is_dir() else 'file'})
    overlay=temp/'overlay'
    for f in relevant:
        p=overlay/f
        if p.is_file(): locals_found.append({'path':str(p),'sha256':sha(p),'classification':'reconstructed approximation per overlay_manifest.json'})
write('local_snapshot_inventory.json',{'bounded_root':str(temp),'exists':temp.exists(),'entries':locals_found})
print(json.dumps({'protected_files':len(protected),'archives_examined':len(archive_rows),'git_unreachable_lines':len(records['unreachable']['stdout'].splitlines()),'snapshot_sha256':sha(OUT/'current_source_snapshot.zip')}))
