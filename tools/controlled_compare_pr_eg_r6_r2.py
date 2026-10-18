"""Controlled comparison with byte-identical state, prior history and proposals.

This is deterministic host-boundary evidence, never fresh-provider qualification.
"""
import copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_eg_r6_r2'
os.environ['ASHEN_DISABLE_EXPRESSION_GENERATION']='1'
os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION']='1'
os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
from tests.test_pr_eg_r6_r2_grounding import prop,proposal
from tests.test_pr_eg_r6_unified_semantic_planning import _multi_scene,_ask
from game import unified_semantic_planning as current
from game.dialogue_authority import select_host_speech
spec=importlib.util.spec_from_file_location('r6_controlled',OUT/'baseline_sources/game/unified_semantic_planning.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)


def main():
    cases=[
      ('A','Mara, what did Oren say about the north road?', 'Oren says the north road is flooded.',prop(predicate='say',subject='Oren',object='',missing='object',evidence='say'),prop(predicate='say',subject='Oren',object='north road is flooded',missing='',evidence='says'),'say_of(oren)'),
      ('B','Mara, who keeps the night drum?','The miller keeps the night ledger.',prop(),prop(subject='miller',object='night ledger',missing=''),'keep_of(night_drum)'),
      ('C','Mara, who told you the road name?','The road is called the north road.',prop(predicate='informant',object='road',evidence='told'),prop(predicate='name',subject='north road',object='road',missing='',evidence='called'),'source_of(road)'),
      ('D','Mara, which person oversees the ferry schedules?','The dock clerk manages the ferry schedules.',prop(predicate='responsibility',object='ferry schedules',evidence='oversees'),prop(predicate='responsibility',subject='dock clerk',object='ferry schedules',missing='',evidence='manages'),'oversee_of(ferry_schedules)'),
      ('E','I meant the north road.','The miller keeps the night ledger.',prop(object='north road',evidence='keeps',prior_reference='keeper_of(bell)'),prop(subject='miller',object='night ledger',missing=''),'keeper_of(north_road)'),
      ('F','No, who keeps the night ledger?','The miller keeps the night ledger.',prop(object='night ledger',prior_reference='keeper_of(bell)'),prop(subject='miller',object='night ledger',missing=''),'keeper_of(night_ledger)'),
      ('G','Who told you?','The road is called the north road.',prop(predicate='informant',object='road',object_evidence='road',evidence='told',prior_reference='keeper_of(bell)'),prop(predicate='name',subject='north road',object='road',evidence='called',missing=''),'source_of(road)'),
      ('H','Warden, who keeps the night ledger?','The miller keeps the night ledger.',prop(object='night ledger'),prop(subject='miller',object='night ledger',missing=''),'keeper_of(night_ledger)'),
      ('I','Mara, who keeps the night drum?','The miller keeps the night drum.',prop(),prop(subject='miller',missing=''),'keeper_of(night_drum)'),
      ('J','Mara, who keeps the night drum?','The miller keeps the night drum.',prop(),prop(subject='miller',missing=''),'keeper_of(night_drum)')]
    output=[]
    for ident,q,text,request,source,relationship in cases:
        scene,world=_multi_scene([{'id':'mara','name':'Mara','aliases':['warden'],'topics':[{'id':'fact','text':text,'disclosure':'secret' if ident=='J' else 'public'}]},{'id':'oren','name':'Oren','aliases':['warden'],'topics':[]}])
        session={}
        prior={'locked':True,'addressee_id':'mara','requested_relationship':'keeper_of(bell)','requested_subject':'bell','question_text':'Mara, who keeps the bell beside the road?','selected_source_ids':[]}
        if ident in {'E','F','G'}:session={'conversational_context':{'delivered_exchanges':[{'player_text':prior['question_text'],'delivered_text':'Mara says, "I do not know."','unified_semantic_plan':prior}]}}
        plan=proposal(request,source,candidate_source_ids=['fact'],proposed_coverage=[{'source_id':'fact','coverage':'direct'}]);plan['requested_relationship']=relationship
        if ident in {'E','F','G'}:
            plan['conversational_act']='follow_up' if ident=='G' else 'correction';plan['correction_target']=prior['question_text'];plan['referenced_prior_proposition']=prior['requested_relationship']
        digest=hashlib.sha256(json.dumps([world,scene,session],sort_keys=True).encode()).hexdigest()
        result={'case':ident,'player':q,'state_and_history_sha256':digest,'proposal':plan,'host_owned_text':text,'runs':{}}
        for label,module in [('r6',old),('r2',current)]:
            inputs=copy.deepcopy([world,scene,session]);r=module.authorize_information_turn(player_text=q,world=inputs[0],scene=inputs[1],session=inputs[2],proposal=copy.deepcopy(plan))
            assert inputs==[world,scene,session]
            result['runs'][label]=r['plan']
        os.environ[current.FLAG]='0'
        inputs=copy.deepcopy([world,scene,session]);resolution=_ask(inputs[0],inputs[2],q,scene=inputs[1]);line=select_host_speech(resolution,player_text=q,session=inputs[2])
        result['runs']['legacy']={'social':resolution.get('social'),'host_line':line[0] if line else ''}
        output.append(result)
    (OUT/'controlled_matched_comparison.json').write_text(json.dumps(output,indent=2,default=str))
    print('10 cases, 30 controlled executions; identical initial world, scene, delivered prior and proposal for R6/R2.')

if __name__=='__main__':main()
