"""R6-R2 controlled and adversarial correspondence qualification.

Provider fixtures exercise host boundaries, not live interpretation accuracy.
Frozen holdouts are evaluated separately, once, by the live runner.
"""
import copy
import json
import hashlib
from pathlib import Path

import pytest
from game import unified_semantic_planning as planning
from game.semantic_correspondence import coverage, proposition_schema
from game.defaults import default_session
from tests.test_pr_eg_r6_unified_semantic_planning import _multi_scene, _valid_plan


def prop(predicate='keeper', subject='', object='night drum', missing='subject', evidence='keeps', **kw):
    p={k:'' for k in proposition_schema()['properties']}
    p.update(predicate=predicate,predicate_evidence=evidence,subject=subject,subject_evidence=subject,
             object=object,object_evidence=object,missing_argument=missing,negated=False,epistemic='npc_knowledge')
    p.update(kw)
    return p


def fixture(text='The miller keeps the night drum.', disclosure='public'):
    return _multi_scene([{'id':'mara','name':'Mara','topics':[{'id':'fact','text':text,'disclosure':disclosure}]},
                         {'id':'oren','name':'Oren','topics':[]}])


def proposal(request=None, source=None, **kw):
    return _valid_plan(requested_relationship='keeper_of(night_drum)',requested_subject='night drum',
                       request_proposition=request or prop(),entity_roles=[],
                       source_propositions=[{'source_id':'fact','proposition':source or prop(subject='miller',subject_evidence='miller',missing='')}],**kw)


def ask(plan, text='Mara, who keeps the night drum?', source='The miller keeps the night drum.', disclosure='public',session=None):
    scene,world=fixture(source,disclosure)
    before=copy.deepcopy(world)
    locked=planning.authorize_information_turn(player_text=text,scene=scene,world=world,session=session or default_session(),proposal=plan)
    assert world==before
    return locked['plan']


def test_direct_semantic_answer():
    p=ask(proposal())
    assert p['response_kind']=='direct'
    assert p['selected_source_ids']==['fact']
    assert p['source_relevance']==[{'source_id':'fact','coverage':'direct'}]


@pytest.mark.parametrize('question,who,mentioned',[
 ('Mara, what did Oren say about the road?','mara','oren'),
 ('Oren, what did Mara say about the road?','oren','mara')])
def test_vocative_separates_mentions(question,who,mentioned):
    scene,world=fixture()
    with planning.plan_proposer(planning.deterministic_semantic_proposal):
        p=planning.authorize_information_turn(player_text=question,scene=scene,world=world,session={})['plan']
    assert p['addressee_id']==who
    assert p['mentioned_entity_ids']==[mentioned]


@pytest.mark.parametrize('text',['What did Mara tell Oren?','Sable, what did Oren say?'])
def test_no_address_invented_from_mentions(text):
    p=ask(proposal(),text=text)
    assert p['response_kind']=='clarification'
    assert not p['selected_source_ids']


def test_shared_alias_remains_ambiguous():
    scene,world=_multi_scene([{'id':'a','name':'North Guard','aliases':['guard']},{'id':'b','name':'South Guard','aliases':['guard']}])
    p=planning.authorize_information_turn(player_text='Guard, who keeps the night drum?',scene=scene,world=world,proposal=proposal())['plan']
    assert p['ambiguity_type']=='addressee'


@pytest.mark.parametrize('slot,value,evidence',[
 ('object','night ledger','night ledger'),('subject','Oren','Oren')])
def test_argument_substitution_rejected(slot,value,evidence):
    request=prop(subject='Mara',subject_evidence='Mara',missing='object',object='',object_evidence='') if slot=='subject' else prop()
    source=prop(subject='miller',missing='')
    source[slot]=value;source[slot+'_evidence']=evidence
    p=ask(proposal(request,source),source=f'{value} keeps the night ledger.')
    assert not p['selected_source_ids']


def test_night_drum_not_ledger_in_compatibility_adapter():
    assert planning.classify_source_coverage('keep_of(night_drum)','who keeps the night drum','The miller keeps the night ledger.') not in {'direct','partial'}


def test_road_name_is_not_informant():
    request=prop(predicate='informant',object='road',evidence='told')
    source=prop(predicate='name',subject='north road',object='road',missing='',evidence='called',subject_evidence='north road')
    p=ask(proposal(request,source),text='Mara, who told you about the road?',source='The road is called the north road.')
    assert p['source_relevance'][0]['coverage']=='related_but_nonanswer'
    assert p['response_kind']=='unknown'


def test_paraphrased_relationship_without_shared_stems():
    request=prop(predicate='responsibility',object='departures',evidence='responsible')
    source=prop(predicate='responsibility',subject='miller',object='departures',evidence='oversees',missing='')
    p=ask(proposal(request,source),text='Mara, who is responsible for departures?',source='The miller oversees departures.')
    assert p['response_kind']=='direct'


@pytest.mark.parametrize('field,value',[('temporal','tomorrow'),('spatial','north'),('negated',True)])
def test_qualifier_mismatch_is_not_direct(field,value):
    request=prop(**{field:value})
    source=prop(subject='miller',missing='')
    text='Mara, who keeps the night drum tomorrow in the north?'
    p=ask(proposal(request,source),text=text)
    assert p['response_kind']=='unknown'
    assert p['request_proposition'][field]==value


def test_partial_requires_same_relationship():
    source=prop(subject='',subject_evidence='',missing='subject')
    p=ask(proposal(source=source))
    assert p['response_kind']=='partial'


@pytest.mark.parametrize('epistemic',['rumor','belief'])
def test_epistemic_qualification_not_promoted(epistemic):
    scene,world=fixture('The miller keeps the night drum.')
    world['npcs'][0]['topics'][0]['epistemic']=epistemic
    source=prop(subject='miller',missing='',epistemic=epistemic)
    p=planning.authorize_information_turn(player_text='Mara, who keeps the night drum?',scene=scene,world=world,proposal=proposal(source=source))['plan']
    assert p['response_kind']=='partial'
    assert p['epistemic_status']==epistemic


@pytest.mark.parametrize('disclosure',['secret','restricted','private'])
def test_relevance_never_grants_disclosure(disclosure):
    p=ask(proposal(),disclosure=disclosure)
    assert not p['selected_source_ids']
    assert not p['authorized_text']


def test_forged_source_id_cannot_select_text():
    plan=proposal(candidate_source_ids=['forged'])
    plan['source_propositions'][0]['source_id']='forged'
    p=ask(plan)
    assert p['response_kind']=='unknown'
    assert 'forged' in p['rejected_source_ids']


@pytest.mark.parametrize('change',[
 {'canonical_fact':'invented'},
 {'entity_roles':[{'role':'mentioned_npc','entity_id':'phantom','reference':'Sable','evidence':'Sable'}]},
 {'entity_roles':[{'role':'mentioned_npc','entity_id':'oren','reference':'Oren','evidence':'Oren'}]},
])
def test_forged_authority_or_entity_rejected(change):
    plan=proposal();plan.update(change)
    p=ask(plan)
    assert p['response_kind']=='clarification'
    assert not p['selected_source_ids']


@pytest.mark.parametrize('field',['predicate_evidence','subject_evidence','object_evidence'])
def test_unwitnessed_source_interpretation_rejected(field):
    source=prop(subject='miller',missing='');source[field]='invented secret'
    p=ask(proposal(source=source))
    assert p['response_kind']=='unknown'


def test_provider_confidence_cannot_upgrade_unknown():
    plan=proposal();plan['source_propositions']=[];plan['interpretation_confidence']=1
    plan['proposed_coverage']=[{'source_id':'fact','coverage':'direct'}]
    assert ask(plan)['response_kind']=='unknown'


def prior_session():
    return {'conversational_context':{'delivered_exchanges':[{'player_text':'Mara, who keeps the bell?',
       'delivered_text':'Mara says, "I do not know."', 'unified_semantic_plan':{'locked':True,
       'question_text':'Mara, who keeps the bell?','requested_subject':'bell','requested_relationship':'keeper_of(bell)',
       'addressee_id':'mara','selected_source_ids':[]}}]}}


def test_entity_only_correction_preserves_relation():
    prior=prior_session()
    p=planning.deterministic_semantic_proposal({'utterance':'I meant the north road.','prior_plan':planning.prior_semantic_plan(prior),'participants':[]})
    assert p['requested_relationship']=='keeper_of(north_road)'


@pytest.mark.parametrize('act',['correction','follow_up'])
def test_structured_continuity_is_not_lexically_rewritten(act):
    session=prior_session()
    request=prop(prior_reference='keeper_of(bell)')
    plan=proposal(request,conversational_act=act,correction_target='Mara, who keeps the bell?',referenced_prior_proposition='keeper_of(bell)')
    text='I meant who keeps the night drum?' if act=='correction' else 'Who keeps the night drum?'
    p=ask(plan,text=text,session=session)
    assert p['requested_relationship']=='keeper_of(night_drum)'
    assert p['addressee_id']=='mara'
    assert p['response_kind']=='direct'


@pytest.mark.parametrize('act',['correction','follow_up'])
def test_bad_prior_target_cannot_launder_history(act):
    plan=proposal(prop(prior_reference='forged'),conversational_act=act,correction_target='invented')
    assert ask(plan,text='Who told you?',session=prior_session())['response_kind']=='clarification'


def test_history_is_not_candidate_source():
    plan=proposal();plan['source_propositions'][0]['source_id']='history:1'
    assert ask(plan,session=prior_session())['response_kind']=='unknown'


def test_candidate_prompt_excludes_restricted_text(monkeypatch):
    scene,world=fixture();world['npcs'][0]['topics'].append({'id':'password','text':'protected sentinel','disclosure':'secret'})
    seen=[]
    def capture(context):
        seen.append(planning._provider_context(context));return proposal()
    with planning.plan_proposer(capture):
        planning.authorize_information_turn(player_text='Mara, who keeps the night drum?',scene=scene,world=world)
    assert 'protected sentinel' not in json.dumps(seen)
    assert [x['id'] for x in seen[0]['permitted_sources']]==['fact']


def test_save_load_keeps_proposition_and_roles():
    p=ask(proposal())
    session={'conversational_context':{'delivered_exchanges':[{'unified_semantic_plan':p}]}}
    restored=json.loads(json.dumps(session))
    assert planning.prior_semantic_plan(restored)['request_proposition']==p['request_proposition']


def test_frozen_inputs_unchanged():
    root=Path('artifacts/pr_eg_r6_r2');freeze=json.loads((root/'freeze.json').read_text())
    assert hashlib.sha256((root/'frozen_holdouts.json').read_bytes()).hexdigest()==freeze['sha256']
    assert hashlib.sha256(Path('artifacts/pr_eg_r6/frozen_holdouts.json').read_bytes()).hexdigest()==freeze['original_sha256']
