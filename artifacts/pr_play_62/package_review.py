"""Established review exporter, explicit restricted-evidence selection, no secrets."""
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff

OUT = ROOT / 'artifacts/pr_play_62'
REPORT = ROOT / 'development/campaigns/product_realization/pr_play_62'
summary = (REPORT / '01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8')
sources = [ROOT / p for p in (
    'game/integrated_investigation_narration.py',
    'game/quarantined_investigation_narration.py',
    'tests/test_pr_play_62_investigation_quality.py',
    'docs/NEXT_SESSION.md',
)]
paths = sources + list(REPORT.glob('*.md'))
paths += [p for p in OUT.iterdir() if p.is_file() and p.suffix in {
    '.json', '.jsonl', '.xml', '.txt', '.py', '.diff'
} and p.name not in {'archive_path.txt', 'archive_verification.json', 'collected_prefix.txt'}]
paths += list((OUT / 'quarantine_evidence').glob('*.json'))
paths += list((OUT / 'entry_source/game').glob('*.py'))
paths += [OUT / 'entry_source/docs/NEXT_SESSION.md']
for path in paths:
    if re.search(br'sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', path.read_bytes()):
        raise SystemExit('Sensitive material in ' + str(path.relative_to(ROOT)))
metrics = json.loads((OUT / 'metrics.json').read_text())
regression = json.loads((OUT / 'regression_summary_final.json').read_text())
config = {
    'campaign_id': 'pr_play_62',
    'campaign_name': 'PR-PLAY-62 — Investigation loop quality and responsiveness',
    'campaign_date': '2026-11-03',
    'purpose': 'Improve restricted investigation recovery and pacing with inspectable bounded evidence.',
    'objective_status': metrics['verdict'],
    'executive_summary': summary,
    'primary_report': 'development/campaigns/product_realization/pr_play_62/01_EXECUTIVE_SUMMARY.md',
    'evidence_packets': [],
    'max_file_bytes': 33554432,
    'changes': {
        'production': ['Action-focused experimental fallback; concise prompt; explicit no-new-clue status; optional resolved-repeat provider bypass.'],
        'validation': ['No validator changed; every prior mandatory anchor remains.'],
        'tooling': ['Real HTTP capture, no-provider controls and failure injection, restricted original reconstruction, stage timing and provider accounting.'],
        'documentation': ['20 reports and session orientation.'],
        'generated_artifacts': ['Per-action state/output/traces, usage ledger, latency/quality/matrix, regression logs and browser blocker trace.'],
    },
    'testing': {
        'focused': '746 passed / 3 known failures of 749; additional failed-examination boundary 1 passed. Zero new focused failures.',
        'broader': 'PR55 holdout wrapper 1 passed; authority assurance 9/9 known hard_validation_attempt_1 failures.',
        'full_suite': 'Not executed.',
        'runtime_validation': 'Five real HTTP actions: one published AI, two rejection fallbacks, two repeat fast paths. Ten required injected failures recover.',
        'model_runtime_boundary': 'OpenAI gpt-4.1-mini-2025-04-14; 3 requests, 1525 tokens, 0 retries.',
        'new_regressions': 'None remaining in focused selection.',
        'pre_existing_failures': '3 focused; 9 broader metadata failures.',
    },
    'decisions_requiring_human_review': ['No enablement requested. Subjective quality remains provisional; rejected candidates are restricted review evidence.'],
    'known_problems': {
        'campaign_specific': ['Browser attachment blocked; no UI-originated action or rendering proof.', 'Only one of three live candidates publishes; latency worsened.'],
        'pre_existing': ['Adjective/access false rejection; bounded route coverage; prior mandatory-anchor repetition; 3 focused and 9 broader failures.'],
    },
    'missing_concepts': ['Meaningful branching choices remain unproven.'],
    'does_not_prove': ['General AI-DM/RPG playability, browser gameplay, systemic narration reliability, isolated latency improvement, or an ATGB score.'],
    'recommended_next_step': 'Restore browser webview attachment and execute the same five-action restricted sequence through the existing UI.',
    'self_contained_review_test': '20 reports, exact published responses, original and new restricted traces, control state comparisons, provider ledger, faults and test results included.',
    'supporting_files': [{
        'path': p.relative_to(ROOT).as_posix(),
        'role': 'source' if p in sources else 'restricted_campaign_evidence',
        'why': 'PR62 scoped source, report, or restricted evidence. Rejected narration is review-only, never player publication.',
        'human_review_required': True,
        'behavioral_evidence': p.suffix in {'.json', '.jsonl', '.xml'},
    } for p in sorted(set(paths))],
}
stage = OUT / 'export_stage'
result = build_handoff(config, root=ROOT, output_dir=stage, archive_history=False)
for name in ('CURRENT_REVIEW.md', 'REVIEW_MANIFEST.json', 'CURRENT_REVIEW.zip'):
    (ROOT / 'handoff' / name).write_bytes((stage / name).read_bytes())
# Client timezone is America/New_York, still EDT on 2026-11-03.
stamp = datetime.now(timezone(timedelta(hours=-4))).strftime('%Y%m%d-%H%M%S')
archive = ROOT / 'handoff' / f'CURRENT_REVIEW({stamp}).zip'
with archive.open('xb') as handle:
    handle.write((stage / 'CURRENT_REVIEW.zip').read_bytes())
with zipfile.ZipFile(archive) as zipped:
    assert zipped.testzip() is None
    manifest = json.loads(zipped.read('REVIEW_MANIFEST.json'))
    for row in manifest['included_files']:
        if row.get('sha256'):
            assert hashlib.sha256(zipped.read(row['bundle_path'])).hexdigest() == row['sha256']
    reports = sum('/pr_play_62/' in name and bool(re.search(r'/\d\d_[A-Z0-9_]+\.md$', name)) for name in zipped.namelist())
    assert reports == 20
    assert not any('.env' in name.split('/') for name in zipped.namelist())
verification = {'path': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                'bytes': archive.stat().st_size, 'crc_valid': True, 'reports': reports,
                'omitted': result['omitted']}
(OUT / 'archive_path.txt').write_text(str(archive) + '\n', encoding='utf-8')
(OUT / 'archive_verification.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
print(json.dumps(verification, indent=2))
