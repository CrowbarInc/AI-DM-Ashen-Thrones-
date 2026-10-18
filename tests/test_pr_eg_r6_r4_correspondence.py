"""Boundary tests for the isolated experiment, never production rewrites."""
from copy import deepcopy
import pytest
from experiments.pr_eg_r6_r4.corpus import cases
from experiments.pr_eg_r6_r4.engine import result, eligible, payload
from experiments.pr_eg_r6_r4.run import scoring


def case(family):return next(c for c in cases() if c['family']==family)
def proposal(c):
    s=c['sources'][0];return dict(source_id=s['id'],proposition=deepcopy(s['facts'][0]),
        evidence_span=s['text'],answer_role='',answer_value='',sufficiency='complete')


@pytest.mark.parametrize('c',cases(),ids=lambda c:c['id'])
def test_structured_contract(c):
    r=dict(result=result(c,'B'))
    s=scoring(c,r)
    if c['family']=='direct_unstructured':assert s['false_rejection']
    else:assert s['answer_success'],(c['id'],r,s)


@pytest.mark.parametrize('mutation',['invented_id','foreign_id','span','role_reversal','predicate','qualifier','answer','restricted','private','history','forged'])
def test_c_adversarial_rejected(mutation):
    c=case('direct_roles');p=proposal(c)
    if mutation=='invented_id':p['source_id']='invented'
    elif mutation=='foreign_id':c['sources'][0]['context']='elsewhere'
    elif mutation=='span':p['evidence_span']='made up quotation'
    elif mutation=='role_reversal':
        p['proposition']['roles'][0]['value']='Brin';p['proposition']['roles'][1]['value']='Cala'
    elif mutation=='predicate':p['proposition']['predicate']='own'
    elif mutation=='qualifier':p['proposition']['epistemic']='certain'
    elif mutation=='answer':p.update(answer_role='message_content',answer_value='the gate is open')
    elif mutation=='restricted':c['sources'][0]['disclosure']='secret'
    elif mutation=='private':c['sources'][0]['knowledge_status']='unknown'
    elif mutation=='history':c['sources'][0]['provenance']='verified_history'
    elif mutation=='forged':c['sources'][0]['provenance']='provider'
    r=result(c,'C',[p]);assert not r['selected_source_ids'];assert not r['bindings']


def test_c_quote_alone_not_semantic_authority():
    c=case('direct_unstructured');p=proposal(case('direct_exact'))
    p['source_id']=c['sources'][0]['id']
    assert result(c,'C',[p])['rejections']==['unverified_semantic_entailment']


@pytest.mark.parametrize('family',['restricted_password','restricted_countersign','unknown_private','unknown_history','unknown_forged'])
def test_payload_access_boundary(family):
    c=case(family);assert not eligible(c)
    assert not payload(c)['permitted_sources']
    assert c['sources'][0]['text'] not in str(payload(c))


def test_qualified_conflict_preserved():
    c=case('partial_conflict');r=result(c,'B')
    assert r['conflict'] and len(r['bindings']['keeper'])==2
    c=case('partial_rumor');r=result(c,'B')
    assert r['response_class']=='PARTIAL' and r['qualifiers'][0]['epistemic']=='rumor'


def test_grader_does_not_credit_safe_unknown_as_answer():
    c=case('direct_exact');s=scoring(c,dict(result=result(c,'C',[])))
    assert s['false_rejection'] and not s['answer_success'] and not s['roles_correct']


@pytest.mark.parametrize('architecture',['A','C'])
def test_provider_adapter_with_well_formed_source(architecture):
    c=case('direct_exact');r=result(c,architecture,[proposal(c)])
    assert r['response_class']=='DIRECT' and r['bindings']=={'keeper':'surveyor'}
