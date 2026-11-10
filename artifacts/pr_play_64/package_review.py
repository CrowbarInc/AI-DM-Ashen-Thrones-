"""Explicit-source handoff export and manifest/CRC verification."""
import hashlib,json,os,re,sys,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.build_review_handoff import build_handoff
OUT=ROOT/'artifacts/pr_play_64';REPORT=ROOT/'development/campaigns/product_realization/pr_play_64'
m=json.loads((OUT/'metrics.json').read_text(encoding='utf-8'))
sources=[ROOT/n for n in ['game/consequential_narration_validation.py','game/mechanical_claims.py','game/integrated_investigation_narration.py','game/mandatory_outcome_coverage.py','game/anchored_investigation_narration.py','game/offline_investigation_projection.py','game/quarantined_investigation_narration.py','game/authorized_information.py','game/persistent_consequence_claims.py','tests/pr_play_64_development.py','tests/test_pr_play_64_discovery_language.py','tests/test_pr_play_63_disclosure.py','tests/test_pr_play_57_integrated_narration.py']]
paths=sources+list(REPORT.glob('*.md'))+[p for p in OUT.iterdir() if p.is_file() and p.suffix in {'.json','.jsonl','.xml','.txt','.py','.diff'} and p.name not in {'archive_path.txt','archive_verification.json'}]+list((OUT/'entry_source').glob('*.py'))+list((OUT/'quarantine_evidence').glob('*.json'))
paths+= [ROOT/n for n in ['docs/review_handoff_standard.md','docs/testing/protected_replay_manifest.md','docs/testing/replay_governance_contract.md','development/reports/atgb_05_baseline_preservation.md']]
for p in paths:
 if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_bytes()):raise SystemExit('Sensitive content in '+str(p.relative_to(ROOT)))
config={'campaign_id':'pr_play_64','campaign_name':'PR-PLAY-64 — Authorized discovery language repair','campaign_date':'2026-11-04','purpose':'Targeted historical narration rejection repair with preserved authority and honest remaining live limitation.','objective_status':m['verdict'],'executive_summary':(REPORT/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8'),'primary_report':'development/campaigns/product_realization/pr_play_64/01_EXECUTIVE_SUMMARY.md','evidence_packets':[],'max_file_bytes':33554432,'changes':{'production':['Finite reported-route carrier handling, finite observation idioms, exact learned-fact complement comparison, separate prior-disclosure authorization.'],'validation':['No mandatory coverage or persistent-state relaxation. Historical route and extended gate candidate FAIL to PASS.'],'tooling':['30-case complete-pipeline development, 40-case one-shot frozen holdout, supported HTTP publication and 12 injected failures.'],'documentation':['18 numbered reports.'],'generated_artifacts':['Raw historical/live traces, state/control comparison, provider accounting, regression XML/logs, scoped diffs, input/source hashes.']},'testing':{'focused':'808 passed, same 3 known failures; 37 new tests included.','broader':'PR55 wrapper passes; same 9 hard_validation_attempt_1 failures.','full_suite':'Not executed.','runtime_validation':'3 supported HTTP application actions; 2 live attempts; 1 AI publication, 2 fallbacks. 12/12 assessed faults; state and session isolation pass.','model_runtime_boundary':'2 OpenAI requests, gpt-4.1-mini-2025-04-14; 895 input + 44 output = 939 tokens; zero retries.','new_regressions':'No new suite failures; a further legitimate live carrier remains rejected. Holdout 39/40 full expectations, 40/40 decisions/publication; 0 false acceptances/rejections.','pre_existing_failures':'3 focused and 9 broader unchanged.'},'decisions_requiring_human_review':['Review partial verdict and bounded next step. No enablement or deployment approval requested.'],'known_problems':{'campaign_specific':['Fresh live discovery phrasing with carefully and discover that still falls back.','Frozen H18 expected coverage PASS but contradictory route correctly returns REVIEW_REQUIRED; expectations unchanged.'],'pre_existing':['Finite heuristic validators; browser gameplay and natural choices unverified; known regression failures.']},'missing_concepts':['Natural branching and typed direct follow-up remain deferred.'],'does_not_prove':['Universal discovery-language support, arbitrary hidden-paraphrase safety, browser or external TCP interaction, independent blind validation, authenticated human quality or general RPG competence.'],'recommended_next_step':m['next_step'],'self_contained_review_test':'18 reports and explicit originals, source deltas, full validation/publication traces, holdout hash/results, live usage/state, failures and regression summaries packaged.','supporting_files':[{'path':p.relative_to(ROOT).as_posix(),'role':'source' if p in sources else 'restricted_campaign_evidence','why':'Scoped implementation, exact evidence, governance or report; no canonical fixture rewrite.','human_review_required':True,'behavioral_evidence':p.suffix in {'.json','.jsonl','.xml'}} for p in sorted(set(paths))]}
(OUT/'review_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
# Preserve existing stable handoff files before replacing their authorized pointers.
prior=OUT/'previous_handoff';prior.mkdir(exist_ok=True)
for n in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
 p=ROOT/'handoff'/n
 if p.exists() and not (prior/n).exists():(prior/n).write_bytes(p.read_bytes())
 pending=p.with_name(n+'.pr_play_64.tmp')
 pending.write_bytes((stage/n).read_bytes())
 os.replace(pending,p)
# Client date is 2026-11-04, after New York's daylight-saving transition.
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S');archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
 for row in manifest['included_files']:
  if row.get('sha256'):assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
 count=sum('/pr_play_64/' in n and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist());assert count==18
 assert not any('.env' in n.split('/') for n in z.namelist())
 assert all(row.get('reason','').startswith('duplicate content of ') for row in result['omitted']),result['omitted']
verification={'path':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'crc_valid':True,'report_count':count,'manifest_hashes_verified':True,'sensitive_pattern_scan':'PASS','omitted':result['omitted']}
(OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8');(OUT/'archive_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8');print(json.dumps(verification,indent=2))
