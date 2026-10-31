"""Read-only Phase A: no inference; no credential/configuration writes."""
import ast
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import time
from urllib.parse import urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, default=str)+'\n', encoding='utf-8')
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

entry = json.loads((ROOT/'artifacts/atgb/atgb_r1_08/entry_hashes.json').read_text())
mismatches = [p for p,h in entry.items() if not (ROOT/p).is_file() or digest(ROOT/p)!=h]
with zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW(20261019-062339).zip') as z:
    reviewed = {p: digest(ROOT/p)==hashlib.sha256(z.read('support/'+p)).hexdigest()
        for p in ('game/live_chat_interpretation.py','game/conversational_orchestration.py')}
from tools.atgb.baseline import load_baseline
load_baseline(ROOT)
baseline = {'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
    'r1_08_entry_files':len(entry),'mismatches':mismatches,'r1_07_review_matches':reviewed,
    'frozen_baseline_verified':True, 'orientation':'docs/NEXT_SESSION.md; requested support path absent'}
write('baseline.json',baseline)
(OUT/'repository_status_before.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),encoding='utf-8')
protected = {}
for folder in ('game','data','experiments','tests','tools/atgb','artifacts/atgb'):
    for p in (ROOT/folder).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and OUT not in p.parents:
            protected[p.relative_to(ROOT).as_posix()] = digest(p)
write('entry_hashes.json', protected)
(OUT/'NEXT_SESSION_before.md').write_bytes((ROOT/'docs/NEXT_SESSION.md').read_bytes())
assert not mismatches and all(reviewed.values()), 'material baseline difference'

from game import config
import openai
import httpx
from tools.atgb import readiness
tree=ast.parse((ROOT/'game/gm.py').read_text(encoding='utf-8'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='provider_timeout_seconds')
ns={'os':os}
exec(compile(ast.Module(body=[fn],type_ignores=[]),'provider_timeout_seconds','exec'),ns)
timeout=ns['provider_timeout_seconds']()
try:
    present=bool(config.get_openai_api_key())
except RuntimeError:
    present=False
client=openai.OpenAI(api_key=config.get_openai_api_key() if present else 'not-a-real-credential',timeout=timeout,max_retries=0)
url=urlsplit(str(client.base_url))
endpoint=f'{url.scheme}://{url.hostname}'+(f':{url.port}' if url.port else '')+url.path
proxies={}
for key in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy'):
    val=os.environ.get(key)
    if val:
        if key.lower()=='no_proxy':
            proxies[key]={'present':True,'entry_count':len(val.split(','))}
        else:
            u=urlsplit(val)
            proxies[key]={'present':True,'scheme':u.scheme,'hostname':u.hostname,'port':u.port,'credentials_present':bool(u.username or u.password)}
cfg={'provider':'OpenAI Responses','configured_model':config.DEFAULT_MODEL_NAME,
     'routing_models':[config.HIGH_PRECISION_MODEL_NAME,config.RETRY_ESCALATION_MODEL_NAME],
     'endpoint':endpoint,'sdk_version':openai.__version__,'httpx_version':httpx.__version__,
     'transport':type(client._client._transport).__name__, 'trust_env':client._client._trust_env,
     'timeout':{k:getattr(client._client.timeout,k) for k in ('connect','read','write','pool')},
     'sdk_retries':client.max_retries,'sdk_retries_note':'Measured-runner setting from R1-05/08; constructor only, no requests',
     'credential_present':present,'flags':readiness.flag_snapshot(),'proxy_configuration':proxies,
     'certificate_override_presence':{k:bool(os.environ.get(k)) for k in ('SSL_CERT_FILE','SSL_CERT_DIR','REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE')},
     'ssl_default_verify_paths':ssl.get_default_verify_paths()._asdict()}
write('provider_configuration.json',cfg)
client.close()
diag={'non_billable':True,'inference_requests':0,'host':url.hostname,'timeout_seconds':5,'proxy_route':'SDK trust_env uses configured proxy if present; direct socket checks below do not test proxy' if proxies else 'No proxy environment configured'}
for name in ('dns','tcp','tls'):
    start=time.perf_counter()
    try:
        if name=='dns':
            values=socket.getaddrinfo(url.hostname,url.port or 443,type=socket.SOCK_STREAM)
            detail={'addresses':sorted({v[4][0] for v in values})}
        elif name=='tcp':
            with socket.create_connection((url.hostname,url.port or 443),timeout=5) as sock:
                detail={'connected':True}
        else:
            context=ssl.create_default_context()
            with socket.create_connection((url.hostname,url.port or 443),timeout=5) as sock:
                with context.wrap_socket(sock,server_hostname=url.hostname) as secure:
                    detail={'certificate_verified':True,'protocol':secure.version()}
        diag[name]={'status':'PASS',**detail}
    except Exception as e:
        diag[name]={'status':'FAIL','exception_type':type(e).__name__,'errno':getattr(e,'errno',None),'winerror':getattr(e,'winerror',None), 'reason':getattr(e,'reason',None)}
    diag[name]['elapsed_ms']=round((time.perf_counter()-start)*1000,3)
block=[]
if not present: block.append('credential_absent')
if cfg['configured_model']!='gpt-4.1-mini' or set(cfg['routing_models'])!={'gpt-4.1-mini'}: block.append('model_mismatch')
if endpoint.rstrip('/')!='https://api.openai.com/v1': block.append('endpoint_mismatch')
if any(diag[k]['status']=='FAIL' for k in ('dns','tcp','tls')): block.append('network_diagnostic_failure')
diag['readiness']='BLOCKED' if block else 'READY'
diag['blockers']=block
diag['limitations']='DNS/TCP/TLS cannot prove authentication, model access or successful inference. No authentication endpoint called.'
write('readiness_diagnostics.json',diag)
print(json.dumps({'baseline':baseline,'configuration':cfg,'diagnostics':diag},indent=2))
