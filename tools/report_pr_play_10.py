"""Explicit offline PR-PLAY-10 evidence and standard review export. No gameplay."""
import ast
from datetime import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools.build_review_handoff import build_handoff
from tools.playtest.analysis import compare
from tools.playtest.overlays import payload
from tools.validate_pr_play_09 import protected_hashes

ROOT = Path(__file__).resolve().parents[1]
O = ROOT/'artifacts/pr_play_10'
R = ROOT/'development/campaigns/product_realization/pr_play_10'
H = O/'historical'
COMMAND = r'.\scripts\run_live_playtest.ps1 -Scenario FiveTurnGameplay -Mode Live -AuthorizeLiveProvider -CaptureResponse'
SOURCES = ['tools/playtest/overlays.py', 'tools/playtest/analysis.py', 'tools/playtest/runner.py',
           'tools/playtest/gameplay.py', 'tools/playtest/worker.py', 'tests/test_pr_play_10_overlays.py',
           'tests/fixtures/pr_play_10/historical_opening.json', 'tests/validation_coverage_registry.py',
           'tools/validate_pr_play_10.py', 'tools/report_pr_play_10.py',
           'docs/AUTOMATED_PLAYTEST_GUIDE.md', 'docs/NEXT_SESSION.md']
CONFIRM = '''
- No live provider calls.
- No provider connectivity diagnostics.
- No model changes.
- No output-budget increases.
- No automatic retries.
- No unrelated gameplay changes.
- No unauthorized gameplay-state mutations; runtime test mutations stayed in disposable isolated fixtures.
- No new persistent gameplay structures.
- No experimental PR-EG integration.
- Frozen ATGB baseline unchanged.
- No secrets included; explicit file selection and configured-secret byte scan.
- No commit or push performed.
'''.strip()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')


def report(name, title, body):
    p = R/(name+'.md')
    p.write_text('# '+title+'\n\nPR-PLAY-10 · 2026-10-30 America/New_York · evidence_scope: structural_only.\n\n'+body.strip()+'\n', encoding='utf-8')


def main():
    R.mkdir(parents=True, exist_ok=True)
    runs = json.loads((O/'regression_runs.json').read_text())
    results = {}
    for p in O.glob('*_regression.xml'):
        suite = next(ET.parse(p).getroot().iter('testsuite'))
        counts = {k: int(suite.get(k, 0)) for k in ('tests', 'failures', 'errors', 'skipped')}
        counts['passed'] = counts['tests']-counts['failures']-counts['errors']-counts['skipped']
        counts['failure_cases'] = [c.get('classname')+'::'+c.get('name') for c in suite if c.find('failure') is not None]
        results[p.stem.removesuffix('_regression')] = counts
    assert all(not r['timeout'] for r in runs.values())
    assert all(results[k]['failures'] == results[k]['errors'] == 0 for k in ('overlay', 'diagnostics', 'harness', 'gameplay', 'hidden_faction'))
    write(O/'test_summary.json', results)
    passed, failed = (sum(r[k] for r in results.values()) for k in ('passed', 'failures'))
    a = json.loads((H/'baseline/documents.json').read_text())
    b = json.loads((H/'opening/documents.json').read_text())
    historical = json.loads((H/'reports/result.json').read_text())
    body = next(s['response'] for s in historical['steps'] if s['action'] == 'start_campaign')
    capture = json.loads(next((H/'opening_response_evidence').glob('*.json')).read_text())
    classification = compare(a, b, accepted=True, opening_response=body)
    assert classification['integrity']
    write(O/'historical_reclassified.json', classification)
    old, new = (payload(d['session.json'])['runtime_scene_overlays'] for d in (a, b))
    sid = payload(a['session.json'])['active_scene_id']
    exact = []
    for index, text in enumerate(new[sid]['visible_facts_add']):
        seed = next(i for i, v in enumerate(a['scenes/'+sid+'.json']['scene']['opening_seed_facts'])
                    if v.casefold().removesuffix('.') == text.casefold().removesuffix('.'))
        exact.append(dict(path=f'session.json:/runtime_scene_overlays/{sid}/visible_facts_add/{index}',
                          previous_value=None, previous_present=False, new_value=text, change_type='added',
                          scene_id=sid, overlay_id=sid, related_opening_declaration=f'parsed_response.scene_update.visible_facts_add.{index}',
                          provenance=f'authored scene.opening_seed_facts.{seed}; captured structured scene_update; native adoption trace',
                          authorization='authorized authored fact projection; narration alone is not evidence'))
    for key, val in new[sid]['mutations'].items():
        exact.append(dict(path=f'session.json:/runtime_scene_overlays/{sid}/mutations/{key}',
                          previous_value=None, previous_present=False, new_value=val, change_type='added',
                          scene_id=sid, overlay_id=sid, related_opening_declaration='parsed_response.scene_update.'+key,
                          provenance='legacy typed scene-update effect; authored scene.mode' if key == 'mode' else 'legacy typed effect empty-list initialization',
                          authorization='authorized existing mode / empty layer initialization'))
    write(O/'exact_historical_overlay_diff.json', dict(before=old, after=new, changed_entries=exact,
        root_existed=True, root_type_before='object', root_type_after='object', removed_entries=[],
        unrelated_overlays_unchanged=all(old[k] == new[k] for k in old if k != sid),
        declaration_caution='scene_update is the structured mutation proposal. declared_claims are realization claims, not a blanket persistence grant.'))
    write(O/'example_improved_state_difference.json', classification['overlay_comparison'])
    matrix = [json.loads((O/('O'+str(i)+'.json')).read_text()) for i in range(1, 16)]
    assert all(row['passed'] for row in matrix)
    for row in matrix:
        if row['case'] == 'O11': row['additional_runtime_evidence'] = 'failed_overlay_rollback.json; diagnostics_regression.xml'
        if row['case'] == 'O12': row['additional_runtime_evidence'] = 'replay.json (repeat 409 checked); diagnostics_regression.xml'
        if row['case'] == 'O13': row['additional_runtime_evidence'] = 'concurrent_overlay.json (200/409, one SDK stub request)'
    write(O/'overlay_authority_matrix.json', matrix)
    replay = json.loads((O/'replay.json').read_text())
    assert replay['historical_overlay_before_equal'] and replay['historical_overlay_after_equal'] and replay['comparison']['integrity']
    http = json.loads((O/'http_run.json').read_text())
    run = ROOT/http['run']
    hr = json.loads((run/'reports/result.json').read_text())
    assert hr['opening_state_comparison']['integrity'] and hr['attempted_turns'] > 0
    assert hr['provider_exposure']['live_calls'] == 0
    target = O/'http_evidence'
    for folder in ('configuration', 'baseline', 'opening', 'after', 'diagnostics', 'reports', 'turns', 'evidence'):
        for p in (run/folder).rglob('*'):
            if p.is_file():
                q = target/p.relative_to(run); q.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, q)
    write(O/'http_summary.json', dict(run=http['run'], opening_integrity=hr['opening_state_comparison']['integrity'],
          attempted_turns=hr['attempted_turns'], completed_turns=hr['completed_turns'], stop_reason=hr['stop_reason'],
          dispatched=hr['provider_usage']['dispatched_requests'], live_calls=hr['provider_exposure']['live_calls']))

    source_map = []
    modules = {
        'game/storage.py': ['get_runtime_scene_overlay', '_default_runtime_scene_overlay', '_ensure_runtime_scene_overlay_shape',
             'get_scene_runtime', 'build_effective_scene', 'get_effective_scene', 'save_session', '_validate_runtime_coherency_structural'],
        'game/api.py': ['_apply_post_gm_updates', '_validate_gm_scene_update_for_legacy_adoption', '_post_gm_adoption_gateway',
             '_record_post_gm_mutation_trace', '_opening_response_rejection', '_capture_opening_baseline',
             '_restore_opening_baseline', '_OpeningScope', '_start_campaign_after_admission', '_complete_chat_turn_after_gm',
             '_complete_opening_turn_persistence_like_chat', 'new_campaign'],
        'game/campaign_state.py': ['default_session'],
        'game/gm.py': ['call_gpt'],
        'game/response_policy_enforcement.py': ['apply_response_policy_enforcement'],
    }
    for module, names in modules.items():
        tree = ast.parse((ROOT/module).read_text(encoding='utf-8'))
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names:
                source_map.append(dict(module=module, function=n.name, line=n.lineno,
                                       input_output_contract=ast.get_docstring(n) or 'See source signature and report 03.'))
    write(O/'production_source_map.json', source_map)
    table = '\n'.join('| '+k+' | '+str(v['passed'])+' | '+str(v['failures'])+' | '+str(v['errors'])+' |' for k, v in results.items())
    report('01_BASELINE_AND_HISTORICAL_EVIDENCE', '01 — Baseline and Historical Evidence', f'''
Revision `{(O/'revision.txt').read_text().strip()}`. Entry was extensively dirty:
production sources, ordinary saves, documentation, prior artifacts and untracked harness work.
`entry_status.txt` preserves the exact inventory; `entry_sources/` isolates this pass's delta.
No reset, checkout, commit or push. Standing authorities reviewed: Constitution, NEXT_SESSION,
validation evidence and Product Realization validation standards, state authority model,
PR-AA portfolio, review-handoff standard, ATGB fixture README, and PR-PLAY-04/06/07/08/09 reports.
No dedicated overlay doctrine was located; executable storage/adoption owners and their tests
supply the specific contract. Runtime progress is session-owned; canon is immutable.

The requested evidence(1).zip attachment was unavailable. The exact matching local run is
`artifacts/atgb/automated_playtests/20261030T191257Z-ecc1b6062bdc`.
Its preserved snapshots, capture, result and ledger are under `historical/`, with SHA-256 provenance.
It records 1 completed request, 26593 input / 1655 output tokens, successful parser/semantic
validation, accepted opening and committed initialization, then overlay integrity failure;
0 player turns attempted. This is distinct from the older 1724-output opening summarized
by PR-PLAY-09; that older run was not substituted for this failure.

Existing tests identified: storage save/load, world updates/clue normalization, post-GM adoption
gateway, state authority, opening integrity/budget/semantic acceptance, automated playtest and
five-turn gameplay. Detailed selection/commands: regression_runs.json and test_summary.json.
''')
    report('02_EXACT_OVERLAY_MUTATION', '02 — Exact Overlay Mutation', '''
`exact_historical_overlay_diff.json` is the exact structured before/after comparison, including
every added list item and mutation key, prior presence/value, provenance and authorization.
The field existed as an object. Three scene overlays existed before and after. Only frontier_gate
changed: five visible_facts_add strings appended to an empty list; mutations gained empty
discoverable_clues_add / hidden_facts_add lists and mode="social". Nothing was removed.
market_quarter and old_milestone remained byte-value identical. No runtime entity, discovered clue,
or state flag changed. Overlay identifier is the scene key; there is no separate overlay UUID.

All five strings match authored opening_seed_facts after case / terminal full-stop normalization:
rain/banners, noble townhouse, still threadbare figure, congested approach, notice board.
They describe locations, objects and observable scene facts; they create no NPC identity.
Mode equals authored scene.mode. The complete provider parsed_response explicitly contains
these exact scene_update strings and mode. This is not inference from narration: the still
figure detail has no exact corresponding sentence in the delivered narration. Several declared
realization claims cover rain/crowd/board, but no one-to-one declaration ID grants persistence
for every overlay string. Authored public seed content plus structured update plus native
adoption and accepted commit establish this particular mutation's authority.

Chain: captured parsed_response.scene_update → parser GM scene_update → policy cleanup →
typed legacy shape validation → native authoritative_adopted trace → overlay append →
opening acceptance → session save → committed opening_outcome → harness false positive.
Raw wire bytes were not captured: replay reproduces the exact captured parsed JSON value,
not an asserted byte-for-byte original network response. Capture reports truncated=false.
''')
    report('03_PRODUCTION_OVERLAY_AUTHORITY', '03 — Production Overlay Authority', '''
`production_source_map.json` provides modules/functions/verified line numbers and contracts.

| Operation | Owner / contract | Persistence and tests |
| --- | --- | --- |
| Create / shape | storage.get_runtime_scene_overlay(session, scene_id) returns mutable default overlay | Lazy in-memory root; saved with session; save_load / post_gm tests |
| Read | storage.get_effective_scene → build_effective_scene(canon, overlay) returns merged copy | Canon unchanged; runtime reader may create default shape |
| Runtime clues | storage.get_scene_runtime merges legacy discovered clues into overlay | Session-owned; world_updates_and_clue_normalization |
| Declaration / shape validation | gm.call_gpt parses structured envelope; immutable_valid_response validates candidate; response_policy_enforcement filters exact hidden-fact promotion | No narration-only persistence authority; structured / semantic suites |
| Apply | api._validate_gm_scene_update_for_legacy_adoption returns PostGmSceneUpdateEffect; _apply_post_gm_updates appends visible/discoverable/hidden layers and mode | Engine/API owns application; post_gm_adoption_gateway |
| Persist | storage.save_session and runtime coherency guard | Session envelope; save/load and persistence tests |
| Clear | new_campaign resets runtime using default session | No general arbitrary overlay deletion authority; campaign initialization tests |
| Failure restore | _OpeningScope captures session/world/combat/log and restores uncommitted attempt | Existing process lock serializes starts; PR-PLAY-04 + new rollback/concurrency tests |

Purpose: scene-scoped playthrough additions without editing authored templates. Reads can create
empty shape. Structured scene_update can append overlays during opening or ordinary processing;
ordinary prose alone is not a scene_update. The gateway is transitional: shape enforcement is
active, semantic policy enforcement is observe_only. It does not prove arbitrary proposed facts
are authorized. Declarations do not authorize themselves. Canonical scene templates remain
unchanged, though runtime mode/layers can affect effective views under existing owners.
Hidden layers remain distinct; exact hidden-to-visible promotion is filtered by response policy.
This pass does not claim that filtering proves all paraphrased disclosures impossible.

Instrumentation in replay.json shows in-memory overlay application BEFORE the final opening
acceptance check, then save_session after acceptance. _OpeningScope restores failed attempts,
including a forced save failure after real overlay application (failed_overlay_rollback.json).
This is not a new transaction implementation or a crash-atomicity claim. Repeated Start and
concurrent starts use the existing single-process lock/started gate; no duplicate commits.
Persistent facts require structured/engine authority. Plain sensory presentation can remain
text-only. No new rule promoting prose to world facts was introduced.
''')
    report('04_HARNESS_STATE_COMPARISON_ANALYSIS', '04 — Harness State-Comparison Analysis', '''
Previously analysis.compare unwrapped snapshots, removed documented envelope/trace bookkeeping,
and compared fixed allowed session/world field names. runtime_scene_overlays was absent.
It distinguished accepted from rejected openings and required one turn/log increment, but did
not inspect overlay entries, declarations, scene ownership, additions/removals or native adoption.
Thus any changed overlay was unexpected, including authorized authored opening projection.
runner stopped before T1 when opening_state_comparison.integrity became false.

Now compare accepts the actual opening response as supporting evidence and delegates overlay
analysis to tools.playtest.overlays. The response session mirror is not the source of truth:
original persistent snapshots and pinned scene content are compared. Required support includes
hard validation, native accepted authority, scene_opening resolution, active scene consistency,
new persisted adoption receipt, proposal counts/mode and exact expected projection. Empty
active-scene initialization can be recognized separately. Other overlays must be unchanged.
No unconditional field allowance. Unknown / missing evidence stays a stop condition.

Ordinary-turn evaluation also emits overlay-specific comparison and stops on changed overlays
whose authority has not been established. Unchanged valid overlays persist. We do not infer
ordinary-turn mutation authority from a successful HTTP response or a shape-only receipt.
Diagnostics retain bounded values, omission counts/hashes, scene IDs, classifications and reasons;
raw snapshots remain preserved. example_improved_state_difference.json is an actual example.
''')
    report('05_ROOT_CAUSE_AND_IMPLEMENTATION', '05 — Root Cause and Implementation', '''
Classification A — Harness false positive; development failure class: evaluation.
Earliest demonstrated error: treating the changed overlay field name as inherently unexpected
without checking its authorized contents. Historical strings are already-authored public opening
facts; mode repeats authored social mode; the native structured-update adoption and accepted
commit are preserved. Both fresh production replay and historical reclassification pass.

Changes are limited to the harness: overlays.py performs conservative evidence reconciliation;
analysis.py integrates it; runner.py supplies the opening response; gameplay.py checks later
overlay differences; worker.py adds a deterministic captured-response fixture. Tests cover
historical replay, adversarial mutations, rollback and concurrent commits; coverage registry,
guide, validation/report tools and handoff were updated. Source diff is incremental from saved
dirty entry bytes; source snapshots are included. No production game module was changed.

Rejected alternatives: whole-field allowlist; trusting narration; trusting an observe-only gateway
as semantic authority; removing declaration/semantic validation; changing prompts/model/budgets;
adding retries; suppressing integrity failures; changing the five player actions. Non-authored
facts remain unresolved rather than acquiring new authority. Historical canon repetition is
sufficiently evidenced without adjudicating the legacy gateway's entire future semantic policy.
''')
    matrix_table = '\n'.join('| '+row['case']+' | '+str(row['expected_integrity'])+' | '+str(row['actual']['integrity'])+' | PASS |' for row in matrix)
    report('06_OVERLAY_AUTHORITY_MATRIX', '06 — Overlay Authority Matrix', '''
All O1–O15 passed their explicit comparison expectations. Machine-readable records contain
fixture, operation, expected result, actual changed values, reasons/evidence and pass/fail.
O1 active authored addition allowed; O2 rejected opening leak flagged; O3 no structured update
flagged; O4 extra existing mutation flagged; O5 removal flagged; O6 wrong-scene addition flagged;
O7 contradiction flagged; O8 protected fact flagged; O9 undocumented metadata flagged (no
overlay bookkeeping exclusion exists); O10 unchanged subsequent state preserved; O11 failed
opening unchanged; O12 repeated start unchanged; O13 concurrent commit once; O14 unrelated
overlays preserved; O15 malformed root flagged. O7/O8 are harness negative controls, not claims
that the legacy shape-only gateway independently rejects every semantic violation.

The table's O12/O13 comparison controls are supplemented by real endpoint evidence: replay
checks repeat 409 with no second SDK stub request; concurrent_overlay.json records 200/409,
one SDK stub request and exactly the historical final overlays. O11 has a real save-failure
rollback control. Missing-root active initialization and unrelated observatory vocabulary have
additional focused coverage. Malformed changed roots fail explicitly; unchanged malformed
state is not a substitute for the production persistence-coherency validation lane.

| Case | Expected integrity | Actual integrity | Result |
| --- | --- | --- | --- |
'''+matrix_table)
    report('07_DETERMINISTIC_REPLAY_AND_REGRESSION', '07 — Deterministic Replay and Regression', f'''
Original reproduction: replay.json executes the exact captured parsed response through the
production parser, semantic validation, acceptance and normal persistence with synthetic SDK
transport. No direct runtime-state injection. Only isolated authored scene fixture content is
prepared before the operation. Historical/replayed before overlays and after overlays compare
equal. Whole documents are not claimed byte-identical: fresh run IDs, clocks and diagnostic
timestamps differ. Instrumentation observes rather than replaces decisions. One SDK stub call.

Runtime HTTP reproduction: http_evidence/ preserves the full owned isolated FiveTurnGameplay
run. Opening integrity true, T1 executed, {hr['attempted_turns']} turns attempted /
{hr['completed_turns']} completed; stop={hr['stop_reason']}, six synthetic dispatches, zero live.
T5 is safely skipped at the original request ceiling. This is progression beyond opening,
not proof of all five turns fitting six requests or of narrative quality. The first sandboxed
HTTP attempt was environment-blocked; localhost-enabled rerun traversed normal production HTTP.
The sandboxed broad run was interrupted while blocked; final lane records supersede it.

Final completed regression: {passed} passed / {failed} failures across selected lanes.
Counts are test executions, including intentional overlap, not a unique-test claim.

| Lane | Passed | Failed | Errors |
| --- | --- | --- | --- |
{table}

Commands, time bounds and exits: regression_runs.json. JUnit and text output accompany every
lane. PR-PLAY-04/06/07 cover valid/invalid/nonresolution openings, retry eligibility, one-time
progression, repeat/concurrency, validation/budget/capture. Harness covers state classification,
stop behavior, accounting, continuation, scenarios and hashed evidence export. Overlay suites
cover gateway effects, save/load, hidden layering and runtime state. World/rules lanes cover
deterministic and faction progression. Frozen ATGB infrastructure is tested without running
a live benchmark or changing baseline attestations.

Known failures are compared by exact test ID against the preserved PR-PLAY-09 JUnit baseline
in failure_classification.json. No unrelated repairs. No full-suite, live quality, human review,
held-out generalization, rendered browser or ATGB score claim. Protected hashes cover ordinary
data, game/static and experiments: entry_to_exit_integrity.json.
''')
    readiness = f'''
**B — Conditionally ready for external review of the bounded diagnostic.** Historical mutation
classified and reconciled; deterministic replay and opening continuation pass. No demonstrated
new relevant regression remains. Existing six-request feasibility limit remains: a complete
five-turn run is not guaranteed. The comparator deliberately stops on any new overlay effect
outside its proven authored opening projection. Broader legacy semantic authority is not
silently accepted. These are explicit limitations, not reasons to spend more requests.

Future command, only after external review and separate live authorization:

```powershell
{COMMAND}
```

Do not execute it in PR-PLAY-10. Fresh unique isolated store; existing frontier-gate-v1 fixture;
unchanged configured provider/model and opening output allowance (normally 3000; ordinary 600);
six request ceiling / input 200000 / output 20000 / total 220000 or stricter inherited limits;
SDK and host retries zero; provider diagnostics and bounded response capture on; per-turn
snapshots, overlay-specific diagnostics and stop-on-integrity-failure on; automatic evidence
export on. The same five player actions are retained. No connectivity probe is needed or
authorized by this package. A blocked or partial run must retain its evidence, without retry.
'''
    report('08_LIVE_TEST_READINESS', '08 — Live-Test Readiness', readiness)
    (O/'live_test_instructions.md').write_text(readiness, encoding='utf-8')
    report('09_FINAL_VERDICT_AND_HANDOFF', '09 — Final Verdict and Handoff', f'''
**B — Conditionally ready.** Classification A: harness false positive for the exact historical
authored scene_update. Exact overlay diff, native receipt and unchanged parsed-response replay
support the decision. No production gameplay changes. The harness accepts the proven projection
and continues to T1; unsupported mutations still stop. {passed} passing regression executions;
{failed} inherited failures are recorded separately. Review failure_classification.json for exact IDs.

Remaining risk: six requests may stop before five turns; unsupported future overlay authority
fails closed; legacy adoption is shape-enforced/semantic observe-only; no broad semantic quality
or crash-atomicity claim. Existing source-attestation failures are not rewritten. The complete
live five-turn result remains unproven. Live execution is NOT authorized during this pass.

One recommended next action: external review of this package. Do not execute a live test.

{CONFIRM}

Stop after generating the review ZIP. Await external review before another live five-turn playtest.
''')

    prior = json.loads((ROOT/'artifacts/pr_play_09/test_summary.json').read_text())
    prior_ids = {n for v in prior.values() for n in v.get('failures_observed', [])}
    failures = [dict(lane=k, test=n, classification='preexisting_defect' if n in prior_ids else 'unresolved')
                for k, v in results.items() for n in v['failure_cases']]
    write(O/'failure_classification.json', dict(failures=failures, new_regressions=[],
         environment_blocked=['Initial sandbox HTTP run / interrupted sandbox regression; successful localhost-enabled rerun'],
         evidence='Exact test IDs compared with artifacts/pr_play_09/test_summary.json; unchanged owners and prior JUnit preserved.'))
    assert all(f['classification'] == 'preexisting_defect' for f in failures), failures
    entry = json.loads((O/'protected_before.json').read_text())
    after = protected_hashes()
    integrity = dict(files=len(entry), unchanged=entry == after,
                     changed=[k for k in entry if entry[k] != after.get(k)], added=sorted(set(after)-set(entry)))
    write(O/'entry_to_exit_integrity.json', integrity)
    assert integrity['unchanged']
    (O/'exit_status.txt').write_text(subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True), encoding='utf-8')
    diff = []
    for name in SOURCES:
        p = ROOT/name
        q = O/'source_snapshots'/name; q.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, q)
        base = O/'entry_sources'/name
        diff.extend(difflib.unified_diff(base.read_text(encoding='utf-8').splitlines(True) if base.exists() else [],
                                      p.read_text(encoding='utf-8').splitlines(True),
                                      fromfile='entry/'+name if base.exists() else '/dev/null', tofile='exit/'+name))
    (O/'source_diff.patch').write_text(''.join(diff), encoding='utf-8')
    selected = [ROOT/s for s in SOURCES] + list(R.glob('*.md')) + [p for p in O.rglob('*')
                if p.is_file() and p.name != 'review_config.json' and 'entry_sources' not in p.parts
                and p.name != 'worker_after_temp.py']
    # No environment dumps or credential files are selected. Check configured
    # secrets in memory without emitting their values.
    from dotenv import dotenv_values
    secrets = [v.encode() for k, v in {**dotenv_values(ROOT/'.env'), **os.environ}.items()
               if any(t in k.upper() for t in ('API_KEY', 'SECRET', 'PASSWORD', 'ACCESS_TOKEN'))
               and isinstance(v, str) and len(v) >= 8 and v != 'offline-placeholder']
    assert not any(secret in p.read_bytes() for p in selected for secret in secrets), 'Configured secret in selected evidence'
    config = dict(campaign_id='pr_play_10', campaign_name='PR-PLAY-10 — Runtime Scene Overlay State-Authority Reconciliation',
       campaign_date='2026-10-30', purpose='Offline evidence-driven bounded harness repair',
       objective_status='B — Conditionally ready; external review only',
       executive_summary=f'Historical harness false positive reconciled; exact parsed response replay passes. {passed} passing checks; {failed} preexisting failures. No live calls.',
       primary_report=str((R/'09_FINAL_VERDICT_AND_HANDOFF.md').relative_to(ROOT)).replace('\\', '/'),
       supporting_files=[dict(path=str(p.relative_to(ROOT)).replace('\\', '/'), role='evidence',
                              why='Explicit PR-PLAY-10 source, report or deterministic evidence') for p in sorted(set(selected))],
       changes=dict(production=[], tooling=['Exact evidence-gated overlay comparison and bounded diagnostics'],
                    validation=['O1–O15, historical production replay, rollback/concurrency and regression lanes'],
                    documentation=['Nine reports, guide and session handoff']),
       testing=dict(focused='Overlay and opening/harness controls pass', broader=f'{passed} passed; {failed} inherited failures',
                    full_suite='Not run', runtime_validation='Production API and owned HTTP with SDK stub',
                    model_runtime_boundary='Zero live provider or connectivity operations', new_regressions='None demonstrated',
                    pre_existing_failures='Exact preserved baseline IDs in failure_classification.json'),
       decisions_requiring_human_review=['External review before any separately authorized live command'],
       known_problems=dict(campaign_specific=['Six-request limit can skip T5; unsupported overlay authority remains a stop condition'],
                           pre_existing=['Stale source attestations and existing opening/conversation test failures']),
       does_not_prove=['Live play quality, all five turns within six requests, general semantic authority, ATGB scores'],
       recommended_next_step='External review only; do not execute live test',
       deferred_work=['Broader legacy semantic policy and larger-budget feasibility are not authorized'],
       validation_evidence=dict(evidence_scope='structural_only'))
    write(O/'review_config.json', config)
    bundle = build_handoff(config, root=ROOT)
    try:
        stamp = datetime.now(ZoneInfo('America/New_York')).strftime('%Y%m%d-%H%M%S')
    except ZoneInfoNotFoundError:
        stamp = subprocess.run(['powershell', '-NoProfile', '-Command',
            "[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMdd-HHmmss')"],
            check=True, capture_output=True, text=True, timeout=10).stdout.strip()
    dest = ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
    shutil.copy2(ROOT/'handoff/CURRENT_REVIEW.zip', dest)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        assert all(any(n.endswith(p.relative_to(ROOT).as_posix()) for n in z.namelist()) for p in R.glob('*.md'))
        assert not any(secret in z.read(n) for n in z.namelist() if not n.endswith('/') for secret in secrets)
    print(dest)


if __name__ == '__main__':
    main()
