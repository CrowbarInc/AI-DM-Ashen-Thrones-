"""Existing authored-topic owner: quantitative relevance, policy and ambiguity."""
import pytest
from game.social import _next_topic_to_reveal, authored_answer_sufficient_for_question, classify_social_question_dimension
from game.dialogue_authority import authorize_npc_disclosure, build_dialogue_authority, requested_information

@pytest.mark.parametrize('question,answer,kind',[
 ('Vendor, what does the tea cost?','Tea costs six gold coins.','quantity'),
 ('Vendor, how much is tea?','Tea costs 12 copper coins.','quantity'),
 ('Guard Captain, how many riders took the west lane?','Five riders took the west lane.','quantity'),
 ('Guard Captain, what is the number of riders on the west lane?','One rider took the west lane.','quantity'),
 ('Guard Captain, which lane is shorter, the west lane or east lane?','The west lane is shorter than the east lane.','comparison'),
 ('Guard Captain, is the east lane longer than the west lane?','The west lane is shorter than the east lane.','comparison'),
])
def test_supported_information_reaches_existing_authority(question,answer,kind):
 npc={'id':'speaker','name':question.split(',')[0],'topics':[{'id':'answer','text':answer}]};selection={}
 assert classify_social_question_dimension(question)==kind
 assert requested_information(question)==kind
 topic=_next_topic_to_reveal(npc,{},player_text=question,selection=selection)
 assert topic and topic['text']==answer
 assert selection['selected_source']=='npc:speaker:answer'
 assert authorize_npc_disclosure(npc,topic)['permission']
 authority=build_dialogue_authority(question,npc=npc,social={'npc_id':'speaker','npc_name':npc['name'],'target_resolved':True,'topic_revealed':topic,'topic_selection':selection})
 assert authority['authorized_proposition']==answer
 assert authority['answer_sufficiency']=='directly_answers'

@pytest.mark.parametrize('policy',[{'disclosure':'forbidden'},{'hidden':True},{'secret':True},{'known':False},{'knowledge_status':'unknown'},{'disclosure':'unrecognized'}])
def test_matching_cannot_grant_disclosure(policy):
 npc={'id':'speaker','topics':[dict(id='tea',text='Tea costs six gold coins.',**policy)]};selection={}
 assert _next_topic_to_reveal(npc,{},player_text='What does the tea cost?',selection=selection) is None
 assert not selection['candidate_sources']
 assert not authorize_npc_disclosure(npc,npc['topics'][0])['permission']

@pytest.mark.parametrize('question,topic',[
 ('What does the tea cost?','Tea is sold at the west stall.'),
 ('How many riders took the west lane?','Riders took the west lane.'),
 ('Which lane is shorter, the west lane or east lane?','The west lane and east lane reach the gate.'),
])
def test_subject_mentions_do_not_answer_missing_dimensions(question,topic):
 assert not authored_answer_sufficient_for_question(question,{'id':'topic','text':topic})

@pytest.mark.parametrize('answer',['One rider took the lane.','Zero riders took the lane.','Twelve riders took the lane.','12 riders took the lane.','Tea costs six silver coins.'])
def test_quantity_forms(answer):
 from game.social import _stored_text_supports_dimension
 assert _stored_text_supports_dimension(answer,'quantity')

def test_competing_authorized_answers_clarify_and_wrong_npc_has_no_source():
 topics=[{'id':'one','text':'Tea costs six gold coins.'},{'id':'two','text':'Tea costs nine gold coins.'}];selection={}
 assert _next_topic_to_reveal({'id':'speaker','topics':topics},{},player_text='What does tea cost?',selection=selection) is None
 assert selection['ambiguous']
 assert _next_topic_to_reveal({'id':'other','topics':[]},{},player_text='What does tea cost?') is None

def test_hidden_classification_and_real_surveillance_keep_precedence():
 assert requested_information('Guard Captain, how many secret passwords are there?')=='hidden'
 assert requested_information('Who guards the west lane?')=='surveillance'
