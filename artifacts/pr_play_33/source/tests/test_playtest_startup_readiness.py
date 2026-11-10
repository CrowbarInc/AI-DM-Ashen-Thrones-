"""Offline regressions for the observed startup visibility boundary."""
import errno
import json
from types import SimpleNamespace
from urllib.error import URLError

import pytest

from tools.playtest import runner


@pytest.fixture
def startup(tmp_path, monkeypatch):
    (tmp_path/'diagnostics').mkdir()
    process = SimpleNamespace(pid=42, returncode=None, poll=lambda: None)
    runner.write(tmp_path/'diagnostics/ready.json', {
        'pid': 42, 'port': 12345, 'data_dir': str(tmp_path/'data'), 'isolation_verified': True})
    clock = [0.0]
    monkeypatch.setattr(runner.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds: clock.__setitem__(0, clock[0]+seconds))
    return tmp_path, process


def events(run):
    return [json.loads(line) for line in (run/'diagnostics/readiness_poll.jsonl').read_text().splitlines()]


def test_configuration_is_not_http_ready(startup, monkeypatch):
    run, process = startup
    responses = iter([(503, {}), (200, {})])
    monkeypatch.setattr(runner, 'request', lambda *args: next(responses))
    ready, base = runner.wait_for_http_ready(process, run, 1)
    assert ready['pid'] == process.pid and base == 'http://127.0.0.1:12345'
    assert [e['status'] for e in events(run) if 'status' in e] == [503, 200]
    assert json.loads((run/'diagnostics/http_ready.json').read_text())['status'] == 200


@pytest.mark.parametrize('exception,event', [
    (URLError(PermissionError(errno.EACCES, 'private text')), 'access_denied'),
    (URLError(ConnectionRefusedError(errno.ECONNREFUSED, 'private text')), 'connection_refused'),
    (URLError(TimeoutError('private text')), 'request_timeout'),
    (ValueError('private text'), 'invalid_response'),
])
def test_transport_failure_is_preserved_safely(startup, monkeypatch, exception, event):
    run, process = startup
    def fail(*args):
        raise exception
    monkeypatch.setattr(runner, 'request', fail)
    with pytest.raises(PermissionError if event == 'access_denied' else TimeoutError):
        runner.wait_for_http_ready(process, run, .1)
    assert event in [e['event'] for e in events(run)]
    assert 'private text' not in (run/'diagnostics/readiness_poll.jsonl').read_text()
    assert not (run/'diagnostics/http_ready.json').exists()
    if event == 'access_denied':
        assert events(run)[-1]['elapsed_seconds'] == 0


def test_exit_is_detected_before_poll(startup, monkeypatch):
    run, process = startup
    process.returncode = 2
    process.poll = lambda: 2
    monkeypatch.setattr(runner, 'request', lambda *args: pytest.fail('HTTP after exit'))
    with pytest.raises(RuntimeError, match='exited'):
        runner.wait_for_http_ready(process, run, 1)
    assert events(run)[-1]['exit_code'] == 2


def test_stale_attestation_rejected(startup, monkeypatch):
    run, process = startup
    process.pid = 43
    monkeypatch.setattr(runner, 'request', lambda *args: pytest.fail('HTTP with stale PID'))
    with pytest.raises(RuntimeError, match='attestation mismatch'):
        runner.wait_for_http_ready(process, run, 1)
    assert events(run)[-1]['event'] == 'attestation_mismatch'


def test_no_attestation_deadline(startup):
    run, process = startup
    (run/'diagnostics/ready.json').unlink()
    with pytest.raises(TimeoutError):
        runner.wait_for_http_ready(process, run, .1)
    assert events(run)[-1]['event'] == 'readiness_deadline_expired'


def test_late_http_success_does_not_beat_deadline(startup, monkeypatch):
    run, process = startup
    def late(*args):
        runner.time.sleep(.2)
        return 200, {}
    monkeypatch.setattr(runner, 'request', late)
    with pytest.raises(TimeoutError):
        runner.wait_for_http_ready(process, run, .1)
    assert not (run/'diagnostics/http_ready.json').exists()


def test_transient_attestation_read_retried(startup, monkeypatch):
    run, process = startup
    (run/'diagnostics/ready.json').write_text('{')
    original_sleep = runner.time.sleep
    def repair(seconds):
        original_sleep(seconds)
        runner.write(run/'diagnostics/ready.json', {
            'pid': 42, 'port': 12345, 'data_dir': str(run/'data'), 'isolation_verified': True})
    monkeypatch.setattr(runner.time, 'sleep', repair)
    monkeypatch.setattr(runner, 'request', lambda *args: (200, {}))
    runner.wait_for_http_ready(process, run, 1)
    assert events(run)[1]['event'] == 'attestation_unavailable'
