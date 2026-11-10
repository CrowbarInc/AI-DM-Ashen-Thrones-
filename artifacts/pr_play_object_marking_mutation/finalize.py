"""Assemble exact baseline comparisons, incremental diff and review inputs."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
MID='pr_play_object_marking_mutation'
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
modes=('before_combined','final_combined','before_preservation','after_preservation',
       'before_identity','final_identity','before_inventory_snapshot','final_inventory_snapshot','verified_marking')
results={m:summary(m) for m in modes}
b,a=results['before_combined'],results['final_combined']
results['new_failures']=sorted(set(a['failures'])-set(b['failures']))
results['resolved_failures']=sorted(set(b['failures'])-set(a['failures']))
def normalize_failure(text):
    text=re.sub(r'object_instance_(before_combined|final_combined)_pytest','object_instance_RUN_pytest',text)
    text=re.sub(r'0x[0-9A-Fa-f]+','ADDRESS',text)
    return re.sub(r'"turn_id": "[0-9a-f]+"','"turn_id": "TURN"',text)
results['changed_normalized_diagnostics']=[k for k in b['failures'] if k in a['failures']
    and normalize_failure(b['failures'][k])!=normalize_failure(a['failures'][k])]
results['diagnostic_variation_note']=('One pre-existing test_two_refusals_then_gameplay_advances failure stays at TestClient.__exit__/wait_shutdown: '
    'before RuntimeError(This portal is not running), after concurrent.futures.CancelledError. '
    'Exact traces retained; this is a teardown diagnostic variation at the same failing identity, not a claimed product repair. Causal origin unproven.')
assert results['changed_normalized_diagnostics']==['tests/test_pr_play_79df3_classification.py::test_two_refusals_then_gameplay_advances']
assert not results['new_failures']
assert all(v['errors']==v['skipped']==0 for v in results.values() if isinstance(v,dict) and 'errors' in v)
assert results['verified_marking']['passed']==76
assert results['after_preservation']['passed']==143
results['startup_failure']={'attempt':'after_combined','process_exit':1,
    'classification':'tooling/environment; Windows access violation in installed openai import; no JUnit result',
    'log':'after_combined.log','rerun':'final_combined','selection_unchanged':True}
write('regression_results.json',results)
write('atomic_save_traces.json',{'failures':[read('atomic_failure_'+s+'.json') for s in
    ('serialization','create','partial_write','flush','sync','replace')],
    'success':read('atomic_success.json'), 'postcommit':[read('atomic_postcommit_'+s+'.json') for s in ('open_directory','sync_directory')],
    'commit_boundary':'successful os.replace','directory_sync_on_windows':False})
write('milestone_identity.json',dict(milestone=MID,date='2026-11-09',verdict='A/PASS',live_provider_calls=0))

old=read('before_sequence.json')['turns']; new=read('final_sequence.json')['turns']
def normalize(value):
    if isinstance(value,dict): return {k:normalize(v) for k,v in value.items() if k!='performance'}
    if isinstance(value,list): return [normalize(v) for v in value]
    if isinstance(value,str) and value.startswith('clue_text_digest:'): return 'clue_text_digest:PROCESS_LOCAL'
    return value
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
assert len(comparison)==12 and all(all(r[k] for k in ('text_equal','character_equal','scene_equal','resolution_equal','no_implicit_identity_or_marking','publication_pointer_consistent')) for r in comparison)
write('twelve_turn_comparison.json',dict(turns=comparison,live_provider_calls=0,
    resolution_normalization='Ignore performance timings and existing process-local clue_text_digest values only.'))
# Preserve selected authoritative states without cumulative log/body duplication.
def selected(r):
    session=r['after']['session']
    return dict(id=r['id'],request=r['request'],visible=r['visible'],resolution=r['resolution'],
        character=r['after']['character'],session={k:session[k] for k in ('campaign_run_id','active_scene_id','scene_state','scene_runtime','clue_knowledge','last_publication','turn_counter') if k in session})
write('twelve_turn_state_evidence.json',{'before':[selected(r) for r in old],'after':[selected(r) for r in new]})

before=read('before_manifest.json')
after={p:sha((ROOT/p).read_bytes()) for p in before}
changed=[p for p in before if before[p]!=after[p]]
assert sorted(changed)==['game/api.py','game/storage.py'],changed
added=['game/object_marking.py','tests/test_object_marking.py','tests/test_atomic_character_save.py']
after.update({p:sha((ROOT/p).read_bytes()) for p in added})
write('after_manifest.json',after)
write('source_changes.json',dict(changed_existing=changed,added=added,protected_files=len(before),frozen_fixture_changes=[],production_data_changes=[]))

# Reconstruct entry sources by subtracting only the known additive patch, and
# authenticate bytes against the pre-edit manifest before using them in a diff.
prior_atomic='''def _atomic_write_bytes(path: Path, content: bytes) -> None:
    """Atomically replace a file's contents with bytes.

    Writes to a temp file in the same directory, fsyncs, then swaps with os.replace.
    Cleans up temp files on failure.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp.{secrets.token_hex(8)}")
    try:
        with open(tmp, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        # Windows readers (including file scanners) can briefly deny replacement.
        # Retry only the same prepared rename, never its enclosing gameplay turn.
        for delay in (0.01, 0.03, 0.09, None):
            try:
                os.replace(tmp, path)
                break
            except PermissionError as exc:
                if getattr(exc, 'winerror', None) != 5 or delay is None:
                    raise
                time.sleep(delay)
        # Best-effort directory fsync for durability; may not be supported on all platforms.
        try:
            dfd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            dfd = None
        if dfd is not None:
            try:
                os.fsync(dfd)
            except OSError:
                pass
            finally:
                os.close(dfd)
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        finally:
            raise


'''
diffs=[]
for p in changed:
    current=(ROOT/p).read_text(encoding='utf-8'); prior=current
    if p.endswith('api.py'):
        start=prior.index('def add_inventory_object_marking('); end=prior.index("@app.get('/api/snapshots')",start)
        prior=prior[:start]+prior[end:]
    else:
        prior=prior.replace('import stat\nimport tempfile\n','')
        prior=prior.replace('        _save_json(path, default)\n',"        path.write_text(json.dumps(default, indent=2), encoding='utf-8')\n",1)
        start=prior.index('    # Keep every character write, including bootstrap, on the snapshot writer.')
        end=prior.index('    path.parent.mkdir',start); prior=prior[:start]+prior[end:]
        start=prior.index('def _sync_directory('); end=prior.index('_RUNTIME_COMMIT: contextvars.ContextVar',start)
        prior=prior[:start]+prior_atomic+prior[end:]
        prior=prior.replace("    with _runtime_persistence_guard('save_character'):\n        _note_runtime_commit_origin()\n        _save_json(CHARACTER_PATH, data)",
            '    _note_runtime_commit_origin()\n    _save_json(CHARACTER_PATH, data)')
    candidates=[prior.encode(),prior.replace('\n','\r\n').encode()]
    raw=next((raw for raw in candidates if sha(raw)==before[p]),None)
    if raw is None:
        # Existing predecessor review includes the actual mixed-newline entry
        # source. Read it as evidence only; never restore a workspace source.
        baseline=OUT/'entry_sources'/p
        if baseline.exists() and sha(baseline.read_bytes())==before[p]:
            raw=baseline.read_bytes()
        else:
            with zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW.zip') as archive:
                raw=archive.read('support/'+p)
            assert sha(raw)==before[p],('predecessor source differs from entry',p)
        prior=raw.decode('utf-8').replace('\r\n','\n')
    assert raw is not None,('entry reconstruction hash mismatch',p)
    baseline=OUT/'entry_sources'/p; baseline.parent.mkdir(parents=True,exist_ok=True); baseline.write_bytes(raw)
    diffs.extend(difflib.unified_diff(prior.splitlines(True),current.splitlines(True),fromfile='entry/'+p,tofile='final/'+p))
for p in added:
    if p.startswith('game/'):
        diffs.extend(difflib.unified_diff([], (ROOT/p).read_text().splitlines(True),fromfile='/dev/null',tofile=p))
(OUT/'production.diff').write_text(''.join(diffs),encoding='utf-8')

counts=lambda r:f"{r['passed']} passed / {r['failed']} failed / {r['errors']} errors / {r['skipped']} skipped ({r['total']} tests)"
totals=f"Combined before: {counts(b)}. After: {counts(a)}. New failures: {results['new_failures']}; resolved: {results['resolved_failures']}."
focused='76 new marking/atomic tests; 52 identity tests; 50 inventory/snapshot controls; 143 preservation controls passed, separately selected.'
limitations=('Single authoritative character inventory and single-process ordered turn lane; no multi-process lost-update protection, '
    'multi-file crash transaction or global exactly-once across timeline rollback. File fsync is required; directory sync is best effort and unavailable on this Windows host. '
    'Permission bits are preserved; custom Windows ACLs, ownership and inode metadata are not portably copied by the standard-library writer. '
    'Read-only Get-Acl audit confirmed current character.json has zero explicit access rules and inherited directory ACLs (permission_audit.json); no custom-file-ACL durability/security guarantee. '
    'Authorization/evidence are trusted internal caller assertions, not gameplay adjudication or a public authentication boundary. '
    'No conversational marking, inspection/removal, equipment/material inference or T06 completion.')
next_step=('Exactly one next milestone: `pr_play_object_marking_inspection` — approved phase 3 current-state, disclosure-safe marking inspection and compatible removal, '
    'with explicit receipt/history semantics before exposing any action. Do not begin automatically. Defer T06, transfer, equipment, ruleset loader, crafting and baseline repairs.')
reports={
 'SUMMARY':f'**A/PASS for bounded validated persistent marking.**\n\n{focused}\n\n{totals}\n\nAn authorized add_marking targets one durable singleton; marking/revision/receipt commit in one atomic character replacement. Reload, exact/conflicting replay and historical snapshots verified. All twelve published turns and authoritative characters unchanged. Zero live provider calls.\n\n{limitations}',
 'BASELINE':f"Branch `{read('entry_identity.json')['branch']}`, HEAD `{read('entry_identity.json')['head']}`. Dirty worktree captured verbatim in entry_git_status.txt; no reset/clean/stash/revert/checkout/commit/push. Entry source/data/test hashes in before_manifest.json.\n\nBefore editing production: 52 identity, 50 inventory/snapshot and 143 preservation passed. {counts(b)} in authoritative combined selection; twenty predecessor failure identities reproduced. Exact IDs/assertions/commands in regression_results.json and before_*_command.json. Source scans confirmed direct character overwrite, existing atomic snapshot writer, revision=0 identity and API/ordered_turn/runtime_commit_scope authority.\n\nKnown failure identities:\n\n"+'\n'.join('- '+k for k in b['failures']),
 'ATOMIC_PERSISTENCE':('Previous save_character -> _save_json -> Path.write_text directly truncated character.json; bootstrap used _load_json direct writes. '
    'Snapshots already used _atomic_save_json/_atomic_write_bytes (same-directory nonexclusive temp, file fsync, os.replace, swallowed directory-sync errors). '
    'Existing runtime_commit_scope restores original bytes on Python exceptions, best effort with direct-write fallback, not a crash transaction. Identity calls this writer within that scope.\n\n'
    'Reused the existing atomic primitive. All character JSON saves/bootstrap now dispatch through _save_json to _atomic_save_json; snapshot restore already uses the same primitive. '
    'JSON indent=2/UTF-8/schema preserved. Serialization finishes before temp creation; regular non-symlink destinations only; exclusive mkstemp in destination directory; '
    'permission bits copied; write/flush/fsync/close then bounded existing Windows rename retry. Successful os.replace is the visibility commit boundary. '
    '_sync_directory returns actual boolean support/success; OS failure after replacement is reduced durability, not an old-file assertion. '
    'Temporary read-only flags are removed for Windows cleanup on failure. Temp names do not end in .json.\n\n'
    'Failure injection: serialization, temp creation, partial write, flush, file sync and replace all preserve exact prior hash, reload and remove temps. '
    'Directory open/sync errors after replacement retain new committed bytes and report false sync. Permission preservation and successful reload are tested. '
    'See atomic_save_traces.json, atomic_failure_*.json, verified_marking_junit.xml.\n\n'+limitations),
 'MARKING_CONTRACT':('Internal `game.api.add_inventory_object_marking(request)` only. No HTTP route. Version 1 exact request fields: operation=add_marking, '
    'campaign_run_id, character_id, instance_id UUID4, request_id, request_digest, expected_revision, content, source, authorization. '
    'Target already has valid unique identity in one authoritative character inventory; integer quantity=1 and predecessor singleton validation. No migration.\n\n'
    'Content is exact trusted text, nonblank, <=2048 UTF-8 bytes; max16 markings and 8192 total text bytes per object. Source kind explicit_literal/disclosed_copy and bounded reference. '
    'Authorization requires caller_id, decision_id, content_sha256, mechanics=not_applicable, and eight bounded evidence references: '
    'target_exists, accessible, rights, writable_surface, medium_available, medium_compatible, source_disclosed, capability. '
    'These are explicit internal assertions, never derived physical facts or arbitrary request-text authorization. No source fetch or hidden-data lookup.\n\n'
    'Each object markings entry has version, type, modification_id(UUID4), exact content, source, authorization, request_id, request_digest, applied_revision. '
    'No whole-object historical copy and no PF fields. Successful new request advances existing revision by one; replay/reject do not. Snapshot restores captured revision. '
    'All legacy/stat/extension fields are deep-preserved. Applied result includes original/result revisions and persistence=committed, returned only after save.'),
 'IDEMPOTENCY_CONTRACT':('Caller supplies stable bounded request_id. Canonical SHA-256 covers all meaningful request fields including scopes, '
    'target, expected revision, exact content, source and authorization; excludes only request_digest. Canonical JSON sorts mapping keys, uses compact separators, ASCII escapes and forbids NaN. '
    'Unknown request fields fail closed. Caller-supplied digest must match recomputation.\n\n'
    'Durable receipt is character.object_marking_receipts={version:1,campaign_run_id,character_id,entries:{request_id:result}}. '
    'Both receipt and marking are checked bidirectionally, including reconstructed semantic digest, identity, unique marking/request IDs, original/result revisions and status. '
    'Exact retry returns original result/UUID with no save or allocation, even though its original expected revision is now stale. Changed digest on same request_id explicitly rejects conflicting_request. '
    'New IDs allow identical content. No in-memory response-cache bypass: ordered_turn is entered without a cache key.\n\n'
    'Receipts retained for the lifetime of the saved character timeline; no pruning, silent eviction or external dedupe DB. O(applied operations) storage outside prompt projection. '
    'Restoring pre-operation snapshot removes its marking and receipt, allowing the original request to apply in that rolled-back timeline; restoring post snapshot restores exact replay. '
    'No global exactly-once claim across arbitrary rollback. On ambiguous completion reconcile the original ID against authoritative disk, never invent a new ID.'),
 'IMPLEMENTATION':('Production changes: game/storage.py: route _load_json/bootstrap and _save_json character dispatch to existing atomic primitive; '
    'save_character takes existing persistence guard; _atomic_write_bytes uses exclusive same-directory temps, modes, cleanup and honest directory sync reporting. '
    'game/object_marking.py (new): pure schema/authorization/revision/digest/receipt validation and detached prepare_marking proposal. '
    'game/api.py: internal add_inventory_object_marking entry reloads in existing ordered_turn lane plus persistence guard, delegates validation, checks existing '
    'WORLD_STATE API mutation authority, commits candidate with existing runtime_commit_scope and save_character, verifies byte rollback on exceptions and returns committed result. '
    'No new authority in object_instances; state_authority.py and identity code unchanged.\n\n'
    'Architecture refinements: use character receipt ledger rather than proposed session ledger because a single-file commit makes marking/receipt indivisible. '
    'Separate pure marking helper keeps the identity owner narrow; existing API remains the mutation coordinator. '
    'No ExplorationEngineResult/noncombat/CTIR changes because this cycle explicitly excludes conversational activation. No competing action result or publication system is introduced. '
    'Positive preconditions are trusted evidence references with explicit no-mechanics decision in controlled requests, not an installed adapter or physical adjudication engine.\n\n'
    'No parser/routing/T04/T05/T06/ruleset/scene/equipment/travel changes. See authenticated incremental production.diff.'),
 'PERSISTENCE_VERIFICATION':('marking_round_trip.json demonstrates two identified otherwise identical objects, selected-ID mutation, exact prior second row, '
    'revision=1, recovered marking/provenance/authorization and durable result. Reloaded exact retry returns original result and leaves bytes unchanged. '
    'marking_snapshots.json captures pre/post snapshots, post restore historical revision/receipt and exact replay; pre restore returns original character without marking or receipt. '
    'Re-execution after historical rollback is legitimate, not global exactly-once. '
    'Both snapshots use actual storage.create_snapshot/load_snapshot and coherency checks. Existing 52 identity and 50 inventory/snapshot controls pass. '
    'Failures before replacement and injected post-write Python exception return no successful result and restore original bytes; rollback failure surfaces coherency error rather than completion.'),
 'NEGATIVE_CONTROLS':('New tests cover missing/malformed/duplicate identity, stacks, malformed state, mismatched campaign/character, unknown operation/fields, '
    'blank/oversized/unencodable text, byte/aggregate/count limits, missing/invalid authorization and all eight missing evidence references, stale revisions, '
    'bad digest, conflicting replay, tampered/orphan receipts and modified content. Unknown legacy data and PF/non-PF opaque extensions remain equal. '
    'Concurrency: same request yields one durable result; distinct same-revision requests yield one applied and one stale rejection. '
    'Persistence faults raise with no success or partial authoritative receipt/marking; retry with original ID succeeds once after recovery. '
    'No endpoint or gameplay route invokes marking, and unchanged twelve-turn character states show no implicit marking or identity migration. '
    'Test identities and complete outcomes in verified_marking_junit.xml; no frozen fixtures changed.'),
 'REGRESSION_RESULTS':totals+'\n\n'+focused+'\n\nExact commands/arguments/executable and elapsed times: regression_results.json plus *_command.json / *_execution.json. '
    'Selections kept separate; no totals combined to imply improvement. Original authoritative 425-node command comes from artifacts/pr_play_t06_persistent_manipulation/baseline_command.json. '
    'Preservation selection is unchanged architecture validation_command.json. Covers T04/T05/T06, closed inspection, physical persistence and state authority; combined covers travel/immutable publication. '
    'One after_combined attempt died in installed openai import with Windows access violation; no result was assigned. Same selection rerun final_combined completed. '
    'No collection errors/skips in completed runs. '+results['diagnostic_variation_note']+' The other nineteen normalized failure diagnostics match after removing addresses, run temp paths and random turn IDs. '
    'No live provider calls or network attempts escaped guards. No full-suite or Gameplay Benchmark claim.\n\n'
    'Known before/after failure identities:\n\n'+'\n'.join('- '+k for k in a['failures']),
 'TWELVE_TURN_COMPARISON':('Unchanged provider-free PR-PLAY HTTP harness run before and final. All twelve text strings, full characters, scene outcomes and '
    'normalized resolutions equal; only timing and existing process-local clue digests excluded. Publication pointer equals current published text, or retains prior completed publication for unsupported T06/T12. '
    'T04 contact, T05 clean clue, T06 unsupported, T09 grounded recall, T11 travel preserved. No implicit IDs/markings, no extra model/provider calls. '
    'See twelve_turn_comparison.json and twelve_turn_state_evidence.json.\n\n'+'\n\n'.join(r['turn']+': unchanged — '+str(r['after']) for r in comparison)),
 'PERFORMANCE':('Small fixture: 20 explicitly identified singleton inventory rows. 100 lookup and validation samples, 30 save samples. '
    'Measure is a micro-measurement of this host, not a broad benchmark.\n\n```json\n'+json.dumps(read('performance.json'),indent=2)+'\n```\n\n'
    'Receipt growth is retained for saved timeline lifetime. Validation scans only this inventory and its marking/receipt state, never world objects. '
    'Prompt character projection in game/prompt_context.py explicitly selects name/hp/ac/conditions/attacks/spells/skills and excludes receipts/markings; prompt path unchanged. '
    'Zero live provider calls, additional model calls/retries/tokens or prompt expansion.'),
 'NEXT_STEP_DECISION':'Recommend A/PASS for the bounded internal capability.\n\n'+next_step+'\n\n'+limitations,
 'INTEGRITY':('Branch/HEAD remain entry_identity.json values. Dirty inputs preserved; only game/api.py and game/storage.py differ among '+str(len(before))+
    'protected source/test/data files; three new implementation/test files. Frozen fixtures and production data match every entry hash. '
    'Incremental production.diff uses authenticated entry bytes (API reconstruction, storage read from predecessor review and matched to before_manifest.json), excluding pre-existing dirty changes. '
    'No reset/clean/stash/revert/historical checkout/commit/push. NEXT_SESSION is prepended and exact prior bytes retained as suffix; prior review saved as entry_current_review.md. '
    'Source/evidence manifests, all 13 reports, tests, implementation, atomic failures, marking/receipts, reload/snapshots, regression and twelve-turn evidence are explicit review inputs. '
    'Fresh generated handoff and dated archive are reopened, CRC/member/canonical/evidence hashes and internal milestone checked by seal_review.py. '
    'Archive SHA-256 and verification are external final seal artifacts (avoids circular hash); see archive_sha256.txt and archive_verification.json. '
    'Live provider calls 0. '+limitations),
}
for name,body in reports.items():
    (REPORT/(name+'.md')).write_text('# '+name.replace('_',' ').title()+'\n\nMilestone: `'+MID+'`. Date: 2026-11-09.\n\n'+body+'\n',encoding='utf-8')
intro=(f'# NEXT_SESSION — PR-PLAY Validated Persistent Object Marking (2026-11-09)\n\n'
    f'**A/PASS for bounded internal marking.** Milestone `{MID}`. Branch {read("entry_identity.json")["branch"]}; HEAD {read("entry_identity.json")["head"]}. '
    'Dirty work preserved; no commits/pushes; live provider calls **0**.\n\n'
    'Explicit trusted add_marking now validates singleton ID, authorization/evidence, content bounds and revision; API existing authority commits marking and durable character receipt in one atomic replacement. '
    'Exact reload retry returns original result; changed request digest rejects. Snapshot before/after restores historical markings/revisions/receipts. No T06 or player-visible changes; all twelve turns unchanged.\n\n'
    +totals+' '+focused+' One import-time Windows access violation was rerun without changing selection.\n\n'
    +next_step+'\n\n'+limitations+'\n\n'
    f'Minimum reading: development/campaigns/product_realization/{MID}/SUMMARY.md, ATOMIC_PERSISTENCE.md, MARKING_CONTRACT.md, IDEMPOTENCY_CONTRACT.md, REGRESSION_RESULTS.md, NEXT_STEP_DECISION.md, INTEGRITY.md. '
    f'Evidence artifacts/{MID}/: atomic_save_traces.json, marking_round_trip.json, marking_snapshots.json, regression_results.json, twelve_turn_comparison.json, source_changes.json. '
    'Review: handoff/CURRENT_REVIEW.md; fresh dated archive/hash/reopen record in archive_sha256.txt and archive_verification.json.\n\n---\n\n')
(ROOT/'docs/NEXT_SESSION.md').write_bytes(intro.encode()+(OUT/'entry_next_session.md').read_bytes())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==read('entry_identity.json')['head']
(OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
write('files_created.json',dict(production=added[:1],tests=added[1:],reports=[p.relative_to(ROOT).as_posix() for p in REPORT.glob('*.md')],evidence_directory=OUT.relative_to(ROOT).as_posix()))

files=[p for p in OUT.iterdir() if p.is_file() and p.suffix in ('.json','.py','.diff','.xml')
       and p.name not in ('archive_verification.json','review_handoff.json','evidence_manifest.json')
       and not p.name.endswith('_sequence.json')]
# Retain failed-startup log as relevant tooling evidence, without raw historical payloads.
files.append(OUT/'after_combined.log')
support=[*REPORT.glob('*.md'),*files,*[ROOT/p for p in changed+added],ROOT/'docs/NEXT_SESSION.md']
support=list(dict.fromkeys(support))
write('evidence_manifest.json',dict(milestone=MID,files=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())} for p in support if p.is_file()]))
support.append(OUT/'evidence_manifest.json')
config=dict(campaign_id=MID,campaign_name='PR-PLAY — Validated Persistent Object Marking',campaign_date='2026-11-09',
    purpose='Bounded production marking, atomic persistence and durable idempotency verification',objective_status='A/PASS — bounded internal marking',
    executive_summary=reports['SUMMARY'],changes=dict(production=['game/storage.py','game/api.py','game/object_marking.py'],
        validation=['76 new marking/atomic tests; existing fixtures unchanged.'],documentation=['13 reports; NEXT_SESSION prepended.'],
        tooling=['Cycle-local runners, metrics, comparison and archive sealing.'],generated_artifacts=['Evidence and fresh review archives.']),
    testing=dict(focused=focused,broader=totals,full_suite='Not run.',runtime_validation='Real save/reload/snapshots and unchanged 12-turn HTTP harness.',
        model_runtime_boundary='Zero live provider calls; network/data guards.',new_regressions='[]',pre_existing_failures='Twenty exact IDs in REGRESSION_RESULTS and regression_results.json.'),
    decisions_requiring_human_review=['Review bounded implementation; no additional authorization needed.'],
    known_problems=dict(campaign_specific=[limitations],pre_existing=['Twenty baseline assertion identities; one import-time Windows access violation rerun.']),
    missing_concepts=['Player-facing inspection/removal and later T06 integration.'],does_not_prove=['Multi-process or cross-timeline exactly-once, custom ACL preservation, general physical adjudication, full-suite or improved gameplay.'],
    recommended_next_step=next_step,self_contained_review_test='Reopen stable/dated ZIPs; verify all canonical/evidence hashes and implementation, atomic/marking/snapshot/regression/twelve-turn/handoff claims.',
    primary_report=(REPORT/'SUMMARY.md').relative_to(ROOT).as_posix(),supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='implementation_or_evidence',canonical=True,
        why='Bounded marking implementation, exact verification or handoff provenance.') for p in support if p.name!='SUMMARY.md'])
write('review_handoff.json',config)
print(totals)
