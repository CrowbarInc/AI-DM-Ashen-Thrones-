"""Established review exporter with selected sanitized evidence and verified ZIP hashes."""
import sys,json,hashlib,zipfile,re,os
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
from tools.build_review_handoff import build_handoff
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(v):
    private={'gm_notes','hidden_facts','private_notes','gm_only','character_secret','gm_guidance','inference_rules','current_plan','current_agenda','goal','topics'}
    if isinstance(v,dict):
        return {k:('[REDACTED PRIVATE CAMPAIGN CONTENT]' if k in private else '[OMITTED NONAUTHORITATIVE DIAGNOSTICS]' if k in {'debug_traces','last_action_debug'} else clean(x)) for k,x in v.items()}
    if isinstance(v,list):return [clean(x) for x in v]
    return v
def main():
 report=ROOT/'development/campaigns/product_realization/pr_play_71';review=OUT/'review_data';review.mkdir(exist_ok=True)
 paths=list(report.glob('*.md'));provenance=[]
 for original in sorted(OUT.iterdir()):
  if not original.is_file() or original.name in {'review_config.json','archive_path.txt','archive_verification.json'}:continue
  if original.suffix not in {'.json','.jsonl','.txt','.xml','.png','.diff','.py'}:continue
  if original.suffix in {'.json','.jsonl'}:
   dest=review/original.name
   if original.suffix=='.json':dest.write_text(json.dumps(clean(json.loads(original.read_text(encoding='utf-8'))),indent=2,ensure_ascii=False),encoding='utf-8')
   else:
    with dest.open('w',encoding='utf-8') as f:
     for line in original.read_text(encoding='utf-8').splitlines():f.write(json.dumps(clean(json.loads(line)),ensure_ascii=False)+'\n')
   paths.append(dest);provenance.append(dict(source=original.relative_to(ROOT).as_posix(),original_sha256=sha(original),review=dest.relative_to(ROOT).as_posix(),review_sha256=sha(dest)))
  else:paths.append(original)
 sources=[ROOT/p for p in ['game/api.py','game/authored_consequences.py','game/campaign_reset.py','game/storage.py','game/quarantined_investigation_narration.py','static/app.js','tests/test_pr_play_71_lifecycle.py','tests/test_pr_play_71_persistence_recovery.py','docs/NEXT_SESSION.md']]
 paths+=sources+list((OUT/'frozen_source').rglob('*.py'))+list((OUT/'frozen_source').rglob('*.js'))
 (review/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8');paths.append(review/'provenance.json')
 for p in paths:
  if p.suffix!='.png':assert not re.search(r'\bsk-[A-Za-z0-9_-]{16,}',p.read_text(encoding='utf-8',errors='replace')),p
 v=json.loads((OUT/'verdict.json').read_text());validation=json.loads((OUT/'final_validation.json').read_text())
 config=json.loads((ROOT/'artifacts/pr_play_70/review_config.json').read_text())
 config.update(campaign_id='PR-PLAY-71',campaign_name='Normal Campaign Lifecycle and Branch Continuity',campaign_date='2026-11-05',purpose='Review normal UI creation, start, branch choice, save/resume and continuity, including preserved failures.',objective_status=v['verdict'],executive_summary='Both normal browser lifecycles demonstrated; one frozen holdout 46/50 precedes targeted persistence/import repairs. Final-source holdout/browser coverage incomplete. No commit/push.',primary_report=(report/'01_EXECUTIVE_SUMMARY.md').relative_to(ROOT).as_posix(),evidence_packets=[],max_file_bytes=60000000,
 changes=dict(production=['Explicit default-off new-campaign enrollment; trusted prerequisite disclosure; full transcript resume; bounded start deadline/busy guards.','Bounded same-file Windows rename retry and failed-New-Campaign rollback; existing adapter dependency retained.'],validation=['50-case frozen developer holdout once: 46 passed, four failures retained.','Final focused recovery/publication/branch and boundary checks; separate baseline comparison for newly measured startup failures.'],tooling=['Isolated normal browser/TCP host, full transport/authority capture and selected sanitized review export.'],documentation=['23 cycle reports and NEXT_SESSION orientation.'],generated_artifacts=['Original failure traces, screenshots, frozen manifest/source and final repair results.']),
 testing=dict(focused=str(validation['post_holdout']),broader='Nine historical authority failures; exact XML/log included.',full_suite='Not run; no official ATGB or external independence.',runtime_validation='Both normal UI branches plus separate TCP replay; final persistence repair has final TCP but no live-browser rerun.',model_runtime_boundary='15 live requests, 189036 tokens including preflight/required gameplay; no shadow study.',new_regressions='PR49 direct-import regression fixed and retested; temporary test directory collisions retained then rerun with isolated basetemp.',pre_existing_failures='Three historical focused, nine broader, plus six newly measured startup failures verified against exact entry API.'),
 decisions_requiring_human_review=['No approval requested; no commit/push.'],known_problems=dict(campaign_specific=['Frozen holdout precedes final recovery changes; raw score 46/50.','Cached frontend initially kept the previous transcript; reopened context verified current frontend.','Complete per-operation browser startup/substage timings unavailable.'],pre_existing=['Six startup failures reproduced on entry API.','Permanent filesystem outages can still prevent rollback.']),missing_concepts=['Final-source fresh holdout and live-browser coverage for final persistence repair.'],does_not_prove=['Full suite, official ATGB, external independent validation, process-crash durability, multiplayer authorization or broad open-world initiative.'],recommended_next_step=v['next_step'],self_contained_review_test='23 requested reports, exact player-facing responses, original failure traces, final repair checks, explicit baseline and scope limits.',supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='source' if p in sources else 'campaign_evidence',why='Selected PR71 implementation, original evidence, or final repair verification.',human_review_required=True,behavioral_evidence=p.suffix in {'.json','.jsonl','.png','.xml'}) for p in sorted(set(paths))])
 (OUT/'review_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
 stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
 previous=OUT/'previous_handoff';previous.mkdir(exist_ok=True)
 for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
  dest=ROOT/'handoff'/name
  if dest.exists() and not (previous/name).exists():(previous/name).write_bytes(dest.read_bytes())
  pending=dest.with_name(name+'.pr71.tmp');pending.write_bytes((stage/name).read_bytes());os.replace(pending,dest)
 stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S');archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
 with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
  for row in manifest['included_files']:
   if row.get('sha256'):assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
  count=sum('/pr_play_71/' in n and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist());assert count==23,count
 (OUT/'archive_path.txt').write_text(str(archive),encoding='utf-8')
 (OUT/'archive_verification.json').write_text(json.dumps(dict(path=str(archive),sha256=sha(archive),crc_valid=True,manifest_hashes_verified=True,reports=count,bytes=archive.stat().st_size,omitted=result['omitted']),indent=2))
 print(archive)
if __name__=='__main__':main()
