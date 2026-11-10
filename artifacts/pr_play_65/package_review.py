"""Established review exporter, explicit files, credential scan and manifest QA."""
import hashlib,json,os,re,sys,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/campaigns/product_realization/pr_play_65'
from tools.build_review_handoff import build_handoff
m=json.loads((OUT/'metrics.json').read_text())
sources=[ROOT/n for n in [
 'game/integrated_investigation_narration.py','game/quarantined_investigation_narration.py',
 'game/anchored_investigation_narration.py','game/consequential_narration_validation.py',
 'game/mandatory_outcome_coverage.py','game/offline_investigation_projection.py',
 'game/api.py','game/intent_parser.py','game/exploration.py',
 'tests/test_pr_play_65_authoritative_disclosure.py','tests/test_pr_play_57_integrated_narration.py',
 'docs/DEVELOPMENT_CONSTITUTION.md','docs/validation_evidence_standard.md',
 'docs/state_authority_model.md','docs/review_handoff_standard.md','docs/NEXT_SESSION.md']]
paths=sources+list(REPORT.glob('*.md'))+[p for p in OUT.iterdir() if p.is_file() and p.suffix in {'.json','.jsonl','.xml','.txt','.py','.diff'} and p.name not in {'archive_path.txt','archive_verification.json','review_config.json'}]+list((OUT/'entry_source').glob('*.py'))+list((OUT/'quarantine_evidence').glob('*.json'))
paths.append(ROOT/'artifacts/pr_play_64/quarantine_evidence/pr_play_64_live-001.json')
for p in paths:
 if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_bytes()):raise SystemExit('Sensitive content in '+str(p.relative_to(ROOT)))
config=dict(campaign_id='pr_play_65',campaign_name='PR-PLAY-65 — Authoritative disclosure rendering',campaign_date='2026-11-04',
 purpose='Bounded engine-disclosure composition and existing gameplay transition, stopped on mandatory HTTP omission.',
 objective_status=m['verdict'],executive_summary=(REPORT/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8'),
 primary_report='development/campaigns/product_realization/pr_play_65/01_EXECUTIVE_SUMMARY.md',evidence_packets=[],max_file_bytes=33554432,
 changes=dict(production=['Two production files: existing integrated hook composition and session-gated provenance publication; flag remains default off.'],
 validation=['All existing gates retained; experimental optional surface restricted after offline missed-safety negatives. No post-holdout tuning.'],
 tooling=['Frozen holdout, exact replay, real HTTP/provider sequence, offline failure diagnosis, protected regression runner.'],
 documentation=['19 reports and session orientation.'],generated_artifacts=['Scoped entry diff, live traces/usage, authority/control snapshots, critical incident, regression and archive evidence.']),
 testing=dict(focused=f"{m['focused_regression']['passed']} passed / {m['focused_regression']['failed']} known failures; 40 new tests.",
 broader=f"{m['broader_regression']['failed']} known authority-assurance failures.",full_suite='Not run.',
 runtime_validation='5 consecutive supported HTTP actions. Existing authored exit transitions; final investigation publication omits mandatory clue. Critical stop.',
 model_runtime_boundary=f"4 real OpenAI calls / {m['provider_usage']['total_tokens']} tokens; 0 AI validated/published; 0 retries.",
 new_regressions='Experimental HTTP mandatory-disclosure omission. No new focused suite failure.',pre_existing_failures='3 focused and 9 broader known failures.'),
 decisions_requiring_human_review=['Review critical publication failure. Experiment stopped; no enablement/deployment requested.'],
 known_problems=dict(campaign_specific=['Legacy rejection suppresses trusted fallback. Four live candidates duplicate mandatory text. Holdout eight false rejections.'],
 pre_existing=['Finite validators, no client disclosure ACK, known suite failures.']),
 missing_concepts=['Publisher-inclusive guarantee of current-action mandatory disclosure; successful live optional AI publication.'],
 does_not_prove=['Successful authoritative discovery rendering end to end, universal natural-language safety, independent blind validation, human quality or official ATGB performance, browser/TCP gameplay.'],
 recommended_next_step=m['next_step'],self_contained_review_test='19 reports plus exact candidates, hook and HTTP outputs, incident, controls, hashes, usage, holdout and regressions.',
 supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='source' if p in sources else 'restricted_campaign_evidence',
 why='Scoped implementation or exact evidence; prior canonical content preserved.',human_review_required=True,behavioral_evidence=p.suffix in {'.json','.jsonl','.xml'}) for p in sorted(set(paths))])
(OUT/'review_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
prior=OUT/'previous_handoff';prior.mkdir(exist_ok=True)
for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
 p=ROOT/'handoff'/name
 if p.exists() and not (prior/name).exists():(prior/name).write_bytes(p.read_bytes())
 pending=p.with_name(name+'.pr_play_65.tmp');pending.write_bytes((stage/name).read_bytes());os.replace(pending,p)
# Client date 2026-11-04 is after New York's daylight-saving transition.
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
 for row in manifest['included_files']:
  if row.get('sha256'):assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
 count=sum('/pr_play_65/' in n and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist());assert count==19
 assert not any('.env' in n.split('/') for n in z.namelist())
 assert all(row.get('reason','').startswith('duplicate content of ') for row in result['omitted']),result['omitted']
verification=dict(path=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,
 crc_valid=True,manifest_hashes_verified=True,report_count=count,sensitive_scan='PASS',omitted=result['omitted'])
(OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
(OUT/'archive_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
print(json.dumps(verification,indent=2))
