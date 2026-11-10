"""Provider-disabled investigation/continuation and deterministic publication."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from game import api
from game import integrated_investigation_narration as integrated
from game import quarantined_investigation_narration as q
from tests.test_pr_play_52_quarantined_integration import _seed,_forbid_provider,_snapshot,_scrub,_facing,_guard_writers
from tests.test_pr_play_57_integrated_narration import ROUTE
from tests.helpers.turn_pipeline_http_fixtures import _gm_response

def test_investigation_then_repeat_preserves_persisted_state(tmp_path,monkeypatch):
    calls=_forbid_provider(monkeypatch)
    # The ordinary follow-up may request wording. Supply a local response at
    # that boundary; the global live-model guard stays installed.
    monkeypatch.setattr(api,'call_gpt',lambda *args,**kwargs:_gm_response('You examine the board again; nothing new is established. '+ROUTE))
    results={}
    original=integrated.run_integrated_hook
    monkeypatch.setattr(integrated,'run_integrated_hook',lambda value:original(value,generator=q._Replay(ROUTE,'')))
    for enabled in (False,True):
        _seed(tmp_path/str(enabled),monkeypatch,'frontier_gate')
        monkeypatch.setenv(q.GATE_ENV,'1' if enabled else '0')
        monkeypatch.setenv(q.MODE_ENV,'integrated')
        monkeypatch.setenv(q.EVIDENCE_ENV,str(tmp_path/'evidence'))
        monkeypatch.delenv(q.LIVE_ENV,raising=False)
        q.clear_evidence();turns=[]
        for text in ('I examine the notice board.','I examine the notice board again.'):
            with TestClient(api.app) as client:
                response=client.post('/api/chat?ui_mode=player',json={'text':text})
                assert response.status_code==200
                body=response.json()
                turns.append({'input':text,'facing':_facing({'body':body}),'state':_scrub(_snapshot())})
        results[str(enabled)]={'turns':turns,'quarantine':q.evidence_records()}
    assert results['False']['turns']==results['True']['turns']
    records=results['True']['quarantine']
    assert len(records)==2 and records[0]['used_fallback'] is False
    assert records[1]['used_fallback'] is True
    assert all(r.get('promoted',False) is False for r in records)
    assert calls['openai']==0
    out=Path(__file__).resolve().parents[1]/'artifacts/pr_play_60/gameplay_sequence.json'
    out.write_text(json.dumps({'scope':'Two-action provider-disabled HTTP comparison, no live narration quality claim.','provider_clients':calls,'results':results},indent=2),encoding='utf-8')
