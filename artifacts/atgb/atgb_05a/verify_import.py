"""Offline integrity of supplied provisional evidence; does not score exchanges."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.atgb.report_human_review import ALLOWED, validate

OUT = Path(__file__).parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    manifest = read(OUT / 'source_manifest.json')
    for item in manifest['originals']:
        supplied = (ROOT / item['supplied_path']).read_bytes()
        preserved = (ROOT / item['preserved_path']).read_bytes()
        assert supplied == preserved
        assert hashlib.sha256(preserved).hexdigest() == item['sha256']
    before = read(OUT / 'preservation_before.json')
    for path, digest in before.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    previous = read(ROOT / 'artifacts/atgb/atgb_05/preservation_before.json')
    for path, digest in previous.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    index = read(ROOT / 'artifacts/atgb/atgb_04/review_index.json')
    assessment = read(OUT / 'assessment/ATGB_04_review_judgments.json')
    summary = (OUT / 'assessment/ATGB_04_review_summary.md').read_text(encoding='utf-8')
    rows = assessment['turns']
    selected = {r['review_id']: r for r in index['turns']}
    assert len(rows) == len(selected) == 37
    assert len({r['review_id'] for r in rows}) == 37
    assert {r['review_id'] for r in rows} == set(selected)
    assert assessment['review_package'] == index['review_package'] == 'ATGB-04'
    assert assessment['rubric_version'] == index['rubric_version'] == 'atgb-rubric-01'
    assert assessment['human_review_attestation'] is False
    assert 'ChatGPT (GPT-6)' in assessment['reviewer']
    assert assessment['reviewed_at']
    assert len(assessment['conversations']) == 10
    assert {(r['scenario_id'], r['trial']) for r in assessment['conversations']} == {
        (r['scenario_id'], r['trial']) for r in index['conversations']}
    for row in rows:
        baseline = selected[row['review_id']]
        assert row['review_id'] == f"{baseline['turn_id']}/trial-{baseline['trial']}"
        assert baseline['trial'] == (2 if baseline['scenario_id'] == 'S04' else 1)
        source = read(ROOT / baseline['source_result'])
        turn = next(t for t in source['turns'] if t['turn_id'] == baseline['turn_id'])
        assert source['trial_number'] == baseline['trial']
        assert baseline['player_input'] == turn['player_input']
        assert baseline['ai_dm_response'] == turn['response_text']
        assert baseline['state_evidence'] == turn['state_evidence']
        assert ('/atgb_03/' if baseline['scenario_id'] in ('S01', 'S02', 'S03')
                else '/atgb_03c/') in baseline['source_result']
        for key, labels in ALLOWED.items():
            assert row[key] in labels, (row['review_id'], key)
        assert all(row[k] in ('pass', 'fail', 'uncertain') for k in
                   ('interpretation', 'response', 'authority'))
        assert row['reviewer_explanation'].strip()
        if row['failure_severity'] == 'critical':
            assert row['authority'] == 'fail'
        if row['failure_severity'] == 'major':
            assert row['response'] == 'fail'
        if row['clarification'] == 'unnecessary_fail':
            assert row['response'] == 'fail' and row['failure_severity'] in ('major', 'critical')
        if row['failure_severity'] == 'minor':
            assert row['response'] == row['authority'] == 'pass'
    # Existing human-reporting authority must reject the exact original input.
    try:
        validate(index, assessment)
    except ValueError as exc:
        assert 'explicit human attestation' in str(exc)
        guard = str(exc)
    else:
        raise AssertionError('Original AI assessment unexpectedly accepted as human review')
    fields = ('interpretation', 'response', 'authority')
    counts = {k: {v: sum(r[k] == v for r in rows) for v in ('pass', 'fail', 'uncertain')}
              for k in fields}
    for field, label in zip(fields, ('Interpretation', 'Response adequacy', 'Authority')):
        match = re.search(r'^\| ' + re.escape(label) + r' \| (\d+) \| (\d+) \| (\d+) \| (\d+)/(\d+) \((\d+(?:\.\d+)?)%', summary, re.M)
        assert match, label
        passed, failed, uncertain, numerator, denominator = map(int, match.groups()[:5])
        assert counts[field] == {'pass': passed, 'fail': failed, 'uncertain': uncertain}
        assert passed + failed + uncertain == 37
        assert numerator == passed and denominator == passed + failed
        assert round(100 * passed / denominator, 1) == float(match.group(6))
    other = {k: dict(Counter(r[k] for r in rows)) for k in
             ('failure_severity', 'clarification', 'continuity')}
    assert other['failure_severity'] == {'': 9, 'minor': 3, 'major': 25}
    assert other['clarification'] == {'none': 30, 'necessary_pass': 1,
                                    'unnecessary_fail': 5, 'missing_when_needed_fail': 1}
    assert other['continuity'] == {'preserved': 11, 'lost': 11, 'not_applicable': 15}
    assert '1 necessary and appropriate; 5 unnecessary; 1 missing focused clarification' in summary
    assert '11 preserved, 11 lost, 15 not applicable' in summary
    assert 'Three successful turns have minor style defects' in summary
    assert 'Twenty-five turns have major response failures' in summary
    assert 'No confirmed critical failure was assigned' in summary
    by_partition = {p: dict(Counter(r['response'] for r in rows if
                                  selected[r['review_id']]['partition'] == p))
                    for p in sorted({r['partition'] for r in index['turns']})}
    assert by_partition == {'development_visible': {'pass': 7, 'fail': 18},
                           'related_variation': {'pass': 2, 'fail': 2},
                           'held_out': {'pass': 1, 'fail': 5, 'uncertain': 2}}
    assert 'development-visible 7/25; related variation 2/4' in summary
    assert 'held-out 1/6 determinate, 2 uncertain' in summary
    uncertain_ids = [r['review_id'] for r in rows if r['authority'] == 'uncertain']
    assert set(uncertain_ids) == {'S03.4/trial-1', 'S05.4/trial-1'}
    assert all('faction' in r['reviewer_explanation'].lower() for r in rows
               if r['review_id'] in uncertain_ids)
    special = [r for r in rows if selected[r['review_id']]['special_review_required']]
    assert len(special) == 6
    assert all('opening' in r['reviewer_explanation'].lower() or
               'undelivered shout' in r['reviewer_explanation'].lower() or
               'posture' in r['reviewer_explanation'].lower() for r in special)
    assert all(selected[r['review_id']]['setup_limitations'] for r in special)
    assert all(r['interpretation'] == r['response'] == 'uncertain' for r in special
               if r['review_id'] in ('S07.1/trial-1', 'S07.3/trial-1'))
    assert 'S07 and S09 lacked the authored opening' in summary
    assert 'not independently unseen' in summary
    orientation = (ROOT / 'docs/NEXT_SESSION.md').read_text(encoding='utf-8')
    report = (ROOT / 'development/reports/atgb_05_baseline_preservation.md').read_text(encoding='utf-8')
    assert 'provisional assessment is imported and verified' in orientation
    assert 'Await review before starting the next Product Realization investigation' in orientation
    assert 'Complete: provisional assessment imported and verified' in report
    result = {'status': 'verified_provisional_import', 'discrepancies': [],
        'scope': 'Artifact integrity and rubric consistency; no re-scoring or human adjudication',
        'authoritative_turns': 37, 'unique_review_ids': 37,
        'baseline_source_text_state_trial_match': True,
        'scenario_conversation_trials_match': True, 'rubric_consistency': 'pass',
        'aggregate_summary_agreement': 'pass', 'dimension_counts': counts,
        'other_summary_counts': other, 'response_counts_by_partition': by_partition,
        'setup_qualified_review_ids': [r['review_id'] for r in special],
        'authority_uncertain_review_ids': uncertain_ids,
        'source_files_byte_identical': True, 'source_manifest': 'source_manifest.json',
        'protected_entry_files_unchanged': len(before),
        'protected_ATGB_05_files_unchanged': len(previous),
        'human_review_attestation': False, 'human_report_rejection': guard,
        'authenticated_human_scoring': 'pending',
        'operational_ATGB_v1_setup': 'complete', 'conversational_competence': 'not_established',
        'gameplay_behavior_changed': False, 'live_provider_requests': 0}
    (OUT / 'assessment_import_verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
