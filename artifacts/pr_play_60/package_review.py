"""Explicit standard export; verify CRC and packaged canonical hashes."""
import hashlib,json,re,sys,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.build_review_handoff import build_handoff
from artifacts.pr_play_60.prepare import OUT,write,hashes,SOURCES
REPORT=ROOT/'development/campaigns/product_realization/pr_play_60'
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
assert hashes()==read('implementation_frozen.json')
assert not read('integrity.json')['unexpected_changes']
summary=(REPORT/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8')
evidence=summary+'''\n\nRepresentative Success: No example observed in this campaign.

Boundary Success: D01, exact D25 prose with a separately supplied resolver key delta; all complete validators PASS. Synthetic positive control, not live gameplay.

Representative Failure: No example observed in this campaign.

Severe / Worst Failure: H03, authorized sealed-letter acquisition rejected by legacy ungrounded_authoritative_rule despite semantic and coverage PASS. H26 is also retained with its missing typed NPC authority.

Evaluator Disagreement: No human adjudication recorded. Both frozen expected/actual mismatches remain inspectable in holdout_error_examples.json; no expectation was rewritten.

Unexpected / Unclassified Behavior: The historical D25 record has no structured authority to recover. Exact replay and explicit-delta control remain distinct.

Stress Probe: H11-H20, unauthorized inventory consequences; all blocked. Synthetic negative controls, not representative play.

Runtime boundary: local complete validators and a two-action provider-disabled HTTP off/on comparison. Ordinary-GM follow-up wording and integrated candidates are local stubs. Four total HTTP actions across the two comparison runs. No live AI-GM quality or ATGB benchmark claim. All human review remains UNREVIEWED.
'''
(OUT/'evidence_summary.md').write_text(evidence,encoding='utf-8')
sources=SOURCES+['game/persistent_consequence_claims.py','game/quarantined_investigation_narration.py','game/narration_authorization.py','game/resolution_contract.py','tests/test_pr_play_60_inventory_projection.py','tests/test_pr_play_60_gameplay_readiness.py','tests/test_pr_play_57_integrated_narration.py','tests/pr_play_59_development.py','tests/pr_play_58_development.py','docs/NEXT_SESSION.md','artifacts/pr_play_59/h41_original.json','artifacts/pr_play_59/combined_positive_preexisting.json']
paths=[p for p in OUT.iterdir() if p.is_file() and p.name not in {'archive_path.txt','archive_verification.json','review_config.json','report_generation.txt'}]+list(REPORT.glob('*.md'))+[ROOT/p for p in sources]
hits=[p.relative_to(ROOT).as_posix() for p in paths if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_bytes())]
assert not hits
write('export_scan.json',{'files_scanned':len(paths),'private_key_or_provider_key_signatures':hits,'selection':'Explicit PR60 evidence/source/reports and exact historical reproductions; no local environment/config credentials.'})
paths.append(OUT/'export_scan.json')
config={'campaign_id':'pr_play_60','campaign_name':'PR-PLAY-60 — Authorized Inventory Projection and Gameplay Readiness','campaign_date':'2026-11-03','purpose':'Repair existing resolver-delta projection and assess complete validation without enabling player narration.','objective_status':'B — PARTIAL / FURTHER INVESTIGATION REQUIRED','executive_summary':summary,'primary_report':'development/campaigns/product_realization/pr_play_60/01_EXECUTIVE_SUMMARY.md','evidence_packets':['artifacts/pr_play_60'],'max_file_bytes':33554432,
'changes':{'production':['Six existing read-side projection/validation files; ordinary publication and inventory hooks remain isolated.'],'validation':['Explicit inventory deltas, quantity retention, bounded requested acquisition wording and mandatory effect coverage.'],'tooling':['34 development cases, one frozen 60-case end-to-end holdout, prior-corpus replays, state comparisons and measurements.'],'documentation':['21 numbered reports and session handoff.'],'generated_artifacts':['All validator traces, exact D25 historical/explicit distinction, H41, test logs, matrices, hashes and scoped diff.']},
'testing':{'focused':'732 passed / 3 known failures of 735; zero errors/skips/new failures.','broader':'PR55 wrapper 1/1; 9 known hard_validation_attempt_1 metadata failures.','full_suite':'Not executed.','runtime_validation':'Two-action provider-disabled HTTP off/on comparison; synthetic complete-pipeline development 34/34 and frozen holdout 58/60.','model_runtime_boundary':'Zero provider requests/tokens; local ordinary-GM and narration stubs; quarantine never promotes.','new_regressions':'No new final-source test regressions. Two frozen positive false rejections preserved.','pre_existing_failures':'3 focused/9 broader; historical text-only D25; existing PR58 positive rejections.'},
'decisions_requiring_human_review':['Review B verdict and separately authorize any PR-PLAY-61 restricted disclosure-only experiment; no enablement performed.'],
'known_problems':{'campaign_specific':['H03 authorized sealed letter triggers legacy rule; H26 text-authorized NPC death lacks typed NPC change.','Historical exact D25 remains rejected because it contains no structured resolver delta; explicit-delta control passes.'],'pre_existing':['3 focused, 9 broader metadata failures; PR58 D15/H12 positive rejections.']},
'missing_concepts':['Native investigation inventory mechanics, transfer/source/destination/post-state authority and independent blind evaluation.'],
'does_not_prove':['Exact historical D25 recovery, general semantic completeness, live AI-GM quality/latency, ATGB score or ordinary-player rollout readiness.'],
'recommended_next_step':'PR-PLAY-61 controlled player-facing investigation, separately authorized, disclosure-only and bounded by deterministic fallback.',
'self_contained_review_test':'21 reports, exact candidates, both D25 traces, all layer inputs/decisions, holdout hash and one-execution marker, regression evidence, state comparisons and source diff included.',
'supporting_files':[{'path':p.relative_to(ROOT).as_posix(),'role':'source' if p.relative_to(ROOT).as_posix() in sources else 'campaign_evidence','why':'PR60 implementation, provenance, inspectable result or regression evidence.','human_review_required':True,'behavioral_evidence':p.suffix=='.json'} for p in sorted(set(paths))]}
write('review_config.json',config);config['configuration_source']='artifacts/pr_play_60/review_config.json'
stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:(ROOT/'handoff'/name).write_bytes((stage/name).read_bytes())
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
 for row in manifest['included_files']:
  if row.get('sha256'):assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
 reports=sum('/pr_play_60/' in n and bool(re.search(r'/\d\d_[A-Z_0-9]+\.md$',n)) for n in z.namelist())
 assert reports==21
 assert not any('.env' in n.split('/') for n in z.namelist())
write('archive_verification.json',{'path':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'crc_valid':True,'manifest_hashes_valid':True,'reports':reports,'omitted':result['omitted'],'frozen_sources_match':hashes()==read('implementation_frozen.json')})
(OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
print(json.dumps(read('archive_verification.json'),indent=2))
