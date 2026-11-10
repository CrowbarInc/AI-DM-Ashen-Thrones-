"""Assemble bounded evidence and standard review inputs from completed checks."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
MID='pr_play_object_marking_inspection'
REPORT=ROOT/'development/campaigns/product_realization'/MID
REPORT.mkdir(parents=True,exist_ok=True)
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=True),encoding='utf-8')
def sha(raw): return hashlib.sha256(raw).hexdigest()
def summary(mode):
    tree=ET.parse(OUT/(mode+'_junit.xml')); rows=list(tree.iter('testcase'))
    failures={t.attrib['classname'].replace('.','/')+'.py::'+t.attrib['name']:t.find('failure').text
              for t in rows if t.find('failure') is not None}
    return dict(total=len(rows),passed=sum(not any(t.find(k) is not None for k in ('failure','error','skipped')) for t in rows),
        failed=len(failures),errors=len(list(tree.iter('error'))),skipped=len(list(tree.iter('skipped'))),
        failures=failures,command=read(mode+'_command.json'),execution=read(mode+'_execution.json'))
modes=['before_'+x for x in ('combined','marking','identity','inventory_snapshot','preservation')]
modes+=['after_'+x for x in ('combined','marking','identity','inventory_snapshot','preservation')]+['final_inspection','bounded_performance']
results={m:summary(m) for m in modes}
b,a=results['before_combined'],results['after_combined']
results['new_failures']=sorted(set(a['failures'])-set(b['failures']))
results['newly_passing']=sorted(set(b['failures'])-set(a['failures']))
assert not results['new_failures'],results['new_failures']
for name,row in results.items():
    if isinstance(row,dict) and 'errors' in row:
        assert row['errors']==row['skipped']==0
        if 'combined' not in name: assert row['failed']==0
results['live_provider_calls']=0
results['startup_note']='Initial launcher attempts used the unavailable Windows Python alias, then omitted repository site-packages. Both failed before test execution; corrected to the documented runtime and PYTHONPATH. No source change or provider call.'
write('regression_results.json',results)

def normalize(value):
    if isinstance(value,dict): return {k:normalize(v) for k,v in value.items() if k!='performance'}
    if isinstance(value,list): return [normalize(v) for v in value]
    if isinstance(value,str) and value.startswith('clue_text_digest:'): return 'clue_text_digest:PROCESS_LOCAL'
    return value
old=read('before_sequence.json')['turns'];new=read('after_sequence.json')['turns']
comparison=[]
for x,y in zip(old,new):
    publication=y['after']['session'].get('last_publication',{})
    prior=y['before']['session'].get('last_publication',{})
    pointer_ok=publication.get('visible')==y['visible'] or (y['id'] in ('T06','T12') and publication==prior)
    comparison.append(dict(turn=y['id'],before=x['visible'],after=y['visible'],
        text_equal=x['visible']==y['visible'],character_equal=x['after']['character']==y['after']['character'],
        scene_equal=x['after']['session']['active_scene_id']==y['after']['session']['active_scene_id'],
        resolution_equal=normalize(x['resolution'])==normalize(y['resolution']),
        no_implicit_identity_or_marking=all(not any(k in r for k in ('instance_id','markings')) for r in y['after']['character'].get('inventory',[]) if isinstance(r,dict)),
        publication_pointer_consistent=pointer_ok,publication=publication))
flags=('text_equal','character_equal','scene_equal','resolution_equal','no_implicit_identity_or_marking','publication_pointer_consistent')
assert len(comparison)==12 and all(all(r[k] for k in flags) for r in comparison)
write('twelve_turn_comparison.json',dict(turns=comparison,live_provider_calls=0,
    normalization='Only performance timings and existing process-local clue_text_digest values.'))
def selected(r):
    session=r['after']['session']
    return dict(id=r['id'],request=r['request'],visible=r['visible'],resolution=r['resolution'],
        character=r['after']['character'],session={k:session[k] for k in ('campaign_run_id','active_scene_id','scene_state','scene_runtime','clue_knowledge','last_publication','turn_counter') if k in session})
write('twelve_turn_state_evidence.json',dict(before=[selected(r) for r in old],after=[selected(r) for r in new]))

before=read('before_manifest.json')
after={p:sha((ROOT/p).read_bytes()) for p in before}
changed=sorted(p for p in before if before[p]!=after[p])
assert changed==['game/api.py','game/object_marking.py'],changed
added=['tests/test_object_marking_inspection.py']
after.update({p:sha((ROOT/p).read_bytes()) for p in added})
write('after_manifest.json',after)
write('source_changes.json',dict(changed_existing=changed,added=added,protected_files=len(before),
    frozen_fixture_changes=[],production_data_changes=[],unchanged_protected_files=len(before)-len(changed)))
diff=''
for name in changed:
    raw=(OUT/'entry_sources'/name).read_bytes();assert sha(raw)==before[name]
    diff+=''.join(difflib.unified_diff(raw.decode().replace('\r\n','\n').splitlines(True),(ROOT/name).read_text(encoding='utf-8').splitlines(True),
        fromfile='before/'+name,tofile='after/'+name))
(OUT/'production.diff').write_text(diff,encoding='utf-8')
write('milestone_identity.json',dict(milestone=MID,date='2026-11-09',verdict='A/PASS',live_provider_calls=0))
identity=read('entry_identity.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==identity['head']
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()==identity['branch']

def totals(r): return f"{r['passed']} passed / {r['failed']} failed / {r['errors']} errors / {r['skipped']} skipped ({r['total']} tests)"
reg=f"Combined before: {totals(b)}. After: {totals(a)}. New failures: {results['new_failures']}; newly passing: {results['newly_passing']}."
n=results['final_inspection']['passed']
focused=f"{n} inspection/removal tests passed. Separate predecessor controls: 76 marking/atomic, 52 identity, 50 inventory/snapshot and 143 preservation passed before and after."
limitations=('Single authoritative character inventory; single-process FIFO and persistence guard. No multi-process lost-update protection, '
    'multi-file crash transaction or global exactly-once across snapshot rollback. File fsync is required; Windows directory sync remains '
    'best effort/unavailable. Existing permission-bit preservation does not promise custom Windows ACL/ownership/inode metadata preservation. '
    'Authorization and prerequisite references are trusted internal assertions, not public authentication or physical adjudication. '
    'Receipts grow O(committed operations) for the saved timeline lifetime; validation scans this character inventory/receipts, not the world. '
    'No player observation policy, natural-language inspection/removal, T06 completion, equipment/material inference, transfer or crafting. '
    'No full-suite, held-out generalization, live-model or gameplay-improvement claim.')
next_step=('Exactly one recommended next milestone: `pr_play_object_marking_disclosure_policy` — define and test the disclosure/access contract '
    'for a future player observation projection over internal marking inspection. Do not activate player routing or begin automatically.')
failure_list='\n'.join('- '+k for k in b['failures'])
commands='\n\n'.join('### '+name+'\n\n```text\n'+row['command']['executable']+'\n'+json.dumps(row['command']['args'])+'\n```\n\n'+totals(row)
    for name,row in results.items() if isinstance(row,dict) and 'command' in row)
timeline=read('inspection_removal_timeline.json')
assert [len(s['inspection']['markings']) for s in timeline['snapshots']]==[0,2,1]
assert timeline['removal_result']==timeline['replay']
assert timeline['before']['inventory'][1]==timeline['after']['inventory'][1]
assert all(timeline['before'][ 'object_marking_receipts']['entries'][k]==timeline['after']['object_marking_receipts']['entries'][k]
           for k in timeline['before']['object_marking_receipts']['entries'])
performance=read('performance.json')
reports={
'SUMMARY':f'**A/PASS for bounded internal inspection and ID-specific marking removal.**\n\n{focused}\n\n{reg}\n\nCurrent inspection returns active object state, never receipt history. Removal and its receipt commit through the existing API state-authority coordinator and atomic character save. Identity unchanged; successful removal advances revision once; exact replay returns the original receipt without allocation/save. Full two-object, two-add, inspect/remove/reinspect/reload/S0-S1-S2 sequence verified. All twelve player-visible turns unchanged; live provider calls 0.\n\n'+limitations,
'BASELINE':f"Branch `{identity['branch']}`; HEAD `{identity['head']}`. Entry dirty status captured verbatim in entry_git_status.txt; source/test/data hashes in before_manifest.json; authenticated production entry bytes in entry_sources/. No reset, clean, stash, revert, historical checkout, commit or push.\n\nBefore production edits: {totals(b)}; separate 76/52/50/143 predecessor controls passed. Initial launcher configuration failures occurred before tests and were corrected. Exact failing identities:\n\n{failure_list}\n\nActual predecessor code cross-checked every add receipt against an active marking and refused orphan receipts. Consequently deletion alone would invalidate all later requests. The compatible history validator now also verifies removed marking evidence in removal receipts; original add receipt shapes/values remain intact. Initial identity revision is 0, confirmed by contract and timeline. Existing storage loaders bootstrap missing files; inspection checks existing files first.",
'INSPECTION_CONTRACT':'''Internal Python APIs: game.object_marking.inspect_markings(character, request), and game.api.inspect_inventory_object_markings(request) for current authoritative disk state. No HTTP route. Exact v1 request fields: version=1, operation=inspect_markings, campaign_run_id, character_id, instance_id (canonical UUID4), context={caller_id: bounded nonblank string, purpose: authoritative_state}. The API validates current session campaign; service validates character ID and identity provenance, singleton shape and all declared identities/receipt consistency. Context explicitly separates internal reads from player observation; it is not an authentication boundary.

Success: status=inspected, version, campaign_run_id, character_id, instance_id, current revision, detached markings list. Each active record supplies modification_id, exact content, source, authorization/evidence, request lineage and applied revision. Empty active collection returns []. Repeated reads are equivalent and detached. Historical removed records never populate this collection.

Refusals use status=rejected/error. Invalid or missing identity/request/context, absent/ambiguous target, malformed marking/receipt data, duplicate IDs, cross-scope state and unsupported legacy records fail closed. No repair or migration. Missing runtime files return missing_runtime_state without bootstrap. Invalid character JSON returns invalid_runtime_state. No allocation, revision, receipt, metadata/order change, persistence, provider call, equipment inference or conversational reconstruction. Existing lane read lock and persistence guard supply a coherent in-process read. Full internal provenance must not be returned directly to players.''',
'REMOVAL_CONTRACT':'''Internal game.api.remove_inventory_object_marking(request) delegates to the same coordinator used by add_inventory_object_marking; pure staging is game.object_marking.prepare_removal. No new writer or state owner. Exact v1 request fields: version, operation=remove_marking, campaign_run_id, character_id, instance_id, modification_id, request_id, request_digest, expected_revision, authorization. Identity is canonical UUID4; revision is a nonnegative integer (bool/string/missing invalid). Canonical SHA-256 covers every semantic field including operation and authorization, excluding request_digest only.

Authorization has exact fields caller_id, decision_id, mechanics=not_applicable, preconditions with bounded positive evidence references for target_exists, accessible, rights, marking_exists, removable, capability. These are trusted internal assertions. No physical cleaning or skill mechanics inferred.

Validate request shape/evidence/digest and authoritative campaign; resolve one existing singleton; validate current/history consistency; look up durable receipt; exact replay returns original result before checking current revision or active marking presence. New request checks expected revision, then resolves exact active modification_id. Missing mark refuses missing_marking, stale revision refuses stale_revision; rejection does not mutate. Stage detached removal of this ID only, revision+1 and compact removal receipt together. Existing game.api WORLD_STATE guard, ordered_turn without cache key, persistence guard, runtime_commit_scope and save_character coordinate one atomic character replacement. Return committed/applied result only after successful save; errors raise and rollback is verified. Same text on other marking IDs survives.''',
'IDEMPOTENCY_VERIFICATION':'''Exact replay returns the original committed result after reload, after later revision advancement, and after restoring the post-removal snapshot; no save/allocation/receipt/revision change. Conflicting payload with the same ID returns conflicting_request. Both add-to-remove and remove-to-add request-ID reuse refuse; operation participates in canonical digest. New ID against an absent marking returns missing_marking at the current revision, not replay. Historical add retries remain valid after removal. Concurrent identical removals produce one revision/receipt. Removed UUIDs cannot be allocated to a new add. Evidence: idempotency_controls.json, inspection_removal_timeline.json, final_inspection_junit.xml. Snapshot rollback can remove the durable key and is a timeline change, not global exactly-once.''',
'STATE_HISTORY_SEPARATION':'''Current state remains solely inventory[index].markings. Successful removal physically removes one entry from that active collection; empty list is valid. The existing character.object_marking_receipts version-1 ledger remains the only durable idempotency/history host. Add receipts remain exactly intact. A removal receipt extends the existing result with operation=remove_marking, its canonical request and removed_marking. The latter is one bounded marking record, not an object snapshot or a second object-state ledger.

This retained marking evidence is required for compatibility with predecessor bidirectional validation: old add receipts contain no content/authorization, so deleting the only semantic evidence would make their digest unverifiable. Retaining one removed record enables the existing digest/provenance/integrity checks without rewriting old receipts or retaining tombstones in the bounded active collection. Validator checks every active/historical add against its unchanged receipt, every removal against its request/target/revisions and removed record, unique IDs/request keys/revision events, and complete receipt coverage. Resurrection, dropped removal receipts, tampered old add receipts and malformed history fail closed. Inspection derives its list exclusively from active state, while history validation may refuse corruption.

S0 restores zero active marks, revision 0, zero receipts; S1 restores two, revision 2, two add receipts; S2 restores one, revision 3, two add plus one removal receipts. No latest external ledger is consulted. Captured timeline semantics and pre-existing multi-file restore limitations remain unchanged.''',
'IMPLEMENTATION':'''Production files changed: game/object_marking.py and game/api.py only. object_marking adds inspect_markings, prepare_removal, exact request/authorization schemas, common target validation and compatible current/history validation. Add collision detection includes removed IDs in durable history. api adds internal inspection/removal wrappers and factors the existing marking coordinator so additions/removals share serialization, authority, rollback and atomic save. Storage, state-authority registry, identity owner, routing, parser, prompt, noncombat results, publication, T04/T05/T06 and ruleset code are unchanged.

Validation: tests/test_object_marking_inspection.py. Cycle-local runner reuses exact predecessor regression selections and unchanged twelve-turn HTTP harness with networking/provider guards and isolated runtime state. Production.diff compares authenticated entry bytes, not HEAD, preserving unrelated dirty work. service_extension.txt is the cycle-local construction input; shipped code is game/object_marking.py. No general mutation engine, campaign registry, alternate ledger, public endpoint or provider call introduced.''',
'PERSISTENCE_VERIFICATION':'''inspection_removal_timeline.json records actual storage loads, two additions, removal, explicit save/reload, original/add/removal receipts, stable identity, unrelated-object equality, revisions and replay. Real create_snapshot/load_snapshot restore S0/S1/S2 with current counts 0/2/1 and revisions 0/2/3. The original add receipts survive removal unchanged; removal receipt survives save/reload and S2 restoration. Replay is checked after later successful add at revision 4.

Four removal-specific failures (save, replace, fsync, exception after completed save) raise without success and preserve exact pre-operation character bytes; retry commits once at revision 3. Evidence removal_failure_*.json includes inspection and no stranded temporary files. Existing atomic-persistence tests additionally cover serialization, creation, partial write, flush, file sync, replace and post-replace directory-sync limitations. Storage writer is unchanged. New state and removal receipt share the same JSON save, never separate writes. Rollback remains exception-oriented; failure to restore exact character bytes raises existing RuntimePersistenceCoherencyError rather than completion.\n\n'''+limitations,
'NEGATIVE_CONTROLS':f'''{n} focused tests cover empty/one/multiple/post-removal reads, repeated detached reads, malformed/missing/duplicate identities, legacy/partial/string records, malformed markings and orphan/corrupt receipts. Missing runtime files do not bootstrap. Persistence and UUID functions are replaced with forbidden callbacks during reads and replay. Request, revision, marking-ID, scope, authorization and every prerequisite failure refuse with unchanged durable bytes. Content-identical marks are selected by identity. New request against removed mark does not become replay. Authority guard denial prevents commit. Concurrent identical requests commit once. Historical resurrection/dropped receipt/tampered add receipt refuse. Save failure controls and opaque extension preservation are explicit. Internal helpers are absent from FastAPI routes; twelve-turn replay verifies no natural-language activation, implicit migration, marking, inspection or removal.\n\nExact parameterized identities and outcomes: final_inspection_junit.xml; requests/results/timeline and failure artifacts provide machine-readable evidence.''',
'REGRESSION_RESULTS':reg+'\n\n'+focused+'\n\nSame selections compared before/after; no totals from overlapping suites added. Combined covers travel/immutable publication and baseline admission/narration controls; preservation selection covers T04/T05/T06, closed inspection, physical persistence and state authority. No live provider calls; no external network attempts in completed runners. Full suite not run. Exact baseline failure identities:\n\n'+failure_list+'\n\nExact commands (Python executable and argument arrays), totals, elapsed times and complete failure text are also in regression_results.json and *_command.json / *_execution.json.\n\n'+commands,
'TWELVE_TURN_COMPARISON':'Unchanged provider-free twelve-turn HTTP harness run before and after. All visible strings, full character states, active scenes and normalized resolutions match; all publication pointers consistent, including prior-pointer retention for unsupported T06/T12. No implicit identity assignment, marking, inspection publication or removal. Provider calls 0; no extra provider work or retries. No gameplay completion claim.\n\n'+'\n\n'.join(r['turn']+': unchanged — '+r['after'] for r in comparison)+'\n\nEvidence: twelve_turn_comparison.json, twelve_turn_state_evidence.json and runner logs. Only timings and existing process-local clue digests are normalized.',
'RULESET_PORTABILITY':'''Parameterized real character save/remove/reload/inspect controls preserve opaque extensions for pf1e@1 (AC/damage), rules_light@1 (tags), and scifi@1 (battery/caliber). Unknown legacy/nested fields, provenance, ID, other objects and character fields remain unchanged. Only selected markings/revision and durable receipts change. No ruleset branching or extension interpretation in service. Evidence portability_*.json and focused JUnit. Core operates on identity, active state, revision, trusted authorization and receipts. Physical feasibility and mechanics remain outside scope; no alternate ruleset runtime is claimed.''',
'PERFORMANCE':'Small two-object fixture; 50 pure read/validation samples and 10 save/reload/commit samples. Host micro-measurement only, not a broad benchmark. Commit measurements restore controlled fixture state between samples. A separate single-test measurement run followed completion of background regressions to avoid their disk contention; exact command/results in bounded_performance_* artifacts.\n\n```json\n'+json.dumps(performance,indent=2)+'\n```\n\nRemoval receipt retains one bounded marking to validate historical add evidence. Net compact character growth accounts for moving the marking out of active state. No prompt projection changes: receipts/markings remain outside selected prompt character fields. No tokens, provider calls, retries, world scans or inventory-wide model classification. Work is O(this inventory and retained receipts), not O(world/conversation).',
'NEXT_STEP_DECISION':'Recommend A/PASS for this bounded internal capability. The two-object original reproduction, authored negative variations, durable timelines and existing regressions are verified; independent held-out or broad gameplay generalization is not claimed.\n\n'+next_step+'\n\n'+limitations,
'INTEGRITY':f"Branch/HEAD unchanged: {identity['branch']} / {identity['head']}. Entry dirty status, full protected source/test/data hashes and production entry bytes captured before modification. Only game/api.py and game/object_marking.py differ among {len(before)} protected files; one new test file. Frozen fixtures and production data are byte-identical. Incremental diff is authenticated against entry hashes, excluding prior dirty changes. Existing handoff is retained as entry_current_review.md; NEXT_SESSION is prepended with its entire prior bytes retained as suffix. No prohibited worktree operations, commits or pushes.\n\nFifteen canonical reports, focused tests, source/evidence manifests and explicit review inputs are generated. Standard handoff generator builds fresh stable/history/dated ZIPs. Independent reopen verifies CRC, milestone, canonical/evidence hashes, inspection/removal/reload/replay/snapshots/faults/portability/regression/twelve-turn evidence and historical handoff suffix. Archive hash and reopen verification are external final seals to avoid circular hashing. Exact final path/hash are in archive_sha256.txt / archive_verification.json. Live provider calls 0.\n\n"+limitations
}
for name,body in reports.items():
    (REPORT/(name+'.md')).write_text('# '+name.replace('_',' ').title()+'\n\nMilestone: `'+MID+'`. Date: 2026-11-09.\n\n'+body+'\n',encoding='utf-8')
prior=(OUT/'entry_next_session.md').read_bytes()
intro=f'''# NEXT_SESSION — PR-PLAY Object Marking Inspection and Removal (2026-11-09)

**A/PASS for bounded internal capabilities.** Milestone `{MID}`. Branch {identity['branch']}; HEAD {identity['head']}. Dirty work preserved; no commits/pushes; live provider calls **0**.

Internal read-only inspection returns active markings only, without migration/save. Trusted remove_marking selects one UUID, checks scope/authorization/revision/digest, removes only that mark and atomically commits revision+1/receipt through existing authority. Historical add receipts preserved; removal receipt retains one bounded removed record for historical integrity. Exact reload/later-revision replay returns original result without save; conflicts across operations reject. S0/S1/S2 restore 0/2/1 active marks and corresponding revisions/receipts. All twelve visible turns unchanged; T06 remains unsupported.

{focused}

{reg}

{next_step}

{limitations}

Minimum reading: development/campaigns/product_realization/{MID}/SUMMARY.md, INSPECTION_CONTRACT.md, REMOVAL_CONTRACT.md, STATE_HISTORY_SEPARATION.md, REGRESSION_RESULTS.md, NEXT_STEP_DECISION.md and INTEGRITY.md. Evidence: artifacts/{MID}/inspection_removal_timeline.json, idempotency_controls.json, removal_failure_*.json, portability_*.json, regression_results.json, twelve_turn_comparison.json, source_changes.json. Review: handoff/CURRENT_REVIEW.md. Fresh dated archive/hash/reopen record: archive_sha256.txt and archive_verification.json.

---

'''
(ROOT/'docs/NEXT_SESSION.md').write_bytes(intro.encode('utf-8')+prior)
assert (ROOT/'docs/NEXT_SESSION.md').read_bytes().endswith(prior)
(OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short']))
# Explicit, bounded review inputs. Redundant large raw HTTP dumps remain local;
# selected full state and turn comparisons are packaged instead.
artifact_names=['entry_identity.json','entry_git_status.txt','entry_next_session.md','entry_current_review.md',
    'before_manifest.json','after_manifest.json','source_changes.json','production.diff','milestone_identity.json',
    'inspection_removal_timeline.json','idempotency_controls.json','performance.json','regression_results.json',
    'twelve_turn_comparison.json','twelve_turn_state_evidence.json','final_git_status.txt',
    'run_checks.py','finalize.py','seal_review.py','before_sequence.log','after_sequence.log']
artifact_names += [p.name for p in OUT.glob('removal_failure_*.json')]
artifact_names += [p.name for p in OUT.glob('portability_*.json')]
for mode in modes:
    artifact_names += [mode+s for s in ('_command.json','_execution.json','_junit.xml','.log')]
support=[p.relative_to(ROOT).as_posix() for p in sorted(REPORT.glob('*.md'))]
support += ['docs/NEXT_SESSION.md','docs/review_handoff_standard.md','docs/state_authority_model.md',
    'game/api.py','game/object_marking.py','game/object_instances.py','game/storage.py',
    'tests/test_object_marking_inspection.py','tests/test_object_marking.py','tests/test_atomic_character_save.py',
    'tests/test_object_instances.py','tests/helpers/storage_isolation.py',
    'tests/pr_play_79df3_harness.py']
support += [(OUT/name).relative_to(ROOT).as_posix() for name in artifact_names]
support += [(OUT/'entry_sources'/name).relative_to(ROOT).as_posix() for name in changed]
write('files_created.json',dict(reports=[p.relative_to(ROOT).as_posix() for p in sorted(REPORT.glob('*.md'))],
    tests=added,artifact_directory=OUT.relative_to(ROOT).as_posix(),artifacts=artifact_names,
    review_outputs=['handoff/CURRENT_REVIEW.md','handoff/REVIEW_MANIFEST.json','handoff/CURRENT_REVIEW.zip','handoff/history/'+MID]))
support.append((OUT/'files_created.json').relative_to(ROOT).as_posix())
write('evidence_manifest.json',dict(milestone=MID,files=[dict(path=p,sha256=sha((ROOT/p).read_bytes()),bytes=(ROOT/p).stat().st_size) for p in support]))
support.append((OUT/'evidence_manifest.json').relative_to(ROOT).as_posix())
config=dict(campaign_id=MID,campaign_name='PR-PLAY — Object Marking Inspection and Removal',campaign_date='2026-11-09',
    purpose='Bounded production implementation, current/history separation, atomic persistence and regression verification',
    objective_status='A/PASS — bounded internal inspection/removal',executive_summary=reports['SUMMARY'],
    changes=dict(production=changed,validation=[focused],tooling=['Cycle-local provider-free runner, evidence assembly and archive verification.'],
        documentation=['15 reports; NEXT_SESSION prepended with historical bytes preserved.'],generated_artifacts=['Evidence and fresh standard review exports.']),
    testing=dict(focused=focused,broader=reg,full_suite='Not run.',runtime_validation='Real save/reload/S0-S1-S2 snapshots, atomic removal failure controls; twelve unchanged HTTP turns.',
        model_runtime_boundary='Zero live provider calls; provider/network guards and runtime isolation.',new_regressions=str(results['new_failures']),pre_existing_failures=failure_list),
    decisions_requiring_human_review=['No additional authorization required; review bounded internal capability.'],
    known_problems=dict(campaign_specific=[limitations],pre_existing=['Twenty established combined-selection failure identities; exact before/after traces retained.']),
    missing_concepts=['Player observation disclosure/access policy and later gameplay integration remain deferred.'],
    does_not_prove=['Public observation rights, T06 completion, physical erasing, broad gameplay generalization, full-suite or multi-process guarantees.'],
    recommended_next_step=next_step,self_contained_review_test='Independent fresh ZIP reopen, CRC/member and all canonical/evidence hashes; internal timeline, failures, portability, regression, twelve-turn and handoff claims.',
    primary_report=(REPORT/'SUMMARY.md').relative_to(ROOT).as_posix(),
    supporting_files=[dict(path=p,role='implementation_or_evidence',canonical=True,why='Explicit bounded inspection/removal implementation, evidence or handoff provenance.') for p in support])
write('review_handoff.json',config)
print(reg+'\n'+focused)
