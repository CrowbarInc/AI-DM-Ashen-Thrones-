"""Build PR-PLAY-31 reports and a self-contained, credential-scanned review ZIP."""
import copy
import difflib
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import timeit
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))


def save(name, data):
    (OUT/name).write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')


def report(name, text):
    (OUT/f'PR_PLAY_31_{name}.md').write_text(text.strip()+'\n', encoding='utf-8')


def junit(name):
    suite = ET.parse(OUT/name).getroot().find('testsuite')
    cases = suite.findall('testcase')
    return dict(tests=int(suite.get('tests')), passed=sum(not any(c.find(k) is not None for k in ('failure','error','skipped')) for c in cases),
                failed=[c.get('classname')+'::'+c.get('name') for c in cases if c.find('failure') is not None],
                errors=[c.get('classname')+'::'+c.get('name') for c in cases if c.find('error') is not None],
                skipped=int(suite.get('skipped')), seconds=float(suite.get('time')))


def build():
    from game.conversational_orchestration import _destination_phrase, _movement_and_purpose, _analyze_clause, _exit_rows
    original = read('baseline_reproduction.json')
    replay = read('integration.json')
    turns = replay['turns']
    base = original['turns'][2]
    t3, travel, inspect, repeated = turns[2:]
    text = t3['player']
    route_scene = json.loads((ROOT/'artifacts/pr_play_30/verified_fixture/scenes/frontier_gate.json').read_text())
    dest_scene = json.loads((ROOT/'artifacts/pr_play_30/verified_fixture/scenes/old_milestone.json').read_text())
    routes = _exit_rows(route_scene)
    save('authored_route_evidence.json', dict(source_scene=route_scene, destination_scene=dest_scene,
         adapted_routes=routes, known_information=t3['before']['session']['clue_knowledge'], decision=t3['router']))
    save('router_after.json', dict(destination=_destination_phrase(text), purpose=_movement_and_purpose(text)[1],
                                  clause=_analyze_clause(text, routes), decision=t3['router']))
    state_checks = []
    for row in turns:
        before, after = row['before'], row['after']
        state_checks.append(dict(turn=row['turn'], player=row['player'],
            scene_before=before['session']['active_scene_id'], scene_after=after['session']['active_scene_id'],
            turn_delta=after['session']['turn_counter']-before['session']['turn_counter'],
            clock_delta=after['session']['clocks']['time_pressure']-before['session']['clocks']['time_pressure'],
            character_unchanged=before['character']==after['character'],
            campaign_unchanged=before['campaign']==after['campaign'],
            new_clue_ids=sorted(set(after['session'].get('clue_knowledge',{}))-set(before['session'].get('clue_knowledge',{}))),
            evaluator_mechanical=row['evaluation']['mechanical']['status'], evaluator_stop=row['evaluation']['stop'],
            overlay_integrity=row['evaluation']['overlay_comparison']['integrity'],
            final_hard_validation=row['evaluation']['semantic']['final_hard_validation']))
    assert all(not c['evaluator_stop'] and c['character_unchanged'] and c['overlay_integrity'] for c in state_checks)
    save('state_integrity_checks.json', state_checks)
    for row in turns:
        save(f'T{row["turn"]}_before.json', row['before'])
        save(f'T{row["turn"]}_after.json', row['after'])
        save(f'T{row["turn"]}_diff.json', row['state_diff'])
        save(f'T{row["turn"]}_evaluation.json', row['evaluation'])
    baseline, extra, after, focused = (junit(n) for n in ('baseline.xml','baseline_extra_valid.xml','regression_final.xml','focused.xml'))
    comparison = dict(baseline_primary=baseline, baseline_extra=extra, after_comparable=after,
                      focused_and_additional_regressions=focused,
                      new_failures=sorted(set(after['failed'])-set(extra['failed'])-set(baseline['failed'])),
                      unchanged_historical_failures=sorted(set(after['failed'])&set(extra['failed'])),
                      live_provider_requests=0)
    assert not comparison['new_failures'] and len(after['failed']) == 7
    assert not after['errors'] and not focused['errors'] and not focused['failed']
    save('test_comparison.json', comparison)
    # The baseline module is captured before edits, including inherited work.
    spec = importlib.util.spec_from_file_location('pr31_before', OUT/'conversational_orchestration.before.py')
    old = importlib.util.module_from_spec(spec); sys.modules[spec.name]=old; spec.loader.exec_module(old)
    count = 10000
    perf = dict(iterations=count,
                before_destination_us=timeit.timeit(lambda: old._destination_phrase(text), number=count)/count*1e6,
                after_destination_us=timeit.timeit(lambda: _destination_phrase(text), number=count)/count*1e6,
                replay_turn_seconds=[row['elapsed_seconds'] for row in turns],
                additional_provider_calls=0, planning_loops=0, retries_added=0)
    save('performance.json', perf)
    # Verify every published line against authored hidden facts and internal identifiers.
    secrets = route_scene['scene']['hidden_facts'] + dest_scene['scene']['hidden_facts']
    ids = ['muddy_footprints_northwest','milestone_mud_prints',routes[1]['id']]
    confidentiality = dict(exact_hidden_fact_disclosures=[], internal_identifier_disclosures=[], final_hard_validations=[])
    for row in turns:
        public = row['response']['gm_output']['player_facing_text']
        confidentiality['exact_hidden_fact_disclosures'] += [s for s in secrets if s in public]
        confidentiality['internal_identifier_disclosures'] += [s for s in ids if s in public]
        confidentiality['final_hard_validations'].append(row['evaluation']['semantic']['final_hard_validation'])
    confidentiality['passed'] = not confidentiality['exact_hidden_fact_disclosures'] and not confidentiality['internal_identifier_disclosures'] and all(confidentiality['final_hard_validations'])
    assert confidentiality['passed']
    save('confidentiality.json', confidentiality)

    report('BASELINE', f'''# PR-PLAY-31 baseline
Revision: `{(OUT/'revision.txt').read_text().strip()}`. Working tree was extensively dirty; inherited status is preserved in git_status_before.txt. No commit, reset, or push was performed.

Before editing: captured conversational_orchestration.before.py and ran the actual PR-PLAY-30 HTTP harness with all model surfaces mocked and the existing live-call guard enabled. baseline_reproduction.json preserves the complete original run.

Exact command: {text}

Original extracted destination: `{read('baseline_router.json')['destination']}`. No purpose field; `investigate` absent from the router's inspection cues. Router: MOVE -> DECLINE / destination_not_established. No selected target, interpreter call, exploration resolver, or gameplay parser invocation. No turn or clock advance, scene transition, inventory, currency, or clue mutation; social interlocutor bookkeeping cleared and refusal logged.

Published: {base['response']['gm_output']['player_facing_text']}

Baseline primary: {baseline['passed']} passed, {len(baseline['errors'])} setup error, zero assertion failures, 211 collected including the historical observation harness. Comparable primary subset excludes that one observation test (which intentionally asserts the old failure): 209 passed + one setup error over 210 tests. Additional comparable suite: 75 passed, seven assertion failures over 82 tests. Baseline WinError 5 in session.json atomic replacement is preserved verbatim. An earlier inventory invocation named two nonexistent test files and collected zero tests; baseline_extra.txt records this command error. Corrected invocation completed normally; no unresolved collection error.

Entry points: game/conversational_orchestration.py (_destination_phrase, _analyze_clause, _committed_movement_or_compound_decision, _resolve_move_target, _resume_bounded_pending); game/local_interaction.py normalize_local_approach; game/player_interpretation_bridge.py normalized_action_from_interpretation; game/exploration.py resolve_exploration_action; game/clues.py apply_socially_revealed_leads and clue_knowledge; game/api.py _apply_authoritative_clues_from_resolution and _apply_authoritative_resolution_state_mutation; game/scene_graph.py is_transition_valid; tools/playtest/gameplay.py evaluate; tools/playtest/overlays.py compare_overlays. Current copies are packaged under source/.
''')
    report('PURPOSE_ROUTING', f'''# PR-PLAY-31 purpose-aware routing
Confirmed root cause: the router matches destination prepositions without first separating infinitive purpose. In the original text its only recognized destination preposition is the purpose's “to”; greedy tail capture yields “investigate the muddy footprints”. The reported last-match loop is present, but is not a general last-preposition parser: its anchored greedy expression can consume the whole remainder. Bare “northwest of the crates” previously has no destination-preposition match.

Repair: a finite verb vocabulary splits movement from “to”, “in order to”, or “so as to” purpose. Existing destination extraction then runs on the movement clause, with a bounded bare-movement fallback. Nested location descriptions retain their prepositions. Purpose is preserved in secondary_intentions, not executed. _analyze_clause also exposes it separately. inspect, examine, investigate, look for, search for and check are recognized; existing investigation target/discovery authority remains in the bridge and resolver. Search wording describes an attempt, not a guaranteed find.

Corrected destination: `{_destination_phrase(text)}`. Purpose: `{_movement_and_purpose(text)[1]}`.

Generalization: 12 parsing cases cover market/buy, guard/ask, gate/speak, road/investigate smoke, wagon/inspect wheels, original command, nested locations, alternative destinations, another purpose preposition, unrelated rest purpose, and no purpose. Six inspection cue cases pass. Local approaches with “to ask” and “to investigate” retain PR-PLAY-23's authored same-scene checks and execute no movement.

Files: game/conversational_orchestration.py, route_authority.py, player_interpretation_bridge.py, local_interaction.py, api.py, api_turn_support.py; tools/playtest/overlays.py and investigation_overlay_authority.py; tests/test_pr_play_31_purpose_routing.py.

Limits: finite purpose vocabulary; no general grammar, coordinate solver, clue semantic equivalence, multi-action execution, or physical target lookup across scenes. Unknown purpose verbs may still require clarification. Existing compound-action confirmation remains for separate consequential clauses. No provider call, model change, retry path, or planner was added.
''')
    report('ROUTE_AUTHORITY', f'''# PR-PLAY-31 route authority
Source: frontier_gate, destination: old_milestone, label: “Follow the missing patrol rumor”. The authored row has no explicit ID; the existing affordance convention derives `{routes[1]['id']}`. The adapter copies the current authored row; it adds no graph edge or canon mutation. Both authored rows and adapted views are in authored_route_evidence.json.

Visibility: public legacy exit (no hidden/visible restriction). Availability: no locked/accessibility restriction. Prerequisites/required discoveries/conditions: absent. Travel cost: none authored; existing ordinary turn clock advances once. The destination must still exist and be reachable through the existing bridge and scene graph.

Knowledge: the actual conversation discloses patrol_rumor and persists muddy_footprints_northwest. The existing minimum-lead mechanism separately persists minlead_exit_frontier_gate_old_milestone with the public route label. This makes the route a legitimate choice, but does not establish that it reaches the precise footprints in the rumor. No foreign-key association links the rumor clue to the exit or to milestone_mud_prints. No prose similarity or clue-ID alias authorizes automatic selection.

Original decision: {t3['router']['authorization']['route_decision']} for the exact referenced destination; actionable clarification presents currently available public exits. Multiple public choices are not treated as multiple proven routes to the exact evidence. The player explicitly selecting the patrol route authorizes the control travel. Direct unambiguous authored destination + purpose selects UNIQUE_AUTHORIZED_ROUTE; ambiguous explicit destinations clarify; blocked routes refuse; unsupported references never move.

Visibility and source-scene filters exclude hidden/wrong-scene routes. Eligibility uses existing flag/clue conditions and checks locked, available, accessible, reachable and availability fields. Unknown prerequisites/required_discoveries fail closed. The bridge rechecks at execution, including after clarification. No hidden route is offered. Data files were not changed.

Clue identity: travel discovers no milestone_mud_prints. Only the separate prints examination discovers it; the original rumor entry remains intact. Neither discovery nor narration asserts that the two clues are identical or causally proven related.
''')
    report('INTENTION_CONTINUITY', '''# PR-PLAY-31 intention continuity
Policy: one authorized primary action per turn. Movement purpose is never a second executed action. Direct uniquely grounded travel executes MOVE only. Unresolved purpose is stored as an existing deferred_intentions entry under conversational_context.pending_clarification, with text, operation, status=pending, target_id empty and supported=false. This is conversation bookkeeping, not a quest, world fact, investigation result, or permission to resume automatically.

For clue-route clarification, existing ambiguous_destination choices additionally carry deferred_steps. Explicit choice resumes the authored move and transfers the purpose to deferred_intentions. The bridge rechecks route eligibility. Context survives save/reload and the authorized scene transition; test snapshots verify it. A bare affirmative cannot execute the unresolved investigation. A later explicit target/action is interpreted anew through the existing bridge and resolver. Completed/failed investigation is recorded by that resolver's success, kind, clue_id and state changes; arrival only records MOVE as the executed operation. An explicit new action supersedes stale pending context.

Player continuation after travel: “Your intended follow-up is still pending. Choose a visible target here when you are ready.” This is projected before final acceptance from successful travel and deferred metadata. Existing immutable-response and confidentiality checks still run. A rejected or blocked route never produces an arrival or investigation result. Unsupported/non-inspection purposes (buy supplies, rest) remain pending and cause no transaction or other effects.

No new persistent intention store, objective system, action planner, or compound resolver was introduced. Pending intent remains non-authoritative and does not automatically bind the rumor to a newly visible object.
''')
    transcript = ['# PR-PLAY-31 offline integration transcript',
                  'All provider responses are deterministic mocks; the application, routing, disclosure, travel, clue resolution, persistence and validators are real. Opening uses the frozen baseline campaign and the production engine-owned opening renderer with a mocked selector. Conversation interpreter records are captured PR-PLAY-29 responses replayed offline; examination uses a conservative single INSPECT proposal. No clue is manually injected into the integration session.',
                  'Opening: '+read('opening.json')['response']['gm_output']['player_facing_text']]
    for row in turns:
        transcript += [f'## T{row["turn"]}: {row["player"]}',
                       row['response']['gm_output']['player_facing_text'],
                       f'Router: {row["router"]["reason"] if row["router"] else "existing interpreter/bridge"}; mocked interpreter requests: {row["mocked_interpretation_calls"]}. Native result: {row["internal"]["resolution"].get("kind")}. Scene {row["before"]["session"]["active_scene_id"]} -> {row["after"]["session"]["active_scene_id"]}. Evaluator stop={row["evaluation"]["stop"]}.']
    transcript += ['Original natural-language result: Outcome B, actionable clarification; no travel or investigation executed. T4–T6 are a separately identified control path after explicit authored-route choice, not evidence of automatic travel from T3. T5 discovers authored evidence; T6 returns already_searched with no second discovery. See integration.json for mock payloads versus actual engine outputs, snapshots, diffs, and resolver traces.']
    report('INTEGRATION_TRANSCRIPT', '\n\n'.join(transcript))
    report('STATE_INTEGRITY', '''# PR-PLAY-31 state integrity
All six actual pipeline turns pass the native final hard validation and the ordinary-turn evaluator with stop=false. Full snapshots, diffs and evaluations are T1–T6_* plus integration.json. state_integrity_checks.json summarizes clock, scene, character, campaign and clue changes.

T3 clarification: zero turn/clock increment, unchanged world, character, clue knowledge and scene. Only conversation context and logging change. T4 control travel: frontier_gate -> old_milestone through the existing authored route/bridge/graph; one turn and one clock increment; no evidence clue. T5: prints -> milestone_mud_prints through existing resolve_exploration_action, discovered only after legitimate arrival; one turn and one clock increment. T6: already_searched, no duplicate clue; one ordinary attempted-action turn. Every character snapshot is unchanged: no inventory, currency or HP grant. No quest completion is created.

The evaluator previously recognized social projections only. A bounded investigation projection now requires matching authored current-scene interactable and clue text/ID, successful persisted resolver result, matching public result and action, hard-valid final emission, one new matching log entry, correct turn increment, persisted discovered knowledge and resolved target. It permits exactly appending that selected clue text to the active overlay. Extra flags, other scenes, hidden/inaccessible targets, invented clues, rejected text, missing persistence and log mismatches remain failures. This is an evidence reconciliation rule, not runtime execution authority.

confidentiality.json verifies exact hidden facts and internal clue/route IDs never occur in the public lines; native hard validations all pass. Existing response-confidentiality and privileged-read tests also run. Exact-string checks alone do not prove absence of every possible paraphrase; no live-provider confidentiality claim is made.
''')
    report('NEGATIVE_TESTS', '''# PR-PLAY-31 negative tests
New test module: 59 cases, including 12 destination/purpose cases; six inspection verbs; 12 route cases (unique explicit route, multiple matches, hidden/invisible/locked/unavailable/inaccessible routes, undiscovered prerequisite, wrong scene, nonexistent exit, unrelated clue, similar prose without authority); four execution-bridge rechecks; five inaccessible/absent inspection cases; six-turn actual HTTP replay; three travel-only purpose cases; two local approach cases; failed examination; and 13 strict overlay evaluator controls.

Known-but-inaccessible or invisible targets, remote physical targets, and unsupported targets never become valid INSPECT actions merely through knowledge. Failed skill check creates no clue. Repeated examination returns already_searched. Movement with inspect/buy/rest purpose advances only travel and leaves inventory and clue knowledge unchanged. Multiple destinations clarify; non-inspection purposes cause no transaction. Similar wording only offers public choices, never selects a destination automatically. No clue IDs are aliased.

Existing movement/compound tests cover focused destinations, ambiguous exits, unsupported passages, confirmation, hostile/restricted NPC access and scene transitions. PR-PLAY-23/25/27/28 regressions and PR-PLAY-20/21 confidentiality/read restrictions are included in the comparable suite; PR-PLAY-29 conversational continuity is reconstructed through actual disclosure and the follow-up question. Existing overlay tests and PR-PLAY-23 harness checks are added to the focused run. Synthetic negative fixtures are explicitly authored in tests; the integration fixture uses the frozen campaign with no manual clue injection.
''')
    report('TEST_RESULTS', f'''# PR-PLAY-31 test results
Raw logs and JUnit XML are preserved. Test transports are blocked by tests/conftest.py's live model guard; interpretation/opening/narration are deterministic mocks only.

Baseline primary: {baseline['passed']} passed, {len(baseline['errors'])} setup error / 211 including one historical failure-observation test. Comparable subset: 210 cases (209 passed, one Windows atomic-file setup error). Baseline additional: 75 passed, seven failed / 82. Baseline inventory typo: zero collected, corrected immediately; log retained.

Final focused run: {focused['passed']} passed / {focused['tests']}, zero failures/errors/skips, {focused['seconds']:.2f}s. This includes 59 new tests plus 40 existing overlay and harness controls.
Final comparable suite: {after['passed']} passed, {len(after['failed'])} failed / {after['tests']}, {len(after['errors'])} errors, {after['skipped']} skipped, {after['seconds']:.2f}s. All seven assertion failures match baseline nodes exactly. New assertion failures: zero. The baseline WinError 5 and a separate intermediate combat.json WinError 5 did not recur in the final run. They are transient Windows filesystem errors, not fixed by this change. Intermediate implementation failures are preserved in smoke/probe logs and resolved in final runs.

Unchanged historical failures:
{chr(10).join('- '+n for n in after['failed'])}

No unrelated historical failure was repaired. The historical PR-PLAY-30 observation harness is intentionally not rerun as a post-repair acceptance test: it asserts that the exact bug still occurs. Its before-run trace is retained; new integration replaces that assertion with the required clarification/travel/examination contract.

No complete repository-wide suite was run; the comparable affected suite covers movement, decomposition, clue knowledge/discovery/idempotence, investigation provenance, state/narration integrity, expression validation, topic authority, confidentiality and privileged reads.

Performance: destination-only microbenchmark over {count} iterations: before {perf['before_destination_us']:.2f} us, after {perf['after_destination_us']:.2f} us per call. Actual mocked-pipeline latencies are in performance.json. Extra provider calls/retries/planning loops: zero. Route matching is deterministic over current authored exits and known clue text; no embedding or semantic search. Interpretation latency on original request remains zero provider requests; clarification avoids interpretation entirely.
''')
    if (OUT/'post_review_verification.xml').exists():
        last = junit('post_review_verification.xml')
        assert not last['failed'] and not last['errors']
        with (OUT/'PR_PLAY_31_TEST_RESULTS.md').open('a', encoding='utf-8') as f:
            f.write(f'\nFinal source verification after the last parsing/status adjustments: {last["passed"]} passed, zero failures/errors in {last["seconds"]:.2f}s (new focused module + movement + local interaction). See post_review_verification.xml/txt.\n')
    answers = [
        'Yes: exact original HTTP refusal and router trace reproduced before repair.',
        'Yes: undifferentiated infinitive-purpose “to” capture plus missing bare destination handling confirmed.',
        'Yes: northwest of the crates retained.', 'Yes: investigate the muddy footprints represented separately.',
        'Yes: 12 parsing/generalization cases and unrelated purposes pass.',
        'Yes: investigate is an inspection cue; target/discovery authorization remains mandatory.',
        'Yes within the affected movement regression suite.', 'Yes: existing tests and new to-purpose approaches pass.',
        'Yes: public legacy frontier_gate exit to old_milestone, no authored prerequisites.',
        'Knowledge permits considering the public lead, but does not prove its physical destination matches the rumor.',
        'Only after explicit authored-route selection; the exact clue-directed request has no sufficient authored link for automatic choice.',
        'Yes: filtering plus execution-time recheck; negative controls pass.', 'Yes: public choices, no automatic ambiguous travel.',
        'No: the original request receives clarification, intentionally.', 'Yes: it names available public authored choices.',
        'Yes: deferred_steps then existing deferred_intentions persist through authorized travel.',
        'Yes: MOVE/arrival remains distinct from INSPECT/discover_clue.',
        'Yes: explicit-route control, examination and repeated examination use actual application pipeline.',
        'Yes: milestone_mud_prints appears only at T5 after prints examination.',
        'Yes: muddy_footprints_northwest remains an independent knowledge entry.',
        'Yes: clarification 0; each executed/attempted ordinary action +1 turn and clock.',
        'Yes for captured turns: exact authorizations, unchanged character, no arbitrary quest/currency/inventory effects, native evaluator passes.',
        'Yes for offline scope: native validations, negative controls and existing confidentiality/read tests pass.',
        'Yes: all 59 new tests pass, including evaluator tampering and authority negatives.',
        'No new assertion regressions in 292 comparable tests; seven historical failures remain.',
        'No: live-provider requests = 0.',
        'Unsupported: automatic rumor-to-physical-evidence equivalence, exact local geometry, automatic second-action execution, unknown purpose grammar, arbitrary route prerequisites.',
        'Ready for a narrowly scoped live clarification -> explicit route -> examination validation after external review; not evidence of a fully clean repository suite.',
        'PR-PLAY-32 should validate that staged chain with the real provider, especially coherent arrival, retained intent and separate clue narration. Do not auto-start it.',
    ]
    report('FINAL_VERDICT', '# PR-PLAY-31 final verdict\n\n**PASS — A: PURPOSE-AWARE EXPLORATION REPAIRED.** Original command produces accepted Outcome B; staged explicit-route control completes safely. Seven existing historical test failures remain, with no new assertion regressions in the comparable suite.\n\n'+'\n\n'.join(f'{i}. {a}' for i,a in enumerate(answers,1))+'\n\nStop for external review. No commit, push, live-provider experiment or PR-PLAY-32 work was performed.')

    sources = ['game/conversational_orchestration.py','game/route_authority.py','game/player_interpretation_bridge.py',
               'game/local_interaction.py','game/api.py','game/api_turn_support.py','game/exploration.py','game/clues.py',
               'game/scene_graph.py','tools/playtest/overlays.py','tools/playtest/investigation_overlay_authority.py',
               'tools/playtest/social_overlay_authority.py','tools/playtest/gameplay.py','tests/test_pr_play_31_purpose_routing.py']
    for name in sources:
        target=OUT/'source'/name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT/name,target)
    before = (OUT/'conversational_orchestration.before.py').read_text(encoding='utf-8')
    current = (ROOT/'game/conversational_orchestration.py').read_text(encoding='utf-8')
    (OUT/'purpose_router.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),current.splitlines(True),fromfile='before/game/conversational_orchestration.py',tofile='after/game/conversational_orchestration.py')),encoding='utf-8')
    (OUT/'git_status_after.txt').write_bytes(subprocess.check_output(['git','status','--short'], cwd=ROOT))
    save('scope.json', dict(changed_files=[n for n in sources if n not in {'game/exploration.py','game/clues.py','game/scene_graph.py','tools/playtest/social_overlay_authority.py','tools/playtest/gameplay.py'}],
                           inherited_dirty_worktree=True, router_patch_against_captured_worktree=True,
                           source_copies_include_inherited_authorized_preceding_passes=True, data_files_changed_by_implementation=False,
                           live_provider_requests=0, commits=0, pushes=0))
    files = [p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.zip'
             and p.name not in {'archive_verification.json','archive_path.txt','MANIFEST.json'}]
    findings=[]
    for p in files:
        raw=p.read_text(encoding='utf-8',errors='replace')
        if re.search(r'(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._-]{24,}',raw): findings.append(str(p.relative_to(OUT)))
    assert not findings, findings
    save('credential_scan.json', dict(matches=findings, environment_files_included=False, authentication_tokens_included=False))
    files = [p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.zip'
             and p.name not in {'archive_verification.json','archive_path.txt','MANIFEST.json'}]
    save('MANIFEST.json', dict(files=[dict(path=str(p.relative_to(OUT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in files]))
    stamp=subprocess.check_output(['powershell', '-NoProfile', '-Command',
        "[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMdd-HHmmss')"], text=True).strip()
    archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[OUT/'MANIFEST.json']:
            z.write(p, 'pr_play_31/'+p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len([n for n in z.namelist() if re.search(r'PR_PLAY_31_[A-Z_]+\.md$',n)]) == 9
        entries=len(z.namelist())
    save('archive_verification.json',dict(path=str(archive),exists=True,zip_crc_passed=True,entries=entries,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest()))
    (OUT/'archive_path.txt').write_text(str(archive),encoding='utf-8')
    print(json.dumps(dict(archive=str(archive),focused=focused,regression=after,verdict='A'),indent=2))


if __name__ == '__main__':
    build()
