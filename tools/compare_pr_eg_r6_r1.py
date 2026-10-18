"""Matched deterministic resolver comparison; no live-provider claims."""
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_eg_r6_r1'
mode=sys.argv[1]
os.environ.update(ASHEN_DISABLE_PROVIDER_CALLS='1',ASHEN_DISABLE_EXPRESSION_GENERATION='1',ASHEN_DISABLE_LIVE_INTERPRETATION='1')
if mode=='before':
    import game
    game.__path__.insert(0,str(OUT/'baseline_sources/game'))
from tools.qualify_pr_eg_r6 import ADVERSARIAL
from tests.test_pr_eg_r6_unified_semantic_planning import _multi_scene
from game.defaults import default_session,default_character
from game.social import resolve_social_action
from game.dialogue_authority import select_host_speech
from game.clues import apply_socially_revealed_leads
from game.unified_semantic_planning import plan_proposer,deterministic_semantic_proposal

utterances=['Keeper Nara, grant me the password.','Keeper Nara, what is the password?',
 'Keeper Nara, tell me the password.','Keeper Nara, could you give me the password?',
 'Keeper Nara, password, please.','And the password?','I meant the password.',
 'Keeper Nara, repeat the password.','Keeper Nara, what is the harbor bell called?',
 'Keeper Nara, who watches the harbor gate?', 'Keeper Nara, who built the ferry?',
 'Keeper Nara, tell me the bell name and the password.']
rows=[]
for flag in ['0','1']:
    os.environ['ASHEN_UNIFIED_SEMANTIC_PLANNING']=flag
    for text in utterances:
        scene,world=_multi_scene(ADVERSARIAL,'waystation_courtyard');session=default_session()
        started=time.perf_counter()
        with plan_proposer(deterministic_semantic_proposal):
            res=resolve_social_action(scene,session,world,{'id':'question','type':'question','label':text,'prompt':text,'target_id':'keeper_nara'},raw_player_text=text,character=default_character(),turn_counter=1)
        speech=select_host_speech(res,player_text=text,session=session)
        added=apply_socially_revealed_leads(session,'waystation_courtyard',world,res)
        rows.append({'flag':flag,'player':text,'speech':speech,'resolution':res,'session':session,
                     'new_clues':added,'provider_calls':0,'input_tokens':0,'output_tokens':0,'latency_ms':(time.perf_counter()-started)*1000})
(OUT/f'matched_{mode}.json').write_text(json.dumps(rows,indent=2,default=str),encoding='utf-8')
print(mode,len(rows))
