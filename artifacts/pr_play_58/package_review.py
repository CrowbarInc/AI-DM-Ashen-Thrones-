"""Use established explicit-selection handoff builder; verify archive bytes."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tools.build_review_handoff import build_handoff
from evaluate import read, write, hashes

def main():
    assert hashes()==read('implementation_frozen.json')['hashes']
    assert not read('integrity.json')['unexpected_changes']
    out=ROOT/'artifacts/pr_play_58'
    # Exact original decision bytes, including raw text embedded in audit spans.
    (out/'previous_decisions_original.json').write_bytes((ROOT/'artifacts/pr_play_57/validation_decisions.json').read_bytes())
    examples=[]
    for row in read('fixed_results.json'):
        examples.append({'example_id':row['id'],'campaign':'PR-PLAY-58','run_id':'PR57-'+row['id'],
            'turn_index':2 if row['id'].startswith('C') else 1,'player_input':row['request']['player_action'],
            'player_input_classification':['runtime_discovered'],
            'prior_context':'Previously examined board.' if row['id'].startswith('C') else 'Fresh isolated investigation.',
            'authorized_context':row['request'],'exact_gm_output':row['text'],
            'publication':'Historical quarantined provider prose, not player-facing output.',
            'previous_result':row['previous_pipeline_reexecuted'],'actual_result':row['validation'],
            'human_review':{'status':'PENDING','rationale':'Same-agent provisional reading; external confirmation not claimed.'},
            'source_artifact_path':'artifacts/pr_play_58/fixed_results.json'})
    write('evidence_manifest.json',{'campaign':{'campaign_id':'pr_play_58','run_count':8,'turn_count':8,
        'gm_boundary':'Replay of preserved historical candidate text through local validation only.'},
        'evidence_scope':'historical_runtime_and_synthetic_semantic_controls','examples':examples,
        'selected_evidence':{'representative_success':{'example_id':'D1'},'representative_failure':{'example_id':'A1'}},
        'holdout_failure':'holdout_results.json H41: unsupported persistent gate opening accepted.'})
    (out/'evidence_summary.md').write_text('# Behavioral evidence\n\nEight original provider candidates replayed exactly; no new provider calls or gameplay benchmark. 43 development controls and one 50-case frozen holdout evaluation. H41 is a critical false acceptance; C verdict. Human review remains pending. Exact authority, prose and all layer audits are retained in fixed_results.json, development_results.json and holdout_results.json.\n',encoding='utf-8')
    for name in ['development','holdout']:
        rows=read(name+'_results.json')['rows']
        write(name+'_error_examples.json',{
            'critical_false_acceptances':[r for r in rows if r['group'] in ('missing','contradictory','expansion') and r['actual']=='PASS'],
            'false_rejections':[r for r in rows if r['group']=='legitimate' and r['actual']!='PASS'],
            'review_required':[r for r in rows if r['actual']=='REVIEW_REQUIRED']})
    sources=[ROOT/p for p in ['game/mandatory_outcome_coverage.py','game/integrated_investigation_narration.py',
        'game/consequential_narration_validation.py','game/anchored_investigation_narration.py',
        'game/offline_investigation_projection.py','game/quarantined_investigation_narration.py',
        'tests/pr_play_58_development.py','tests/test_pr_play_58_semantic_coverage.py',
        'tests/test_pr_play_57_integrated_narration.py']]
    paths=[p for p in out.iterdir() if p.is_file() and p.name not in {'archive_path.txt','archive_verification.json','review_config.json'}]+sources
    # Explicit payload only; no environment/configuration or hidden campaign data.
    hits=[p.relative_to(ROOT).as_posix() for p in paths if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_bytes())]
    assert not hits, 'Sensitive payload signature found'
    write('export_scan.json',{'files_scanned':len(paths),'private_key_or_provider_key_signatures':hits,
        'selection':'Explicit campaign evidence and relevant source; .env, caches and unrelated data excluded.'})
    paths=sorted(set(paths+[out/'export_scan.json']))
    config= json.loads((ROOT/'artifacts/pr_play_57/review_config.json').read_text(encoding='utf-8'))
    config.update(campaign_id='pr_play_58',campaign_name='PR-PLAY-58 — Semantic Outcome Coverage',campaign_date='2026-11-03',
        purpose='Recognize authorized semantic paraphrases while preserving quarantine and combined authority gates.',
        objective_status='C — FAIL / REMEDIATION REQUIRED',executive_summary=(out/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8'),
        primary_report='artifacts/pr_play_58/01_EXECUTIVE_SUMMARY.md',evidence_packets=['artifacts/pr_play_58'],
        changes={'production':['No gameplay or publication change.'],
            'validation':['Bounded movement/uncertainty/status coverage leaf; narrow consequential assertion controls in existing PR55 owner.'],
            'tooling':['Frozen corpora, one-pass holdout runner, baseline replay, local measurements and integrity verification.'],
            'documentation':['18 requested campaign reports.'],'generated_artifacts':['Raw original samples, all layer audits and review export.']},
        testing={'focused':'601 passed / 3 known failures of 604; final frozen-source lane 204/204 passed (overlaps focused lane).',
            'broader':'PR55 holdout wrapper passed; nine known authority-assurance metadata failures reproduced.',
            'full_suite':'Not executed.','runtime_validation':'Eight fixed local sample replays, 43 development controls and one frozen 50-case holdout pass.',
            'model_runtime_boundary':'No provider requests; quarantine remains mandatory.','new_regressions':'No unexplained new regression-test failure; H41 semantic false acceptance remains.',
            'pre_existing_failures':'Three focused failures and nine hard_validation_attempt_1 failures.'},
        decisions_requiring_human_review=['Review C verdict and preserved H41 failure; no action or player-facing enablement requested.'],
        known_problems={'campaign_specific':['H41 unsupported permanent gate opening passes; H12 legitimate repeat is reviewed; D15 legacy rejection remains.'],
            'pre_existing':['Three focused and nine broader known regression failures.']},
        missing_concepts=['General assertion entailment, grammatical scope and robust temporal/coreference reasoning.'],
        does_not_prove=['Semantic completeness, independent blind holdout validation, live gameplay quality, ATGB score or safe player-facing narration.'],
        recommended_next_step='Repair unsupported persistent-consequence detection exposed by H41 in a subsequent bounded validation cycle; preserve quarantine.',
        self_contained_review_test='All 18 reports, fixed corpora/authority, result audits, incremental source diff and regression summaries present; ZIP CRC and included-file hashes verified.',
        supporting_files=[{'path':p.relative_to(ROOT).as_posix(),'role':'source' if p in sources else 'campaign_evidence',
            'why':'Explicit PR58 change, original evidence or validation result.','human_review_required':True,
            'behavioral_evidence':p.suffix=='.json'} for p in paths])
    write('review_config.json',config)
    config['configuration_source']='artifacts/pr_play_58/review_config.json'
    stage=out/'export_stage'
    result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
    for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
        pending=ROOT/'handoff'/('PR_PLAY_58_pending_'+name)
        pending.write_bytes((stage/name).read_bytes())
        pending.replace(ROOT/'handoff'/name)
    # Nov 3 client context is EST. No new timezone dependency on Windows.
    timestamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
    archive=ROOT/'handoff'/f'CURRENT_REVIEW({timestamp}).zip'
    with archive.open('xb') as f: f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
        for row in manifest['included_files']:
            if row.get('sha256'):
                assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
        assert sum(bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist())==18
        assert not any('.env' in n.split('/') for n in z.namelist())
    write('archive_verification.json',{'path':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'bytes':archive.stat().st_size,'crc_valid':True,'all_manifest_hashes_valid':True,'reports':18,
        'stable_matches':archive.read_bytes()==(ROOT/'handoff/CURRENT_REVIEW.zip').read_bytes(),'omitted':result['omitted']})
    (out/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
    print(json.dumps(read('archive_verification.json'),indent=2))

if __name__=='__main__':main()
