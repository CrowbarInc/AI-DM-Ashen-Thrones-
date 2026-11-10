"""Generate, reopen and verify the standard architectural review export."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, hashlib, subprocess, sys, zipfile, os
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
MID='pr_play_object_identity_architecture'
REPORT=ROOT/'development/campaigns/product_realization'/MID
def sha(raw): return hashlib.sha256(raw).hexdigest()
def dump(name,value): (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
required=['SUMMARY','EXISTING_OBJECT_ARCHITECTURE','ACTION_OWNERSHIP_MAP','CORE_RULESET_BOUNDARY','OBJECT_INSTANCE_CONTRACT','MODIFICATION_CONTRACT','MUNDANE_AFFORDANCE_POLICY','ACTION_RESOLUTION_CONTRACT','ARCHITECTURE_OPTIONS','RULESET_PORTABILITY','T04_T06_INTEGRATION','IMPLEMENTATION_ROADMAP','NEXT_STEP_DECISION','INTEGRITY']
assert sorted(p.stem for p in REPORT.glob('*.md'))==sorted(required)
assert all((REPORT/(s+'.md')).stat().st_size>1800 for s in required)
checks=[
 ('existing_objects','EXISTING_OBJECT_ARCHITECTURE.md'),('action_owners','ACTION_OWNERSHIP_MAP.md'),
 ('mutation_persistence','MODIFICATION_CONTRACT.md'),('repository_evidence','EXISTING_OBJECT_ARCHITECTURE.md'),
 ('responsibility_matrix','CORE_RULESET_BOUNDARY.md'),('no_universal_pf_fields','RULESET_PORTABILITY.md'),
 ('stable_identity','OBJECT_INSTANCE_CONTRACT.md'),('modification_semantics','MODIFICATION_CONTRACT.md'),
 ('reload_inspection','MODIFICATION_CONTRACT.md'),('mundane_policy','MUNDANE_AFFORDANCE_POLICY.md'),
 ('physical_integration','ACTION_OWNERSHIP_MAP.md'),('t04_compatibility','T04_T06_INTEGRATION.md'),
 ('t06_requirements','T04_T06_INTEGRATION.md'),('three_options','ARCHITECTURE_OPTIONS.md'),
 ('selected_architecture','ARCHITECTURE_OPTIONS.md'),('roadmap','IMPLEMENTATION_ROADMAP.md'),
 ('one_next_milestone','NEXT_STEP_DECISION.md'),('no_production_change','INTEGRITY.md'),
 ('zero_live_provider','INTEGRITY.md'),('archive_handoff','INTEGRITY.md')]
dump('acceptance_review.json',{'milestone':MID,'review_kind':'design/document coverage, not runtime proof','criteria':[{'number':i,'criterion':c,'report':f,'assessment':'addressed; inspect report for actual claim/limits'} for i,(c,f) in enumerate(checks,1)]})
dump('report_inventory.json',[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'size_bytes':p.stat().st_size} for p in sorted(REPORT.glob('*.md'))])
# Refresh evidence/config after final manifests and this sealing procedure exist.
subprocess.run([sys.executable,str(OUT/'prepare_review.py')],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(OUT/'investigate.py'),'final'],cwd=ROOT,check=True)
# The second preparation adds final source manifests to explicit package support.
subprocess.run([sys.executable,str(OUT/'prepare_review.py')],cwd=ROOT,check=True)
generated=datetime.now(timezone.utc).isoformat()
export=OUT/'review_export'
cmd=[sys.executable,'tools/build_review_handoff.py','--config',str(OUT/'review_handoff.json'),'--output-dir',str(export),'--generated-at',generated,'--no-history']
run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
(OUT/'handoff_generation.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
assert run.returncode==0,(run.returncode,run.stderr)
history=ROOT/'handoff/history'/MID
history.mkdir(parents=True,exist_ok=True)
for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip'):
    raw=(export/name).read_bytes()
    target=ROOT/'handoff'/name
    temp=target.with_name(target.name+'.object_identity.tmp')
    temp.write_bytes(raw); os.replace(temp,target)
    histname={'CURRENT_REVIEW.md':'REVIEW.md','CURRENT_REVIEW.zip':'REVIEW.zip'}.get(name,name)
    (history/histname).write_bytes(raw)
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
dated=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
assert not dated.exists(),'Refusing to reuse a dated archive'
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
        assert len(z.namelist())==manifest['bundle_metrics']['file_count']
        for row in manifest['included_files']:
            if row.get('sha256'):
                raw=z.read(row['bundle_path'])
                assert sha(raw)==row['sha256'],row
                if row.get('canonical_source_path'):
                    assert raw==(ROOT/row['canonical_source_path']).read_bytes(),row['canonical_source_path']
        base='support/development/campaigns/product_realization/'+MID+'/'
        for s in required: assert base+s+'.md' in z.namelist()
        for name,needles in {
          'SUMMARY.md':[MID,'Option B','A/PASS','143'],
          'ARCHITECTURE_OPTIONS.md':['Choose B','A alone','C alone'],
          'RULESET_PORTABILITY.md':['PF1e','Rules-light','Modern/science-fiction','Conceptual compatibility'],
          'IMPLEMENTATION_ROADMAP.md':['Phase 1','Phase 6','pr_play_object_instance_identity'],
          'NEXT_STEP_DECISION.md':['Exactly one','pr_play_object_instance_identity','Exclusions'],
          'INTEGRITY.md':['Production files changed: **None (0)**','Live provider calls **0**'],
        }.items():
            text=z.read(base+name).decode('utf-8')
            assert all(n in text for n in needles),(name,needles)
        nextbytes=z.read('support/docs/NEXT_SESSION.md')
        assert nextbytes.startswith(b'# NEXT_SESSION') and MID.encode() in nextbytes[:800]
        assert nextbytes.endswith((OUT/'entry_next_session.md').read_bytes())
        ebase='support/artifacts/'+MID+'/'
        for s in ('before_manifest.json','after_manifest.json','source_changes.json','evidence_manifest.json','existing_contract_excerpts.json','validation_summary.json','ruleset_portability_matrix.json','implementation_dependencies.json','acceptance_review.json'):
            member(ebase+s)
        changes=json.loads(z.read(ebase+'source_changes.json'))
        assert changes=={'changed':[],'added':[]}
        evidence=json.loads(z.read(ebase+'evidence_manifest.json'))
        for item in evidence['files']:
            assert sha(member('support/'+item['path']))==item['sha256'],item['path']
        report_index=json.loads(z.read(ebase+'report_inventory.json'))
        for item in report_index:
            assert sha(z.read('support/'+item['path']))==item['sha256'],item['path']
        verified.append({'path':str(path),'sha256':sha(path.read_bytes()),'files':len(z.namelist()),'bytes':path.stat().st_size,'crc':'pass','canonical_hashes':'pass','report_and_evidence_manifests':'pass','all_14_reports':'pass','milestone_architecture_portability_roadmap_next_step_handoff':'pass'})
assert verified[0]['sha256']==verified[1]['sha256']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==json.loads((OUT/'entry_identity.json').read_text())['head']
dump('archive_verification.json',{'milestone':MID,'verified_at':datetime.now(timezone.utc).isoformat(),'verdict':'A/PASS for architectural investigation only','archives':verified,'historical_next_session_suffix':'byte-identical','production_test_data_source_changes':[],'live_provider_calls':0,'conceptual_controls_not_runtime_tests':True})
(OUT/'archive_sha256.txt').write_text(verified[1]['sha256']+'  '+str(dated)+'\n',encoding='utf-8')
print(json.dumps({'verdict':'A/PASS','archive':str(dated),'sha256':verified[1]['sha256'],'files':verified[1]['files'],'bytes':verified[1]['bytes']},indent=2))
