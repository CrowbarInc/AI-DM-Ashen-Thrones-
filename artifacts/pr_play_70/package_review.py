"""Explicit established review exporter; include sanitized selected evidence only."""
import sys,json,pathlib,hashlib,zipfile,os,re
from datetime import datetime,timezone,timedelta
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=pathlib.Path(__file__).resolve().parent
from tools.build_review_handoff import build_handoff
from artifacts.pr_play_67.http_harness import redact

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=ROOT/'development/campaigns/product_realization/pr_play_70';review=OUT/'review_data';review.mkdir(exist_ok=True)
 names=['baseline','frozen_holdout','frozen_holdout_manifest','holdout_results','holdout_summary','implementation_freeze','freeze_integrity','protected_integrity','http_survey','http_report','http_summary','browser_survey_network','browser_report_network','browser_results','live_provider_results','metrics','failure_injection','complete_payload_scan','state_integrity','regression_summary','regression_comparison','verdict','snapshot_relocation']
 paths=list(report.glob('*.md'));provenance=[]
 for name in names:
  original=OUT/(name+'.json');dest=review/original.name
  data=json.loads(original.read_text(encoding='utf-8'));data=redact(data)
  dest.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8');paths.append(dest)
  provenance.append(dict(source=original.relative_to(ROOT).as_posix(),original_sha256=sha(original),review=dest.relative_to(ROOT).as_posix(),review_sha256=sha(dest)))
 sources=[ROOT/p for p in ['game/authored_consequences.py','game/exploration.py','game/storage.py','game/api.py','game/player_http_projection.py','experiments/pr_play_70/scene_actions.json','tests/test_pr_play_70_branching.py','docs/NEXT_SESSION.md']]
 paths+=sources+[OUT/'implementation.diff',OUT/'development.xml',OUT/'development_final.txt',OUT/'focused_final.txt',OUT/'boundary_final.txt',OUT/'broader_final.txt',OUT/'regression_diagnose.txt',OUT/'gameplay.py',OUT/'holdout.py',OUT/'live_provider.py',OUT/'regression.py',OUT/'report.py',OUT/'package_review.py']
 paths+=list(OUT.glob('browser_*.png'))+list(OUT.glob('browser_*reload.txt'))+list(OUT.glob('browser_*continuation.txt'))
 (review/'provenance.json').write_text(json.dumps(provenance,indent=2));paths.append(review/'provenance.json')
 # Raw campaign lore is redacted; provider candidate and player-facing text retained.
 for p in paths:
  if p.suffix in ['.json','.md','.txt','.py','.diff']:
   text=p.read_text(encoding='utf-8',errors='replace')
   assert not re.search(r'\bsk-[A-Za-z0-9_-]{16,}',text),p
 v=json.loads((OUT/'verdict.json').read_text(encoding='utf-8'));metrics=json.loads((OUT/'metrics.json').read_text(encoding='utf-8'))
 config=dict(campaign_id='PR-PLAY-70',campaign_name='Meaningful Player Choice and Branching Consequences',campaign_date='2026-11-05',purpose='Review deterministic exclusive branch gameplay with persistent and observable follow-ups.',objective_status=v['verdict'],executive_summary='Both branches demonstrated through real HTTP and actual existing browser UI. Qualified evidence: seeded browser sessions, clipped viewport captures, shadow-only provider experiment, incomplete latency attribution. No commit/push.',primary_report=(report/'01_EXECUTIVE_SUMMARY.md').relative_to(ROOT).as_posix(),evidence_packets=['artifacts/validation_evidence/pr_play_70'],max_file_bytes=25000000,changes=dict(production=['Finite authored consequence schema over existing world flags, action conditions, persistence and trusted HTTP publication.','Default-off/session-bound Old Milestone scenario with survey/report branches and distinct follow-ups.'],validation=['42 development tests; frozen once-only 50-case holdout.'],tooling=['Isolated HTTP/browser and bounded provider harnesses.'],documentation=['23 campaign reports and current session orientation.'],generated_artifacts=['Full sanitized requests/responses, before/after authority, frozen holdout, original provider candidates, browser traces, exact regression failures.']),testing=dict(focused='42 development passed; see regression_summary for established lanes.',broader='See exact broader failed node IDs and comparison.',full_suite='Not run; no official ATGB or independent external validation claim.',runtime_validation=f"{metrics['http']['gameplay_actions']} TCP gameplay actions; {metrics['browser']['gameplay_actions']} browser actions.",model_runtime_boundary='Four configured provider shadow calls, 1287 tokens, zero AI publications.',new_regressions='See regression summary.',pre_existing_failures='Three focused and nine broader in historical baseline.'),decisions_requiring_human_review=['No approval requested. No commit/push.'],known_problems=dict(campaign_specific=['Browser starts from clean prestarted isolated campaigns.','Clipped viewport captures; browser-visible latency unmeasured.','Provider study shadow-only; deterministic branch text published.','Modest scripted stakes; no broad free-text initiative or concurrent-choice guarantee.'],pre_existing=['Historical regression failures retained.']),missing_concepts=['Normal browser campaign startup/save-slot resume evidence.'],does_not_prove=['Independent external holdout, official ATGB, full suite, open-world agency, concurrent persistence atomicity, live AI publication.'],recommended_next_step=v['next_step'],self_contained_review_test='23 requested reports and explicit source/evidence selection with complete player-facing branch text and machine traces.',supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='source' if p in sources else 'campaign_evidence',why='PR70 selected implementation or retained review evidence.',human_review_required=True,behavioral_evidence=p.suffix=='.json') for p in sorted(set(paths))])
 (OUT/'review_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
 stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
 previous=OUT/'previous_handoff';previous.mkdir(exist_ok=True)
 for n in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
  dest=ROOT/'handoff'/n
  if dest.exists() and not (previous/n).exists():(previous/n).write_bytes(dest.read_bytes())
  pending=dest.with_name(n+'.pr_play_70.tmp');pending.write_bytes((stage/n).read_bytes());os.replace(pending,dest)
 stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S');archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
 archive.open('xb').write((stage/'CURRENT_REVIEW.zip').read_bytes())
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
  for row in manifest['included_files']:
   if row.get('sha256'):assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
  count=sum('/pr_play_70/' in n and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist());assert count==23,count
 (OUT/'archive_path.txt').write_text(str(archive),encoding='utf-8')
 (OUT/'archive_verification.json').write_text(json.dumps(dict(path=str(archive),sha256=sha(archive),crc_valid=True,manifest_hashes_verified=True,reports=count,bytes=archive.stat().st_size,omitted=result['omitted']),indent=2))
 print(archive)
if __name__=='__main__':main()
