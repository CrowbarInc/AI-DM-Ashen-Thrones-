"""Established review exporter; explicit safe evidence, hashed archive verification."""
import sys,json,hashlib,zipfile,re,os
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/campaigns/product_realization/pr_play_68'
from tools.build_review_handoff import build_handoff
from artifacts.pr_play_67.package_review import redact,sha
def main():
    reg=json.loads((OUT/'regression_summary.json').read_text());verdict=json.loads((OUT/'verdict.json').read_text())
    review=OUT/'review_data';review.mkdir(exist_ok=True)
    names=['baseline.json','frozen_holdout.json','frozen_holdout_manifest.json','holdout_results.json','holdout_summary.json','live_results.json','provider_snapshot.json','state_integrity.json','browser_before_network.json','browser_after_network.json','browser_results.json','pr65_rejection_analysis.json','live_candidate_classification.json','presentation_contract.json','call_chains.json','metrics.json','complete_payload_scan.json','failure_injection.json','protected_integrity.json','freeze_integrity.json','implementation_freeze.json','regression_summary.json','verdict.json']
    provenance=[]
    for n in names:
        source=OUT/n;dest=review/n
        dest.write_text(json.dumps(redact(json.loads(source.read_text(encoding='utf-8'))),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        provenance.append(dict(canonical=source.relative_to(ROOT).as_posix(),canonical_sha256=sha(source),review_copy=dest.relative_to(ROOT).as_posix(),review_sha256=sha(dest),redaction='Internal campaign leaves masked; synthetic canaries and original AI prose retained.'))
    usage=[redact(json.loads(line)) for line in (OUT/'provider_usage.jsonl').read_text().splitlines() if line.strip()]
    (review/'provider_usage.json').write_text(json.dumps(usage,indent=2),encoding='utf-8')
    (review/'provenance.json').write_text(json.dumps(provenance,indent=2))
    sources=[ROOT/n for n in ['game/api.py','game/integrated_investigation_narration.py','tests/test_pr_play_68_structured_publication.py','docs/NEXT_SESSION.md']]
    paths=sources+list(REPORT.glob('*.md'))+list(review.glob('*.json'))+[OUT/'implementation.diff']
    paths += [p for p in OUT.iterdir() if p.is_file() and p.suffix in ['.py','.png','.xml']]
    paths += [OUT/n for n in ['browser_before_ax.txt','browser_before_journal.txt','browser_after_milestone_ax.txt','browser_after_journal_ax.txt','browser_after_final_ax.txt','development.txt','focused_final.txt','boundary_final.txt','broader_final.txt','live_run.txt']]
    for p in paths:
        if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_bytes()):raise RuntimeError('Credential-shaped content: '+str(p))
    config=json.loads((ROOT/'artifacts/pr_play_67/review_config.json').read_text(encoding='utf-8'))
    config.update(campaign_id='pr_play_68',campaign_name='PR-PLAY-68 — Structured-action narration and natural AI presentation',campaign_date='2026-11-05',purpose='Repair structured-action disclosure and evaluate bounded optional AI presentation.',objective_status=verdict['verdict'],executive_summary=(REPORT/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8'),primary_report=(REPORT/'01_EXECUTIVE_SUMMARY.md').relative_to(ROOT).as_posix(),
      changes=dict(production=['Shared PR66 post-persistence publication for structured/chat.','Finite natural attention frames and clearer optional-presentation responsibility.'],validation=['53 new HTTP development tests; one-shot 50-case developer holdout.'],tooling=['Reuse isolated PR67 browser/TCP and regression procedures.'],documentation=['21 requested reports; canonical NEXT_SESSION update.'],generated_artifacts=['Redacted original candidate, network, authority, holdout, latency, browser and regression evidence.']),
      testing=dict(focused='53 new development checks; existing 893 passed / same three failures.',broader='82 boundary checks pass; nine historical authority-assurance failures.',full_suite='Not run; official ATGB not run.',runtime_validation='Five browser actions, five live TCP actions, five matched authoritative controls.',model_runtime_boundary='Four real configured OpenAI provider requests; 2003 tokens; one accepted/published, three fallbacks.',new_regressions=str(reg['new_focused_failures']),pre_existing_failures='Three focused; nine broader. Reused browser seed has a replay-constructor TypeError, retained as fallback evidence.'),
      decisions_requiring_human_review=['No decision required for review. No commit, push or default flag enablement.'],
      known_problems=dict(campaign_specific=['Harmless mud-prints target reference falsely rejected.','Repeat deterministic fallback duplicates no-new status.','Some requested timing and frontend fault instrumentation incomplete.'],pre_existing=['Three focused and nine broader failures.','Inherited PR67 browser replay constructor missing fault parameter.']),
      missing_concepts=['No new authoritative gameplay concept needed; presentation remains bounded.'],does_not_prove=['Universal prose safety, official ATGB, independent external validation, broad naturalness, exact browser-visible latency, general branching/combat or multiplayer.'],recommended_next_step=verdict['next_step'],self_contained_review_test='21 reports, incremental diff, exact before/after browser request/response and AX evidence, original PR65/live AI texts, provider usage, source/holdout freezes, state and regression results.',
      supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='source' if p in sources else 'campaign_evidence',why='Explicit scoped PR68 source or sanitized evidence.',human_review_required=True,behavioral_evidence=p.suffix in ['.json','.png']) for p in sorted(set(paths))])
    (OUT/'review_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
    stage=OUT/'export_stage';result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
    previous=OUT/'previous_handoff';previous.mkdir(exist_ok=True)
    for n in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
        dest=ROOT/'handoff'/n
        if dest.exists() and not (previous/n).exists():(previous/n).write_bytes(dest.read_bytes())
        pending=dest.with_name(n+'.pr_play_68.tmp');pending.write_bytes((stage/n).read_bytes());os.replace(pending,dest)
    # This cycle's explicit client date is 2026-11-05 (EST, UTC-05).
    stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
    archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
    with archive.open('xb') as f:f.write((stage/'CURRENT_REVIEW.zip').read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
        for r in manifest['included_files']:
            if r.get('sha256'):assert hashlib.sha256(z.read(r['bundle_path'])).hexdigest()==r['sha256']
        count=sum('/pr_play_68/' in n and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$',n)) for n in z.namelist());assert count==21
    (OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
    verification=dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,crc_valid=True,manifest_hashes_verified=True,reports=count,credential_shape_scan='passed',omitted=result['omitted'])
    (OUT/'archive_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
    print(json.dumps(verification,indent=2))
if __name__=='__main__':main()
