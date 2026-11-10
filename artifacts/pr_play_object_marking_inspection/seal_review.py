"""Generate the standard export, reopen it and verify bundled claims/hashes."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
MID='pr_play_object_marking_inspection'
def sha(raw): return hashlib.sha256(raw).hexdigest()
export=OUT/'review_export'
run=subprocess.run([sys.executable,'tools/build_review_handoff.py','--config',str(OUT/'review_handoff.json'),
    '--output-dir',str(export),'--no-history'],cwd=ROOT,text=True,capture_output=True)
(OUT/'handoff_generation.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
assert run.returncode==0,run.stderr
history=ROOT/'handoff/history'/MID;history.mkdir(parents=True,exist_ok=True)
for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip'):
    raw=(export/name).read_bytes();target=ROOT/'handoff'/name
    temp=target.with_name(target.name+'.inspection.tmp');temp.write_bytes(raw);os.replace(temp,target)
    hist={'CURRENT_REVIEW.md':'REVIEW.md','CURRENT_REVIEW.zip':'REVIEW.zip'}.get(name,name)
    (history/hist).write_bytes(raw)
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
dated=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
assert not dated.exists();dated.write_bytes((export/'CURRENT_REVIEW.zip').read_bytes())
verified=[]
for archive in (ROOT/'handoff/CURRENT_REVIEW.zip',dated):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json'));assert manifest['campaign_id']==MID
        omissions=manifest['omitted_artifacts']
        assert all(o['reason'].startswith('duplicate content of ') for o in omissions),omissions
        def member(path):
            if path in z.namelist(): return z.read(path)
            relative=path.removeprefix('support/')
            item=next(o for o in omissions if o['path']==relative)
            duplicate=item['reason'].split('duplicate content of ',1)[1].split(';',1)[0]
            raw=z.read('support/'+duplicate);assert sha(raw)==item['sha256'];return raw
        for row in manifest['included_files']:
            if row.get('sha256'):
                raw=z.read(row['bundle_path']);assert sha(raw)==row['sha256']
                if row.get('canonical_source_path'): assert raw==(ROOT/row['canonical_source_path']).read_bytes()
        base='support/artifacts/'+MID+'/'
        evidence=json.loads(member(base+'evidence_manifest.json'))
        for row in evidence['files']:
            assert sha(member('support/'+row['path']))==row['sha256'],row['path']
        report_base='support/development/campaigns/product_realization/'+MID+'/'
        reports=['SUMMARY','BASELINE','INSPECTION_CONTRACT','REMOVAL_CONTRACT','IDEMPOTENCY_VERIFICATION',
            'STATE_HISTORY_SEPARATION','IMPLEMENTATION','PERSISTENCE_VERIFICATION','NEGATIVE_CONTROLS',
            'REGRESSION_RESULTS','TWELVE_TURN_COMPARISON','RULESET_PORTABILITY','PERFORMANCE','NEXT_STEP_DECISION','INTEGRITY']
        for name in reports: assert MID.encode() in member(report_base+name+'.md')
        source=member('support/game/api.py')
        assert b'def inspect_inventory_object_markings' in source and b'def remove_inventory_object_marking' in source
        timeline=json.loads(member(base+'inspection_removal_timeline.json'))
        before,after=timeline['before'],timeline['after']
        assert len(timeline['two_markings']['markings'])==2 and len(timeline['current']['markings'])==1
        assert timeline['removal_result']==timeline['replay']
        assert after==timeline['reloaded']
        assert after['inventory'][0]['instance_id']==timeline['original']['inventory'][0]['instance_id']
        assert after['inventory'][0]['revision']==before['inventory'][0]['revision']+1==3
        assert after['inventory'][1]==before['inventory'][1]
        entries=after['object_marking_receipts']['entries']
        assert len(entries)==3
        assert all(entries[k]==v for k,v in before['object_marking_receipts']['entries'].items())
        assert [len(s['inspection']['markings']) for s in timeline['snapshots']]==[0,2,1]
        assert [s['inspection']['revision'] for s in timeline['snapshots']]==[0,2,3]
        assert [len(s['character'].get('object_marking_receipts',{}).get('entries',{})) for s in timeline['snapshots']]==[0,2,3]
        controls=json.loads(member(base+'idempotency_controls.json'))
        assert controls['exact_replay']==controls['original']
        assert controls['conflicting']['error']==controls['cross_operation']['error']=='conflicting_request'
        assert controls['absent']['error']=='missing_marking'
        for fault in ('save','replace','sync','post_save'):
            row=json.loads(member(base+'removal_failure_'+fault+'.json'))
            assert row['unchanged_after_failure'] and row['temporary_files']==[]
            assert row['retry_result']['resulting_revision']==3
        for name in ('pf1e@1','rules_light@1','scifi@1'):
            row=json.loads(member(base+'portability_'+name+'.json'))
            assert row['before']['inventory'][0]['extensions']==row['after']['inventory'][0]['extensions']
            assert row['before']['inventory'][1:]==row['after']['inventory'][1:]
        regression=json.loads(member(base+'regression_results.json'))
        assert not regression['new_failures']
        assert regression['final_inspection']['passed']==72
        for name in ('marking','identity','inventory_snapshot','preservation'):
            assert regression['before_'+name]['passed']==regression['after_'+name]['passed']
            assert regression['after_'+name]['failed']==0
        comparison=json.loads(member(base+'twelve_turn_comparison.json'))
        flags=('text_equal','character_equal','scene_equal','resolution_equal','no_implicit_identity_or_marking','publication_pointer_consistent')
        assert len(comparison['turns'])==12 and all(all(t[k] for k in flags) for t in comparison['turns'])
        handoff=member('support/docs/NEXT_SESSION.md')
        assert MID.encode() in handoff[:700] and handoff.endswith((OUT/'entry_next_session.md').read_bytes())
        sources=json.loads(member(base+'source_changes.json'))
        assert sources['changed_existing']==['game/api.py','game/object_marking.py']
        assert not sources['frozen_fixture_changes'] and not sources['production_data_changes']
        assert MID.encode() in z.read('CURRENT_REVIEW.md')
        verified.append(dict(path=str(archive),sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,
            members=len(z.namelist()),crc='pass',canonical_hashes='pass',evidence_manifest='pass',all_15_reports='pass',
            inspection='pass',removal='pass',history='pass',save_reload='pass',snapshots='pass',idempotency='pass',
            failure_injection='pass',portability='pass',regression='pass',twelve_turn='pass',handoff='pass'))
assert verified[0]['sha256']==verified[1]['sha256']
entry=json.loads((OUT/'entry_identity.json').read_text())
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==entry['head']
(OUT/'archive_verification.json').write_text(json.dumps(dict(milestone=MID,verdict='A/PASS',archives=verified,
    historical_handoff_suffix='byte-identical',live_provider_calls=0),indent=2),encoding='utf-8')
(OUT/'archive_sha256.txt').write_text(verified[1]['sha256']+'  '+str(dated)+'\n',encoding='utf-8')
print(json.dumps(verified[1],indent=2))
