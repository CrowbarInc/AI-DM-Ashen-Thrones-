"""Verify the standard ZIP using workspace-local extraction, offline only."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent


def main():
    with zipfile.ZipFile(ROOT / 'handoff/CURRENT_REVIEW.zip') as z:
        assert z.testzip() is None
        manifest = json.loads(z.read('REVIEW_MANIFEST.json'))
        assert manifest['campaign_id'] == 'atgb_05_baseline_preservation'
        checked = 0
        for row in manifest['included_files']:
            if row.get('canonical_source_path'):
                data = z.read(row['bundle_path'])
                assert hashlib.sha256(data).hexdigest() == row['sha256']
                assert data == (ROOT / row['canonical_source_path']).read_bytes()
                checked += 1
        assert not manifest['omitted_artifacts'], manifest['omitted_artifacts']
        # Explicit workspace output avoids this machine's sandbox temp ACL failure.
        extraction = ROOT / 'development/tmp/atgb_05_bundle_review'
        extraction.mkdir(parents=True, exist_ok=True)
        z.extractall(extraction)
    support = extraction / 'support'
    index = json.loads((support / 'artifacts/atgb/atgb_04/review_index.json').read_text())
    assert len(index['turns']) == len({r['review_id'] for r in index['turns']}) == 37
    assert all(r['trial'] == (2 if r['scenario_id'] == 'S04' else 1) for r in index['turns'])
    assert sum(r['special_review_required'] for r in index['turns']) == 6
    summary = (extraction / 'CURRENT_REVIEW.md').read_text(encoding='utf-8')
    assert all(x in summary for x in ['Executive Summary', 'Changes Made',
        'What Was Tested', 'Behavioral Evidence', 'Decisions Requiring Human Review',
        'Known Problems', 'Missing Concepts', 'What This Campaign Does NOT Prove',
        'Recommended Next Step', 'Review Bundle Contents'])
    assert 'PARTIAL' in summary and 'missing' in summary.lower()
    meta = json.loads((support / 'artifacts/atgb/atgb_05/requested_assessment_metadata.json').read_text())
    assert meta['human_review_attestation'] is False and meta['individual_judgments'] is None
    result = subprocess.run([sys.executable, str(support / 'tools/atgb/report_human_review.py'),
        '--index', str(support / 'artifacts/atgb/atgb_04/review_index.json'),
        '--judgments', str(support / 'artifacts/atgb/atgb_04/blank_judgments.json'),
        '--output', str(extraction / 'pending.json')], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads((extraction / 'pending.json').read_text())
    assert report['coverage_only']['turns_with_any_human_judgment'] == 0
    assert report['gameplay_performance_claim'] is False
    record = {'zip_crc': 'pass', 'canonical_files_hash_checked': checked,
        'extracted_baseline_turns': 37, 'trial_provenance': 'pass',
        'setup_qualifications': 6, 'explicit_partial_status': 'pass',
        'attestation_false': 'pass', 'missing_individual_judgments_explicit': True,
        'isolated_pending_human_reporting': 'pass',
        'environment_note': 'Initial system-temp extraction failed with sandbox ACL PermissionError; workspace-local extraction passed.'}
    (OUT / 'bundle_verification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
