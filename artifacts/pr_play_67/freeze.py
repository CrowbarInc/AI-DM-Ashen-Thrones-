import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
assert not (OUT/'implementation_freeze.json').exists()
files=['game/api.py','game/player_http_projection.py','game/player_http_boundary.py','tests/test_pr_play_67_player_projection.py']
(OUT/'implementation_freeze.json').write_text(json.dumps({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},indent=2)+'\n')
print('Implementation frozen before one-shot holdout.')
