"""R2C: information, final-response and persistence integrity at production seams."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from game import api, storage
from game.conversational_continuity import record_delivered_exchange, continuity_directive
from game.dialogue_authority import authorize_npc_disclosure, build_dialogue_authority, remember_dialogue_commitment
from game.immutable_valid_response import run_preserve_if_valid, restore_accepted_text
from game.models import ChatRequest
from tests.test_pr_ef_gm_authority import seed_scene, raw_record

ROOT = Path(__file__).resolve().parents[1]
H = ROOT / 'artifacts/pr_eg_r2c'
HOLDOUTS = json.loads((H/'frozen_holdouts.json').read_text())
ADVERSARIAL = [
    'I prefer the evening because the guards usually leave the north gate unattended.',
    'I like the quiet. The patrol changes every hour at the east post.',
    'The guard captain cannot see anyone wearing a grey cloak.',
    'The secret stairway starts beneath the old well.',
    'I will pay you ten silver to carry this message.',
    'If you bring the letter, I promise you a reward of ten silver.',
    'The council secretly serves the Ash Cowl.',
    'I owe you safe passage through the gate.',
    'The hidden password is Winter.',
    'Rumor has it the treasury door is never locked.',
    'I prefer evening because the sentries all sleep after dusk.',
]


def resolution(question, fact='', session=None, npc_id='sergeant_mara', name='Sergeant Mara'):
    social = dict(target_resolved=True, npc_id=npc_id, npc_name=name,
                  reply_plan_kind='authoritative_answer_available' if fact else 'genuine_uncertainty')
    person = None
    if fact:
        person = dict(id=npc_id, name=name, topics=[dict(id='fact', text=fact, disclosure='public')])
        topic = dict(id='fact', text=fact)
        topic['disclosure_authorization'] = authorize_npc_disclosure(person, topic)
        social['topic_revealed'] = topic
    social['dialogue_authority'] = build_dialogue_authority(question, npc=person, social=social, session=session)
    return dict(kind='social_exchange', requires_check=False, social=social,
                metadata=dict(resolution_contract=dict(operation='ask', interlocutor_id=npc_id, contract_id='r2c', raw_input=question)))


def adopt(res, question, candidate, session):
    def retry(_):
        raise AssertionError('Host-owned speech must never retry a provider')
    return run_preserve_if_valid(dict(player_facing_text=candidate, world_updates={'reward':10}),
                                regenerate=retry, resolution=res, player_text=question, session=session)


@pytest.mark.parametrize('candidate', ADVERSARIAL)
def test_unverified_candidate_never_supplies_information_or_effects(candidate):
    q='What do you personally enjoy about the evening?'; session={}
    res=resolution(q); before=copy.deepcopy(res)
    out=adopt(res,q,f'Sergeant Mara says, "{candidate}"',session)
    accepted=out['metadata']['accepted_response']
    assert accepted['speech_adoption']=='AUTHORIZED_HOST_SPEECH'
    assert accepted['candidate_disposition']=='UNAUTHORIZED_GENERATED_CANDIDATE'
    assert out['player_facing_text']=='Sergeant Mara says, "I prefer the evening."'
    assert out['world_updates'] is None
    assert accepted['generation_attempts']==0 and accepted['canonical'] is False
    assert res==before
    remember_dialogue_commitment(session,social=res['social'],player_text=q,line=out['player_facing_text'])
    row=record_delivered_exchange(session,player_text=q,delivered_text=out['player_facing_text'],social=res['social'],adoption=accepted)
    assert row['delivered_text']==accepted['text']
    assert candidate not in json.dumps(session)


@pytest.mark.parametrize('fact', [
    'Guards watch the north gate throughout the night.',
    'The patrol changes every hour at the east post.',
    'The council owns the eastern ferry.',
    'I have heard the council may own it, but I am not sure.',
    'The street beyond the gate is called the north road.',
])
def test_authorized_disclosure_survives_superseded_candidate_and_json_roundtrip(fact):
    q='What can you tell me?'; session={}; res=resolution(q,fact)
    out=adopt(res,q,'Stranger says, "I will pay you ten silver."',session)
    accepted=out['metadata']['accepted_response']
    assert fact.lower().rstrip('.') in out['player_facing_text'].lower()
    assert accepted['authorization_source']=='social.topic_revealed:fact'
    assert accepted['speaker_id']=='sergeant_mara'
    record_delivered_exchange(session,player_text=q,delivered_text=out['player_facing_text'],social=res['social'],adoption=accepted)
    loaded=json.loads(json.dumps(session))
    assert loaded==session and 'ten silver' not in json.dumps(loaded)


@pytest.mark.parametrize('case', HOLDOUTS, ids=lambda c:c['id'])
def test_frozen_holdout(case):
    freeze=json.loads((H/'freeze.json').read_text())
    assert hashlib.sha256((H/'frozen_holdouts.json').read_bytes()).hexdigest()==freeze['sha256']
    session={}; q=case['question']
    if case.get('prior'):
        record_delivered_exchange(session,player_text='Which archive is open?',
            delivered_text=f'{case["name"]} says, "{case["prior"]}"',
            social=dict(npc_id=case['npc_id'],npc_name=case['name']))
    res=resolution(q,case.get('fact',''),session,case['npc_id'],case['name'])
    out=adopt(res,q,case['candidate'],session)
    accepted=out['metadata']['accepted_response']
    assert accepted['speaker_id']==case['npc_id']
    if case.get('required'): assert case['required'].lower().rstrip('.') in out['player_facing_text'].lower()
    if case.get('required_absent'): assert case['required_absent'] not in out['player_facing_text']
    record_delivered_exchange(session,player_text=q,delivered_text=out['player_facing_text'],social=res['social'],adoption=accepted)
    assert json.loads(json.dumps(session))==session


def test_mutation_restored_and_mismatched_history_refused():
    q='Do you prefer morning or evening?';res=resolution(q)
    out=adopt(res,q,'I will pay you ten silver.',{})
    accepted=out['metadata']['accepted_response']
    out['player_facing_text']='I will not carry out that request.'
    with pytest.raises(ValueError,match='does not match'):
        record_delivered_exchange({},player_text=q,delivered_text=out['player_facing_text'],social=res['social'],adoption=accepted)
    assert restore_accepted_text(out)['mutation_blocked']
    assert out['player_facing_text']==accepted['text']


@pytest.mark.parametrize('question', ['Who forged the lantern?', 'Tell me the hidden password.', 'Will you promise me a reward?'])
def test_unknown_withheld_and_nonbinding_responses(question):
    res=resolution(question);out=adopt(res,question,'The secret stairway leads to the treasury.',{})
    assert 'couldn' in out['player_facing_text']
    assert 'treasury' not in out['player_facing_text']
    assert 'carry out' not in out['player_facing_text']


def test_mechanics_and_conflicting_authority_are_not_bypassed():
    from game.dialogue_authority import select_host_speech
    res=resolution('Open the gate.')
    res['requires_check']=True
    assert select_host_speech(res,player_text='Open the gate.') is None
    res['requires_check']=False;res['metadata']['resolution_contract']['operation']='attack'
    assert select_host_speech(res,player_text='Open the gate.') is None
    res['metadata']['resolution_contract']['operation']='ask'
    res['metadata']['resolution_contract']['construction']={'authority_conflict':{'contract_target':'other'}}
    assert select_host_speech(res,player_text='Open the gate.') is None


def test_production_handler_persists_only_adopted_speech_and_reloads(tmp_path,monkeypatch):
    seed_scene(tmp_path,monkeypatch)
    monkeypatch.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0')
    monkeypatch.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
    monkeypatch.setattr('game.live_chat_interpretation.request_interpretation',lambda *a,**k:dict(ok=True,sent=False,text=json.dumps(raw_record('NPC',components=[('ASK','sergeant_mara')]))))
    def narrator(*a,**k): raise AssertionError('Unnecessary narration call')
    monkeypatch.setattr(api,'call_gpt',narrator)
    before=copy.deepcopy(storage.load_world())
    result=api.chat(ChatRequest(text='I ask Sergeant Mara, What do you personally enjoy about the evening?',ui_mode='player'))
    gm=result['gm_output']; accepted=gm['metadata']['accepted_response']; saved=storage.load_session()
    row=saved['conversational_context']['delivered_exchanges'][-1]
    assert row['delivered_text']==gm['player_facing_text']==accepted['text']
    assert row['speaker_id']==accepted['speaker_id']=='sergeant_mara'
    assert row['authorization_source']==accepted['authorization_source']
    storage.save_session(copy.deepcopy(saved))
    assert storage.load_session()['conversational_context']==saved['conversational_context']
    after=storage.load_world()
    # The existing passive faction clock/event log remains resolver-owned.
    assert {k:v for k,v in after.items() if k not in {'factions','event_log'}}=={k:v for k,v in before.items() if k not in {'factions','event_log'}}
    follow=api.chat(ChatRequest(text='Why do you prefer the evening?',ui_mode='player'))
    assert 'prefer the evening' in follow['gm_output']['player_facing_text']
    assert 'carry out' not in follow['gm_output']['player_facing_text']


def test_gm_and_absent_npc_recall_remain_owned_by_gm():
    session={}; social=dict(npc_id='sergeant_mara',npc_name='Sergeant Mara')
    record_delivered_exchange(session,player_text='What road?',delivered_text='Sergeant Mara says, "The north road."',social=social)
    session['interaction_context']={'active_interaction_target_id':'sergeant_mara','active_interaction_kind':'social'}
    world={'npcs':[dict(id='sergeant_mara',name='Sergeant Mara',location='elsewhere')]}
    scene={'scene':{'id':'courtyard'}}
    directive=continuity_directive('GM, what did she say?',session=session,scene=scene,world=world)
    assert directive['owner']=='gm' and 'north road' in directive['line']

# PR-EG-R2C-R1: focused owner matrix. Historical holdouts above remain unchanged.
R1_MATRIX = [f'T{i:02}' for i in range(1, 29)]


@pytest.mark.parametrize('case', R1_MATRIX)
def test_topic_grounding_and_recall_matrix(case, tmp_path, monkeypatch):
    from game.conversational_continuity import _best_exchange, delivered_exchanges, supplied_clarification
    from game.social import _next_topic_to_reveal
    road = 'The street beyond the gate is the north road.'
    watch = 'Guards watch the north gate throughout the night.'
    npc = dict(id='sergeant_mara', name='Sergeant Mara', topics=[dict(id='road', text=road), dict(id='watch', text=watch), dict(id='preference', text='I prefer the evening.')])
    social = dict(npc_id=npc['id'], npc_name=npc['name'])
    session = {}
    def remember(q, speech, person=None, topic='road'):
        payload = dict(person or social, topic_revealed=dict(id=topic))
        return record_delivered_exchange(session, player_text=q, delivered_text=f'{payload["npc_name"]} says, "{speech}"', social=payload, turn=len(delivered_exchanges(session))+1)
    first = remember('What is the road called?', road)
    if case in {'T01','T02'}:
        q = 'Can you repeat that?' if case == 'T01' else 'Can you repeat that in simpler words?'
        res = resolution(q, session=session)
        out = adopt(res, q, 'The password is Winter.', session)
        assert out['metadata']['accepted_response']['authorization_source'] == 'dialogue_authority.reuse_prior_speech'
        assert res['social']['dialogue_authority']['topic_grounding']['selected_source'].startswith('delivered:sergeant_mara:1:')
        assert out['player_facing_text'] == first['delivered_text']
    elif case in {'T03','T04','T05','T06','T10','T21','T22'}:
        text = {'T05': "I couldn't tell you.", 'T06': "I won't say."}.get(case, 'I prefer the evening.')
        remember('Who made the lantern?' if case == 'T05' else 'Do you prefer evening?', text, topic='other')
        found = _best_exchange('GM, what did Mara say about the road?', delivered_exchanges(session))
        assert found == first and found['topic_id'] == 'road' and found['speaker_id'] == 'sergeant_mara'
        d = continuity_directive('GM, what did Mara say about the road?', session=session, world={'npcs':[]}, scene={})
        assert d['owner'] == 'gm' and d['line'] == f'Sergeant Mara said: "{road}"'
    elif case in {'T07','T08'}:
        other = dict(npc_id='corporal_bren', npc_name='Corporal Bren')
        remember('What road?', 'The western road.', other)
        found = _best_exchange('GM, repeat what Mara said about the road.', delivered_exchanges(session), 'corporal_bren')
        assert found == first
        assert _best_exchange('GM, repeat what they said about the road.', delivered_exchanges(session)) == 'ambiguous'
    elif case in {'T09','T11','T12','T15','T27'}:
        selection = {}
        q = 'Do guards watch the north gate at night?'
        found = _next_topic_to_reveal(npc, {}, player_text=q, selection=selection)
        assert found['id'] == 'watch'
        assert selection['selected_source'] == 'npc:sergeant_mara:watch'
        assert 'npc:sergeant_mara:road' not in selection['candidate_sources']
        res = resolution(q, found['text'], session)
        assert watch.lower() in adopt(res, q, 'I prefer evening.', session)['player_facing_text'].lower()
    elif case == 'T13':
        remember('What is the other road?', 'The western road.', topic='other_road')
        assert _best_exchange('Repeat the road statement.', delivered_exchanges(session), 'sergeant_mara') == 'ambiguous'
        assert 'Which earlier remark' in supplied_clarification('Repeat the road statement.', session, 'sergeant_mara', 'Sergeant Mara')
        selection = {}
        npc['topics'].append(dict(id='other_road', text='The street beyond the gate is the west road.'))
        assert _next_topic_to_reveal(npc, {}, player_text='What road?', selection=selection) is None
        assert selection['ambiguous'] and len(selection['candidate_sources']) == 2
    elif case == 'T14':
        assert _best_exchange('GM, what did Mara say about the treasury?', delivered_exchanges(session)) is None
        assert _best_exchange('Repeat that.', [], 'sergeant_mara') is None
        assert 'Which statement' in supplied_clarification('Repeat that.', {}, 'sergeant_mara', 'Sergeant Mara')
    elif case in {'T16','T17','T18','T19','T25','T26'}:
        q = 'What do you personally enjoy about the evening?'
        candidate = 'I prefer the evening because the guards leave the gate unattended.'
        before = copy.deepcopy(session)
        res = resolution(q, session=session)
        out = adopt(res, q, candidate, session)
        accepted = out['metadata']['accepted_response']
        assert accepted['candidate_disposition'] == 'UNAUTHORIZED_GENERATED_CANDIDATE'
        assert out['world_updates'] is None and session == before
        remember_dialogue_commitment(session, social=res['social'], player_text=q, line=out['player_facing_text'])
        row = record_delivered_exchange(session, player_text=q, delivered_text=out['player_facing_text'], social=res['social'], adoption=accepted)
        assert row['delivered_text'] == accepted['text'] and candidate not in json.dumps(session)
        assert 'carry out' not in row['delivered_text'] and 'unattended' not in row['delivered_text']
    elif case == 'T20':
        d = continuity_directive('GM, repeat exactly what Mara said about the road.', session=session, world={}, scene={})
        assert d['owner'] == 'gm' and d['line'] == f'Sergeant Mara said: "{road}"'
    elif case in {'T23','T24'}:
        seed_scene(tmp_path, monkeypatch)
        remember('Do guards watch the gate?', watch, topic='watch')
        remember('Do you prefer morning?', 'I prefer the evening.', topic='preference')
        for i in range(12):
            remember('Who made object '+str(i)+'?', "I couldn't tell you.", topic='unknown')
        storage.save_session(copy.deepcopy(session))
        loaded = storage.load_session()
        assert delivered_exchanges(loaded) == delivered_exchanges(session)
        found = _best_exchange('GM, what did Mara say about the road?', delivered_exchanges(loaded))
        assert found == first and found['speaker_id'] == npc['id'] and found['topic_id'] == 'road'
        selection = {}
        found = _next_topic_to_reveal(npc, dict(revealed_topics=['road','watch']), player_text='What is the road called?', allow_revealed=True, selection=selection)
        assert found['id'] == 'road' and selection['selected_source'] == 'npc:sergeant_mara:road'
    elif case == 'T28':
        before = copy.deepcopy(npc)
        remember('What is in the treasury?', 'I believe there is a dragon.', topic='belief')
        found = _best_exchange('GM, what did Mara say about the treasury?', delivered_exchanges(session))
        assert found['supplied_text'] == 'I believe there is a dragon.'
        assert npc == before
        assert _next_topic_to_reveal(npc, {}, player_text='What is in the treasury?') is None
    else:
        raise AssertionError('Uncovered matrix row: '+case)


def test_grounding_multiple_owned_topics_and_speakers():
    from game.social import _next_topic_to_reveal
    from game.conversational_continuity import _best_exchange, delivered_exchanges
    road = dict(id='street_name', text='The street beyond the gate is the north road.')
    watch = dict(id='night_watch', text='Guards watch the north gate throughout the night.')
    session = {}
    for npc_id, name, preference in [('mara','Mara','evening'), ('bren','Bren','morning')]:
        npc = dict(id=npc_id, name=name, topics=[road, watch, dict(id='preference',text=f'I prefer the {preference}.')])
        for question, expected in [('What is the road called?','street_name'), ('Do guards watch the gate at night?','night_watch'), ('Do you prefer morning or evening?','preference')]:
            selection = {}
            found = _next_topic_to_reveal(npc, {}, player_text=question, selection=selection)
            assert found['id'] == expected
            assert selection['selected_source'] == f'npc:{npc_id}:{expected}'
            record_delivered_exchange(session, player_text=question, delivered_text=f'{name} says, "{found["text"]}"', social=dict(npc_id=npc_id,npc_name=name,topic_revealed=found))
    record_delivered_exchange(session, player_text='Will you open the treasury?', delivered_text='Orr says, "I will not."', social=dict(npc_id='orr',npc_name='Orr'))
    found = _best_exchange('GM, recall what Bren said about the road.', delivered_exchanges(session))
    assert found['speaker_id'] == 'bren' and found['topic_id'] == 'street_name'
    found = _best_exchange('GM, what did Orr say about the treasury?', delivered_exchanges(session))
    assert found['speaker_id'] == 'orr' and found['supplied_text'] == 'I will not.'
    assert _best_exchange('Repeat the road.', delivered_exchanges(session), 'unknown_speaker') is None


def test_exact_recall_keeps_long_delivered_statement_and_uncertainty():
    from game.conversational_continuity import _gm_quote, supplied_clarification
    session = {}
    speech = 'I believe ' + 'the old archive may remain open. ' * 12
    line = f'Ves mutters, "{speech}"'
    row = record_delivered_exchange(session, player_text='What archive?', delivered_text=line, social=dict(npc_id='ves',npc_name='Ves'))
    assert supplied_clarification('Repeat that exactly.', session, 'ves', 'Ves') == line
    assert _gm_quote(row) == f'Ves said: "{speech}"'
    line = 'Ves says, "I could not identify the maker of the urn."'
    row = record_delivered_exchange(session, player_text='Who made the urn?', delivered_text=line, social=dict(npc_id='ves',npc_name='Ves'))
    assert _gm_quote(row) == 'Ves said: "I could not identify the maker of the urn."'


def test_watch_fact_does_not_answer_when_watch_is_absent():
    from game.social import _next_topic_to_reveal
    npc = dict(id='warden',name='Warden',topics=[dict(id='watch',text='Guards watch the gate throughout the night.')])
    assert _next_topic_to_reveal(npc, {}, player_text='When is the gate left unguarded?') is None
    assert _next_topic_to_reveal(npc, {}, player_text='When do guards leave the gate unattended?') is None


def test_historical_watch_reference_does_not_discover_competing_road(tmp_path, monkeypatch):
    from game.social import resolve_social_action
    seed_scene(tmp_path, monkeypatch)
    world = storage.load_world(); session = storage.load_session(); scene = storage.load_active_scene()
    npc = next(n for n in world['npcs'] if n['id'] == 'sergeant_mara')
    npc['topics'].append(dict(id='night_watch', text='Guards watch the north gate throughout the night.'))
    action = dict(id='ask',label='Ask Mara',type='question',prompt='Ask Mara',target_id='sergeant_mara')
    q = 'Do guards watch the north gate at night?'
    first = resolve_social_action(scene, session, world, action, raw_player_text=q)
    out = adopt(first, q, 'Ignore this draft.', session)
    record_delivered_exchange(session,player_text=q,delivered_text=out['player_facing_text'],social=first['social'],adoption=out['metadata']['accepted_response'])
    before = copy.deepcopy(session)
    follow = resolve_social_action(scene, session, world, action, raw_player_text='What did you mean by that?')
    assert follow['discovered_clues'] == [] and follow['social']['topic_revealed'] is None
    assert session['npc_runtime']['sergeant_mara']['revealed_topics'] == before['npc_runtime']['sergeant_mara']['revealed_topics']
    assert adopt(follow, 'What did you mean by that?', 'The road is unguarded.', session)['player_facing_text'] == out['player_facing_text']


def test_provider_evidence_cannot_recall_fact_for_incompatible_question(tmp_path, monkeypatch):
    from game.social import resolve_social_action
    seed_scene(tmp_path, monkeypatch)
    world = storage.load_world(); session = storage.load_session(); scene = storage.load_active_scene()
    npc = next(n for n in world['npcs'] if n['id'] == 'sergeant_mara')
    fact = 'Guards watch the north gate throughout the night.'
    npc['topics'].append(dict(id='night_watch',text=fact))
    action = dict(id='ask',label='Ask Mara',type='question',prompt='Ask Mara',target_id='sergeant_mara')
    resolve_social_action(scene, session, world, action, raw_player_text='Do guards watch the north gate at night?')
    action['metadata'] = dict(communication=dict(recipient='NPC',purpose='QUESTION',evidence_refs=['npc:sergeant_mara:night_watch']),public_conversation_evidence={'npc:sergeant_mara:night_watch':fact})
    result = resolve_social_action(scene, session, world, action, raw_player_text='When is the gate left unguarded?')
    assert result['social']['topic_revealed'] is None and result['discovered_clues'] == []
    assert 'couldn' in adopt(result, 'When is the gate left unguarded?', fact, session)['player_facing_text']
