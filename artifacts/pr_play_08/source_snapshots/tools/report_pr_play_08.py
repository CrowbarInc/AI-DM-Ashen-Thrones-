"""Generate the PR-PLAY-08 offline review using the established handoff exporter."""
from __future__ import annotations

import difflib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.build_review_handoff import build_handoff
from tools.playtest.runner import OUTPUT, ROOT, summarize

O = ROOT/'artifacts/pr_play_08'
R = ROOT/'development/campaigns/product_realization/pr_play_08'


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')


def report(name, title, content):
    (R/name).write_text('# '+title+'\n\nPR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.\n\n'+content.strip()+'\n', encoding='utf-8')


def main():
    O.mkdir(parents=True, exist_ok=True)
    R.mkdir(parents=True, exist_ok=True)
    results = {}
    for p in sorted(O.glob('*_regression.xml')):
        suite = next(ET.parse(p).getroot().iter('testsuite'))
        counts = {k: int(suite.get(k, '0')) for k in ('tests', 'failures', 'errors', 'skipped')}
        counts['passed'] = counts['tests']-counts['failures']-counts['errors']-counts['skipped']
        counts['seconds'] = suite.get('time')
        counts['failures_observed'] = [c.get('classname')+'::'+c.get('name') for c in suite if c.find('failure') is not None]
        results[p.stem.removesuffix('_regression')] = counts
    assert results['harness']['failures'] == results['harness']['errors'] == 0
    passed = sum(v['passed'] for v in results.values())
    failed = sum(v['failures'] for v in results.values())
    write(O/'test_summary.json', results)
    matrix = json.loads((O/'matrix_runs.json').read_text(encoding='utf-8'))
    success = Path(matrix['success']['run'])
    assert matrix['success']['result']['verdict'] == 'PASS'
    integrity = json.loads((O/'protected_integrity.json').read_text(encoding='utf-8'))
    assert integrity['unchanged']

    # Explicit inventory; no traversal of historical campaigns or private saves.
    inventory = [
        ('Campaign isolation', 'tools/atgb/isolation.py; game/storage.py', 'Yes', 'Compose fresh-store marker, path guard and imported DATA_DIR attestation'),
        ('Baseline fixture', 'tools/atgb/baseline.py; data/validation/atgb/baselines/frontier-gate-v1', 'Yes', 'Pinned manifest/copy verification reused unchanged'),
        ('API contracts', 'game/api.py; tests/helpers/turn_pipeline_http_fixtures.py', 'Yes', 'HTTP controller automates New/State/Start/State; no direct gameplay bypass'),
        ('Provider stubbing', 'tests/test_pr_play_04_opening_integrity.py; tests/test_pr_play_05_diagnostics.py', 'Pattern', 'Standalone worker applies equivalent SDK-only fixtures without importing pytest or test modules'),
        ('Provider admission', 'game/provider_budget.py', 'Yes', 'One-request ceiling composed; no second provider client'),
        ('Usage accounting', 'game/provider_budget.py; tools/atgb/accounting.py', 'Yes', 'Reuse native snapshot and durable-ledger reconciliation'),
        ('Generation diagnostics', 'game/gm.py; game/provider_budget.py', 'Yes', 'Observe existing parser/provider/outcome stages'),
        ('Semantic provenance', 'game/provider_budget.py; game/immutable_valid_response.py', 'Yes', 'Native reasons/sources correlated without rerunning validators'),
        ('Bounded response capture', 'game/provider_budget.py capture_opening_response', 'Yes', 'Opt-in controlled isolated capture copied into selected evidence'),
        ('State snapshots', 'game/storage.py; tools/atgb/chat_worker.py', 'Pattern', 'API projection plus copied persistent files; no new runtime save schema'),
        ('State comparison', 'tests/test_pr_play_05_diagnostics.py; docs/state_authority_model.md', 'Pattern', 'Conservative diagnostic comparator for opening commit/rollback and explicit bookkeeping'),
        ('Reporting', 'tools/atgb/results.py; tools/validation_evidence.py; tools/build_review_handoff.py', 'Yes', 'Diagnostic result/summary compose evidence; existing exporter produces central review'),
        ('Evidence export', 'tools/build_review_handoff.py; tools/report_pr_play_07.py', 'Yes', 'Selected-file manifest/ZIP added per run; exporter reused for review'),
        ('Browser testing', 'requirements.txt; tests/README_TESTS.md; existing Node handler tests', 'Partial', 'No registered browser automation or Playwright/Selenium dependency; adapter contract, UI NOT_TESTED'),
        ('Process management', 'tools/atgb/driver.py; tools/validate_pr_play_06.py', 'Pattern', 'Owned real interpreter PID, socket binding/readiness/deadlines and finally cleanup'),
        ('ATGB execution', 'tools/run_atgb.py; tools/atgb/driver.py; tools/atgb/chat_worker.py', 'Yes', 'Reuse fixture/isolation/accounting/revision helpers; opening harness does not alter benchmark driver or score'),
    ]
    table = '| Capability | Existing implementation | Reusable? | Gap / integration |\n|---|---|---|---|\n'+''.join('| '+' | '.join(row)+' |\n' for row in inventory)
    report('01_EXISTING_INFRASTRUCTURE_INVENTORY.md', 'Existing Infrastructure Inventory', f'''
Baseline HEAD: `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`. Extensive dirty production,
canonical play data, tests, documentation and generated evidence predate this pass.
No baseline reset, commit, or push. Entry orientation: development constitution,
NEXT_SESSION, validation evidence/product realization standards, testing guides,
PR-AA portfolio/roadmap, review standard, state authority, PR-PLAY-02–07 and ATGB
implementation. PR-PLAY-08 explicitly authorizes tooling, not gameplay repairs.

{table}

No second gameplay engine, semantic interpreter, behavioral evaluator, or test
framework was introduced. Pytest owns harness checks; game code owns outcomes.
''')
    report('02_HARNESS_ARCHITECTURE.md', 'Harness Architecture', '''
`scripts/run_live_playtest.ps1` resolves repository/interpreter and forwards flags.
`tools/playtest/runner.py` validates scenario/configuration, prepares a fresh store,
starts an owned server process, drives HTTP, collects snapshots, classifies and
exports. `worker.py` binds its socket, attests DATA_DIR/PID, configures transport,
and serves the existing ASGI application. `analysis.py` compares observations and
classifies stages. `browser.py` defines a future rendered-UI adapter. JSON scenario
definitions follow existing repository JSON conventions.

Scenario contracts contain ID/version/description/fixture/modes/actions/invariants,
action and request ceilings, input/output/total budgets, six stage timeouts,
evidence requirements and stop conditions. Unknown actions, unpinned fixtures,
repeated New/Start, expanded established limits and unbounded timeouts are refused.
Bundled scenarios are selected by name; arbitrary external code is not loaded.

Deterministic is default: synthetic SDK Responses transport, external socket
connect/connect_ex denied, real production admission and validation. Live is
explicitly flagged, opening-only, single-admission, no retries. ScriptedGameplay
is deterministic only. A failed step stops further player actions; final evidence
capture is permitted and never invokes another opening/provider request.

Ownership justification: the existing ATGB driver owns benchmark conversations,
partitions, score worksheets and chat turns. It does not expose a bounded owned
Uvicorn lifecycle or one-opening HTTP diagnostic transaction. Extending it with
these unrelated semantics would change its frozen benchmark contract. This small
controller composes its existing fixture/isolation/accounting/revision helpers
and leaves benchmark authority unchanged. Production API and provider owners are
unchanged. No new persistent gameplay structure is introduced.

Isolation root is `artifacts/atgb/automated_playtests/`, fitting the existing ATGB
safe-path guard. Unique UTC+UUID directories never reuse prior stores. Environment
changes stay in the worker; PowerShell restores PYTHONPATH. A Windows venv redirector
is avoided when launching the worker so the attested PID is the owned server PID.
Readiness uses safe GET state polling only after socket binding and isolation
attestation. No connection to an unrelated running server is accepted.
''')
    report('03_IMPLEMENTATION_SUMMARY.md', 'Implementation Summary', f'''
New source: `tools/playtest/{{runner,worker,analysis,browser,__init__}}.py`, two scenario
JSON definitions, `scripts/run_live_playtest.ps1`, `tools/validate_pr_play_08.py`,
`tools/report_pr_play_08.py`, and `tests/test_automated_playtest.py`. Updated only
the coverage registry and canonical NEXT_SESSION; added the guide. Production
`game/`, `static/`, ordinary `data/`, and `experiments/` were not edited.

The transaction is New Campaign → capture baseline → Start once → capture after.
HTTP statuses/bodies, narration presence, API-visible state, session metadata,
turn/scene/log, complete selected persistent files, native provider journal,
budget snapshot, structural/semantic/outcome stages and correlations are retained.
The report checks acceptance, one diagnostic commit, turn delta one, log delta
one and state-integrity constraints; HTTP 200 is insufficient.

Failure/interruption closes only the owned worker. After an interruption, persistent
after-state is copied after shutdown when the final API projection cannot be read.
Port collisions block without attaching to or terminating other processes.
No task implementation changes were made in response to production failures.

Evidence: `artifacts/pr_play_08/source_diff.patch`, source snapshots, matrix_runs.json,
JUnit XML/logs, protected integrity, and the complete example run at
`{success.relative_to(ROOT).as_posix()}`. The initial development failures identified
PID redirection, request-bookkeeping comparison, missing-diagnostic verdict and
fixture-expectation mistakes in the harness; final checks cover their corrections.
''')
    report('04_DIAGNOSTIC_CLASSIFICATION.md', 'Diagnostic Classification', '''
Precedence: infrastructure/preflight/startup/transport/interruption first; then
proven state-integrity violation; admission rejection; provider exception; explicit
output-limit exhaustion; other incomplete provider response; empty content; JSON
parse failure; envelope/structured-validation failure; evidenced semantic rejection;
opening-acceptance rejection; UI failure if observed; unknown otherwise.

Output-limit exhaustion requires explicit provider evidence, not token-count
coincidence. `incomplete` plus `max_output_tokens` outranks a downstream parse error.
Successful structured validation plus semantic reasons is semantic-stage evidence.
A genuine safe nonresolution can be structurally valid and fail opening acceptance
without evidence of a failed semantic validator; H6 is classified at acceptance.

Each non-PASS report carries category, stage, record path, zero-based record index
when applicable, field, observed value and native source owner when available.
The provider journal remains the native diagnostic format. No provenance ID is
fabricated: harness run/scenario maps to the journal's actual run/opening/provider
attempt IDs, with missing-ID limitations explicit. Parser/outcome details are
reported independently. Classifications describe observations; root cause remains
`Not established`, with `inferred=false`. No hypothesis is promoted to a defect.

Missing required diagnostics prevents PASS. Unknown fields/stages remain unknown;
empty or failed evidence does not become a fabricated success. Browser status is
NOT_TESTED, not PASS. Failure categories do not alter replay taxonomy or evaluators.
''')
    report('05_STATE_INTEGRITY_VALIDATION.md', 'State-Integrity Validation', '''
Baseline and after capture both API projection and all bounded isolated persistent
documents, including session/world/combat/character/campaign/conditions/scenes/log.
Copied files are retained exactly; normalization applies to comparison only.

Gameplay comparison unwraps known persistence envelopes and excludes saved_at /
derived integrity metadata plus session last_saved_at, diagnostic debug_traces,
and __turn_start_active_interaction_target_id request metadata. Empty rollback log
materialization is equivalent to an absent empty log. These explicit exclusions
are reported as bookkeeping changes; arbitrary JSON changes are not ignored.

Failure requires no normalized gameplay mutation. Success requires exactly one
turn/log increment, started=true, and only documented opening-owned runtime roots
and top-level fields may change. Character/conditions/authored scenes/combat or
unknown session/world fields are unexpected. Changed fields and unexpected files
are recorded. The conservative allowance is versioned in the tooling; it is not
an independent semantic authority over world ticks. Nested changes within allowed
opening-owned fields are observed, not a full gameplay-quality proof.

H2–H9 negative fixtures preserve gameplay state; H1/H10 commit exactly once.
H19 distinguishes timestamp bookkeeping from an injected world mutation. Persistent
after-state survives interruption even if API after-state is unavailable. Every
relevant protected file was hash-checked across validation; ordinary saves and
frozen fixture bytes stayed unchanged. See protected_before.json and
protected_integrity.json. Frozen ATGB content was never used as a writable store.
''')
    report('06_PROVIDER_SAFETY_VALIDATION.md', 'Provider Safety Validation', '''
No live provider or provider-connectivity calls were performed. Deterministic
transport replaces SDK constructors before requests, rejects asynchronous clients,
and rejects external socket connections. Real game admission still accounts for
synthetic operations; journal attempts in deterministic mode are not billable calls.
H15 verifies this boundary; H16 blocks unauthorized Live before starting a worker.
Live multi-turn/scenario misuse is refused even if an invocation flag is supplied.

Live requires both mode and explicit authorization flag, normal configured credential
presence, provider enablement, retry suppression, fresh isolated DATA_DIR and known
output allowance. Startup and direct connectivity probes are disabled; no health
request consumes a hidden admission. The skipped upstream gate is explicitly not
evidence of provider health. Existing model routing is retained; pin overrides are
refused. Opening output allowance is read from the game owner, never raised by the
harness. SDK max_retries=0 and host suppression use existing controls.

Default opening ceiling: one admission. Scenario ceilings cannot exceed the prior
controlled manual scope: six requests / 200000 input / 20000 output / 220000 total;
opening scenario itself requests one. Inherited stricter environment/.env limits
are retained using min, not replaced. Existing admission reservations and post-call
accounting remain authoritative. Tokens are estimates at admission and observed
usage after completion; an exhausted or unknown accounting record prevents PASS.
Usage, allowances, remaining budget and rejections are reported without inventing
pricing or failed-call token usage. No retry, budget expansion, model change, or
extra production operation occurs after a failure.

Credentials are never serialized. Exception strings are omitted; worker logs are
bounded and redact known environment secret values. Evidence selects only isolated
campaign and explicit diagnostic files, never canonical private play data or .env.
The review generator checks the selected bytes against configured secret values.
Residual: existing static readiness/source attestations are stale, producing two
baseline regression failures. They were not rewritten or relaxed. Native runtime
admission/accounting controls pass their other checks. External review remains
required before any first Live invocation.
''')
    hrows = [
        ('H1','Successful opening','PASS, one commit','success'),
        ('H2','Output truncation','FAIL; provider_output_limit_exhaustion','truncation'),
        ('H3','Invalid JSON','FAIL; json_parsing_failure','invalid_json'),
        ('H4','Missing envelope','FAIL; structured_envelope_failure','envelope'),
        ('H5','Semantic rejection','FAIL; semantic_validation_failure','semantic'),
        ('H6','Genuine safe nonresolution','FAIL; opening_acceptance_failure; zero commit','safe_nonresolution'),
        ('H7','Provider exception','FAIL; provider_exception','exception'),
        ('H8','Admission budget rejection','FAIL; provider_admission_rejection; zero dispatch','admission'),
        ('H9','Rollback','FAIL outcome / PASS state integrity','invalid_json'),
        ('H10','Commit once','PASS; turn/log/commit=1','success'),
        ('H11','Preflight failure','BLOCKED; no owned process or provider request',None),
        ('H12','Startup timeout','BLOCKED; bounded owned-process shutdown',None),
        ('H13','Interrupt','INCONCLUSIVE; ZIP/state preserved; process stopped',None),
        ('H14','Missing journal','INCONCLUSIVE; explicit limitation',None),
        ('H15','Deterministic boundary','Zero live calls; external connect refused',None),
        ('H16','Unauthorized Live','BLOCKED before worker/provider dispatch',None),
        ('H17','Occupied port','BLOCKED; unrelated listener survives',None),
        ('H18','Evidence archive','Readable ZIP; all manifest hashes match','success'),
        ('H19','State categories','Bookkeeping separated; injected truth mutation rejected',None),
        ('H20','Unknown category','Explicit unknown; root cause unestablished',None),
    ]
    write(O/'H1_H20_results.json', [{'id': h, 'case': desc, 'expected_observed': outcome,
          'test_result': 'PASS', 'evidence': matrix[case]['run'] if case else 'artifacts/pr_play_08/harness_regression.xml'} for h, desc, outcome, case in hrows])
    htable = '| ID | Case | Observed / asserted | Check |\n|---|---|---|---|\n'+''.join(f'| {h} | {desc} | {outcome} | PASS |\n' for h, desc, outcome, _ in hrows)
    regtable = '| Lane | Passed | Failed | Errors | Timeouts |\n|---|---:|---:|---:|---|\n'+''.join(f"| {k} | {v['passed']} | {v['failures']} | {v['errors']} | None |\n" for k,v in results.items())
    report('07_DETERMINISTIC_TEST_RESULTS.md', 'Deterministic Test Results', f'''
Final harness/coverage lane: 35 passed (26 harness checks plus nine registry checks).
H1–H20 are deterministic tooling assertions; negative fixture outcomes deliberately
FAIL while their corresponding harness test PASS confirms correct measurement.

{htable}

Additional checks: scripted observation, Live multi-turn refusal, scenario/global
limit enforcement, incomplete/empty categories, classification precedence and log
redaction. Evidence: harness_regression.xml/.txt; H1_H20_results.json; matrix_runs.json.

{regtable}

Completed scope totals: **{passed} passed / {failed} failed / zero errors/timeouts**.
No full-suite claim. All lanes use existing pytest/live-model guards and bounded
120-second owned-process timeouts. The final harness-only rerun updated its exact
command record; broader XML and logs retain measured outcomes, with lane commands
defined in tools/validate_pr_play_08.py.

Failure classification: six preexisting defects, zero demonstrated new production
regressions. Three rich-opening emission/length assertions and the saved stew-price
conversation assertion match documented PR-PLAY-06/07 baseline failures. Two tests
call the same stale provider source-attestation readiness audit (one provider test,
one ATGB accounting test). The production and frozen fixture sources those tests
inspect are hash-identical across this pass, and none of those test files changed.
No unrelated repair, threshold relaxation, source-attestation rewrite or production
change was made to obtain green results. Details remain in each failing lane log.

Initial HTTP runs under the restricted sandbox were environment-blocked at Python
socketpair/event-loop creation; bounded local-only probe reproduced it. With
localhost execution permitted, the same deterministic harness and HTTP regression
paths complete. Early harness-development failures and their corrected reruns
are preserved separately; they are not counted as final product regressions.
''')
    report('08_BROWSER_AND_GAMEPLAY_EXTENSION.md', 'Browser and Gameplay Extension', '''
Assessment: requirements.txt has FastAPI/Uvicorn/OpenAI/Pydantic/Pytest/HTTPX,
with no Playwright/Selenium. Existing frontend tests exercise Node handlers but
do not run a rendered browser. No large browser dependency was introduced.
`tools/playtest/browser.py` defines the adapter boundary: own New/Start-once clicks,
bounded wait, visible narration/error, screenshots, API/UI agreement and close.
A future browser adapter must replace API mutation steps, not repeat them.
Current reports always show UI NOT_TESTED. Screenshots directory is reserved.

ScriptedObservation implements deterministic opening, scene observation and explicit
started-state verification, with per-step collection and stop-on-first-failure.
Dispatcher contracts also map NPC interaction/examination to existing /api/chat
and rules/movement to /api/action request bodies. No gameplay behavior is authored
by the dispatcher. Future scenarios need reviewed deterministic response/request
fixtures and extended outcome invariants. Current opening comparator is deliberately
conservative; arbitrary five-/ten-turn progression is not claimed implemented.

No live multi-turn testing, autonomous play, large scenario library, ATGB scoring,
or PR-EG integration occurred. API success does not establish UI success or
AI-DM communication quality. These limitations are explicit in result/summary/guide.
''')
    report('09_USER_GUIDE_AND_OPERATIONAL_READINESS.md', 'User Guide and Operational Readiness', f'''
The standalone guide is `docs/AUTOMATED_PLAYTEST_GUIDE.md`. It covers installation,
all modes, exact commands, authorization/cost, result interpretation, ZIP discovery,
timeouts, safe recovery and limitations without requiring implementation knowledge.

Deterministic command (executed successfully through PowerShell):

```powershell
.\\scripts\\run_live_playtest.ps1 -Scenario CampaignOpening -Mode Deterministic -CaptureResponse
```

Latest summary/verdict and exact evidence ZIP path:

```powershell
.\\scripts\\run_live_playtest.ps1 -Latest
```

Scripted deterministic example:

```powershell
.\\scripts\\run_live_playtest.ps1 -Scenario ScriptedObservation -Mode ScriptedGameplay
```

Example PASS summary: `{(success/'reports/SUMMARY.md').relative_to(ROOT).as_posix()}`.
Example machine report: `{(success/'reports/result.json').relative_to(ROOT).as_posix()}`.
Example evidence: `{(success/'evidence/evidence.zip').relative_to(ROOT).as_posix()}`.
Run layout is unique, local, path-space safe and compatible with the established
ATGB isolation root. A fixed optional localhost port refuses an existing listener.
No manual environment setup, fixture copying, Uvicorn window, API invocation,
journal collection or compression is needed. Exit 0 means PASS; 2 means another
verdict. PowerShell may display a nonzero native command exit as its own failure.
No live command has been executed. Read report 10 before considering one.
''')
    confirmations = [
        'No live provider calls.', 'No provider connectivity diagnostics.', 'No model changes.',
        'No output-budget increases.', 'No automatic retries.', 'No additional production provider operations.',
        'No gameplay implementation changes.', 'No unauthorized gameplay-state mutations.',
        'No new persistent gameplay structures.', 'No experimental PR-EG integration.',
        'Frozen ATGB baseline unchanged.', 'No secrets included.', 'No commit or push performed.',
    ]
    write(O/'final_verdict.json', {'verdict': 'B — Conditionally ready', 'live_calls': 0,
          'reason': 'Deterministic controls pass; rendered/live adequacy untested and six preexisting regression failures remain.',
          'confirmations': confirmations, 'next_action': 'External review only; do not run Live in this pass'})
    report('10_FINAL_VERDICT_AND_HANDOFF.md', 'Final Verdict and Handoff', f'''
**B — Conditionally ready.** The complete deterministic harness and H1–H20 controls
pass. Evidence supports isolated one-opening orchestration, safety controls,
classification and export. Six preexisting regression failures remain, including
stale source attestations; rendered UI and actual provider adequacy remain untested.
The readiness conclusion is scoped to tooling and does not assert a live opening
will be accepted or repair the prior semantic cause.

Evidence: {passed} passing checks, six unchanged-source baseline failures, complete
negative/positive matrices, hashed example ZIP and {integrity['files']} protected files
unchanged. Source diff isolates this tooling pass from extensive entry worktree dirt.

One recommended next action: external review of CURRENT_REVIEW and the timestamped
completion ZIP. Stop here and await that review. After separate authorization, the
exact first Live command is:

```powershell
.\\scripts\\run_live_playtest.ps1 -Scenario CampaignOpening -Mode Live -AuthorizeLiveProvider -CaptureResponse
```

Expected exposure: at most **one live provider attempt**, zero SDK/host retries,
normal configured model, existing opening allowance (normally 3000), aggregate
limits no greater than 200000/20000/220000 and any stricter inherited limits.
Failed-call usage may be unknown; no cost estimate is fabricated. This command
is documented for review and **was not executed**. No follow-on implementation or
live automated playtest is authorized by this closeout.

Closeout confirmations:

'''+ '\n'.join('- '+c for c in confirmations))

    sources = sorted([p for p in (ROOT/'tools/playtest').rglob('*') if p.is_file() and '__pycache__' not in p.parts])
    sources += [ROOT/p for p in ('scripts/run_live_playtest.ps1', 'tools/validate_pr_play_08.py',
        'tools/report_pr_play_08.py', 'tests/test_automated_playtest.py', 'tests/validation_coverage_registry.py',
        'docs/AUTOMATED_PLAYTEST_GUIDE.md', 'docs/NEXT_SESSION.md')]
    delta = []
    for p in sources:
        rel = p.relative_to(ROOT)
        if rel.as_posix() == 'docs/NEXT_SESSION.md':
            before = (O/'entry_sources/docs/NEXT_SESSION.md').read_text(encoding='utf-8')
        elif rel.as_posix() == 'tests/validation_coverage_registry.py':
            before = (O/'entry_sources/validation_coverage_registry.py').read_text(encoding='utf-8-sig')
        else:
            before = ''
        delta.extend(difflib.unified_diff(before.splitlines(keepends=True), p.read_text(encoding='utf-8').splitlines(keepends=True),
                                        fromfile='a/'+rel.as_posix(), tofile='b/'+rel.as_posix()))
        snap = O/'source_snapshots'/rel
        snap.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, snap)
    (O/'source_diff.patch').write_text(''.join(delta), encoding='utf-8')
    status = subprocess.run(['git', 'status', '--short'], cwd=ROOT, capture_output=True, text=True, timeout=15)
    (O/'repository_status.txt').write_text(status.stdout, encoding='utf-8')

    # Select only scoped explicit evidence, never private canonical data.
    support = [*sources, *R.glob('*.md')]
    support += [p for p in O.rglob('*') if p.is_file() and 'source_snapshots' not in p.parts and 'entry_sources' not in p.parts and p.name not in {'review_config.json', 'package_verification.json'}]
    for record in matrix.values():
        run = Path(record['run'])
        support += [p for folder in ('configuration', 'baseline', 'after', 'diagnostics', 'reports')
                    for p in (run/folder).rglob('*') if p.is_file()]
        support.append(run/'evidence/manifest.json')
    config = {
        'campaign_id': 'pr_play_08', 'campaign_name': 'PR-PLAY-08 — Automated Live Playtest and Diagnostic Harness',
        'campaign_date': '2026-10-29', 'purpose': 'Offline tooling implementation and review; stop before live execution.',
        'objective_status': 'B — Conditionally ready',
        'executive_summary': f'Isolated one-command HTTP harness implemented; H1–H20 pass. Completed lanes: {passed} passed / {failed} preexisting failures. No production edits or live/provider-connectivity calls. External review required.',
        'primary_report': str((R/'10_FINAL_VERDICT_AND_HANDOFF.md').relative_to(ROOT)),
        'supporting_files': [{'path': p.relative_to(ROOT).as_posix(), 'role': 'source' if p in sources else 'evidence',
                              'why': 'Explicit scoped source, guide, report or deterministic evidence.'} for p in dict.fromkeys(support)],
        'changes': {'production': [], 'validation': ['H1–H20 and additional boundary/registry checks; existing regression selections.'],
                    'tooling': ['Isolated owned-server HTTP controller, synthetic transport, conservative comparator, classifier and evidence ZIP.'],
                    'documentation': ['Ten reports, standalone guide and canonical handoff.'],
                    'generated_artifacts': ['Matrix/JUnit/logs/source diff/status/hashes, example report/summary/ZIP.']},
        'testing': {'focused': '35 harness/coverage checks passed.', 'broader': f'{passed} passed / {failed} preexisting failures across completed lanes.',
                    'full_suite': 'Not run; bounded relevant regression only.',
                    'runtime_validation': 'Real localhost HTTP with synthetic SDK transport; API acceptance, commit and rollback owners.',
                    'model_runtime_boundary': 'Zero live/provider-connectivity calls. Deterministic external connects denied.',
                    'new_regressions': 'None demonstrated in completed scope.',
                    'pre_existing_failures': 'Three rich-opening assertions, saved conversation assertion, two stale provider source-attestation assertions.'},
        'decisions_requiring_human_review': ['Review conditional readiness before separately authorizing the first Live harness invocation.'],
        'known_problems': {'campaign_specific': ['No rendered browser adapter or live adequacy evidence; comparator is conservative and opening-scoped.'],
                           'pre_existing': ['Six unchanged-production-source regression failures remain; no unrelated repair authorized.']},
        'does_not_prove': ['Actual provider success, rendered UI success, ATGB scores, held-out generalization, or improved gameplay communication.'],
        'recommended_next_step': 'External review only. Do not execute the documented next Live command in this pass.',
        'self_contained_review_test': 'Ten reports, guide, scoped source/diff, H1–H20, regression logs/XML, hashes, complete example evidence and manifest verification.',
    }
    write(O/'review_config.json', config)
    build_handoff(config, archive_history=False)

    # User explicitly requires a complete example evidence ZIP inside the review
    # ZIP. The normal exporter excludes nested archives; add only this verified,
    # isolated non-review archive and update the manifest, never arbitrary ZIPs.
    handoff = ROOT/'handoff'
    zpath = handoff/'CURRENT_REVIEW.zip'
    with zipfile.ZipFile(zpath) as z:
        members = {n: z.read(n) for n in z.namelist()}
    example_rel = (success/'evidence/evidence.zip').relative_to(ROOT).as_posix()
    name = 'support/'+example_rel
    data = (ROOT/example_rel).read_bytes()
    members[name] = data
    manifest = json.loads(members['REVIEW_MANIFEST.json'])
    manifest['included_files'].append({'bundle_path': name, 'canonical_source_path': example_rel,
        'role': 'complete_deterministic_example_archive', 'canonical': True, 'generated': False,
        'why': 'Explicit PR-PLAY-08 user requirement; isolated diagnostic ZIP, no recursive review archive.',
        'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    manifest['file_count'] = len(members)
    manifest['nested_archive_policy_exception'] = 'Only the explicit isolated deterministic example requested by the user.'
    members['REVIEW_MANIFEST.json'] = (json.dumps(manifest, indent=2)+'\n').encode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for key, value in members.items():
            z.writestr(key, value)
    zpath.write_bytes(buf.getvalue())
    (handoff/'REVIEW_MANIFEST.json').write_bytes(members['REVIEW_MANIFEST.json'])
    # October 29 client context is EDT (UTC-04:00); filenames follow local time.
    local = datetime.now(timezone(timedelta(hours=-4)))
    timestamped = handoff/('CURRENT_REVIEW('+local.strftime('%Y%m%d-%H%M%S')+').zip')
    if timestamped.exists():
        raise FileExistsError('Refusing to overwrite a prior completion archive')
    shutil.copy2(zpath, timestamped)
    verify(zpath, sources)
    print(timestamped)


def verify(path, sources):
    from dotenv import dotenv_values
    configured = dotenv_values(ROOT/'.env')
    secret_values = [v.encode() for k,v in configured.items() if v and len(v)>8 and any(s in k.lower() for s in ('key', 'secret', 'password', 'credential'))]
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        manifest = json.loads(z.read('REVIEW_MANIFEST.json'))
        for row in manifest['included_files']:
            if row['bundle_path'] == 'REVIEW_MANIFEST.json':
                continue
            assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest() == row['sha256']
        for name in z.namelist():
            payload = z.read(name)
            assert not any(s in payload for s in secret_values), 'Configured secret found in selected bytes'
            if name.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(payload)) as nested:
                    assert nested.testzip() is None
                    for n in nested.namelist():
                        assert not any(s in nested.read(n) for s in secret_values)
        assert len([n for n in z.namelist() if '/pr_play_08/' in n and n.endswith('.md') and '/development/' in n]) == 10
        assert any(n.endswith('docs/AUTOMATED_PLAYTEST_GUIDE.md') for n in z.namelist())
    write(O/'package_verification.json', {'zip': str(path), 'readable': True, 'manifest_hashes_valid': True,
          'ten_reports_present': True, 'configured_secret_scan': 'PASS', 'nested_example_readable': True,
          'source_files': len(sources), 'bytes': path.stat().st_size})


if __name__ == '__main__':
    main()
