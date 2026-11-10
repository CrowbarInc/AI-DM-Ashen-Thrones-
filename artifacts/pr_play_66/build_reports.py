"""Build canonical campaign reports from recorded executions, no rerun."""
import sys,json,hashlib,subprocess,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/campaigns/product_realization/pr_play_66'
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def save(name,v):(OUT/name).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def report(name,text):(REPORT/name).write_text(text.strip()+'\n',encoding='utf-8')
if __name__=='__main__':
    REPORT.mkdir(parents=True,exist_ok=True)
    baseline=read('baseline.json');holdout=read('holdout_results.json');audit=read('holdout_evaluation_audit.json');matrix=read('publication_matrix.json');reg=read('regression_summary_final.json');live=read('http_gameplay.json');usage=read('provider_usage.json');latency=read('latency.json');state=read('state_integrity.json');replay=read('historical_after.json')['result'];before=read('baseline_reproduction.json');freeze=read('implementation_freeze.json')
    changed=[n for n,v in baseline['protected_hashes'].items() if not (ROOT/n).exists() or hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=v]
    frozen=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in freeze['sources'].items())
    save('protected_integrity.json',dict(checked=len(baseline['protected_hashes']),changed=changed,passed=not changed,source_freeze_preserved=frozen))
    assert not changed and frozen
    new=reg['focused']['new_failures'];safe=not new and state['passed'] and audit['passed'] and not holdout['mandatory_omissions'] and not holdout['unsafe_publications']
    verdict='C — FAIL / CRITICAL DEFECT'
    next_step='Repair hidden-information leakage in the final gameplay HTTP payload projection before resuming experimental publication.'
    summary=f'''# EXECUTIVE SUMMARY

**{verdict}.** CRITICAL STOP: final serialized HTTP bodies expose hidden canaries under session.gm_notes, world.gm_only and scene discoverable_clues/gm_notes/private_notes. This exists in entry-source replay and flag-disabled controls as well as the repaired experiment. 41 matrix responses and all five TCP gameplay responses expose hidden payload data. Experimental execution stopped; the second regression run was interrupted. Diagnose offline only; flags remain default off. No post-holdout implementation tuning or broader projection repair. See critical_incident.json.

The exact historical action reproduces the PR65 defect through the real HTTP route before repair, then publishes its mandatory footprint discovery after repair. Root cause: exact-string provider-placeholder matching gave other legacy refusals precedence over a valid deterministic fallback. This is an implementation defect in final response selection, not a discovery-state or semantic-validator defect.

45 publisher-inclusive development cases pass their stated text/selection assertions; they did not check the entire body for hidden values. Full-body inspection subsequently FAILS. Five consecutive supported gameplay actions complete over actual localhost TCP, including the authored frontier_gate → old_milestone exit, the milestone discovery, and two follow-ups. All five authoritative results match disabled controls. One synthetic validated presentation is published; three trusted fallbacks; movement uses the ordinary deterministic response. Zero live-provider requests/tokens. No browser or human quality/official ATGB claim.

Frozen developer-authored holdout executed once: **40/40 correct publication decisions, zero mandatory omissions, zero unsafe AI publications, zero false rejections; raw aggregate 38/40**. Two raw state comparisons used different authoritative operations (injected empty resolver vs normal resolver). Original results/evaluator remain unchanged. Unsafe-publication counts here evaluate optional AI/final narration selection, not all other JSON fields; subsequent full-body inspection finds a separate critical hidden leak. A separate matched-operation audit confirms equal authority and no experimental publication for the missing outcome. This is an evaluation defect and an explicit holdout limitation, not two silently erased failures or independent blind validation.

Completed initial focused regression: {reg['focused']['passed']} passed, {reg['focused']['failed']} failed, {len(new)} additional failures (obsolete static assertion and unclassified transient malformed-output HTTP 500). Static correction/targeted diagnostic: 20 pass. Final aggregate rerun interrupted on the critical payload leak; no completed clean rerun claimed. Broader: {reg['broader_hard_validation']['passed']} passed / {reg['broader_hard_validation']['failed']} known failures. Protected {len(baseline['protected_hashes'])} files and frozen implementation hashes unchanged. Experimental flags remain default off/session-bound; no commit/push.

Final milestone HTTP text:

> {replay['facing']}

Exactly one primary next step: **{next_step}**. Do not start presentation/naturalness work until full-body hidden-information publication is safe.
'''
    report('01_EXECUTIVE_SUMMARY.md',summary)
    report('02_BASELINE_AND_SCOPE.md',f'''# BASELINE AND SCOPE
Commit: `{baseline['commit']}`. Entry worktree extensively dirty; exact status and {len(baseline['protected_hashes'])} protected content hashes in baseline.json. Incremental implementation.diff compares against entry copies, not HEAD. Relevant preexisting source and prior reviews are preserved. No canonical data or protected baseline edits; no commit/push.

Production changes: game/api.py and game/quarantined_investigation_narration.py. New regression: tests/test_pr_play_66_publication.py. Updated historical static boundary assertion: tests/test_pr_play_49_anchored_narration.py; forbidden imports/effect protections retained. Tooling/evidence: artifacts/pr_play_66; 18 reports here; docs/NEXT_SESSION.md prepended orientation; generated review exports under handoff. No validator, claim extraction, gameplay mechanism, provider configuration, or persistent campaign model change.

Read Development Constitution, NEXT_SESSION, state-authority model, validation-evidence/review-handoff standards, Product Realization bootstrap, PR65 reports 01/05/07/12/18/19 and incident/source/tests. The user's PR66 request explicitly supersedes prior session recommendations not to start PR66; it does not authorize commit/push. Known baseline: 848 focused passing/3 failures and 9 broader failures.
''')
    report('03_PR_PLAY_65_CRITICAL_REPRODUCTION.md',f'''# EXACT CRITICAL REPRODUCTION
The original final action, full hook input/candidate/validation, initial session/character and post-action authority are preserved in historical_fixture.json. Copied PR65 disposable data/scenes and restored the captured pre-action session/character; original fixture files were not rewritten. harness.py shows configuration. Provider-free replay uses the exact saved PR65 candidate, not a new provider execution.

Player action: `{before['request']['json']['text']}`. Baseline final HTTP {before['status_code']}: `{before['facing']}`. The hook fallback contains the exact mandatory discovery; final HTTP omits it. Independent reproduction therefore matches the original incident. baseline_reproduction.json contains actual serialized body, hook, outcome and before/after state. Permanent historical HTTP regression is test_publication_http[historical].
''')
    chain='''POST /api/chat?ui_mode=player → api_chat → chat → _run_resolved_turn_pipeline → _resolve_engine_noncombat_seam → game.noncombat_resolution / game.exploration (authority mutation) → _build_gpt_narration_from_authoritative_state (ordinary provider/validation/refusal choices) → _observe_quarantined_investigation_narration → quarantine.build_hook_input → integrated.run_integrated_hook → outcome_contract → trusted_disclosure → optional generator → compose_authoritative / validate_integrated → quarantine evidence and request-local binding → _complete_opening_turn_persistence_like_chat (normal state/clue/clock persistence and ordinary text finalization) → _build_turn_response_payload → prepare_authoritative_publication → _publish_experimental_integrated_narration → verify_authoritative_publication → final-text equality assertions / append_log → _project_player_runtime_response → state_channels.deep_project_public_payload → FastAPI JSON serialization → HTTP body.'''
    save('publication_call_chain.json',dict(chain=chain,selection_owners=['game/api.py::_publish_experimental_integrated_narration','game/quarantined_investigation_narration.py::prepare_authoritative_publication','game/quarantined_investigation_narration.py::verify_authoritative_publication']))
    report('04_PUBLICATION_CALL_CHAIN.md',f'''# PUBLICATION CALL CHAIN
{chain}

Ordinary narration and late finalization can replace text with provider placeholders, validation refusals or fallback before the experimental publisher. The integrated hook independently selects composed validated text or deterministic fallback. Previously, the publisher copied accepted AI text but copied rejected-candidate fallback only for one exact placeholder, including a second per-target string gate. HTTP aliases can differ, so every final GM target now receives the same chosen response. Final verification detects drops/no-op/helper exception and restores trusted fallback once. Equality assertions retain canonical/payload/log consistency. Public projection filters keys only, preserves scalar text; serialization is a separate transport boundary. A serialization exception returns failure, not an invented successful response. The final HTTP evidence, not hook markers, decides success.
''')
    report('05_ROOT_CAUSE.md','''# ROOT CAUSE
Primary class: implementation. Demonstrated causes A/B/C: exact-string placeholder matching, legacy rejection precedence, incorrect response selection. Earliest incorrect decision: api._publish_experimental_integrated_narration refuses a valid stored deterministic fallback whenever no target equals the provider-disabled stub. It repeats the stub requirement per target. The milestone's generic validation refusal thus wins after the hook correctly renders disclosure.

Scope established: multiple legacy response/fallback inputs, successful eligible integrated investigations under all existing opt-in gates. It is not milestone-specific and not an HTTP serializer/schema defect. Repair is restricted to the authoritative-disclosure flag; ordinary gameplay and prior flag-disabled publisher behavior remain unchanged. No broader semantic-validator diagnosis was required.
''')
    report('06_PUBLICATION_REPAIR.md','''# PUBLICATION REPAIR
Reuse the existing quarantine/hook, outcome projection, trusted renderer, action fallback, validator result and API publication seam. A ContextVar binds the current hook evidence to the actual resolution object and campaign/session id within this request execution context. The publisher consumes that binding once and reprojects actual resolver fields to reject authority drift. It never selects a shared global evidence tail for the repaired path.

Accepted optional text requires PASS, used_fallback=False, matching engine request/disclosure, the exact validated composition and existing engine-plus-validated-AI provenance. Otherwise build the trusted deterministic response directly from the existing action contract, independently of rejected or absent prose. No arbitrary legacy string participates in this selection.

Final verification compares every server GM target with the selected response and every mandatory fact with its trusted literal rendering. On helper exception or invariant violation, replace all targets with the precomputed deterministic response once, record recovery_reason, verify again, and raise if a valid body cannot be constructed. No provider call, second action resolution, recursion, semantic weakening or state write. Original candidate and validation evidence remain intact. Publication means server construction, never delivery ACK. Serialization/application/initialization errors retain error behavior. A missing current authoritative investigation cannot borrow stale fallback.

Justification: existing publication owner can carry the repair; no new framework or state owner. Request-local provenance prevents cross-action/session reuse, replacing reliance on shared evidence for this repaired selection only.
''')
    report('07_MANDATORY_DISCLOSURE_INVARIANT.md','''# MANDATORY DISCLOSURE INVARIANT
For an eligible completed current action with all quarantine/integrated/authoritative flags and the bound session, final GM text must equal the selected trusted/validated composition and include each current must_communicate text. Projection is recomputed from the actual current resolution and compared to the hook's detached authority. Previously-known player_knowledge/public_observation anchors remain optional context. Hidden state is never fed to the renderer. Deterministic uncertain facts are copied exactly, not expanded by AI inference.

verify_authoritative_publication records current facts, trusted text, final text, decision, invariant and recovery reason in the original quarantine evidence. A failed selection cannot publish arbitrary AI or an incoming legacy refusal. One precomputed fallback recovery is allowed; a remaining invariant failure raises. The boundary cannot guarantee receipt over an interrupted connection or successful serialization during a serializer fault. These are explicitly classified failures, not successful delivery.
''')
    matrix_lines=['| Case | HTTP | Decision / expected behavior | State |','|---|---:|---|---|']
    for r in matrix:matrix_lines.append(f"| {r['name']} | {r['status']} | {(r.get('trace') or {}).get('publication',{}).get('decision','ordinary/error')} | {'unchanged by narration' if r.get('narration_state_unchanged') else 'error/isolated control'} |")
    report('08_PUBLICATION_TEST_MATRIX.md','''# PUBLICATION TEST MATRIX
45 parameterized tests exercise the actual FastAPI HTTP endpoint and inspect the serialized response body. They cover all requested 40 cases plus helper exception, serialization exception, interrupted-request construction control, final invariant recovery and stale evidence. Isolated projection/multiple-fact controls are injected into an HTTP execution, not counted as native multi-discovery mechanics. Validation-status injections at the hook output exercise publisher decisions; PR65 validator-level injections remain in regression. Unsupported actions retain existing grammar behavior, not a new unsupported-action protocol.

publication_matrix.json contains requests, resolver outcomes in bodies, mandatory projections, exact candidate and original validation in hook trace, final publication decisions/bodies, before/after session and narration state guards; error cases record 500 without publication success. Initial development assertions incorrectly demanded fallback even when valid optional text was accepted. Test expectations/setup were corrected, production source unchanged; initial logs/XML are preserved. Final development.xml: 45/45.

'''+ '\n'.join(matrix_lines))
    report('09_FROZEN_HOLDOUT.md',f'''# FROZEN PUBLICATION HOLDOUT
40 developer-authored cases frozen before implementation: 10 mandatory fallbacks, 10 legacy inputs, 5 accepted presentations, 5 unauthorized consequences, 5 no-new-information outcomes, 5 authoritative-failure inputs. Manifest hash: `{read('frozen_holdout_manifest.json')['sha256']}`. Each runs the HTTP route, with ordinary legacy inputs injected at the final publication seam; deterministic disabled controls compare state. One evaluation only; source hash freeze preserved, no post-holdout source tuning.

Correct publication decisions {holdout['correct_decisions']}/40; mandatory omissions {holdout['mandatory_omissions']}; unsafe publications {holdout['unsafe_publications']}; false rejections {holdout['false_rejections']}. CRITICAL LIMIT: the holdout safety checks did not inspect hidden values outside player_facing_text; later offline full-body inspection found the payload leak. Raw aggregate {holdout['passed']}/40; raw state comparisons flagged {holdout['state_integrity_failures']} mismatches in H36/H40. Both injected an empty resolver mapping, but the control arm restored normal resolution and therefore discovered the clue. Frozen results/evaluator are preserved unchanged. Separate holdout_evaluation_audit.json compares identical missing-outcome operations in both arms: equal authority, no experimental publication. That targeted diagnostic is related evaluation evidence, not a corrected holdout score or blind validation. Experimental-isolation assurance comes from the dedicated HTTP matrix and provenance checks, not the holdout's placeholder summary field alone.

This holdout is developer-authored, not independent blind validation; its state-comparator defect limits two cases' original integrity evidence.
''')
    report('10_HISTORICAL_MILESTONE_REPLAY.md',f'''# HISTORICAL MILESTONE AFTER REPAIR
Request and original saved candidate match PR65. historical_after.json includes exact initial/post-state, authoritative resolution, mandatory projection/trusted disclosure, validation rejection, hook fallback, actual publication helper input/output, final serialized HTTP body and measured stages. Status {replay['status_code']}; final body:

> {replay['facing']}

Discovery is communicated verbatim. Count/origin/direction remain unclear. No patrol identity, extra tracks, encounter, route or persistent consequence is added. This proves final HTTP publication, not merely hook output. No fresh provider execution is claimed.
''')
    lines=[]
    for k,r in enumerate(live,1):lines.append(f"{k}. `{r['request']['json']['text']}` — HTTP {r['status']}, {r['http_ms']/1000:.3f}s. Final text: {r['facing']}")
    report('11_HTTP_GAMEPLAY.md','''# REAL HTTP GAMEPLAY
Uvicorn served the actual FastAPI app on an ephemeral loopback TCP port. urllib sent JSON POST requests to /api/chat?ui_mode=player, read serialized response bodies, and shut the server down afterward. Five consecutive supported actions, no browser claim. http_gameplay.json records full requests/bodies, authority snapshots, current mandatory disclosure and validation/publication evidence for every action. disabled_sequence_controls.json and state_integrity.json compare the same five actions without experimental publication; all authority/resolution comparisons pass.

'''+ '\n\n'.join(lines))
    report('12_LIVE_PROVIDER_RESULTS.md',f'''# PROVIDER RESULTS
Live requests: 0. Provider tokens: 0. Live accepted/published presentations: 0/0. No key or connectivity probe was needed. Existing provider configuration was not changed. This optional experiment instead used the exact saved historical candidate, synthetic accepted introductions, and controlled unavailable/timeout faults. Synthetic sequence accepted/published: {usage['accepted']}/{usage['published']}; deterministic experimental fallbacks: {usage['fallbacks']}. Movement is a separate ordinary deterministic response.

Provider latency for saved/faulted cases is not live-provider latency. Ordinary narration is locally stubbed; its internal legacy attempt counters do not represent actual network requests. Each optional hook makes at most one generator call; provider-free repeat makes zero. Fallback adds no provider call or retry. No claim that live acceptance/naturalness improved.
''')
    faults={'A_provider_unavailable':'unavailable','B_timeout':'timeout','C_empty':'empty','D_malformed':'malformed','E_FAIL':'FAIL','F_REVIEW_REQUIRED':'REVIEW_REQUIRED','G_VALIDATION_ERROR':'VALIDATION_ERROR','H_refusal':'legacy_refusal','I_unknown_refusal':'legacy_unknown','J_missing_optional':'missing','K_persistent':'persistent','L_inventory':'inventory','M_hidden':'hidden','N_route':'contradiction','O_helper_exception':'helper_exception','P_serialization_exception':'serialization_exception','Q_unsupported':'unsupported','R_resolution_failure':'resolution_failure','S_interrupted_client':'interruption','T_flag_disabled':'flag_disabled'}
    selected={r['name']:r for r in matrix}
    faultrows=[dict(id=k,matrix_case=v,status=selected[v]['status'],passed=True,publication=(selected[v].get('trace') or {}).get('publication'),scope='HTTP regression; actual disconnected TCP construction evidence separately in client_interruption.json' if v=='interruption' else 'HTTP regression') for k,v in faults.items()]
    
    for item in faultrows:
        if item['id']=='M_hidden':item.update(passed=False,finding='Narration safe, but full JSON body exposes hidden canaries in other fields')
    save('failure_injection.json',dict(cases=20,passed_specific_controls=19,hidden_payload_control='FAIL',full_body_safety='FAIL',rows=faultrows,interruption=read('client_interruption.json')))
    report('13_FAILURE_INJECTION.md','''# FAILURE INJECTION
20 requested controls executed. Nineteen meet their specific fault-selection/error expectations; the hidden-output control only checked player_facing_text and is FAIL when applied to the whole body. Full-body safety is not established by these local control results. Recoverable optional provider/presentation failures publish current trusted information; unsafe prose is absent; helper exception and final body drop restore deterministic text and record recovery. Resolution/initialization and serialization injections return HTTP 500 rather than synthetic success. Unsupported grammar does not create a destination; flag disabled uses ordinary publication. Detailed decisions and response bodies are in failure_injection.json and publication_matrix.json.

Actual TCP interruption: a full request was sent and the socket closed before reading. Server-side ASGI capture records a complete response containing trusted current no-new-information outcome; client receipt is not claimed. This is not durable acknowledgment/redelivery. Serializer fault is a real HTTP construction failure; no successful publication claim. Do not conflate optional failure recovery with general application-error recovery.
''')
    report('14_STATE_AND_DISCLOSURE.md',f'''# STATE AND DISCLOSURE INTEGRITY
Five TCP actions match disabled controls on location/visited scenes, scene runtime/overlays, world, character/inventory and combat; deterministic resolutions match. Movement reaches old_milestone; discovered footprint text remains persisted through both follow-ups. Narration guards compare full session/world/character/combat before and after every tested hook invocation; all equal. Provider arguments remain detached. Trusted facts are read from current resolver projection; old known facts remain contextual. Narration-only hidden and cross-session/campaign controls pass. The full HTTP body leaks hidden canaries through existing state-bearing fields; hidden-information integrity therefore FAILS. See critical_incident.json; this is present before repair and with the flag disabled. Request-local resolution identity plus consumed binding prevents stale or duplicate-action fallback.

{len(baseline['protected_hashes'])} entry data, protected ATGB and PR65 evidence hashes unchanged after regression. Original dirty baseline changes are retained. Two raw holdout state mismatches are audited evaluation errors (different resolver operations), not hidden as passes; separate matched missing-outcome control is equal. Publication never reruns resolution or applies effects. No delivery-state database, ACK queue or new truth owner.
''')
    timings=read('historical_after.json')['timings']
    report('15_LATENCY_AND_QUALITY.md',f'''# LATENCY AND QUALITY
Five TCP response times: {', '.join(f"{v/1000:.3f}s" for v in latency['http_ms'])}. Mean {latency['average_ms']/1000:.3f}s; max {latency['maximum_ms']/1000:.3f}s. PR65 reference 7.39s/16.13s used live provider and a different sequence/TestClient transport. These measurements do not establish a responsiveness improvement.

Exact after-repair replay measured stages in milliseconds (nested, not additive): `{json.dumps(timings)}`. Includes deterministic resolution, trusted rendering, validation/composition, publication preparation/verification and HTTP serialization. Optional provider is saved/faulted (no live latency). HTTP serialization timing arrays and total latency are preserved; instrumentation is tooling-only and adds no provider call.

Discovery clarity/mechanical accuracy/state consistency: exact uncertain print wording survives. Action relevance/agency: supported action resolution and existing exit retained. Continuity/recovery: follow-ups persist discovery and publish no-new outcome. Naturalness/repetition remain limited: generic target fallback and repeated no-new statements are visible in exact transcripts. No human rating or broad gameplay-quality claim.
''')
    report('16_REGRESSION_RESULTS.md',f'''# REGRESSION RESULTS
Focused: {reg['focused']['passed']} passed / {reg['focused']['failed']} failed / {reg['focused']['errors']} errors; new failures: `{new}`. Historical focused baseline 848 passing / 3 known failures. PR55 holdout wrapper: {reg['holdout']['passed']} passed / {reg['holdout']['failed']} failed. Broader authority assurance: {reg['broader_hard_validation']['passed']} passed / {reg['broader_hard_validation']['failed']} known failures; no unrelated repair. Exact commands, node ids/messages and XML in regression_summary_final.json and *_final files. First aggregate run also exposed a stale PR49 static prohibition on consuming hook evidence and one unclassified transient HTTP 500 for malformed output. The static assertion was updated to require the explicit publication/binding/verification boundary while retaining forbidden-import and unsupported-effect assertions. Malformed output passed the isolated diagnostic (20 checks) without production changes. The aggregate rerun was interrupted on the independently discovered critical hidden payload leak, so no completed clean final rerun is claimed. Initial aggregate logs/XML are preserved; the transient cause is not established. Full repository suite not run.

Relevant PR55–65 coverage, H41, consequence/inventory/hidden protections, discovery language, contextual facts, uncertainty/paraphrase, quarantine/fallback, authoritative movement/persistence, provider-free repeat and state guards retained. The protected regression runner restores known historical artifact rewrites and records the restored paths. Source freeze/protected-hash checks follow the entire run.
''')
    report('17_LIMITATIONS_AND_OPEN_RISKS.md','''# LIMITATIONS AND OPEN RISKS
CRITICAL: serialized JSON exposes hidden information beyond narrated text. Experimental execution stopped. Entry-source and disabled controls also leak, so this is a preexisting publication-boundary defect, not a new AI claim. No PASS on hidden-information protection. Developer-authored holdout, not blind validation. Raw holdout remains 38/40 because two failure controls compared different resolver operations; matched-operation audit is a separate targeted diagnostic, not a rerun or replacement score. Finite existing AI validators and bounded optional grammar remain unchanged. No live provider, browser, human quality review or official ATGB evaluation. No guarantee of delivery after client interruption or serialization failure. No durable ACK/redelivery protocol. Existing ordinary pipeline can return HTTP 200/legacy refusal for an empty resolver mapping; the experimental publisher supplies no fabricated gameplay outcome. General malformed-resolver error schema is not repaired here.

Optional sentence naturalness, target labels and duplicate no-new prose remain limited. Experimental flags remain default off and session-gated. Internal provenance is trusted in-process data, not cryptographic attestation. Request-local binding is not a persistent message store. Existing known broader/focused failures remain; full suite unrun. One initial aggregate malformed-output HTTP 500 did not reproduce under exception-enabled diagnostics before the interrupted aggregate rerun; its transient cause remains unclassified and the original failure is preserved. Prior dirty work remains outside this incremental diff.
''')
    report('18_NEXT_SESSION.md',f'''# NEXT SESSION
Verdict: {verdict}. Exactly one primary next step: **{next_step}**. Stop affected experimental execution. Preserve the mandatory-text repair, frozen holdout and critical incident evidence. Diagnose the existing full-state response projection offline, then repair its hidden-information boundary in a separately scoped cycle. Do not expand gameplay or start PR67 presentation work.

Read reports 01/04/06/09/13/16/17, historical_after.json, holdout_results.json plus holdout_evaluation_audit.json, state_integrity.json, protected_integrity.json and implementation.diff. Source is frozen after repair; holdout was executed once and must not be rerun/tuned. Experimental flags remain off outside isolated test subprocesses. No commit/push. Review archive pointer is artifacts/pr_play_66/archive_path.txt.
''')
    metrics=dict(verdict=verdict,baseline=baseline['commit'],production_files=['game/api.py','game/quarantined_investigation_narration.py'],development_tests=45,holdout={k:v for k,v in holdout.items() if k!='rows'},holdout_evaluation_audit=audit['passed'],critical_mandatory_omissions=0,critical_unsafe_publications=46,critical_unsafe_ai_presentations=0,unsafe_count_scope='41 matrix responses plus five TCP gameplay responses with hidden payload values; other responses not included in this count',http_gameplay_actions=5,provider=usage,latency=latency,state_integrity=state['passed'],experimental_isolation=True,hidden_payload_integrity=False,hidden_payload_matrix_failures=41,hidden_payload_gameplay_failures=5,failure_injection_specific_passes=19,regression=reg,next_step=next_step)
    save('metrics.json',metrics)
    nextpath=ROOT/'docs/NEXT_SESSION.md';current=nextpath.read_text(encoding='utf-8')
    intro=f'''## Latest publication repair — PR-PLAY-66 (2026-11-04)

**{verdict}.** Critical stop: complete HTTP JSON exposes hidden canaries through existing session/world/scene fields, including entry-source and flag-disabled controls. Do not run the affected experimental pathway. The second regression run was interrupted; continue offline diagnosis only. See critical_incident.json. Exact PR65 mandatory-text HTTP defect reproduced and repaired at the existing publication seam. Request-local provenance plus final mandatory-disclosure verification recovers deterministic text once on presentation/helper failure, without provider or resolver replay. Flags remain default off and session-bound.

45 HTTP development cases; 40/40 frozen publication decisions, zero critical omissions/unsafe publications. Raw holdout 38/40: two state comparisons used different resolver operations; preserved unchanged, with separate matched-operation audit passing. Five consecutive real localhost TCP actions include existing movement, exact milestone disclosure and two follow-ups; all authority/resolution states equal disabled controls. One synthetic accepted/published presentation, three fallbacks; zero live requests/tokens. Initial aggregate {reg['focused']['passed']} pass / {reg['focused']['failed']} failures (3 known, obsolete static assertion, unexplained malformed HTTP 500); 20 targeted diagnostic checks pass. Final aggregate rerun interrupted, broader {reg['broader_hard_validation']['failed']} known failures. Full-body hidden integrity FAILS in 41 matrix responses and five TCP actions. Protected entry hashes and implementation freeze intact. No commit/push; prior dirty work retained.

Read development/campaigns/product_realization/pr_play_66 reports 01/04/06/09/13/16/17 and artifacts/pr_play_66/{{historical_after,holdout_results,holdout_evaluation_audit,state_integrity,regression_summary_final}}.json. Exact archive: artifacts/pr_play_66/archive_path.txt. Exactly one primary next cycle: {next_step}. No ACK protocol, semantic redesign or broad synonym repair. Older stop/next-cycle instructions below are historical and superseded by the explicit PR66 request.

'''
    if '## Latest publication repair — PR-PLAY-66' not in current:nextpath.write_text(current.replace('# NEXT_SESSION\n','# NEXT_SESSION\n\n'+intro,1),encoding='utf-8')
    print(verdict)

    packet=ROOT/'artifacts/validation_evidence/pr_play_66';packet.mkdir(parents=True,exist_ok=True)
    examples=[]
    for label,row,source,result in [('representative_failure',before,'artifacts/pr_play_66/baseline_reproduction.json','mandatory_omission'),('representative_success',replay,'artifacts/pr_play_66/historical_after.json','trusted_disclosure_published')]:
        trace=row['trace'];examples.append(dict(campaign='pr_play_66',scenario_id='historical_milestone',turn_index=5,player_input=row['request']['json']['text'],input_classification='runtime_discovered',simulated_player_rationale='Exact historical defect replay',prior_context='Existing authored patrol-rumor exit moved to old_milestone; captured pre-action state retained.',gm_player_facing_output=row['facing'],original_semantic_result=result,mandatory_gates=trace.get('validation'),diagnostic_result=trace.get('publication',{}),runtime_validity=row['status_code']==200,final_emission_metadata=trace.get('publication'),continuation='Two follow-ups completed in the separate five-action TCP sequence' if result=='trusted_disclosure_published' else 'Baseline reproduction stopped before repair',source_artifact=source,human_review_status='not_human_reviewed',evidence_label=label,evaluator_disagreement='No semantic evaluator override; raw holdout control defect documented separately'))
    selected={}
    for row in examples:
        row.update(example_id=row['evidence_label'],player_input_classification=[row['input_classification']],exact_gm_output=row['gm_player_facing_output'],semantic_result=row['original_semantic_result'],human_review=dict(status='not_human_reviewed',rationale='Inspect exact response and source trace.'),source_artifact_path=row['source_artifact'],evaluator_disagreement=dict(present=False))
        selected[row['evidence_label']]={'example_id':row['example_id']}
    incident=read('critical_incident.json')
    examples.append(dict(example_id='critical_hidden_payload',player_input='I examine the weathered milestone.',player_input_classification=['runtime_discovered'],exact_gm_output='Full HTTP payload exposes hidden values: '+json.dumps(incident['paths'],ensure_ascii=False),semantic_result='FAIL_HIDDEN_INFORMATION_PUBLICATION',human_review=dict(status='not_human_reviewed',rationale='Offline exact payload inspection.'),source_artifact_path='artifacts/pr_play_66/critical_incident.json',evaluator_disagreement=dict(present=True,rationale='Narration-only safety assertions missed hidden data elsewhere in JSON.')))
    selected.update(unexpected_unclassified={'example_id':'critical_hidden_payload'},evaluator_disagreement={'example_id':'critical_hidden_payload'})
    (packet/'evidence_manifest.json').write_text(json.dumps(dict(campaign=dict(campaign_id='pr_play_66',run_count=2,turn_count=2,gm_boundary='Historical HTTP before/after saved-candidate replay; full-body hidden leak forces C FAIL.'),selected_evidence=selected,evidence_scope='runtime_and_semantic_behavioral_evidence',official_ATGB=False,examples=examples),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (packet/'evidence_summary.md').write_text("""# PR-PLAY-66 behavioral evidence

Tested final HTTP publication, not broad RPG quality. Exact saved historical candidate at original milestone; controlled runtime-discovered player input. One baseline failure and repaired replay, plus five consecutive actual TCP actions; saved/synthetic candidates, no live provider or browser/human-realism claim.

Representative Success: exact footprint fact reaches final HTTP body; examples embedded in manifest.

Boundary Success: rejected/empty/malformed/provider timeout and publisher exception recover mandatory text in HTTP matrix.

Representative Failure and Severe / Worst Failure: before repair, HTTP refusal omits the deterministic discovery. Exact transcript embedded in manifest.

Evaluator Disagreement: two raw holdout state comparators use different resolver operations; raw 38/40 preserved, 40/40 publication decisions. Separate matched-operation audit passes.

Critical Full-body Failure: hidden canaries are published outside player_facing_text in 41 matrix responses and all five gameplay actions; entry/disabled controls also leak. Experiment stopped; no PASS. Unexpected / Ambiguous: first aggregate malformed-output 500 did not reproduce in targeted checks; cause unclassified, aggregate rerun interrupted. Finite optional language and repetitive fallback remain quality limitations.

Not proven: live-provider acceptance, universal natural-language safety, client delivery after interruption, independent blind validation, human quality or official ATGB performance. All examples require human review; no human judgment is fabricated.
""",encoding='utf-8')
