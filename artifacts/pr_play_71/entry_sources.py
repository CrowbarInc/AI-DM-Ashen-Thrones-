import json,hashlib,zipfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
b=json.loads((OUT/'baseline.json').read_text())
z=zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW(20261105-190621).zip')
sources={}
for p in ['game/api.py','game/authored_consequences.py','game/storage.py']:
 sources[p]=z.read('support/'+p)
sources['game/campaign_reset.py']=subprocess.check_output(['git','show','HEAD:game/campaign_reset.py'],cwd=ROOT)
sources['game/campaign_reset.py']=sources['game/campaign_reset.py'].replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
sources['static/app.js']=(ROOT/'artifacts/pr_play_70/entry_source/app.js').read_bytes()
sources['game/quarantined_investigation_narration.py']=(ROOT/'game/quarantined_investigation_narration.py').read_bytes()
for p,raw in sources.items():
 assert hashlib.sha256(raw).hexdigest()==b['entry'][p],p
 dest=OUT/'entry_source'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
(OUT/'entry_source_provenance.json').write_text(json.dumps({p:hashlib.sha256(raw).hexdigest() for p,raw in sources.items()},indent=2))
