"""Assemble measured cycle evidence, reports and explicit standard review inputs."""
from pathlib import Path
import ast
import difflib
import gzip
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
MID='pr_play_object_visibility_authoring'
REPORT=ROOT/'development/campaigns/product_realization'/MID
REPORT.mkdir(parents=True,exist_ok=True)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read(name):
    p=OUT/name
    return json.loads((p.read_bytes() if p.exists() else gzip.decompress((OUT/(name+'.gz')).read_bytes())).decode('utf-8-sig'))
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
def summary(mode):
    tree=ET.parse(OUT/(mode+'_junit.xml')); rows=list(tree.iter('testcase'))
    failures={t.attrib['classname'].replace('.','/')+'.py::'+t.attrib['name']:t.find('failure').text
              for t in rows if t.find('failure') is not None}
    return dict(total=len(rows),passed=sum(not any(t.find(k) is not None for k in ('failure','error','skipped')) for t in rows),
        failed=len(failures),errors=len(list(tree.iter('error'))),skipped=len(list(tree.iter('skipped'))),
        failures=failures,command=read(mode+'_command.json'),execution=read(mode+'_execution.json'))
modes=[prefix+name for prefix in ('before_','sealed_after_') for name in
       ('observation','inspection','marking','identity','inventory_snapshot','preservation','combined','visibility')]
modes+=['evidence_authoring']
results={m.replace('sealed_after_','after_'):summary('retry_sealed_after_preservation' if m=='sealed_after_preservation' else m) for m in modes}
for group in ('combined','visibility'):
    b,a=results['before_'+group],results['after_'+group]
    results[group+'_new_failures']=sorted(set(a['failures'])-set(b['failures']))
    results[group+'_newly_passing']=sorted(set(b['failures'])-set(a['failures']))
    assert not results[group+'_new_failures']
for key,value in list(results.items()):
    if not isinstance(value,dict): continue
    assert value['errors']==value['skipped']==0
    if 'combined' not in key and 'visibility' not in key: assert value['failed']==0,(key,value)
    assert not value['execution']['network_blocks']
results['live_provider_calls']=0
write('validation_interruptions.json',dict(attempt='sealed_after_preservation',exit_code=-1073741819,
    windows_status='0xC0000005',kind='Native access violation during scene read; cause not established',
    completed_pytest_result=False,log='sealed_after_preservation.log',command=read('sealed_after_preservation_command.json'),
    unchanged_selection_retry='retry_sealed_after_preservation',retry_result=results['after_preservation']))
write('regression_results.json',results)

def normalize(value):
    if isinstance(value,dict): return {k:normalize(v) for k,v in value.items() if k!='performance'}
    if isinstance(value,list): return [normalize(v) for v in value]
    if isinstance(value,str) and value.startswith('clue_text_digest:'): return 'clue_text_digest:PROCESS_LOCAL'
    return value
old,new=read('before_sequence.json')['turns'],read('sealed_after_sequence.json')['turns']
comparison=[]
for x,y in zip(old,new):
    pub=y['after']['session'].get('last_publication',{}); prior=y['before']['session'].get('last_publication',{})
    comparison.append(dict(turn=y['id'],before=x['visible'],after=y['visible'],text_equal=x['visible']==y['visible'],
        character_equal=x['after']['character']==y['after']['character'],
        scene_equal=x['after']['session']['active_scene_id']==y['after']['session']['active_scene_id'],
        resolution_equal=normalize(x['resolution'])==normalize(y['resolution']),
        no_implicit_identity_or_marking=all(not any(k in r for k in ('instance_id','markings','marking_visibility'))
            for r in y['after']['character'].get('inventory',[]) if isinstance(r,dict)),
        publication_pointer_consistent=pub.get('visible')==y['visible'] or (y['id'] in ('T06','T12') and pub==prior)))
flags=('text_equal','character_equal','scene_equal','resolution_equal','no_implicit_identity_or_marking','publication_pointer_consistent')
assert len(comparison)==12 and all(all(r[k] for k in flags) for r in comparison)
write('twelve_turn_comparison.json',dict(turns=comparison,live_provider_calls=0,
    normalization='Only performance and existing process-local clue digests.'))
for name in ('before_sequence.json','after_sequence.json','sealed_after_sequence.json'):
    p=OUT/name
    if p.exists():
        raw=p.read_bytes(); packed=gzip.compress(raw,mtime=0); assert gzip.decompress(packed)==raw
        (OUT/(name+'.gz')).write_bytes(packed); p.unlink()

before=read('before_manifest.json'); after={p:sha((ROOT/p).read_bytes()) for p in before}
changed=sorted(p for p in before if before[p]!=after[p]); assert changed==['game/api.py','game/object_marking.py'],changed
added=['tests/test_object_visibility_authoring.py']; after.update({p:sha((ROOT/p).read_bytes()) for p in added})
write('after_manifest.json',after)
write('source_changes.json',dict(changed_existing=changed,added=added,protected_files=len(before),
    unchanged_protected_files=len(before)-len(changed),frozen_fixture_changes=[],production_data_changes=[]))
diff=''
for path,entry in [('game/api.py','entry_api.py'),('game/object_marking.py','entry_object_marking.py')]:
    diff+=''.join(difflib.unified_diff((OUT/entry).read_text().splitlines(True),(ROOT/path).read_text().splitlines(True),
        fromfile='entry/'+path,tofile=path))
(OUT/'production.diff').write_text(diff,encoding='utf-8')
identity=read('entry_identity.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==identity['head']
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()==identity['branch']

timeline=read('classification_timeline.json'); snaps=timeline['snapshots']
assert [s['state']['inventory'][0]['revision'] for s in snaps]==[1,2,3,4]
assert [len(s['observation']['properties'][0]['values']) for s in snaps]==[0,1,0,1]
assert [s['receipt_count'] for s in snaps]==[1,2,3,4]
assert timeline['leakage']['leaks']==[]
assert read('no_change_and_restricted.json')['no_change']['status']=='no_change'
assert read('ambiguous_reconciliation.json')['no_duplicate']
for stage in ('serialization','create','partial_write','flush','sync','replace','ambiguous'):
    assert read('classification_failure_'+stage+'.json')['unchanged']
for fault in ('insert','change','drop','rebind','duplicate'): assert read('http_bypass_'+fault+'.json')['rejected']
port=[read('visibility_portability_'+n+'.json') for n in ('pf1e@1','rules_light@1','scifi@1')]
assert all(p['observation']['properties']==port[0]['observation']['properties'] for p in port)

def ref(path,name):
    tree=ast.parse((ROOT/path).read_text(encoding='utf-8'))
    node=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
    return f'{path}:{node.lineno} ({name})'
stages=[
 ('Player-message interpretation','Implemented and usable','game/api.py','api_chat','Existing HTTP/FIFO/commit envelope; original T06 enters conversational orchestration.'),
 ('Action extraction','Implemented but not integrated','game/intent_parser.py','recover_actionable_explicit_world_action','Recovery captures physical verb try and an unbound clause. No canonical copy/source/garment/medium action.'),
 ('Object-target resolution','Implemented but not integrated','game/object_marking.py','_target','Durable inventory ID lookup works internally; no natural-language sleeve-to-existing-garment/part binding.'),
 ('Inventory/equipment resolution','Missing','game/object_instances.py','inspect_object_identity','Existing singleton identity is usable. Generic equipment/garment-part relation is absent; T06 has a Spellbook only.'),
 ('Environmental-material resolution','Missing','game/physical_adjudication.py','_objects','Scene enumeration is not an accessible usable-mud supply resolver. Experimental owner remains disabled.'),
 ('Physical prerequisite validation','Blocked by missing authority','game/object_marking.py','_request_error','Internal positive evidence schema exists; no upstream basis for this sleeve, wet accessible mud or compatibility.'),
 ('Ruleset adjudication','Blocked by missing authority','game/skill_checks.py','resolve_skill_check','Existing checks exist. No integrated marking decision adapter; explicit not_applicable is a trusted assertion, not default success.'),
 ('Object mutation authorization','Implemented but not integrated','game/api.py','_mutate_inventory_object_marking','Existing world-state guard, lane and durable receipts. No player action issuer; do not call standalone lane recursively inside api_chat.'),
 ('Marking application','Implemented but not integrated','game/object_marking.py','prepare_marking','Exact known text can stage one addition after all evidence is established; T06 never calls it.'),
 ('Visibility classification','Implemented but not integrated','game/object_marking.py','prepare_visibility','This cycle stages typed-authorized metadata and shared receipt; no natural-language authority.'),
 ('Observation/disclosure','Implemented but not integrated','game/object_observation.py','observe_object','Existing typed grants filter current active metadata. No player inspection path calls it.'),
 ('State persistence','Implemented and usable','game/storage.py','save_character','Atomic character file carries active state and receipts; real save/reload/snapshots verified. Whole-turn integration still needed.'),
 ('Narrative publication','Implemented but not integrated','game/immutable_valid_response.py','seal_delivery_contract','Existing seal/publication is usable, but no applied-marking DTO/assertion adapter reaches it.')]
source_map=[dict(stage=s,status=status,source=ref(path,name),finding=finding) for s,status,path,name,finding in stages]
source_map += [dict(stage='Current decisive decline',status='Implemented and usable',
    source=ref('game/conversational_orchestration.py','_unbound_physical_decline'),finding='Unsupported before resolver/preconditions; T06 prior publication pointer retained.')]
write('t06_source_map.json',dict(request="I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording.",stages=source_map))

def total(r): return f"{r['passed']} passed / {r['failed']} failed / {r['errors']} errors / {r['skipped']} skipped ({r['total']} tests)"
b,a=results['before_combined'],results['after_combined']
reg=f"Combined before: {total(b)}. After: {total(a)}. New failing identities: {results['combined_new_failures']}; newly passing: {results['combined_newly_passing']}."
focused=f"{results['evidence_authoring']['passed']} focused authoring tests passed."
predecessors='; '.join(f"{g}: {results['before_'+g]['passed']} before / {results['after_'+g]['passed']} after" for g in
    ('observation','inspection','marking','identity','inventory_snapshot','preservation'))+'.'
supp=f"Supplemental disclosure before: {total(results['before_visibility'])}; after: {total(results['after_visibility'])}. New failures: {results['visibility_new_failures']}."
next_step='Exactly one recommended next milestone: `pr_play_grounded_marking_action_integration` — a bounded end-to-end player copy action over an explicitly established existing target, disclosed source and usable medium, with truthful missing-prerequisite handling for original T06. No general object-framework expansion.'
limits=('Trusted internal Python assertions only; no authenticated decision issuer or cryptographic grant. Upstream owns classification basis, access, physical eligibility and mechanics. '
    'Single-process FIFO/persistence guard; no multi-process lost-update, multi-file crash-atomic or global exactly-once across snapshot rollback guarantee. '
    'File fsync required; Windows directory fsync unavailable/best effort; permission-bit preservation does not guarantee custom ACL/ownership metadata. '
    'Receipts grow for the saved timeline lifetime; no pruning. No player observation, conversational marking/classification, T06 completion, fabricated equipment/materials or provider use. '
    'No full-suite, independent holdout, live-model or broad gameplay-improvement claim.')
failure_list='\n'.join('- '+x for x in b['failures'])
commands='\n\n'.join('### '+mode+'\n\n```text\n'+row['command']['executable']+'\n'+json.dumps(row['command']['args'])+'\n```\n\n'+total(row)+'\n\n'+
    ('\n'.join('- '+x for x in row['failures']) or 'No failures.') for mode,row in results.items() if isinstance(row,dict))
map_table='| Stage | Status | Actual source and finding |\n|---|---|---|\n'+'\n'.join(f"| {r['stage']} | {r['status']} | `{r['source']}` — {r['finding']} |" for r in source_map)
t06=('Existing call graph: `/api/chat` -> api_chat -> chat/_chat_turn -> conversational decision -> `_unbound_physical_decline` -> parser probes -> unsupported_physical_manipulation -> sealed decline; resolver and prerequisites not reached. '
    'Standalone internal path: set_marking_visibility -> shared API mutation coordinator -> prepare_visibility -> existing character atomic save. Observation is a separate read-only call, never mutation authority.\n\n'+map_table+'\n\n'
    'Required authority decisions: bind the exact previously disclosed patrol wording; identify an actually established garment and sleeve part; establish usable wet mud, access, rights and surface compatibility; supply explicit noncontested no-mechanics adjudication or delegate real mechanics. '
    'The original fixture establishes a muddy gate line but no equipped garment or accessible compatible smear. Spellbook possession and the phrase my sleeve prove neither.\n\n'
    'Minimum viable sequence: recognize one bounded semantic copy proposal before the unconditional decline; bind disclosed source and an existing authored target/part; resolve only positively established material facts; return precise missing/ambiguous prerequisites without creating facts. '
    'For a valid controlled fixture, stage prepare_marking then prepare_visibility against its resulting revision within the already-entered whole-turn lane; commit both receipts and final character together through the existing API authority/save seam. '
    'Do not call standalone ordered_turn helpers recursively. Establish fresh observation authority, project permitted committed text, adapt that result into ExplorationEngineResult/noncombat resolution and authorized narration, validate then seal/publish. '
    'On failure discard/roll back staged state and never publish completion. Verify immediate/later inspection, reload/retry and twelve-turn preservation.\n\n'
    'Risks: invented mud is an unauthorized material grant; invented clothing is an unauthorized inventory/equipment grant; prose before commit can claim a marking that never exists; raw receipts leak private evidence. '
    'Keep PF1e checks, DCs, spell effects and technology eligibility upstream; core metadata and IDs remain ruleset neutral. '
    'Smallest defensible next implementation is one grounded copy path with explicitly authored positive fixtures plus negative original-state cases, not transfer, crafting, a registry or a general equipment system.\n\n'+next_step)
reports={
 'SUMMARY':f'**A/PASS for bounded trusted internal classification.**\n\n{focused} {reg}\n\n{predecessors} {supp}\n\n'
    'Authoritative visible/concealed/restricted metadata now changes through one trusted internal operation, with stable object/mark IDs, preserved content/extensions, exact revision lifecycle and shared atomic durable receipts. '
    'Existing whole-character HTTP editing now refuses classification insertion/change/drop/rebinding; unchanged metadata survives reorder and ordinary edits. Its compare/save shares the existing lane and persistence guard so a concurrent edit cannot erase a classification. '
    'Historical snapshot observation and replay, negative authority, atomic failure and hidden-output controls pass. Twelve player-visible turns unchanged. Live provider calls **0**.\n\n'+limits+'\n\n'+next_step,
 'BASELINE':f"Branch `{identity['branch']}`; HEAD `{identity['head']}`. Entry dirty status and all protected file hashes are in entry_git_status.txt/before_manifest.json. {predecessors}\n\n{reg}\n\n{supp}\n\nExact current baseline failures:\n\n{failure_list}\n\n"
    'Verified-code discrepancies: original architecture proposed a session ledger; shipped ledger is character.object_marking_receipts to keep one-file atomicity. Architecture phase 3 described player inspection; shipped observation remains internal. '
    'Old exact marking validation rejected inert per-mark unknown fields; this cycle preserves them while validating required fields. Existing /api/character allowed raw visibility replacement; this cycle closes that specific client bypass. '
    'No frozen historical files were edited. Source inspection and complete pre-edit runs preceded production edits.',
 'VISIBILITY_CONTRACT':'Authoritative location is inventory row `marking_visibility={version:1,markings:{modification_id:visibility}}`, exactly the predecessor observation schema. '
    'Leaf forms are {classification:visible}, {classification:concealed}, or {classification:restricted,scope:<bounded nonblank scope>}. No observable alias or default visible migration. '
    'Legacy missing classification remains unknown/undisclosed. Malformed/unsupported metadata containers or selected leaves refuse authoring rather than overwrite opaque data. Unknown row/map fields and other entries survive.\n\n'
    'Verified transitions: unclassified -> visible -> concealed -> visible; visible -> restricted -> visible. Ordinary authority may see visible only, explicit concealed authority may see concealed, restricted requires matching scope or trusted wildcard. '
    'All observations still need independently established observer/access/scope/current-state authority. Exact same-value replay returns original receipt. New same-value requests commit status=no_change receipt with unchanged revision and no object delta; storing this receipt makes no-change replay durable without pretending a mutation occurred.',
 'AUTHORITY_INTEGRATION':'Internal entry `game.api.set_marking_visibility(request, authorization=grant)` reuses the existing marking coordinator. '
    'Pure `game.object_marking.prepare_visibility` requires the same private typed _VisibilityAuthorization. Trusted `_establish_visibility_authorization` validates request shape and binds canonical digest covering campaign/character, object, mark, operation, classification/scope, expected revision, request identity and structured evidence. '
    'Request authorization requires caller_id, decision_id, mechanics=not_applicable and positive bounded evidence refs for target_exists, marking_exists, rights, classification_basis, capability. These are upstream assertions, not physical checks or authentication. '
    'JSON authorized=true and serialized grants refuse. All binding mismatch cases tested. No new grant issuer endpoint exists.\n\n'
    'API validates campaign from authoritative session and character/object from saved character, enters existing ordered_turn without in-memory request cache, holds existing persistence guard, checks WORLD_STATE ownership, stages detached candidate, and saves under runtime_commit_scope. '
    'No second state owner/database. Existing whole-character replacement route calls _client_visibility_unchanged and rejects introduction/change/removal/rebinding/duplication of classified bindings. Compare/save holds the same ordered_turn lane and persistence guard as classification, preventing a stale client replacement from erasing concurrent metadata. The two-thread blocking control verifies this serialization. Unchanged metadata and inventory reordering remain compatible. '
    'Trusted direct storage and historical snapshot restore retain their established roles; this is a local application, not a new authentication boundary.',
 'IDEMPOTENCY_VERIFICATION':'Shared ledger remains character.object_marking_receipts v1. Add/remove receipt shapes remain unchanged. Classification result adds operation and complete canonical request; status applied increments exactly once, no_change increments zero. '
    'Validator checks historical semantic digests, mark-to-object linkage, revision bounds/types, revision uniqueness for actual changes, complete ledger coverage and malformed receipts. '
    'Same request/digest returns detached original committed result before current revision or active mark checks, even after later transitions/removal/reload. Different digest conflicts, including all tested add/remove/classification request-ID reuse directions. '
    'Current classification is read solely from row metadata; receipts never drive observation or reconstruct current classification. Snapshot rollback restores that timeline receipt set; no global exactly-once claim. '
    'Evidence: visibility_idempotency_controls.json, no_change_and_restricted.json, classification_timeline.json, ambiguous_reconciliation.json and evidence_authoring_junit.xml.',
 'OBSERVATION_INTEGRATION':'Existing game.object_observation.py is byte-identical. Existing projection observes legacy state as unknown, visible as known_present, concealed under ordinary authority as unknown, and concealed with explicit authority as known_present. Restricted scope controls and reverse transition pass. '
    'No classification alone grants observation; missing grants and stale prior-state grants fail unresolved. Ordinary empty subset remains unknown, never concealed-count/absence inference. Existing 88 observation controls preserve complete known_absent semantics. '
    'Only authorized text/presentation/local evidence/content hash leave the service. Authoring requests, digests, UUIDs, private decision/prerequisite references, receipts, removed records and extensions do not appear in structured/serialized projection. '
    'Timeline leak sentinels plus predecessor confidentiality/noninterference controls pass; supplemental pre-existing failures are reported separately. Read-only projection does not save or advance revision. '
    'Evidence: classification_timeline.json, no_change_and_restricted.json, visibility_idempotency_controls.json, predecessor/focused JUnit.',
 'PERSISTENCE_VERIFICATION':'One candidate contains classification and its receipt; existing save_character atomically replaces the single authoritative character JSON. S0/S1/S2/S3 restore revisions 1/2/3/4, receipts 1/2/3/4 and ordinary permitted counts 0/1/0/1. Full restored character equality verifies IDs, no implicit migration and no future-state leakage. '
    'Each transition saves/reloads and repeats every earlier request without disk changes. Missing metadata remains unclassified in S0.\n\n'
    'Operation-level failure injection exercises actual nonserializable candidate, temp creation, partial write, flush, file fsync and replacement failures; exact previous bytes/classification/receipt remain, no temporary file remains, and original-ID retry commits once. '
    'Post-replacement exception with successful rollback restores old bytes. A separate forced rollback failure raises RuntimePersistenceCoherencyError, publishes no success and leaves the committed state available for original-ID reconciliation; retry returns its existing receipt. '
    'No-change receipt save failure is atomic too. Existing atomic writer tests separately preserve permission-bit/reduced-directory-durability contracts. '+limits,
 'NEGATIVE_CONTROLS':focused+' Scope/operation/classification/revision/mark/object/request grant binding; malformed/missing/JSON grants; positive prerequisite fields with invalid values; unsupported classification and malformed scope; stale/missing/bool/string/negative revisions; missing/removed marks; missing/duplicate/malformed/legacy identities; malformed records/maps/version/leaves; invalid digest/receipts; wrong authoritative campaign/character; cross-object and identical-content isolation; reorder; inert unknown fields; ruleset fields; atomic failures; HTTP classification bypass and preserved edits; observation purity and no mutation route. '
    'No gameplay caller is introduced; guarded twelve-turn execution verifies no implicit object identity/marking/classification. All executions disable provider/interpretation/expression/retries and block non-loopback networking. Authored variations are not independent holdout evidence. '
    'Development iterations remain recorded: initial HTTP tests invoked full scene startup against an intentionally partial object fixture; the next iteration expected an internal error code in a deliberately sanitized player DTO. Final tests assert both internal rejection and safe HTTP output without changing production projection. A final two-thread control verifies whole-character compare/save and classification share the existing lane; all after selections were rerun following that guard change.',
 'RULESET_PORTABILITY':'PF1e perception_dc/ac, rules_light tags and science-fiction sensor/encryption/battery extensions persist unchanged at character, object and marking levels through classification/save/reload. All three produce identical permitted inscription DTOs. '
    'Core never interprets Perception/DCs, spells, proficiency, rarity or technology. No mechanics means explicit upstream not_applicable evidence for this internal classification, not a general gameplay exemption. '
    'Evidence: visibility_portability_pf1e@1.json, visibility_portability_rules_light@1.json, visibility_portability_scifi@1.json. Boundary portability only; no alternate-ruleset runtime implemented.',
 'REGRESSION_RESULTS':reg+'\n\n'+predecessors+'\n\n'+supp+'\n\n'+focused+' Overlapping groups are not summed. Full suite not run. Zero live provider calls/network attempts. Baseline source variants and exact selections are retained; no different selections compared as equivalent. '
    'The first final preservation process terminated with Windows native access violation 0xC0000005 during a scene-read/stat stack, without completed JUnit or execution summary. Cause is unproven; it is retained as a native process interruption, not counted as a completed passing run or a pytest assertion failure. '
    'The identical 143-test selection was rerun without source changes and passed. Earlier before/after preservation runs also passed. See validation_interruptions.json, sealed_after_preservation.log and retry_sealed_after_preservation outputs.\n\n'+commands,
 'TWELVE_TURN_COMPARISON':'Provider-free established twelve-turn HTTP harness ran before and after. All visible text, characters, scenes, normalized resolution and publication-pointer checks match. T04 contact, T05 clue, T09 grounded recall and T11 travel remain successful; T06 remains unsupported and retains prior pointer. No identity, marking or visibility implicitly appears; no hidden publication or additional provider calls. Only existing process-local clue digest and timing fields normalized.\n\n'+'\n\n'.join(r['turn']+': unchanged — '+str(r['after']) for r in comparison),
 'PERFORMANCE':'Representative two-object/one-mark fixtures. Comparable refined measurements use 100 iterations for pure initial/transition/replay validation and observation with fresh grants on already-loaded state, plus 25 isolated atomic writer samples. Microseconds, local host only; no portable threshold. Receipt growth is linear in committed requests (including durable no_change); current marking state remains bounded.\n\n```json\n'+json.dumps(read('performance_refined.json'),indent=2)+'\n```\n\n'
    'The earlier visibility_performance.json retains full-service initial/transition/replay samples. Its before observation uses cached state while after includes a disk read; that difference is not pure projection overhead. Refined measurements separate those costs. '
    'Validation scans this character inventory/receipt history only. No world scan, prompt expansion, new model classification, live provider calls, database, ACL engine or player endpoint. Authoring receipts remain outside prompts and projection.',
 'T06_INTEGRATION_MAP':t06,
 'NEXT_STEP_DECISION':'Recommend **A/PASS** for this bounded trusted internal lifecycle: authority, atomic persistence, durable replay, current-state observation, historical snapshots and regression preservation are verified. '
    'No new material regression identity, no player-visible gameplay change and no T06-completion claim.\n\n'+next_step+'\n\n'+limits,
 'INTEGRITY':f"Branch/HEAD unchanged: {identity['branch']} / {identity['head']}. Entry status retained. Of {len(before)} protected files, only game/api.py and game/object_marking.py changed; test addition tests/test_object_visibility_authoring.py. "
    'Incremental production.diff compares entry bytes, preserving all pre-existing dirty work. All other protected source/test/data/static/tool/script bytes, including frozen fixtures, remain unchanged. No reset/clean/stash/revert/checkout/commit/push. '
    'NEXT_SESSION prepends this milestone and preserves historical bytes as suffix. Fifteen reports, exact commands/results and bounded evidence feed standard build_review_handoff.py; canonical review stable/history and fresh dated ZIP are reopened for CRC, identity, all canonical/evidence hashes and semantic acceptance claims. '
    'Archive SHA-256/reopen seal remain external to avoid circular hashing; see archive_sha256.txt/archive_verification.json. No completed archive claim is made until seal_review.py succeeds. Live provider calls 0.'}
for name,body in reports.items():
    (REPORT/(name+'.md')).write_text('# '+name.replace('_',' ').title()+'\n\nMilestone: `'+MID+'`. Date: 2026-11-09.\n\n'+body+'\n',encoding='utf-8')
handoff=(f'# NEXT_SESSION — PR-PLAY Trusted Visibility Authoring (2026-11-09)\n\n**A/PASS for bounded internal classification.** Milestone `{MID}`. '
    f"Branch {identity['branch']}; HEAD {identity['head']}. Dirty work preserved, no commits/pushes; live provider calls **0**.\n\n"
    'Internal set_marking_visibility now authors existing visible/concealed/restricted metadata using typed request-bound authority, shared add/remove receipts, expected revision and existing atomic character persistence. '
    'Same-value no_change stores replay receipt with zero revision delta. IDs/content/unknown extensions survive. Whole-character HTTP replacement refuses visibility insertion/change/drop/rebinding; unchanged metadata/reorder still works. '
    'Observation unchanged; real reload and S0/S1/S2/S3 restoration yield correct historical disclosure. All twelve HTTP turns/publication pointers unchanged; T06 remains unsupported.\n\n'
    +focused+' '+reg+'\n\n'+predecessors+' '+supp+'\n\n'+next_step+' Do not begin automatically.\n\n'+limits+'\n\n'
    f'Minimum: development/campaigns/product_realization/{MID}/SUMMARY.md, VISIBILITY_CONTRACT.md, AUTHORITY_INTEGRATION.md, PERSISTENCE_VERIFICATION.md, REGRESSION_RESULTS.md, T06_INTEGRATION_MAP.md, NEXT_STEP_DECISION.md and INTEGRITY.md. '
    f'Evidence: artifacts/{MID}/classification_timeline.json, visibility_idempotency_controls.json, ambiguous_reconciliation.json, regression_results.json, twelve_turn_comparison.json, source_changes.json, archive_sha256.txt and archive_verification.json. '
    'Review: handoff/CURRENT_REVIEW.md.\n\n---\n\n')
(ROOT/'docs/NEXT_SESSION.md').write_bytes(handoff.encode('utf-8')+(OUT/'entry_next_session.md').read_bytes())
write('milestone_identity.json',dict(milestone=MID,verdict='A/PASS',live_provider_calls=0))
(OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short']))
write('files_created.json',dict(production_changed=changed,validation_added=added,
    reports=[p.relative_to(ROOT).as_posix() for p in sorted(REPORT.glob('*.md'))],
    artifacts=[p.relative_to(ROOT).as_posix() for p in sorted(OUT.iterdir()) if p.is_file()],
    handoff='Fresh stable/history/dated standard exports; external archive seal.'))
excluded={'review_handoff.json','evidence_manifest.json','archive_sha256.txt','archive_verification.json','handoff_generation.log'}
evidence_files=[p for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in excluded]
write('evidence_manifest.json',dict(milestone=MID,files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p.read_bytes())) for p in evidence_files]))
support=[p.relative_to(ROOT).as_posix() for p in sorted(REPORT.glob('*.md')) if p.name!='SUMMARY.md']
support+=['docs/NEXT_SESSION.md','docs/state_authority_model.md','docs/DEVELOPMENT_CONSTITUTION.md','docs/review_handoff_standard.md']
support+=['game/'+n+'.py' for n in ('api','storage','object_marking','object_instances','object_observation',
    'conversational_orchestration','intent_parser','physical_adjudication','exploration','skill_checks',
    'narration_authorization','player_http_projection','immutable_valid_response','publication_contract','state_authority')]
support+=added+[p.relative_to(ROOT).as_posix() for p in evidence_files]+[(OUT/'evidence_manifest.json').relative_to(ROOT).as_posix()]
config=dict(campaign_id=MID,campaign_name='PR-PLAY — Trusted Visibility Classification and Revision Lifecycle',campaign_date='2026-11-09',
    purpose='Bounded trusted authoring, persistence and integration planning',objective_status='A/PASS — bounded internal classification',
    executive_summary=reports['SUMMARY'],changes=dict(production=changed,validation=[focused],tooling=['Cycle-local guarded runner and evidence/archive scripts'],
    documentation=['15 reports; historical NEXT_SESSION retained'],generated_artifacts=['Bounded evidence and fresh standard review exports']),
    testing=dict(focused=focused,broader=reg+' '+predecessors+' '+supp,runtime_validation='Real atomic failures/reload/snapshot timelines and unchanged twelve HTTP turns',
    full_suite='Not run',model_runtime_boundary='Zero provider calls; disabled providers and non-loopback audit guard',
    new_regressions='[]',pre_existing_failures=failure_list),decisions_requiring_human_review=['No further authorization required for this bounded implementation.'],
    known_problems=dict(campaign_specific=[limits],pre_existing=['Combined and supplemental unchanged baseline failure identities; see regression report.']),
    missing_concepts=['Grounded player marking action and observation/publication integration.'],does_not_prove=['T06 completion, authenticated public grants, full suite, live-model or gameplay improvement.'],
    recommended_next_step=next_step,self_contained_review_test='CRC, canonical/evidence hashes, classification/authority/replay/persistence/disclosure/regression/T06/handoff claims reopened.',
    primary_report=(REPORT/'SUMMARY.md').relative_to(ROOT).as_posix(),supporting_files=[dict(path=p,role='implementation_or_evidence',canonical=True,
        why='Explicit source, contract or measured verification evidence for this bounded cycle.') for p in dict.fromkeys(support)])
write('review_handoff.json',config)
print(focused); print(reg); print(predecessors); print(supp)

