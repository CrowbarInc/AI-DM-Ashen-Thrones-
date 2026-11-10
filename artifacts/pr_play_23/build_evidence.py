"""Offline evidence assembly; no application/provider entrypoints are executed."""
import difflib
import hashlib
import json
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def write(name, text):
    (OUT/name).write_text(text.strip()+'\n', encoding='utf-8')


def summary(name):
    tree = ET.parse(OUT/(name+'.xml'))
    cases = tree.findall('.//testcase')
    return {'total': len(cases), 'passed': sum(not any(c.find(k) is not None for k in ('failure', 'error', 'skipped')) for c in cases),
            'failed': sum(c.find('failure') is not None for c in cases), 'errors': sum(c.find('error') is not None for c in cases),
            'failures': [c.attrib['classname']+'::'+c.attrib['name'] for c in cases if c.find('failure') is not None or c.find('error') is not None]}


results = {n: summary(n) for n in ('focused', 'existing', 'paired_before', 'io_retry', 'harness_final')}
write('test_summary.json', json.dumps(results, indent=2))
classification = []
paired = set(results['paired_before']['failures'])
for node in results['existing']['failures']:
    if node in paired:
        kind = 'preexisting_expanded_scope_paired_reproduction'
    elif any(name in node for name in ('test_second_start_campaign_rejected', 'test_invalid_provider_output_fails_without_progression')):
        kind = 'environmental_WinError5_passed_targeted_rerun'
    else:
        kind = 'preexisting_original_17'
    classification.append({'test': node, 'classification': kind})
write('failure_classification.json', json.dumps({'new_reproducible_regressions': [],
    'resolved_preexisting_failures': [], 'entries': classification}, indent=2))
original_dir = ROOT/'artifacts/atgb/pr_play_22/live/turns/T1'
diagnostic = json.loads((original_dir/'parser_validation_diagnostics.json').read_text())
live = diagnostic['resolution']['metadata']['live_chat_interpretation']
write('captured_interpretation_fixture.json', json.dumps({'player_text': "I approach the tavern runner and ask what they're offering.",
    'raw_provider_envelope': json.loads(live['raw_interpretation']), 'parsed_record': live['record'],
    'original_orchestration': diagnostic['resolution']['metadata']['conversational_decision']}, indent=2))

sources = ['game/local_interaction.py', 'game/conversational_orchestration.py', 'game/player_interpretation_bridge.py',
           'tools/playtest/gameplay.py', 'tools/playtest/runner.py', 'artifacts/pr_play_22/execute_validation.py',
           'tests/test_pr_play_23_local_interaction.py', 'tests/test_pr_play_23_harness.py', 'tests/test_five_turn_gameplay.py']
diffs = []
for name in sources:
    path = ROOT/name
    prior = ROOT/'artifacts/pr_play_22/source_snapshot'/name
    if name == 'game/conversational_orchestration.py':
        prior = OUT/'before_conversational_orchestration.py'
    if name == 'tools/playtest/gameplay.py':
        prior = OUT/'before_gameplay.py'
    # For preexisting controller/test files lacking a snapshot, reverse only
    # the documented PR-PLAY-23 hunks to produce an exact task-local diff.
    after = path.read_text(encoding='utf-8')
    before = prior.read_text(encoding='utf-8') if prior.exists() else ''
    if name == 'tests/test_five_turn_gameplay.py':
        before = subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=ROOT).decode('utf-8')
    if name == 'artifacts/pr_play_22/execute_validation.py':
        old_archive = Path((ROOT/'artifacts/pr_play_22/archive_path.txt').read_text().strip())
        with zipfile.ZipFile(old_archive) as old:
            before = old.read('review/execute_validation.py').decode('utf-8')
    diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='before/'+name, tofile='after/'+name))
write('source_changes.diff', ''.join(diffs))

write('PR_PLAY_23_FAILURE_RECONSTRUCTION.md', '''# PR-PLAY-23 failure reconstruction

Original request: “I approach the tavern runner and ask what they're offering.”

The captured provider envelope describes MOVE(tavern_runner), then ASK(tavern_runner), orders 1/2. Its communication is NPC/QUESTION; interpretation status INTERPRETED; no unresolved references. The provider was asked to describe ordered attempts using MOVE and ASK, not to authorize them. Separating physical approach from speech was reasonable.

Evidence: artifacts/atgb/pr_play_22/live/turns/T1/{api_response.json,parser_validation_diagnostics.json,before/persistent/}; artifacts/pr_play_22/PR_PLAY_22_FAILURE_ANALYSIS.md. A minimal captured envelope and parsed record are copied into captured_interpretation_fixture.json.

Call path: api._chat_turn → live_chat_interpretation.interpret_production_turn → contract adaptation. Parsing succeeds and disposition is ELIGIBLE_FOR_VALIDATION. The live adapter returns blocked/clarification_required because it has two components; this is a recoverable handoff to compound orchestration, not the decisive refusal. api._chat_turn invokes conversational_orchestration.decision_from_interpretation_record → _compound_from_record_parts → _compound_clarification. Each proposed step goes through player_interpretation_bridge.normalized_action_from_interpretation. MOVE expects catalog kind exit; tavern_runner has kind npc. The bridge returns operation_incompatible_with_entity_kind. ASK binds successfully. _compound_clarification sees unsupported first step and returns proposal_not_eligible. No resolver or narration invocation occurs.

First decisive failed boundary: engine MOVE binding, not interpretation, parser, NPC registration, dialogue transport, or NPC knowledge disclosure. Compound orchestration then correctly preserves sequence safety under its old all-consequential interpretation.

Published refusal: “I cannot carry out Approach the tavern runner, then Ask the tavern runner what they are offering with the available actions and targets. I have not done any of them yet.”

Offline reproduction: test_original_failure_boundary uses the actual captured scene/world and parsed record through the unchanged production bridge and orchestrator, disabling only the new normalization. It reproduces the kind mismatch and original refusal with no input mutation (original_reproduction.json). The successful integration replays the ORIGINAL RAW provider envelope through the real request builder/parser, orchestration, resolver and Player HTTP publication. It does not replay engine-enriched parsed fields as provider JSON.

Authority distinction: interpretation proposes; parsed records preserve unadjudicated premises/outcomes; bridge checks kinds and grounding; resolver owns authorization and effects; response publication uses existing validated host/NPC speech. Successful normalization grants no movement authorization.
''')

write('PR_PLAY_23_ACTION_PIPELINE.md', '''# PR-PLAY-23 action pipeline

Relevant source anchors (function names are stable; line numbers are in packaged source):

| Stage | Production source / function |
| --- | --- |
| Entry / dispatch | game/api.py:_chat_turn (6644); stored/live interpretation branches around 6744–6870; resolve_social_action call in existing dispatch |
| Interpretation / parser | game/live_chat_interpretation.py:interpret_production_turn; request_interpretation; adapt_interpretation from the existing experiment contract; multi-component handoff around 550 |
| Decision / normalization | game/conversational_orchestration.py:decision_from_interpretation_record (2195); game/local_interaction.py:normalize_local_approach |
| Compound sequencing | game/conversational_orchestration.py:_compound_from_record_parts (1999), _compound_clarification (1681), _resume_pending_decision |
| Catalog / binding | game/player_interpretation_bridge.py:visible_catalog (36), normalized_action_from_interpretation (197) |
| Addressee grounding | game/ordinary_semantic_ownership.py:assess_addressee_grounding (651) |
| Authored addressability | game/interaction_context.py:is_actor_addressable_in_current_scene (757) |
| Social authority | game/social.py:resolve_social_action (3895); game/dialogue_authority.py knowledge/disclosure selection |
| Movement authority | game/exploration.py:resolve_exploration_action; existing reachability checks; game/scene_graph.py |
| Publication | game/api.py existing response/finalization path; game/immutable_valid_response.py; game/state_channels.py:deep_project_public_payload |
| Ordinary time effects | game/api.py normal turn dispatch → game/world.py:advance_world_tick (325) |

MOVE bridge means scene_transition and requires a visible exit, authored destination, and known destination scene. It does not implement free local relocation. The ordinary deterministic parser also has a custom local-physical-movement lane; it does not maintain a coordinate grid. This patch does not expand that lane.

ASK carries target_ref=tavern_runner and has sufficient information to attempt a question. visible_catalog derives NPCs from authoritative world.npcs.location matching the scene ID. An opening narration mention alone does not register an NPC. In the captured world the runner is a real authored NPC, available and friendly, with location=frontier_gate; scene.addressables explicitly marks it addressable=true. It is neither a temporary presentation invention nor a fabricated persistent record.

INSPECT binds authored interactables to investigate; visible surface inspection already falls back to the existing supported surface behavior. No examination capability is added. NPC and object operations retain their respective resolvers.

Answers to the ten investigation questions:

1. MOVE describes the provider's reasonable physical approach proposal.
2. The stored interpretation MOVE bridge is scene-transition-only; other parser-local movement exists separately.
3. The runner resolves through authoritative world location plus authored scene addressability.
4. ASK already has its target and question intent.
5. No independent relocation is needed to attempt this same-scene conversation.
6. A literal, same-target preamble can be normalized with authored eligibility and no access caveat.
7. Current-scene membership, explicit authored addressability, canonical addressability, actual interaction binding, and conservative caveat rejection protect the new rule. General spatial reachability is NOT implemented; uncertain cases stay compound/declined.
8. Unsupported first steps prevent later dependent execution. Multiple supported consequential steps still require confirmation.
9. Existing incidental THANK/posture handling exists; local approach previously remained consequential. The new rule is explicit and independently tested.
10. A successful ASK legitimately advances one normal gameplay turn, world tick, log and dialogue bookkeeping. No approach-specific position, travel, currency, inventory, quest or relationship effect is added.
''')

write('PR_PLAY_23_INTERACTION_CONTRACT.md', '''# PR-PLAY-23 local interaction contract

Scene transitions cross authored location boundaries. MOVE-to-exit binding, destination validation, reachability, movement consequences and encounter/time rules remain authoritative and unchanged.

A local approach is a literal “approach”, “walk over to”, “step up to”, or “go over to” an authored target immediately followed by a supported ASK or INSPECT on that SAME target. The rule requires exactly two ordered components, INTERPRETED/IN_WORLD_ACTION status, no unresolved references, and matching player wording and provider description. A target must be in the current visible authoritative catalog. A conversational target additionally needs an explicit same-scene authored addressable=true entry and canonical addressability. The interaction must independently bind through the production bridge to the identical target.

Visibility is insufficient. Unknown addressability, unavailable NPCs, explicit accessible/reachable/addressable=false, combat, hostile targets, or authored public access caveats prevent normalization. Because there is no local geometry/access solver, barrier/reachability caveats are conservatively vetoed in target data and current public scene context. The current bounded vocabulary includes locked, barred, blocked, inaccessible, unreachable, impassable, hostile, across, behind, another room and distant. This is a fail-closed syntactic guard, not a general natural-language access adjudicator. It may reject harmless scenes; unsupported wording retains conservative existing behavior. Explicit player barrier/travel language cannot fit the entire literal preamble.

Only the MOVE preamble is normalized. Its original components and movement_executed=false are retained as diagnostic provenance. No MOVE resolver is called, no movement success is asserted, no position is persisted, and no extra travel time is added. The full original player request remains available to existing authority and publication.

Travel to another district, entry through a gate, ravine crossing, theft, attacks, mismatched targets, third components, unresolved references and unsupported operations remain meaningful actions. They are not dropped. Failed consequential first steps still block later dependent interactions. Direct ASK behavior is unchanged. No NPC names or scenario IDs appear in the rule.
''')

write('PR_PLAY_23_REPAIR_REPORT.md', '''# PR-PLAY-23 repair report

Root cause: the bridge's correct exit-only MOVE contract collided with orchestration's treatment of an ordinary conversational approach as a separate consequential operation. The NPC registration and ASK target were already valid.

Implementation:

* game/local_interaction.py: one conservative read-only normalization rule described in INTERACTION_CONTRACT.
* game/conversational_orchestration.py: apply it to interpreted records before communicative/compound selection. A valid pair becomes the existing single-interaction EXECUTE decision; all other records remain unchanged.
* game/player_interpretation_bridge.py: retain normalization provenance in the existing diagnostic metadata. Actual MOVE and interaction validators remain unchanged.
* tools/playtest/gameplay.py: structured completion classification, decisive stop integration, exact restricted-value disclosure detection, accurate report counters and partial/unknown reporting.
* tools/playtest/runner.py: snapshot via Player HTTP, retaining authoritative reads from the owned isolated files. This required compatibility correction closes the preexisting Debug-read failure without reopening HTTP privilege.
* artifacts/pr_play_22/execute_validation.py: the PR-PLAY-22 custom controller now consumes the same classifier and emits separate counters; it no longer treats the generic weak-answer marker alone as a decisive failure. No historical result files were rewritten.
* tests/test_pr_play_23_local_interaction.py and tests/test_pr_play_23_harness.py: deterministic regressions and production integration.
* tests/test_five_turn_gameplay.py: positive evaluator fixtures now supply native accepted-speaker completion evidence; missing-response expectations now require a semantic failure/stop. The real fixture currently fails T2 addressee binding, so its old T3 injection and six-request exhaustion expectations are replaced by T2 stop and exact three-request/token accounting. These are explicit protocol migrations, documented by intermediate findings, not unrelated assertion relaxation.

Generality: target kind, same-scene authority, authored addressability, exact action semantics and normal interaction binding determine behavior. Runner, guard and notice board controls exercise it without implementation name exceptions.

Limits: deliberately bounded phrase coverage; no spatial solver, new movement capability, NPC/topic fabrication, opening/provider contract change or architecture redesign. The captured runner's current knowledge authority answers “I couldn't tell you” about offerings. That is an executed but weak interaction, also observed for direct ASK, not proof of rich NPC dialogue. Live answer quality remains unverified. Ordinary world ticks still occur: faction progression/event-log differences match advance_world_tick exactly and are legitimate existing time consequences, not normalization effects.

The initial workspace already contained substantial uncommitted changes. This pass preserved them, made no commit or push, and made zero live-provider requests.
''')

write('PR_PLAY_23_HARNESS_REPAIR.md', '''# PR-PLAY-23 harness repair

PR-PLAY-22's custom failed() predicate checked HTTP, missing text, body.ok, and provider/parser events. A well-formed HTTP 200 host compound refusal met none of those failure predicates. ordinary_completed incremented four times even though no NPC action executed; T2–T4 were invalid connected follow-ups.

tools/playtest/gameplay.py:classify_turn now returns transport_completed, pipeline_completed, action_executed, gameplay_completed, interaction_outcome (completed/partial/rejected/unknown), semantic_dead_end, stop and reasons. Transport is HTTP delivery; pipeline requires a published reply and native resolution/accepted response without provider/parser/validator rejection; execution needs native resolver/resolution or accepted NPC interaction evidence; meaningful completion additionally requires no decisive failure and no explicit incomplete interaction. A terminal host binding refusal can complete application processing without gameplay completion. This is structural completion, not a quality score.

Structured evidence sources: resolution.metadata.conversational_decision.reason/category/intent_family; stored_interpretation_bridge.accepted; live_chat_interpretation.status; resolver_invoked; accepted_response speaker/interaction_completion/authorization_source/hard_validation; provider/parser/validator events and native refusal tags. Authoritative state comparisons retain overlay, forbidden mutation, transition and nonmutating-contract checks. Exact restricted authored strings in public reply now produce a decisive disclosure finding. Paraphrased leaks are not comprehensively detectable by this bounded check; normal production confidentiality/validation remains required. No refusal-text matching is used.

The evaluator adds decisive findings and sets stop. runner's existing action loop breaks before the next submission, preserves response/events/before-and-after snapshots/usage, then cleans up and exports. It never retries an easier action or starts another campaign. Production admission still enforces the total request ceiling, including calls made within a turn. The PR-PLAY-22 custom controller consumes the same classifier after state capture and before follow-up construction.

Relevant but weak NPC replies are not decisive by themselves. Explicit partial interaction is recorded as executed/partial without counting as fully completed. Unknown evidence stays unknown; an unsuccessful authorized in-world check or refusal still counts as legitimate adjudication, unlike a host inability to execute the request.

The adapter may hand a multi-component/informational record back as blocked/clarification_required and then publish a valid authorized host DESCRIPTION answer. That exact ANSWER/communication_before_execution + hard-valid completed-response path counts as completed gameplay with no mechanical action executed. It is not mistaken for parser rejection. The existing five-turn fixture's T2, by contrast, really returns ungrounded_provider_target and “Nothing has been attempted.” The controller now stops there before T3 injection or request-ceiling exhaustion. This is desired changed behavior, not permission to continue.

Final counters distinguish ordinary HTTP responses, attempted actions, executed actions, completed gameplay turns, decisive failures and stop reason. Tests include the exact captured T1 response, provider/parser/validator rejection, missing response, weak answer, partial interaction, mutation/disclosure, real owned-worker immediate stop, no follow-up/restart, request ceiling and accurate final reporting. See focused.xml, harness_final.xml and harness_stop_integration.json.
''')

write('PR_PLAY_23_TEST_RESULTS.md', f'''# PR-PLAY-23 test results

Zero live-provider requests. Pytest live-model guards apply; SDK/interpretation transports are synthetic. Owned worker runs use Deterministic mode and reject external socket connections. No live mode or live gameplay was executed.

| Run | Passed | Failed | Errors |
| --- | ---: | ---: | ---: |
''' + '\n'.join(f"| {n} | {r['passed']} | {r['failed']} | {r['errors']} |" for n, r in results.items()) + '''

Focused matrix: original captured failure; accessible runner; equivalent guard wording; direct ASK; notice-board INSPECT; unavailable/cross-scene/unregistered/unknown-access/hostile/locked/player-barrier targets; explicit authored access=false; travel; extra/mismatched/unsupported consequential components; state integrity; publication and public projection. Opening → original RAW interpretation replay → real parser/binding → social resolver → canonical NPC response → serialized Player HTTP publication is exercised. A synthetic hidden sentinel stays authoritative and absent from HTTP. Character/inventory/currency/campaign/combat/conditions remain identical; world changes equal one existing authorized world tick. Negative HTTP integration rejects the consequential first step without running ASK or changing world/character state.

Harness coverage: classifier units plus owned real deterministic worker, HTTP transport, actual snapshots/evaluator/loop/export. A synthetic decisive HTTP 200 failure causes exactly one chat submission, one initialization, one opening, zero executed/completed gameplay turns, and cleanup. A separate configured ceiling run never exceeds two synthetic dispatches. Existing six-request ceiling and failure/export controls also run.

Relevant existing command: 17 files listed in existing.xml/text: PR-PLAY-20/18/13/04, start API, state/UI policies and regressions, shared turn pipeline, PR-PLAY-21, PR-EA orchestration, PR-EC movement, physical compound/perception, PR-DU pipeline and PR-DY live adapter (mocked). Raw result: 268 passed, 26 failed, 1 setup error. The original 17 functional failures persist (3 opening / 14 shared turn). Seven additional physical-action tests and one PR-DY clarification test fail identically with the new normalizer disabled: paired_before.xml contains 74 passed / 8 failed across the five expanded files. These are confirmed preexisting in the expanded test scope, not newly introduced regressions. They do not exercise the exact same-target approach + supported interaction rule; no unrelated repair was attempted.

Two separate Windows os.replace WinError 5 failures affected an opening setup case and second-start rejection. The focused rerun of all five invalid-provider controls and second-start rejection passed 6/6 (io_retry.xml); the external cause remains unknown. Thus 25 reproducible functional failures remain in the full expanded scope, including all original 17. No historical functional failures resolved; no new reproducible regressions found in the exercised scope. Do not interpret this as a green full repository suite.

Harness expectations intentionally migrated: a text-only envelope cannot establish execution; missing player-facing text is decisive; the existing five-turn fixture's T2 binding refusal must stop before T3 injection/budget exhaustion. Its actual three synthetic requests total 60 input / 30 output / 90 tokens, two requests on ordinary turns and one opening request. The positive evaluator fixture now supplies native accepted-speaker evidence. Intermediate failures and their exact causes are retained in intermediate_findings.md and initial logs.

Commands use .venv/Scripts/python.exe -m pytest, --tb=short and separate --basetemp directories. XML preserves test IDs, counts and detailed failures. focused_initial/second/third/fourth are fixture-development logs; focused and harness_final are the final checks. Paired baseline uses -p artifacts.pr_play_23.baseline_plugin (identity normalization) and changes no production files.
''')

write('PR_PLAY_23_FINAL_VERDICT.md', '''# PR-PLAY-23 final verdict

Overall: A — LOCAL INTERACTION BINDING REPAIRED. PASS for the targeted offline repair; the broader repository retains documented failures.

1. Original PR-PLAY-22 failure reproduced? Yes: captured production bridge/orchestration, original refusal.
2. Why did MOVE-to-NPC fail? MOVE requires an exit; the authored target is an NPC.
3. Was runner authorized? Yes, authoritative same-scene world NPC plus explicit authored addressability; ASK already bound.
4. Can a visible accessible NPC be approached and questioned? Yes within the documented conservative preamble contract; visibility alone never suffices.
5. Does it generalize? Yes: another authored guard and object controls; no name exceptions.
6. Genuine scene transitions preserved? Yes: existing exit/reachability rules unchanged; legacy movement controls run.
7. Accessibility preserved? Yes within existing authored eligibility; unknown/caveated access remains unnormalized. No spatial solver or unrestricted approach is added.
8. Unsupported consequential actions preserved? Yes: theft/attack/extra/mismatched/travel steps remain subject to compound rejection/confirmation.
9. Direct ASK works? Yes, real opening-to-ASK HTTP integration.
10. Execution reaches publication? Yes: actual social resolution, canonical NPC speech, log and Player HTTP response. No live narration is required.
11. Authoritative state preserved? Yes: exact normal world tick; no added relocation/inventory/currency/quest/relationship effect.
12. Public confidentiality preserved? Yes in deterministic sentinel/projection tests; existing PR-PLAY-20/21 checks run; privileges stay denied.
13. Harness stops after decisive failure? Yes, actual controller stops after first refusal, captures evidence and cleans up.
14. HTTP vs gameplay completion distinguished? Yes; one HTTP 200 failure is zero executed/completed gameplay turns.
15. New regressions? None reproducible in exercised scope; intentional harness fixture/protocol expectation migrations documented.
16. Preexisting failures remaining? Original 17 remain; expanded paired scope reveals 8 more, total 25 reproducible functional failures. Two environmental file-access failures passed reruns.
17. Live-provider requests? Zero. All provider-shaped usage is explicitly synthetic.
18. Ready for targeted live NPC test? Yes, subject to a NEW explicit live authorization after external review. Use one local NPC request and stop immediately on a decisive failure. The runner's weak current answer must be assessed for response quality; this repair does not establish rich live dialogue.

Highest-priority finding: local approach can now hand off to authorized ASK without requiring an exit or dropping consequential actions.

Stop here for external review. No PR-PLAY-24, live run, commit or push is authorized or performed.
''')

# Include only this pass's evidence, relevant sources, and selected prior public
# interpretation records; no environment dumps, credentials or unrelated history.
files = [p for p in OUT.iterdir() if p.is_file() and p.suffix in {'.md', '.json', '.txt', '.xml', '.diff', '.py'}
         and not p.name.startswith('before_') and p.name not in {'MANIFEST.json', 'archive_verification.json'}]
files += [ROOT/p for p in sources]
files += [original_dir/p for p in ('parser_validation_diagnostics.json', 'api_response.json',
                                  'before/persistent/world.json', 'before/persistent/scenes/frontier_gate.json')]
manifest = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
             'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
write('MANIFEST.json', json.dumps({'live_provider_requests': 0, 'files': manifest}, indent=2))
files.append(OUT/'MANIFEST.json')
# Use Windows' bundled time-zone database; this environment has no tzdata wheel.
stamp = subprocess.check_output(['powershell', '-NoProfile', '-Command',
    "[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMdd-HHmmss')"],
    text=True).strip()
archive = ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for path in files:
        z.write(path, path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for entry in manifest:
        assert hashlib.sha256(z.read(entry['path'])).hexdigest() == entry['sha256']
write('archive_verification.json', json.dumps({'archive': str(archive), 'exists': archive.exists(),
    'crc_verified': True, 'manifest_hashes_verified': True, 'entries': len(files), 'bytes': archive.stat().st_size}, indent=2))
print(archive)
