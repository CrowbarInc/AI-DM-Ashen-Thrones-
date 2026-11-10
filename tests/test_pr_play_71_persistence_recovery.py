"""Fault injection at the observed Windows rename boundary; never replay a turn."""
import errno,os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from game import api,storage
from tests.test_pr_play_71_lifecycle import configure,create,start

def denied(code=5):
    exc=PermissionError(errno.EACCES,'injected temporary Windows file lock')
    exc.winerror=code
    return exc

@pytest.mark.parametrize('failures',[1,2,3])
def test_atomic_replace_transient_lock(tmp_path,monkeypatch,failures):
    target=tmp_path/'session.json';target.write_bytes(b'prior')
    original=os.replace;calls=[]
    def replace(src,dst):
        calls.append((src,dst))
        if len(calls)<=failures:raise denied()
        return original(src,dst)
    monkeypatch.setattr(storage.os,'replace',replace)
    storage._atomic_write_bytes(target,b'next')
    assert target.read_bytes()==b'next' and len(calls)==failures+1
    assert len({str(src) for src,dst in calls})==1
    assert not list(tmp_path.glob('*.tmp.*'))

@pytest.mark.parametrize('code',[5,32,13])
def test_atomic_replace_persistent_failure_is_bounded(tmp_path,monkeypatch,code):
    target=tmp_path/'session.json';target.write_bytes(b'prior');calls=[]
    def replace(*args):calls.append(args);raise denied(code)
    monkeypatch.setattr(storage.os,'replace',replace)
    with pytest.raises(PermissionError):storage._atomic_write_bytes(target,b'next')
    assert target.read_bytes()==b'prior'
    assert len(calls)==(4 if code==5 else 1)
    assert not list(tmp_path.glob('*.tmp.*'))

def test_new_campaign_failure_restores_prior_runtime(tmp_path,monkeypatch):
    configure(tmp_path,monkeypatch)
    with TestClient(api.app,raise_server_exceptions=False) as cl:
        identity=create(cl);start(cl)
        paths=[storage.SESSION_PATH,storage.WORLD_PATH,storage.COMBAT_PATH,storage.SESSION_LOG_PATH]
        before={p:p.read_bytes() for p in paths}
        original=storage._atomic_write_bytes
        def fail_log(path,data):
            if path==storage.SESSION_LOG_PATH:raise denied()
            return original(path,data)
        monkeypatch.setattr(storage,'_atomic_write_bytes',fail_log)
        r=cl.post('/api/new_campaign')
        assert r.status_code==500 and 'Windows file lock' not in r.text
        assert all(p.read_bytes()==raw for p,raw in before.items())
        assert storage.load_session()['campaign_run_id']==identity

def test_publication_transient_session_rename_resolves_once(tmp_path,monkeypatch):
    from tests.test_pr_play_66_publication import setup
    setup(tmp_path,monkeypatch)
    from game import integrated_investigation_narration as integrated,quarantined_investigation_narration as q
    hook=integrated.run_integrated_hook
    monkeypatch.setattr(integrated,'run_integrated_hook',lambda h,**kw:hook(h,generator=q._Replay('The gate is permanently open.','')))
    original=os.replace;attempts=[];successful=[]
    def replace(src,dst):
        if Path(dst)==storage.SESSION_PATH:
            attempts.append(src)
            if len(attempts)==1:raise denied()
        result=original(src,dst);successful.append(str(dst));return result
    monkeypatch.setattr(storage.os,'replace',replace)
    before=storage.load_session().get('turn_counter',0)
    with TestClient(api.app) as cl:r=cl.post('/api/chat',json={'text':'I examine the weathered milestone.'})
    from tests.test_pr_play_52_quarantined_integration import PRINT_CLUE
    assert r.status_code==200 and PRINT_CLUE in r.json()['gm_output']['player_facing_text']
    assert 'permanently open' not in r.text
    assert storage.load_session()['turn_counter']==before+1
    assert attempts[0]==attempts[1]
