"""Verify the partial live review ZIP using only packaged content."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import REQUIRED_SUMMARY_SECTIONS, sensitive_path_reason

bundle = ROOT / 'handoff/CURRENT_REVIEW.zip'
checked = 0
with zipfile.ZipFile(bundle) as archive:
    assert archive.testzip() is None
    manifest = json.loads(archive.read('REVIEW_MANIFEST.json'))
    summary = archive.read('CURRENT_REVIEW.md').decode()
    assert all(s in summary for s in REQUIRED_SUMMARY_SECTIONS)
    # Identical frozen bootstrap/state files may be deduplicated by the standard builder.
    assert all('duplicate' in str(row).lower() for row in manifest['omitted_artifacts']), manifest['omitted_artifacts']
    for row in manifest['included_files']:
        path = row.get('canonical_source_path')
        if path and row['bundle_path'].startswith('support/'):
            assert sensitive_path_reason(Path(path)) is None
            content = archive.read(row['bundle_path'])
            assert hashlib.sha256(content).hexdigest() == row['sha256']
            assert content == (ROOT / path).read_bytes(), path
            checked += 1
    def read(name):
        return json.loads(archive.read('support/artifacts/atgb/atgb_03/' + name))
    statuses = read('scenario_status.json')
    assert len(statuses) == 10 and sum(s['expected_turns'] for s in statuses) == 37
    assert sum(s['captured_turns'] for s in statuses) == 15
    assert all(s['conversational_scores'] == 'not_evaluated' for s in statuses)
    assert statuses[3]['stop_reason'] == 'provider_call_ceiling_not_observable'
    assert all(s['opening_context_delivery']['delivered'] is None for s in statuses if s['scenario_id'] in {'S07','S09'})
    sheet = read('worksheet.json')
    turns = [t for c in sheet['conversations'] for t in c['turns']]
    assert len(turns) == 15 and all(t['ai_dm_response'] for t in turns)
    assert all(t['human_review_status'] == 'not_reviewed' for t in turns)
    assert read('execution_blocker.json')['approval_blocker_resolved'] is True
    assert read('stage_a_acceptance.json')['accepted'] is True
    assert read('provider_telemetry.json')['application_requests_recorded_sent'] == 12
    assert read('evaluation_status.json')['uncaptured_turns_not_evaluated'] == 22
    assert read('evaluation_status.json')['evaluated_failures'] is None
    assert read('preservation_checks.json')['preserved']
    assert 'INFRASTRUCTURE STOP AT S04' in summary
    for sid in ['S01','S02','S03','S04']:
        assert f'support/artifacts/atgb/atgb_03/{sid}/transcript.md' in archive.namelist()
result = {'ok': True, 'canonical_files_checked': checked, 'zip_size_bytes': bundle.stat().st_size,
    'zip_sha256': hashlib.sha256(bundle.read_bytes()).hexdigest(), 'captured_turns_pending_human_review': 15,
    'uncaptured_turns_not_evaluated': 22, 'bundle_only_partial_live_review': True, 'sensitive_paths_excluded': True}
(ROOT / 'artifacts/atgb/atgb_03/bundle_verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
