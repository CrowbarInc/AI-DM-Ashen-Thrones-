"""Targeted comparison against saved pre-pass functions, without changing files under the regression run."""
import pathlib,sys,importlib,pytest
p=pathlib.Path('artifacts/pr_play_28');sys.path.insert(0,str(pathlib.Path.cwd()))
for name in ['game.social','tools.playtest.overlays','tools.playtest.gameplay']:
 module=importlib.import_module(name);source=p/'source_before'/pathlib.Path(*name.split('.')).with_suffix('.py')
 exec(compile(source.read_text(encoding='utf-8'),str(source),'exec'),module.__dict__)
raise SystemExit(pytest.main(['tests/test_pr_play_27_expression_recovery.py::test_budget_stops_real_controller_after_recovery','tests/test_clue_idempotence.py::test_apply_socially_revealed_leads_twice_preserves_canonical_state','-q','--tb=short','--basetemp=development/tmp/pr_play_28_extra_baseline','--junitxml='+str(p/'extra_baseline.xml')]))
