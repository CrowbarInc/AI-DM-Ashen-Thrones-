"""Established regression lanes with historical generated-file restoration."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_66 import run_regression as r
r.OUT=Path(__file__).resolve().parent
if __name__=='__main__':
    saved=r.snapshot(r.PROTECT_ROOTS)
    try:
        focused=r.run_pytest('focused',r.SUITES)
        boundary=r.run_pytest('boundary',['tests/test_pr_play_67_player_projection.py','tests/test_ui_mode_backend_integration.py','tests/test_ui_mode_regression_matrix_objective15.py','tests/test_frontend_ui_mode_hardening_objective15.py','tests/test_state_channels.py','tests/test_snapshots.py'])
        broader=r.run_pytest('broader',['tests/test_pr_cx_authority_assurance.py'])
    finally:restored=r.restore(saved)
    summary=dict(focused=focused,boundary=boundary,broader=broader,new_focused_failures=[n for n in focused['failed_nodeids'] if n not in r.PRIOR],historical_failures=sorted(r.PRIOR),restored_generated_evidence=restored)
    (r.OUT/'regression_summary.json').write_text(json.dumps(summary,indent=2))
