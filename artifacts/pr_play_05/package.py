"""Explicit reviewed-file selection using the existing handoff exporter."""
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/pr_play_05'
REPORT=ROOT/'development/campaigns/product_realization/pr_play_05'
sources=['game/api.py','game/gm.py','game/provider_budget.py','tools/atgb/accounting.py',
         'tests/test_start_campaign_api.py','tests/test_pr_play_05_diagnostics.py',
         'tests/test_pr_play_05_emission_evidence.py','tests/helpers/pr_play_05_http_capture.py','docs/NEXT_SESSION.md']
selected=[ROOT/p for p in sources]+list(REPORT.glob('*'))
evidence_names=['head.txt','status_before.txt','status_after.txt','entry_hashes.json','integrity.json',
    'scope_verification.json','historical_facts.json','comparison_provenance.json','reconstruct_pre04_api.patch',
    'source.diff','performance.json','emission_comparison.json','test_totals.json','integrated.txt','integrated.xml',
    'placeholder_http.json','entry_remaining.txt','entry_remaining.json','entry_accounting.txt','entry_accounting.json',
    'emission.txt','emission.xml','emission_pre04.txt','emission_pre04.json',
    'run_checks.py','run_additional.py','prepare_comparison.py','finalize_evidence.py','measure.py','write_reports.py','package.py']
selected += [OUT/n for n in evidence_names]
for prefix in ['entry_','fixed_','pre04_','baseline_','repeat_','regression_','provider_final']:
    selected += [p for p in OUT.glob(prefix+'*') if p.suffix in {'.txt','.json'}]
for folder in ['entry','http','diagnostics','emission','emission_pre04']:
    selected += [p for p in (OUT/folder).rglob('*') if p.is_file()]
selected += [ROOT/'docs/DEVELOPMENT_CONSTITUTION.md',ROOT/'docs/validation_evidence_standard.md',ROOT/'docs/product_realization_validation.md']
selected=list(dict.fromkeys(p.resolve() for p in selected))
for path in selected:
    assert path.is_file(),path
    raw=path.read_bytes()
    # Scan explicit final artifacts without reading environment/credential files.
    assert not re.search(rb'sk-(?:proj-)?[A-Za-z0-9_-]{30,}',raw),path
    assert not re.search(rb'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----\r?\n[A-Za-z0-9+/=]{40,}',raw),path
config={
 'campaign_id':'pr_play_05','campaign_name':'PR-PLAY-05 — Opening Regression Closure and Generation Diagnostics',
 'campaign_date':'2026-10-27','purpose':'Bounded offline regression closure and opt-in structural diagnostics; no live authority.',
 'objective_status':'B — Conditionally ready for one controlled live opening after external review',
 'executive_summary':'Two obsolete placeholder/journal fixtures repaired with valid declared structured openings. Three rich emission failures reproduced on hash-verified pre04 API and explicitly excluded, unchanged and unskipped. Existing ledger now retains structural SDK extraction/parsing/finish and final acceptance/commit evidence. 39 focused checks pass; broader 238 pass and 5 demonstrated preexisting failures. No live calls, prompt/schema/model/cap changes, extra provider operations, normal-save/frozen/experimental changes, commit or push.',
 'primary_report':'development/campaigns/product_realization/pr_play_05/08_final_verdict_and_handoff.md',
 'supporting_files':[{'path':p.relative_to(ROOT).as_posix(),'role':'review_evidence' if 'artifacts' in p.relative_to(ROOT).parts else 'source_or_report',
                      'why':'Explicit PR-PLAY-05 report, exact source/fixture, bounded regression result, diagnostic boundary or integrity evidence.'} for p in selected],
 'evidence_packets':[],
 'changes':{
   'production':['Supported SDK output-text extraction; opt-in existing ledger observations; correlated final opening acceptance/commit disposition.'],
   'validation':['Two journal fixtures repaired with actual structured declarations; D1–D10/native SDK/HTTP/repeated/retry/concurrent/budget controls; rich contract assertions retained.'],
   'tooling':['Existing accounting reader recognizes explicit diagnostic observations without changing request lifecycle counts.'],
   'documentation':['Eight reports, exact one-Start PowerShell procedure, canonical NEXT_SESSION.'],
   'generated_artifacts':['Isolated pre04 comparison, HTTP response excerpts, structural diagnostics, test logs, entry-to-final diff and protected hashes.']},
 'testing':{'focused':'39 passed; all 18 PR-PLAY-04 checks retained. Three rich boundary capture controls also pass on current and pre04 source.',
   'broader':'238 passed / 5 demonstrated preexisting failures; exact files and logs in report 06.',
   'full_suite':'Not run.', 'runtime_validation':'Production endpoint, SDK extraction/parser/validation/commit and guarded HTTP controls; synthetic SDK transport only.',
   'model_runtime_boundary':'No live provider calls or connectivity diagnostics. Structural evidence only; no ATGB/gameplay-quality or independent-generalization result.',
   'new_regressions':'None identified within the tested slice.',
   'pre_existing_failures':'Three rich emission/telemetry/prepared precedence conflicts; stale accounting attestation; existing stew-price conversation assertion. All reproduced on earlier source; explicitly excluded.'},
 'decisions_requiring_human_review':['Review verdict B and the preexisting exclusions; accept or decline the single-Start operator procedure. No live attempt performed or scheduled.'],
 'known_problems':{'campaign_specific':['Original generation cause remains unknown; metadata may still be insufficient to explain specific raw content. No raw-capture mode added.'],
                   'pre_existing':['Rich emission preservation/prepared promotion/telemetry conflicts; stale frozen source attestation; conversation assertion. Extensive dirty entry tree retained.']},
 'missing_concepts':[],
 'does_not_prove':['Live generation success, historical confirmed truncation, rendered UI behavior, statistical reliability, full-suite or benchmark acceptance.'],
 'recommended_next_step':'External review of this package, then separately approved operator execution of PR_PLAY_05_LIVE_OPENING_TEST.txt, exactly one Start and stop/export.',
 'self_contained_review_test':'Eight reports, exact manual commands, actual HTTP bodies, boundary comparisons and D1–D10 results are included with source hashes. No secrets or unrelated campaign saves included.'}
(OUT/'review_config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
subprocess.run([sys.executable,str(ROOT/'tools/build_review_handoff.py'),'--config',str(OUT/'review_config.json')],cwd=ROOT,check=True)
source=ROOT/'handoff/CURRENT_REVIEW.zip'
# America/New_York is EDT on this report date; do not use the host timezone.
stamp=datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-4))).strftime('%Y%m%d-%H%M%S')
dest=ROOT/f'handoff/CURRENT_REVIEW({stamp}).zip'
assert not dest.exists()
shutil.copyfile(source,dest)
manifest=json.loads((ROOT/'handoff/REVIEW_MANIFEST.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    names=z.namelist()
    assert sum('/pr_play_05/' in n and re.search(r'/0[1-8]_[^/]+\.md$',n) is not None for n in names)==8
    assert any(n.endswith('/PR_PLAY_05_LIVE_OPENING_TEST.txt') for n in names)
    assert not any('/.env' in n or '/.git/' in n for n in names)
    for item in manifest.get('included_files',[]):
        # The exporter itself owns canonical hashes; validate again when fields are present.
        member=item.get('bundle_path')
        if member in names and item.get('sha256'):
            assert hashlib.sha256(z.read(member)).hexdigest()==item['sha256']
verification={'zip':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
              'bytes':dest.stat().st_size,'members':len(names),'crc_ok':True,'reports':8,
              'secret_pattern_scan':'passed explicit selected files','live_provider_calls':0,
              'commit_or_push':False,'verdict':'B — Conditionally ready; external review required before live attempt'}
(OUT/'package_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
print(json.dumps(verification,indent=2))
