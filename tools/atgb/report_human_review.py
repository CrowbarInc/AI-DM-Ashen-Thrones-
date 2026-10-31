"""Aggregate explicitly entered human judgments. Never judges transcript content."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

RESULTS = {'', 'pass', 'fail', 'uncertain', 'not_evaluated', 'unchecked'}
ALLOWED = {
    'interpretation': RESULTS, 'response': RESULTS, 'authority': RESULTS,
    'failure_severity': {'', 'minor', 'major', 'critical', 'uncertain', 'not_evaluated'},
    'clarification': {'', 'none', 'necessary_pass', 'unnecessary_fail',
                      'missing_when_needed_fail', 'uncertain', 'not_evaluated'},
    'continuity': {'', 'not_applicable', 'preserved', 'lost', 'uncertain', 'not_evaluated'},
}


def validate(index, judgments):
    if judgments.get('review_package') != 'ATGB-04' or judgments.get('rubric_version') != index['rubric_version']:
        raise ValueError('Wrong review package or rubric')
    expected = {r['review_id'] for r in index['turns']}
    rows = judgments.get('turns', [])
    if len(rows) != len(expected) or {r['review_id'] for r in rows} != expected:
        raise ValueError('Missing, duplicate, unknown or wrong-trial rows')
    any_entered = any(any(r.get(k, '') for k in (*ALLOWED, 'reviewer_explanation')) for r in rows)
    convs = judgments.get('conversations', [])
    expected_convs = {(c['scenario_id'], c['trial']) for c in index['conversations']}
    if len(convs) != len(expected_convs) or {(c['scenario_id'], c['trial']) for c in convs} != expected_convs:
        raise ValueError('Missing, duplicate or wrong-trial conversations')
    any_entered |= any(c.get('qualitative_observations', '') for c in convs)
    if any_entered and (judgments.get('human_review_attestation') is not True or
                        not judgments.get('reviewer', '').strip() or not judgments.get('reviewed_at', '').strip()):
        raise ValueError('Entered judgments require reviewer, date and explicit human attestation')
    for r in rows:
        for k, values in ALLOWED.items():
            if r.get(k, '') not in values:
                raise ValueError(f"Unknown {k} for {r['review_id']}")
        if any(r.get(k, '') for k in ALLOWED) and not r.get('reviewer_explanation', '').strip():
            raise ValueError(f"Reviewer explanation missing: {r['review_id']}")
        if r.get('failure_severity') == 'critical' and r.get('authority') != 'fail':
            raise ValueError('Rubric requires critical severity to have authority fail')
        if r.get('failure_severity') == 'major' and r.get('response') != 'fail':
            raise ValueError('Rubric requires major severity to have response fail')
        if r.get('clarification') == 'unnecessary_fail' and (r.get('response') != 'fail' or
                                                            r.get('failure_severity') not in ('major', 'critical')):
            raise ValueError('Rubric assigns unnecessary clarification a major response failure')
    return {r['review_id']: r for r in rows}


def counts(rows, key, positive='pass', negative='fail'):
    c = Counter(r.get(key, '') for r in rows)
    n = c[positive] + c[negative]
    return {'counts': {v or 'pending': c[v] for v in sorted(ALLOWED[key])},
            'numerator': c[positive], 'denominator': n,
            'percent': round(100 * c[positive] / n, 2) if n else None}


def summarize(rows):
    complete_dimensions = sum(all(r.get(k) in ('pass', 'fail') for k in
                                  ('interpretation', 'response', 'authority')) for r in rows)
    out = {'available_turns': len(rows), 'turns_with_any_human_judgment': sum(any(r.get(k) for k in ALLOWED) for r in rows),
           'evaluated_turns_all_three_dimensions': complete_dimensions,
           'dimensions': {k: counts(rows, k) for k in ('interpretation', 'response', 'authority')},
           'failure_severity': counts(rows, 'failure_severity')['counts'],
           'clarification': counts(rows, 'clarification')['counts'],
           'continuity': counts(rows, 'continuity', 'lost', 'preserved')}
    out['authority_violations'] = {'count': sum(r.get('authority') == 'fail' for r in rows),
                                  'evaluated_authority_turns': out['dimensions']['authority']['denominator']}
    out['unnecessary_clarifications'] = out['clarification']['unnecessary_fail']
    out['continuity_failures'] = out['continuity']['counts']['lost']
    return out


def aggregate(index, judgments):
    entered = validate(index, judgments)
    rows = [dict(r, **entered[r['review_id']]) for r in index['turns']]
    def exchanges(severity):
        return [{k: r[k] for k in ('review_id', 'primary_capability', 'partition', 'player_input',
                                   'ai_dm_response', 'preceding_conversation', 'reviewer_explanation')}
                for r in rows if r.get('failure_severity') == severity]
    # Ordering intentionally surfaces critical and major exchanges before rates.
    report = {'review_package': 'ATGB-04', 'rubric_version': index['rubric_version'],
              'human_reviewer': judgments.get('reviewer', ''), 'reviewed_at': judgments.get('reviewed_at', ''),
              'review_status': 'pending_or_partial', 'gameplay_performance_claim': False,
              'critical_failures': exchanges('critical'), 'major_failures': exchanges('major'),
              'coverage_only': summarize(rows)}
    # Overall rates are deliberately suppressed; evidence classes retain separate rates.
    for dimension in report['coverage_only']['dimensions'].values():
        dimension.pop('percent')
    report['coverage_only']['continuity'].pop('percent')
    report['by_partition'] = {p: summarize([r for r in rows if r['partition'] == p])
                              for p in sorted({r['partition'] for r in rows})}
    report['by_primary_capability_and_partition'] = {
        cap: {p: summarize([r for r in rows if r['primary_capability'] == cap and r['partition'] == p])
              for p in sorted({r['partition'] for r in rows if r['primary_capability'] == cap})}
        for cap in sorted({r['primary_capability'] for r in rows})}
    report['conversation_observations'] = judgments['conversations']
    report['special_review_entries'] = [{k: r[k] for k in ('review_id', 'setup_limitations',
                                                           'interpretation', 'response', 'authority',
                                                           'reviewer_explanation')}
                                         for r in rows if r['special_review_required']]
    report['efficiency'] = {'scope': 'Original host telemetry only; missing values preserved; not scored.',
                           'turns': [{'review_id': r['review_id'], **r['telemetry']} for r in rows]}
    if all(all(r.get(k) in ('pass', 'fail', 'uncertain', 'not_evaluated', 'unchecked') for k in
               ('interpretation', 'response', 'authority')) and r.get('clarification') and r.get('continuity')
           for r in rows):
        report['review_status'] = 'human_entries_supplied_check_qualifications'
    report['limitations'] = [
        'No universal gameplay score. Zero entered failures is not evidence of no failures.',
        'S07/S09 opening-dependent criteria need special review; missing setup is not gameplay failure.',
        'Partial reviews and uncertain/not_evaluated/unchecked values are excluded from pass/fail denominators.',
        'Held-out material was previously exposed; no independent unseen generalization.',
        'Original S04 trial 1 excluded. Single selected trial; no stability claim.',
        'Review attribution is self-attested; retain independent reviewer files and disagreements.',
        'Reported coverage counts are not gameplay success rates. Authority compliance rates use pass/(pass+fail).',
        'Continuity percentage is the loss rate: lost/(lost+preserved); not_applicable excluded.']
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--index', required=True, type=Path)
    p.add_argument('--judgments', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    index = json.loads(args.index.read_text(encoding='utf-8'))
    judgments = json.loads(args.judgments.read_text(encoding='utf-8'))
    try:
        report = aggregate(index, judgments)
    except (ValueError, KeyError, TypeError) as exc:
        p.error(str(exc))
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"Report written: {report['review_status']}; human performance claim remains false.")


if __name__ == '__main__':
    main()
