"""Assemble this cycle's measured evidence and standard review configuration."""
from pathlib import Path
import difflib
import gzip
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
MID='pr_play_object_marking_disclosure_policy'
REPORT=ROOT/'development/campaigns/product_realization'/MID
REPORT.mkdir(parents=True,exist_ok=True)

def read(name):
    p=OUT/name
    raw=p.read_bytes() if p.exists() else gzip.decompress((OUT/(name+'.gz')).read_bytes())
    return json.loads(raw.decode('utf-8-sig'))
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
def sha(raw): return hashlib.sha256(raw).hexdigest()

def summary(mode):
    tree=ET.parse(OUT/(mode+'_junit.xml')); rows=list(tree.iter('testcase'))
    failures={t.attrib['classname'].replace('.','/')+'.py::'+t.attrib['name']:t.find('failure').text
              for t in rows if t.find('failure') is not None}
    return dict(total=len(rows),passed=sum(not any(t.find(k) is not None for k in ('failure','error','skipped')) for t in rows),
        failed=len(failures),errors=len(list(tree.iter('error'))),skipped=len(list(tree.iter('skipped'))),
        failures=failures,command=read(mode+'_command.json'),execution=read(mode+'_execution.json'))

modes=[prefix+name for prefix in ('before_','after_')
       for name in ('combined','inspection','marking','identity','inventory_snapshot','preservation')]
modes+=['verified_observation','additional_visibility','reference_visibility']
results={m:summary(m) for m in modes}
b,a=results['before_combined'],results['after_combined']
results['new_failures']=sorted(set(a['failures'])-set(b['failures']))
results['newly_passing']=sorted(set(b['failures'])-set(a['failures']))
assert not results['new_failures'] and not results['newly_passing']
for name,row in results.items():
    if not isinstance(row,dict) or 'errors' not in row: continue
    assert row['errors']==row['skipped']==0
    if 'combined' not in name and 'visibility' not in name: assert row['failed']==0,(name,row)
    assert not row['execution']['network_blocks']
results['live_provider_calls']=0
ref=results['reference_visibility']; vis=results['additional_visibility']
assert set(ref['failures'])==set(vis['failures']) and ref['passed']==vis['passed']
assert ref['execution']['feature_absent_control'] and not ref['execution']['observation_imported']
results['supplemental_new_failures']=sorted(set(vis['failures'])-set(ref['failures']))
write('regression_results.json',results)

def normalize(value):
    if isinstance(value,dict): return {k:normalize(v) for k,v in value.items() if k!='performance'}
    if isinstance(value,list): return [normalize(v) for v in value]
    if isinstance(value,str) and value.startswith('clue_text_digest:'): return 'clue_text_digest:PROCESS_LOCAL'
    return value

old=read('before_sequence.json')['turns']; new=read('after_sequence.json')['turns']
comparison=[]
for x,y in zip(old,new):
    publication=y['after']['session'].get('last_publication',{})
    prior=y['before']['session'].get('last_publication',{})
    comparison.append(dict(turn=y['id'],before=x['visible'],after=y['visible'],
        text_equal=x['visible']==y['visible'],character_equal=x['after']['character']==y['after']['character'],
        scene_equal=x['after']['session']['active_scene_id']==y['after']['session']['active_scene_id'],
        resolution_equal=normalize(x['resolution'])==normalize(y['resolution']),
        no_implicit_identity_or_marking=all(not any(k in r for k in ('instance_id','markings','marking_visibility'))
            for r in y['after']['character'].get('inventory',[]) if isinstance(r,dict)),
        publication_pointer_consistent=publication.get('visible')==y['visible'] or
            (y['id'] in ('T06','T12') and publication==prior),publication=publication))
flags=('text_equal','character_equal','scene_equal','resolution_equal','no_implicit_identity_or_marking','publication_pointer_consistent')
assert len(comparison)==12 and all(all(r[k] for k in flags) for r in comparison)
write('twelve_turn_comparison.json',dict(turns=comparison,live_provider_calls=0,
    normalization='Only performance timings and existing process-local clue_text_digest values.'))
def selected(r):
    session=r['after']['session']
    return dict(id=r['id'],request=r['request'],visible=r['visible'],resolution=r['resolution'],
        character=r['after']['character'],session={k:session[k] for k in
            ('campaign_run_id','active_scene_id','scene_state','scene_runtime','clue_knowledge','last_publication','turn_counter') if k in session})
write('twelve_turn_state_evidence.json',dict(before=[selected(r) for r in old],after=[selected(r) for r in new]))
# Compress only these two cycle-owned raw outputs; retain every original byte.
for name in ('before_sequence.json','after_sequence.json'):
    p=OUT/name
    if p.exists():
        raw=p.read_bytes(); compressed=gzip.compress(raw,mtime=0)
        assert gzip.decompress(compressed)==raw
        (OUT/(name+'.gz')).write_bytes(compressed)
        p.unlink()

before=read('before_manifest.json')
after={p:sha((ROOT/p).read_bytes()) for p in before}
changed=sorted(p for p in before if before[p]!=after[p])
assert changed==[],changed
added=['game/object_observation.py','tests/test_object_observation.py']
after.update({p:sha((ROOT/p).read_bytes()) for p in added})
write('after_manifest.json',after)
write('source_changes.json',dict(changed_existing=changed,added=added,protected_files=len(before),
    frozen_fixture_changes=[],production_data_changes=[],unchanged_protected_files=len(before)))
diff=''.join(''.join(difflib.unified_diff([], (ROOT/p).read_text().splitlines(True),
    fromfile='/dev/null',tofile=p)) for p in added if p.startswith('game/'))
(OUT/'production.diff').write_text(diff,encoding='utf-8')
identity=read('entry_identity.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==identity['head']
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()==identity['branch']

timeline=read('observation_timeline.json')
assert [len(s['result']['properties'][0]['values']) for s in timeline['snapshots']]==[0,2,1]
assert timeline['current_result']==timeline['reloaded_result']
purity=read('read_only.json'); assert purity['state_equal'] and purity['disk_equal'] and purity['before_hash']==purity['after_hash']
assert read('information_leakage.json')['leaks']==[]
assert read('noninterference.json')['hidden_variants_equal']
for name in ('pf1e@1','rules_light@1','scifi@1'):
    row=read('observation_portability_'+name+'.json'); assert row['before']==row['after']
performance=read('observation_performance.json')

def totals(r): return f"{r['passed']} passed / {r['failed']} failed / {r['errors']} errors / {r['skipped']} skipped ({r['total']} tests)"
reg=f"Combined before: {totals(b)}. After: {totals(a)}. New failures: {results['new_failures']}; newly passing: {results['newly_passing']}."
focused=f"{results['verified_observation']['passed']} observation tests passed; supplemental visibility/confidentiality/publication: {totals(vis)}, identical failure identities/pass count with the new module import-blocked in a feature-absent control."
predecessors='; '.join(f"{n}: {results['before_'+n]['passed']} before / {results['after_'+n]['passed']} after" for n in
    ('inspection','marking','identity','inventory_snapshot','preservation'))
limitations=('Trusted internal Python entry only. No authenticated observation-decision issuer exists; the private typed grant is an upstream assertion, '
    'not cryptographic authentication or independent physical-feasibility verification. Caller must supply a coherent authoritative character snapshot '
    'under the existing read lane and reestablish grants when current visibility/access/scene evidence changes. Revision plus relevant-state fingerprint '
    'detect target changes, but the service does not independently load scene state, revoke rights or adjudicate reachability. Visibility metadata is '
    'consumed from authoritative object state; no classification authoring/migration API ships. Existing legacy markings therefore remain undisclosed '
    'until upstream establishes classification. No player route, natural-language observation, AI narration, T06 completion, mechanics, transfers or '
    'general-purpose property ontology. No full-suite, independent holdout, live-model or gameplay-improvement claim. Internal Python runtime is not '
    'a cryptographic constant-time boundary; no observer-facing timing, hidden counts, diagnostics, receipt traversal or public timing route is exposed.')
next_step='Exactly one recommended next milestone: `pr_play_object_visibility_authoring` — bounded trusted authoring and revision lifecycle for object marking visibility metadata, before any player observation integration. Do not begin automatically.'
failure_list='\n'.join('- '+k for k in b['failures'])
commands='\n\n'.join('### '+name+'\n\n```text\n'+row['command']['executable']+'\n'+json.dumps(row['command']['args'])+'\n```\n\n'+totals(row)
    for name,row in results.items() if isinstance(row,dict) and 'command' in row)
reports={
'SUMMARY':f'**A/PASS for bounded trusted internal object disclosure.**\n\n{focused}\n\n{reg}\n\n{predecessors}.\n\nOne new production module, no existing production changes. Current active markings project through a reusable category contract and a single concrete marking adapter. Visible/concealed/restricted permissions are consumed, never adjudicated. Unknown legacy classification fails closed; ordinary empty visual results mean unknown, not absence. Hidden, removed, unrelated and private lineage data do not escape. Real save/reload and snapshots preserve permitted results. All twelve HTTP turns unchanged. Live provider calls: **0**.\n\n'+limitations,
'BASELINE':f"Branch `{identity['branch']}`; HEAD `{identity['head']}`. Entry status: entry_git_status.txt. All {len(before)} protected source/test/data/tool hashes: before_manifest.json. Before edits, 72 inspection/removal, 76 marking/atomic, 52 identity, 50 inventory/snapshot and 143 preservation passed. {reg}\n\nExact baseline failures:\n\n{failure_list}\n\nCode/report cross-check: object_marking.inspect_markings exposes full active records (including private authorization/request lineage) to trusted internal callers and validates historical receipts. It is not a player projection. Mark records have no visibility classification and exact MARK_FIELDS validation precludes casually appending per-mark fields. Existing row-level opaque fields are preserved. Identity validation is owned by object_instances; observation reuses its validator without copying receipt history. Existing context caller_id strings are trusted assertions, not authentication. No reset/clean/stash/revert/checkout/commit/push performed.",
'DISCLOSURE_OWNERSHIP':'''Decision **B**: add narrow shared game.object_observation, using existing identity and character-host authority. No owner already supplies observation of durable instance properties.

| Responsibility | Existing owner and reference |
|---|---|
| Scene/public entity visibility | game/narration_visibility.py: build_narration_visibility_contract; game/scene_state_anchoring.py: public read contract |
| Checks and perception success | game/skill_checks.py: resolve_skill_check; game/exploration.py: process_investigation_discovery |
| Hidden/authored inspection targets | game/referenced_surface.py: target binding/render_referenced_surface_inspection_line; exploration.resolve_interactable_hidden_fact_text |
| Resolved clue disclosure | game/authorized_information.py: revealed_information; only selected successful resolver output |
| Internal object inspection | game/object_marking.py: inspect_markings; full authoritative read, unsuitable for observer payloads |
| Provider evidence projection | game/narration_authorization.py: project_narration_payload |
| Player HTTP state | game/player_http_projection.py: source-specific allowlists; inventory ITEM has no markings |
| Immutable publication | game/immutable_valid_response.py: seal_delivery_contract/verify_delivery_record; game/publication_contract.py |
| State ownership | game/state_authority.py: WORLD_STATE authoritative and PLAYER_VISIBLE_STATE derived; storage character host |

Extending narrative visibility would couple durable instances to scene prose/entity matching. Extending authorized_information would couple generic property reads to completed clue resolution. Extending internal inspect_markings would change its intentionally private contract and couple observation to receipt history. The narrow projector consumes existing durable identities and established internal authority instead; it neither decides perception nor publishes. Existing modules, authority registry and endpoints remain unchanged. Approved architecture sources: development/campaigns/product_realization/pr_play_object_identity_architecture/{CORE_RULESET_BOUNDARY,OBJECT_INSTANCE_CONTRACT,MODIFICATION_CONTRACT,ACTION_RESOLUTION_CONTRACT,MUNDANE_AFFORDANCE_POLICY,IMPLEMENTATION_ROADMAP}.md. This cycle implements the read boundary only.''',
'OBSERVATION_CONTRACT':'''Internal function observe_object(character, request, *, authorization=None). Caller supplies a coherent authoritative character snapshot; target uses durable campaign_run_id+instance_id, never name/index. Exact v1 request fields: version, campaign_run_id, character_id, instance_id, observer_id, scope, categories. Categories are unique supported strings; currently only markings. Empty/all/unsupported/duplicate requests refuse. The closed _PROJECTORS map separates contract orchestration from _project_markings; future categories add bounded code adapters, not executable policy/plugins.

Authorization is a frozen private _ObservationAuthorization, established only by trusted Python orchestration through _establish_observation_authorization. It binds observer, campaign, character host, target, scope, requested categories, object revision and fingerprint of relevant active state/classification. Mandatory bounded decision_ref, visibility_ref and access_ref stay private. Missing/malformed/JSON/wrong-bound/stale/conflicting grants refuse. Reestablishing a grant is an upstream assertion; it performs no check or reachability decision.

Success DTO: version=1, status=observed, target={campaign_run_id,instance_id}, properties=[{category,knowledge,coverage,values}], limitations and evidence. Marking values: content, presentation=inscription, result-local evidence_ref and authorized-content SHA-256. Evidence repeats only safe category/ref/content fingerprint. References are scoped by result target/category; no mutation UUID or private source reference. General refusal: status=unresolved, target=null, empty properties/evidence, constant observation_unavailable limitation.

Knowledge=known_present means at least one permitted value; coverage=subset does not claim global completeness. An empty subset means knowledge=unknown even when current state happens to have zero marks. Knowledge=known_absent requires a complete grant (concealed=true, restricted_scopes=("*",), complete=true), a valid empty active collection and thus no ambiguous active classification. Missing/invalid classification yields subset/unknown for an empty result even with complete authority. Full authority with valid classified marks yields complete known_present. Ordinary visual payloads are identical across absent/concealed/restricted/legacy-only states and reveal no undisclosed count.''',
'MARKING_VISIBILITY':'''Small optional object-row metadata (not inside exact legacy marking records):

```json
{"marking_visibility":{"version":1,"markings":{"<existing-mark-UUID>":{"classification":"visible"}}}}
```

Classifications: visible; concealed; restricted with exactly one additional scope string. Ordinary established visual authority includes visible only. Explicit concealed=true permits concealed classifications. Restricted marks require a matching restricted_scopes tuple; wildcard is explicit trusted all-scopes authority. Complete observation requires both concealed authority and wildcard restricted authority. Publicly visible does not mean public access: observer/target/scope/access authorization is still mandatory.

Missing/unknown/ambiguous metadata never defaults to visible or concealed. Existing source_disclosed/write authorization does not prove later visibility. Legacy records stay byte-identical and undisclosed until upstream supplies evidence. Classification is object state consumed by the projection, not inferred from inventory, names, mechanics or text. Unmatched stale metadata for removed marks is ignored; only active UUIDs are looked up. No receipt or latest-timeline lookup. IDs, revisions, content, receipts, unknown fields and extensions are untouched. Metadata survives ordinary storage/snapshots as existing opaque row data. No marking-application API, schema migration, new writer or arbitrary ACL evaluator is introduced. Fixture authoring uses existing trusted storage solely to establish controlled state; shipping classification-authoring lifecycle is deferred.''',
'INFORMATION_BOUNDARY':'''Four distinct boundaries remain: authoritative character state; trusted established observation context; detached allowlisted disclosure DTO; future narration/publication. Only the first three are implemented. Nothing is fed to provider prompts or HTTP responses.

Permitted values: authorized exact content, constant inscription presentation, result-local evidence reference and SHA-256 of that permitted content. Target reference is the requested durable campaign/instance identity. No internal marking/modification UUID, applied revision, request ID/digest, authorization object/token/reference, identity provenance, source reference, receipt/history, hidden extension, unrelated property, inventory record or object snapshot returns.

The authority fingerprint is private and hashes only relevant active fields and classifications; neither historical receipts nor unrelated private extensions are traversed. Serialized DTO checks include sentinel values and actual internal request/digest/marking IDs, not just missing keys. Noninterference controls change hidden count/content and receipt/extension data while requiring identical authorized DTOs. Ordinary subset limitations are constant and do not reveal why a mark was omitted. Unresolved diagnostics are uniform. No observer-facing timing fields/branches or public route are introduced; benchmark timings stay internal. This is not a cryptographic constant-time Python implementation. Future public integration must retain the trusted issuance and existing projection/immutable publication boundaries.''',
'IMPLEMENTATION':'''Only new production file: game/object_observation.py. It adds a private frozen authorization record, trusted establishment seam, identity-based host resolution using object_instances._identity_error, relevant-state fingerprint, category orchestration, uniform unresolved result and _project_markings adapter. No files in existing production are modified.

The service reads supplied current character state; storage remains the sole durable host and existing API/read lane remains caller authority. No allocation, mutation, persistence, scene checks, provider, publication or parser imports. Existing internal inspect_markings stays private/full-state. Existing exact marking schemas and add/remove receipts remain unchanged. Visibility resides in an optional opaque object-level map, so old callers continue to operate unmodified; timeline tests apply additional marks and remove marks with that map present.

Tests: tests/test_object_observation.py. Cycle tooling: artifacts/pr_play_object_marking_disclosure_policy/run_checks.py, finalize.py, seal_review.py. The final focused run is verified_observation; focused_observation/final_observation are earlier development iterations retained for transparency. No existing test/fixture changed. No new gameplay route or provider work.''',
'READ_ONLY_VERIFICATION':f'''The focused read-only test forbids save_character, save_session, save_world, atomic writer, UUID allocation and GM generation where available. Input deep equality, repeated detached DTO equality and every temporary runtime file hash are checked. before_hash={purity['before_hash']}; after_hash={purity['after_hash']}. Disk equality={purity['disk_equal']}. Tests run with disabled provider/interpretation/expression/retries and a non-loopback network audit guard. No network attempts or provider calls in completed runs.

No identity assignment, revision increment, marking mutation, receipt creation, inventory reorder, equipment/scene/world update, campaign fact, clock advancement or narration log write occurs. Production contains no storage/provider call. Per-read complexity: character inventory identity validation plus bounded selected active state; no full-world or receipt scan. Evidence: read_only.json and noninterference.json. Existing production and canonical data hashes remain identical to entry.''',
'PERSISTENCE_VERIFICATION':'''observation_timeline.json uses real atomic character save/load and create_snapshot/load_snapshot. Apply A and B with visible classification, capture pre-removal snapshot, remove A through existing API, observe B only, save/reload and observe identical B-only result. An old pre-removal grant cannot inspect the changed target. Restore empty/pre-removal/post-removal snapshots: permitted values are respectively [], [A,B], [B]. Fresh corresponding context is established against each restored state. Removed A remains in historical receipt evidence but never in current projection. Snapshot rollback consults its own active state, not future external receipts/knowledge. IDs, metadata, revisions and original receipt semantics are retained. Read/save/snapshot storage infrastructure is unchanged; existing single-process/multi-file rollback limitations persist.''',
'NEGATIVE_CONTROLS':'''Authored controls cover missing/malformed/serialized grants, wrong observer/campaign/character/instance/scope/category, stale revision and content/classification changes without revision, blank evidence references, conflicting complete permissions and unsupported/all/history requests. Durable duplicate/malformed/partial/cross-campaign identities fail without migration. Mixed visible/concealed/restricted/legacy records require exact permission; hidden and restricted records cannot be inferred from an empty visual subset. Identical object A/B and reorder controls use durable IDs. Invalid active IDs/revisions/types/versions/content/size/capacity refuse. Malformed or missing classification never guesses. Repeated requests do not widen authority.

information_leakage.json verifies both explicit allowlisted field shape and serialized sentinel values, including actual private request IDs, request digests and mutation UUIDs. noninterference.json verifies equal ordinary output for different concealed/restricted/legacy counts/content and unrelated private history/extensions. Removed metadata/history is ignored even when supplied. Snapshot/read-only/extension controls cover future-state exclusion and purity. These are authored variations, not an independently held-out generalization claim.''',
'RULESET_PORTABILITY':'''The same mechanism and authorized inscription are tested with pf1e@1 (AC/perception DC), rules_light@1 (tags/private data) and scifi@1 (sensor/battery/encryption). Exact whole-character equality across observation and actual save/reload proves extensions are opaque and preserved. The projected value is identical across all three; no extension is inspected for permission. Evidence: observation_portability_*.json and focused JUnit. No DC/skill/spell/proficiency/rarity/crafting/sensor interpretation occurs; those remain upstream authority or future adapters. This demonstrates boundary portability, not a complete alternate-ruleset game runtime.''',
'REGRESSION_RESULTS':f'''{reg}\n\n{focused}\n\nSeparate identical predecessor selections: {predecessors}. No overlaps are summed into combined totals. Supplemental coverage does not replace the established before/after command. Its two failures are tests/test_pr_play_20_response_confidentiality.py::test_successful_start_serialized_boundary (HTTP 422 versus expected 200) and ::test_rejected_turn_with_composed_state (missing character_secret in existing player DTO). These are unrelated existing contract/fixture disagreements; no repair is attempted. Reference rerun explicitly blocks importing game.object_observation, verifies it never loaded, and uses the exact same prior-source bytes/selection: 238 passed / 2 failed, same identities. This is a post-implementation feature-absent control, not a fabricated pre-edit run. Existing production source hashes are all identical to entry.\n\nCombined protects immutable publication/travel and narration; preservation protects state authority, T04/T05/T06 and closed inspection. Zero collection errors/skips and zero live provider/network calls. Full suite not run. All exact failure texts and command arrays retained in regression_results.json.\n\nBaseline failure identities:\n\n{failure_list}\n\nExact commands:\n\n{commands}''',
'TWELVE_TURN_COMPARISON':'''Established unchanged provider-free twelve-turn HTTP harness, before and after. All text, character states, scenes and normalized resolutions match. T04 contact, T05 clue, T09 grounded recall and T11 travel remain successful. T06 remains unsupported. T06/T12 retain prior publication pointer; all other visible text matches current pointer. No implicit object observation, metadata migration, identity assignment, marking mutation, hidden publication or provider call. New service is not imported by gameplay. Only process-local clue digests/performance are normalized.

'''+ '\n\n'.join(r['turn']+': unchanged — '+str(r['after']) for r in comparison),
'PERFORMANCE':'''100 observations per small representative fixture; internal authorization establishment/validation and projection serialization measured separately. No enforced machine-specific performance threshold. No live provider calls, retries, prompt expansion, full-world scan, ACL engine, database or endpoint. Character identity validation is O(inventory rows); selected active projection is at most 16 markings, 2048 UTF-8 bytes each/8192 permitted bytes. No history scan. JSON output contains no timing metadata. Measurements (microseconds, local host):

```json
'''+json.dumps(performance,indent=2)+'\n```',
'NEXT_STEP_DECISION':f'''Recommend **A/PASS** for the bounded trusted internal projection: authored ordinary/adversarial disclosure, persistence, snapshots, purity, portability and unchanged regressions verified. No gameplay improvement or authenticated external-access claim.\n\n{next_step}\n\n{limitations}''',
'INTEGRITY':f'''Branch/HEAD unchanged: {identity['branch']} / {identity['head']}. Entry dirty work preserved. All {len(before)} previously protected files remain byte-identical, including existing production, canonical data and frozen tests/fixtures. Only production addition is game/object_observation.py; test addition tests/test_object_observation.py. Incremental production.diff is the new file, not unrelated HEAD diff. No prohibited Git operations, commits or pushes.

Entry NEXT_SESSION and review are saved in this cycle. NEXT_SESSION is prepended while retaining all historical bytes as suffix. Sixteen reports, exact test outputs, fixtures/results, hashes, timelines, performance, regression and twelve-turn evidence feed an explicit standard handoff configuration. Review generator emits fresh stable/history/dated ZIPs. seal_review.py independently reopens archives, verifies CRC, all included canonical/evidence SHA-256 values, report identity, contract, hidden controls, read-only/persistence/snapshot/portability/regression/twelve-turn/handoff claims. Final archive SHA-256 and reopen record remain external to avoid circular hashing. Final seal paths: archive_sha256.txt and archive_verification.json. Live provider calls: 0.'''
}
for name,body in reports.items():
    (REPORT/(name+'.md')).write_text('# '+name.replace('_',' ').title()+'\n\nMilestone: `'+MID+'`. Date: 2026-11-09.\n\n'+body+'\n',encoding='utf-8')

handoff=(f'# NEXT_SESSION — PR-PLAY Object Observation and Disclosure Policy (2026-11-09)\n\n'
    f'**A/PASS for bounded trusted internal disclosure.** Milestone `{MID}`. Branch {identity["branch"]}; HEAD {identity["head"]}. Dirty work preserved; no commits/pushes. Live provider calls **0**.\n\n'
    'New game/object_observation.py consumes typed established authorization and object-level versioned marking_visibility metadata. '
    'It returns only authorized current active content through a reusable category contract and one marking adapter. '
    'Legacy ambiguity stays undisclosed; empty visual subset is unknown, complete authority can establish absence. '
    'Observer/target/scope/revision/relevant-state binding, hidden/history isolation and read-only behavior verified. '
    'No existing production changes, public route, narration or T06 activation.\n\n'
    f'{focused} {predecessors}. {reg} All twelve HTTP turns and publication pointers unchanged.\n\n'
    f'{next_step}\n\n{limitations}\n\n'
    f'Minimum: development/campaigns/product_realization/{MID}/SUMMARY.md, DISCLOSURE_OWNERSHIP.md, OBSERVATION_CONTRACT.md, MARKING_VISIBILITY.md, '
    'INFORMATION_BOUNDARY.md, REGRESSION_RESULTS.md, NEXT_STEP_DECISION.md, INTEGRITY.md. '
    f'Evidence: artifacts/{MID}/observation_timeline.json, information_leakage.json, read_only.json, regression_results.json, '
    'twelve_turn_comparison.json, source_changes.json, archive_sha256.txt and archive_verification.json. Review: handoff/CURRENT_REVIEW.md.\n\n---\n\n')
(ROOT/'docs/NEXT_SESSION.md').write_bytes(handoff.encode()+(OUT/'entry_next_session.md').read_bytes())
write('milestone_identity.json',dict(milestone=MID,verdict='A/PASS',live_provider_calls=0))
(OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git','status','--short']))
write('files_created.json',dict(production=added[:1],validation=added[1:],reports=[p.relative_to(ROOT).as_posix() for p in sorted(REPORT.glob('*.md'))],
    artifacts=[p.relative_to(ROOT).as_posix() for p in sorted(OUT.iterdir()) if p.is_file()],
    handoff='Fresh stable/history/dated standard exports and external archive seal generated by seal_review.py'))

# Explicit bounded selection: no recursive artifact tree or old archives.
excluded={'review_handoff.json','evidence_manifest.json','archive_sha256.txt','archive_verification.json','handoff_generation.log'}
evidence_files=[p for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in excluded]
write('evidence_manifest.json',dict(milestone=MID,files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p.read_bytes())) for p in evidence_files]))
support=[p.relative_to(ROOT).as_posix() for p in sorted(REPORT.glob('*.md')) if p.name!='SUMMARY.md']
support+=['docs/NEXT_SESSION.md','docs/state_authority_model.md','docs/DEVELOPMENT_CONSTITUTION.md','docs/review_handoff_standard.md']
support+=['game/'+n+'.py' for n in ('object_observation','object_instances','object_marking','authorized_information','narration_authorization',
    'player_http_projection','immutable_valid_response','publication_contract','state_authority')]
support+=['tests/test_object_observation.py']
support += ['development/campaigns/product_realization/pr_play_object_identity_architecture/'+n+'.md' for n in
    ('CORE_RULESET_BOUNDARY','OBJECT_INSTANCE_CONTRACT','MODIFICATION_CONTRACT','ACTION_RESOLUTION_CONTRACT','MUNDANE_AFFORDANCE_POLICY','IMPLEMENTATION_ROADMAP')]
support += ['game/api.py','game/storage.py','game/narration_visibility.py','game/scene_state_anchoring.py']
support += [p.relative_to(ROOT).as_posix() for p in evidence_files]+[str((OUT/'evidence_manifest.json').relative_to(ROOT)).replace('\\','/')]
config=dict(campaign_id=MID,campaign_name='PR-PLAY — System-Agnostic Object Observation and Disclosure Policy',campaign_date='2026-11-09',
    purpose='Bounded internal production projection and information-boundary verification',objective_status='A/PASS — bounded trusted internal disclosure',
    executive_summary=reports['SUMMARY'],changes=dict(production=added[:1],validation=[focused],tooling=['Cycle-local guarded runner and evidence/archive assembly'],
        documentation=['16 reports; historical NEXT_SESSION bytes retained'],generated_artifacts=['Bounded evidence and fresh standard review exports']),
    testing=dict(focused=focused,broader=reg,runtime_validation='Real save/reload/snapshot timeline; twelve unchanged HTTP turns',full_suite='Not run',
        model_runtime_boundary='Zero live provider calls; disabled provider and network audit guard',new_regressions='[]',pre_existing_failures=failure_list),
    decisions_requiring_human_review=['No additional authorization required for this bounded internal capability.'],
    known_problems=dict(campaign_specific=[limitations],pre_existing=['Twenty unchanged combined-selection failures; two supplemental confidentiality contract failures reproduced with feature import blocked.']),
    missing_concepts=['Trusted classification authoring lifecycle and later player integration remain deferred.'],
    does_not_prove=['Authenticated public observation, independent physical feasibility, AI observation narration, T06 completion, full suite or broad gameplay improvement.'],
    recommended_next_step=next_step,self_contained_review_test='Reopened ZIP CRC, canonical/evidence hashes and bounded disclosure/persistence/regression/handoff claims.',
    primary_report=(REPORT/'SUMMARY.md').relative_to(ROOT).as_posix(),supporting_files=[dict(path=p,role='implementation_or_evidence',canonical=True,
        why='Explicit bounded observation contract, source or measured verification evidence.') for p in dict.fromkeys(support)])
write('review_handoff.json',config)
print(focused);print(reg)
