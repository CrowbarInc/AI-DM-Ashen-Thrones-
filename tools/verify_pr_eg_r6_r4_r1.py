"""Verify review ZIP contents, provenance hashes and unchanged frozen runtime."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.pr_eg_r6_r4_r1.run import verify,OUT,read,sha,dump


def main():
    verify()
    for r in read(OUT/'source_inventory.json'):
        assert sha(ROOT/r['path'])==r['sha256'],r['path']
    with zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW.zip') as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
        assert manifest==read(ROOT/'handoff/REVIEW_MANIFEST.json'),'External manifest differs from ZIP'
        assert z.read('CURRENT_REVIEW.md').decode('utf-8').replace('\r\n','\n')==(ROOT/'handoff/CURRENT_REVIEW.md').read_text(encoding='utf-8'),'External review differs from ZIP'
        records=manifest.get('included_files',manifest.get('included',[]))
        if not records:raise RuntimeError('Manifest file records missing')
        checked=0
        for item in records:
            if not item.get('sha256'):continue
            p=item['bundle_path']
            assert hashlib.sha256(z.read(p)).hexdigest()==item['sha256'],p
            if item.get('canonical_source_path'):
                assert sha(ROOT/item['canonical_source_path'])==item['sha256'],item['canonical_source_path']
            checked+=1
        docs=[p for p in z.namelist() if p.startswith('support/artifacts/pr_eg_r6_r4_r1/') and len(p.split('/'))==4 and p.split('/')[-1][:2].isdigit() and p.endswith('.md')]
        assert len(docs)==39,len(docs)
        assert not any('_tmp/' in p or '/.env' in p or '/attempts/' in p for p in z.namelist())
        # Confirm the packaged freeze and primary results, not just live files.
        freeze=read(OUT/'freeze.json')
        for path,h in freeze['hashes'].items():
            assert hashlib.sha256(z.read('support/'+path)).hexdigest()==h,path
        exported=[json.loads(l) for l in z.read('support/artifacts/pr_eg_r6_r4_r1/provider_calls.jsonl').decode('utf-8').splitlines()]
        assert len(exported)==570
        for record in exported:
            # Prove compact export can recover exact original request evidence.
            serialized=json.dumps(record['record'],ensure_ascii=False,indent=2)
            candidates=[serialized.encode('utf-8'),serialized.replace('\n','\r\n').encode('utf-8')]
            assert sha(ROOT/record['path']) in {hashlib.sha256(v).hexdigest() for v in candidates},record['path']
        assert len(z.read('support/artifacts/pr_eg_r6_r4_r1/per_case_results.jsonl').splitlines())==510
    result=dict(zip_readable=True,manifest_hashes_verified=checked,numbered_artifacts=39,
        frozen_hashes_verified=len(read(OUT/'freeze.json')['hashes']),source_inventory_verified=True,
        production_unchanged=True,zip_bytes=(ROOT/'handoff/CURRENT_REVIEW.zip').stat().st_size,
        human_adjudication='pending',broader_regression='interrupted; focused 228 passed')
    dump(OUT/'bundle_verification.json',result);print(json.dumps(result))


if __name__=='__main__':main()
