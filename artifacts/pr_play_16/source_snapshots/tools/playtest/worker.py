"""Owned server process. Imported only after the controller prepares isolation."""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as NS


def write(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)


NARRATION = (
    "You stand at Cinderwatch's eastern gate. Rain spatters soot-dark stone; frayed banners hang "
    "above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; "
    "guards hold the choke while the crowd presses in. A tavern runner shouts offers of hot stew and "
    "paid rumor. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. "
    "You can read the notice board, approach the tavern runner, or watch the crowd."
)


CURRENT_TURN = 0


def gameplay_fixture(turn, interpretation):
    """Synthetic SDK output only. The normal host validates and resolves it."""
    if not interpretation:
        lines = {1: 'Rain falls over the gate district and the crowded muddy approach.',
                 2: 'The gate serjeant says, "The patrol route changed after the Ash Compact census choke worsened."',
                 3: 'The notice board lists taxes, curfew rules, and a warning about a missing patrol.',
                 4: 'You can examine the notice board or ask the gate serjeant about the missing patrol.',
                 5: 'You approach the gate to enter Cinderwatch.'}
        return json.dumps({'declared_claims': [], 'narration': lines[turn]})
    operation, target = {1: (None, None), 2: ('ASK', 'gate_serjeant'), 3: ('INSPECT', 'notice_board'),
                         4: (None, None), 5: ('MOVE', 'market_quarter')}[turn]
    return json.dumps({
        'communication_mode': 'IN_WORLD_ACTION' if operation else 'OTHER', 'interpretation_status': 'INTERPRETED',
        'player_intent': {'summary': {1: 'Look around the gate district', 2: 'Ask gate serjeant about missing patrol',
                          3: 'Inspect notice board', 4: 'Ask for available missing patrol leads', 5: 'Enter Cinderwatch'}[turn]},
        'asserted_premises': [], 'requested_outcomes': [],
        'action_components': [{'order': 1, 'operation_class': operation, 'target_ref': target,
                               'description': 'Attempt the requested interaction'}] if operation else [],
        'references': {'permitted_entity_ids': [target] if target else [], 'unresolved_references': []},
        'clarification_question': '', 'correction': {'subject': 'NONE', 'note': ''},
        'communication': {'recipient': 'NPC' if turn == 2 else 'CHARACTER' if operation else 'GM',
                          'purpose': 'QUESTION' if turn == 2 else 'ACTION' if operation else 'DESCRIPTION',
                          'subject': 'missing patrol' if turn in (2, 4) else 'surroundings',
                          'evidence_refs': ['visible:0', 'visible:1'] if not operation else []}})


def install_transport(case, gameplay=False):
    import openai
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def local_only(self, address):
        if not isinstance(address, tuple) or address[0] not in {'127.0.0.1', '::1', 'localhost'}:
            raise RuntimeError('Deterministic external network access refused')
        return real_connect(self, address)

    def local_ex(self, address):
        if not isinstance(address, tuple) or address[0] not in {'127.0.0.1', '::1', 'localhost'}:
            raise RuntimeError('Deterministic external network access refused')
        return real_connect_ex(self, address)

    socket.socket.connect = local_only
    socket.socket.connect_ex = local_ex
    text = json.dumps({'declared_claims': [], 'narration': NARRATION})
    text = {
        'invalid_json': '{broken', 'envelope': '{"ordinary": true}', 'empty': '',
        'safe_nonresolution': json.dumps({'declared_claims': [], 'narration': 'No one here can answer that from what is settled here.'}),
        'semantic': json.dumps({'declared_claims': [], 'narration': NARRATION + ' The guards give you a brass key and you gain 100 gold.'}),
        'truncation': '{"declared_claims": [], "narration": "You stand',
    }.get(case, text)
    if case == 'authored_overlay':
        # Unmodified parsed response captured in PR-PLAY-09. Only the SDK
        # transport is stubbed; all production validators and persistence run.
        text = (Path(__file__).resolve().parents[2]/'tests/fixtures/pr_play_10/historical_opening.json').read_text(encoding='utf-8')

    def create(**kwargs):
        if case == 'exception' or (case == 'turn2_exception' and CURRENT_TURN == 2):
            raise RuntimeError('Synthetic provider exception')
        content = gameplay_fixture(CURRENT_TURN, (kwargs.get('text', {}).get('format', {}).get('name') == 'pr_dr_interpretation')) if gameplay and CURRENT_TURN else text
        if case == 'success' and not (gameplay and CURRENT_TURN):
            from game.opening_presentation_renderer import opening_renderer_mode, plan_selecting_required

            if opening_renderer_mode() == 'enabled':
                planned = plan_selecting_required(kwargs.get('input'))
                if planned:
                    content = planned
        if case == 'turn3_invalid_json' and CURRENT_TURN == 3:
            content = '{broken'
        value = NS(output_text=content, id='synthetic-response', model=kwargs['model'],
                   status='completed', usage=NS(input_tokens=20, output_tokens=10, total_tokens=30))
        if case == 'truncation':
            value.status = 'incomplete'
            value.incomplete_details = NS(reason='max_output_tokens')
        if case == 'incomplete':
            value.status = 'incomplete'
            value.incomplete_details = NS(reason='synthetic_incomplete')
        return value

    def constructor(**kwargs):
        if kwargs.get('max_retries') != 0:
            raise RuntimeError('SDK retry guard missing')
        return NS(responses=NS(create=create))

    openai.OpenAI = constructor
    def forbidden(*args, **kwargs):
        raise RuntimeError('Async provider not supported in deterministic playtest')
    openai.AsyncOpenAI = forbidden


def main():
    run = Path(sys.argv[1]).resolve()
    cfg = json.loads((run/'configuration/run.json').read_text(encoding='utf-8'))
    diagnostics = run/'diagnostics'
    def stage(name):
        with (diagnostics/'startup_events.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'event': name, 'time': datetime.now(timezone.utc).isoformat(),
                                     'monotonic': time.monotonic(), 'pid': os.getpid()})+'\n')
    import faulthandler
    stack_log = (diagnostics/'startup_stack.log').open('w', encoding='utf-8')
    faulthandler.dump_traceback_later(8, file=stack_log)
    stage('worker_started')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind before readiness; an occupied port is never reused or terminated.
    stage('socket_binding')
    sock.bind(('127.0.0.1', cfg['port']))
    sock.listen(128)
    stage('socket_listening')
    from game import storage as st
    from tools.atgb.isolation import assert_imported_data_dir
    assert_imported_data_dir(st.DATA_DIR, run/'data', player_campaign_dir=Path(cfg['player_data']))
    if cfg['mode'] != 'Live':
        os.environ['OPENAI_API_KEY'] = 'offline-placeholder'
        install_transport(cfg['fixture_response'], cfg['scenario_id'] == 'FiveTurnGameplay')
    from game import api, gm, provider_budget as budget
    from game.config import get_openai_api_key, DEFAULT_MODEL_NAME
    from game.opening_presentation_renderer import opening_renderer_diagnostics
    if cfg['mode'] == 'Live':
        # Existence check only. Never dispatch connectivity probes.
        if not get_openai_api_key().strip() or budget.provider_calls_disabled():
            raise RuntimeError('Live credentials or provider enablement missing')
    if budget.sdk_retry_options() != {'max_retries': 0} or not budget.provider_retries_disabled():
        raise RuntimeError('Retry suppression missing')
    budget.initialize_accounting()
    # A fresh cache + explicit skipped startup leaves the ordinary gate unblocked.
    # Refuse any unexpected direct probe instead of silently spending an admission.
    def no_probe(*args, **kwargs):
        raise RuntimeError('Connectivity diagnostics forbidden by harness')
    api.run_upstream_api_preflight = no_probe
    import game.api_upstream_preflight as preflight
    preflight.run_upstream_api_preflight = no_probe
    if api._compute_upstream_gate_for_live_gameplay()[0].get('manual_testing_blocked'):
        raise RuntimeError('Existing upstream gate blocked this run')
    write(diagnostics/'ready.json', {'pid': os.getpid(), 'port': sock.getsockname()[1],
          'phase': 'configuration_initialized', 'time': datetime.now(timezone.utc).isoformat(),
          'data_dir': str(st.DATA_DIR), 'isolation_verified': True,
          'model': DEFAULT_MODEL_NAME, 'opening_output_allowance': gm._opening_max_output_tokens(),
          'opening_renderer': opening_renderer_diagnostics(),
          'limits': budget.limits(), 'sdk_retries': 0, 'host_retries': 0,
          'diagnostics_enabled': budget.generation_diagnostics_enabled(),
          'credentials_present': cfg['mode'] == 'Live', 'connectivity_diagnostics': False})

    async def application(scope, receive, send):
        global CURRENT_TURN
        async def observed_send(message):
            if message['type'] in {'lifespan.startup.complete', 'lifespan.startup.failed'}:
                stage(message['type'])
            await send(message)
        if scope['type'] == 'lifespan':
            stage('application_initializing')
        if scope['type'] == 'http' and scope.get('path') == '/api/chat':
            CURRENT_TURN += 1
        if scope['type'] == 'http':
            faulthandler.cancel_dump_traceback_later()
        try:
            await api.app(scope, receive, observed_send)
        finally:
            if scope['type'] == 'http':
                write(diagnostics/'budget_snapshot.json', budget.snapshot())

    stage('configuration_initialized')
    import uvicorn
    stage('uvicorn_imported')
    try:
        stage('server_run_entered')
        uvicorn.Server(uvicorn.Config(application, log_level='info', access_log=False)).run(sockets=[sock])
    finally:
        faulthandler.cancel_dump_traceback_later()
        stack_log.close()
        write(diagnostics/'budget_snapshot.json', budget.snapshot())
        sock.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Exception messages can contain provider/private text. Record the type only.
        run = Path(sys.argv[1])
        events = run/'diagnostics/startup_events.jsonl'
        last_stage = json.loads(events.read_text(encoding='utf-8').splitlines()[-1])['event'] if events.exists() else 'worker_bootstrap'
        write(run/'diagnostics/worker_failure.json', {'type': type(exc).__name__, 'stage': last_stage,
              'os_error': getattr(exc, 'winerror', None) or getattr(exc, 'errno', None)})
        raise SystemExit(2)
