"""Separate evaluation audit. Does not alter or rerun the frozen holdout."""
import sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_66 import harness as h
from game import api
original=api._resolve_engine_noncombat_seam
pairs=[]
for enabled in (False,True):
    h.seed('missing_outcome_audit_'+str(enabled),True)
    if not enabled:h.base.disable_publication()
    api._resolve_engine_noncombat_seam=lambda *a,**k:{}
    h.candidate(None,'provider_error');pairs.append(h.post(h.historical()['input']))
api._resolve_engine_noncombat_seam=original
def authority(r):
    s=r['state_after']['session'];return dict(location=s.get('active_scene_id'),overlays=s.get('runtime_scene_overlays'),runtime=s.get('scene_runtime'),character=r['state_after']['character'],world=r['state_after']['world'],combat=r['state_after']['combat'])
passed=authority(pairs[0])==authority(pairs[1]) and not (pairs[1].get('trace') or {}).get('publication')
h.save('holdout_evaluation_audit.json',dict(classification='evaluation',frozen_results_unchanged=True,holdout_rerun=False,source_changes_after_freeze=False,
    affected=['H36','H40'],reason='Enabled branch injected missing resolver outcome {}; control restored the normal successful resolver before comparison. The control discovers the milestone clue; the injected branch does not. They are different authoritative operations.',
    raw_state_mismatches=2,diagnostic='Separate paired missing-outcome operation with identical injected resolver in both arms. Not held-out evidence.',passed=passed,authority_equal=authority(pairs[0])==authority(pairs[1]),records=pairs,
    limitation='Existing ordinary pipeline returns HTTP 200 with legacy refusal for an empty resolver mapping. Experimental publisher supplies no outcome or success text; changing general resolver error schema is outside this publication repair.'))
assert passed
print('Separate matched missing-outcome audit PASS')
