"""Read-only entry-source comparison; original API hash checked against session baseline."""
import sys,types,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
from artifacts.pr_play_66 import run_regression as r
import game
raw=(OUT/'entry_api.py').read_bytes()
assert hashlib.sha256(raw).hexdigest()==json.loads((OUT/'baseline.json').read_text())['entry']['game/api.py']
module=types.ModuleType('game.api');module.__file__=str(ROOT/'game/api.py');module.__package__='game'
sys.modules['game.api']=module;game.api=module
exec(compile(raw,module.__file__,'exec'),module.__dict__)
import pytest
files=['tests/test_start_campaign_api.py::'+n for n in ['test_start_campaign_emits_opening_and_sets_started','test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text','test_start_campaign_promotes_valid_upstream_prepared_scene_opening','test_failed_start_campaign_does_not_mark_started']]
files+=['tests/test_pr_play_37_opening_recovery.py::'+n for n in ['test_http_invalid_declaration_discards_provider_text','test_http_composer_failure_does_not_commit']]
saved=r.snapshot([ROOT/'data'])
try:code=pytest.main(['-q','--tb=short','--junitxml='+str(OUT/'baseline_start_regression.xml')]+files)
finally:r.restore(saved)
sys.exit(code)
