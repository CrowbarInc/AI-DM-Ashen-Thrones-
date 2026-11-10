"""Generate bounded investigation reports from recorded local evidence."""
from pathlib import Path
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
ID='pr_play_t06_persistent_manipulation'
REPORT=ROOT/'development/campaigns/product_realization'/ID
REPORT.mkdir(parents=True,exist_ok=True)
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
def md(name,text): (REPORT/name).write_text(text.strip()+'\n',encoding='utf-8')
def results(name):
    tree=ET.parse(OUT/(name+'_junit.xml'))
    suites=list(tree.iter('testsuite'))
    totals={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    totals['passed']=totals['tests']-totals['failures']-totals['errors']-totals['skipped']
    totals['failed_nodes']=[t.get('classname').replace('.','/')+'.py::'+t.get('name') for t in tree.iter('testcase') if t.find('failure') is not None]
    return totals
r={k:results(k) for k in ('baseline','after','focused','persistence_controls')}
r['new_failure_identities']=sorted(set(r['after']['failed_nodes'])-set(r['baseline']['failed_nodes']))
r['resolved_failure_identities']=sorted(set(r['baseline']['failed_nodes'])-set(r['after']['failed_nodes']))
r['live_provider_calls']=0
historical=json.loads((ROOT/'artifacts/pr_play_t04_local_action/test_results.json').read_text())['remaining_failures']
r['baseline_vs_predecessor_new']=sorted(set(r['baseline']['failed_nodes'])-set(historical))
r['baseline_vs_predecessor_not_reproduced']=sorted(set(historical)-set(r['baseline']['failed_nodes']))
r['recurrent_predecessor_fluctuation_assessment']={
    'test_duplicate_refusal_does_not_publish':'Events file contains published clarification instead of remaining empty.',
    'test_two_refusals_then_gameplay_advances':'RuntimeError: This portal is not running during TestClient exit.',
    'test_save_reload_keeps_the_preceding_publication':'No OPERATIONAL_REFUSAL log entry after greeting/clarification.',
    'provenance':'All three named as previously failing, not repaired, in T04 REGRESSION_RESULTS.md. Recur in fresh untouched production baseline.'}
write('test_results.json',r)
before=read('before_sequence.json'); final=read('final_sequence.json')
t=read('before_t06.json'); f=read('final_t06.json')
text=t['request']; clue=t['before']['session']['clue_knowledge']['notice_patrol_route']
rows=[]
for x,y in zip(before['turns'],final['turns']):
    fields={'visible':(x['visible'],y['visible']),
            'kind':(x['resolution'].get('kind'),y['resolution'].get('kind')),
            'reason':(x['resolution']['metadata'].get('conversational_decision',{}).get('reason'),y['resolution']['metadata'].get('conversational_decision',{}).get('reason')),
            'scene':(x['after']['session']['active_scene_id'],y['after']['session']['active_scene_id']),
            'inventory':(x['after']['character'].get('inventory'),y['after']['character'].get('inventory')),
            'knowledge':(x['after']['session'].get('clue_knowledge'),y['after']['session'].get('clue_knowledge')),
            'state_changes':(x['resolution'].get('state_changes'),y['resolution'].get('state_changes')),
            'publication':((x['after']['session'].get('last_publication') or {}).get('visible'),(y['after']['session'].get('last_publication') or {}).get('visible'))}
    rows.append({'id':x['id'],'request':x['request'],'before':x['visible'],'after':y['visible'],
                 'differences':[k for k,(a,b) in fields.items() if a!=b]})
write('twelve_turn_comparison.json',{'milestone':ID,'turns':rows,'changed_turns':[x['id'] for x in rows if x['differences']]})
prereqs={'source':{'status':'established','reference':'clue_knowledge.notice_patrol_route','record':clue},
         'target':{'status':'unresolved','requested':'my sleeve','object_id':None,'reason':'No clothing or equipped-item record in seeded character.'},
         'material':{'status':'unknown','requested':'a bit of mud','reason':'Muddy gate scenery and a mud-track clue do not establish an accessible usable supply or suitable marking medium.'},
         'suitability':{'status':'unknown','reason':'No identified receiving object, material compatibility, or writable surface contract.'},
         'character_capability':{'status':'unknown','reason':'Skills do not establish marking-material use or legibility.'},
         'adjudication':{'status':'unresolved','reason':'No configured copy/mark action or prerequisite validator.'},
         'runtime_evaluated_prerequisites':False,
         'note':'This is investigator evaluation from snapshots; runtime declines before these checks.'}
write('prerequisite_evaluation.json',prereqs)
write('mutation_evidence.json',{'proposal':None,'validation':'not_reached','application':'not_attempted',
      'state_changes':f['resolution']['state_changes'],
      'character_unchanged':f['before']['character']==f['after']['character'],
      'world_unchanged':f['before']['world']==f['after']['world'],
      'scene_unchanged':f['before']['scene']==f['after']['scene'],
      'knowledge_unchanged':f['before']['session'].get('clue_knowledge')==f['after']['session'].get('clue_knowledge'),
      'publication_pointer_unchanged':f['before']['session'].get('last_publication')==f['after']['session'].get('last_publication'),
      'physical_modification_created':False})
architecture={
 'game/defaults.py':['def default_character(', '"inventory":'],
 'game/importers/pf_json_importer.py':['def collect_inventory('],
 'game/conversational_orchestration.py':['def _unbound_physical_decline(', 'reason="unsupported_physical_manipulation"'],
 'game/api.py':['def _nonmutating_conversational_decision_response(', 'deterministic_decision.category != ConversationalDecisionCategory.EXECUTE'],
 'game/world.py':['def apply_resolution_world_updates('],
 'game/physical_adjudication.py':['ROUTINES =', 'def _objects(', 'setdefault("accessible", True)', 'def _write_props(', 'def _consequence(', 'def commit_physical('],
 'game/storage.py':['def runtime_commit_scope(', 'def save_character(', 'def create_snapshot(', 'def load_snapshot('],
 'game/mechanical_claims.py':['Delta-only inventory authority'],
 'game/narration_authorization.py':["'items_added', 'items_removed'"],
 'game/offline_investigation_projection.py':["unsupported ="]}
write('architecture_evidence.json',{path:[{'line':i+1,'text':line.strip()} for i,line in enumerate((ROOT/path).read_text(encoding='utf-8').splitlines()) if any(term in line for term in terms)] for path,terms in architecture.items()})
prior=read('before_manifest.json')
after={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
       for folder in ('game','tests','data','static','prompts') for p in (ROOT/folder).rglob('*')
       if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
write('after_manifest.json',after)
changes={'changed':[p for p,v in prior.items() if after.get(p)!=v], 'added':sorted(set(after)-set(prior)),
         'missing':sorted(set(prior)-set(after)), 'production_changes':[],
         'frozen_changes':[p for p,v in prior.items() if (p.startswith('data/') or p.startswith('tests/fixtures/')) and after.get(p)!=v]}
assert not changes['changed'] and not changes['missing'],changes
assert changes['added']==['tests/test_pr_play_t06_persistent_manipulation.py'],changes
write('source_changes.json',changes)
(OUT/'production.diff').write_text('',encoding='utf-8')
write('persistence_results.json',{'implemented_modification_roundtrip':'not_available_blocked',
      'refused_action_snapshot_restore_retry':'passed','subsequent_known_clue_reference':'passed',
      'focused_results':r['focused'],'existing_persistence_and_authority_results':r['persistence_controls'],
      'limitation':'A negative-state round trip does not demonstrate successful inscription persistence or later object inspection.'})
totals=lambda v:f"{v['passed']} passed / {v['failures']} failed / {v['errors']} errors / {v['skipped']} skipped ({v['tests']} tests)"
decision='Conduct one bounded architecture review to assign item-instance modification ownership and define its validated mutation and inspection contract within existing character persistence.'
summary=f'''# PR-PLAY T06 Persistent Physical Manipulation

Milestone: `{ID}`. Predecessor: `pr_play_t04_local_action`. Cycle verdict: **BLOCKED**. Primary failure class: **architectural**.

Original HTTP T06 reproduces. Parsing recovers a physical interaction but calls its verb `try` and leaves the entire copy clause as an unbound target. `_unbound_physical_decline` selects `unsupported_physical_manipulation`; `_chat_turn` returns before any physical resolver or prerequisite checks. The refusal is truthful but generic.

The known clue is present; an equipped sleeve identity, access, suitability and usable mud supply are not established. More fundamentally, inventory dictionaries can persist JSON but there is no existing item-instance modification validator/application owner, equipment binding, or later item-inspection projection for this action. Adding fields to character inventory alone would not satisfy the authority contract. The experimental physical owner has its own scene-object/posture ledger and no carried-item binding; enabling or repurposing it here would create a parallel authority.

No production files changed. No successful controlled-fixture modification is claimed. The stop conditions in sections 8 and 17 of the request apply; no fabricated A/PASS or B/PARTIAL implementation.

Original and final T06: “{f['visible']}” Character, world, scene and knowledge are unchanged. Refusal text is hard-valid and immutable; the completed-publication pointer still references T05, accurately not recording a completed inscription.

Fresh baseline: {totals(r['baseline'])}. Final same selection: {totals(r['after'])}. New failure identities: {len(r['new_failure_identities'])}. New diagnostic controls: {totals(r['focused'])}. Existing physical/persistence/state-authority controls: {totals(r['persistence_controls'])}. Historical 408/17 is reference only; exact fresh identities are in REGRESSION_RESULTS and test_results.json. No causal repair claim for fluctuating failures.

All twelve published turns and compared authority/state fields are unchanged. T04 contact, T05 disclosure, T09 recall and T11 travel remain. T01/T07 narration, T02 NPC usefulness, T08 acknowledgment, T10 trading and T12 refusal remain deferred. Zero live provider calls; no commits/pushes.

Exactly one proposed next action: {decision}
'''
md('SUMMARY.md',summary)
md('ROOT_CAUSE.md',f'''# Original T06 trace

Request (unchanged):

> {text}

Scene: `frontier_gate`; location Cinderwatch Gate District. Complete prior conversation and T01–T05 state: artifacts/{ID}/before_sequence.json. Exact T06 request, scene, character, world, session, log, raw response, parser returns and sealing events: before_t06.json and final_t06.json.

T05 authorized `notice_patrol_route`: “{clue['text']}” The knowledge record is discovered, explicit, source scene frontier_gate and source interactable notice_board. It identifies the full disclosed warning as the intended copy; no excerpt or paraphrase was requested. No additional patrol records or hidden signals are authorized.

Inventory: one Spellbook (`spellbook`, quantity 1, usable false). There is no equipped clothing record and no sleeve instance. No mud inventory/tool record. The scene contains a muddy gate line; that is environmental evidence, not proof of a usable accessible marking supply or sleeve compatibility. Tool absence in inventory does not prove all environmental materials absent. These prerequisite states remain unknown, not satisfied.

`parse_freeform_to_action` returns null. `recover_actionable_explicit_world_action` returns custom, parser_lane physical_object_interaction, physical_verb try, authored_interactable_id null, target_id the full remainder “to copy … wording”. This is partial intent recovery, not resolved source/target/material parsing.

Selected owner: conversational orchestration's unsupported-physical decline; intent family physical_action; category DECLINE; policy decline_unadjudicated_contact. Physical resolver not reached. Source/target/prerequisite evaluation, mutation proposal/validation/application are all not reached (not rejected proposals). Resolution conversational_decline, success false, state_changes empty, world_updates null, authoritative_mutation false. The gameplay_parser_invoked flag is false although diagnostic parser helpers were called during classification; do not interpret that flag as no parsing at all.

Candidate: “{f['visible']}” Hard-valid true, immutable true, authorization_source conversational_decision:unsupported_physical_manipulation. Accepted text equals published HTTP text. Publication pointer remains T05. No publication failure caused the lack of completion.

Earliest demonstrated boundary: unbound physical request is declined before action ownership/prerequisite adjudication. A parser-only verb extension would still lack target identity, equipment authority, compatibility checks, validated persistent mutation and later inspection. Primary architectural blocker: no existing carried-object modification contract spanning those owners. Experimental physical adjudication is disabled; the decline yields to it when enabled, but its operation set omits copy/write/mark, and its object enumeration includes controlled scene facts/interactables, not character inventory. It defaults accessible to true for enumerated scene objects, unsuitable for assuming this task's unknown prerequisites. It remains unmodified and disabled.
''')
md('MANIPULATION_CONTRACT.md','''# Proposed contract — not implemented

Supported runtime modification class in this cycle: **none**. Proposed scope: one simple non-destructive marking of one established object with an established compatible medium, using only known content; no new independent object, crafting, combat or contested resolution.

Information knowledge is the discovered clue record. A physical representation is a copy on a surface. Persistent object state is the authoritative modification attached to that same object. None implies the next.

Resolve the exact full disclosed clue (or an explicitly requested, grounded excerpt). Preserve its meaning and provenance; never promote hidden facts, speculation, or narration into source truth. Ambiguous sources/content request clarification.

Required positive evidence: stable object identity; ownership or current access; receiving surface suitability; actual tool/material access; compatibility and character capability; no authority veto or unresolved check. False prerequisites decline; unknown prerequisites clarify or remain unresolved. Merely naming an implement does not establish it.

The future proposal must carry target instance id, modification type, exact content, source knowledge reference and version/content fingerprint, material/tool identity, positive preconditions, request id, validation result, expected prior state and applied result. Route validation/application through the designated existing-state owner. Attach the result to the canonical item representation, never a narration-only record, world-flag surrogate or shadow inventory.

Apply atomically through the existing runtime commit scope; no successful publication after failed application. Revalidate prior state, access and source at commit. Stable request identity must avoid replay duplication across save/reload. Only the applied receipt authorizes narration and later object inspection. Snapshot round trips must preserve identity and modification; authored source stays unchanged.

Missing today: item-instance/equipment binding, material/surface compatibility contract, validated item-modification owner and receipt, inspection projection. Character JSON serialization alone supplies neither authority nor semantics. These are architecture-review requirements, not a new executable schema approved by this report.

Excluded: item acquisition, destruction, damage, cutting/engraving requiring adjudication, travel, hidden targets/content, NPC speech, transient contact, generalized object editing. Specialized owner precedence must remain unchanged.
''')
md('IMPLEMENTATION.md','''# Conditional implementation decision

**BLOCKED; production files/functions changed: none.** production.diff is empty. Existing storage can serialize dictionaries and snapshots include character state; storage durability itself is not the blocker.

The conditional implementation gate fails for a complete existing mutation path. Default/imported inventory is id/name/quantity/usable rows; importer ids may identify gear slots or grouped gear, not a validated sleeve part or equipped instance. No item-modification proposal validator/application seam was found in exploration, world updates, character storage or authored consequences. World resolution updates apply flags/counters/clocks. Authored consequences supply finite flag effects. Neither is an object-state owner.

Read-side inventory effects in mechanical_claims, narration_authorization and offline_investigation_projection are delta projections (items_added/items_removed), not mutation application or modification authority. Character notes is a free-text sheet field, not a player action note/physical inscription contract. Journal/knowledge is derived disclosure state and cannot substitute for an object copy.

The experimental physical owner writes controlled scene-entry properties or scene|object overlays, plus posture/position and consequences. It does not enumerate carried items or provide copy/write routines. Extending that ledger for inventory objects would create competing state unless ownership is settled first. It was not activated.

Existing runtime_commit_scope and validate-first snapshot restore are reusable durability mechanisms. Their presence does not validate the proposed content or equipment. No mutation proposal, validation, application or successful narration was added. Save/reload verifies only that a refused copy remains absent. No successful controlled HTTP or persistence result is claimed.

Added tests: tests/test_pr_play_t06_persistent_manipulation.py, six diagnostic cases. Added investigation runner and report/archive evidence under artifacts/pr_play_t06_persistent_manipulation. Exact owner references and line numbers: architecture_evidence.json.
''')
md('T06_BEFORE_AFTER.md',f'''# T06 before and after investigation

> {text}

Before: {t['visible']}

After: {f['visible']}

No production behavior change. Both route to conversational_decline / unsupported_physical_manipulation / decline_unadjudicated_contact, success false. Required source exists; sleeve identity, suitability, compatible accessible material and capability remain unresolved. The engine does not yet evaluate those prerequisites individually.

Mutation proposal: none. Validation/application: not reached. State_changes empty. Character/world/scene/knowledge unchanged. Sealed accepted text equals HTTP published text; immutable and hard_valid true. Completed-publication pointer continues to T05, not a completed inscription. Full snapshots and immutable acceptance are in before_t06.json/final_t06.json; summarized evidence in mutation_evidence.json and prerequisite_evaluation.json.

Original T06 **remains unresolved**. There is no controlled-fixture successful completion. This investigation does not claim a repaired original action.
''')
md('PERSISTENCE_VERIFICATION.md',f'''# Persistence verification

Applied physical modification: none. Immediate and later object inspection of an inscription: not available. Successful modification save/reload and duplicate suppression: not implemented and not proven.

The new snapshot test posts the original T06 after T05, creates a real storage snapshot, restores it with load_snapshot, retries the request, and recalls the known notice on a subsequent HTTP turn. Character remains unchanged, knowledge survives and no physical copy appears. This is a **negative-state** persistence check, not a successful-modification round trip. Diagnostic suite: {totals(r['focused'])}.

Existing physical/persistence/state-authority controls: {totals(r['persistence_controls'])}. These cover established physical receipts, durability/fault rollback and owner guards; they do not establish an inscription mechanism. Detailed test cases and failures: persistence_controls_junit.xml, focused_junit.xml, persistence_results.json. The original notice source is unchanged in both HTTP traces and repeated-request tests.
''')
md('NEGATIVE_CONTROLS.md',f'''# Negative controls

New provider-free HTTP tests: {totals(r['focused'])}.

| Control | Evidence and limit |
|---|---|
| Original inventory / no material record | Original T06 declines; no character/source/knowledge mutation |
| Explicit empty inventory | Same refusal; no invented equipment |
| Unknown inventory field | Same refusal; no assumed equipment |
| Named mud inventory row | No sleeve identity or suitability contract; declines without mutation |
| Hidden content | Hidden signal request creates no item/copy and publishes no coordinated signal |
| Snapshot restore/retry | Refusal stays absent; known clue recall survives |
| Unsuitable/unknown surface | No runtime suitability gate exists; target remains unresolved. A dedicated unsuitable-target mechanism test is deferred with implementation |
| Unauthorized content fidelity | No copied content is created. Fidelity of successful inscription is untested |
| Mutation failure | No inscription mutation reaches application. Existing transaction fault controls rerun; no inscription-specific success-after-failure claim |
| Acquisition / travel / dialogue / T04 | Existing combined selection and twelve-turn replay preserve their present owners/limitations |
| Immutable acceptance | Both T06 traces have hard-valid immutable refusal equal to visible HTTP text |

These are fail-closed and preservation checks. They do not prove that a new prerequisite evaluator distinguishes missing from unknown, validates suitability or can complete an authorized inscription. Required success-oriented tests B/E/F/H/I/J/K/L/R remain dependent on the blocked mutation contract; no synthetic success was fabricated.
''')
failures='\n'.join('- `'+n+'`' for n in r['after']['failed_nodes']) or 'None.'
md('REGRESSION_RESULTS.md',f'''# Regression results

| Selection | Result |
|---|---|
| Historical predecessor reference | 408 passed / 17 failed of 425 |
| Fresh pre-production-edit baseline | {totals(r['baseline'])} |
| Final same 425 selected nodes | {totals(r['after'])} |
| New diagnostic manipulation tests | {totals(r['focused'])} |
| Existing physical/persistence/authority | {totals(r['persistence_controls'])} |

New failure identities: {json.dumps(r['new_failure_identities'])}. Resolved fresh identities: {json.dumps(r['resolved_failure_identities'])}. Collection errors are recorded as errors in the above JUnit; live provider calls 0. No production change exists to credit for differing results. Predecessor fluctuations are not repairs.

Commands (repository root):

```powershell
.venv/Scripts/python.exe artifacts/{ID}/investigate.py entry
.venv/Scripts/python.exe artifacts/{ID}/investigate.py baseline
.venv/Scripts/python.exe artifacts/{ID}/investigate.py before
.venv/Scripts/python.exe artifacts/{ID}/investigate.py persistence_controls
.venv/Scripts/python.exe artifacts/{ID}/investigate.py focused
.venv/Scripts/python.exe artifacts/{ID}/investigate.py final
.venv/Scripts/python.exe artifacts/{ID}/investigate.py after
```

The runner records executable and every exact pytest argument in *_command.json. The module/selected-node arguments come from predecessor main/authority commands plus pre-seal/T05/T04 modules; collection is asserted equal to all 425 predecessor JUnit node identities. Its tests include conversational handoff, inventory/mechanical, travel/transition, pre-seal closed-inspection, T04 and T05 controls. Tests run with fail-closed external-network and protected production-data guards; fixtures can use local provider stubs. Live providers are disabled and client construction is forbidden by existing pytest fixtures. Initial harness attempts hit the evidence-directory write guard before test execution; corrected to this cycle's evidence directory without weakening the guard. Two attempts passing all 425 individual node names stalled during collection and were interrupted without a completed test result; those aborted argument lists are retained in *_aborted_node_command.json. The established module arguments complete collection and verify the exact same node set. These setup/collection attempts are not passing or failing regression results.

Fresh baseline versus predecessor: new identities {json.dumps(r['baseline_vs_predecessor_new'])}; not reproduced {json.dumps(r['baseline_vs_predecessor_not_reproduced'])}. Any differences predate production edits (none were made) and receive no repair credit.

The three recurring greeting/refusal cases are explicitly listed as previously failing (not repaired) in T04 REGRESSION_RESULTS.md. Fresh diagnostics repeat its events-file assertion, AnyIO portal RuntimeError, and missing OPERATIONAL_REFUSAL log entry. These are historical fluctuations relative to 408/17, not new failures caused by T06. Full exact assertions remain in the fresh JUnit.

Final failure identities:

{failures}

Full diagnostics in baseline_junit.xml/after_junit.xml and logs; exact fresh differences in test_results.json. No full-suite, live-model, independent-generalization or gameplay benchmark claim.
''')
md('TWELVE_TURN_COMPARISON.md','# Twelve-turn comparison\n\nUnchanged original requests and provider-free HTTP harness. All twelve published strings and compared kind/reason, scene, inventory, knowledge, mutation and publication-text fields match. Campaign ids, timing and other run-local values are not equality claims.\n\n| Turn | Final published text | Changed |\n|---|---|---|\n'+'\n'.join('| '+x['id']+' | '+x['after'].replace('|','\\|')+' | '+('yes' if x['differences'] else 'no')+' |' for x in rows)+'''\n
T06 remains refused. T04 contact, T05 clue without stock jab, T09 grounded recall and T11 Old Milestone travel remain intact. Hidden-information/NPC controls are in the combined and new diagnostic selections. T01/T07 narration, T02 usefulness, T08 acknowledgment, T10 trade and T12 refusal remain limitations. No next cycle was started.
''')
md('PERFORMANCE.md',f'''# Performance and provider impact

Live provider calls **0**; external network block lists empty in both twelve-turn runs. No production change, prompts, retries, dispatches, planners, reconciliation or new standing state. Production deterministic overhead introduced: **zero**. No token-use increase introduced.

Instrumented local twelve-turn HTTP elapsed: before {before['elapsed_ms']:.3f} ms; final {final['elapsed_ms']:.3f} ms. These include deep-copy trace instrumentation and concurrent regression workloads, unlike the historical uninstrumented 2616.811 ms. They are diagnostic timings, not a benchmark or evidence of production overhead/regression. No broad performance benchmark performed.
''')
md('NEXT_STEP_DECISION.md',f'''# Next-step decision

Acceptance recommendation: **BLOCKED**, with investigation complete. No A/PASS implementation claim; no successful controlled HTTP path or physical-modification persistence evidence.

Exactly one proposed next action: {decision}

Scope: resolve canonical object identity (including equipped object parts), access/suitability/material prerequisites, validated mutation receipt and downstream inspection authority. Reuse character storage and runtime transaction/snapshot infrastructure; prohibit scene-ledger shadow inventory. Decide this contract before authorizing a new implementation cycle. This meets the portfolio architecture-review trigger: missing ownership/unusable contract for a real product requirement.

Deferred: implementation and success-oriented tests, more specific runtime prerequisite refusal, T01/T02/T07/T08/T10/T12 limitations, baseline failures, broader inventory/crafting systems and experimental-owner activation. Do not automatically begin another cycle.
''')
identity=read('entry_identity.json')
md('INTEGRITY.md',f'''# Integrity

Branch `{identity['branch']}`; HEAD `{identity['head']}`. Entry dirty status preserved in entry_git_status.txt. No reset, clean, stash, revert, historical checkout, commit or push. Baseline production/test/data hashes captured before adding tests; before_manifest.json and after_manifest.json retain SHA-256 for every selected source/test/data/static/prompt input.

Existing protected files changed or missing: **0**. Added: only tests/test_pr_play_t06_persistent_manipulation.py within those roots. Production diff empty; frozen fixture/data changes **0**. Exact manifest comparison: source_changes.json. All pre-existing dirty source/tests remain byte-identical. Investigation reports/evidence, six diagnostic tests, handoff configuration and a prepended NEXT_SESSION entry are new cycle work.

Historical NEXT_SESSION bytes are preserved in entry_next_session.md and as the exact suffix of docs/NEXT_SESSION.md. Prior generated review text is preserved in entry_current_review.md; historical review archives are not overwritten. A fresh stable and dated review archive are generated and independently reopened. archive_verification.json verifies milestone identity, T06 before/after, blocked persistence status, regressions, handoff suffix and all packaged canonical hashes. Archive SHA-256 and dated path are in archive_sha256.txt (external to the sealed archive to avoid circular hashing).

The standard generator's direct write to the existing stable ZIP returned OSError 22 (Invalid argument). The same generator was run with --output-dir artifacts/pr_play_t06_persistent_manipulation/review_export --no-history, then its three generated files were installed at the standard stable paths by copying to sibling temporary files and atomic os.replace. This is an export/installation workaround, not a production or handoff-generator change. The dated ZIP is copied from the freshly installed stable ZIP and both are reopened and compared.

No successful persistent manipulation is hidden behind a green test claim. BLOCKED is the accurate outcome. Live provider calls 0.
''')
entry=(OUT/'entry_next_session.md').read_bytes()
intro=f'''# NEXT_SESSION — PR-PLAY T06 Persistent Physical Manipulation (2026-11-09)

**BLOCKED; investigation complete, no production implementation.** Milestone `{ID}`; predecessor `pr_play_t04_local_action`. Branch {identity['branch']}; HEAD {identity['head']}. Dirty source/tests/data preserved. No commits/pushes. Live provider calls **0**.

Original HTTP T06 recovers a physical interaction with verb `try` and an unbound copy clause, then declines as unsupported_physical_manipulation before resolver/prerequisite evaluation. T05 clue is known. No equipped sleeve instance, writable/compatible surface, or accessible usable mud supply is established. Existing character JSON can persist fields but no validated item-modification/inspection owner spans this path. Experimental physical ledger owns scene objects/posture and must not become shadow inventory. No mutation or successful controlled-fixture path was fabricated; original T06 still says “That part is not supported here. It was not carried out.”

Fresh 425 baseline: {totals(r['baseline'])}; final same selection: {totals(r['after'])}. New diagnostics {r['focused']['passed']}/{r['focused']['tests']}; physical/persistence/authority {r['persistence_controls']['passed']}/{r['persistence_controls']['tests']}. New failure identities {len(r['new_failure_identities'])}. No causal repair claims for fluctuations. All twelve published turns unchanged; T04/T05/T09/T11 preserved. Negative snapshot/restore/retry passes; successful inscription persistence/inspection remains unimplemented.

**Exactly one proposed next action:** {decision} Do not begin automatically. Defer implementation, more specific prerequisite responses, T01/T02/T07/T08/T10/T12 and baseline defects.

Reports: development/campaigns/product_realization/{ID}/. Evidence: artifacts/{ID}/. Minimum: SUMMARY, ROOT_CAUSE, MANIPULATION_CONTRACT, IMPLEMENTATION, REGRESSION_RESULTS, NEXT_STEP_DECISION; before_t06.json, final_t06.json, prerequisite_evaluation.json, architecture_evidence.json, test_results.json, source_changes.json. Review: handoff/CURRENT_REVIEW.md. Fresh archive path/SHA-256 and verification: artifacts/{ID}/archive_sha256.txt and archive_verification.json.

---

'''
(ROOT/'docs/NEXT_SESSION.md').write_bytes(intro.encode('utf-8')+entry)
config=read('../pr_play_t04_local_action/review_handoff.json')
config.update(campaign_id=ID,campaign_name='PR-PLAY T06 Persistent Physical Manipulation',
    campaign_date='2026-11-09',purpose='Investigate persistent physical modification through existing authority; stop when existing item ownership and mutation contracts cannot safely carry it.',
    objective_status='BLOCKED',executive_summary=summary.split('\n\n',2)[2],
    changes={'production':['None; conditional implementation stopped on architectural ownership/contract gaps.'],
             'validation':['Six diagnostic provider-free HTTP tests; fresh same-node regression and existing persistence/authority selections.'],
             'tooling':['Cycle-local trace/report runners; no production tools changed.'],
             'documentation':['Twelve reports and a prepended NEXT_SESSION entry, preserving historical suffix.'],
             'generated_artifacts':['Before/final T06 traces, source manifests, twelve-turn comparison, JUnit, prerequisite and architecture evidence.']},
    testing={'focused':totals(r['focused']),'broader':totals(r['after'])+'; physical/persistence/authority '+totals(r['persistence_controls']),
             'full_suite':'Not run','runtime_validation':'Original T06 remains refused. All twelve published turns unchanged. Negative snapshot restore/retry passed; no successful inscription persistence claim.',
             'model_runtime_boundary':'Zero live provider calls. Fail-closed network/provider and production-data guards.',
             'new_regressions':str(r['new_failure_identities']),'pre_existing_failures':'Exact identities and fluctuation notes: REGRESSION_RESULTS.md and test_results.json.'},
    decisions_requiring_human_review=['Item-instance mutation and inspection ownership must be settled before implementation; see NEXT_STEP_DECISION.md.'],
    known_problems={'campaign_specific':['No persistent-modification mechanism implemented. Original T06 still unresolved. Successful controlled HTTP, mutation and inspection verification unavailable.'],
                    'pre_existing':['T01/T02/T07/T08/T10/T12 and baseline failures remain.']},
    missing_concepts=['Equipped item/part binding, positive material/surface prerequisites, validated item-instance mutation and later inspection contract.'],
    does_not_prove=['Successful original or controlled inscription, successful modification persistence/idempotency, playability, full-suite or live-provider acceptance.'],
    recommended_next_step=decision+' Do not begin automatically.',
    self_contained_review_test='Reopen ZIP; verify BLOCKED identity, unchanged original T06, absent mutation, negative persistence result, fresh regressions, source hashes and preserved historical handoff suffix.',
    primary_report=REPORT.relative_to(ROOT).as_posix()+'/SUMMARY.md')
write('files_created.json',{'reports':[p.relative_to(ROOT).as_posix() for p in REPORT.glob('*.md')],
      'evidence':[p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file()],
      'tests':['tests/test_pr_play_t06_persistent_manipulation.py'],
      'updated':['docs/NEXT_SESSION.md','handoff/CURRENT_REVIEW.md','handoff/REVIEW_MANIFEST.json','handoff/CURRENT_REVIEW.zip']})
support=list(REPORT.glob('*.md'))+[ROOT/'docs/NEXT_SESSION.md',ROOT/'tests/test_pr_play_t06_persistent_manipulation.py',
        OUT/'entry_next_session.md',OUT/'entry_current_review.md']
support += [p for p in OUT.iterdir() if p.is_file() and p.suffix in ('.json','.xml','.py','.diff','.txt')
            and not p.name.startswith('review_handoff') and not p.name.startswith('archive_')
            and p.name!='evidence_manifest.json']
support += [ROOT/path for path in architecture]
write('evidence_manifest.json',{'milestone':ID,'entries':[{'path':p.relative_to(ROOT).as_posix(),
    'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in support+[REPORT/'SUMMARY.md']],
    'exclusions':'Temporary runtime storage, caches, previous archives, and final external archive seal are excluded.'})
support += [OUT/'evidence_manifest.json',OUT/'review_handoff.json']
config['supporting_files']=[{'path':p.relative_to(ROOT).as_posix(),'role':'investigation_evidence','canonical':True,
    'why':'Supports the bounded T06 investigation, stop decision, regression or integrity evidence.',
    'behavioral_evidence':p.name.endswith('_t06.json'),'human_review_required':False}
    for p in support if p!=REPORT/'SUMMARY.md']
write('review_handoff.json',config)
print(json.dumps(r,indent=2))
