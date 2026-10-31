"""Verify packaged continuation using standard manifest plus exact benchmark evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import REQUIRED_SUMMARY_SECTIONS, sensitive_path_reason
from tools.atgb.accounting import inspect_ledger, live_accounting_readiness
from tools.atgb.fixtures import load_corpus
from tools.validation_evidence import validate_packet

bundle = ROOT / 'handoff/CURRENT_REVIEW.zip'
checked = 0
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    manifest = json.loads(z.read('REVIEW_MANIFEST.json'))
    assert manifest['campaign_id'] == 'atgb_03c_live_baseline_continuation'
    summary = z.read('CURRENT_REVIEW.md').decode()
    assert all(s in summary for s in REQUIRED_SUMMARY_SECTIONS)
    assert all('duplicate' in str(row).lower() for row in manifest['omitted_artifacts'])
    for row in manifest['included_files']:
        source = row.get('canonical_source_path')
        if source and row['bundle_path'].startswith('support/'):
            assert sensitive_path_reason(Path(source)) is None
            content = z.read(row['bundle_path'])
            assert hashlib.sha256(content).hexdigest() == row['sha256']
            assert content == (ROOT / source).read_bytes(), source
            checked += 1
    def read(name):
        return json.loads(z.read('support/artifacts/atgb/atgb_03c/' + name))
    coverage = read('baseline_coverage.json')
    assert coverage['continuation_captured_turns'] == 24
    assert coverage['combined_baseline_unique_turns_captured'] == 37
    assert coverage['total_observations_including_historical_partial'] == 39
    assert not coverage['review_complete'] and not coverage['gameplay_performance_claim']
    assert coverage['original_partial_S04_trial_1']['included_in_baseline_set'] is False
    assert read('preservation_checks.json')['all_unchanged']
    for filename, count in [('continuation_worksheet.json', 24), ('combined_baseline_worksheet.json', 37)]:
        sheet = read(filename)
        rows = [t for c in sheet['conversations'] for t in c['turns']]
        assert len(rows) == count and len({t['turn_id'] for t in rows}) == count
        assert all(t['human_review_status'] == 'not_reviewed' for t in rows)
        assert all(all(t[k] == 'unchecked' for k in ('interpretation_assessment', 'response_assessment', 'authority_assessment')) for t in rows)
    fixtures = {s['scenario_id']: s for s in load_corpus(ROOT)['scenarios']}
    expected_digest = 'c12cb0dfe6a31980b4ecc00a59cc359a143a76452e517a36ad76753a6145561a'
    totals = 0
    for n in range(4, 11):
        sid = f'S{n:02}'
        r = read(sid + '/result.json')
        assert r['trial_number'] == (2 if n == 4 else 1)
        assert not r['stop_reason']
        assert [(t['turn_id'], t['player_input']) for t in r['turns']] == [(t['turn_id'], t['player_input']) for t in fixtures[sid]['turns']]
        assert r['scenario_records'][0]['preflight']['ok']
        assert r['scenario_records'][0]['preflight']['starting_state_sha256'] == expected_digest
        assert r['turns'][0]['state_evidence']['before']['transcript_entries'] == 0
        last = r['turns'][-1]['provider_accounting']['process_snapshot']
        observed = inspect_ledger(OUT / sid / 'provider_usage.jsonl', last)
        assert observed['status'] == 'recorded' and not observed['pending_requests']
        assert last['total_tokens'] is not None and not last['stopped']
        totals += last['requests']
        assert f'support/artifacts/atgb/atgb_03c/{sid}/transcript.md' in z.namelist()
    assert totals == 23
    opening = read('opening_context.json')
    assert {r['scenario_id'] for r in opening} == {'S07', 'S09'}
    assert all(r['context_present_in_world_state'] and r['opening_delivered_before_first_player_turn'] is False and not r['extra_context_injected'] for r in opening)
    assert 'support/artifacts/atgb/atgb_03/S04/transcript.md' in z.namelist()
    packet = read('behavioral_evidence/evidence_manifest.json')
    assert not validate_packet(packet) and len(packet['examples']) == 24
    assert all(t['semantic_result'] is None and t['human_review']['status'] == 'UNREVIEWED' for t in packet['examples'])
assert live_accounting_readiness(ROOT)['ok']
before = json.loads((OUT / 'provenance_before.json').read_text())
assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in before['source_sha256'].items())
status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
initial_status = (OUT / 'initial_git_status.txt').read_text()
record = {'ok': True, 'canonical_files_checked': checked, 'zip_bytes': bundle.stat().st_size,
    'zip_sha256': hashlib.sha256(bundle.read_bytes()).hexdigest(), 'continuation_turns': 24,
    'unique_baseline_turns': 37, 'all_human_judgments_pending': True,
    'protected_file_hashes_unchanged': len(before['source_sha256']),
    'production_and_harness_changes_this_pass': False,
    'worktree_dirty_before_and_after': bool(initial_status.strip()) and bool(status.strip()),
    'new_porcelain_entries': sorted(set(status.splitlines()) - set(initial_status.splitlines())),
    'self_contained_bundle_review': True}
(OUT / 'bundle_verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
