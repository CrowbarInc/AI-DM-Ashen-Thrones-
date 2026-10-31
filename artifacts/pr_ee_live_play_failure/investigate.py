"""PR-EE diagnostic runner. No production source edits; all API writes isolated.

Run with .venv/Scripts/python.exe artifacts/pr_ee_live_play_failure/investigate.py
or add --live for bounded fresh provider probes. No lifespan/startup preflight.
"""
from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
LIVE = '--live' in sys.argv

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding='utf-8')

def hashes():
    paths = list((ROOT / 'data').glob('*.json*')) + list((ROOT / 'data/scenes').glob('*.json'))
    paths += list((ROOT / 'game').rglob('*.py')) + list((ROOT / 'static').rglob('*.*'))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}

before_hashes = hashes()
original = [json.loads(line) for line in (ROOT / 'data/session_log.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
if not LIVE:
    dump('original_session_log.json', original)
    dump('original_session.json', json.loads((ROOT / 'data/session.json').read_text(encoding='utf-8')))
    dump('production_hashes_before.json', before_hashes)
    for name in ('CURRENT_REVIEW.md', 'REVIEW_MANIFEST.json', 'CURRENT_REVIEW.zip'):
        target = OUT / 'predecessor_handoff' / name
        target.parent.mkdir(exist_ok=True)
        if not target.exists():
            shutil.copy2(ROOT / 'handoff' / name, target)

tmp = Path(tempfile.mkdtemp(prefix='pr_ee_', dir=OUT))
data = tmp / 'data'
data.mkdir()
for p in (ROOT / 'data').glob('*.json*'):
    shutil.copy2(p, data / p.name)
shutil.copytree(ROOT / 'data/scenes', data / 'scenes')
os.environ['ASHEN_DATA_DIR'] = str(data)
os.environ['ASHEN_DISABLE_PROVIDER_CALLS'] = '0'
os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION'] = '0'
os.environ['ASHEN_PROVIDER_REQUEST_LIMIT'] = '16'
os.environ['ASHEN_PROVIDER_INPUT_TOKEN_LIMIT'] = '150000'
os.environ['ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT'] = '20000'
os.environ['ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT'] = '170000'
os.environ['ASHEN_PROVIDER_USAGE_PATH'] = str(OUT / ('live_usage.jsonl' if LIVE else 'replay_usage.jsonl'))

from game import storage
from game import api
from game import live_chat_interpretation as interp
from game.campaign_state import create_fresh_session_document
from game.config import DEFAULT_MODEL_NAME, HIGH_PRECISION_MODEL_NAME, ENABLE_MODEL_ROUTING
from fastapi.testclient import TestClient

assert storage.DATA_DIR == data
client = TestClient(api.app)
base_session = create_fresh_session_document()
base_world = storage.load_world()
base_combat = storage.load_combat()

def reset(log=None):
    storage.save_session(copy.deepcopy(base_session))
    storage.save_world(copy.deepcopy(base_world))
    storage.save_combat(copy.deepcopy(base_combat))
    storage.clear_log()
    for row in log or []:
        storage.append_log(copy.deepcopy(row))

requests = []
real_request = interp.request_interpretation
replay_current = None

def capture_request(messages, **kwargs):
    request = {'messages': messages, 'kwargs': kwargs, 'evidence_kind': 'new_live_provider' if LIVE else 'recorded_provider_replay'}
    started = time.perf_counter()
    if LIVE:
        result = real_request(messages, **kwargs)
    else:
        recorded = replay_current['resolution']['metadata']['live_chat_interpretation']
        assert recorded is not None, 'Unexpected interpreter request on deterministic recorded turn'
        result = {'ok': True, 'sent': False, 'text': recorded['raw_interpretation']}
    request['elapsed_ms'] = round((time.perf_counter()-started)*1000, 3)
    request['result'] = result
    requests.append(request)
    return result

interp.request_interpretation = capture_request

def turn(text):
    print('Starting HTTP turn: '+text, flush=True)
    start = time.perf_counter()
    session_before = storage.load_session()
    log_before = storage.load_log()
    offset = len(requests)
    response = client.post('/api/chat?ui_mode=player', json={'text': text, 'ui_mode': 'player'})
    session_after = storage.load_session()
    result = {'input': text, 'http_status': response.status_code, 'elapsed_ms': round((time.perf_counter()-start)*1000, 3),
              'session_before': session_before, 'session_after': session_after,
              'conversation_log_before': log_before, 'interpretation_requests': requests[offset:],
              'response': response.json(), 'changed_session_keys': [k for k in set(session_before)|set(session_after) if session_before.get(k)!=session_after.get(k)],
              'world_unchanged': storage.load_world()==base_world}
    print(json.dumps({'input':text,'status':response.status_code,'response':result['response'].get('gm_output',{}).get('player_facing_text')}), flush=True)
    return result

reset()
sequence = []
for row in original[:6]:
    replay_current = row
    result = turn(row['player_input'])
    result['matches_original_text'] = result['response'].get('gm_output',{}).get('player_facing_text') == row['player_facing_text']
    sequence.append(result)
dump('live_original_inputs.json' if LIVE else 'recorded_output_http_replay.json', sequence)

probes = []
if LIVE:
    for text in ('Can we start playing?', 'Describe the opening scene.', 'What is happening around me?', "I'm speaking to you, the DM.", "Why can't you do that?", 'What should my character do next?'):
        # Each probe has the original rejection context through turn four.
        reset(original[:4])
        probes.append(turn(text))
    dump('live_semantic_probes.json', probes)
else:
    lifecycle = []
    for text in ("I'm ready to begin play!", "I'd like you to start the campaign.", 'Begin.'):
        for nonempty in (False, True):
            s = copy.deepcopy(base_session)
            log = original[:1] if nonempty else []
            lifecycle.append({'input':text, 'log_nonempty':nonempty,
                              'chat_start_cue':api._is_campaign_start_turn_request(text,s,log),
                              'structured_start_available':api._session_allows_structured_start_campaign(s,log)})
    dump('lifecycle_gate_probes.json', lifecycle)
    # A recognized fresh start still encounters live interpretation before the
    # later opening branch. Replay that original provider result on empty log.
    reset()
    replay_current = original[1]
    fresh_start = turn(original[1]['player_input'])
    fresh_start['campaign_start_predicate_before_request'] = True
    dump('recognized_fresh_start_replay.json', fresh_start)
    from game.conversational_orchestration import deterministic_conversational_decision, decision_from_interpretation_record
    diagnostics = []
    rejected_session = sequence[3]['session_after']
    for text in ('Can we start playing?', 'Describe the opening scene.', 'What is happening around me?', "I'm speaking to you, the DM.", "Why can't you do that?", 'What should my character do next?'):
        for label, session, log in (('fresh',base_session,[]), ('after_original_rejection',rejected_session,original[:4])):
            decision = deterministic_conversational_decision(player_text=text,scene=storage.load_active_scene(),world=base_world,session=session,log=log)
            diagnostics.append({'input':text,'context':label,'evidence_kind':'deterministic_router_probe_only',
                                'decision':decision.to_public_dict() if decision else None,
                                'meaning_of_null':'No deterministic decision; provider outcome unavailable, not a failed completed API turn.'})
    dump('semantic_alternatives_static_probes.json', diagnostics)

dump('live_environment.json' if LIVE else 'replay_environment.json', {
    'data_dir': str(storage.DATA_DIR), 'actual_route': '/api/chat?ui_mode=player', 'transport':'FastAPI TestClient, no lifespan startup',
    'provider_mode':'live' if LIVE else 'recorded raw outputs injected at request_interpretation only; real adapter/orchestration/bridge/HTTP/persistence',
    'default_narration_model':DEFAULT_MODEL_NAME,'high_precision_model':HIGH_PRECISION_MODEL_NAME,'model_routing':ENABLE_MODEL_ROUTING,
    'interpreter_model':interp._contract()[4],
    'startup_preflight_run':False, 'baseline_note':'Fresh session from current create_fresh_session_document; copied current bootstrap/world/combat. Not an original pre-turn snapshot.',
    'provider_call_timeout_note':'Current implementation timeout; SDK default retries not overridden.'})
after_hashes = hashes()
dump('live_preservation_check.json' if LIVE else 'replay_preservation_check.json', {'unchanged':before_hashes==after_hashes,
     'changed_paths':[k for k in set(before_hashes)|set(after_hashes) if before_hashes.get(k)!=after_hashes.get(k)]})
assert before_hashes == after_hashes, 'Production files changed during isolated investigation'
