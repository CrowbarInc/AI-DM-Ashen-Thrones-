"""Identical-input host comparison, separate from fresh-provider qualification."""
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_eg_r6_r2_r1'
os.environ.update(ASHEN_UNIFIED_SEMANTIC_PLANNING='1',ASHEN_DISABLE_PROVIDER_CALLS='1')
from game import unified_semantic_planning as current, conversational_referents as refs
from game.conversational_continuity import record_delivered_exchange
from game.immutable_valid_response import seal_host_speech, accepted_record
from tests.test_pr_eg_r6_r2_grounding import prop
from tests.test_pr_eg_r6_r2_r1_referents import question,operation
from tests.test_pr_eg_r6_unified_semantic_planning import _multi_scene
spec=importlib.util.spec_from_file_location('r6r2_snapshot',OUT/'baseline_sources/game/unified_semantic_planning.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)


def run():
    results=[]
    for case in ['amber_copper','aqueduct_attribution','north_road','multiple_npc','partial_follow_up','ambiguous_alternative','public_answer','restricted_answer']:
        scene,world=_multi_scene([{'id':'tavi','name':'Tavi','topics':[{'id':'fact','text':'The miller keeps the copper reliquary.','disclosure':'secret' if case=='restricted_answer' else 'public'}]},
            {'id':'mara','name':'Mara','topics':[{'id':'fact','text':'Oren says the road is flooded.'}]},{'id':'oren','name':'Oren','topics':[]}])
        session={}
        initial='amber reliquary' if case=='amber_copper' else 'aqueduct' if case=='aqueduct_attribution' else 'bell'
        initial_request=prop(object=initial,object_evidence=initial)
        if case=='aqueduct_attribution':initial_request.update(predicate='name',predicate_evidence='called')
        first_question=f'Tavi, who keeps the {initial}?' if case!='aqueduct_attribution' else 'Tavi, what is the aqueduct called?'
        if case in {'amber_copper','aqueduct_attribution','north_road','partial_follow_up','ambiguous_alternative'}:
            if case=='partial_follow_up':
                world['npcs'][0]['topics'][0]['text']='Someone keeps the bell.'
                p=question(initial_request);p['source_propositions'][0]['proposition']=prop(object='bell',object_evidence='bell',missing='subject')
            else:
                p=question(initial_request);p['source_propositions']=[]
            locked=current.authorize_information_turn(player_text=first_question,world=world,scene=scene,session=session,proposal=p)['plan']
            gm=seal_host_speech({},text=locked['host_line'],source='host',speaker_id='tavi',speaker_name='Tavi',resolution=None,player_text=first_question)
            record_delivered_exchange(session,player_text=first_question,delivered_text=gm['player_facing_text'],turn=1,
                social={'npc_id':'tavi','npc_name':'Tavi','unified_semantic_plan':locked},adoption=accepted_record(gm))
        target=refs.active(session)
        q='Tavi, who keeps the copper reliquary?';p=question(prop(object='copper reliquary',object_evidence='copper reliquary'))
        p['source_propositions'][0]['proposition']=prop(subject='miller',object='copper reliquary',missing='')
        if case in {'amber_copper','north_road'}:
            obj='copper reliquary' if case=='amber_copper' else 'north road'
            q='I meant the copper reliquary.' if case=='amber_copper' else "I wasn't asking about the bell. I meant the north road."
            p['conversational_act']='correction';p['request_proposition']={**initial_request,'object':obj,'object_evidence':obj}
            p['referent_operation']=operation(target['referent_id'],'replace_object',['object'])
        elif case in {'aqueduct_attribution','partial_follow_up','ambiguous_alternative'}:
            q='Who told you?' if case!='ambiguous_alternative' else 'And the other one?'
            p['conversational_act']='follow_up';p['request_proposition']=prop(predicate='informant',evidence='told',object=initial,object_evidence=initial)
            p['referent_operation']=operation(target['referent_id'],fields=['object'] if case=='ambiguous_alternative' else [],
                follow='alternative_argument' if case=='ambiguous_alternative' else 'source_attribution')
        elif case=='multiple_npc':
            q='Mara, what did Oren say about the road?';p=question(prop(predicate='say',evidence='say',subject='Oren',object='road',missing='predicate'))
            p['source_propositions']=[]
        before=copy.deepcopy([world,scene,session]);runs={}
        for label,module in [('r6_r2',old),('durable',current)]:
            inputs=copy.deepcopy(before)
            runs[label]=module.authorize_information_turn(player_text=q,world=inputs[0],scene=inputs[1],session=inputs[2],proposal=copy.deepcopy(p))['plan']
            assert inputs==before
        results.append({'case':case,'player':q,'identical_inputs_sha256':hashlib.sha256(json.dumps([*before,p],sort_keys=True).encode()).hexdigest(),
            'initial_state':before,'proposal':p,'runs':runs})
    (OUT/'controlled_matched_comparison.json').write_text(json.dumps(results,indent=2))
    print('Eight cases, sixteen identical-input host executions; not provider qualification.')


if __name__=='__main__':run()
