"""Provider-free preservation checks for the architecture review."""
from pathlib import Path
import os, sys, json, time
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT)); os.chdir(ROOT)
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
            blocks.append(str(dest)); raise RuntimeError('Architecture review forbids external network')
sys.addaudithook(guard)
os.environ['ASHEN_TEST_EVIDENCE_DIR']=str(OUT)
from tests.helpers.storage_isolation import install
install(ROOT/'development/tmp/object_identity_architecture_storage')
import pytest
args=['tests/test_pr_play_76_physical.py','tests/test_pr_play_71_persistence_recovery.py',
      'tests/test_pr_play_75_persistence.py','tests/test_state_authority.py',
      'tests/test_pr_play_t06_persistent_manipulation.py','tests/test_pr_play_t04_local_action.py',
      'tests/test_pr_play_t05_composition.py','tests/test_pr_play_preseal_authority.py',
      '-q','--tb=short','-p','no:cacheprovider','--junitxml='+str(OUT/'preservation_junit.xml'),
      '--basetemp='+str(ROOT/'development/tmp/object_identity_architecture_pytest')]
(OUT/'validation_command.json').write_text(json.dumps({'executable':sys.executable,'args':args},indent=2))
start=time.perf_counter(); result=pytest.main(args)
(OUT/'validation_execution.json').write_text(json.dumps({'exit_code':int(result),'elapsed_s':time.perf_counter()-start,'network_blocks':blocks,'live_provider_calls':0},indent=2))
sys.exit(result)
