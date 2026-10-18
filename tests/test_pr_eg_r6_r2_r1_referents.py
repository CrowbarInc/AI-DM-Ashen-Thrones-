"""Durable host referents: transactional continuity, bounded deltas and integrity."""
import copy
import json
from pathlib import Path

import pytest

from game import conversational_referents as refs, unified_semantic_planning as planning
from game.conversational_continuity import record_delivered_exchange
from game.immutable_valid_response import seal_host_speech, accepted_record
from tests.test_pr_eg_r6_r2_grounding import prop, proposal, fixture


@pytest.fixture(autouse=True)
def gate(monkeypatch):
    monkeypatch.setenv(planning.FLAG, '1')


def operation(target='', op='', fields=(), follow=''):
    return dict(target_referent_id=target, operation=op, changed_fields=list(fields), follow_up_relationship=follow)


def question(request=None, **kw):
    p = proposal(request or prop(), **kw)
    p['referent_operation'] = operation()
    return p


def resolve(session, plan=None, text='Mara, who keeps the night drum?', source='The miller keeps the night drum.', disclosure='public'):
    scene, world = fixture(source, disclosure)
    before = copy.deepcopy([session, world])
    result = planning.authorize_information_turn(player_text=text, scene=scene, world=world, session=session, proposal=plan or question())['plan']
    assert before == [session, world]
    return result


def deliver(session, plan, turn=1, adoption=True):
    gm = seal_host_speech({}, text=plan['host_line'], source='host', speaker_id=plan['addressee_id'], speaker_name='Mara',
                          resolution=None, player_text=plan['question_text'])
    return record_delivered_exchange(session, player_text=plan['question_text'], delivered_text=gm['player_facing_text'],
        turn=turn, social={'npc_id':plan['addressee_id'], 'npc_name':'Mara', 'unified_semantic_plan':plan},
        adoption=accepted_record(gm) if adoption else None)


def seeded(kind='direct'):
    session = {}
    request = prop()
    source = prop(subject='miller', missing='')
    text = 'The miller keeps the night drum.'
    if kind == 'unknown':
        text = 'The miller keeps the night ledger.'
        source = prop(subject='miller', object='night ledger', missing='')
    elif kind == 'partial':
        text = 'Someone keeps the night drum.'
        source = prop(subject='', subject_evidence='', missing='subject')
    p = question(request); p['source_propositions'][0]['proposition'] = source
    locked = resolve(session, p, source=text)
    deliver(session, locked)
    return session, refs.active(session)


def correction(record, field='object', value='night ledger', op='replace_object', fields=None):
    request = copy.deepcopy(record['request_proposition'])
    request[field] = value
    if field in {'subject', 'object', 'predicate'}:
        request[field+'_evidence'] = value
    p = question(request, conversational_act='correction')
    p['referent_operation'] = operation(record['referent_id'], op, fields or [field])
    return p


def follow(record, kind='source_attribution'):
    request = prop(predicate='informant', evidence='told', object=record['request_proposition']['object'],
                   object_evidence=record['request_proposition']['object_evidence'], prior_reference=record['requested_relationship'])
    p = question(request, conversational_act='follow_up')
    p['referent_operation'] = operation(record['referent_id'], follow=kind)
    return p


def test_stable_identity_and_sealed_history():
    session, record = seeded()
    assert record['referent_id'] and record['conversation_id']
    assert record['answer_status'] == 'direct'
    assert session['conversational_context']['delivered_exchanges'][-1]['referent_id'] == record['referent_id']
    assert refs.active(json.loads(json.dumps(session))) == record


def test_identity_unique_across_conversations():
    assert seeded()[1]['referent_id'] != seeded()[1]['referent_id']


@pytest.mark.parametrize('kind', ['unknown', 'partial', 'direct'])
def test_answer_status_preserves_focus(kind):
    session, record = seeded(kind)
    assert record['answer_status'] == kind
    assert planning.prior_semantic_plan(session)['referent_id'] == record['referent_id']
    assert record['request_proposition']['missing_argument'] == 'subject'


def test_object_correction_is_bounded_and_lineage_is_immutable():
    session, old = seeded('unknown')
    history = copy.deepcopy(session['conversational_context']['delivered_exchanges'])
    p = correction(old)
    p['source_propositions'][0]['proposition'] = prop(subject='miller', object='night ledger', missing='')
    locked = resolve(session, p, text='I meant the night ledger.', source='The miller keeps the night ledger.')
    assert locked['response_kind'] == 'direct'
    deliver(session, locked, 2)
    new = refs.active(session)
    assert new['parent_referent_id'] == old['referent_id']
    assert new['revision'] == 1 and new['corrected_fields'] == ['object']
    assert new['request_proposition']['predicate'] == old['request_proposition']['predicate']
    assert {k:v for k,v in session['conversational_context']['delivered_exchanges'][0].items() if k!='active'} == {k:v for k,v in history[0].items() if k!='active'}
    assert refs.state(session)['records'][0]['request_proposition'] == old['request_proposition']


@pytest.mark.parametrize('field,value,op,text', [
    ('predicate', 'owns', 'replace_relationship', 'No, who owns it?'),
    ('temporal', 'tomorrow', 'replace_qualifier', 'I meant tomorrow.'),
    ('spatial', 'north', 'replace_qualifier', 'I meant in the north.'),
])
def test_corrections_preserve_unmodified_slots(field, value, op, text):
    session, old = seeded()
    p = correction(old, field, value, op)
    locked = resolve(session, p, text=text)
    assert locked['referent_eligible']
    assert locked['request_proposition'][field] == value
    for slot in refs.FIELDS:
        if slot != field:
            assert locked['request_proposition'][slot] == old['request_proposition'][slot]


def test_subject_replacement_and_role_reversal():
    session = {}
    request = prop(predicate='tell', evidence='tell', subject='Oren', subject_evidence='Oren', object='Mara', object_evidence='Mara', missing='predicate')
    original = resolve(session, question(request), text='Mara, what did Oren tell Mara?')
    deliver(session, original)
    old = refs.active(session)
    p = correction(old, 'subject', 'Mara', 'replace_roles', ['subject', 'object'])
    p['request_proposition'].update(object='Oren', object_evidence='Oren')
    locked = resolve(session, p, text='I meant what Mara told Oren.')
    assert locked['request_proposition']['subject'] == 'Mara'
    assert locked['request_proposition']['object'] == 'Oren'
    assert locked['referent_eligible']


@pytest.mark.parametrize('kind,text', [('source_attribution','Who told you?'), ('explanation','Why told?'), ('evidence','How do you know who told?'), ('speech_clarification','What did you mean by told?')])
def test_follow_up_after_uncertainty_retains_original_focus(kind, text):
    session, old = seeded('unknown')
    p = follow(old, kind)
    locked = resolve(session, p, text=text)
    assert locked['bound_referent_id'] == old['referent_id']
    assert locked['response_kind'] == 'unknown' and not locked['selected_source_ids']
    deliver(session, locked, 2)
    assert refs.active(session)['referent_id'] == old['referent_id']
    assert refs.state(session)['records'][-1]['proposition_referent_id'] == old['referent_id']


def test_follow_up_after_partial_preserves_partial_status():
    session, old = seeded('partial')
    locked = resolve(session, follow(old), text='Who told you?')
    deliver(session, locked, 2)
    assert refs.active(session)['answer_status'] == 'partial'
    assert not locked['selected_source_ids']


def test_temporal_follow_up_inherits_proposition():
    session, old = seeded()
    p = follow(old, 'temporal_modification');p['request_proposition'] = {**old['request_proposition'], 'temporal':'tomorrow'}
    p['referent_operation']['changed_fields'] = ['temporal']
    locked = resolve(session, p, text='What about tomorrow?')
    assert locked['request_proposition']['temporal'] == 'tomorrow'
    assert locked['request_proposition']['predicate'] == old['request_proposition']['predicate']
    assert locked['response_kind'] == 'unknown'


@pytest.mark.parametrize('value,evidence', [('', ''), ('night ledger', 'invented')])
def test_ambiguous_or_ungrounded_alternative_clarifies(value, evidence):
    session, old = seeded()
    p = follow(old, 'alternative_argument');p['referent_operation']['changed_fields'] = ['object']
    p['request_proposition'].update(object=value, object_evidence=evidence)
    locked = resolve(session, p, text='And the other one?')
    assert locked['response_kind'] == 'clarification' and not locked['referent_eligible']


def test_multiple_questions_and_explicit_older_target():
    session, first = seeded()
    deliver(session, resolve(session, question(prop(object='night ledger', object_evidence='night ledger')),
        text='Mara, who keeps the night ledger?'), 2)
    second = refs.active(session)
    assert second['referent_id'] != first['referent_id']
    assert resolve(session, follow(second), text='Who told you?')['bound_referent_id'] == second['referent_id']
    assert resolve(session, follow(first), text='Who told you about the night drum?')['bound_referent_id'] == first['referent_id']


@pytest.mark.parametrize('attack', ['forged', 'cross_conversation', 'stale', 'speaker', 'field', 'operation', 'unwitnessed', 'substitution'])
def test_untrusted_operations_fail_closed_without_losing_focus(attack):
    session, old = seeded('unknown');p = correction(old)
    if attack == 'forged':p['referent_operation']['target_referent_id'] = 'invented'
    if attack == 'cross_conversation':p['referent_operation']['target_referent_id'] = seeded()[1]['referent_id']
    if attack == 'stale':
        session['conversational_context'][refs.KEY]['records'][0]['correction_status'] = 'corrected'
    if attack == 'speaker':
        p['addressee_id'] = 'oren'
    if attack == 'field':p['referent_operation']['changed_fields'] = ['predicate']
    if attack == 'operation':p['referent_operation']['operation'] = 'grant_truth'
    if attack == 'unwitnessed':p['request_proposition']['object_evidence'] = 'unseen ledger'
    if attack == 'substitution':p['request_proposition']['predicate'] = 'invent'
    before = copy.deepcopy(refs.state(session))
    text = 'Oren, I meant the night ledger.' if attack == 'speaker' else 'I meant the night ledger.'
    locked = resolve(session, p, text=text)
    assert locked['response_kind'] == 'clarification'
    deliver(session, locked, 2)
    assert refs.state(session) == before


def test_prior_entity_cannot_be_replaced_by_unrelated_follow_up():
    session, old = seeded();p = follow(old)
    p['request_proposition'].update(object='secret vault', object_evidence='secret vault')
    locked = resolve(session, p, text='Who told you about the secret vault?')
    assert locked['request_proposition']['object'] == old['request_proposition']['object']
    assert not locked['selected_source_ids']


def test_addressee_replacement_requires_explicit_grounding():
    session, old = seeded();p = correction(old, op='replace_addressee', fields=['addressee_id'])
    p['request_proposition'] = copy.deepcopy(old['request_proposition']);p['addressee_id'] = 'oren'
    locked = resolve(session, p, text='Oren, I meant to ask you.')
    assert locked['addressee_id'] == 'oren' and locked['referent_eligible']


def test_mentioned_npc_never_becomes_addressee():
    session = {};p = question(prop(predicate='say', evidence='say', subject='Oren',subject_evidence='Oren',object='road',object_evidence='road',missing='predicate'))
    locked = resolve(session,p,text='Mara, what did Oren say about the road?')
    assert locked['addressee_id'] == 'mara' and locked['mentioned_entity_ids'] == ['oren']


def test_save_load_preserves_identity_and_next_revision(tmp_path, monkeypatch):
    from game import storage
    from tests.test_pr_ef_gm_authority import seed_scene
    seed_scene(tmp_path, monkeypatch)
    session, old = seeded('unknown');storage.save_session(session)
    loaded = storage.load_session()
    assert refs.active(loaded) == old
    locked = resolve(loaded, correction(old), text='I meant the night ledger.')
    deliver(loaded, locked, 2);storage.save_session(loaded)
    assert refs.active(storage.load_session())['revision'] == 1
    assert len(refs.state(storage.load_session())['records']) == 2


def test_legacy_save_compatibility_is_noncanonical():
    assert refs.active({}) == {}
    assert resolve({},question())['response_kind'] == 'direct'


def test_retry_idempotence():
    session = {};locked = resolve(session)
    deliver(session, locked);before = copy.deepcopy(session)
    deliver(session, locked)
    assert session == before


def test_no_commit_before_verified_delivery_or_on_rejection():
    session = {};locked = resolve(session)
    assert not refs.state(session)
    deliver(session, locked, adoption=False)
    assert not refs.state(session)
    gm = seal_host_speech({},text=locked['host_line'],source='host',speaker_id='mara',speaker_name='Mara',resolution=None,player_text=locked['question_text'])
    bad = copy.deepcopy(accepted_record(gm));bad['text'] = 'bad'
    with pytest.raises(ValueError):
        record_delivered_exchange(session,player_text=locked['question_text'],delivered_text=locked['host_line'],adoption=bad)
    assert not refs.state(session)


def test_retention_pins_active_question_and_compacts_history():
    session, old = seeded('unknown')
    for turn in range(2, 40):
        locked = resolve(session,follow(old),text='Who told you?')
        deliver(session,locked,turn)
    assert len(refs.state(session)['records']) == refs.MAX_RECORDS
    assert refs.active(session)['referent_id'] == old['referent_id']
    assert old['referent_id'] in {r['referent_id'] for r in refs.context(session)['recent']}
    assert refs.state(session)['sequence'] == 39


@pytest.mark.parametrize('disclosure', ['secret', 'restricted', 'private'])
def test_referents_never_grant_disclosure_or_create_facts(disclosure):
    session, old = seeded()
    p = correction(old)
    p['source_propositions'][0]['proposition'] = prop(subject='miller', object='night ledger', missing='')
    locked = resolve(session,p,text='I meant the night ledger.',source='The miller keeps the night ledger.',disclosure=disclosure)
    assert not locked['authorized_text'] and not locked['selected_source_ids']
    assert locked['response_kind'] in {'unknown','refusal'}
    assert old['canonical'] is False


def test_gate_off_creates_no_referents(monkeypatch):
    session={};locked=resolve(session)
    monkeypatch.setenv(planning.FLAG,'0');deliver(session,locked)
    assert not refs.state(session)


def test_all_frozen_holdouts_unchanged():
    import hashlib
    root=Path(__file__).resolve().parents[1]
    hashes=json.loads((root/'artifacts/pr_eg_r6_r2_r1/freeze.json').read_text())
    assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==digest for p,digest in hashes.items())


def test_structured_schema_requires_all_declared_properties():
    def check(schema):
        if schema.get('type')=='object':
            assert set(schema['required'])==set(schema['properties'])
            for value in schema['properties'].values():check(value)
        if schema.get('type')=='array':check(schema['items'])
    check(planning._proposal_schema())


def test_unqualified_historical_id_cannot_override_focus():
    session, first = seeded()
    deliver(session,resolve(session,question(prop(object='night ledger',object_evidence='night ledger')),
        text='Mara, who keeps the night ledger?'),2)
    locked=resolve(session,follow(first),text='Who told you?')
    assert locked['bound_referent_id']==refs.active(session)['referent_id']


def test_valid_alternative_is_grounded_and_preserves_predicate():
    session, old=seeded();p=follow(old,'alternative_argument')
    p['referent_operation']['changed_fields']=['object']
    p['request_proposition'].update(object='night ledger',object_evidence='night ledger')
    locked=resolve(session,p,text='And the night ledger?')
    assert locked['request_proposition']['object']=='night ledger'
    assert locked['request_proposition']['predicate']==old['request_proposition']['predicate']


def test_rejected_delivery_never_commits_referent():
    session={};locked=resolve(session)
    gm=seal_host_speech({},text=locked['host_line'],source='host_terminal_safety',speaker_id='mara',speaker_name='Mara',resolution=None,player_text=locked['question_text'])
    record_delivered_exchange(session,player_text=locked['question_text'],delivered_text=gm['player_facing_text'],
        social={'unified_semantic_plan':locked},adoption=accepted_record(gm))
    assert not refs.state(session)


@pytest.mark.parametrize('kind',['unknown','partial','direct'])
def test_http_delivery_save_load_and_correction_use_same_referent(tmp_path,monkeypatch,kind):
    from fastapi.testclient import TestClient
    from game import storage,api
    from tests.test_pr_ef_gm_authority import seed_scene
    seed_scene(tmp_path,monkeypatch)
    scene=storage.load_active_scene();sid=scene['scene']['id']
    scene['scene']['addressables']=[{'id':'mara','name':'Mara','kind':'npc'}]
    scene['scene']['discoverable_clues']=[];storage.save_scene(scene)
    source='The miller keeps the night drum.' if kind=='direct' else 'Someone keeps the night drum.' if kind=='partial' else 'The miller keeps the night ledger.'
    world=storage.load_world();world['npcs']=[{'id':'mara','name':'Mara','location':sid,'topics':[{'id':'fact','text':source}]}];storage.save_world(world)
    def propose(ctx):
        if not refs.active(storage.load_session()):
            p=question()
            p['source_propositions'][0]['proposition']=prop(subject='miller',missing='') if kind=='direct' else prop(subject='',subject_evidence='',missing='subject') if kind=='partial' else prop(subject='miller',object='night ledger',missing='')
            return p
        r=refs.active(storage.load_session());p=correction(r)
        p['source_propositions'][0]['proposition']=prop(subject='miller',object='night ledger',missing='')
        return p
    with planning.plan_proposer(propose):
        client=TestClient(api.app)
        first=client.post('/api/chat?ui_mode=player',json={'text':'Mara, who keeps the night drum?','ui_mode':'player'})
        assert first.status_code==200
        old=refs.active(storage.load_session());assert old['answer_status']==kind
        storage.save_session(storage.load_session())
        second=client.post('/api/chat?ui_mode=player',json={'text':'I meant the night ledger.','ui_mode':'player'})
        assert second.status_code==200
    session=storage.load_session();new=refs.active(session)
    assert new['parent_referent_id']==old['referent_id'] and new['revision']==1
    gm=second.json()['gm_output'];adopted=gm['metadata']['accepted_response']
    assert adopted['text']==gm['player_facing_text']==session['conversational_context']['delivered_exchanges'][-1]['delivered_text']
    assert new['request_proposition']['object']=='night ledger'
