import os
from pathlib import Path
import shutil
import sys
from run_checks import ROOT,OUT,capture,FIVE

mode=sys.argv[1]
if mode=='comparison':
    isolated=ROOT/'development/tmp/pr_play_05/pre04'
    shutil.copy2(ROOT/'tests/test_pr_play_05_emission_evidence.py',isolated/'tests/test_pr_play_05_emission_evidence.py')
    os.environ['PR_PLAY_05_EMISSION_OUT']=str(OUT/'emission_pre04')
    capture('emission_pre04',['tests/test_pr_play_05_emission_evidence.py'],cwd=isolated)
    os.environ.pop('PR_PLAY_05_EMISSION_OUT')
    shutil.copy2(OUT/'entry/game/api.py',isolated/'game/api.py')
    for i,name in enumerate(FIVE,1):
        capture('entry_'+str(i),['tests/test_start_campaign_api.py::'+name],cwd=isolated)
    capture('entry_accounting',['tests/test_provider_accounting_integrity.py'],cwd=isolated)
elif mode=='regression':
    groups={
        'http':['tests/test_start_campaign_api.py','tests/test_opening_start_seam_regressions.py',
                'tests/test_scene_canon_hygiene.py'],
        'provider':['tests/test_pr_play_02_controls.py','tests/test_provider_accounting_integrity.py'],
        'structured':['tests/test_pr_br_structured_realization_envelope.py',
                      'tests/test_pr_bw_narration_only_envelope.py','tests/test_pr_by_narration_only_retry_contract.py',
                      'tests/test_pr_br_continuation18_immutable_boundary.py'],
        'ordinary':['tests/test_gm_retry.py','tests/test_social_interaction_authority.py',
                    'tests/test_pr_ef_gm_authority.py','tests/test_pr_ef_r2_social_authority.py'],
        'export':['tests/test_review_handoff.py'],
    }
    for name,args in groups.items():
        capture('regression_'+name,args,timeout=90)
elif mode=='final':
    capture('integrated',['tests/test_pr_play_05_diagnostics.py','tests/test_pr_play_04_opening_integrity.py',
                          '--junitxml=artifacts/pr_play_05/integrated.xml'],timeout=90)
    capture('provider_final',['tests/test_pr_play_02_controls.py','tests/test_provider_accounting_integrity.py'],timeout=90)
elif mode=='baseline_remaining':
    isolated=ROOT/'development/tmp/pr_play_05/pre04'
    shutil.copytree(ROOT/'tools',isolated/'tools',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(OUT/'entry/tools/atgb/accounting.py',isolated/'tools/atgb/accounting.py')
    capture('entry_remaining',['tests/test_provider_accounting_integrity.py::test_readiness_acceptance_is_not_live_execution',
        'tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid'],cwd=isolated)
