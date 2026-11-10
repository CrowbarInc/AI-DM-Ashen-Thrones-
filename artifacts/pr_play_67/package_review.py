"""Established review exporter with explicit, redacted evidence selection."""
import sys,json,hashlib,os,re,zipfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/campaigns/product_realization/pr_play_67'
from tools.build_review_handoff import build_handoff
from game.player_http_projection import STATE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mask(value):
    if isinstance(value,str):
        sentinels=re.findall(r'(?:CANARY_[A-Z0-9_]+|[A-Z_]*SENTINEL[A-Z0-9_]*)',value)
        return ' '.join(sentinels) if sentinels else '[REDACTED INTERNAL CAMPAIGN CONTENT]'
    if isinstance(value,list):return [mask(v) for v in value]
    if isinstance(value,dict):return {k:mask(v) for k,v in value.items()}
    return value
def according(value,schema):
    if not isinstance(value,dict):return redact(value)
    return {k:according(v,schema[k]) if k in schema and isinstance(schema[k],dict)
            else redact(v) if k in schema else mask(v) for k,v in value.items()}
def redact(value):
    if isinstance(value,list):return [redact(v) for v in value]
    if isinstance(value,dict):
        out={}
        for k,v in value.items():
            if k in ('world','session','campaign','character','scene') and isinstance(v,dict):out[k]=according(v,STATE.get(k,{}))
            elif k.startswith('_') or k in ('debug','debug_traces','metadata','gm_only','gm_notes','private_notes','hidden_facts','discoverable_clues'):out[k]=mask(v)
            elif k in ('redacted_reserialized_json','serialized_body') and isinstance(v,str):
                try:out[k]=json.dumps(redact(json.loads(v)),ensure_ascii=False,separators=(',',':'))
                except ValueError:out[k]=mask(v)
            else:out[k]=redact(v)
        return out
    return value

def main():
    verdict=json.loads((OUT/'verdict.json').read_text());reg=json.loads((OUT/'regression_summary.json').read_text())
    target=OUT/'review_data';target.mkdir(exist_ok=True)
    names=['baseline.json','original_leak_reproduction.json','endpoint_inventory.json','response_contract.json','visibility_classification.json','frozen_holdout.json','frozen_holdout_manifest.json','holdout_results.json','holdout_summary.json','http_integration.json','gameplay_replay.json','failure_injection.json','persistence.json','metrics.json','supplemental_http.json','browser_results.json','browser_entry_comparison.json','state_comparisons.json','state_equivalence_audit.json','raw_authority_audit.json','regression_summary_initial.json','regression_summary.json','implementation_freeze.json','freeze_integrity.json','protected_integrity.json','complete_payload_scan.json','serialized_http_payloads.json','verdict.json']
    provenance=[]
    for name in names:
        original=OUT/name;copy=target/name
        copy.write_text(json.dumps(redact(json.loads(original.read_text())),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        provenance.append(dict(canonical=str(original.relative_to(ROOT)),canonical_sha256=sha(original),review_copy=str(copy.relative_to(ROOT)),review_sha256=sha(copy),redaction='Internal campaign string leaves masked; synthetic sentinels retained; schemas preserved.'))
    (target/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    sources=[ROOT/p for p in ['game/player_http_projection.py','game/player_http_boundary.py','tests/test_pr_play_67_player_projection.py','docs/NEXT_SESSION.md']]
    paths=sources+list(REPORT.glob('*.md'))+list(target.glob('*.json'))+[OUT/'implementation.diff',OUT/'browser_smoke.png']
    paths += [OUT/n for n in ['development.xml','boundary_final.xml','focused_retry_final.xml','winerror_diagnostic_final.xml','broader_final.xml'] if (OUT/n).exists()]
    # Include executables of this evaluation, never fixture campaign stores or
    # raw old baseline transcripts with authored hidden campaign content.
    paths += [OUT/n for n in ['prepare.py','http_harness.py','integration.py','holdout.py','regression.py','retry_regression.py','raw_authority_audit.py','browser_entry_comparison.py','summarize.py','build_reports.py','package_review.py','supplemental.py']]
    for p in paths:
        if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_bytes()):raise RuntimeError('Credential-shaped content in selected file: '+str(p))
    config=dict(campaign_id='pr_play_67',campaign_name='PR-PLAY-67 — Player-safe HTTP state projection',campaign_date='2026-11-04',
        purpose='Repair and verify the server/player HTTP trust boundary.',objective_status=verdict['verdict'],
        executive_summary=(REPORT/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8'),primary_report=str((REPORT/'01_EXECUTIVE_SUMMARY.md').relative_to(ROOT)),evidence_packets=[],max_file_bytes=134217728,
        changes=dict(production=['Explicit player HTTP nested DTOs; shared final JSON boundary and safe error responses.'],validation=['42 development tests; existing private-metadata assertions migrated to server logs without removing authoritative checks.'],tooling=['Real TCP endpoint/replay/fault tests, one-shot frozen holdout, raw authority control and browser entry comparison.'],documentation=['20 requested reports and canonical NEXT_SESSION orientation.'],generated_artifacts=['Redacted complete HTTP bodies, state/persistence evidence, provenance/hashes, latency and regression summaries.']),
        testing=dict(focused=f"{reg['focused']['passed']} passed / {reg['focused']['failed']} failed",broader='82 boundary/frontend/persistence checks; nine historical broader failures.',full_suite='Not run; official ATGB not run.',runtime_validation='78 TCP endpoint/fault requests; 50 frozen HTTP holdout cases; ten raw-authority control requests; browser-originated core display/action/navigation smoke.',model_runtime_boundary='Zero live provider calls. Synthetic controlled narration only.',new_regressions=str(reg['new_focused_failures']),pre_existing_failures='Three focused and nine broader historical failures. New Windows file-replacement failures preserved separately, with focused retry evidence.'),
        decisions_requiring_human_review=['No approval is required to review the repair. No commit, push, deployment or default flag enablement was performed.'],
        known_problems=dict(campaign_specific=reg['new_focused_failures'],pre_existing=['Structured milestone button narration refusal remains identical in entry source; clue reaches the journal.','Three focused and nine broader historical failures.']),
        missing_concepts=['Item-level public visibility contracts for world factions/projects/events; natural optional presentation remains deferred.'],
        does_not_prove=['Universal semantic safety, independent external validation, official ATGB, live-provider quality, concurrent multi-tenant authorization, browser verification of every endpoint or client delivery ACK.'],
        recommended_next_step=verdict['next_step'],self_contained_review_test='20 reports, redacted full HTTP schemas/bodies, exact replay, frozen manifest/results/hash, raw authority/persistence comparisons, endpoint/field contract, browser proof and incremental implementation diff.',
        supporting_files=[dict(path=str(p.relative_to(ROOT)),role='source' if p in sources else 'campaign_evidence',why='Explicitly selected scoped implementation or redacted PR67 evidence.',human_review_required=True,behavioral_evidence=p.suffix in ('.json','.png')) for p in sorted(set(paths))])
    (OUT/'review_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
    prior=OUT/'previous_handoff';prior.mkdir(exist_ok=True)
    for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
        dest=ROOT/'handoff'/name
        if dest.exists() and not (prior/name).exists():(prior/name).write_bytes(dest.read_bytes())
        pending=dest.with_name(name+'.pr_play_67.tmp');pending.write_bytes((stage/name).read_bytes());os.replace(pending,dest)
    stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
    archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
    with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
        for row in manifest['included_files']:
            if row.get('sha256'):assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
        count=sum('/pr_play_67/' in n and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist());assert count==20
        assert all(r.get('reason','').startswith('duplicate content of ') for r in result['omitted']),result['omitted']
    verification=dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,crc_valid=True,manifest_hashes_verified=True,report_count=count,sensitive_scan='passed',redacted_review_data=True,omitted=result['omitted'])
    (OUT/'archive_path.txt').write_text(str(archive)+'\n')
    (OUT/'archive_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps(verification,indent=2))
if __name__=='__main__':main()
