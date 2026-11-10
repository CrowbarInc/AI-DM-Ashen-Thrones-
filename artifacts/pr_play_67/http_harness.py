"""Isolated real TCP evidence; never uses canonical campaign persistence."""
import os, sys, json, time, copy, socket, threading, urllib.request, urllib.error
from contextlib import contextmanager
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
for key in ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT','ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES']: os.environ[key]='1'
import pytest, uvicorn
from game import api, storage
from game import integrated_investigation_narration as integrated, quarantined_investigation_narration as quarantine
from tests.test_pr_play_52_quarantined_integration import _seed, _forbid_provider
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def snapshot(): return {name:getattr(storage,'load_'+name)() for name in ['session','world','character','combat']}
def scan(value):
    text=json.dumps(value)
    return sorted({word for word in text.replace('"',' ').replace('\\',' ').split() if 'CANARY_' in word or 'SENTINEL_' in word})
@contextmanager
def seed(name, enabled=False, scene='frontier_gate'):
    with pytest.MonkeyPatch.context() as mp:
        _forbid_provider(mp); _seed(OUT/name,mp,scene)
        mp.setattr(storage,'SNAPSHOTS_DIR',OUT/name/'snapshots')
        mp.setattr(api,'BASE_DIR',OUT/name)
        mp.setattr(api,'call_gpt',lambda *a,**k:_gm_response('Provider calls are disabled for this run, so no live narration was generated.'))
        mp.setenv(quarantine.GATE_ENV,'1' if enabled else '0');mp.setenv(quarantine.MODE_ENV,'integrated')
        mp.setenv(quarantine.PUBLICATION_ENV,'1' if enabled else '0');mp.setenv(integrated.DISCLOSURE_ENV,'1' if enabled else '0')
        mp.setenv(quarantine.PUBLICATION_SESSION_ENV,storage.load_session()['campaign_run_id'])
        mp.setenv(quarantine.EVIDENCE_ENV,str(OUT/name/'evidence'))
        original=integrated.run_integrated_hook
        mp.setattr(integrated,'run_integrated_hook',lambda h,**kw:original(h,generator=quarantine._Replay('You examine the weathered milestone.')))
        quarantine.clear_evidence()
        yield mp
@contextmanager
def server():
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    service=uvicorn.Server(uvicorn.Config(api.app,log_level='critical',lifespan='off'))
    thread=threading.Thread(target=lambda:service.run(sockets=[sock]),daemon=True);thread.start()
    for _ in range(3000):
        if service.started: break
        time.sleep(.01)
    assert service.started
    def request(path, payload=None, method=None):
        req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method=method or ('GET' if payload is None else 'POST'))
        start=time.perf_counter()
        try: response=urllib.request.urlopen(req,timeout=60)
        except urllib.error.HTTPError as error: response=error
        raw=response.read().decode(); elapsed=(time.perf_counter()-start)*1000
        try: body=json.loads(raw)
        except ValueError: body=raw
        return dict(request={'path':path,'method':req.method,'json':payload},status=response.status,body=body,serialized_body=raw,bytes=len(raw.encode()),http_ms=elapsed,hidden_exposures=scan(body))
    try: yield request
    finally: service.should_exit=True;thread.join(10);assert not thread.is_alive()
def redact(value):
    # Evidence retains entire schemas; campaign-authored hidden values are replaced.
    keys={'hidden_facts','discoverable_clues','gm_notes','gm_only','private_notes','character_secret','gm_guidance','quest_journal','inference_rules','topics','current_plan','goal','current_agenda'}
    def mask(v):
        if isinstance(v,str): return v if ('CANARY_' in v or 'SENTINEL_' in v) else '[REDACTED CAMPAIGN CONTENT]'
        if isinstance(v,list): return [mask(x) for x in v]
        if isinstance(v,dict): return {k:mask(x) for k,x in v.items()}
        return v
    if isinstance(value,dict): return {k:mask(v) if k in keys else redact(v) for k,v in value.items() if k!='serialized_body'}
    if isinstance(value,list): return [redact(v) for v in value]
    return value
if __name__=='__main__':
    rows=[]
    for enabled in [False,True]:
        with seed('before_'+str(enabled),enabled),server() as request:
            rows.append(dict(enabled=enabled,state=request('/api/state'),action=request('/api/chat',{'text':'I examine the notice board.'})))
    save('original_leak_reproduction.json',redact(rows))
    print([(r['enabled'],r['action']['status'],r['action']['hidden_exposures']) for r in rows])
