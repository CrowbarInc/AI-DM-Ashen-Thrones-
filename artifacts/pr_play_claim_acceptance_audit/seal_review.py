"""Cycle-owned evidence packaging and independent archive verification; no runtime edits."""
import hashlib, json, os, shutil, subprocess, sys, zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
R=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent
ID='pr_play_claim_acceptance_audit'; RP='development/campaigns/product_realization/'+ID+'/'
AP='artifacts/'+ID+'/'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,x): (O/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def protected_check():
 m=read(R/'artifacts/pr_play_baseline_provenance/source_manifest.json')
 dif=[p for p,h in m['files'].items() if not (R/p).is_file() or sha(R/p)!=h]
 assert not dif,dif
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==m['head']
 assert subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()==m['branch']
 return m

if len(sys.argv)>1 and sys.argv[1]=='prepare':
 m=protected_check()
 prior={p.relative_to(R).as_posix():sha(p) for p in (R/'handoff').glob('CURRENT_REVIEW(*).zip')}
 save('prior_dated_archives.json',prior)
 # The predecessor's selected historical archives are only rehashed, not reconstructed/opened.
 old=read(R/'artifacts/pr_play_baseline_provenance/historical_archives.json')
 comparisons=[{'path':v['path'],'matches_predecessor_hash':sha(R/v['path'])==v['sha256']} for v in old if v['path']!='handoff/CURRENT_REVIEW.zip']
 assert all(v['matches_predecessor_hash'] for v in comparisons)
 save('prior_archive_preservation.json',comparisons)
 save('archive_validation_protocol.json',{'milestone':ID,'reports':9,'checks':['ZIP CRC','internal milestone','required reports','canonical member hashes','updated NEXT_SESSION and preserved historical suffix','evidence manifest','baseline source preservation','prior dated archives','stable/dated SHA-256 equality'],'final_seal_external_to_avoid_circularity':True})
 # Include this cycle's raw captures as well as compact three-case evidence.
 names=['baseline_verification.json','source_hashes.json','entry_git_status.txt','entry_next_session.md',
 'run_audit.py','run_controls.py','analyze_traces.py','build_reports.py','seal_review.py',
 'command.json','collected_nodes.json','baseline_junit.xml','failures.json','execution_integrity.json','pytest_output.txt',
 'controls_output.txt','probe_output.txt','probe_integrity.json','three_case_trace.json','trace_summary.json',
 'classification_matrix.json','classification_probes.json','negative_controls.json','related_publication.json','test_results.json',
 'prior_dated_archives.json','prior_archive_preservation.json','archive_validation_protocol.json',
 'authority/command.json','authority/collected_nodes.json','authority/recovery_junit.xml','authority/failures.json','authority/execution_integrity.json',
 'authority/entry_git_status.txt','authority/entry_hashes.json','authority/http_capture.json','entry_hashes.json','http_capture.json','stage_events.json']
 source=['game/api.py','game/immutable_valid_response.py','game/perception_grounding.py','game/referenced_surface.py',
 'game/exploration.py','game/mechanical_claims.py','game/gm_resolution_decision.py','game/proposition_authority.py',
 'game/bounded_improvisation.py','game/consequential_narration_validation.py','game/publication_contract.py','game/player_http_projection.py',
 'tests/test_referenced_surface_grounding_inspection_resolution.py','tests/test_pr_play_post_npc_handoff.py',
 'tests/test_pr_play_46_mechanical_boundary.py','tests/test_pr_br_continuation18_immutable_boundary.py',
 'tests/test_pr_play_79df3_classification.py','tests/test_perception_narration_authority_audible_non_invention.py',
 'docs/DEVELOPMENT_CONSTITUTION.md','docs/review_handoff_standard.md','docs/state_authority_model.md','docs/validation_layer_separation.md',
 'docs/NEXT_SESSION.md','development/campaigns/product_realization/pr_play_67/05_PLAYER_SAFE_RESPONSE_CONTRACT.md',
 'artifacts/pr_play_baseline_provenance/source_manifest.json','development/campaigns/product_realization/pr_play_baseline_provenance/CURRENT_BASELINE.md']
 report_paths=[p.relative_to(R).as_posix() for p in (R/RP).glob('*.md')]
 supports=report_paths+[AP+n for n in names]+source+[AP+'evidence_manifest.json',AP+'review_handoff.json']
 config={
 'campaign_id':ID,'campaign_name':'PR-PLAY Consequential Narrative Claim Acceptance Audit','campaign_date':'2026-11-08',
 'purpose':'Trace three unsupported consequential claims through real acceptance/publication and select the smallest pre-seal remedy without implementation.',
 'objective_status':'A/PASS',
 'executive_summary':'Investigation A/PASS; no repair. All three unsupported claims reproduce. Existing claim auditing runs but extracts nothing; hard/perception validation pass, initial text seals and downstream grounding skips. Recommend pre-seal closed-surface inspection outcome projection using existing authority/rendering, with validated neutral hidden-target wording. 381 tests: 358 passed, 23 known failures; unchanged 356 baseline plus 25 mechanical passes. No production/test edits; live provider calls 0.',
 'changes':{'production':[],'validation':['Unchanged provider-free reproductions and negative controls; isolated unchanged-function probes.'],'tooling':[],'documentation':['Nine investigation reports; NEXT_SESSION prepended, all historical entries preserved.'],'generated_artifacts':['Runtime traces, classification, source/test evidence and fresh sealed review.']},
 'testing':{'focused':'235 tests: 219 passed / 16 failed, matching original baseline failure ids.','broader':'146 tests: 139 passed / 7 failed; original 121 plus 25 passing mechanical controls.','full_suite':'Not run','runtime_validation':'Three unchanged HTTP defects reproduce; seven post-NPC HTTP controls pass. Renderer/fallback compatibility probes retained.','model_runtime_boundary':'0 live provider calls; storage isolated, external network blocked; 1,294 baseline hashes match.','new_regressions':'None identified; both failure-id sets match baseline. No production edits.','pre_existing_failures':'23: obsolete public-resolution assertions, three publication defects, stew mismatch, authority/pointer failures and portal exception, three unrelated KeyErrors.'},
 'decisions_requiring_human_review':['No approval is needed to complete the audit. The sole future recommendation is bounded pre-seal closed-surface outcome projection; implementation has not begun.'],
 'known_problems':{'campaign_specific':['Unimplemented repair; hidden renderer/generic safe-line validation incompatibilities; general English recognition incomplete.'],'pre_existing':['T05 stock jab, incomplete physical actions, stew/refusal/pointer defects, portal exception and unrelated KeyErrors remain deferred.']},
 'missing_concepts':['No missing authority for these three closed inspections; no general semantic completeness claim.'],
 'does_not_prove':['Repair completion, broad playability, live-model frequency, independent generalization, full-suite acceptance or later world corruption.'],
 'recommended_next_step':'Exactly one next action: implement pre-seal closed-surface inspection outcome projection under NEXT_STEP_DECISION acceptance criteria. Stop after audit; do not implement automatically.',
 'self_contained_review_test':'Reopen exact dated/stable ZIP; verify milestone, nine reports, included hashes/canonical bytes, evidence manifest, NEXT_SESSION/historical suffix and baseline/prior archive preservation. External final seal retained.',
 'primary_report':RP+'SUMMARY.md','supporting_files':[{'path':p,'role':'audit_evidence' if p.startswith('artifacts/') else 'source_or_authority','why':'Supports the claim-acceptance finding, negative controls, bounded recommendation or provenance.','behavioral_evidence':p.endswith(('three_case_trace.json','trace_summary.json','test_results.json','negative_controls.json','related_publication.json')),'human_review_required':False} for p in supports if p!=RP+'SUMMARY.md'],
 'max_file_bytes':40*1024*1024}
 save('review_handoff.json',config)
 requested=set(supports)
 inventory=[]
 for p in sorted(O.rglob('*')):
  if p.is_file() and 'review_export' not in p.parts and p.name not in {'evidence_manifest.json','archive_verification.json','archive_contents.txt','archive_sha256.txt','files_created.json','final_git_status.txt','handoff_generation_output.txt'}:
   rel=p.relative_to(R).as_posix()
   inventory.append({'path':rel,'sha256':sha(p),'bytes':p.stat().st_size,'packaged':rel in requested,'reason':'selected compact review evidence' if rel in requested else 'large raw capture retained locally; compact derived evidence packaged'})
 for rel in report_paths:
  p=R/rel;inventory.append({'path':rel,'sha256':sha(p),'bytes':p.stat().st_size,'packaged':True,'reason':'required report'})
 save('evidence_manifest.json',{'milestone':ID,'source_manifest_identity':m['manifest_identity_sha256'],'entries':inventory,'self_excluded_for_no_circular_hash':True,'external_final_seal_files':['archive_verification.json','archive_sha256.txt','archive_contents.txt','files_created.json','final_git_status.txt','handoff_generation_output.txt'],'large_baseline_archive_duplicated':False})
 print(json.dumps({'prepared':True,'reports':len(report_paths),'support_paths':len(supports),'manifest_entries':len(inventory),'baseline_files':len(m['files'])}))
 sys.exit()

export=O/'review_export'
for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip'):
 temp=R/'handoff'/(ID+'_'+name+'.tmp')
 shutil.copyfile(export/name,temp);os.replace(temp,R/'handoff'/name)
stamp=datetime.now(timezone(timedelta(hours=-5),'America/New_York EST')).strftime('%Y%m%d-%H%M%S')
archive=R/'handoff'/f'CURRENT_REVIEW({stamp}).zip';assert not archive.exists()
shutil.copyfile(R/'handoff/CURRENT_REVIEW.zip',archive)
reports=['SUMMARY.md','PIPELINE_TRACE.md','CLAIM_CLASSIFICATION.md','THREE_CASE_ANALYSIS.md','AUTHORITY_GAP.md','NEGATIVE_CONTROLS.md','IMPLEMENTATION_OPTIONS.md','NEXT_STEP_DECISION.md','INTEGRITY.md']
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 names=z.namelist();summary=z.read('CURRENT_REVIEW.md').decode()
 assert 'Identifier: `'+ID+'`' in summary and '358 passed' in summary
 assert all('support/'+RP+n in names for n in reports)
 manifest=json.loads(z.read('REVIEW_MANIFEST.json'));assert manifest['campaign_id']==ID
 assert all(r['reason'].startswith('duplicate content of ') for r in manifest['omitted_artifacts']),manifest['omitted_artifacts']
 checked=[]
 for row in manifest['included_files']:
  data=z.read(row['bundle_path'])
  if row.get('sha256'): assert hashlib.sha256(data).hexdigest()==row['sha256'],row
  if row.get('canonical_source_path'):
   assert data==(R/row['canonical_source_path']).read_bytes(),row
   checked.append(row['canonical_source_path'])
 current=z.read('support/docs/NEXT_SESSION.md')
 assert current==(R/'docs/NEXT_SESSION.md').read_bytes()
 assert current.endswith((O/'entry_next_session.md').read_bytes())
 assert ID.encode() in current[:500]
 em=json.loads(z.read('support/'+AP+'evidence_manifest.json'));assert em['milestone']==ID
 for row in em['entries']:
  assert sha(R/row['path'])==row['sha256'],row['path']
  if row['packaged']:
   member='support/'+row['path']
   if member in names: assert hashlib.sha256(z.read(member)).hexdigest()==row['sha256']
   else: assert any(v.get('sha256')==row['sha256'] and v['reason'].startswith('duplicate content of ') for v in manifest['omitted_artifacts']),row
 results=json.loads(z.read('support/'+AP+'test_results.json'))
 assert results['counts']=={'tests':381,'passed':358,'failed':23,'errors':0,'skipped':0}
 assert all(results['comparison'].values())
 # Generator writes its stable Markdown with Windows text newlines; ZIP uses LF.
 assert z.read('CURRENT_REVIEW.md').decode().replace('\r\n','\n')==(R/'handoff/CURRENT_REVIEW.md').read_text(encoding='utf-8')
 assert json.loads(z.read('REVIEW_MANIFEST.json'))==read(R/'handoff/REVIEW_MANIFEST.json')
 assert not any(p.lower().endswith('.zip') or '/.git/' in p.lower() or '/.env' in p.lower() for p in names)
assert sha(archive)==sha(R/'handoff/CURRENT_REVIEW.zip')
with zipfile.ZipFile(R/'handoff/CURRENT_REVIEW.zip') as z:assert z.testzip() is None and z.namelist()==names
m=protected_check()
for p,h in read(O/'prior_dated_archives.json').items():assert sha(R/p)==h,p
for p in ('execution_integrity.json','authority/execution_integrity.json'):
 i=read(O/p);assert not i['changed'] and not i['added'] and not i['network_attempts_blocked'] and i['live_provider_calls']==0
assert read(O/'probe_integrity.json')['all_inputs_unchanged']
verify={'verdict':'PASS','milestone':ID,'archive_path':str(archive),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'member_count':len(names),'reports_verified':reports,'canonical_files_byte_verified':checked,'evidence_manifest_entries_verified':len(em['entries']),'stable_triplet_matches':True,'generated_summary_comparison':'LF/CRLF presentation normalization; canonical support checked byte-for-byte','historical_handoff_bytes_preserved':True,'source_manifest_files_unchanged':len(m['files']),'prior_dated_archives_unchanged':len(read(O/'prior_dated_archives.json')),'omissions':manifest['omitted_artifacts'],'live_provider_calls':0,'tests':results['counts']}
save('archive_verification.json',verify)
(O/'archive_contents.txt').write_text('\n'.join(names)+'\n')
(O/'archive_sha256.txt').write_text(str(archive)+'\nSHA-256 '+sha(archive)+'\n')
(O/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=R))
save('files_created.json',{'milestone':ID,'created':[str(p.relative_to(R)) for base in (O,R/RP) for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[str(archive.relative_to(R))],'updated':['docs/NEXT_SESSION.md','handoff/CURRENT_REVIEW.md','handoff/REVIEW_MANIFEST.json','handoff/CURRENT_REVIEW.zip'],'external_seal_inventory_self_excluded':True})
print(json.dumps({k:verify[k] for k in ('verdict','archive_path','archive_sha256','archive_bytes','member_count','source_manifest_files_unchanged','prior_dated_archives_unchanged')}))
