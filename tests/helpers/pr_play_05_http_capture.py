"""Opt-in offline test evidence; observes responses without changing HTTP calls."""
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def capture_opening_http_response(monkeypatch,request):
    destination=os.environ.get('PR_PLAY_05_HTTP_CAPTURE_DIR')
    if not destination:
        yield
        return
    records=[]
    post=TestClient.post
    def observed(client,url,*args,**kwargs):
        response=post(client,url,*args,**kwargs)
        if str(url)=='/api/start_campaign':
            body=response.json()
            gm=body.get('gm_output') or {}
            records.append({'status':response.status_code,'response':{
                key:body.get(key) for key in ['ok','status','error','opening_failure_reason','campaign_started','gameplay_committed']},
                'gm_output':{'player_facing_text':gm.get('player_facing_text'),
                             'metadata':gm.get('metadata')},
                'session':body.get('session'), 'resolution_kind':(body.get('resolution')or{}).get('kind')})
        return response
    monkeypatch.setattr(TestClient,'post',observed)
    yield
    path=Path(destination)
    path.mkdir(parents=True,exist_ok=True)
    (path/(request.node.name+'.json')).write_text(json.dumps(records,indent=2),encoding='utf-8')
