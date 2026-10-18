"""Host-owned, bounded question memory. Never a source of disclosure authority.

Interpretation is read-only. A validated plan is committed only with its sealed
delivered exchange. Session persistence already supplies an integrity envelope.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping
from uuid import uuid4

KEY = 'question_referents'
MAX_RECORDS = 24
FIELDS = ('predicate', 'subject', 'object', 'missing_argument', 'temporal', 'spatial', 'epistemic', 'negated')
OPERATIONS = {
    'replace_subject': {'subject'}, 'replace_object': {'object'},
    'replace_relationship': {'predicate', 'missing_argument'},
    'replace_qualifier': {'temporal', 'spatial', 'epistemic', 'negated'},
    'replace_roles': {'subject', 'object', 'missing_argument'},
    'replace_addressee': {'addressee_id'},
    'clarify_argument': set(FIELDS), 'reject_interpretation': set(FIELDS),
    'replace_role_value': {'roles'}, 'reassign_roles': {'roles'},
    'replace_requested_argument': {'requested_role', 'missing_argument'},
}
FOLLOW_UPS = ('source_attribution', 'explanation', 'evidence', 'temporal_modification',
              'alternative_argument', 'speech_clarification')


def operation_schema(extended=False):
    from game.semantic_correspondence import object_schema
    properties = {
        'target_referent_id': {'type': 'string'},
        'operation': {'type': 'string', 'enum': ['', *OPERATIONS]},
        'changed_fields': {'type': 'array', 'items': {'type': 'string', 'enum': [*FIELDS, 'addressee_id', 'roles', 'requested_role']}, 'maxItems': 11},
        'follow_up_relationship': {'type': 'string', 'enum': ['', *FOLLOW_UPS]},
    }
    if extended:
        properties.update(changed_roles={'type': 'array', 'items': {'type': 'string'}, 'maxItems': 8},
                          evidence={'type': 'string', 'maxLength': 400},
                          target_evidence={'type': 'string', 'maxLength': 160})
    return object_schema(properties)


def clean_operation(raw):
    if not isinstance(raw, Mapping):
        return None
    extended = bool(set(raw) & {'changed_roles', 'evidence', 'target_evidence'})
    if set(raw) != set(operation_schema(extended)['properties']):
        return None
    if not isinstance(raw['target_referent_id'], str) or len(raw['target_referent_id']) > 100:
        return None
    if not isinstance(raw['operation'], str) or not isinstance(raw['follow_up_relationship'], str):
        return None
    if raw['operation'] not in {'', *OPERATIONS} or raw['follow_up_relationship'] not in {'', *FOLLOW_UPS}:
        return None
    fields = raw['changed_fields']
    if not isinstance(fields, list) or len(fields) > 11 or any(not isinstance(f, str) or f not in {*FIELDS, 'addressee_id', 'roles', 'requested_role'} for f in fields):
        return None
    if len(fields) != len(set(fields)):
        return None
    if extended:
        names = raw['changed_roles']
        from game.semantic_operations import NAME
        if not isinstance(names, list) or len(names) > 8 or any(not isinstance(n, str) or not NAME.fullmatch(n) for n in names):
            return None
        if len(names) != len(set(names)):
            return None
        if any(not isinstance(raw[k], str) or len(raw[k]) > limit for k, limit in [('evidence', 400), ('target_evidence', 160)]):
            return None
    return deepcopy(dict(raw))


def state(session):
    ctx = (session or {}).get('conversational_context') or {}
    value = ctx.get(KEY) or {}
    return value if isinstance(value, Mapping) and value.get('version') == 1 else {}


def active(session):
    memory = state(session)
    return next((deepcopy(r) for r in memory.get('records', [])
                 if r['referent_id'] == memory.get('active_id')), {})


def as_prior(record):
    if not record:
        return {}
    return {**deepcopy(record), 'locked': True, 'question_text': record['witness_text'],
            'response_kind': record['answer_status'], 'selected_source_ids': []}


def context(session):
    memory = state(session)
    # Only accepted questions and delivery links; no authored or protected facts.
    keys = ('referent_id', 'parent_referent_id', 'revision', 'addressee_id',
            'requested_relationship', 'request_proposition', 'answer_status',
            'focus_status', 'follow_up_relationship', 'proposition_referent_id', 'delivered_speech', 'corrected_fields',
            'semantic_answer_status', 'missing_roles', 'outstanding_clarification')
    recent = list(memory.get('records', []))[-6:]
    focused = active(session)
    if focused and not any(r['referent_id'] == focused['referent_id'] for r in recent):
        recent = [focused, *recent[-5:]]
    return {'conversation_id': memory.get('conversation_id', ''),
            'active_id': memory.get('active_id', ''),
            'recent': [{k: deepcopy(r.get(k)) for k in keys} for r in recent]}


def bind(plan, session, utterance, participants, explicit_addressee=''):
    """Validate target and apply a bounded delta, preserving unmodified meaning.

    Returns (plan, selected prior, error). Never changes session or world state.
    Legacy plans remain on the earlier bounded compatibility behavior.
    """
    op = plan.get('referent_operation')
    if op is None:
        return plan, {}, ''
    memory = state(session)
    target_id = op['target_referent_id']
    act = plan['conversational_act']
    if act == 'other':
        return plan, {}, ''
    if act == 'reference_to_prior_speech':
        plan = deepcopy(plan)
        plan['referent_operation']['follow_up_relationship'] = 'speech_clarification'
        op = plan['referent_operation']
        act = 'follow_up'
    if act == 'information_question':
        if target_id or op['operation'] or op['changed_fields'] or op['follow_up_relationship']:
            return plan, {}, 'unexpected_referent_operation'
        return plan, {}, ''
    records = memory.get('records', [])
    if not target_id and not plan.get('clarification_needed'):
        target_id = memory.get('active_id', '')
    target = next((r for r in records if r['referent_id'] == target_id), None)
    if not target or target.get('conversation_id') != memory.get('conversation_id'):
        return plan, {}, 'invalid_referent_target'
    if target.get('correction_status') == 'corrected':
        return plan, {}, 'stale_correction_target'
    if target_id != memory.get('active_id'):
        # An old ID alone is insufficient to select a different question.
        # Without an explicit distinguishing argument the host retains focus.
        from game.semantic_correspondence import normalize
        words = normalize(utterance)
        proposition = target.get('request_proposition', {})
        args = [proposition.get(k, '') for k in ('subject', 'object')]
        args.extend(r['value'] for r in proposition.get('roles', []))
        distinctions = [value for value in args if value and normalize(value) in words]
        others = [r for r in records if r['referent_id'] != target_id and r.get('correction_status') != 'corrected']
        if not any(all(value not in [other.get('request_proposition', {}).get(k) for k in ('subject', 'object')]
                       + [r['value'] for r in other.get('request_proposition', {}).get('roles', [])]
                       for other in others) for value in distinctions):
            return plan, {}, 'ambiguous_historical_target'
    if target['addressee_id'] not in {p['id'] for p in participants}:
        return plan, {}, 'referent_speaker_absent'
    if explicit_addressee and explicit_addressee != target['addressee_id'] and op['operation'] != 'replace_addressee':
        return plan, {}, 'referent_speaker_mismatch'
    prior = as_prior(target)
    if 'request_proposition' not in plan or not target.get('request_proposition'):
        return plan, prior, 'referent_proposition_missing'
    result = deepcopy(plan)
    result['referent_operation']['target_referent_id'] = target_id
    old = target['request_proposition']
    proposed = result['request_proposition']
    changed = set(op['changed_fields'])
    evidence = op.get('evidence')
    if evidence is not None and (not evidence or evidence.casefold() not in utterance.casefold()):
        return plan, prior, 'unwitnessed_operation'
    if act == 'correction' or act == 'clarification_response':
        if act == 'clarification_response' and target['answer_status'] != 'clarification':
            return plan, prior, 'no_pending_clarification'
        if op['operation'] == 'reject_interpretation':
            return plan, prior, 'rejected_interpretation'
        if not op['operation'] or not changed or not changed <= OPERATIONS[op['operation']] or op['follow_up_relationship']:
            return plan, prior, 'invalid_correction_operation'
        if 'addressee_id' in changed and (not explicit_addressee or result['addressee_id'] != explicit_addressee):
            return plan, prior, 'ungrounded_addressee_replacement'
        if 'roles' in old:
            from game.semantic_operations import apply_role_delta
            prop, role_error = apply_role_delta(old, proposed, op, utterance, participants)
            if role_error:
                return plan, prior, role_error
        else:
            prop = deepcopy(old)
        if op['operation'] == 'replace_role_value' and len(op.get('changed_roles', [])) != 1:
            return plan, prior, 'invalid_role_delta'
        for field in changed - {'addressee_id', 'roles', 'requested_role'}:
            prop[field] = proposed[field]
            if field in {'predicate', 'subject', 'object'}:
                evidence = proposed[field + '_evidence']
                if proposed[field] and (not evidence or evidence.casefold() not in utterance.casefold()):
                    return plan, prior, 'unwitnessed_correction'
                prop[field + '_evidence'] = evidence
            elif field in {'temporal', 'spatial', 'epistemic'} and proposed[field] and proposed[field].casefold() not in utterance.casefold():
                return plan, prior, 'unwitnessed_qualifier'
        # Omitted fields inherit; a nonempty unlisted semantic change is rejected.
        for field in FIELDS:
            if field not in changed and proposed[field] not in ('', old[field]):
                return plan, prior, 'unlisted_correction_change'
        if all(prop.get(f) == old.get(f) for f in (*FIELDS, 'roles', 'requested_role')) and 'addressee_id' not in changed:
            return plan, prior, 'empty_correction'
        result['request_proposition'] = prop
        result['correction_target'] = prior['question_text']
        result['correction_of_prior_question'] = True
    elif act == 'follow_up':
        relation = op['follow_up_relationship']
        if relation not in FOLLOW_UPS or op['operation']:
            return plan, prior, 'invalid_follow_up_operation'
        if relation == 'temporal_modification':
            if changed != {'temporal'} or not proposed['temporal'] or proposed['temporal'].casefold() not in utterance.casefold():
                return plan, prior, 'ungrounded_temporal_follow_up'
            result['request_proposition'] = {**old, 'temporal': proposed['temporal']}
        elif relation == 'alternative_argument':
            if 'roles' in old and changed == {'roles'} and len(op.get('changed_roles', [])) == 1:
                from game.semantic_operations import apply_role_delta
                prop, role_error = apply_role_delta(old, proposed, op, utterance, participants)
                if role_error:
                    return plan, prior, role_error
                result['request_proposition'] = prop
            else:
                if changed not in ({'subject'}, {'object'}):
                    return plan, prior, 'ambiguous_alternative_argument'
                field = next(iter(changed))
                evidence = proposed[field + '_evidence']
                if not proposed[field] or not evidence or evidence.casefold() not in utterance.casefold():
                    return plan, prior, 'ambiguous_alternative_argument'
                result['request_proposition'] = {**old, field: proposed[field], field + '_evidence': evidence}
        else:
            if changed:
                return plan, prior, 'invalid_follow_up_fields'
            # Attribution/evidence/explanation are questions ABOUT the exact
            # target proposition. Provider cannot substitute a different object.
            if relation == 'speech_clarification':
                result['request_proposition'] = deepcopy(old)
            elif 'roles' in old:
                # Keep the complete target as a separate host-owned proposition.
                # The new relation cannot turn a topic into an informant identity.
                result['target_proposition'] = deepcopy(old)
                result['request_proposition']['roles'] = deepcopy(old['roles'])
            else:
                prop = result['request_proposition']
                # The operation targets a proposition, not a newly proposed
                # argument. Ignore redundant provider slots and project the
                # bound proposition's argument under the requested relation.
                slot = 'object' if old['object'] else 'subject'
                prop.update(subject='', subject_evidence='', missing_argument='subject',
                            object=old[slot], object_evidence=old[slot+'_evidence'],
                            temporal=old['temporal'], spatial=old['spatial'],
                            epistemic=old['epistemic'], negated=False)
        result['proposition_referent_id'] = target.get('proposition_referent_id') or target_id
    else:
        return plan, prior, 'invalid_referent_act'
    prop = result['request_proposition']
    prop['prior_reference'] = target['requested_relationship']
    result['referenced_prior_proposition'] = target['requested_relationship']
    # Derive the legacy projection from the accepted proposition, never vice versa.
    argument = prop['object'] or prop['subject'] or next((r['value'] for r in prop.get('roles', []) if r['name'] == 'topic'), '') or target['requested_subject']
    import re
    arg = re.sub(r'[^a-z0-9]+', '_', argument.lower()).strip('_')
    result['requested_subject'] = argument
    result['requested_relationship'] = f"{prop['predicate']}_of({arg})"
    result['bound_referent_id'] = target_id
    result['referent_prior_answer_status'] = target['answer_status']
    if not explicit_addressee:
        result['addressee_id'] = target['addressee_id']
    return result, prior, ''


def commit(session: dict[str, Any], row: dict[str, Any], plan: Mapping[str, Any], adoption):
    """Commit once after delivery verification; invalid/fallback plans keep focus."""
    from game.immutable_valid_response import verify_delivery_record
    from game.unified_semantic_planning import unified_semantic_planning_enabled
    if not unified_semantic_planning_enabled():
        return
    if not adoption or not verify_delivery_record(adoption) or adoption.get('text') != row['delivered_text']:
        return
    if adoption.get('authorization_source') in {'host_terminal_safety', 'dialogue_authority.disclosure_denied'}:
        return
    if adoption.get('provenance') == 'safe_nonresolution':
        return
    if not plan.get('referent_eligible') or not plan.get('addressee_id'):
        return
    memory = deepcopy(state(session)) or {'version': 1, 'conversation_id': uuid4().hex, 'active_id': '', 'sequence': 0, 'records': []}
    delivery_id = row.get('adoption_turn_identity') or f"{row['turn']}:{row['player_text']}"
    if any(r['delivery_id'] == delivery_id for r in memory['records']):
        return
    parent = next((r for r in memory['records'] if r['referent_id'] == plan.get('bound_referent_id')), None)
    if plan.get('referent_operation') and plan['conversational_act'] != 'information_question' and not parent:
        return
    memory['sequence'] += 1
    ident = f"{memory['conversation_id']}:{memory['sequence']}"
    correction = plan['conversational_act'] in {'correction', 'clarification_response'}
    prop = deepcopy(plan.get('request_proposition') or {})
    witness = ' '.join([*(str(prop.get(k) or '') for k in ('predicate_evidence', 'subject_evidence', 'object_evidence', 'temporal', 'spatial')),
                        *(r['evidence'] for r in prop.get('roles', []))])[:1600]
    record = {
        'referent_id': ident, 'conversation_id': memory['conversation_id'],
        'originating_turn_id': row['turn'], 'delivery_id': delivery_id,
        'parent_referent_id': parent['referent_id'] if parent else '',
        'revision': parent['revision'] + 1 if parent and correction else 0,
        'corrected_fields': list((plan.get('referent_operation') or {}).get('changed_fields') or []),
        'addressee_id': plan['addressee_id'], 'mentioned_entity_ids': plan.get('mentioned_entity_ids', []),
        'requested_subject': plan['requested_subject'], 'requested_relationship': plan['requested_relationship'],
        'request_proposition': prop, 'witness_text': witness or plan['question_text'],
        'answer_status': plan['response_kind'], 'epistemic_status': plan['epistemic_status'],
        'semantic_answer_status': plan.get('answer_status', plan['response_kind']),
        'missing_roles': [prop['requested_role']] if prop.get('requested_role') and plan['response_kind'] != 'direct' else [],
        'outstanding_clarification': plan.get('ambiguity_type', '') if plan['response_kind'] == 'clarification' else '',
        'correction_status': 'revision' if correction else 'original', 'focus_status': 'active',
        'follow_up_relationship': (plan.get('referent_operation') or {}).get('follow_up_relationship', ''),
        'proposition_referent_id': plan.get('proposition_referent_id') or ident,
        'source_plan_id': row.get('response_integrity_digest', ''),
        'delivered_speech': row['delivered_text'][:800],
        'operation': deepcopy(plan.get('referent_operation') or {}),
        'target_proposition': deepcopy(plan.get('target_proposition') or {}),
        'provenance': 'host_interpretation', 'canonical': False,
    }
    # A follow-up retains the original unresolved question as focus; its own
    # request stays addressable in the bounded history.
    keep_focus = parent and plan['conversational_act'] in {'follow_up', 'reference_to_prior_speech'}
    for r in memory['records']:
        if not keep_focus and r['focus_status'] == 'active':
            r['focus_status'] = 'superseded'
    if parent and correction:
        parent['correction_status'] = 'corrected'
    if keep_focus:
        record['focus_status'] = 'archived'
    else:
        memory['active_id'] = ident
    memory['records'].append(record)
    # Pin active focus and immediate parent. Older lineage remains traceable by
    # monotonic identities, even after bounded records are compacted.
    pinned = {memory['active_id'], record['parent_referent_id'], ident}
    while len(memory['records']) > MAX_RECORDS:
        index = next(i for i,r in enumerate(memory['records']) if r['referent_id'] not in pinned)
        del memory['records'][index]
    session['conversational_context'][KEY] = memory
    row['referent_id'] = ident
    row['unified_semantic_plan']['referent_id'] = ident
