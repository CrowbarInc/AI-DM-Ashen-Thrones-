"""R2C: information, final-response and persistence integrity at production seams."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from game import api, storage
from game.conversational_continuity import record_delivered_exchange, continuity_directive
from game.dialogue_authority import build_dialogue_authority, remember_dialogue_commitment
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
    if fact:
        social['topic_revealed'] = dict(id='fact', text=fact)
    social['dialogue_authority'] = build_dialogue_authority(question, social=social, session=session)
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
