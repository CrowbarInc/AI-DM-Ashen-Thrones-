"""Matched production-path comparison using preserved R6 module or final R2 module."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
mode=sys.argv[1]
if mode=='r6':
    spec=importlib.util.spec_from_file_location('game.unified_semantic_planning',ROOT/'artifacts/pr_eg_r6_r2/baseline_sources/game/unified_semantic_planning.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    import game
    game.unified_semantic_planning=module
from tools import qualify_pr_eg_r6_r2 as runner
runner.OUT=ROOT/'artifacts/pr_eg_r6_r2'/('matched_'+mode)

def specs():
    from tools.qualify_pr_eg_r6 import npc,topic
    topics=[topic('road','Oren says the north road is flooded.'),topic('ledger','The miller keeps the night ledger.'),topic('name','The north road is called the Crown Way.'),topic('manager','The dock clerk manages the ferry schedules.'),topic('bell','The harbor bell is called the Tide Bell.'),topic('password','The gate password is sword.','secret')]
    cast=[npc('mara','Mara','warden',topics,aliases=['warden']),npc('oren','Oren','warden',topics,aliases=['warden'])]
    questions=[('Mara, what did Oren say about the north road?',{'addressee':'mara','sufficiency':'direct'}),('Mara, who keeps the night drum?',{'addressee':'mara','sufficiency':'unknown'}),('Oren, who told you the north road name?',{'addressee':'oren','sufficiency':'unknown'}),('Mara, which person oversees the ferry schedules?',{'addressee':'mara','sufficiency':'direct'}),('I meant the harbor bell.',{'act':'correction'}),('No, who keeps the night ledger?',{'act':'correction','sufficiency':'direct'}),('Who told you?',{'act':'follow_up','sufficiency':'unknown'}),('Warden, who keeps the night ledger?',{'sufficiency':'clarification'}),('Mara, who manages the ferry schedules?',{'addressee':'mara','sufficiency':'direct'}),('Mara, what is the gate password?',{'addressee':'mara','sufficiency':'refusal'})]
    return [{'id':'matched','npcs':cast,'turns':questions,'source':'matched_'+mode}]
runner.specifications=specs
# The runner sets the gate itself. Legacy mode is run with a tiny wrapper around
# TestClient dispatch rather than maintaining another production implementation.
if mode=='legacy':
    import os
    from fastapi.testclient import TestClient
    original=TestClient.post
    def post(self,*args,**kwargs):
        os.environ['ASHEN_UNIFIED_SEMANTIC_PLANNING']='0'
        return original(self,*args,**kwargs)
    TestClient.post=post
runner.main()
