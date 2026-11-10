"""Generate and independently reopen the cycle's standard review archives."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, subprocess, sys, zipfile
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
MID='pr_play_object_instance_identity'
def sha(raw): return hashlib.sha256(raw).hexdigest()
config=json.loads((OUT/'review_handoff.json').read_text())
config['supporting_files'].append({'path':(OUT/'seal_review.py').relative_to(ROOT).as_posix(),
    'role':'verification_tool','canonical':True,'why':'Reproducible archive verification.'})
(OUT/'review_handoff.json').write_text(json.dumps(config,indent=2))
export=OUT/'review_export'
cmd=[sys.executable,'tools/build_review_handoff.py','--config',str(OUT/'review_handoff.json'),
    '--output-dir',str(export),'--no-history']
run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
(OUT/'handoff_generation.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
assert run.returncode==0,run.stderr
history=ROOT/'handoff/history'/MID
history.mkdir(parents=True,exist_ok=True)
for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip'):
    raw=(export/name).read_bytes()
    target=ROOT/'handoff'/name
    temporary=target.with_name(target.name+'.object_instance.tmp')
    temporary.write_bytes(raw); os.replace(temporary,target)
    histname={'CURRENT_REVIEW.md':'REVIEW.md','CURRENT_REVIEW.zip':'REVIEW.zip'}.get(name,name)
    (history/histname).write_bytes(raw)
# New York is on EST on this cycle's 2026-11-09 client date.
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
dated=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
assert not dated.exists()
dated.write_bytes((ROOT/'handoff/CURRENT_REVIEW.zip').read_bytes())
verified=[]
for path in (ROOT/'handoff/CURRENT_REVIEW.zip',dated):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
        assert manifest['campaign_id']==MID
        omissions=manifest['omitted_artifacts']
        assert all(o['reason'].startswith('duplicate content of ') for o in omissions),omissions
        def member(path):
            if path in z.namelist(): return z.read(path)
            relative=path.removeprefix('support/')
            match=next(o for o in omissions if o['path']==relative)
            duplicate=match['reason'].split('duplicate content of ',1)[1].split(';',1)[0]
            raw=z.read('support/'+duplicate)
            assert sha(raw)==match['sha256']
            return raw
        for row in manifest['included_files']:
            if row.get('sha256'):
                raw=z.read(row['bundle_path']); assert sha(raw)==row['sha256']
                if row.get('canonical_source_path'):
                    assert raw==(ROOT/row['canonical_source_path']).read_bytes()
        ebase='support/artifacts/'+MID+'/'
        evidence=json.loads(member(ebase+'evidence_manifest.json'))
        for item in evidence['files']:
            assert sha(member('support/'+item['path']))==item['sha256'],item['path']
        reports='support/development/campaigns/product_realization/'+MID+'/'
        required=['SUMMARY','BASELINE','IDENTITY_CONTRACT','IMPLEMENTATION','MIGRATION_SAFETY','PERSISTENCE_VERIFICATION','NEGATIVE_CONTROLS','REGRESSION_RESULTS','TWELVE_TURN_COMPARISON','PERFORMANCE','NEXT_STEP_DECISION','INTEGRITY']
        for name in required: assert MID.encode() in member(reports+name+'.md')
        assert b'def ensure_object_instance_identity' in member('support/game/object_instances.py')
        assert b'def migrate_inventory_object_identity' in member('support/game/api.py')
        persistence=json.loads(member(ebase+'persistence_round_trip.json'))
        assert persistence['assigned']==persistence['reloaded']==persistence['restored']
        regression=json.loads(member(ebase+'regression_results.json'))
        assert not regression['new_failures'] and regression['final_identity_v2']['passed']==52
        comparison=json.loads(member(ebase+'twelve_turn_comparison.json'))
        assert len(comparison['turns'])==12 and all(t['published_text_equal'] and t['no_implicit_identity'] for t in comparison['turns'])
        next_session=member('support/docs/NEXT_SESSION.md')
        assert MID.encode() in next_session[:800] and next_session.endswith((OUT/'entry_next_session.md').read_bytes())
        assert 'pr_play_object_marking_mutation' in member(reports+'NEXT_STEP_DECISION.md').decode()
        verified.append({'path':str(path),'sha256':sha(path.read_bytes()),'bytes':path.stat().st_size,
            'members':len(z.namelist()),'crc':'pass','canonical_hashes':'pass','evidence_manifest':'pass',
            'all_12_reports':'pass','implementation':'pass','persistence':'pass','regression':'pass','twelve_turn':'pass','handoff':'pass'})
assert verified[0]['sha256']==verified[1]['sha256']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==json.loads((OUT/'entry_identity.json').read_text())['head']
(OUT/'archive_verification.json').write_text(json.dumps({'milestone':MID,'verdict':'A/PASS','archives':verified,
    'historical_next_session_suffix':'byte-identical','live_provider_calls':0},indent=2))
(OUT/'archive_sha256.txt').write_text(verified[1]['sha256']+'  '+str(dated)+'\n')
print(json.dumps(verified[1],indent=2))
