"""Execute existing boundary tests with replay output redirected into R5."""
import os,sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
os.environ.update(ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1',ASHEN_DISABLE_LIVE_INTERPRETATION='1',ASHEN_DISABLE_EXPRESSION_GENERATION='1',ASHEN_DISABLE_PROVIDER_CALLS='1',ASHEN_PROVIDER_REQUEST_LIMIT='0',ASHEN_DATA_DIR=str(OUT/'test_import_state'))
import tools.qualify_pr_eg_r4_r1 as replay
replay.OUT=OUT/'controlled_replay';replay.OUT.mkdir(exist_ok=True)
import pytest
class IsolatedEnvironment:
    @pytest.fixture(autouse=True)
    def reset_provider_flag(self,monkeypatch):
        # Existing replay sets this process flag to 1 without restoring it.
        # Expression tests stub their transport but need the feature enabled.
        # The independent zero request budget still forbids real transmission.
        monkeypatch.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0')
args=['tests/test_pr_eg_r4_r1_delivery_integrity.py','tests/test_pr_eg_r3_expressive_dialogue.py','tests/test_pr_eg_r3_r1_expression_semantics.py','-q','--basetemp='+str(OUT/'pytest_tmp'),'--junitxml='+str(OUT/'checks_junit.xml'),'-p','no:cacheprovider']
start=time.perf_counter();code=pytest.main(args,plugins=[IsolatedEnvironment()])
(OUT/'checks_run.json').write_text(json.dumps(dict(args=args,exit_code=code,elapsed_seconds=time.perf_counter()-start,provider_requests_allowed=0),indent=2))
sys.exit(code)
