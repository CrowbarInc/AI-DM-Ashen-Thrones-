"""Cycle-local provider-free baseline, regression, and replay runner."""
from pathlib import Path
import ast, copy, hashlib, json, os, subprocess, sys, time
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT)); os.chdir(ROOT)
def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, default=str), encoding='utf-8')
def manifest():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('game','tests','data','static','prompts','tools','scripts')
            for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
mode = sys.argv[1]
if mode == 'entry':
    write('before_manifest.json', manifest())
    write('entry_identity.json', {k:subprocess.check_output(v,text=True).strip() for k,v in
        {'branch':['git','branch','--show-current'],'head':['git','rev-parse','HEAD']}.items()})
    (OUT/'entry_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short']))
    for name, path in [('entry_next_session.md','docs/NEXT_SESSION.md'),('entry_current_review.md','handoff/CURRENT_REVIEW.md')]:
        (OUT/name).write_bytes((ROOT/path).read_bytes())
    sys.exit()
for key in ('ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES','ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'):
    os.environ[key]='1'
for key in ('OPENAI_API_KEY','ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION','ASHEN_EXPERIMENTAL_DYNAMIC_NPCS','ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE','ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION'):
    os.environ.pop(key,None)
blocks=[]
def guard(event,args):
    if event in ('socket.connect','socket.getaddrinfo'):
        dest=args[1] if event=='socket.connect' else args[0]
        host=dest[0] if isinstance(dest,tuple) else dest
        if host not in ('127.0.0.1','::1','localhost'):
            blocks.append(str(dest)); raise RuntimeError('Live networking forbidden')
sys.addaudithook(guard)
os.environ['ASHEN_TEST_EVIDENCE_DIR']=str(OUT)
from tests.helpers.storage_isolation import install
install(ROOT/'development/tmp'/('object_instance_'+mode))
if 'sequence' not in mode:
    import pytest
    if 'combined' in mode:
        args=json.loads((ROOT/'artifacts/pr_play_t06_persistent_manipulation/baseline_command.json').read_text())['args']
        nodes=args[:args.index('-q')]
    elif 'marking' in mode:
        nodes=['tests/test_object_marking.py','tests/test_atomic_character_save.py']
    elif 'inventory_snapshot' in mode:
        nodes=['tests/test_pr_play_60_inventory_projection.py','tests/test_snapshots.py']
    elif 'identity' in mode:
        nodes=['tests/test_object_instances.py']
    else:
        args=json.loads((ROOT/'artifacts/pr_play_object_identity_architecture/validation_command.json').read_text())['args']
        nodes=args[:args.index('-q')]
    args=nodes+['-q','--tb=short','-p','no:cacheprovider','--junitxml='+str(OUT/(mode+'_junit.xml')),'--basetemp='+str(ROOT/'development/tmp'/('object_instance_'+mode+'_pytest'))]
    write(mode+'_command.json',{'executable':sys.executable,'args':args})
    import faulthandler
    faulthandler.dump_traceback_later(45, repeat=True)
    start=time.perf_counter(); code=pytest.main(args)
    faulthandler.cancel_dump_traceback_later()
    write(mode+'_execution.json',{'exit_code':int(code),'elapsed_s':time.perf_counter()-start,'network_blocks':blocks,'live_provider_calls':0})
    sys.exit(code)
from fastapi.testclient import TestClient
from game import storage, api
from tests.pr_play_79df3_harness import seed_gate
from pytest import MonkeyPatch
seed_gate(ROOT/'development/tmp'/('object_instance_'+mode),MonkeyPatch())
source=(ROOT/'artifacts/pr_play_t05_composition/run_sequence.py').read_text(encoding='utf-8')
turns=ast.literal_eval(source.split('TURNS = ',1)[1].split('\n]\n',1)[0]+'\n]')
def snap():
    return copy.deepcopy({'session':storage.load_session(),'character':storage.load_character(),'world':storage.load_world(),'scene':storage.load_scene(storage.load_session()['active_scene_id'])})
rows=[]
with TestClient(api.app) as client:
    for turn in turns:
        before=snap()
        response=client.post('/api/chat?ui_mode=player',json={'text':turn['text']})
        body=response.json(); log=copy.deepcopy(storage.load_log()[-1])
        rows.append({'id':turn['id'],'request':turn['text'],'status':response.status_code,'visible':(body.get('gm_output') or {}).get('player_facing_text'),'resolution':log.get('resolution'),'before':before,'after':snap(),'log':log,'body':body})
        print(turn['id'],rows[-1]['visible'],flush=True)
write(mode+'.json',{'turns':rows,'network_blocks':blocks,'live_provider_calls':0})
