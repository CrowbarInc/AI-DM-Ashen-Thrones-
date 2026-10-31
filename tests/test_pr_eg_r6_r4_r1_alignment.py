"""Adversarial boundary tests; synthetic inputs are not provider qualification."""
from copy import deepcopy
import json
import pytest
from experiments.pr_eg_r6_r4_r1 import engine as E
from experiments.pr_eg_r6_r4_r1.corpus import build


def source(): return build()[0]['sources'][0]
def fact():
    return dict(fact_id='f1',source_id='s00',relationship='keep',
        roles=[dict(name='keeper',value='surveyor',evidence='surveyor'),dict(name='object',value='amber lens',evidence='amber lens')],
        unknown_roles=[],qualifiers=[],negated=False,temporal='',spatial='',epistemic='npc_knowledge',
        provenance='world_source',evidence_span='The surveyor keeps the amber lens in a padded case.')


@pytest.mark.parametrize('change,reason',[
    ({'source_id':'forged'},'unavailable_source_id'),
    ({'evidence_span':'Invented evidence'},'evidence_span_mismatch'),
    ({'provenance':'canonical_fact'},'authority_mismatch'),
    ({'epistemic':'canonical_truth'},'authority_mismatch'),
    ({'qualifiers':['certainly']},'qualifier_anchor_mismatch'),
    ({'temporal':'tomorrow'},'scope_anchor_mismatch'),
    ({'roles':[dict(name='keeper',value='queen',evidence='surveyor')]},'argument_anchor_mismatch'),
])
def test_c_rejects_mechanical_forgery(change,reason):
    f=fact();f.update(change)
    v=E.validate(f,[source()],'C')
    assert v['level']=='REJECTED' and reason in v['reasons']


def test_role_swap_proves_anchoring_is_not_entailment():
    f=fact();f['roles'][0]['name']='object';f['roles'][1]['name']='keeper'
    v=E.validate(f,[source()],'C')
    assert v['level']=='SOURCE_ANCHORED' and v['semantic_support']=='unestablished'


@pytest.mark.parametrize('key,val', [('disclosure','secret'),('knowledge_status','unknown'),('npc','other'),('context','foreign'),('provenance','verified_history')])
def test_unavailable_sources_never_enter_public_payload(key,val):
    s=source();s[key]=val
    assert E.public_sources(E.eligible([s],'vesper','experiment'))==[]


def test_b_and_c_are_different_validators():
    f=fact();f['evidence_span']='fabricated'
    assert E.validate(f,[source()],'B')['level']=='STRUCTURALLY_VALID'
    assert E.validate(f,[source()],'C')['level']=='REJECTED'


def test_candidate_has_no_delivery_or_canonical_authority():
    a=dict(response_class='DIRECT',values=['surveyor'],qualifiers=[],selected_fact_ids=['f1'],selected_source_ids=['s00'])
    g=E.candidate_gate(a,[fact()],[source()])
    assert g['candidate_eligible'] and not g['delivery_authorized'] and not g['canonical']
    a['selected_source_ids']=['foreign']
    assert 'unavailable_source_id' in E.candidate_gate(a,[fact()],[source()])['reasons']


def test_lost_qualifier_is_a_prediction_failure_not_safe_success():
    c=build()[8]['cases'][0]
    a=dict(response_class='DIRECT',values=['keeper'],qualifiers=[])
    assert E.score(c,a)['false_acceptance']
    a.update(response_class='UNKNOWN',values=[])
    assert not E.score(c,a)['answer_success'] and E.score(c,a)['false_rejection']


def test_corpus_has_diversity_and_family_partitions():
    fs=build();assert len(fs)==34 and sum(len(f['cases']) for f in fs)==170
    assert len({f['category'] for f in fs})==34
    assert sum(bool(E.eligible(f['sources'],f['cases'][0]['npc'],'experiment')) for f in fs)==30
    for f in fs:
        assert len({c['partition'] for c in f['cases']})==1
        for c in f['cases']:
            if c['expected']['response_class']=='DIRECT':
                assert c['expected']['values']
                assert not set(c['expected']['values']) & set(c['gold_diagnostic']['known_roles'].values())


def test_historical_authority_never_promoted():
    f=build()[26];assert f['sources'][0]['provenance']=='verified_history'
    assert E.eligible(f['sources'],f['cases'][0]['npc'],'experiment')==[]


def test_duplicate_fact_ids_reject_both():
    records=E.validate_extraction({'facts':[fact(),fact()]},[source()],'C')
    assert all(r['validation']['level']=='REJECTED' for r in records)


def test_schema_failure_is_recorded():
    for f in ({},None,[],{'source_id':'s00'}):
        assert E.validate(f,[source()],'C')['level']=='REJECTED'
