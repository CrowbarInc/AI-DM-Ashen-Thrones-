"""Final review export; verify packaged sources and stop at the ZIP."""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib,json,shutil,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tools.build_review_handoff import build_handoff
from tools.validation_evidence import validate_packet
out=ROOT/'artifacts/atgb/atgb_r1_02'
config_path=ROOT/'data/validation/review_handoffs/atgb_r1_02_mechanical_revision_boundary.json'
config=json.loads(config_path.read_text(encoding='utf-8'))
# Capture status immediately before review generation. Existing dirty changes are
# distinguished by repository_status_before and the scoped source/handoff diffs.
(out/'repository_status_after.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),encoding='utf-8')
base=json.loads((out/'baseline_hashes.json').read_text())
assert all((ROOT/p).is_file() and hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in base.items())
packet=json.loads((ROOT/'artifacts/validation_evidence/atgb_r1_02/evidence_manifest.json').read_text(encoding='utf-8'))
assert not validate_packet(packet)
now=datetime.now(timezone.utc)
result=build_handoff(config,root=ROOT,output_dir=ROOT/'handoff',generated_at=now.isoformat(),archive_history=True)
assert all('duplicate' in row['reason'].lower() for row in result['omitted']), result['omitted']
with zipfile.ZipFile(result['zip_path']) as archive:
 assert archive.testzip() is None
 manifest=json.loads(archive.read('REVIEW_MANIFEST.json'))
 for row in manifest['included_files']:
  if row.get('canonical_source_path'):
   assert hashlib.sha256(archive.read(row['bundle_path'])).hexdigest()==row['sha256']
 names=archive.namelist()
 assert sum('/development/reports/atgb_r1_02/' in n and n.endswith('.md') for n in names)==8
 assert 'support/artifacts/atgb/atgb_r1_02/s08_2_trace.json' in names
 summary=archive.read('CURRENT_REVIEW.md').decode('utf-8')
 assert 'NOT EVALUABLE' in summary and 'Conditional' not in '' # explicit grade is in summary
stamp=now.astimezone(ZoneInfo('America/New_York')).strftime('%Y%m%d-%H%M%S')
timestamped=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
shutil.copyfile(result['zip_path'],timestamped)
assert timestamped.read_bytes()==Path(result['zip_path']).read_bytes()
print(json.dumps({'timestamped_review_zip':str(timestamped),'standard_review_zip':result['zip_path'],'files':result['file_count'],'zip_bytes':result['zip_size_bytes'],'zip_crc_and_source_hashes':'PASS','protected_files_unchanged':len(base),'verdict':'B — Conditional','stop':'External review; ATGB-R1-03 not started.'},indent=2))
