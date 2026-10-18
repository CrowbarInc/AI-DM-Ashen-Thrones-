"""Implementing-agent explicit intent labels, separate from automated grading.

Indices refer to the frozen scripted qualification plan, not production rules.
These labels cannot alter routing, provider prompts, source authorization or state.
"""
import json
from pathlib import Path

CORRECTIONS = {'continuity_0': {2, 7}, 'continuity_1': {2, 10}, 'continuity_2': {2, 5},
               'continuity_3': {7, 11}, 'frozen_0': {2, 4, 6}, 'frozen_1': set()}
FOLLOWUPS = {'continuity_0': {3, 5, 10, 12}, 'continuity_1': {3, 5, 6, 8, 12, 14},
             'continuity_2': {3, 6, 8, 10, 11, 13}, 'continuity_3': {3, 5, 9, 13},
             'frozen_0': {8, 10, 12, 14}, 'frozen_1': {2, 4, 6, 8, 10, 12, 14}}
for i in range(4, 8):
    CORRECTIONS[f'operation_{i}'] = {2, 5, 8}
    FOLLOWUPS[f'operation_{i}'] = {3, 6, 9, 11, 13}
GENUINE = {('continuity_0', 13), ('continuity_2', 13), ('continuity_3', 14), ('frozen_1', 4)}


def assess(rows, grades):
    index = {(g['conversation'], g['turn']): g for g in grades}
    result = []
    for r in rows:
        conv, turn = r['conversation'], r['turn']
        corr = turn in CORRECTIONS.get(conv, set())
        follow = turn in FOLLOWUPS.get(conv, set())
        expected = {'correction'} if corr else {'follow_up', 'reference_to_prior_speech'} if follow else {'information_question'}
        plan = r['plan']; prior = r.get('prior_referents') or {}
        act_ok = plan.get('conversational_act') in expected
        target = plan.get('bound_referent_id')
        binding = bool(target and target == prior.get('active_id')) if corr or follow else None
        grade = index.get((conv, turn))
        adequate = bool(grade and grade['relevant'] and grade['sufficient'] and grade['roles_preserved'])
        role_check = None
        # Required communication example, independent of the provider's role names
        # for unrelated relationships. Check all arguments and requested content.
        if conv.startswith('operation_') and turn in {1, 2}:
            prop = plan.get('request_proposition') or {}
            roles = {v['name']: v['value'].lower() for v in prop.get('roles', [])}
            speaker, recipient = ('mara', 'oren') if turn == 1 else ('oren', 'mara')
            role_check = (roles.get('speaker') == speaker and roles.get('recipient') == recipient
                          and roles.get('topic') in {'road', 'the road'} and prop.get('requested_role') == 'message_content')
        result.append({'conversation': conv, 'turn': turn, 'player': r['player'], 'expected_acts': sorted(expected),
            'operation_correct': act_ok, 'referent_correct': binding,
            'correction_success': bool(act_ok and binding and adequate and role_check is not False) if corr else None,
            'follow_up_success': bool(act_ok and binding and adequate) if follow else None,
            'false_clarification': plan.get('response_kind') == 'clarification' and (conv, turn) not in GENUINE,
            'communication_roles': role_check,
            'expected_behavior': 'Revise prior request and preserve unchanged roles.' if corr else
                'Bind the active question and answer the dependent relationship without inventing information.' if follow else 'Interpret the explicit new request.',
            'actual_reason': plan.get('reason'), 'actual_act': plan.get('conversational_act')})
    return result


def summarize_local(scores):
    metrics = {}
    for field in ['operation_correct', 'referent_correct', 'correction_success', 'follow_up_success', 'false_clarification', 'communication_roles']:
        values = [s[field] for s in scores if s[field] is not None]
        metrics[field] = {'count': sum(values), 'denominator': len(values), 'rate': sum(values) / len(values) if values else None}
    return metrics
