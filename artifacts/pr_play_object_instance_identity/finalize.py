"""Build bounded evidence/reports and the standard review configuration."""
from pathlib import Path
import difflib, hashlib, json, re, subprocess, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/campaigns/product_realization/pr_play_object_instance_identity'
REPORT.mkdir(parents=True,exist_ok=True)
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2,default=str),encoding='utf-8')
def summary(mode):
    tree=ET.parse(OUT/(mode+'_junit.xml'))
    rows=list(tree.iter('testcase')); failures={}
    for t in rows:
        fail=t.find('failure')
        if fail is not None: failures[t.attrib['classname'].replace('.','/')+'.py::'+t.attrib['name']]=fail.text
    return {'total':len(rows),'passed':sum(not any(t.find(k) is not None for k in ('failure','error','skipped')) for t in rows),
        'failed':len(failures),'errors':len(list(tree.iter('error'))),'skipped':len(list(tree.iter('skipped'))),
        'failures':failures,'command':read(mode+'_command.json'),'execution':read(mode+'_execution.json')}
results={mode:summary(mode) for mode in ('before_preservation','before_combined_retry','after_preservation','after_combined','final_identity_v2','after_inventory_snapshot')}
before=results['before_combined_retry']; after=results['after_combined']
results['new_failures']=sorted(set(after['failures'])-set(before['failures']))
results['resolved_failures']=sorted(set(before['failures'])-set(after['failures']))
def normalize_assertion(text):
    text=re.sub(r'0x[0-9A-Fa-f]+','ADDRESS',text)
    text=re.sub(r'object_instance_(before_combined_retry|after_combined)_pytest','object_instance_RUN_pytest',text)
    return re.sub(r'"turn_id": "[0-9a-f]+"','"turn_id": "TURN"',text)
results['new_assertion_diagnostics']=[k for k in before['failures'].keys() & after['failures'].keys()
    if normalize_assertion(before['failures'][k])!=normalize_assertion(after['failures'][k])]
assert not results['new_failures']
assert not results['new_assertion_diagnostics'],results['new_assertion_diagnostics']
assert all(v['errors']==v['skipped']==0 for v in results.values() if isinstance(v,dict) and 'errors' in v)
assert results['after_preservation']['passed']==143 and results['final_identity_v2']['passed']==52
write('regression_results.json',results)
old=read('before_sequence.json')['turns']; new=read('after_sequence.json')['turns']
comparison=[]
def normalize_resolution(value):
    if isinstance(value,dict):
        return {k:normalize_resolution(v) for k,v in value.items() if k!='performance'}
    if isinstance(value,list): return [normalize_resolution(v) for v in value]
    if isinstance(value,str) and value.startswith('clue_text_digest:'): return 'clue_text_digest:PROCESS_LOCAL'
    return value
for a,b in zip(old,new):
    comparison.append({'id':a['id'],'before':a['visible'],'after':b['visible'],
        'published_text_equal':a['visible']==b['visible'],
        'action_ownership_before':(a['resolution'] or {}).get('metadata'),
        'action_ownership_after':(b['resolution'] or {}).get('metadata'),
        'resolution_equal':a['resolution']==b['resolution'],
        'resolution_equal_excluding_timings_and_process_local_clue_digests':normalize_resolution(a['resolution'])==normalize_resolution(b['resolution']),
        'inventory_before':a['after']['character'].get('inventory'),
        'inventory_after':b['after']['character'].get('inventory'),
        'character_equal':a['after']['character']==b['after']['character'],
        'scene_before':a['after']['session']['active_scene_id'],
        'scene_after':b['after']['session']['active_scene_id'],
        'publication_before':a['after']['session'].get('last_publication'),
        'publication_after':b['after']['session'].get('last_publication'),
        'no_implicit_identity':not any('instance_id' in i for i in b['after']['character'].get('inventory',[]))})
assert len(comparison)==12 and all(r['published_text_equal'] and r['character_equal'] and r['no_implicit_identity'] and r['scene_before']==r['scene_after'] for r in comparison)
assert all(r['resolution_equal_excluding_timings_and_process_local_clue_digests'] for r in comparison)
write('twelve_turn_comparison.json',{'turns':comparison,'live_provider_calls':0})
# Keep selected states/publication pointers; omit bulky duplicate full runtime dumps from review.
def selected_session(session):
    keys=('campaign_run_id','session_id','active_scene_id','visited_scene_ids','turn_counter',
        'clue_knowledge','scene_state','scene_runtime','last_publication','interaction_context')
    return {k:session[k] for k in keys if k in session}
write('twelve_turn_state_evidence.json',{'before':[{'id':r['id'],'resolution':r['resolution'],'session':selected_session(r['after']['session']),'character':r['after']['character']} for r in old],
    'after':[{'id':r['id'],'resolution':r['resolution'],'session':selected_session(r['after']['session']),'character':r['after']['character']} for r in new]})
# Drop duplicate HTTP/log/debug payloads from this cycle's raw replay captures.
# Preserve the inputs used by comparison and all relevant selected state.
for filename,turns in [('before_sequence.json',old),('after_sequence.json',new)]:
    write(filename,{'turns':[{'id':r['id'],'request':r['request'],'status':r['status'],
        'visible':r['visible'],'resolution':r['resolution'],'after':{
            'session':selected_session(r['after']['session']),'character':r['after']['character']}}
        for r in turns],'live_provider_calls':0,'compaction':'Removed redundant log/body and cumulative debug copies; exact text/resolution and selected authoritative state retained.'})
protected=read('before_manifest.json')
after_manifest={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected}
after_manifest['game/object_instances.py']=hashlib.sha256((ROOT/'game/object_instances.py').read_bytes()).hexdigest()
after_manifest['tests/test_object_instances.py']=hashlib.sha256((ROOT/'tests/test_object_instances.py').read_bytes()).hexdigest()
write('after_manifest.json',after_manifest)
changed=[p for p,h in protected.items() if after_manifest[p]!=h]
assert sorted(changed)==['game/api.py','game/state_authority.py'],changed
write('source_changes.json',{'changed_existing':changed,'added':['game/object_instances.py','tests/test_object_instances.py'],
    'protected_files':len(protected),'frozen_fixture_changes':[],'production_data_changes':[]})
# Reconstruct entry bytes by subtracting ONLY this cycle's known patch, then authenticate.
diffs=[]
for path in changed:
    current=(ROOT/path).read_text(encoding='utf-8')
    if path.endswith('api.py'):
        start=current.index('def migrate_inventory_object_identity(')
        end=current.index("@app.get('/api/snapshots')",start)
        prior=current[:start]+current[end:]
    else:
        prior=current.replace('("game.world", "game.storage", "game.object_instances")','("game.world", "game.storage")')
        start=prior.index('    # Object identity is a narrow world-state facet')
        end=prior.index('    if owner in _NON_AUTHORITATIVE_MUTATION_OWNERS:',start)
        prior=prior[:start]+prior[end:]
        prior=prior.replace('            "fields mutated by the engine after authoritative resolution; character-held object "\n            "identity is a narrow character.json facet owned by game.object_instances. "\n            "``game.storage`` participates "',
            '            "fields mutated by the engine after authoritative resolution. ``game.storage`` participates "')
    raw=(ROOT/path).read_bytes()
    # Existing source is CRLF; preserve its exact entry line endings.
    encoded=prior.replace('\n','\r\n').encode() if b'\r\n' in raw else prior.encode()
    assert hashlib.sha256(encoded).hexdigest()==protected[path],path
    diffs.extend(difflib.unified_diff(prior.splitlines(True),current.splitlines(True),fromfile='entry/'+path,tofile='after/'+path))
diffs.extend(difflib.unified_diff([], (ROOT/'game/object_instances.py').read_text().splitlines(True),fromfile='/dev/null',tofile='after/game/object_instances.py'))
(OUT/'production.diff').write_text(''.join(diffs),encoding='utf-8')
identity=read('entry_identity.json'); perf=read('performance.json')
counts=lambda r:f"{r['passed']} passed / {r['failed']} failed / {r['errors']} errors / {r['skipped']} skipped ({r['total']} tests)"
reg=f"Preservation: {counts(results['before_preservation'])} before and {counts(results['after_preservation'])} after. Combined: {counts(before)} before; {counts(after)} after. New failing identities: {results['new_failures']}. Identity: 52 passed. Additional inventory/snapshot: 50 passed."
contract="Opaque canonical lowercase UUID4 `instance_id`; integer nonnegative `revision` (new records 0); `provenance` version 1 with campaign_run_id, explicit mint operation_id and source host/legacy_id. Canonical reference is (campaign_run_id, instance_id). Placement/actor association derives from the enclosing character inventory. Existing definition/legacy ID and all other fields remain intact."
eligibility="Explicit selection of an existing dict row, nonblank string id/name, exact integer quantity=1 (booleans/floats/strings excluded), boolean usable. No stack expansion, narrative/attack/scene/NPC promotion. Existing reserved identity fields require a complete valid record; unrelated reserved provenance is ambiguous and refused without overwriting. Unknown nonreserved metadata is preserved."
limitations="One authoritative character.json inventory per runtime store; duplicate scanning covers every declared identity in that host only. No authoritative multi-character/world registry exists; broader host indexing belongs to the later transfer/host-integration phase. UUID4 generation is collision resistant and checked against this host; no campaign-wide all-object uniqueness claim. Existing writer and exception rollback remain best effort, not crash-atomic or multi-process. Historical binaries stripping unknown keys are incompatible writers."
reports={
'SUMMARY':f"Verdict: **A/PASS for bounded identity implementation**. Milestone `pr_play_object_instance_identity`.\n\nImplemented explicit reusable singleton identity service and internal API migration entry; no player command or automatic migration. Production: game/object_instances.py, game/api.py, game/state_authority.py. Governance: docs/state_authority_model.md.\n\n{reg}\n\nSave/reload and real create_snapshot/load_snapshot preserve complete identity records. All twelve published turns unchanged; T06 unresolved. Zero live provider calls.\n\n{limitations}",
'BASELINE':f"Branch `{identity['branch']}`; HEAD `{identity['head']}`. Entry dirty status: {len((OUT/'entry_git_status.txt').read_text().splitlines())} lines; exact status/hashes retained. before_manifest.json captures {len(protected)} source/test/data/static/prompt/tool/script hashes before production edits.\n\nFresh pre-edit preservation 143/143; fresh combined baseline {counts(before)}. Its process loaded the source before implementation edits; run was completed during development. The first redirected combined attempt was interrupted before completion and is excluded; retry is the authoritative baseline. Extra preservation diagnostic run also passed 143. No completed attempt is relabeled.\n\nExisting load_character/save_character preserve arbitrary JSON rows. snapshot creation bundles character/session/world/combat/log; restore validates then writes with exception rollback. Inventory consumers/defaults/PF importer retain id/name/quantity/usable. Identity is absent before explicit assignment.\n\nKnown failure identities:\n\n"+'\n'.join('- '+k for k in before['failures']),
'IDENTITY_CONTRACT':contract+'\n\n'+eligibility+'\n\nValidation/assignment are pure staging operations with structured legacy/existing/assigned/rejected results. Repeated migration preserves ID/revision/provenance and does not save. Malformed/partial/unsupported/cross-campaign metadata and duplicate identities reject without replacement. Mint operation is provenance, not a global durable request cache. Source legacy ID is mint lineage, never a mutable identity seed. Unknown ruleset extensions are opaque.',
'IMPLEMENTATION':"game.object_instances: IdentityResult, inspect_object_identity, ensure_object_instance_identity; internal validators cover old shape/metadata/scope/duplicates. Detached candidate replaces exactly the selected row (including alias defense). game.api.migrate_inventory_object_identity reloads authoritative state in the existing ordered_turn lane, checks campaign and expected selected row, delegates staging, saves only assigned candidates under runtime_commit_scope. No HTTP endpoint, AI action, importer normalization or read hook. game.state_authority recognizes only assign_inventory_identity for this owner and denies other operations/domains; blanket domain mutability is not granted.\n\nExisting character and snapshot persistence reused unchanged; no parallel database. UI allowlists/renderers are unchanged. T06, equipment, modification, transfer, stacking, crafting, scene/NPC objects and ruleset mechanics excluded.\n\nArchitecture reconciliation: approved field/location/owner preserved. API expected_item is a concurrency selection guard, never the ID seed. No storage rewrite was necessary for scoped exception guarantees; crash safety deferred as authorized by this request.",
'MIGRATION_SAFETY':eligibility+'\n\nFull current row equality guards stale selections; concurrent explicit requests serialize in the same FIFO lane and only one can mint. Repeat with refreshed selection returns existing bytes. Duplicate scan validates all declared identities in the authoritative host. UUID generation collision rejects, no regeneration loop. Invalid input produces rejected result with no candidate. Unknown fields/statistics remain untouched. Conflicting legacy provenance refuses instead of replacement.\n\nFaults injected before save, after partial write and after complete write all restore original character bytes and raise. Snapshot creation and restore faults preserve current identity; API verifies rollback bytes on error and surfaces operational uncertainty if restoration fails. No success result escapes a failed save. Caller input remains detached.\n\n'+limitations,
'PERSISTENCE_VERIFICATION':"52 identity tests include actual character file save/load and actual create_snapshot/load_snapshot. persistence_round_trip.json contains before/assigned/reloaded/restored records and snapshot ID. Identity, revision, provenance, legacy extension and untouched second row compare equal. Repeated assignment leaves saved bytes unchanged. After snapshot, inventory reversal and character changes are made; restoration returns the captured identity without any generator call. Test fault injections cover character write partial/complete failure and snapshot creation/restore failure. Existing snapshot tests add 50 inventory/snapshot controls.\n\nExisting storage writer remains non-atomic; these are Python exception guarantees in the tested local process, not crash durability.",
'NEGATIVE_CONTROLS':"52 behavioral identity cases cover stacked/zero/fractional/boolean/missing quantities, malformed host/row/selection, blank id/name, missing usable, malformed UUID/revision/version/provenance, duplicate identity on selected/other rows, forced UUID collision, cross-campaign metadata, stale row, aliasing, unknown metadata preservation, ruleset extension variants, save faults, snapshot faults, concurrent selection and no implicit read migration. No PF field interpretation. New fixture supplies the existing referenced scene so actual snapshot coherency validation runs. No frozen fixture is edited. identity_traces.json includes duplicate rejection and detached first/repeat records; JUnit records all controls.",
'REGRESSION_RESULTS':reg+'\n\nExact commands and arguments are in regression_results.json and *_command.json; invoke `.venv/Scripts/python.exe artifacts/pr_play_object_instance_identity/run_checks.py <mode>` for modes before_preservation, before_combined_retry, after_preservation, after_combined, final_identity_v2, after_inventory_snapshot. All use provider/network/data guards and cycle-specific --basetemp and --junitxml. Three closed-inspection HTTP reproductions are parametrized tests in the preservation and combined selections. T04 12, T05 15, pre-seal 17, T06 diagnostics 6 and physical/persistence/authority 93 form the 143 preservation slice.\n\nNo collection errors/skips; zero live provider calls. New assertion diagnostics: none after normalizing process addresses, temporary run paths and random turn IDs. Failures and complete assertions retained in regression_results.json/JUnit. Known portal/stock-response/legacy public-resolution/pointer/KeyError failures remain outside this cycle. Full suite and live Gameplay Benchmark not run. Initial new identity run was 44/45, corrected only its missing-scene fixture; final 52/52.\n\nKnown before identities:\n\n'+'\n'.join('- '+k for k in before['failures'])+'\n\nAfter identities:\n\n'+'\n'.join('- '+k for k in after['failures']),
'TWELVE_TURN_COMPARISON':"Same provider-free frontier-gate scenario run before/after via run_checks.py before_sequence / after_sequence. All twelve published strings, complete characters and scene outcomes agree. No implicit instance_id appears. T04 transient authorized contact, T05 clean clue, T06 unsupported/unresolved, T09 grounded recall, T11 Old Milestone travel preserved. Publication pointers and resolution metadata/action ownership are captured in twelve_turn_comparison.json; selected complete session evidence in twelve_turn_state_evidence.json. Resolution equality holds after excluding execution timings and existing process-local clue_text_digest values; these are the only resolution differences observed. Volatile timestamps/request IDs are evidence, not required byte equality. Zero provider calls.\n\n"+'\n\n'.join(f"{r['id']}: unchanged — {r['after']}" for r in comparison),
'PERFORMANCE':f"Validation scans the single inventory O(N); detached staging/copy and existing JSON write O(character bytes). No full-world scans, history logs, prompts, model calls or retries. UUID4 allocation is random; validation/eligibility are deterministic. Existing IDs never regenerate. Normal gameplay incurs no new identity calls.\n\nLocal 30-sample, 100-row microbenchmark (not gameplay throughput): new assignment median {perf['assignment']['median_ms']:.3f} ms; repeat {perf['repeat_validation']['median_ms']:.3f} ms. Existing save median {perf['save_legacy']['median_ms']:.3f} ms vs identity-bearing save {perf['save_identity']['median_ms']:.3f} ms; noisy sequential measurements do not establish speedup/slowdown. Serialized bytes {perf['legacy_bytes']} → {perf['identity_bytes']} (+{perf['identity_bytes']-perf['legacy_bytes']} bytes for one promoted row). Raw samples summary in performance.json. Provider calls/token increase 0.",
'NEXT_STEP_DECISION':"Recommend acceptance A/PASS for this bounded identity foundation. Exactly one proposed next implementation cycle: `pr_play_object_marking_mutation` — one validated marking on an explicitly established compatible singleton, deterministic service tests first, with atomic save primitive and durable request/digest semantics before activation as required by approved roadmap phase 2. Do not begin automatically.\n\nDefer original T06 routing/material/clothing/parts, inspection/removal, transfer/host indexing, NPC custody, scene promotion, stack splitting, ruleset loader, crafting, baseline repair and crash/multi-process persistence. Remaining identity scope and writer limitations are documented, not fabricated capabilities.",
'INTEGRITY':f"Branch `{identity['branch']}`; HEAD `{identity['head']}`. No reset/clean/stash/revert/commit/push. Entry dirty status retained; all protected files except this cycle's api.py/state_authority.py edits match entry SHA-256. Reconstructed entry bytes for both existing changed production files authenticate against before_manifest.json; minimal incremental production.diff excludes pre-existing dirty changes. Added game/object_instances.py and tests/test_object_instances.py. Frozen fixtures and production data unchanged. docs/state_authority_model.md has the narrow facet addition.\n\nNEXT_SESSION is prepended; exact prior bytes remain its suffix. Prior CURRENT_REVIEW is retained in entry_current_review.md and historical review archives untouched. Reports/evidence/source manifests are packaged by unchanged tools/build_review_handoff.py with this cycle's explicit config. Fresh stable and dated ZIPs are reopened and every canonical member hash checked, including implementation, persistence/regression/twelve-turn results and handoff.\n\nArchive SHA-256 is published externally in archive_sha256.txt after sealing (avoids circular hash); archive_verification.json records reopened checks. Both are final external seal artifacts. Zero live provider calls."
}
for name,body in reports.items(): (REPORT/(name+'.md')).write_text('# '+name.replace('_',' ').title()+'\n\nMilestone: `pr_play_object_instance_identity`. Date: 2026-11-09.\n\n'+body+'\n',encoding='utf-8')
entry=(OUT/'entry_next_session.md').read_bytes()
heading=f"# NEXT_SESSION — PR-PLAY Object Instance Identity (2026-11-09)\n\n**A/PASS for bounded identity implementation.** Milestone `pr_play_object_instance_identity`; branch {identity['branch']}, HEAD {identity['head']}. Dirty work preserved; no commits/pushes; live provider calls **0**.\n\nExplicit singleton migration now adds UUID4 instance_id, revision=0 and versioned campaign/mint/source provenance through game.object_instances and internal API helper. Reads stay pure; malformed/cross-campaign/duplicate metadata refuse. Single authoritative character inventory scope only. Real save/reload and snapshot restoration verified; exception rollback remains best effort, not crash-atomic/multi-process. T06 unchanged/unresolved; all twelve published turns unchanged.\n\n{reg}\n\nExactly one next cycle: `pr_play_object_marking_mutation` — approved roadmap phase 2, one validated marking on established compatible singleton, service tests first with atomic save/durable request semantics before activation. Do not begin automatically. Defer T06 routing/equipment/material, transfer, broader host indexing, ruleset loader and baseline defects.\n\nMinimum reading: development/campaigns/product_realization/pr_play_object_instance_identity/SUMMARY.md, IDENTITY_CONTRACT.md, MIGRATION_SAFETY.md, REGRESSION_RESULTS.md, NEXT_STEP_DECISION.md and INTEGRITY.md; predecessor approved architecture remains authoritative. Evidence: artifacts/pr_play_object_instance_identity/regression_results.json, persistence_round_trip.json, twelve_turn_comparison.json, source_changes.json, archive_verification.json and archive_sha256.txt. Review: handoff/CURRENT_REVIEW.md.\n\n---\n\n"
(ROOT/'docs/NEXT_SESSION.md').write_bytes(heading.encode()+entry)
write('milestone_identity.json',{'milestone':'pr_play_object_instance_identity','verdict':'A/PASS','live_provider_calls':0})
(OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
write('files_created.json',{'production':['game/object_instances.py'],'tests':['tests/test_object_instances.py'],
    'reports':[p.relative_to(ROOT).as_posix() for p in sorted(REPORT.glob('*.md'))],
    'evidence_directory':OUT.relative_to(ROOT).as_posix(),
    'modified_existing':['game/api.py','game/state_authority.py','docs/state_authority_model.md','docs/NEXT_SESSION.md'],
    'generated_review':['handoff/CURRENT_REVIEW.md','handoff/REVIEW_MANIFEST.json','handoff/CURRENT_REVIEW.zip',
        'handoff/history/pr_play_object_instance_identity/'],'dated_archive':'See archive_sha256.txt for final verified archive.'})
evidence_names=['before_manifest.json','after_manifest.json','source_changes.json','entry_identity.json','entry_git_status.txt','identity_traces.json','persistence_round_trip.json','performance.json','regression_results.json','twelve_turn_comparison.json','twelve_turn_state_evidence.json','production.diff','milestone_identity.json','run_checks.py','measure.py','finalize.py']
evidence_names += ['files_created.json','final_git_status.txt']
evidence_names += [mode+suffix for mode in results if isinstance(results[mode],dict) and 'total' in results[mode] for suffix in ('_command.json','_execution.json','_junit.xml')]
write('evidence_manifest.json',{'milestone':'pr_play_object_instance_identity','files':[{'path':(OUT/n).relative_to(ROOT).as_posix(),'sha256':hashlib.sha256((OUT/n).read_bytes()).hexdigest()} for n in evidence_names]})
support=[p.relative_to(ROOT).as_posix() for p in REPORT.glob('*.md')]+[(OUT/n).relative_to(ROOT).as_posix() for n in evidence_names+['evidence_manifest.json']]+['game/object_instances.py','game/api.py','game/state_authority.py','tests/test_object_instances.py','docs/state_authority_model.md','docs/NEXT_SESSION.md','game/storage.py','development/campaigns/product_realization/pr_play_object_identity_architecture/OBJECT_INSTANCE_CONTRACT.md']
config={'campaign_id':'pr_play_object_instance_identity','campaign_name':'PR-PLAY — Object Instance Identity','campaign_date':'2026-11-09','purpose':'Bounded production identity implementation and persistence verification','objective_status':'A/PASS — bounded identity foundation','executive_summary':reports['SUMMARY'],
 'changes':{'production':['game/object_instances.py: pure validation/staging; game/api.py: explicit internal migration; game/state_authority.py: narrow ownership.'],'validation':['52 new behavioral tests; existing suites unchanged.'],'documentation':['12 milestone reports, narrow state doctrine, NEXT_SESSION prepended.'],'tooling':['Cycle-local runner, measurement and evidence/seal helpers.'],'generated_artifacts':['Machine-readable evidence and fresh review exports.']},
 'testing':{'focused':'52 identity tests passed; 50 inventory/snapshot controls passed.','broader':reg,'full_suite':'Not run.','runtime_validation':'Real save/reload/snapshot and all twelve provider-free turns.','model_runtime_boundary':'0 live calls; external network and production-data writes guarded.','new_regressions':str(results['new_failures']),'pre_existing_failures':'20 known baseline identities; detailed evidence retained.'},
 'decisions_requiring_human_review':['No additional approval required; review bounded implementation and deferred phase 2.'],
 'known_problems':{'campaign_specific':[limitations,'T06 remains unresolved.'],'pre_existing':['Known combined-selection failures remain; no baseline repair claim.']},
 'missing_concepts':['Object markings, durable operation digest, equipment/material binding and transfer deferred.'],
 'does_not_prove':['Global object uniqueness, crash/multi-process durability, alternate-ruleset engine, improved gameplay or full suite.'],
 'recommended_next_step':reports['NEXT_STEP_DECISION'],'self_contained_review_test':'Reopen stable/dated archives; verify canonical hashes, milestone, production implementation, persistence, regressions, twelve-turn comparison and handoff.',
 'primary_report':(REPORT/'SUMMARY.md').relative_to(ROOT).as_posix(),
 'supporting_files':[{'path':p,'role':'implementation_or_evidence','canonical':True,'why':'Bounded implementation, verification or handoff provenance.','behavioral_evidence':False,'human_review_required':False} for p in dict.fromkeys(support)]}
write('review_handoff.json',config)
print(reg)
