"""Faults at the existing transaction owner for dynamic NPC writes."""
import json
import pytest
from fastapi.testclient import TestClient
from game import api,storage,bounded_improvisation as b
from tests.test_pr_play_71_lifecycle import configure,create,start,chat
from tests.test_pr_play_75_dynamic_npcs import enable,proposal

@pytest.mark.parametrize('stage',['creation','conversation'])
def test_npc_failed_commit_rolls_back(tmp_path,monkeypatch,stage):
    configure(tmp_path,monkeypatch);enable(monkeypatch);monkeypatch.delenv('ASHEN_EXPERIMENTAL_BRANCHING_SESSION',raising=False)
    original_provider=b.provider_npc_proposal
    monkeypatch.setattr(b,'provider_npc_proposal',lambda **kw:original_provider(**kw,invoke=lambda *a:proposal(kw['session'],kw['scene'])))
    with TestClient(api.app,raise_server_exceptions=False) as cl:
        create(cl);start(cl)
        if stage=='conversation':chat(cl,'Introduce an ordinary traveler to speak with.')
        paths=[storage.SESSION_PATH,storage.WORLD_PATH,storage.COMBAT_PATH,storage.SESSION_LOG_PATH]
        before={p:p.read_bytes() for p in paths};write=storage._atomic_write_bytes
        def fail(path,content):
            if path==storage.SESSION_PATH and content!=before[path]:raise PermissionError('injected NPC commit fault')
            return write(path,content)
        monkeypatch.setattr(storage,'_atomic_write_bytes',fail)
        out=cl.post('/api/chat',json={'text':'Who are you?' if stage=='conversation' else 'Introduce an ordinary traveler to speak with.'})
        assert out.status_code==500
        assert 'Mara' not in out.text and 'injected' not in out.text
        assert all(p.read_bytes()==v for p,v in before.items())


def test_npc_focus_does_not_mutate_player_inquiry(tmp_path,monkeypatch):
    configure(tmp_path,monkeypatch);enable(monkeypatch);monkeypatch.delenv('ASHEN_EXPERIMENTAL_BRANCHING_SESSION',raising=False)
    original=b.provider_npc_proposal
    monkeypatch.setattr(b,'provider_npc_proposal',lambda **kw:original(**kw,invoke=lambda *a:proposal(kw['session'],kw['scene'])))
    with TestClient(api.app) as cl:
        create(cl);start(cl);chat(cl,'Introduce an ordinary traveler to speak with.')
        before=storage.load_session();world=storage.load_world()
        chat(cl,'What do I know about this area?')
        assert storage.load_session()==before and storage.load_world()==world


def test_name_substring_does_not_create_reference(monkeypatch):
    from tests.test_pr_play_75_dynamic_npcs import context
    enable(monkeypatch);session,scene,world=context();p=proposal();p['name']='Eli'
    npc=b.validate_npc_proposal(p,session=session,scene=scene,world=world)['entry']
    session[b.LEDGER_KEY]={'entries':[npc], 'npc_focus':npc['id']}
    assert b.npc_request('I believe the water is cold.',session=session,scene=scene,world=world) is None
