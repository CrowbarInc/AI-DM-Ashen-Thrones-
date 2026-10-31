"""Verify offline provenance and export the explicit review allowlist."""
from build_review import *
import shutil
import zipfile
import io

sys.path.insert(0,str(ROOT))
from tools.validation_evidence import validate_packet
from tools.build_review_handoff import build_handoff

before=read('artifacts/atgb/atgb_r2_01/entry_hashes.json')
changed=[name for name,sha in before.items() if not (ROOT/name).is_file() or digest(ROOT/name)!=sha]
assert not changed, changed
dump('integrity_verification.json',{'protected_file_count':len(before),'changed_or_missing':changed,
    'scope':'Entry-existing game, data, tests, experiments, prior ATGB artifacts, final PR-EG R5 artifacts and prior development reports; caches excluded.',
    'production_prompt_schema_unchanged':True,'frozen_atgb_unchanged':True,'canonical_gameplay_state_unchanged':True,
    'prior_experimental_candidates_unchanged':True,'provider_calls_this_pass':0,'network_diagnostics_this_pass':0,
    'gameplay_executions_this_pass':0,'commit_push_operations':0})
packet=read('artifacts/validation_evidence/atgb_r2_01/evidence_manifest.json')
assert not validate_packet(packet)
assert len(packet['examples'])==19 and packet['campaign']['run_count']==6
traces=read('artifacts/atgb/atgb_r2_01/representative_traces.json')
for t in traces:
    assert digest(ROOT/t['source'])==t['source_sha256']
    assert digest(ROOT/t['log_source'])==t['log_sha256']
scores=read('artifacts/atgb/atgb_r2_01/prioritization_scores.json')
assert [x['weighted_score'] for x in scores['rows']]==[4.3,4.,3.8,3.5,3.95]

excerpts=[]
for name, spans in {
    'game/interaction_completion.py':[(82,106),(492,499),(627,650)],
    'game/ordinary_semantic_ownership.py':[(526,528),(615,627),(643,699),(726,802),(839,854)],
    'game/conversational_orchestration.py':[(308,345),(461,515),(573,630)],
    'game/live_chat_interpretation.py':[(323,362),(490,505)],
}.items():
    lines=(ROOT/name).read_text(encoding='utf-8').splitlines()
    excerpts.append(f'## {name} (SHA-256 {digest(ROOT/name)})\n')
    for lo,hi in spans:
        excerpts.append('```text\n'+'\n'.join(f'{n}: {lines[n-1]}' for n in range(lo,min(hi,len(lines))+1))+'\n```\n')
(OUT/'source_excerpts.md').write_text('# Current-source excerpts\n\nOne-based current working-tree lines; static reconstruction, not original historical instruction-pointer trace.\n\n'+'\n'.join(excerpts),encoding='utf-8')

sources=[
    'docs/DEVELOPMENT_CONSTITUTION.md','docs/NEXT_SESSION.md','docs/validation_evidence_standard.md',
    'docs/product_realization_validation.md','docs/review_handoff_standard.md','docs/state_authority_model.md',
    'development/reports/atgb_05_baseline_preservation.md',
    'development/reports/atgb_r1_01_s08_2_causal_trace.md',
    'development/reports/atgb_r1_02/08_final_verdict.md',
    'development/reports/atgb_r1_03/08_final_verdict.md',
    'development/reports/atgb_r1_04/08_final_verdict.md',
    'development/reports/atgb_r1_05/08_final_verdict.md',
    'development/reports/atgb_r1_06/06_pr_eg_comparison_and_causal_verdict.md',
    'development/reports/atgb_r1_06/08_final_verdict.md',
    'development/reports/atgb_r1_07/07_change_review.md',
    'development/reports/atgb_r1_07/08_final_verdict.md',
    'development/reports/atgb_r1_08/08_final_verdict.md',
    'development/reports/atgb_r1_09/08_final_verdict_and_closure_recommendation.md',
    'artifacts/atgb/atgb_05a/assessment/ATGB_04_review_judgments.json',
    'artifacts/atgb/atgb_05a/assessment/ATGB_04_review_summary.md',
    'artifacts/pr_ea_conversational_orchestration/REVIEW.md',
    'artifacts/pr_eb_conversational_continuity/REVIEW.md',
    'artifacts/pr_ef_gm_authority/03_CONVERSATIONAL_AUTHORITY_CONTRACT.md',
    'artifacts/pr_ef_gm_authority/11_REMAINING_ISSUES.md',
    'artifacts/pr_ef_r4/03_AUTHORIZATION_CONTRACT_DESIGN.md',
    'artifacts/pr_ef_r4/05_AMBIGUOUS_TARGET_INTEGRITY.md',
    'artifacts/pr_ef_r4/17_FINAL_RECOMMENDATION.md',
    'artifacts/pr_eg_r6_r4_r1/38_FINAL_VERDICT.md',
    'artifacts/pr_eg_r6_r5/baseline.jsonl','artifacts/pr_eg_r6_r5/summary.json',
    'artifacts/pr_eg_r6_r5/first_failures.json',
    'artifacts/pr_eg_r6_r5/03_PRODUCTION_PIPELINE_MAP.md',
    'artifacts/pr_eg_r6_r5/07_CONVERSATIONAL_CONTEXT.md',
    'artifacts/pr_eg_r6_r5/11_PRODUCTION_BASELINE.md',
    'artifacts/pr_eg_r6_r5/20_AUTHORIZED_PLAN_INTERVENTION.md',
    'artifacts/pr_eg_r6_r5/22_EXPRESSION_CONTROL.md',
    'artifacts/pr_eg_r6_r5/25_FIRST_FAILURE_ATTRIBUTION.md',
    'artifacts/pr_eg_r6_r5/30_PERFORMANCE.md',
    'artifacts/pr_eg_r6_r5/32_REPAIR_PRIORITIZATION.md',
    'artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md',
    'game/interaction_completion.py','game/ordinary_semantic_ownership.py',
    'game/conversational_orchestration.py','game/live_chat_interpretation.py','game/conversational_continuity.py',
]
for number in [13,14,15,16,17,18,19,21,27,34]:
    sources.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'artifacts/pr_eg_r6_r5').glob(f'{number:02d}_*.md'))
sources.extend(p.relative_to(ROOT).as_posix() for p in REPORTS.glob('*.md'))
sources.extend(p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.suffix in {'.md','.json','.csv','.txt','.py'} and p.name not in {'review_config.json','review_verification.json','source_inventory.json','repository_status_after.txt','payload_verification.json'})
for base in sorted({str(Path(t['source']).parent).replace('\\','/') for t in traces}):
    sources.extend([base+'/result.json',base+'/transcript.md'])
sources.extend(t['log_source'] for t in traces)
for part in ['visible','held_out']:
    sources.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'data/validation/atgb'/part).glob('*.json'))
sources=sorted(set(sources))
assert all((ROOT/p).is_file() for p in sources)

# No credential/local config files are selected. Check the selected content, not any secret source.
patterns=[re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}'),re.compile(rb'\bAKIA[A-Z0-9]{16}\b'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
hits=[]
for name in sources:
    raw=(ROOT/name).read_bytes()
    for n,pattern in enumerate(patterns):
        if pattern.search(raw): hits.append({'path':name,'pattern_index':n})
assert not hits,hits
dump('payload_verification.json',{'protected_file_count':len(before),'trace_count':19,'scenario_count':6,
    'trace_hashes_verified':True,'rubric_counts_recomputed':True,'weighted_scores_recomputed':True,
    'standard_evidence_packet_errors':validate_packet(packet),'secret_pattern_hits':hits,
    'secret_scan_scope':'Explicit selected payloads only; no credential or local configuration source read.',
    'limitation':'Pattern scan is supplementary; explicit allowlist excludes local configuration and credential sources.'})
sources.append('artifacts/atgb/atgb_r2_01/payload_verification.json')
(OUT/'repository_status_after.txt').write_text(git('status','--short','--untracked-files=all'),encoding='utf-8')
sources.append('artifacts/atgb/atgb_r2_01/repository_status_after.txt')
(OUT/'orientation_change.diff').write_text(git('diff','--','docs/NEXT_SESSION.md'),encoding='utf-8')
sources.append('artifacts/atgb/atgb_r2_01/orientation_change.diff')
dump('source_inventory.json',[{'path':p,'sha256':digest(ROOT/p),'size_bytes':(ROOT/p).stat().st_size} for p in sources])
sources.append('artifacts/atgb/atgb_r2_01/source_inventory.json')

config={'campaign_id':'atgb_r2_01','campaign_name':'ATGB-R2-01 — Player-Facing Conversational Failure Prioritization',
    'campaign_date':'2026-10-19','purpose':'Offline evidence-driven prioritization; implementation/provider authority NONE.',
    'objective_status':'A — Implementation target established (prioritization only)',
    'executive_summary':'Recommend one bounded ATGB-R2-02 repair: speech-participant grounding at the existing shared addressee owner. S03.3/S05.3 raw interpretations select the runner, but the host asks which person. F1 4.30, F2 4.00, F3 3.80, F4 3.50; F5 comparison only. No implementation or new live evidence. R1-07 remains pending live acceptance. Historical baseline figures preserved.',
    'changes':{'production':[],'validation':['Historical count/provenance verification and unmodified isolated syntax-helper probe; no gameplay/evaluator changes.'],
    'tooling':['Evidence-local extraction/report/package scripts only.'], 'documentation':['Eight reports and concise canonical orientation update.'],
    'generated_artifacts':['Failure matrix, weighted scores, trace extracts, historical standard packet, source inventory, protected hashes and review ZIP.']},
    'testing':{'focused':'19 historical trace extracts across six scenarios; 37 imported judgments and 164 PR-EG rows recounted; weights and protected bytes verified.',
    'broader':'Not run; read-only investigation.','full_suite':'Not run.',
    'runtime_validation':'No fresh gameplay execution. Pure unmodified AST-selected regex helpers evaluated without importing gameplay modules.',
    'model_runtime_boundary':'Saved historical production captures only; zero current provider calls or network diagnostics.',
    'new_regressions':'No product changes; protected bytes verified. No repair-effect claim.',
    'pre_existing_failures':'Historical inadequacy and two uncertain authority cases preserved; latest R1-07 live effect unknown.'},
    'known_problems':{'campaign_specific':['S05 topic remains ambiguous; exact original request messages unavailable for selected initial ATGB captures.'],
    'pre_existing':['Unresolved provider connectivity, human attestation pending, extensive dirty tree and historical test failures.']},
    'decisions_requiring_human_review':['Accept or revise F1 repair priority and report 07 bounded ATGB-R2-02 scope. No implementation/live authority carries forward.'],
    'missing_concepts':[],
    'does_not_prove':['Improved gameplay, live repair effectiveness, independent generalization, current benchmark performance, full authority safety or full-suite green.'],
    'recommended_next_step':'Stop for external review. Proposed ATGB-R2-02 is existing-owner speech-participant grounding only; do not implement in this pass.',
    'primary_report':'development/reports/atgb_r2_01/08_final_verdict_and_handoff.md',
    'evidence_packets':['artifacts/validation_evidence/atgb_r2_01'],
    'self_contained_review_test':'Eight reports, exact original model/host/response excerpts, canonical source hashes, matrix, scores, state/routing limits and protected-byte verification included. Historical excerpts remain unattested; no synthetic PASS assigned.',
    'configuration_source':'artifacts/atgb/atgb_r2_01/review_config.json',
    'supporting_files':[{'path':p,'role':'source_or_review_evidence','why':'Explicit support for historical reconstruction, prioritization, ownership, safety or provenance.','behavioral_evidence':p.endswith(('result.json','transcript.md','session_log.jsonl','representative_traces.json')),'human_review_required':True} for p in sources]}
dump('review_config.json',config)

# Preserve the user's pre-existing generated mirrors before their standard replacement.
backup=ROOT/'development/tmp/atgb_r2_01/preexisting_handoff'
backup.mkdir(parents=True,exist_ok=True)
for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
    p=ROOT/'handoff'/name
    if p.is_file() and not (backup/name).exists():shutil.copyfile(p,backup/name)

now=datetime.now(timezone.utc)
result=build_handoff(config,root=ROOT,output_dir=ROOT/'handoff',generated_at=now.isoformat(),archive_history=True)
zip_path=Path(result['zip_path'])
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    names=z.namelist()
    assert all('support/development/reports/atgb_r2_01/'+p.name in names for p in REPORTS.glob('*.md'))
    manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
    for row in manifest['included_files']:
        bundle=row.get('bundle_path')
        if bundle and bundle in names and row.get('sha256'):
            assert hashlib.sha256(z.read(bundle)).hexdigest()==row['sha256']
    for name in names:
        for pattern in patterns: assert not pattern.search(z.read(name)), name
# Client date is within US daylight time (America/New_York UTC-04 on 2026-10-19).
stamp=now.astimezone(timezone(timedelta(hours=-4))).strftime('%Y%m%d-%H%M%S')
timestamped=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
shutil.copyfile(zip_path,timestamped)
dump('review_verification.json',{'zip':timestamped.relative_to(ROOT).as_posix(),'sha256':digest(timestamped),
    'bytes':timestamped.stat().st_size,'file_count':len(names),'crc_errors':None,'payload_hash_check':'passed',
    'secret_pattern_hits':0,'eight_reports_present':True,'protected_file_count':len(before),
    'omitted':result['omitted'],'timestamp_timezone':'America/New_York',
    'stop':'Await external review; no ATGB-R2-02 execution.'})
print(json.dumps({'zip':str(timestamped),'bytes':timestamped.stat().st_size,'files':len(names),'protected_files':len(before),'omitted_count':len(result['omitted'])}))
