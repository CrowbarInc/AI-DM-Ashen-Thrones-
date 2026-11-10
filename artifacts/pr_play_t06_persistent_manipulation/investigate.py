"""T06 provider-free investigation; no production mutation extensions."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
for key in ('ASHEN_DISABLE_PROVIDER_CALLS', 'ASHEN_DISABLE_LIVE_INTERPRETATION',
            'ASHEN_DISABLE_EXPRESSION_GENERATION', 'ASHEN_DISABLE_PROVIDER_RETRIES',
            'ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'):
    os.environ[key] = '1'
for key in ('OPENAI_API_KEY', 'ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION',
            'ASHEN_EXPERIMENTAL_DYNAMIC_NPCS', 'ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE',
            'ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION'):
    os.environ.pop(key, None)
blocked = []
def guard(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo'):
        dest = args[1] if event == 'socket.connect' else args[0]
        host = dest[0] if isinstance(dest, tuple) else dest
        if host not in ('127.0.0.1', '::1', 'localhost'):
            blocked.append(str(dest))
            raise RuntimeError('T06 investigation forbids external network')
sys.addaudithook(guard)

def write(name, obj):
    (OUT/name).write_text(json.dumps(obj, indent=2, default=str), encoding='utf-8')

def manifest():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('game', 'tests', 'data', 'static', 'prompts')
            for p in (ROOT/folder).rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and p.suffix != '.pyc'}

mode = sys.argv[1]
if mode == 'entry':
    write('before_manifest.json', manifest())
    write('entry_identity.json', {'branch': subprocess.check_output(['git','branch','--show-current'], text=True).strip(),
        'head': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()})
    (OUT/'entry_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short']))
    (OUT/'entry_next_session.md').write_bytes((ROOT/'docs/NEXT_SESSION.md').read_bytes())
    (OUT/'entry_current_review.md').write_bytes((ROOT/'handoff/CURRENT_REVIEW.md').read_bytes())
    exit()

os.environ['ASHEN_TEST_EVIDENCE_DIR'] = str(OUT)
from tests.helpers.storage_isolation import install
install(ROOT/'development/tmp'/('t06_'+mode))

if mode in ('baseline', 'after', 'persistence_controls', 'focused'):
    import pytest
    if mode == 'focused':
        nodes = ['tests/test_pr_play_t06_persistent_manipulation.py']
    elif mode == 'persistence_controls':
        nodes = ['tests/test_pr_play_76_physical.py', 'tests/test_pr_play_71_persistence_recovery.py',
                 'tests/test_pr_play_75_persistence.py', 'tests/test_state_authority.py']
    else:
        tree = ET.parse(ROOT/'artifacts/pr_play_t04_local_action/after_regression_junit.xml')
        expected = [t.attrib['classname'].replace('.', '/')+'.py::'+t.attrib['name'] for t in tree.iter('testcase')]
        assert len(expected) == 425
        main = json.loads((ROOT/'artifacts/pr_play_t05_composition/after_final/command.json').read_text())['args']
        authority = json.loads((ROOT/'artifacts/pr_play_t05_composition/after_final/authority/command.json').read_text())['args']
        nodes = main[:main.index('-q')]+authority[:authority.index('-q')]+[
            'tests/test_pr_play_preseal_authority.py','tests/test_pr_play_t05_composition.py',
            'tests/test_pr_play_t04_local_action.py']
    args = nodes+['-q','--tb=short','-p','no:cacheprovider', '--junitxml='+str(OUT/(mode+'_junit.xml')),
                  '--basetemp='+str(ROOT/'development/tmp'/('t06_'+mode+'_pytest'))]
    previous=OUT/(mode+'_command.json')
    if mode in ('baseline','after') and previous.exists() and len(json.loads(previous.read_text())['args'])>400:
        write(mode+'_aborted_node_command.json',json.loads(previous.read_text()))
    write(mode+'_command.json', {'executable':sys.executable,'args':args})
    class CheckCollection:
        def pytest_collection_finish(self,session):
            actual=[item.nodeid for item in session.items]
            write(mode+'_collected_nodes.json',actual)
            if mode in ('baseline','after'):
                assert sorted(actual)==sorted(expected),(len(actual),len(expected))
    import faulthandler
    faulthandler.dump_traceback_later(90,repeat=True)
    start = time.perf_counter()
    code = pytest.main(args,plugins=[CheckCollection()])
    faulthandler.cancel_dump_traceback_later()
    write(mode+'_execution.json', {'exit_code':code,'elapsed_s':time.perf_counter()-start,
        'network_blocks':blocked,'live_provider_calls':0})
    exit()

from fastapi.testclient import TestClient
from game import storage, api
from tests.pr_play_79df3_harness import seed_gate
class Monkey:
    def setenv(self, key, value): os.environ[key] = str(value)
    def delenv(self, key, raising=True): os.environ.pop(key, None)
    def setattr(self, target, name, value, raising=True):
        if isinstance(target, str):
            module, attr = target.rsplit('.',1)
            setattr(sys.modules[module], attr, value)
        else: setattr(target,name,value)

seed_gate(ROOT/'development/tmp'/('t06_'+mode), Monkey())
source = (ROOT/'artifacts/pr_play_t05_composition/run_sequence.py').read_text(encoding='utf-8')
turns = ast.literal_eval(source.split('TURNS = ',1)[1].split('\n]\n',1)[0]+'\n]')
def snap():
    return copy.deepcopy({'session':storage.load_session(), 'character':storage.load_character(),
        'world':storage.load_world(), 'scene':storage.load_scene(storage.load_session()['active_scene_id'])})
events=[]
import game.intent_parser as parser
import game.immutable_valid_response as ivr
import game.conversational_orchestration as orchestration
def wrap(module,name):
    original = getattr(module,name)
    def traced(*args,**kwargs):
        value=original(*args,**kwargs)
        events.append({'function':module.__name__+'.'+name,'args':copy.deepcopy(args),
                       'kwargs':copy.deepcopy(kwargs),'result':copy.deepcopy(value)})
        return value
    setattr(module,name,traced)
for module,names in ((parser,('parse_freeform_to_action','recover_actionable_explicit_world_action')),
                     (orchestration,('_unbound_physical_decline',)),
                     (ivr,('seal_accepted_response',))):
    for name in names: wrap(module,name)
rows=[]
start=time.perf_counter()
with TestClient(api.app) as client:
    for turn in turns:
        before=snap(); events.clear()
        response=client.post('/api/chat?ui_mode=player',json={'text':turn['text']})
        after=snap(); log=copy.deepcopy(storage.load_log()[-1])
        body=response.json()
        rows.append({'id':turn['id'],'request':turn['text'],'status':response.status_code,
                     'visible':(body.get('gm_output') or {}).get('player_facing_text'),
                     'resolution':log.get('resolution'), 'before':before,'after':after,
                     'log':log,'body':body,'events':copy.deepcopy(events)})
        print(turn['id'], rows[-1]['visible'], flush=True)
        if turn['id']=='T06': write(mode+'_t06.json',rows[-1])
write(mode+'_sequence.json',{'turns':rows,'elapsed_ms':(time.perf_counter()-start)*1000,
                            'network_blocks':blocked,'live_provider_calls':0})
