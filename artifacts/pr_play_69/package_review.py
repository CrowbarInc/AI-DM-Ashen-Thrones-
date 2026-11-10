"""Established review export with explicit selection, redaction and hash checks."""
import sys,json,hashlib,os,re,zipfile,copy
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/campaigns/product_realization/pr_play_69'
from tools.build_review_handoff import build_handoff
from artifacts.pr_play_67.package_review import redact
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sanitize(value):
    if isinstance(value,list):return [sanitize(v) for v in value]
    if isinstance(value,dict):
        return {k:redact({'session':v})['session'] if k=='authority' else
            redact(v) if k in {'authority_before','authority_after','control'} else
            copy.deepcopy(v) if k in {'hook','hook_input','authorized_outcome_contract'} else
            sanitize(v) for k,v in value.items()}
    return value
def main():
    review=OUT/'review_data';review.mkdir(exist_ok=True)
    names=['baseline','historical_reproduction','historical_after','repeat_before','adversarial_decisions',
        'frozen_holdout','frozen_holdout_manifest','holdout_results','holdout_summary','holdout_classification',
        'live_results','live_candidate_classification','provider_snapshot','state_integrity','browser_results',
        'metrics','failure_injection','context_isolation','complete_payload_scan','protected_integrity',
        'implementation_freeze','freeze_integrity','regression_summary','regression_comparison','test_summary','verdict']
    provenance=[]
    for name in names:
        source=OUT/(name+'.json');dest=review/source.name
        dest.write_text(json.dumps(sanitize(json.loads(source.read_text(encoding='utf-8'))),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        provenance.append(dict(canonical=source.relative_to(ROOT).as_posix(),canonical_sha256=sha(source),review_copy=dest.relative_to(ROOT).as_posix(),review_sha256=sha(dest),redaction='Authoritative private state leaves masked using established PR67 projection; public hook/candidate/final narration retained.'))
    (review/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    sources=[ROOT/n for n in ['game/integrated_investigation_narration.py','game/quarantined_investigation_narration.py',
        'tests/test_pr_play_69_target_references.py','tests/test_pr_play_62_investigation_quality.py','docs/NEXT_SESSION.md']]
    paths=sources+list(REPORT.glob('*.md'))+list(review.glob('*.json'))+[OUT/'implementation.diff']
    paths += [p for p in OUT.iterdir() if p.is_file() and p.suffix in {'.py','.xml','.png'}]
    paths += [OUT/n for n in ['development.txt','focused_final.txt','boundary_final.txt','broader_final.txt','live_run.txt','browser_server.txt','diagnostics_run.txt','holdout_run.txt']]
    for p in paths:
        if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_bytes()):raise RuntimeError('Credential-shaped content: '+str(p))
    reg=json.loads((OUT/'regression_summary.json').read_text());verdict=json.loads((OUT/'verdict.json').read_text())
    config=dict(campaign_id='pr_play_69',campaign_name='PR-PLAY-69 — Contextual Target References & Repeat-Action Quality',campaign_date='2026-11-05',
        purpose='Bounded contextual-target overlap repair, deterministic repeat quality and authority preservation.',objective_status=verdict['verdict'],
        executive_summary=(REPORT/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8'),primary_report=(REPORT/'01_EXECUTIVE_SUMMARY.md').relative_to(ROOT).as_posix(),
        evidence_packets=[],max_file_bytes=134217728,
        changes=dict(production=['Resolver-selected public target names/aliases projected into finite attention validation.','Only full nonassertive frames exempt from vocabulary overlap; entire remaining candidate validated.','Known fallback states the action and no-new outcome once each.'],
            validation=['55 new target tests; 53 PR68 and six PR62 development controls.','Fresh frozen developer holdout 60/60 once; historical focused/boundary/broader lanes.'],
            tooling=['Isolated capped live HTTP and matched authority controls.','Browser harness restores the real hook, avoiding inherited _Replay fault-argument defect.'],
            documentation=['Twenty requested reports and NEXT_SESSION updated.'],generated_artifacts=['Original historical/live narration, faults, holdout, HTTP payloads, state, latency, integrity and regression evidence.']),
        testing=dict(focused=f"114 development pass; historical focused {reg['focused']['passed']} pass / {reg['focused']['failed']} known failures.",
            broader=f"Boundary {reg['boundary']['passed']} pass; broader {reg['broader']['failed']} historical failures.",full_suite='Not run; no official ATGB claim.',
            runtime_validation='Five real TCP actions; matched raw authority equal 5/5. Browser attachment blocked twice; zero browser actions.',
            model_runtime_boundary='Four real configured gpt-4.1-mini requests / 2060 tokens; one accepted/published, three correct duplicate fallbacks.',
            new_regressions=str(reg['new_focused_failures']),pre_existing_failures='Three focused; nine broader; browser adapter defect handled only in new harness.'),
        decisions_requiring_human_review=['No decision required. No commit, push or default feature enablement.'],
        known_problems=dict(campaign_specific=['Actual browser verification/screenshots/visible latency unavailable.','Three live provider candidates still duplicated engine-owned outcomes.','HTTP timings higher under concurrent local checks; no causal performance conclusion.'],pre_existing=['Three focused/nine broader failures.']),
        missing_concepts=['Player agency/meaningful branching is the next milestone.'],
        does_not_prove=['Independent external validation, official ATGB, arbitrary prose safety, broad acceptance improvement, browser-originated publication, meaningful branching or complete latency attribution.'],
        recommended_next_step=verdict['next_step'],self_contained_review_test='Twenty requested reports, incremental diff, exact historical/live narration, sealed holdout, state controls, complete HTTP payload scans, explicit browser blocker and all regression failures.',
        supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='source' if p in sources else 'campaign_evidence',why='Explicit PR69 review source or sanitized evidence.',human_review_required=True,behavioral_evidence=p.suffix=='.json') for p in sorted(set(paths))])
    (OUT/'review_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
    stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
    previous=OUT/'previous_handoff';previous.mkdir(exist_ok=True)
    for n in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
        dest=ROOT/'handoff'/n
        if dest.exists() and not (previous/n).exists():(previous/n).write_bytes(dest.read_bytes())
        pending=dest.with_name(n+'.pr_play_69.tmp');pending.write_bytes((stage/n).read_bytes());os.replace(pending,dest)
    # Client date 2026-11-05 is Eastern Standard Time (UTC-05).
    stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
    archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
    with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
        for row in manifest['included_files']:
            if row.get('sha256'):assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
        count=sum('/pr_play_69/' in n and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist());assert count==20
        assert any('12_BROWSER_GAMEPLAY' in n for n in z.namelist())
    (OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
    verification=dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,crc_valid=True,manifest_hashes_verified=True,reports=count,credential_shape_scan='passed',omitted=result['omitted'])
    (OUT/'archive_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
    print(json.dumps(verification,indent=2))
if __name__=='__main__':main()
