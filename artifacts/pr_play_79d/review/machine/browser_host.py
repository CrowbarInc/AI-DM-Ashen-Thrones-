"""Restored 79C normal-flow campaign, isolated execution accounting and evidence."""
import hashlib, json, os, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
SOURCE = ROOT/'artifacts/pr_play_79c/browser_data'
DATA = OUT/'browser_data'
if not DATA.exists():
    shutil.copytree(SOURCE, DATA, ignore=shutil.ignore_patterns('provider_usage.jsonl', 'publication_events.jsonl'))
    manifest = [{'path': str(p.relative_to(SOURCE)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(SOURCE.rglob('*')) if p.is_file() and p.name != 'provider_usage.jsonl']
    (OUT/'browser_fixture.json').write_text(json.dumps({'source': str(SOURCE), 'files':manifest,
        'provenance':'79C initialized through normal live opening and browser conversation; restored continuation, not fresh opening',
        'execution_ledger':'fresh, excluded copied provider ledger; admission controls unchanged'}, indent=2))
from tests.helpers.storage_isolation import install
install(DATA)
phase = os.environ.get('PR79D_BROWSER_PHASE', '')
os.environ['ASHEN_PROVIDER_USAGE_PATH'] = str(OUT/('browser_provider_usage'+phase+'.jsonl'))
os.environ['ASHEN_PUBLICATION_TRACE_PATH'] = str(OUT/'browser_publication.jsonl')
os.environ['ASHEN_PROVIDER_REQUEST_LIMIT'] = '1' if phase == '_boundary' else ('10' if phase else '12')
os.environ['ASHEN_PROVIDER_INPUT_TOKEN_LIMIT'] = '10000'
os.environ['ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT'] = '2000'
os.environ['ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT'] = '11000' if phase else '12000'
os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'] = '1'
os.environ['ASHEN_DISABLE_PROVIDER_RETRIES'] = '1'
for key in ['ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION']:
    os.environ.pop(key, None)
for suffix in ['BRANCHING','BRANCHING_NEW_CAMPAIGNS','PLAYER_INITIATIVE','WORLD_IMPROVISATION',
               'PHYSICAL_ADJUDICATION','DYNAMIC_NPCS','INTEGRATED_NARRATION']:
    os.environ['ASHEN_EXPERIMENTAL_'+suffix] = '1'
os.environ['ASHEN_BOUNDED_SPEECH'] = '1'
from game import api, storage
from starlette.responses import Response

@api.app.middleware('http')
async def evidence(request, call_next):
    started = time.perf_counter()
    raw = await request.body()
    before = storage.load_session() if request.url.path in {'/api/chat','/api/snapshots/load'} else None
    response = await call_next(request)
    body = b''.join([chunk async for chunk in response.body_iterator])
    row = dict(path=request.url.path, method=request.method, request=raw.decode('utf-8',errors='replace'),
        status=response.status_code, server_ms=round((time.perf_counter()-started)*1000,2),
        response=json.loads(body) if 'application/json' in response.headers.get('content-type','') else None,
        before=before, after=storage.load_session() if before else None)
    if row['response'] is not None:
        with (OUT/'browser_network.jsonl').open('a',encoding='utf-8') as handle:
            handle.write(json.dumps(row,ensure_ascii=False)+'\n')
    return Response(body,status_code=response.status_code,headers=dict(response.headers),media_type=response.media_type)

if __name__ == '__main__':
    import uvicorn
    (OUT/('browser_host'+phase+'.pid')).write_text(str(os.getpid()))
    uvicorn.run(api.app, host='127.0.0.1', port=8100 if phase == '_boundary' else (8099 if phase else 8098), log_level='warning')
