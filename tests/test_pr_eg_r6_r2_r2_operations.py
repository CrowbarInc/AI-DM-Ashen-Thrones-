"""Operation contracts and attack boundaries; no provider-competence claims."""
import copy
import json
import pytest

from game import conversational_referents as refs, semantic_operations as ops
from game import unified_semantic_planning as planning
from game.semantic_correspondence import coverage, clean_proposition
from tests.test_pr_eg_r6_r2_grounding import prop
from tests.test_pr_eg_r6_r2_r1_referents import seeded, question, operation, resolve, deliver, correction


@pytest.fixture(autouse=True)
def gate(monkeypatch):
    monkeypatch.setenv(planning.FLAG, '1')


def role(name, value, entity=''):
    return dict(name=name, value=value, entity_id=entity, evidence=value)


def named(**kw):
    p = prop(predicate='communicate', evidence='tell', object='', missing='')
    p.update(roles=[role('speaker', 'Mara', 'mara'), role('recipient', 'Oren', 'oren'), role('topic', 'road')],
             requested_role='message_content')
    p.update(kw)
    return p


CAST = [{'id': 'mara', 'name': 'Mara'}, {'id': 'oren', 'name': 'Oren'}]


@pytest.mark.parametrize('bad', [None, '', {}, [1], [role('bad name', 'Mara')],
    [role('speaker', '')], [role('speaker', 'Mara'), role('speaker', 'Oren')],
    [{**role('speaker', 'Mara'), 'authority': True}], [role('x'*49, 'Mara')],
    [role('speaker', 'Mara')]*9])
def test_role_schema_rejects_malformed(bad):
    assert ops.clean_roles(bad) is None


@pytest.mark.parametrize('name', ['speaker', 'recipient', 'topic', 'instrument', 'beneficiary', 'message_content', 'unfamiliar_role'])
def test_open_bounded_role_vocabulary(name):
    assert ops.clean_roles([role(name, 'road')])


@pytest.mark.parametrize('mutation', ['value', 'entity_id', 'evidence'])
def test_role_grounding_rejects_forgery(mutation):
    p = named()
    p['roles'][0][mutation] = 'forged'
    assert not ops.roles_witnessed(p, 'Mara tell Oren about road', CAST)


@pytest.mark.parametrize('missing', ['speaker', 'recipient', 'topic', 'message_content'])
def test_coverage_missing_role_is_partial(missing):
    request = named()
    source = named(requested_role='', roles=[*request['roles'], role('message_content', 'flooded')])
    source['roles'] = [r for r in source['roles'] if r['name'] != missing]
    assert ops.named_coverage(request, source) == 'partial'


@pytest.mark.parametrize('field,value', [('predicate', 'own'), ('negated', True), ('temporal', 'tomorrow'), ('spatial', 'quay')])
def test_coverage_conflicts_are_nonanswers(field, value):
    request = named()
    source = named(requested_role='', roles=[*request['roles'], role('message_content', 'flooded')])
    if field in {'temporal', 'spatial'}:
        request[field] = 'today' if field == 'temporal' else 'road'
    source[field] = value
    assert ops.named_coverage(request, source) == 'related_but_nonanswer'


def test_full_role_coverage():
    request = named()
    assert ops.named_coverage(request, named(requested_role='', roles=[*request['roles'], role('message_content', 'flooded')])) == 'direct'


def test_role_reversal_preserves_topic_and_requested_content():
    old = named()
    proposed = named(roles=[role('speaker', 'Oren', 'oren'), role('recipient', 'Mara', 'mara')])
    op = operation(op='reassign_roles', fields=['roles'])
    op['changed_roles'] = ['speaker', 'recipient']
    result, error = ops.apply_role_delta(old, proposed, op, 'No, what did Oren tell Mara?', CAST)
    assert not error
    assert result['roles'][2] == old['roles'][2]
    assert result['requested_role'] == 'message_content'
    assert old['roles'][0]['value'] == 'Mara'


@pytest.mark.parametrize('names', [[], ['speaker', 'speaker'], ['invented'], ['topic']])
def test_role_delta_requires_exact_supported_changes(names):
    old = named()
    proposed = named(roles=[role('speaker', 'Oren', 'oren'), role('recipient', 'Mara', 'mara')])
    op = operation(op='reassign_roles', fields=['roles']); op['changed_roles'] = names
    assert ops.apply_role_delta(old, proposed, op, 'Oren tell Mara', CAST)[1]


@pytest.mark.parametrize('kind', ['direct', 'partial', 'unknown'])
def test_existing_statuses_roundtrip_and_rejection_keeps_focus(kind):
    session, record = seeded(kind)
    before = copy.deepcopy(session)
    p = correction(record); p['referent_operation']['target_referent_id'] = 'other-conversation:1'
    locked = resolve(session, p, text='I meant the night ledger.')
    assert not locked['referent_eligible']
    assert session == before
    assert refs.active(json.loads(json.dumps(session))) == record


@pytest.mark.parametrize('field', ['roles', 'requested_role'])
def test_partial_named_extension_rejected(field):
    p = prop(); p[field] = [] if field == 'roles' else 'speaker'
    assert clean_proposition(p) is None


@pytest.mark.parametrize('bad', ['bad role', 'x'*49, 'Speaker', ''])
def test_requested_role_syntax(bad):
    p = named(requested_role=bad)
    if bad:
        assert clean_proposition(p) is None
    else:
        assert clean_proposition(p) is not None


@pytest.mark.parametrize('act', ['information_question', 'correction', 'follow_up', 'clarification_response', 'reference_to_prior_speech', 'other'])
def test_operation_taxonomy_schema(act):
    p = question(); p['conversational_act'] = act
    assert planning.validate_plan_schema(p)[0] is not None


def test_malformed_operation_is_uncertainty_not_player_ambiguity():
    session, record = seeded()
    p = correction(record); p['referent_operation']['operation'] = 'invent_fact'
    result = resolve(session, p, text='I meant the night ledger.')
    assert result['response_kind'] == 'unknown'
    assert result['ambiguity_type'] == ''
    assert refs.active(session) == record


@pytest.mark.parametrize('qualifier', ['temporal', 'spatial', 'epistemic'])
def test_unwitnessed_qualifier_rejected(qualifier):
    session, record = seeded()
    p = correction(record, field=qualifier, value='invented', op='replace_qualifier')
    locked = resolve(session, p, text='I meant the night ledger.')
    assert not locked['referent_eligible']


def test_legacy_binary_read_does_not_invent_roles():
    p = clean_proposition(prop())
    assert p and 'roles' not in p


def test_named_proposition_schema_and_serialization():
    p = named()
    assert clean_proposition(json.loads(json.dumps(p))) == p


def test_named_role_reversal_is_not_direct_answer():
    q = named()
    s = named(requested_role='', roles=[role('speaker', 'Oren', 'oren'), role('recipient', 'Mara', 'mara'),
                                      role('topic', 'road'), role('message_content', 'flooded')])
    assert ops.named_coverage(q, s) == 'related_but_nonanswer'


def named_seed():
    session = {}
    q = named()
    source = named(requested_role='', roles=[*q['roles'], role('message_content', 'flooded')], predicate_evidence='told')
    p = question(q, source=source)
    locked = resolve(session, p, text='Mara, what did Mara tell Oren about road?',
                     source='Mara told Oren about road: flooded.')
    assert locked['response_kind'] == 'direct'
    deliver(session, locked)
    return session, refs.active(session)


def test_named_commit_save_roundtrip():
    session, record = named_seed()
    assert refs.active(json.loads(json.dumps(session))) == record
    assert record['request_proposition']['roles'][1]['name'] == 'recipient'


def test_integrated_role_reversal_lineage_and_history():
    session, record = named_seed()
    history = copy.deepcopy(session['conversational_context']['delivered_exchanges'])
    q = named(roles=[role('speaker', 'Oren', 'oren'), role('recipient', 'Mara', 'mara')])
    p = question(q, conversational_act='correction', source=named(requested_role='', predicate_evidence='told',
        roles=[*q['roles'], role('topic', 'road'), role('message_content', 'flooded')]))
    p['referent_operation'] = {**operation(record['referent_id'], 'reassign_roles', ['roles']),
        'changed_roles': ['speaker', 'recipient'], 'evidence': 'Oren tell Mara', 'target_evidence': ''}
    locked = resolve(session, p, text='No, what did Oren tell Mara?', source='Oren told Mara about road: flooded.')
    assert locked['response_kind'] == 'direct'
    assert locked['request_proposition']['roles'][2]['value'] == 'road'
    deliver(session, locked, 2)
    assert refs.active(session)['revision'] == 1
    assert [r['delivered_text'] for r in session['conversational_context']['delivered_exchanges'][:-1]] == [r['delivered_text'] for r in history]


@pytest.mark.parametrize('key', ['canonical_fact', 'state_update', 'disclosure_granted', 'world_fact'])
def test_named_authority_metadata_rejected(key):
    p = question(named()); p[key] = 'forged'
    assert planning.validate_plan_schema(p)[1] == 'unsupported_authority_field'


def test_named_forged_source_entity_is_unknown():
    q = named()
    s = named(requested_role='', roles=[*q['roles'], role('message_content', 'flooded', 'phantom')], predicate_evidence='told')
    assert coverage(q, s, question='Mara tell Oren road', source_text='Mara told Oren road flooded', participants=CAST) == 'unknown'


def test_compact_provider_contract_normalizes_without_inventing_roles():
    p = {k: v for k, v in named().items() if k not in {'subject', 'object', 'subject_evidence', 'object_evidence', 'missing_argument'}}
    cleaned = clean_proposition(p)
    assert cleaned['roles'] == p['roles']
    assert cleaned['subject'] == cleaned['object'] == ''


@pytest.mark.parametrize('sources', [None, [None], ['forged'], {'source_id': 'forged'}])
def test_malformed_compact_source_container_rejected_without_exception(sources):
    p = {k: v for k, v in named().items() if k not in {'subject', 'object', 'subject_evidence', 'object_evidence', 'missing_argument'}}
    raw = dict(conversational_act='information_question', addressee_id='mara',
        referent_operation={**operation(), 'changed_roles': [], 'evidence': '', 'target_evidence': ''},
        request_proposition=p, source_propositions=sources, ambiguity_type='', clarification_needed=False)
    plan, error = planning.validate_plan_schema(raw)
    assert plan is None
    assert error in {'invalid_semantic_bounds', 'invalid_source_proposition'}
