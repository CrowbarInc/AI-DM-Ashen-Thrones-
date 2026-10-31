"""ATGB-05 offline preservation checks; no gameplay/provider imports."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.atgb.report_human_review import validate

OUT = Path(__file__).parent


def main():
    before = json.loads((OUT / 'preservation_before.json').read_text())
    changed = [p for p, digest in before.items()
               if not (ROOT / p).is_file() or
               hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != digest]
    assert not changed, changed
    index = json.loads((ROOT / 'artifacts/atgb/atgb_04/review_index.json').read_text())
    rows = index['turns']
    assert len(rows) == len({r['review_id'] for r in rows}) == 37
    assert len({r['turn_id'] for r in rows}) == 37
    for row in rows:
        source = json.loads((ROOT / row['source_result']).read_text())
        original = next(t for t in source['turns'] if t['turn_id'] == row['turn_id'])
        assert row['trial'] == source['trial_number'] == (2 if row['scenario_id'] == 'S04' else 1)
        assert row['player_input'] == original['player_input']
        assert row['ai_dm_response'] == original['response_text']
        assert row['state_evidence'] == original['state_evidence']
        assert ('/atgb_03/' if row['scenario_id'] in ('S01', 'S02', 'S03')
                else '/atgb_03c/') in row['source_result']
    special = [r for r in rows if r['special_review_required']]
    assert len(special) == 6 and {r['scenario_id'] for r in special} == {'S07', 'S09'}
    for source in json.loads((ROOT / 'artifacts/atgb/atgb_04/evidence_sources.json').read_text()):
        assert hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest() == source['sha256']
    meta = json.loads((OUT / 'requested_assessment_metadata.json').read_text())
    assert meta['human_review_attestation'] is False
    assert meta['individual_judgments'] is None
    assert all(sum(c.values()) == 37 for c in meta['reported_counts'].values())
    blank = json.loads((ROOT / 'artifacts/atgb/atgb_04/blank_judgments.json').read_text())
    validate(index, blank)
    # Exercise the existing guard with a disposable synthetic input only.
    probe = copy.deepcopy(blank)
    probe.update(reviewer='SYNTHETIC GUARD PROBE', reviewed_at='2026-10-18',
                 human_review_attestation=False)
    probe['turns'][0].update(interpretation='uncertain', reviewer_explanation='Guard probe only')
    try:
        validate(index, probe)
    except ValueError as error:
        assert 'human attestation' in str(error)
    else:
        raise AssertionError('Human attestation guard accepted entered AI-style input')
    suites = list(ET.parse(OUT / 'focused_tests.xml').getroot().iter('testsuite'))
    tests = sum(int(s.get('tests', 0)) for s in suites)
    assert tests == 21
    assert all(int(s.get('errors', 0)) == int(s.get('failures', 0)) == 0 for s in suites)
    next_session = (ROOT / 'docs/NEXT_SESSION.md').read_text(encoding='utf-8')
    assert 'import and per-turn verification are pending' in next_session
    result = {
        'scope': 'offline documentation, evidence integrity and existing reporting safeguards',
        'protected_files_checked': len(before), 'protected_files_changed': changed,
        'authoritative_turns': 37, 'unique_turn_ids': 37,
        'source_text_state_and_trial_correspondence': 'pass',
        'ATGB_04_original_source_hashes': 'pass',
        'historical_S04_trial_1': 'preserved separately; excluded from 37',
        'setup_qualified_turns': 6,
        'focused_offline_tests': {'passed': tests, 'failed': 0, 'errors': 0},
        'human_attestation_false_preserved': True,
        'existing_human_guard_rejects_unattested_entries': True,
        'request_reported_aggregate_arithmetic': 'each dimension sums to 37; not individual verification',
        'assessment_import': 'blocked_missing_original_files',
        'assessment_coverage_consistency_and_aggregate_agreement': 'not_verifiable',
        'no_new_gameplay_or_provider_execution': True,
        'gameplay_change': False, 'benchmark_expectation_change': False,
        'broad_regression_and_full_suite': 'not run; no gameplay changes',
        'ATGB_05_completion': 'partial; original assessment files required',
    }
    (OUT / 'validation_results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
