from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import hashlib,json,re,shutil,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/atgb/atgb_r1_03'
from tools.validation_evidence import build_packet,write_packet,validate_packet
p=ROOT/'artifacts/validation_evidence/atgb_r1_03/evidence_manifest.json'
x=json.loads(p.read_text(encoding='utf-8'))
for e in x['examples']:
    if e['example_id']=='L4':
        e['semantic_result']='INVALID_RUN'
        e['historical_result']='Frozen correction_pending expects revision without execution; this live control setup was invalid.'
        e['diagnostic_result']['note']=e['diagnostic_result']['note'].replace('tests/conftest.py','experiments/pr_dq/__init__.py')
        e['unexpected_behavior']=True
    e['continuation_action']='Stop; no retry or next pass.'
x=build_packet(campaign=x['campaign'],claim_types=x['claim_types'],examples=x['examples'],
    missing_concepts=[],limitations=x['limitations_and_unproven_claims'],evidence_scope=x['evidence_scope'])
assert not validate_packet(x)
write_packet(p.parent,x)
configpath=ROOT/'data/validation/review_handoffs/atgb_r1_03_controlled_live_validation.json'
c=json.loads(configpath.read_text(encoding='utf-8'))
for path in [Path(__file__),ROOT/'experiments/pr_dq/__init__.py',ROOT/'tests/test_pr_du_player_pipeline.py']:
    if not any(row['path']==path.relative_to(ROOT).as_posix() for row in c['supporting_files']):
        c['supporting_files'].append({'path':path.relative_to(ROOT).as_posix(),'role':'review_verification','why':'Export integrity or invalid fixture environment provenance.','behavioral_evidence':False,'human_review_required':True})
configpath.write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(OUT/'repository_status_after.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),encoding='utf-8')
# Preserve existing sources/baseline and player data; only docs/evidence/export authored.
for inventory in [OUT/'entry_hashes.json',ROOT/'artifacts/atgb/atgb_r1_02/baseline_hashes.json']:
    for path,digest in json.loads(inventory.read_text()).items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
# Content scan selected inputs without emitting sensitive configuration values.
from dotenv import dotenv_values
values=dotenv_values(ROOT/'.env')
protected=[str(v).encode() for k,v in values.items() if v and len(str(v))>=8 and any(s in k.upper() for s in ['KEY','SECRET','PASSWORD','TOKEN'])]
def scan(blob):
    assert not any(v in blob for v in protected),'sensitive configuration value in export'
    assert not re.search(rb'\bsk-[A-Za-z0-9_-]{16,}',blob),'API credential pattern in export'
    assert (b'-----BEGIN '+b'PRIVATE KEY-----') not in blob
for row in c['supporting_files']:
    scan((ROOT/row['path']).read_bytes())
from tools.build_review_handoff import build_handoff
now=datetime.now(timezone.utc)
result=build_handoff(c,root=ROOT,output_dir=ROOT/'handoff',generated_at=now.isoformat(),archive_history=True)
assert all('duplicate' in row['reason'].lower() for row in result['omitted']),result['omitted']
with zipfile.ZipFile(result['zip_path']) as z:
    assert z.testzip() is None
    names=z.namelist()
    for name in names: scan(z.read(name))
    m=json.loads(z.read('REVIEW_MANIFEST.json'))
    for row in m['included_files']:
        if row.get('canonical_source_path'):
            assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
    assert sum('/development/reports/atgb_r1_03/' in n and n.endswith('.md') for n in names)==8
    for t in ['L1','L2','L3','L4']:
        for name in ['setup.json','before.json','after.json','response.json','trace.json','accounting.json','provider_usage.jsonl']:
            assert f'support/artifacts/atgb/atgb_r1_03/{t}/{name}' in names
    summary=z.read('CURRENT_REVIEW.md').decode('utf-8')
    assert 'INCONCLUSIVE' in summary and 'L4' in summary
    assert not any('/store/' in n or '/fixture/' in n or '/.env' in n for n in names)
stamp=now.astimezone(ZoneInfo('America/New_York')).strftime('%Y%m%d-%H%M%S')
dest=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
shutil.copyfile(result['zip_path'],dest)
assert dest.read_bytes()==Path(result['zip_path']).read_bytes()
print(json.dumps({'timestamped_zip':str(dest),'standard_zip':result['zip_path'],'files':result['file_count'],
    'zip_bytes':result['zip_size_bytes'],'verification':'CRC, source hashes, eight reports, four raw trace sets, sensitive-content scan PASS',
    'verdict':'D — Inconclusive','stop':'External review; no ATGB-R1-04 begun.'},indent=2))
