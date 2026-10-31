"""Offline PR-PLAY-03 host reproduction. Synthetic SDK responses; no network."""
from pathlib import Path
import os, sys, json, socket, copy, uuid, subprocess, shutil
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if len(sys.argv)==1:
    for case in ['valid_structured','rich_structured_rejected','missing_envelope','historical_seed_missing','provider_exception','pipeline_exception']:
        subprocess.run([sys.executable,__file__,case],check=True)
    merged=[json.loads((ROOT/f'artifacts/pr_play_03/{case}_output.json').read_text()) for case in ['valid_structured','rich_structured_rejected','missing_envelope','historical_seed_missing','provider_exception','pipeline_exception']]
    (ROOT/'artifacts/pr_play_03/reproduction_outputs.json').write_text(json.dumps(merged,indent=2))
    sys.exit(0)
sys.path.insert(0, str(ROOT))
os.environ['ASHEN_DISABLE_PROVIDER_RETRIES'] = '1'
os.environ['ASHEN_PLAYTEST_DISABLE_SDK_RETRIES'] = '1'
os.environ['ASHEN_DISABLE_PROVIDER_CALLS'] = '0'  # SDK constructor replaced below
os.environ['ASHEN_DATA_DIR'] = str(ROOT/'development/tmp/pr_play_03/import_data')
os.environ['ASHEN_PROVIDER_USAGE_PATH'] = str(ROOT/f'development/tmp/pr_play_03/mock_usage_{uuid.uuid4().hex}.jsonl')
for key in ['ASHEN_PROVIDER_REQUEST_LIMIT','ASHEN_PROVIDER_INPUT_TOKEN_LIMIT','ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT','ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT']:
    os.environ.pop(key, None)

def denied(*a, **k):
    raise AssertionError('Network forbidden in offline reproduction')

with patch.object(socket.socket, 'connect', denied), patch.object(socket, 'getaddrinfo', denied):
    import pytest
    from starlette.requests import Request
    import game.api as api
    import game.gm as gm
    import game.storage as st
    from tests.helpers.turn_pipeline_http_fixtures import _seed_campaign_start_storage
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE

    outdir = ROOT/'artifacts/pr_play_03'
    captures=[]
    results=[]
    current={}
    def create(**kwargs):
        captures.append({'case': current['case'], 'kwargs': kwargs})
        if current['case']=='provider_exception':
            raise RuntimeError('synthetic SDK operation failure')
        text = current['text']
        return SimpleNamespace(output_text=text, model='offline-stub', id='synthetic-response',
                               usage=SimpleNamespace(input_tokens=100,output_tokens=40,total_tokens=140),
                               status='completed')
    def ctor(**kwargs):
        assert kwargs.get('max_retries') == 0
        return SimpleNamespace(responses=SimpleNamespace(create=create))
    def req():
        return Request({'type':'http','method':'POST','path':'/api/start_campaign',
                        'headers':[], 'query_string':b'ui_mode=player'})
    def decode(response):
        return json.loads(response.body) if hasattr(response,'body') else response
    def snap():
        s=st.load_session();w=st.load_world()
        return {'campaign_started':s.get('campaign_started'),'turn_counter':s.get('turn_counter'),
                'clocks':s.get('clocks'),'active_scene_id':s.get('active_scene_id'),
                'world':copy.deepcopy(w),'log_length':len(st.load_log()),
                'campaign_can_start': api._session_allows_structured_start_campaign(s,st.load_log())}
    for case in [sys.argv[1]]:
        mp=pytest.MonkeyPatch()
        current['case']=case
        valid_text = "You stand at Cinderwatch's eastern gate. Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. A tavern runner shouts offers of hot stew and paid rumor. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. You can read the notice board, approach the tavern runner, or watch the crowd."
        current['text']=json.dumps({'declared_claims':[],'narration':valid_text if case=='valid_structured' else RICH_OPENING_GPT_RESPONSE['player_facing_text']}) if case in ['valid_structured','rich_structured_rejected'] else 'You stand beside the gate in the rain.'
        base=ROOT/'development/tmp/pr_play_03'/case
        _seed_campaign_start_storage(base,mp)
        if case=='historical_seed_missing':
            seed=ROOT/'data/validation/atgb/baselines/frontier-gate-v1'
            for name in ['campaign.json','character.json','conditions.json','world.json']:
                shutil.copyfile(seed/name,st.DATA_DIR/name)
            shutil.copytree(seed/'scenes',st.SCENES_DIR,dirs_exist_ok=True)
        mp.setattr(api,'_compute_upstream_gate_for_live_gameplay',lambda: ({'manual_testing_blocked':False},{}))
        mp.setattr(gm,'get_openai_api_key',lambda:'offline-placeholder')
        import openai
        mp.setattr(openai,'OpenAI',ctor)
        record={'case':case,'classification':'synthetic_positive_control' if case=='valid_structured' else 'synthetic_negative_control',
                'input':current['text'] if case not in ['provider_exception','pipeline_exception'] else case,
                'http_transport_exercised':False,'network_forbidden':True}
        try:
            record['new_campaign']=decode(api.new_campaign(req())).get('ok')
            record['before']=snap()
            before_calls=len(captures)
            if case=='pipeline_exception':
                mp.setattr(api,'_run_resolved_turn_pipeline',lambda **k: (_ for _ in ()).throw(RuntimeError('synthetic pipeline failure')))
            try:
                response=api.start_campaign(req());body=decode(response)
                record['response']=body
                record['status_code']=getattr(response,'status_code',200)
            except Exception as e:
                record['raised']={'type':type(e).__name__,'message':str(e)}
            record['after']=snap()
            record['sdk_mock_calls']=len(captures)-before_calls
            if case!='pipeline_exception':
                second=api.start_campaign(req());record['repeated_start']={'status_code':getattr(second,'status_code',200),'body':decode(second),'state':snap(),'calls_after':len(captures)-before_calls}
            else:
                try:api.start_campaign(req())
                except RuntimeError:pass
                record['repeated_pipeline_failure']=snap()
            record['log']=st.load_log()
        finally:
            mp.undo()
        results.append(record)
    (outdir/f'{sys.argv[1]}_output.json').write_text(json.dumps(results[0],indent=2,default=str),encoding='utf-8')
    (outdir/f'{sys.argv[1]}_requests.json').write_text(json.dumps(captures,indent=2),encoding='utf-8')
    print(json.dumps([{'case':r['case'],'status':r.get('status_code'),'raised':r.get('raised'),
          'text':(r.get('response',{}).get('gm_output') or {}).get('player_facing_text'),
          'sdk_mock_calls':r['sdk_mock_calls'],
          'before':{k:v for k,v in r['before'].items() if k!='world'},
          'after':{k:v for k,v in r['after'].items() if k!='world'},
          'repeat_status':r.get('repeated_start',{}).get('status_code')} for r in results],indent=2))
