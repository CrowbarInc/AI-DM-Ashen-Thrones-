"""PR-PLAY-12 evidence preparation; no provider or gameplay mutation."""
import hashlib, json, subprocess, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'artifacts/pr_play_12'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    (OUT/'entry_status.txt').write_bytes(subprocess.check_output(['git','status','--short'], cwd=ROOT))
    (OUT/'revision.txt').write_bytes(subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT))
    protected = {}
    for folder in ['game','data','static','experiments','tests','tools','scripts','docs','development/campaigns/reconciliation']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                protected[p.relative_to(ROOT).as_posix()] = sha(p)
    (OUT/'protected_before.json').write_text(json.dumps(protected,indent=2))
    # A byte-preserved, isolated regression checkout prevents legacy tests from rewriting history.
    sandbox = OUT/'sandbox'
    for folder in ['game','tests','tools','scripts','docs','data','static','development/campaigns','development/README.md']:
        src=ROOT/folder; dest=sandbox/folder
        if src.is_dir(): shutil.copytree(src,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.zip'))
        elif src.exists(): dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dest)
    for f in ['pytest.ini','requirements.txt','.gitignore']:
        shutil.copy2(ROOT/f,sandbox/f)
    for folder in ['pr_play_04','pr_play_05','pr_play_06','pr_play_07','pr_play_08','pr_play_09','pr_play_10','pr_play_11']:
        src=ROOT/'artifacts'/folder
        shutil.copytree(src,sandbox/'artifacts'/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.zip'))
    runs=['20261030T183848Z-5fe421902485','20261030T191257Z-ecc1b6062bdc','20261031T015747Z-5a6c03c902e3','20261031T170523Z-92cd9d058c92']
    inventory=[]
    for run in runs:
        src=ROOT/'artifacts/atgb/automated_playtests'/run
        dst=sandbox/'artifacts/atgb/automated_playtests'/run
        shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.zip','__pycache__'))
        cap=next((src/'opening_response_evidence').glob('*.json'))
        preserved=OUT/'historical'/run
        preserved.mkdir(parents=True,exist_ok=True)
        shutil.copy2(cap,preserved/'capture.json')
        shutil.copy2(src/'baseline/documents.json',preserved/'baseline_documents.json')
        data=json.loads(cap.read_text())
        inventory.append(dict(run=run,source=str(cap.relative_to(ROOT)),sha256=sha(cap),capture_keys=list(data),declarations=len(data['parsed_response']['declared_claims']),parsed=data['parsed_response']))
    (OUT/'capture_inventory.json').write_text(json.dumps(inventory,indent=2))
if __name__=='__main__': main()
