"""Standard selected review export with sanitized state snapshots and screenshots."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import sys,json,hashlib,zipfile,re,os
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));O=Path(__file__).resolve().parent
from tools.build_review_handoff import build_handoff
from artifacts.pr_play_71v.package_review import clean

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 metrics=json.loads((O/'metrics.json').read_text());report=R/'development/campaigns/product_realization/pr_play_72v';review=O/'review_data';review.mkdir(exist_ok=True)
 sources=[R/p for p in ['game/player_initiative.py','game/exploration.py','game/api.py','game/api_turn_support.py','game/conversational_orchestration.py','game/player_interpretation_bridge.py','game/authored_consequences.py','game/player_http_projection.py','game/storage.py','game/journal.py','game/integrated_investigation_narration.py','game/quarantined_investigation_narration.py','tests/conftest.py','tests/helpers/storage_isolation.py','tests/test_pr_play_71_lifecycle.py','tests/test_pr_play_72_initiative.py','tests/test_pr_play_72v_resolution.py','tests/test_pr_play_72v_post_holdout.py','tests/test_pr_play_72_supplemental.py','tests/test_pr_play_46_mechanical_boundary.py','tests/test_pr_play_60_gameplay_readiness.py','docs/NEXT_SESSION.md']]
 paths=list(report.glob('*.md'))+sources;provenance=[]
 for p in sorted(O.iterdir()):
  if not p.is_file() or p.name in ['review_config.json','archive_verification.json','archive_path.txt'] or p.suffix not in ['.json','.jsonl','.txt','.xml','.diff','.py','.png']:continue
  if p.suffix in ['.json','.jsonl']:
   dest=review/p.name
   if p.suffix=='.json':dest.write_text(json.dumps(clean(json.loads(p.read_text())),indent=2),encoding='utf-8')
   else:
    with dest.open('w',encoding='utf-8') as f:
     for line in p.read_text().splitlines():
      if line.strip():f.write(json.dumps(clean(json.loads(line)))+'\n')
   paths.append(dest);provenance.append(dict(source=p.relative_to(R).as_posix(),source_sha256=sha(p),review_sha256=sha(dest)))
  else:paths.append(p)
 for name in ['frozen_holdout.json','frozen_holdout_manifest.json','holdout_summary.json','post_holdout_changes.json']:
  original=R/'artifacts/pr_play_72'/name;dest=review/('original_PR72_'+name);dest.write_bytes(original.read_bytes());paths.append(dest)
 (review/'provenance.json').write_text(json.dumps(provenance,indent=2));paths.append(review/'provenance.json')
 for p in paths:
  if p.suffix!='.png':assert not re.search(r'\bsk-[A-Za-z0-9_-]{16,}',p.read_text(encoding='utf-8',errors='replace')),p
 cfg=json.loads((R/'artifacts/pr_play_72/review_config.json').read_text())
 cfg.update(campaign_id='PR-PLAY-72V',campaign_name='Natural Initiative Verification & Resolution Closure',campaign_date='2026-11-06',purpose='Repair and verify repeat resolution, genuine ambiguity and read-only inquiries through existing authority boundaries.',objective_status='B',executive_summary=metrics['verdict'],primary_report=(report/'01_EXECUTIVE_SUMMARY.md').relative_to(R).as_posix(),evidence_packets=[],max_file_bytes=90000000,
 changes=dict(production=['Completed accessible repeat outcome in existing exploration resolver.','Read-only contextual/auxiliary inquiry classification repairs; no new resolver or persistence layer.'],validation=['Frozen developer holdout once: 46/50, with failures preserved.','Final 78-case safety development plus existing and isolated regression lanes.','Two normal HTTP campaigns, two browser lifecycles and final-source resumed safety checks.','Two test-isolation boundary defects repaired.'],tooling=['Existing isolated runtime host and existing standard review exporter.'],documentation=['21 requested reports and canonical NEXT_SESSION handoff.'],generated_artifacts=['Raw inputs/publications, authority and resolver traces, hashes, XML, screenshots, timings.']),
 testing=dict(focused=str(metrics['development']),broader=str({k:dict(passed=v['passed'],failed=len(v['failed'])) for k,v in metrics['regression'].items()}),full_suite='Not run; no official ATGB or external validation.',runtime_validation='Both normal HTTP campaigns and browser branch lifecycles, plus final-source resumed browser safety.',model_runtime_boundary='0 live provider requests / 0 tokens / 0 retries; deterministic interpretation and offline opening fixture.',new_regressions='Two additional focused test-isolation failures repaired and verified separately; no confirmed new product regression in executed paths.',pre_existing_failures='Exact identity comparisons retained. Combined and isolated lanes are separate.'),
 decisions_requiring_human_review=['Review the B closure and its preserved frozen failures before proceeding to PR-PLAY-73; no commit or push authorized.'],known_problems=dict(campaign_specific=['Frozen 46/50 precedes final safety repairs; no independent final-source holdout.','Two critical read-only mutations and unrelated fallback publications occurred in the frozen run; repaired separately.','Full browser lifecycles precede final auxiliary repair; both resumed branches verified on final source.','Browser timings are observed upper bounds, not paint measurements.','One isolated atomic test observed an extra rename call; fresh 4/4 recheck passed, exact external cause unproven.'],pre_existing=['Historical boundary/authority and combined-suite failures remain as reported.','Historical session-log loss from PR71V is not recovered or reinterpreted.']),missing_concepts=['Live AI interpretation; unrestricted natural intentions.'],does_not_prove=['Arbitrary world simulation, external independence, full-suite pass or live narration quality.'],recommended_next_step=metrics['next_cycle'],self_contained_review_test='21 reports, original failed case reconstruction, both frozen manifests/results, final development/HTTP/browser/persistence evidence, protected hashes, source diffs and limitations.',supporting_files=[dict(path=p.relative_to(R).as_posix(),role='source' if p in sources else 'campaign_evidence',why='PR72V implementation or retained repair/verification evidence.',human_review_required=True,behavioral_evidence=p.suffix in ['.json','.jsonl','.png']) for p in sorted(set(paths))])
 (O/'review_config.json').write_text(json.dumps(cfg,indent=2));stage=O/'export_stage';result=build_handoff(cfg,root=R,output_dir=stage,archive_history=False)
 previous=O/'previous_handoff';previous.mkdir(exist_ok=True)
 for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
  dest=R/'handoff'/name
  if dest.exists() and not (previous/name).exists():(previous/name).write_bytes(dest.read_bytes())
  pending=dest.with_name(name+'.pr72v.tmp');pending.write_bytes((stage/name).read_bytes());os.replace(pending,dest)
 stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S');archive=R/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
 with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
  for row in manifest['included_files']:
   if row.get('sha256'):assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
  count=sum('/pr_play_72v/' in n and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist());assert count==21,count
 (O/'archive_path.txt').write_text(str(archive));(O/'archive_verification.json').write_text(json.dumps(dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,reports=count,crc_valid=True,manifest_hashes_verified=True,omitted=result['omitted']),indent=2));print(archive)
if __name__=='__main__':main()
