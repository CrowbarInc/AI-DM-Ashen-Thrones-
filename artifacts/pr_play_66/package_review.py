"""Established CURRENT_REVIEW exporter; explicit selection, hashes, CRC and content scan."""
import sys,json,hashlib,os,re,zipfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent;REPORT=ROOT/'development/campaigns/product_realization/pr_play_66'
from tools.build_review_handoff import build_handoff
m=json.loads((OUT/'metrics.json').read_text(encoding='utf-8'))
sources=[ROOT/n for n in ['game/api.py','game/quarantined_investigation_narration.py','game/integrated_investigation_narration.py','game/anchored_investigation_narration.py','game/mandatory_outcome_coverage.py','game/consequential_narration_validation.py','game/state_channels.py','tests/test_pr_play_66_publication.py','tests/test_pr_play_49_anchored_narration.py','tests/test_pr_play_65_authoritative_disclosure.py','docs/DEVELOPMENT_CONSTITUTION.md','docs/validation_evidence_standard.md','docs/state_authority_model.md','docs/review_handoff_standard.md','docs/NEXT_SESSION.md']]
paths=sources+list(REPORT.glob('*.md'))+[p for p in OUT.iterdir() if p.is_file() and p.suffix in {'.json','.xml','.txt','.py','.diff'} and p.name not in {'archive_path.txt','archive_verification.json','review_config.json'}]+list((OUT/'entry_source').glob('*'))+[ROOT/'artifacts/pr_play_65/critical_incident.json']
for p in paths:
    if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_bytes()):raise SystemExit('Sensitive content in '+str(p.relative_to(ROOT)))
config=dict(campaign_id='pr_play_66',campaign_name='PR-PLAY-66 — Mandatory disclosure publication integrity',campaign_date='2026-11-04',
 purpose='Narrow current-action publication repair and exact historical/final-HTTP verification.',objective_status=m['verdict'],executive_summary=(REPORT/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8'),
 primary_report='development/campaigns/product_realization/pr_play_66/01_EXECUTIVE_SUMMARY.md',evidence_packets=['artifacts/validation_evidence/pr_play_66'],max_file_bytes=134217728,
 changes=dict(production=['Existing API publisher and quarantine module: request-local authority provenance, explicit text selection, final mandatory invariant with one deterministic recovery.'],validation=['Semantic validators unchanged; new HTTP matrix and updated obsolete PR49 static integration assertion.'],tooling=['Exact replay, frozen HTTP holdout, matched-operation evaluation audit, actual TCP gameplay/disconnect capture, disabled controls, protected regression.'],documentation=['18 campaign reports, behavioral evidence packet and NEXT_SESSION.'],generated_artifacts=['Before/after raw HTTP bodies, state/candidate/validation traces, unchanged frozen results/hash, latency, diffs, regression and review manifests.']),
 testing=dict(focused=f"{m['regression']['focused']['passed']} passed / {m['regression']['focused']['failed']} known failures; 45 new HTTP cases.",broader='9 known authority-assurance failures; full suite not run. Final aggregate rerun interrupted on critical hidden-payload leak.',full_suite='Not run.',runtime_validation='Five consecutive supported actions over actual localhost TCP. Exact historical milestone also replayed through TestClient before and after repair.',model_runtime_boundary='Zero live requests/tokens; one synthetic accepted/published presentation and three fallbacks in TCP sequence. No fallback provider call.',new_regressions='Critical preexisting full-body hidden leak confirmed before/after/disabled. Additional initial regression failures: '+str(m['regression']['focused']['new_failures']),pre_existing_failures='3 focused and 9 broader known failures. Initial transient malformed HTTP 500 preserved; did not reproduce in targeted diagnostics. Aggregate rerun interrupted.'),
 decisions_requiring_human_review=['Critical experimental stop; repair full-payload hidden visibility before future execution. No deployment/enablement requested. No deploy/commit/push.'],
 known_problems=dict(campaign_specific=['CRITICAL STOP: hidden values survive final JSON state-bearing fields in entry/disabled/repaired paths. 41 matrix responses and five TCP actions leak; narration-only safety assertions were insufficient.','Frozen holdout raw 38/40 due two mismatched authoritative-operation controls; 40/40 publication decisions. Separate matched-operation audit, not a corrected holdout score.','Initial aggregate malformed-output 500 remains unclassified after nonreproduction.','No live-provider acceptance/naturalness validation.'],pre_existing=['3 focused/9 broader known failures; finite validators; no durable client ACK; legacy empty-resolver HTTP 200 refusal.']),
 missing_concepts=['Natural optional presentation and delivery acknowledgement remain outside this repair.'],does_not_prove=['Universal semantic safety, independent blind validation, human/browser gameplay quality, official ATGB score, successful client delivery after disconnect or serialization error.'],recommended_next_step=m['next_step'],self_contained_review_test='18 reports, original failed/repaired final HTTP text, full fixtures/outcomes/state, frozen hash/results plus audit, TCP sequence, failures/regressions, incremental entry diff and hash manifest.',
 supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='source' if p in sources else 'restricted_campaign_evidence',why='Scoped implementation or exact campaign evidence; prior baseline preserved.',human_review_required=True,behavioral_evidence=p.suffix in {'.json','.xml'}) for p in sorted(set(paths))])
(OUT/'review_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
prior=OUT/'previous_handoff';prior.mkdir(exist_ok=True)
for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
    target=ROOT/'handoff'/name
    if target.exists() and not (prior/name).exists():(prior/name).write_bytes(target.read_bytes())
    pending=target.with_name(name+'.pr_play_66.tmp');pending.write_bytes((stage/name).read_bytes());os.replace(pending,target)
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S');archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
    for row in manifest['included_files']:
        if row.get('sha256'):assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
    count=sum('/pr_play_66/' in n and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist());assert count==18
    assert not any('.env' in n.split('/') for n in z.namelist())
    assert all(row.get('reason','').startswith('duplicate content of ') for row in result['omitted']),result['omitted']
verification=dict(path=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,crc_valid=True,manifest_hashes_verified=True,report_count=count,sensitive_scan='PASS',omitted=result['omitted'])
(OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8');(OUT/'archive_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8');print(json.dumps(verification,indent=2))
