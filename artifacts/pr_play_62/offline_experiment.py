"""No-provider controls and injected failures; never rewrites PR61 evidence."""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_61 import run_experiment as base
OUT=ROOT/'artifacts/pr_play_62'
base.OUT=OUT
os.environ['ASHEN_PROVIDER_USAGE_PATH']=str(OUT/'offline_usage.jsonl')
from game import integrated_investigation_narration as integrated
from game import quarantined_investigation_narration as q
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
from game import api
api.call_gpt=lambda *a,**k:_gm_response('Provider calls are disabled for this run, so no live narration was generated.')
ACTIONS=[base.NOTICE,base.BARREL,base.REPEAT,base.LOOK,base.BARREL]
base.disable_publication();base._seed(OUT/'control_session',base._Patch(),'frontier_gate')
control={'before':base.authority(),'actions':base.post_all(ACTIONS),'after':base.authority()}
(OUT/'control.json').write_text(json.dumps(control,indent=2))
failures=base.failure_injection()
(OUT/'failure_injection.json').write_text(json.dumps(failures,indent=2))
isolation=base.isolation_check('different-bound-session')
(OUT/'isolation.json').write_text(json.dumps(isolation,indent=2))
# Original candidates, traces and fallbacks remain verbatim in restricted evidence.
history=json.loads((ROOT/'artifacts/pr_play_61/experiment_results.json').read_text())
(OUT/'pr_play_61_reconstruction.json').write_text(json.dumps({'original_live':history['live'],'original_replay':json.loads((ROOT/'artifacts/pr_play_61/replay_results.json').read_text()),'original_traces':[json.loads(p.read_text()) for p in sorted((ROOT/'artifacts/pr_play_61/quarantine_evidence').glob('*.json'))[:4]]},indent=2))
print('Offline controls, failures and isolation complete',flush=True)
