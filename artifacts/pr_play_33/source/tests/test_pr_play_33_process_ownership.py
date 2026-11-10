"""Offline ownership regressions; never import the historical live controller."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.playtest import runner


@pytest.mark.parametrize('script', [None, Path('observer.py')])
def test_shared_launcher_uses_base_and_preserves_environment(monkeypatch, tmp_path, script):
    captured = {}
    def spawn(command, **kwargs):
        captured.update(command=command, **kwargs)
        return captured
    monkeypatch.setattr(runner.subprocess, 'Popen', spawn)
    env = {'PYTHONPATH': 'custom_packages', 'ASHEN_DISABLE_PROVIDER_CALLS': '1',
           'ASHEN_DATA_DIR': str(tmp_path/'data'), 'ASHEN_PROVIDER_REQUEST_LIMIT': '6'}
    result = runner.start_worker(tmp_path, env, script=script)
    assert result['command'][0] == sys._base_executable
    assert result['command'][1:] == ['-u', *([str(script)] if script else ['-m', 'tools.playtest.worker']), str(tmp_path)]
    assert result['env']['PYTHONPATH'].split(os.pathsep)[0] == str(runner.ROOT)
    assert 'custom_packages' in result['env']['PYTHONPATH'].split(os.pathsep)
    for key in env.keys()-{'PYTHONPATH'}:
        assert result['env'][key] == env[key]
    assert env['PYTHONPATH'] == 'custom_packages'
    for package in (p for p in sys.path if p and 'site-packages' in p):
        assert package in result['env']['PYTHONPATH'].split(os.pathsep)


@pytest.mark.parametrize('base', ['', 'missing-interpreter.exe', None])
def test_missing_expected_interpreter_fails_before_spawn(monkeypatch, tmp_path, base):
    monkeypatch.setattr(sys, '_base_executable', base)
    monkeypatch.setattr(runner.subprocess, 'Popen', lambda *a, **k: pytest.fail('Unsafe fallback'))
    with pytest.raises(FileNotFoundError, match='base interpreter unavailable'):
        runner.start_worker(tmp_path, {})


def test_pr_play_32_calls_shared_launcher_without_executing_live_code():
    tree = ast.parse(Path('artifacts/pr_play_32/execute.py').read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert not any(isinstance(c.func, ast.Attribute) and c.func.attr == 'Popen' for c in calls)
    launch = next(c for c in calls if isinstance(c.func, ast.Attribute) and c.func.attr == 'start_worker')
    assert ast.unparse(launch) == "runner.start_worker(run, env, script=OUT / 'worker_capture.py')"


@pytest.mark.parametrize('shutdown', ['normal', 'terminate', 'timeout', 'startup_failure'])
def test_real_worker_owned_and_reaped(tmp_path, shutdown):
    script = tmp_path/'probe.py'
    report = tmp_path/'pid.json'
    code = ('import os, sys, json, time\nfrom pathlib import Path\n'
            'Path(sys.argv[1], "pid.json").write_text(json.dumps({"pid": os.getpid(), "parent": os.getppid()}))\n')
    code += {'normal': '', 'terminate': 'time.sleep(30)\n', 'timeout': 'time.sleep(30)\n',
             'startup_failure': 'raise SystemExit(2)\n'}[shutdown]
    script.write_text(code)
    process = runner.start_worker(tmp_path, {'SYSTEMROOT': os.environ.get('SYSTEMROOT', ''),
        'ASHEN_DISABLE_PROVIDER_CALLS': '1'}, script=script)
    try:
        if shutdown in {'normal', 'startup_failure'}:
            process.wait(timeout=10)
            assert process.returncode == (2 if shutdown == 'startup_failure' else 0)
        else:
            import time
            deadline = time.monotonic()+10
            while not report.exists() and time.monotonic()<deadline:
                time.sleep(.02)
            if shutdown == 'timeout':
                with pytest.raises(subprocess.TimeoutExpired):
                    process.wait(timeout=.05)
        row = json.loads(report.read_text())
        assert row['pid'] == process.pid and row['parent'] == os.getpid()
    finally:
        cleanup = runner.stop_owned(process, 5)
        process.stdout.close()
    assert cleanup['owned'] and cleanup['stopped'] and process.poll() is not None
    assert runner.stop_owned(process, 5)['stopped']


@pytest.mark.parametrize('alteration', ['pid', 'data_dir', 'isolation_verified'])
def test_ownership_and_isolation_mismatch_never_reach_http(tmp_path, monkeypatch, alteration):
    from types import SimpleNamespace
    (tmp_path/'diagnostics').mkdir()
    row = dict(pid=42, data_dir=str(tmp_path/'data'), isolation_verified=True, port=12345)
    row[alteration] = {'pid': 43, 'data_dir': str(tmp_path/'wrong'), 'isolation_verified': False}[alteration]
    runner.write(tmp_path/'diagnostics/ready.json', row)
    process = SimpleNamespace(pid=42, poll=lambda: None)
    monkeypatch.setattr(runner, 'request', lambda *a: pytest.fail('HTTP before ownership'))
    with pytest.raises(RuntimeError, match='attestation mismatch'):
        runner.wait_for_http_ready(process, tmp_path, 1)


def test_cleanup_escalates_only_owned_handle():
    class Stubborn:
        pid = 42
        returncode = None
        calls = []
        def poll(self): return self.returncode
        def terminate(self): self.calls.append('terminate')
        def kill(self): self.calls.append('kill'); self.returncode = -9
        def wait(self, timeout):
            self.calls.append(('wait', timeout))
            if self.returncode is None:
                raise subprocess.TimeoutExpired('owned', timeout)
    process = Stubborn()
    assert runner.stop_owned(process, .1)['stopped']
    assert process.calls == ['terminate', ('wait', .1), 'kill', ('wait', .1)]
    assert runner.stop_owned(None, .1) == {'owned': False, 'stopped': True}
