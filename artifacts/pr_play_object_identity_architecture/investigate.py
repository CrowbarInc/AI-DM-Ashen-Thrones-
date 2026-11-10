"""Design-cycle evidence only; does not import the runtime or contact providers."""
from pathlib import Path
import hashlib, json, subprocess, re, sys
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
def manifest():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('game','tests','data','static','prompts','tools','scripts')
            for p in (ROOT/folder).rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and p.suffix != '.pyc'}
if sys.argv[1] == 'entry':
    write('before_manifest.json', manifest())
    write('entry_identity.json', {k: subprocess.check_output(['git',*v], cwd=ROOT, text=True).strip()
          for k,v in {'branch':['branch','--show-current'],'head':['rev-parse','HEAD']}.items()})
    (OUT/'entry_git_status.txt').write_bytes(subprocess.check_output(['git','status','--porcelain=v1'],cwd=ROOT))
    for name,path in [('entry_next_session.md','docs/NEXT_SESSION.md'),('entry_current_review.md','handoff/CURRENT_REVIEW.md')]:
        (OUT/name).write_bytes((ROOT/path).read_bytes())
    groups = {
      'object_model_references': r'inventory|equipment|equipped|container|item_template|items_added|items_removed',
      'action_owner_references': r'^def .*resolv|^def .*physical|resolve_transient_local_action|unsupported_physical_manipulation',
      'state_mutation_references': r'runtime_commit_scope|assert_owner_can_mutate|apply_resolution_world_updates|def _write_props',
      'persistence_references': r'^def (save_character|load_character|create_snapshot|load_snapshot)|CHARACTER_PATH|_RUNTIME_COMMIT_PATHS',
    }
    for name,pattern in groups.items():
        rows=[]
        for p in (ROOT/'game').rglob('*.py'):
            for i,line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
                if re.search(pattern,line,re.I): rows.append({'path':p.relative_to(ROOT).as_posix(),'line':i,'text':line.strip()})
        write(name+'.json',rows)
    print('Entry captured; reference rows:', {n:len(json.loads((OUT/(n+'.json')).read_text(encoding='utf-8'))) for n in groups})
elif sys.argv[1] == 'final':
    after=manifest(); before=json.loads((OUT/'before_manifest.json').read_text())
    write('after_manifest.json',after)
    changes={'changed':[p for p,h in before.items() if after.get(p)!=h], 'added':sorted(set(after)-set(before))}
    write('source_changes.json',changes)
    assert not changes['changed'] and not changes['added'],changes
    assert (ROOT/'docs/NEXT_SESSION.md').read_bytes().endswith((OUT/'entry_next_session.md').read_bytes())
    (OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--porcelain=v1'],cwd=ROOT))
    print('Protected manifests identical:',len(before),'files; historical session handoff preserved')
