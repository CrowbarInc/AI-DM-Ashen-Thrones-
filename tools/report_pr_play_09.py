"""Explicit-selection offline review package for PR-PLAY-09. Never runs gameplay."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from tools.build_review_handoff import build_handoff
from tools.playtest.runner import ROOT, write

O = ROOT/'artifacts/pr_play_09'
R = ROOT/'development/campaigns/product_realization/pr_play_09'
COMMAND = r'.\scripts\run_live_playtest.ps1 -Scenario FiveTurnGameplay -Mode Live -AuthorizeLiveProvider -CaptureResponse'
SOURCES = ['tools/playtest/runner.py', 'tools/playtest/worker.py', 'tools/playtest/gameplay.py',
           'tools/playtest/scenarios/FiveTurnGameplay.json', 'scripts/run_live_playtest.ps1',
           'tests/test_five_turn_gameplay.py', 'tests/validation_coverage_registry.py',
           'tools/validate_pr_play_09.py', 'tools/report_pr_play_09.py',
           'docs/AUTOMATED_PLAYTEST_GUIDE.md', 'docs/NEXT_SESSION.md']
CONFIRMATIONS = '''
- No live provider calls or provider-connectivity probes during this pass.
- No model changes.
- No output-budget increases (opening normally 3000; ordinary narration normally 600).
- No automatic retries (existing SDK=0 and host=0 controls retained).
- No gameplay implementation changes.
- No unauthorized gameplay-state mutations; only production endpoints changed disposable isolated stores.
- No new persistent gameplay structures.
- No experimental PR-EG integration.
- Frozen ATGB baseline unchanged.
- No secrets included; explicit file selection and configured-secret byte scan applied.
- No commit or push performed.
'''.strip()


def report(name, title, body):
    path = R/(name+'.md')
    path.write_text(f'# {title}\n\nPR-PLAY-09 · 2026-10-30 America/New_York · evidence_scope: structural_only.\n\n'+body.strip()+'\n', encoding='utf-8')
    return path


def main():
    O.mkdir(parents=True, exist_ok=True)
    R.mkdir(parents=True, exist_ok=True)
    results = {}
    cases = []
    for p in sorted(O.glob('*_regression.xml')):
        suite = next(ET.parse(p).getroot().iter('testsuite'))
        counts = {k: int(suite.get(k, '0')) for k in ('tests', 'failures', 'errors', 'skipped')}
        counts['passed'] = counts['tests']-counts['failures']-counts['errors']-counts['skipped']
        counts['failures_observed'] = [c.get('classname')+'::'+c.get('name') for c in suite if c.find('failure') is not None]
        results[p.stem.removesuffix('_regression')] = counts
        if p.name == 'gameplay_regression.xml':
            cases = [{'name': c.get('name'), 'outcome': 'FAIL' if c.find('failure') is not None else 'ERROR' if c.find('error') is not None else 'PASS'} for c in suite if c.tag == 'testcase']
    assert results['gameplay']['failures'] == results['gameplay']['errors'] == 0
    assert results['harness']['failures'] == results['harness']['errors'] == 0
    runs = json.loads((O/'regression_runs.json').read_text())
    assert not any(v['timeout'] for v in runs.values())
    passed, failed = (sum(v[k] for v in results.values()) for k in ('passed', 'failures'))
    write(O/'test_summary.json', results)
    write(O/'G1_G25_results.json', {'scope': 'Synthetic instrumentation controls; G1 evaluator-only, not six-request end-to-end completion', 'tests': cases})

    before = json.loads((O/'protected_before.json').read_text())
    after = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for name in ('data', 'game', 'static', 'experiments') for p in (ROOT/name).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    integrity = {'files': len(before), 'unchanged': before == after,
                 'changed': [k for k in before if before[k] != after.get(k)], 'added': sorted(set(after)-set(before))}
    write(O/'entry_to_exit_integrity.json', integrity)
    assert integrity['unchanged']
    example = Path(json.loads((O/'example_run.json').read_text())['run'])
    result = json.loads((example/'reports/result.json').read_text())
    assert result['provider_usage']['dispatched_requests'] == 6 and result['stop_reason'] == 'provider_budget_exhaustion'
    assert result['provider_exposure']['live_calls'] == 0
    target = O/'example'
    target.mkdir(exist_ok=True)
    for name in ('result.json', 'GAMEPLAY_REPORT.md', 'SUMMARY.md'):
        shutil.copy2(example/'reports'/name, target/name)
    with zipfile.ZipFile(example/'evidence/evidence.zip') as z:
        assert z.testzip() is None
        for item in json.loads(z.read('evidence/manifest.json'))['files']:
            assert hashlib.sha256(z.read(item['path'])).hexdigest() == item['sha256']
    # Preserve the full example evidence as selected uncompressed members so the
    # standard exporter can hash each member without nested-review archives.
    selected_example = [p for folder in ('configuration', 'baseline', 'opening', 'after', 'turns', 'diagnostics', 'reports', 'evidence')
                        for p in (example/folder).rglob('*') if p.is_file() and p.suffix != '.zip']
    historical = ROOT/'artifacts/atgb/automated_playtests/20261030T183848Z-5fe421902485/reports/result.json'
    history = json.loads(historical.read_text()) if historical.exists() else None
    historical_evidence = {'available': bool(history), 'source': str(historical.relative_to(ROOT)),
                           'sha256': hashlib.sha256(historical.read_bytes()).hexdigest() if history else None,
                           'opening_only': True}
    if history:
        historical_evidence.update({k: history[k] for k in ('provider_usage', 'opening_acceptance', 'opening_commits_observed', 'state_comparison')})
    write(O/'historical_opening_summary.json', historical_evidence)

    table = '| Lane | Passed | Failed | Errors |\n|---|---:|---:|---:|\n'+''.join(f"| {k} | {v['passed']} | {v['failures']} | {v['errors']} |\n" for k,v in results.items())
    report('01_BASELINE_AND_EXISTING_HARNESS', '01 — Baseline and Existing Harness', f'''
HEAD: `{(O/'revision.txt').read_text().strip()}`. Entry worktree extensively dirty:
production, normal campaign saves, governance, old evidence and untracked harness
files. Full entry status retained in artifacts/pr_play_09/entry_status.txt. Existing
work was preserved; scoped diff is against entry bytes, not an assumed clean HEAD.

Reviewed authorities: Development Constitution, NEXT_SESSION, PR-AA Product
Realization portfolio/roadmap, validation evidence standard, Product Realization
validation, review-handoff standard, state authority, testing documentation and ATGB
benchmark specification. Reviewed PR-PLAY-04 acceptance/commit repair, -05 diagnostics,
-06 output caps, -07 independent semantic diagnostics/capture and -08 runner/worker,
analysis, scenarios, deterministic matrix and closeout. No new gameplay owner.

Reused: runner HTTP/process lifecycle, worker SDK replacement, pinned ATGB isolation
and hashes, production provider admission/accounting/parser/semantic/acceptance and
persistence, existing comparator/classifier/export and standard review exporter.

Historical live evidence is locally available at the path recorded in
historical_opening_summary.json and its sibling evidence/evidence.zip. It records
one request, 26593 input / 1724 output / 28317 total tokens, accepted structured and
semantic opening, one commit, turn +1, log +1. This pass read that evidence; it did
not create it or make another live call. One opening proves no subsequent-turn reliability.
''')
    report('02_SCENARIO_DESIGN', '02 — Scenario Design', '''
FiveTurnGameplay v1.0.0 is pinned to frontier-gate-v1. Opening occurs once through
/api/start_campaign after /api/new_campaign and baseline capture. It is not a player turn.

| Step | Exact input | Fixture authority |
|---|---|---|
| T1 | I take a moment to look around the gate district. What do I notice? | scene visible_facts/opening_seed_facts |
| T2 | I approach the gate serjeant and ask what happened to the missing patrol. | world.npcs gate_serjeant; route_change topic; scene visible_facts |
| T3 | I examine the notice board carefully. What notices are posted? | scene.interactables notice_board; discoverable notice_patrol_route |
| T4 | I want to investigate the missing patrol. What leads can I pursue from here? | established notices, authorized prior discoveries and NPC topics |
| T5 | I approach the gate and try to enter the city. | Enter Cinderwatch exit targets market_quarter |

The serjeant is authored in world.npcs despite a different set of scene.addressables;
runtime recognition is tested rather than patched. Private identities and unearned
route-clue disclosure are not assumed available. No curfew hours, prices or patrol
fate are invented. Each action defines ID, input/category, properties, permitted and
forbidden changes, criteria, timeout, stop conditions, subject probes and scene prerequisite.

All inputs use production /api/chat, including movement. No direct resolver calls
in the harness, injected outcomes, forced quest acceptance, rewritten failed actions,
or invented alternatives. A refusal/check/obstacle may be legitimate. Unexpected
pre-turn scene invalidates the remaining fixed script: PARTIAL with skipped reasons.
No unbounded AI player exists. Changing the scenario requires a new explicit version.
''')
    report('03_HARNESS_IMPLEMENTATION', '03 — Harness Implementation', '''
Modified runner.py extends the existing scenario dispatcher and opening checkpoint;
worker.py adds synthetic SDK interpretation/narration records and two deterministic
turn faults. gameplay.py is an observer/evaluator/report helper composed by that
runner, not a second harness or a gameplay authority. PowerShell and Python entry
points recognize FiveTurnGameplay. Coverage registry names the new test module.

Each submitted turn waits for its HTTP response, captures state and native journal
slice, evaluates it, then decides continuation. Before the next submission, exhausted
request limits stop without dispatch. Token admission failures also stop. Structure,
semantic, provider and state failures stop; quality probes may continue. All skipped
turns receive reasons. No automatic retries or concurrently submitted actions.

Turn deadlines include before/API/after capture. The scenario retains the existing
180-second ceiling, individual request/turn cap 90 seconds, startup 30 and owned
shutdown 5. On interruption, owned worker cleanup precedes persistent salvage;
interruption.json and final/turn state survive where available. Missing final API
state remains explicitly unavailable. No restart continues a spent budget.

Exports include opening/, turns/Tn/{before,after,api_response,evaluation}, diagnostics
and reports. Individual source/API captures retain 2 MiB bounds; DM text in results
is bounded to 8192 characters with truncation metadata. Large diff values use 2048
character previews and SHA-256; exact values remain in snapshots. No repeated full
state blobs in result.json. Existing 32 MiB and 30-second evidence bounds remain.
''')
    report('04_MECHANICAL_EVALUATION', '04 — Mechanical Evaluation', '''
Opening retains PR-PLAY-04 acceptance, exact one commit/turn/log checks and rollback
comparison. Later turns compare preceding snapshots separately; zero turn advancement
is allowed for nonmutating informational responses, including their logged exchanges.
Advancing a resolved turn requires one corresponding log entry. Campaign must stay
started; movement must match an authored permitted destination and native resolved
transition/target. Characters, campaign configuration, combat, conditions and authored
scene structures are forbidden mutation roots in this noncombat script. New world
roots fail; native nonmutating contracts cannot change world, scene or turn count.

HTTP, provider finish, extraction, JSON, envelope, native semantic attempts/final seal,
nonresolution provenance and gameplay acceptance remain distinct. Failed candidate
validation is preserved separately from final hard validation. An unvalidated response
does not become semantic PASS from valid JSON. Missing evidence is UNKNOWN/INCONCLUSIVE.

Rules checks use the native noncombat_resolution contract: required check_request
presence and agreement between engine success_state and emitted resolution success.
No harness dice, check DC, success or failure is invented. Absent canonical rules
evidence stays uncertain; a recorded resolution alone is not proof of full adjudication.
Native semantic validation supplies unsupported-claim/disclosure authority. The tool
does not claim exhaustive hidden-information or world-mutation verification. Other
world/time/session changes and narration versus consequences remain reviewable from
full snapshots, resolution and native diagnostics; mutation authority beyond the
explicit checks is REQUIRES_HUMAN_REVIEW, not a generalized state-authority proof.

Findings distinguish confirmed mechanical, confirmed semantic, heuristic quality,
scenario limitation and unknown. Legitimate refusal and blocked movement controls
pass technical checks. Earliest mechanical/semantic/quality findings are separate,
linked to input, response, source, journal and comparison. No root cause is invented.
''')
    report('05_NARRATIVE_QUALITY_EVALUATION', '05 — Narrative-Quality Evaluation', '''
Rubric pr-play-09-quality-v1 covers Q1 responsiveness, Q2 grounding, Q3 continuity,
Q4 actionability, Q5 narrative quality, Q6 agency/consequences. Human scale:
0 complete failure, 1 major deficiency, 2 partially adequate, 3 good, 4 strong.

Every dimension has score/status, response evidence, method, confidence and explanation.
Automated evidence cannot justify a numerical narrative grade: scores remain null,
status REQUIRES_HUMAN_REVIEW. Q6 is N/A for simple observation/posted-information
description; no arbitrary zero. Human engagement, dialogue naturalness, believability
and pacing remain unscored. A future reviewer may populate supported judgments.

Deterministic probes: response existence, exact known generic marker and exact repeat.
Subject-word matching and repetition-as-poor-quality are explicitly heuristic. Missing
subject words cannot establish irrelevance; a refused answer is not automatically a
defect. No keyword-derived narrative score or global quality PASS is generated.
QualityReviewer is an interface for future optional assessment; no live judge/client
or extra grading call is implemented. Mechanical verdict and quality concerns stay separate.

The example flags repetition at T4 and a possible relevance concern on the serjeant
clarification. These originate in synthetic SDK control records; they are not a live
product diagnosis. Five completed API submissions would still not prove five meaningful
interactions. The exported assessment says NOT_ESTABLISHED for this budget-stopped run.
''')
    feasibility = '''
The hard ceiling is six provider requests total: opening plus whatever production
operations each action actually needs. Existing atomic admission and cumulative
ledger reconciliation remain authoritative. The worker disables SDK/host retries,
forbids connectivity probes, preserves normal routing/model selection and per-operation
output limits. No provider escalation/retry path is introduced. All operation records
retain model/purpose/owner, count, input/output/total tokens, latency, status and configured
zero retry count. Missing usage/latency stays null. Application latency is separate.

Aggregate ceilings remain 200000 input / 20000 output / 220000 total; any stricter
inherited ceiling wins. Effective limits print before worker launch. Opening normally
reserves up to 3000 output, ordinary narration 600; no allowance is increased. Existing
interpretation reservations also count. A successful historical opening used 28317
tokens; that is evidence, not a forecast of five additional turns or monetary cost.
No currency estimate is supplied.

Live interpretation calls request_interpretation; resolved actions can separately
call gm.call_gpt. The normal-pipeline synthetic example records opening=1, T1=1,
T2=1, T3=2, T4=1: six requests, 120/60/180 synthetic usage. T5 is skipped before
submission. The T2 fixture was clarified rather than forcing an NPC success. Five
actions each using interpretation+narration would expose eleven calls including
opening; this illustrates feasibility, not a guaranteed upper bound for every optional
production path. A complete five-turn run inside six cannot be guaranteed.

Readiness is conditional for a six-request diagnostic that may stop early. Keep the
hard limit. External reviewers may instead authorize a separately designed budget
scope after reviewing these native operation records. No larger ceiling or bypass
is implemented or authorized here. Do not restart the process to finish the script.
'''
    report('06_PROVIDER_SAFETY_AND_PERFORMANCE', '06 — Provider Safety and Performance', feasibility)
    (O/'provider_budget_feasibility.md').write_text(feasibility.strip()+'\n', encoding='utf-8')
    matrix = '''
| G | Control | Scope |
|---|---|---|
| G1 | Five successful evaluator records; final PASS while quality remains human-review | evaluator positive control only |
| G2 | Failed opening, no Turn 1 | HTTP |
| G3 | Turn 2 provider exception, stop with journal | HTTP + native-record control |
| G4 | Turn 3 malformed interpretation; invalid narration envelope | HTTP + native-record control |
| G5 | Generic semantic nonresolution classified separately | native-record/heuristic control |
| G6 | Legitimate NPC refusal not automatically failed | evaluator |
| G7 | Unsupported world claim rejected by native hard-validation evidence | evaluator of native contract |
| G8 | Forbidden character/new-world mutation | snapshot comparison |
| G9 | Authored movement agrees with native transition | evaluator |
| G10 | Supported blocked movement accepted | evaluator |
| G11 | Next action invalidated by scene divergence | HTTP read-side fault; no persistent injection |
| G12 | Six admissions exhausted; T5 never submitted | HTTP |
| G13 | Turn timeout, worker stopped, interrupted state exported | HTTP controller fault |
| G14 | Missing text/semantic evidence stays uncertain | evaluator |
| G15 | Off-topic text is heuristic concern, not confirmed defect | evaluator |
| G16 | Exact repeated narration is a concern | evaluator |
| G17 | Descriptive response changes no state/turn | evaluator |
| G18 | Canonical engine noncombat result consistent | real resolver-derived fixture; evaluator |
| G19 | Contradictory engine outcome detected | real resolver-derived fixture with negative control |
| G20 | Inapplicable Q6 is N/A, score null | rubric |
| G21 | Narrative Q5 requires human review, no score invented | rubric |
| G22 | Exact ledger accounting, opening versus turns | HTTP |
| G23 | Zero live; external connection refused | worker subprocess + HTTP |
| G24 | Unauthorized Live blocked before worker | controller |
| G25 | Transcript/state/API/diagnostics/hash-complete export | HTTP ZIP verification |
'''
    report('07_DETERMINISTIC_VALIDATION', '07 — Deterministic Validation', f'''
{table}

Completed selected scope: **{passed} passed / {failed} failed / zero errors or timeouts**.
G1–G25 and additional safeguards are covered by {results['gameplay']['passed']} passing tests.
G1 proves positive evaluator behavior, not an end-to-end successful five-turn run under
the six-request production limit. The real HTTP example completes four turns and stops
for budget. Do not promote fixture controls to live-quality or generalization claims.

{matrix}

Six failures match the pre-existing PR-PLAY-08 baseline: three rich-opening assertions,
one saved stew-price conversation assertion, and two stale source-attestation readiness
assertions. Exact names/text remain in JUnit/logs. Production sources and failing test
owners are unchanged in this pass; no unrelated repairs or threshold changes. No new
regression demonstrated in completed lanes. Initial restricted-localhost startup was
environment-blocked; deterministic lanes ran with localhost access, external provider
transport denied. Earlier instrument failures (oversized duplicated state export and
pytest's inherited interpretation-disable flags) were tooling defects corrected before
the final runs; they do not imply production defects.

Relevant lanes include prior harness, opening/diagnostics/budgets, structured/semantic,
world progression, conversation/ATGB interpretation, canonical noncombat rules,
state authority/persistence and evidence export. Commands/exits/timing are recorded in
regression_runs.json. This is no full-suite claim. No live benchmark or independent
held-out generalization was run. Entry-to-exit {len(before)} protected hashes match.
''')
    readiness = f'''
**B — Conditionally ready for a controlled six-request diagnostic; complete five-turn
execution is not guaranteed.** Do not label this A or claim live AI-DM competence.

Future exact command, only after external review and separate live authorization:

```powershell
{COMMAND}
```

Preflight: pinned fixture present/hash-verified; five authored inputs; fresh isolated
store and worker binding/ownership attestation; scenario/version/evidence paths saved;
capture mandatory; six-request/aggregate/inherited ceilings displayed and enforced;
SDK/host retry suppression attested; ordinary interpretation/expression flags required;
normal provider routing/output caps preserved; stop conditions and owned cleanup active.
Credentials are checked only for presence through normal configuration, never probed,
printed or included. Deterministic faults cannot be selected in Live mode.

Expected maximum live exposure: six provider dispatches, possibly fewer, no retries.
Normal interpretation and narration can use more than one dispatch per turn, so budget
may stop the script. Token/latency telemetry is recorded, not a fabricated dollar quote.
Exports: reports/result.json, reports/GAMEPLAY_REPORT.md, turn snapshots/diffs/native
diagnostics and evidence/evidence.zip with SHA-256 manifest. Browser remains NOT_TESTED.

Remaining limitations: no actual live five-turn transcript or human quality review;
full rules/disclosure/mutation authority beyond recorded native evidence is uncertain;
six inherited baseline regressions/source attestations remain. ATGB baseline/scores and
existing experimental integration restrictions remain unchanged. Review the feasibility
report before deciding whether a potentially partial six-request test is useful.
This command was not executed during this implementation pass.
'''
    report('08_LIVE_TEST_READINESS', '08 — Live-Test Readiness', readiness)
    (O/'live_execution_instructions.md').write_text(readiness.strip()+'\n', encoding='utf-8')
    final = report('09_FINAL_VERDICT_AND_HANDOFF', '09 — Final Verdict and Handoff', f'''
**B — Conditionally ready.** The scoped five-turn harness extension exists and its
{results['gameplay']['passed']} deterministic instrumentation checks pass. Relevant completed lanes:
{passed} passed / six pre-existing failures. No full live five-turn success established.
The real SDK-stubbed HTTP example exhausts six requests after four turns and safely
skips T5. Quality remains separately REQUIRES_HUMAN_REVIEW. The G1 positive evaluator
control is not evidence of end-to-end six-request feasibility. No production repair.

One recommended next action: external review of this completion package, including
the budget feasibility analysis. Do not execute a live test or expand budgets in this pass.
If separately authorized later, the exact six-request diagnostic command is:

```powershell
{COMMAND}
```

Maximum exposure six dispatches, zero retries, unchanged configured models/output
allowances and bounded aggregate tokens. It may stop before five turns; a larger scope
requires new explicit authorization. No unbounded player/judge or provider escalation.

Behavioral Evidence: example/result.json and GAMEPLAY_REPORT.md plus the complete
selected example store evidence identify four captured synthetic player turns, no live
turns. Representative infrastructure success: grounded nonmutating observation.
Representative concern: T2 clarification and T4 repeated response. These are synthetic
controls, not actual provider-performance findings; no human review or evaluator-policy
change, no observed human/evaluator disagreement, no independent generalization or
ATGB result. Rendered UI, actual meaningful five-turn play, and live adequacy remain unproven.

{CONFIRMATIONS}

Stop after generating the timestamped CURRENT_REVIEW ZIP. Await external review.
''')

    # Concise current-session orientation; older dirty content is retained verbatim.
    handoff = ROOT/'docs/NEXT_SESSION.md'
    original = (O/'entry_sources/docs/NEXT_SESSION.md').read_text(encoding='utf-8')
    intro = f'''## Latest gameplay tooling pass — PR-PLAY-09

2026-10-30: **B — Conditionally ready for a bounded six-request diagnostic.**
FiveTurnGameplay v1.0.0 extends tools/playtest and scripts/run_live_playtest.ps1:
opening prerequisite then five fixed intents through production /api/chat; sequential,
no retry, per-turn evidence/state/native validation/accounting and human-review rubric.
Normal-pipeline SDK-stubbed HTTP example uses six requests through four turns, then
skips T5. Complete five-turn execution within six is not guaranteed; no pipeline bypass.
G1 is evaluator-only positive control, not end-to-end feasibility. {results['gameplay']['passed']} new
instrumentation tests pass; relevant lanes {passed} passed/six matching pre-existing failures.
{len(before)} protected data/game/static/experiment hashes unchanged. No production repair,
live/provider-connectivity calls, model/output increase, retries, new gameplay structures,
PR-EG integration, frozen ATGB edit, secrets, commit or push. Prior dirty work preserved.
Quality, broader authority and actual live meaningful play remain unproven.

Nine reports: development/campaigns/product_realization/pr_play_09/.
Evidence and feasibility: artifacts/pr_play_09/. Guide: docs/AUTOMATED_PLAYTEST_GUIDE.md.
Review: handoff/CURRENT_REVIEW.md and timestamped ZIP. Recommended next action:
external review only; exact separately authorized six-request Live command is in
report 08. Stop after review ZIP; no next live action is authorized by this handoff.

'''
    handoff.write_text(original.replace('Updated 2026-10-29 / PR-PLAY-08.', 'Updated 2026-10-30 / PR-PLAY-09.').replace('## Latest tooling pass — PR-PLAY-08', intro+'## Latest tooling pass — PR-PLAY-08', 1), encoding='utf-8')

    diff_parts = []
    snapshots = []
    for name in SOURCES:
        source = ROOT/name
        old = O/'entry_sources'/name
        diff_parts.extend(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True) if old.exists() else [],
                           source.read_text(encoding='utf-8').splitlines(True), fromfile='entry/'+name, tofile='current/'+name))
        dest = O/'source_snapshots'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        snapshots.append(dest)
    (O/'source_diff.patch').write_text(''.join(diff_parts), encoding='utf-8')
    (O/'exit_status.txt').write_text(subprocess.run(['git', 'status', '--short'], cwd=ROOT, capture_output=True, text=True).stdout, encoding='utf-8')
    support = [*map(lambda n: ROOT/n, SOURCES), *snapshots, *sorted(R.glob('*.md')),
               *sorted(p for p in O.iterdir() if p.is_file() and p.suffix in {'.json', '.md', '.txt', '.patch', '.xml'} and p.name != 'review_config.json'),
               *sorted(target.glob('*')), *selected_example]
    support = list(dict.fromkeys(support))
    # Read configured secrets only in memory; never save environment or secret values.
    from dotenv import dotenv_values
    values = {**dotenv_values(ROOT/'.env'), **os.environ}
    secrets = [v.encode() for k,v in values.items() if isinstance(v, str) and len(v)>8
               and any(x in k.lower() for x in ('api_key', 'secret', 'password', 'credential'))]
    for p in support:
        assert not any(secret in p.read_bytes() for secret in secrets), 'Configured secret detected in selected review file'
    config = {
        'campaign_id': 'pr_play_09', 'campaign_name': 'PR-PLAY-09 — Automated Five-Turn Gameplay Smoke Test',
        'campaign_date': '2026-10-30', 'purpose': 'Offline bounded harness extension; stop before live execution.',
        'objective_status': 'B — Conditionally ready; six-request diagnostic may stop before five turns',
        'executive_summary': f'{results["gameplay"]["passed"]} gameplay instrument checks pass. {passed} passing checks and six matching pre-existing failures across relevant lanes. Synthetic HTTP example completes four turns within six requests; fifth skipped. No live calls or production changes.',
        'primary_report': final.relative_to(ROOT).as_posix(),
        'supporting_files': [{'path': p.relative_to(ROOT).as_posix(), 'role': 'source' if p in [ROOT/n for n in SOURCES] else 'evidence', 'why': 'Explicit PR-PLAY-09 source, report, provenance or deterministic evidence.'} for p in support],
        'changes': {'production': [], 'tooling': ['Existing runner/worker extended with bounded five-action scenario, native evidence evaluation and transcript export.'],
                    'validation': ['G1–G25 controls, coverage registry and bounded regression lanes.'],
                    'documentation': ['Nine reports, guide and current session handoff.'], 'generated_artifacts': ['Selected transcripts, JUnit/logs, source diff/status and protected hashes.']},
        'testing': {'focused': f'{results["gameplay"]["passed"]} gameplay and {results["harness"]["passed"]} prior harness/registry checks passed.',
                    'broader': f'{passed} passed / six matching pre-existing failures; no timeout or error.',
                    'full_suite': 'Not run.', 'runtime_validation': 'Owned localhost HTTP and production pipeline, synthetic SDK and external socket denial.',
                    'model_runtime_boundary': 'Zero live provider/connectivity operations.', 'new_regressions': 'None demonstrated in completed scope.',
                    'pre_existing_failures': 'Three rich-opening, one stew-price conversation and two stale source-attestation assertions.'},
        'decisions_requiring_human_review': ['External review of conditional readiness and six-request feasibility before any separately authorized Live invocation.'],
        'known_problems': {'campaign_specific': ['No end-to-end successful five-turn execution under six requests demonstrated; G1 is evaluator-only. Narrative quality and complete authority need human review.'],
                           'pre_existing': ['Six baseline failures; stale ATGB source attestations are not rewritten.']},
        'does_not_prove': ['Live meaningful five-turn play, rendered UI, conversational competence, independent generalization or ATGB performance.'],
        'recommended_next_step': 'External review only; do not execute the future Live command in this pass.',
        'self_contained_review_test': 'Nine reports, scenario/source/diff, G1–G25/JUnit/regression evidence, complete selected synthetic HTTP example, feasibility and future command.',
    }
    write(O/'review_config.json', config)
    build_handoff(config, archive_history=False)
    try:
        stamp = datetime.now(ZoneInfo('America/New_York')).strftime('%Y%m%d-%H%M%S')
    except ZoneInfoNotFoundError:
        # Stock Windows Python may have no IANA database. Use the Windows zone
        # database explicitly, independent of the host's selected local zone.
        stamp = subprocess.run(['powershell', '-NoProfile', '-Command',
            "[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMdd-HHmmss')"],
            check=True, capture_output=True, text=True, timeout=10).stdout.strip()
    archive = ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
    shutil.copy2(ROOT/'handoff/CURRENT_REVIEW.zip', archive)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():
            assert not any(secret in z.read(name) for secret in secrets), 'Configured secret detected in review archive'
        for p in sorted(R.glob('*.md')):
            assert any(name.endswith(p.relative_to(ROOT).as_posix()) for name in z.namelist())
    print(json.dumps({'review_zip': str(archive), 'bytes': archive.stat().st_size, 'tests_passed': passed,
                      'preexisting_failures': failed, 'protected_files': len(before), 'protected_unchanged': True,
                      'live_calls': 0, 'verdict': 'B — Conditionally ready'}, indent=2))


if __name__ == '__main__':
    main()
