"""Inspection controls; do not change the existing rich-emission contracts."""
import copy
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
import game.api as api
import game.immutable_valid_response as immutable
import game.storage as storage
from tests.helpers.turn_pipeline_http_fixtures import _seed_campaign_start_storage
from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE, SHORT_OPENING_WITH_RICH_UPSTREAM_PREPARED_RESPONSE


@pytest.mark.parametrize('case',['rich','reconcile','prepared'])
def test_capture_emission_boundaries(tmp_path,monkeypatch,case):
    _seed_campaign_start_storage(tmp_path,monkeypatch)
    monkeypatch.setattr(api,'log_upstream_api_preflight_at_startup',lambda:None)
    fixture = copy.deepcopy(SHORT_OPENING_WITH_RICH_UPSTREAM_PREPARED_RESPONSE if case=='prepared' else RICH_OPENING_GPT_RESPONSE)
    monkeypatch.setattr(api,'call_gpt',lambda *_a,**_k:copy.deepcopy(fixture))
    boundaries=[]
    def snapshot(stage,gm):
        meta=gm.get('metadata') or {}
        text=gm.get('player_facing_text') or ''
        boundaries.append({'stage':stage,'text':text,'length':len(text),
                           'accepted':copy.deepcopy(meta.get('accepted_response')),
                           'debug':copy.deepcopy(meta.get('emission_debug')),
                           'rejected':copy.deepcopy(meta.get('rejected_candidate'))})
    real=immutable.run_preserve_if_valid
    def preserve(gm,*args,**kwargs):
        snapshot('before_acceptance',gm)
        result=real(gm,*args,**kwargs)
        snapshot('after_acceptance',result)
        return result
    monkeypatch.setattr(immutable,'run_preserve_if_valid',preserve)
    finalize=api._finalize_player_facing_for_turn
    def final(gm,**kwargs):
        snapshot('before_final_emission',gm)
        result=finalize(gm,**kwargs)
        snapshot('after_final_emission',result[0])
        return result
    monkeypatch.setattr(api,'_finalize_player_facing_for_turn',final)
    if case=='reconcile':
        import game.api_turn_support as support
        def shorten(**kwargs):
            kwargs['gm_output']['player_facing_text']='You stand at the gate. Rain falls.'
            return {'mismatch_kind':'synthetic_summary'}
        monkeypatch.setattr(support,'reconcile_final_text_with_structured_state',shorten)
    with TestClient(api.app) as client:
        assert client.post('/api/new_campaign').status_code==200
        response=client.post('/api/start_campaign')
        assert response.status_code==200
    snapshot('response',response.json()['gm_output'])
    snapshot('persisted',storage.load_log()[0]['gm_output'])
    out=Path(os.environ.get('PR_PLAY_05_EMISSION_OUT','artifacts/pr_play_05/emission'))
    out.mkdir(parents=True,exist_ok=True)
    (out/(case+'.json')).write_text(json.dumps({'fixture':fixture,'boundaries':boundaries},indent=2))
