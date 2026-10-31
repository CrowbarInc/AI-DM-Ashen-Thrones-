"""Verify standalone ATGB-05A review export, with no gameplay/provider imports."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent


def main():
    with zipfile.ZipFile(ROOT / 'handoff/CURRENT_REVIEW.zip') as z:
        assert z.testzip() is None
        manifest = json.loads(z.read('REVIEW_MANIFEST.json'))
        assert manifest['campaign_id'] == 'atgb_05a_assessment_import'
        assert not manifest['omitted_artifacts'], manifest['omitted_artifacts']
        checked = 0
        for row in manifest['included_files']:
            if row.get('canonical_source_path'):
                data = z.read(row['bundle_path'])
                assert hashlib.sha256(data).hexdigest() == row['sha256']
                assert data == (ROOT / row['canonical_source_path']).read_bytes()
                checked += 1
        extraction = ROOT / 'development/tmp/atgb_05a_bundle_review'
        extraction.mkdir(parents=True, exist_ok=True)
        z.extractall(extraction)
    support = extraction / 'support'
    evidence = support / 'artifacts/atgb/atgb_05a'
    summary = (extraction / 'CURRENT_REVIEW.md').read_text(encoding='utf-8')
    assert all(x in summary for x in ['Executive Summary', 'Changes Made',
        'What Was Tested', 'Behavioral Evidence', 'Decisions Requiring Human Review',
        'Known Problems', 'Missing Concepts', 'What This Campaign Does NOT Prove',
        'Recommended Next Step', 'Review Bundle Contents'])
    assert 'INITIAL OPERATIONAL SETUP CLOSED' in summary
    assert 'AUTHENTICATED HUMAN SCORING PENDING' in summary
    index = json.loads((support / 'artifacts/atgb/atgb_04/review_index.json').read_text())
    judgments = json.loads((evidence / 'assessment/ATGB_04_review_judgments.json').read_text())
    record = json.loads((evidence / 'assessment_import_verification.json').read_text())
    assert len(index['turns']) == len(judgments['turns']) == 37
    assert {r['review_id'] for r in judgments['turns']} == {r['review_id'] for r in index['turns']}
    assert judgments['human_review_attestation'] is False
    assert not record['discrepancies'] and record['status'] == 'verified_provisional_import'
    provenance = json.loads((evidence / 'source_manifest.json').read_text())
    for item in provenance['originals']:
        data = (support / item['preserved_path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item['sha256']
        assert data == (ROOT / item['supplied_path']).read_bytes()
    target = extraction / 'must_not_write_human_report.json'
    assert not target.exists()
    result = subprocess.run([sys.executable, str(support / 'tools/atgb/report_human_review.py'),
        '--index', str(support / 'artifacts/atgb/atgb_04/review_index.json'),
        '--judgments', str(evidence / 'assessment/ATGB_04_review_judgments.json'),
        '--output', str(target)], capture_output=True, text=True)
    assert result.returncode != 0 and 'explicit human attestation' in result.stderr
    assert not target.exists()
    suites = list(ET.parse(OUT / 'focused_tests.xml').getroot().iter('testsuite'))
    assert sum(int(s.get('tests', 0)) for s in suites) == 21
    assert all(int(s.get('errors', 0)) == int(s.get('failures', 0)) == 0 for s in suites)
    output = {'zip_crc': 'pass', 'canonical_files_hash_checked': checked,
        'omitted_files': 0, 'standalone_review_sections': 'pass',
        'exact_original_assessment_bytes': 'pass', 'baseline_turns': 37,
        'import_record_discrepancies': [], 'closure_status': 'pass',
        'isolated_human_reporter_rejects_original_assessment': True,
        'no_human_report_written': True, 'focused_offline_tests_passed': 21}
    (OUT / 'bundle_verification.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output))


if __name__ == '__main__':
    main()
