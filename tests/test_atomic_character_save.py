"""Failure boundaries of the authoritative character writer (isolated files)."""
import json
import os
import stat
import hashlib
from pathlib import Path

import pytest
from game import storage


def evidence(name, value):
    out = os.getenv('ASHEN_TEST_EVIDENCE_DIR')
    if out: (Path(out)/name).write_text(json.dumps(value, indent=2), encoding='utf-8')


@pytest.fixture
def target(tmp_path, monkeypatch):
    path = tmp_path / 'character.json'
    monkeypatch.setattr(storage, 'CHARACTER_PATH', path)
    storage.save_character({'name': 'Old', 'unknown': [1, None]})
    return path


@pytest.mark.parametrize('stage', ['serialization', 'create', 'partial_write', 'flush', 'sync', 'replace'])
def test_precommit_failures_preserve_previous_file(target, monkeypatch, stage):
    before = target.read_bytes()
    def fail(*a, **kw):
        raise OSError('injected ' + stage)
    payload = {'name': 'New'}
    if stage == 'serialization':
        payload['bad'] = object()
    elif stage == 'create':
        monkeypatch.setattr(storage.tempfile, 'mkstemp', fail)
    elif stage in ('partial_write', 'flush'):
        original = storage.os.fdopen
        class BrokenFile:
            def __init__(self, fd, *args, **kw): self.file = original(fd, *args, **kw)
            def __enter__(self): return self
            def __exit__(self, *args): self.file.close()
            def write(self, content):
                if stage == 'partial_write':
                    self.file.write(content[:3]); fail()
                return self.file.write(content)
            def flush(self): fail()
            def fileno(self): return self.file.fileno()
        monkeypatch.setattr(storage.os, 'fdopen', BrokenFile)
    elif stage == 'sync':
        monkeypatch.setattr(storage.os, 'fsync', fail)
    else:
        monkeypatch.setattr(storage.os, 'replace', fail)
    with pytest.raises((OSError, TypeError)):
        storage.save_character(payload)
    assert target.read_bytes() == before
    assert storage.load_character()['name'] == 'Old'
    assert list(target.parent.iterdir()) == [target]
    evidence('atomic_failure_'+stage+'.json', {'stage':stage,'raised':True,
        'before_sha256':hashlib.sha256(before).hexdigest(),
        'after_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'old_character':storage.load_character(),'temporary_files':[], 'replaced':False})


def test_success_replaces_and_reloads_with_mode(target, monkeypatch):
    previous_mode = stat.S_IMODE(target.stat().st_mode)
    replace = storage.os.replace
    seen = []
    def observe(src, dst):
        assert Path(src).parent == target.parent
        assert json.loads(target.read_text())['name'] == 'Old'
        seen.append(json.loads(Path(src).read_text()))
        return replace(src, dst)
    monkeypatch.setattr(storage.os, 'replace', observe)
    payload = {'name': 'New café', 'unknown': {'pf1': [3], 'scifi': [4]}}
    storage.save_character(payload)
    assert seen == [payload] and storage.load_character() == payload
    assert stat.S_IMODE(target.stat().st_mode) == previous_mode
    assert list(target.parent.iterdir()) == [target]
    evidence('atomic_success.json', {'before':{'name':'Old','unknown':[1,None]},
        'reloaded':storage.load_character(),'replacement_payloads':seen,
        'permission_mode_preserved':True,'same_directory':True,'temporary_files':[]})


def test_directory_sync_failure_is_committed_with_reduced_durability(target, monkeypatch):
    monkeypatch.setattr(storage, '_sync_directory', lambda path: False)
    outcome = storage._atomic_write_bytes(target, b'{"name": "New"}')
    assert outcome is False
    assert storage.load_character() == {'name': 'New'}
    assert list(target.parent.iterdir()) == [target]


def test_directory_sync_reports_platform_support(tmp_path):
    supported = storage._sync_directory(tmp_path)
    assert type(supported) is bool
    if os.name == 'nt': assert supported is False


def test_invalid_destination_is_rejected_before_temp_creation(target):
    with pytest.raises((OSError, ValueError)):
        storage._atomic_write_bytes(target.parent, b'no')
    assert storage.load_character()['name'] == 'Old'


@pytest.mark.parametrize('stage', ['open_directory', 'sync_directory'])
def test_real_post_replace_directory_failures_do_not_undo_commit(target, monkeypatch, stage):
    from types import SimpleNamespace
    # Exercise POSIX directory-sync failures without changing the host platform.
    monkeypatch.setattr(storage, 'os', SimpleNamespace(**{**vars(os), 'name':'posix'}))
    original_open, original_sync = storage.os.open, storage.os.fsync
    directory_fds = set()
    def fake_open(path, flags, *args, **kw):
        if path == target.parent:
            if stage == 'open_directory': raise OSError('directory open unavailable')
            # Use a file descriptor on Windows to exercise the fsync error branch.
            fd = original_open(target, os.O_RDONLY); directory_fds.add(fd); return fd
        return original_open(path, flags, *args, **kw)
    def fake_sync(fd):
        if fd in directory_fds: raise OSError('directory sync unavailable')
        return original_sync(fd)
    monkeypatch.setattr(storage.os, 'open', fake_open)
    monkeypatch.setattr(storage.os, 'fsync', fake_sync)
    assert storage._atomic_write_bytes(target, b'{"name":"Committed"}') is False
    assert storage.load_character()['name'] == 'Committed'
    evidence('atomic_postcommit_'+stage+'.json', {'stage':stage,'replaced':True,
        'directory_synchronized':False,'committed_character':storage.load_character()})


def test_readonly_permission_failure_cleans_temp_and_preserves_original(target, monkeypatch):
    before = target.read_bytes(); mode = target.stat().st_mode
    target.chmod(stat.S_IREAD)
    def denied(*args): raise PermissionError('replacement denied')
    monkeypatch.setattr(storage.os,'replace',denied)
    try:
        with pytest.raises(PermissionError): storage.save_character({'name':'New'})
        assert target.read_bytes() == before
        assert list(target.parent.iterdir()) == [target]
    finally:
        target.chmod(mode)
