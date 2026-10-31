import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import pytest
import game.immutable_valid_response as immutable
from tests.test_start_campaign_api import test_start_campaign_opening_fallback_basis_uses_journal_seed_not_visible_facts

captures=[]
real=immutable.run_preserve_if_valid
def wrap(gm,*args,**kwargs):
    result=real(gm,*args,**kwargs)
    captures.append(copy.deepcopy(result))
    return result
with pytest.MonkeyPatch.context() as mp:
    from tests.helpers.live_model_guard import install_live_model_guard
    install_live_model_guard(mp)
    mp.setenv('ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT','1')
    mp.setattr(immutable,'run_preserve_if_valid',wrap)
    try:
        test_start_campaign_opening_fallback_basis_uses_journal_seed_not_visible_facts(Path('development/tmp/pr_play_05/journal_probe'),mp)
    finally:
        Path('artifacts/pr_play_05/journal_probe.json').write_text(json.dumps(captures,indent=2))
