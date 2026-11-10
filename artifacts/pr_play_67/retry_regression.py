"""Verify newly observed WinError 5 failures without changing persistence code."""
import sys,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from artifacts.pr_play_66 import run_regression as prior
OUT=Path(__file__).resolve().parent;prior.OUT=OUT
summary=json.loads((OUT/'regression_summary.json').read_text())
saved=prior.snapshot(prior.PROTECT_ROOTS)
try:
    diagnostic=prior.run_pytest('winerror_diagnostic',[
        'tests/test_pr_play_61_player_facing.py::test_rejected_narration_stays_off_the_response[malformed-]',
        'tests/test_pr_play_52_quarantined_integration.py::test_saved_responses_stay_paired'])
    focused=prior.run_pytest('focused_retry',prior.SUITES)
finally:restored=prior.restore(saved)
summary['previous_focused']=summary['focused'];summary['focused']=focused
summary['winerror_diagnostic']=diagnostic
summary['new_focused_failures']=[n for n in focused['failed_nodeids'] if n not in prior.PRIOR]
summary['retry_reason']='Two newly observed WinError 5 os.replace session persistence failures; no persistence or production changes made.'
summary['retry_restored']=restored
(OUT/'regression_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:focused[k] for k in ['passed','failed','failed_nodeids']},indent=2))
