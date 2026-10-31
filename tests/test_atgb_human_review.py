"""Offline integrity and aggregation tests; synthetic judgments are never baseline findings."""
import copy
import json
from pathlib import Path

import pytest

from tools.atgb.report_human_review import aggregate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/atgb/atgb_04'


def materials():
    return (json.loads((OUT / 'review_index.json').read_text(encoding='utf-8')),
            json.loads((OUT / 'blank_judgments.json').read_text(encoding='utf-8')))


def test_exact_selection_and_verbatim_evidence():
    index, blank = materials()
    assert len(index['turns']) == len({r['turn_id'] for r in index['turns']}) == 37
    for row in index['turns']:
        source = json.loads((ROOT / row['source_result']).read_text(encoding='utf-8'))
        original = next(t for t in source['turns'] if t['turn_id'] == row['turn_id'])
        assert row['trial'] == source['trial_number'] == (2 if row['scenario_id'] == 'S04' else 1)
        assert original['player_input'] == row['player_input']
        assert original['response_text'] == row['ai_dm_response']
        assert original['state_evidence'] == row['state_evidence']
        prior = [r for r in index['turns'] if r['scenario_id'] == row['scenario_id'] and
                 int(r['turn_id'].split('.')[1]) < int(row['turn_id'].split('.')[1])]
        assert row['preceding_conversation'] == [{k: r[k] for k in
            ('review_id', 'player_input', 'ai_dm_response')} for r in prior]
    assert sum(r['special_review_required'] for r in index['turns']) == 6
    assert all(not value for r in blank['turns'] for k, value in r.items() if k != 'review_id')


def test_blank_review_cannot_produce_rates():
    report = aggregate(*materials())
    assert report['coverage_only']['evaluated_turns_all_three_dimensions'] == 0
    assert not report['gameplay_performance_claim']
    for part in report['by_partition'].values():
        assert all(d['percent'] is None and d['denominator'] == 0 for d in part['dimensions'].values())
        assert all(d['counts']['pending'] == part['available_turns'] for d in part['dimensions'].values())


def entered():
    index, j = materials()
    j.update(reviewer='SYNTHETIC TEST ONLY', reviewed_at='test', human_review_attestation=True)
    return index, j


def test_denominators_exclude_uncertain_and_not_evaluated():
    index, j = entered()
    for row, result in zip(j['turns'][:4], ('pass', 'fail', 'uncertain', 'not_evaluated')):
        row.update(interpretation=result, response=result, authority=result,
                   reviewer_explanation='Synthetic fixture; not a human baseline judgment.')
    report = aggregate(index, j)
    dim = report['by_partition']['development_visible']['dimensions']['response']
    assert (dim['numerator'], dim['denominator'], dim['percent']) == (1, 2, 50)
    assert dim['counts']['uncertain'] == dim['counts']['not_evaluated'] == 1
    assert report['coverage_only']['evaluated_turns_all_three_dimensions'] == 2
    held = report['by_partition']['held_out']['dimensions']['response']
    assert held['denominator'] == 0 and held['percent'] is None


@pytest.mark.parametrize('mutation', ['duplicate', 'wrong_trial', 'unattested', 'unknown_value', 'critical_pass', 'missing_explanation'])
def test_invalid_review_is_rejected(mutation):
    index, j = entered()
    row = j['turns'][0]
    row.update(response='pass', reviewer_explanation='Synthetic test')
    if mutation == 'duplicate':
        j['turns'][1] = copy.deepcopy(row)
    elif mutation == 'wrong_trial':
        next(r for r in j['turns'] if r['review_id'].startswith('S04'))['review_id'] = 'S04.1/trial-1'
    elif mutation == 'unattested':
        j['human_review_attestation'] = False
    elif mutation == 'unknown_value':
        row['response'] = 'great'
    elif mutation == 'critical_pass':
        row.update(failure_severity='critical', authority='pass')
    elif mutation == 'missing_explanation':
        row['reviewer_explanation'] = ''
    with pytest.raises(ValueError):
        aggregate(index, j)


def test_severe_exchanges_and_continuity_counts_are_retained():
    index, j = entered()
    j['turns'][0].update(authority='fail', failure_severity='critical', continuity='lost',
                         reviewer_explanation='Synthetic critical test')
    j['turns'][1].update(response='fail', failure_severity='major', clarification='unnecessary_fail',
                         reviewer_explanation='Synthetic major test')
    report = aggregate(index, j)
    assert report['critical_failures'][0]['ai_dm_response'] == index['turns'][0]['ai_dm_response']
    assert report['major_failures'][0]['player_input'] == index['turns'][1]['player_input']
    assert report['coverage_only']['unnecessary_clarifications'] == 1
    assert report['coverage_only']['continuity_failures'] == 1
