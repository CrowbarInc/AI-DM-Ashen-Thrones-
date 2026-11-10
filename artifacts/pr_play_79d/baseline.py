import hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8', errors='replace')
def hashes():
    return [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
            for p in sorted((ROOT/'data').rglob('*')) if p.is_file()]
if __name__ == '__main__':
    result = {'branch': git('branch','--show-current').strip(), 'head': git('rev-parse','HEAD').strip(),
              'status': git('status','--short'), 'files': hashes()}
    (OUT/'baseline.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    (OUT/'entry.diff').write_text(git('diff','--','game','tests','docs/NEXT_SESSION.md'), encoding='utf-8')
    print(result['branch'], result['head'], 'protected', len(result['files']))
