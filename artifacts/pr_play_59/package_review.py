"""Build and verify the standard explicit-selection review export."""
import sys,json,hashlib,re,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.build_review_handoff import build_handoff
from artifacts.pr_play_59.evaluate import read,write,hashes
OUT=ROOT/'artifacts/pr_play_59';REPORT=ROOT/'development/campaigns/product_realization/pr_play_59'
assert hashes()==read('implementation_frozen.json');assert not read('integrity.json')['unexpected_changes']
summary=(REPORT/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8')
h=read('h41_original.json')
write('evidence_manifest.json',{'campaign':{'campaign_id':'pr_play_59','run_count':1,'turn_count':1,'gm_boundary':'Local replay of exact historical H41 prose, no gameplay or provider execution.'},'evidence_scope':'historical_failure_replay_and_same_session_synthetic_controls','examples':[{'example_id':'H41','campaign':'PR-PLAY-59','run_id':'PR58-H41-replay','turn_index':1,'player_input':h['request']['player_action'],'player_input_classification':['runtime_discovered'],'prior_context':'Completed investigation with no gate effect.','authorized_context':h['request'],'exact_gm_output':h['case']['text'],'publication':'Quarantined historical candidate only.','previous_result':read('h41_before.json'),'actual_result':read('h41_after.json'),'human_review':{'status':'PENDING','rationale':'External review not claimed.'},'source_artifact_path':'artifacts/pr_play_59/h41_original.json'}]})
(OUT/'evidence_summary.md').write_text(summary,encoding='utf-8')
sources=['game/persistent_consequence_claims.py','game/consequential_narration_validation.py','game/integrated_investigation_narration.py','game/mandatory_outcome_coverage.py','game/anchored_investigation_narration.py','game/offline_investigation_projection.py','game/quarantined_investigation_narration.py','tests/pr_play_59_development.py','tests/test_pr_play_59_persistent_consequences.py','docs/NEXT_SESSION.md']
paths=[p for p in OUT.iterdir() if p.is_file() and p.name not in {'archive_path.txt','archive_verification.json','review_config.json'}]+list(REPORT.glob('*.md'))+[ROOT/p for p in sources]
hits=[p.relative_to(ROOT).as_posix() for p in paths if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_bytes())]
assert not hits
write('export_scan.json',{'files_scanned':len(paths),'private_key_or_provider_key_signatures':hits,'selection':'Explicit current-campaign evidence, source and reports; no .env or unrelated configuration.'})
paths.append(OUT/'export_scan.json')
config={'campaign_id':'pr_play_59','campaign_name':'PR-PLAY-59 — Persistent Consequence Authority Repair','campaign_date':'2026-11-03','purpose':'Block unauthorized persistent narration while preserving deterministic authority and quarantine.','objective_status':'B — PARTIAL / FURTHER INVESTIGATION REQUIRED','executive_summary':summary,'primary_report':'development/campaigns/product_realization/pr_play_59/01_EXECUTIVE_SUMMARY.md','evidence_packets':['artifacts/pr_play_59'],'max_file_bytes':33554432,'changes':{'production':['No gameplay, publication or state mutation change.'],'validation':['Persistent-state frames and entity/property/result/duration authority matching in existing consequential gate.'],'tooling':['Frozen corpora, local replay, measurements, integrity and export.'],'documentation':['18 reports and session handoff.'],'generated_artifacts':['All layer traces, matrices, original H41 and regression evidence.']},'testing':{'focused':'686 passed / 3 known failures of 689; zero errors or skips.','broader':'PR55 wrapper passed; 9 known authority metadata failures reproduced.','full_suite':'Not executed.','runtime_validation':'Original H41 and eight PR57 samples replayed; 46 development and one frozen 50-case consequence holdout; combined development 45/46.','model_runtime_boundary':'No provider requests; narration remains quarantined.','new_regressions':'No new final-source test regressions; one pre-existing combined positive rejection limits verdict.','pre_existing_failures':'3 focused and 9 hard_validation_attempt_1 metadata failures; combined D25 projection rejection.'},'decisions_requiring_human_review':['Review bounded repair and B verdict; no player-facing enablement requested.'],'known_problems':{'campaign_specific':['End-to-end holdout not run; combined D25 authorized acquisition is rejected.'],'pre_existing':['Three focused, nine broader metadata failures; PR58 D15/H12 rejections.']},'missing_concepts':['General semantic entailment and complete resolved-effect authority projection.'],'does_not_prove':['Universal paraphrase detection, independent blind generalization, live gameplay quality, ATGB score or player-facing safety.'],'recommended_next_step':'PR-PLAY-60 bounded resolved-inventory authority projection repair with a fresh end-to-end corpus; retain quarantine.','self_contained_review_test':'18 reports, exact H41, before/after traces, frozen corpora/hashes, matrices, source/diff, regression logs and limitations included.','supporting_files':[{'path':p.relative_to(ROOT).as_posix(),'role':'source' if p.relative_to(ROOT).as_posix() in sources else 'campaign_evidence','why':'PR59 implementation, provenance or evaluation evidence.','human_review_required':True,'behavioral_evidence':p.suffix=='.json'} for p in sorted(set(paths))]}
write('review_config.json',config);config['configuration_source']='artifacts/pr_play_59/review_config.json'
stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
 (ROOT/'handoff'/name).write_bytes((stage/name).read_bytes())
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S');archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
 for r in manifest['included_files']:
  if r.get('sha256'):assert hashlib.sha256(z.read(r['bundle_path'])).hexdigest()==r['sha256']
 assert sum('/pr_play_59/' in n and bool(re.search(r'/\d\d_[A-Z_0-9]+\.md$',n)) for n in z.namelist())==18
 assert not any('.env' in n.split('/') for n in z.namelist())
write('archive_verification.json',{'path':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'crc_valid':True,'manifest_hashes_valid':True,'reports':18,'omitted':result['omitted'],'frozen_source_matches':hashes()==read('implementation_frozen.json')})
(OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
print(json.dumps(read('archive_verification.json'),indent=2))
