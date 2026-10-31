"""Bounded offline regression driver. Pytest live-model guard forbids providers."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

GROUPS = {
 'focused': ['test_pr_play_06_opening_budget','test_pr_play_04_opening_integrity','test_pr_play_05_diagnostics'],
 'provider': ['test_pr_play_02_controls','test_provider_accounting_integrity'],
 'structured': ['test_pr_br_structured_realization_envelope','test_pr_bw_narration_only_envelope',
                'test_pr_by_narration_only_retry_contract','test_pr_br_continuation18_immutable_boundary'],
 'ordinary': ['test_gm_retry','test_social_interaction_authority','test_pr_ef_gm_authority','test_pr_ef_r2_social_authority'],
 'opening': ['test_start_campaign_api','test_opening_start_seam_regressions','test_scene_canon_hygiene'],
 'world': ['test_world_progression_tick_integration','test_world_state','test_world_progression_backbone',
           'test_opening_scene_realization','test_scene_opening_narrative_plan','test_atgb_r2_04_question_evidence_contract',
           'test_atgb_r2_02_speech_participant_grounding'],
 'export': ['test_review_handoff'],
}
GROUPS['focused_non_http'] = GROUPS['focused']
GROUPS['entry_failures'] = [
    'test_provider_accounting_integrity.py::test_readiness_acceptance_is_not_live_execution',
    'test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid',
    'test_start_campaign_api.py::test_start_campaign_emits_opening_and_sets_started',
    'test_start_campaign_api.py::test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text',
    'test_start_campaign_api.py::test_start_campaign_promotes_valid_upstream_prepared_scene_opening',
]

if __name__ == '__main__':
    for name in sys.argv[1:] or GROUPS:
        os.environ['PR_PLAY_DIAGNOSTIC_OUT'] = 'artifacts/pr_play_06/diagnostics'
        command = [sys.executable, '-u','-m','pytest', *['tests/'+f+('' if '::' in f else '.py') for f in GROUPS[name]],
                   '-q','--tb=short','--basetemp=development/tmp/pr_play_06/'+name,
                   '--junitxml=artifacts/pr_play_06/'+name+'.xml']
        if name == 'focused_non_http':
            command += ['-k', 'not invalid_placeholder_over_http']
        if name == 'entry_failures':
            command += ['-p','tests.helpers.pr_play_06_entry_source']
        start=time.perf_counter()
        with Path('artifacts/pr_play_06/'+name+'.txt').open('w',encoding='utf-8') as log:
            try:
                result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=90)
                code,timeout=result.returncode,False
            except subprocess.TimeoutExpired:
                code,timeout=None,True
        record={'command':command,'exit':code,'timeout':timeout,'seconds':time.perf_counter()-start}
        Path('artifacts/pr_play_06/'+name+'_run.json').write_text(json.dumps(record,indent=2))
        print(name,code,'timeout',timeout,flush=True)
