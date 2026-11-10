import sys,json,hashlib,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sources=['game/api.py','game/integrated_investigation_narration.py','tests/test_pr_play_68_structured_publication.py']
assert not (OUT/'implementation_freeze.json').exists()
(OUT/'implementation_freeze.json').write_text(json.dumps({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sources},indent=2))
diff=''
for n in sources[:2]:diff+=''.join(difflib.unified_diff((OUT/'entry_source'/Path(n).name).read_text(encoding='utf-8').splitlines(True),(ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile='entry/'+n,tofile=n))
(OUT/'implementation.diff').write_text(diff,encoding='utf-8')
