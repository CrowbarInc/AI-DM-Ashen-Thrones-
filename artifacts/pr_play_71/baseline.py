import sys,json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
def hashes(paths):return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
if __name__=='__main__':
    data=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),protected=hashes((ROOT/'data').rglob('*')),entry=hashes(list((ROOT/'game').glob('*.py'))+list((ROOT/'static').glob('*'))))
    (OUT/'baseline.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
