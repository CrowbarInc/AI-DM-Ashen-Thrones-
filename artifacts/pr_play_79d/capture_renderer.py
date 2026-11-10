"""Capture the final controlled-renderer fixture through its actual owners."""
import copy, json, os, sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tests.helpers.storage_isolation import install
install(OUT/'controlled_probe_data')
for key in ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT','ASHEN_DISABLE_PROVIDER_CALLS',
            'ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION']:
    os.environ[key]='1'
from tests.test_pr_play_47_controlled_renderer import scenarios, payload, STYLES, Stub, cr
from game.api import deterministic_provider_skip_line
from game.defaults import default_session
row=scenarios()[5]
before=copy.deepcopy(row)
view=cr.authorize_investigation(row['resolution'],payload(row['scene'],row['known']))
selected=deterministic_provider_skip_line(resolution=row['resolution'],scene=row['scene'],world={},
    session=default_session(),player_text=row['player'])
outputs=[dict(style=style,**json.loads(cr.preview_investigation(view,Stub(plan),enabled=True).to_json()))
         for style,plan in STYLES.items()]
assert row==before
(OUT/'controlled_renderer_payloads.json').write_text(json.dumps(dict(
    input=row['player'],handler='deterministic_provider_skip_line / controlled preview',
    expected_resolution=before['resolution'],actual_resolution=row['resolution'],
    starting_fixture=before,selected_engine_line=selected,authorized_view=asdict(view),
    controlled_outputs=outputs,state_unchanged=row==before,provider_requests=0,
    original_failure_evidence='renderer_before.xml; original exact unexpected payload was not separately captured',
    production_publication='none: offline preview remains unwired'),indent=2),encoding='utf-8')
print('Final controlled payload captured; resolution unchanged; zero provider requests.')
