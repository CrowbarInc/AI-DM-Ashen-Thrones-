"""Reuse the established focused and broader lanes without overwriting PR66."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_66 import run_regression as prior
prior.OUT=Path(__file__).resolve().parent
if __name__=='__main__':
    saved=prior.snapshot(prior.PROTECT_ROOTS)
    try:
        focused=prior.run_pytest('focused',prior.SUITES)
        boundary=prior.run_pytest('boundary',['tests/test_pr_play_67_player_projection.py','tests/test_ui_mode_backend_integration.py','tests/test_ui_mode_regression_matrix_objective15.py','tests/test_frontend_ui_mode_hardening_objective15.py','tests/test_state_channels.py','tests/test_snapshots.py'])
        broader=prior.run_pytest('broader',['tests/test_pr_cx_authority_assurance.py'])
        summary=dict(focused=focused,boundary=boundary,broader=broader,historical_focused_failures=sorted(prior.PRIOR),
                     new_focused_failures=[n for n in focused['failed_nodeids'] if n not in prior.PRIOR],full_suite='not run')
    finally: restored=prior.restore(saved)
    summary['restored_generated_evidence']=restored
    (prior.OUT/'regression_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:{f:v for f,v in summary[k].items() if f in ['passed','failed','errors','failed_nodeids']} for k in ['focused','boundary','broader']},indent=2))
