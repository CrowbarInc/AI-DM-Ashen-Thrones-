import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_66 import run_regression as r
r.OUT=Path(__file__).resolve().parent
saved=r.snapshot(r.PROTECT_ROOTS+[ROOT/'data'])
try:
 focused=r.run_pytest('focused',r.SUITES+['tests/test_pr_play_68_structured_publication.py','tests/test_pr_play_69_target_references.py','tests/test_pr_play_70_branching.py'])
 boundary=r.run_pytest('boundary',['tests/test_pr_play_67_player_projection.py','tests/test_ui_mode_backend_integration.py','tests/test_ui_mode_regression_matrix_objective15.py','tests/test_frontend_ui_mode_hardening_objective15.py','tests/test_state_channels.py','tests/test_snapshots.py','tests/test_start_campaign_api.py','tests/test_pr_play_37_opening_recovery.py'])
 broader=r.run_pytest('broader',['tests/test_pr_cx_authority_assurance.py'])
finally:restored=r.restore(saved)
(r.OUT/'regression_summary.json').write_text(json.dumps(dict(focused=focused,boundary=boundary,broader=broader,restored=restored),indent=2))
