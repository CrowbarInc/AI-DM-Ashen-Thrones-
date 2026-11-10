"""Author recovery reports from recorded evidence; never imports production code."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REPORT = ROOT/'development/campaigns/product_realization/pr_play_adjacent_regression_recovery'
REPORT.mkdir(parents=True, exist_ok=True)
PREFIX = 'artifacts/pr_play_adjacent_regression_recovery/'
RP = 'development/campaigns/product_realization/pr_play_adjacent_regression_recovery/'
old = json.loads((ROOT/'artifacts/pr_play_adjacent_regression/classification_matrix.json').read_text())
failures = json.loads((OUT/'failures.json').read_text())
turns = json.loads((OUT/'http_capture.json').read_text())
integrity = json.loads((OUT/'execution_integrity.json').read_text())
assert not integrity['changed'] and not integrity['added']
assert not integrity['network_attempts_blocked']
assert len(failures) == 12 and {f['nodeid'] for f in failures} == {f['test'] for f in old['failures']}
assert all(f['phase'] == 'call' for f in failures)
suite = next(ET.parse(OUT/'recovery_junit.xml').getroot().iter('testsuite'))
assert suite.attrib['tests'] == '183' and suite.attrib['errors'] == '0'

def write(name, text):
    (REPORT/name).write_text(text.rstrip()+'\n', encoding='utf-8')

def engine(turn):
    for raw in turn['raw_before_projection']:
        if isinstance(raw, dict) and raw.get('resolution'):
            return raw
    logs = turn['after'].get('log', [])
    return logs[-1] if logs else {}

contract_paths = [
    'development/campaigns/product_realization/pr_play_67/05_PLAYER_SAFE_RESPONSE_CONTRACT.md',
    'development/campaigns/product_realization/pr_play_67/09_FRONTEND_COMPATIBILITY.md',
    'development/campaigns/product_realization/pr_play_67/10_DEVELOPMENT_TESTS.md',
    'artifacts/pr_play_67/response_contract.json',
]
rows = []
for oldrow in old['failures']:
    row = copy.deepcopy(oldrow)
    recorded = next(f for f in failures if f['nodeid'] == row['test'])
    events = turns[row['test']]
    row['http_capture_ref'] = PREFIX+'http_capture.json#'+row['test']
    row['traceback'] = recorded['traceback']
    row['fixtures'] = recorded['fixtures']
    row['production_paths'] = ['game/api.py', 'game/conversational_orchestration.py',
                               'game/referenced_surface.py', 'game/exploration.py',
                               'game/player_http_projection.py']
    row['http_events'] = []
    for t in events:
        raw = engine(t)
        res = raw.get('resolution') or {}
        gm = raw.get('gm_output') or {}
        changes = {}
        for owner in ('session', 'character', 'world'):
            a, b = t['before'].get(owner, {}), t['after'].get(owner, {})
            if isinstance(a, dict) and isinstance(b, dict):
                changes[owner] = {k: {'before': a.get(k), 'after': b.get(k)}
                                  for k in set(a)|set(b) if a.get(k) != b.get(k)}
        row['http_events'].append({'request': t['request'], 'status': t['http_status'],
            'public_resolution': t['response'].get('resolution'),
            'published_text': (t['response'].get('gm_output') or {}).get('player_facing_text'),
            'routing': t['routing'], 'engine_resolution': res,
            'gm_metadata': gm.get('metadata'), 'state_changes': changes})
    is_prose = row['id'] in (3, 5, 8)
    row['classification'] = 'E' if is_prose else 'C'
    row['classification_name'] = 'unresolved_origin' if is_prose else 'obsolete_expectation'
    row['confidence'] = 'high that origin remains unresolved; high in current failure' if is_prose else 'high'
    row['supporting_evidence'] = (
        ['Fresh unchanged-test failure and full HTTP capture.',
         'Prior current/historical captures agree; documented overlay removes handoff symbols.',
         'game/perception_grounding.py exits when immutable acceptance forbids replacement.'] if is_prose else
        ['PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder.',
         'PR-PLAY-67 migrated analogous assertions to persisted server logs.',
         'Fresh capture contains the engine resolution, while player response resolution is {}.'])
    row['contradictory_evidence'] = (
        ['Prior audit labels this B/high; overlay equality supports a preexisting hypothesis.',
         'No authenticated exact pre-repair dirty source snapshot or exact pre-repair run exists.'] if is_prose else
        ['Older test expects internal resolver fields; prior adjacent audit labeled this B.',
         'Some tests also have later prose assertions; class C covers only the actual stopping assertion.'])
    row['remaining_uncertainty'] = (
        'Exact historical origin and compatibility/provenance of reconstructed overlay cannot be established. '
        'Current publication defect is demonstrated; no evidence establishes it as new because of the repair.' if is_prose else
        'Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures '
        'remains a separate publication concern, not excused by this classification.')
    row['fixture_description'] = (
        'Synthetic mill-loft scene/world, tariff slate, skylight, hidden token, abstract ledger; '
        '_seed_scene_runtime and stubbed generation in referenced-surface HTTP tests.' if row['id'] <= 8 else
        'Authored frontier_gate fixture with roster/notice board.' if row['id'] <= 10 else
        'PR-PLAY-38 recorded interpretation and persistent frontier-gate fixture; _install_frontier, _quiet_models.')
    if is_prose:
        row['production_paths'] += ['game/perception_grounding.py', 'game/immutable_valid_response.py']
    rows.append(row)

matrix = {'milestone': 'pr_play_adjacent_regression', 'execution': 'regression_audit_recovery',
    'audit_verdict': 'A/PASS', 'selection': {'adjacent_tests':176,'adjacent_failures':12,'adjacent_passed':164,
    'focused_tests':7,'focused_passed':7,'errors':0,'skipped':0,'modules':old['selection']['modules']},
    'totals':{'A':0,'B':0,'C':9,'D':0,'E':3},'previous_repair_acceptance':'B — Conditional acceptance',
    'next_action':'Option C — Baseline-integrity correction','live_provider_calls':0,'failures':rows}
(OUT/'classification_matrix.json').write_text(json.dumps(matrix,indent=2,default=str))

write('SUMMARY.md', '''# Adjacent Regression Reconciliation — recovery execution

Milestone: `pr_play_adjacent_regression`. Recovery reports: `pr_play_adjacent_regression_recovery`.

**Audit verdict: A/PASS. Previous repair: B — Conditional acceptance.**

The exact 176-test adjacent selection reproduces the same 12 failed test identities: 164 passed,
12 failed, zero collection/setup errors, zero skipped. Seven focused handoff tests pass, for
171 passed / 12 failed across 183 tests. Actual stopping assertions: A=0, B=0, C=9, D=0, E=3.
Nine assertions conflict with the established PR-PLAY-67 empty public-resolution contract.
Three prose assertions demonstrate publication defects whose pre-repair origin remains unresolved.
No failure is proven to be a new regression. That is not proof that none is new.

T04/T05/T06/T09 retain their corrected intent/routing. T04 and T06 decline without completing a
physical action. T05 publishes the authorized clue plus the unwanted stock jab sentence. T09 recalls
the disclosed clue. Explicit repetition, genuine NPC follow-up, unknown destination, hidden-information,
genuine travel, and publication-refusal controls pass. This is provider-free focused evidence,
not independent generalization, a live-play result, or a Gameplay Benchmark.

Highest risk: a hidden-token inspection publishes a claim that the player pockets it while the
authoritative resolution does not commit that retrieval. Glassport crews and four overseers are
also unsupported prose. Some C-class tests additionally expose wrong-scene stock sentences;
obsolete public-metadata assertions do not make those sentences acceptable.

**Exactly one next action: Option C — Baseline-integrity correction.** Establish a coherent,
authenticated pre-repair baseline or obtain an explicit contract/provenance decision before
claiming full regression acceptance. Defer T05 repair. No production/test changes, live providers,
campaign openings, commits or pushes occurred. Stop after this investigation and verified handoff.

The local stale stable ZIP is the earlier repair package even though the local Markdown/manifest
describe the audit. The dated 174500 audit ZIP is different and valid for its older scope.
The user-named 232824 ZIP is unavailable here; its individual provenance remains unresolved.
See HANDOFF_RECOVERY.md and the separately recorded final archive verification/SHA-256.
''')

write('HANDOFF_RECOVERY.md', '''# Handoff recovery

## Established facts

At entry, docs/NEXT_SESSION.md, handoff/CURRENT_REVIEW.md, and handoff/REVIEW_MANIFEST.json already
identify Adjacent Regression Reconciliation. Seven audit reports, a 12-row classification matrix,
current/historical captures, JUnit logs, an export directory and a dated audit ZIP exist.
Thus the audit did execute and update reports and NEXT_SESSION; alternatives 1–3 are contradicted
by local evidence. A completed local audit exists, though this recovery revises its classifications.

`handoff/CURRENT_REVIEW.zip` has SHA-256
`648317fb809da2e8f2dfb2baa3dc17a0be8c892d8cd9669272bad8507a14f540`, identical to
`CURRENT_REVIEW(20261108-172122).zip`; both internally identify the previous post-NPC repair.
`CURRENT_REVIEW(20261108-174500).zip` instead identifies the audit; its SHA-256 is
`4b1b8e9533aee81cc6d7a39155a2c4aae24f39bf3832a0c043577be2f57c5f2d`.
The audit export under artifacts/pr_play_adjacent_regression/review_export is also distinct.
See archive_diagnosis.json for exact members, sizes, hashes and internal summary headers.

## Cause and limits

Confirmed local failure mode: publication of the new review surfaces was incomplete/inconsistent;
the stable ZIP retained the previous cycle while Markdown and manifest advanced. This matches
stale-file packaging/selection or reuse (alternatives 4–6). The exact copy command, directory-selection
mistake, or execution interruption cannot be determined from available logs. No evidence establishes
alternative 7. Do not infer a particular command solely from mtimes.
The specifically reported CURRENT_REVIEW(20261108-232824).zip does not exist in this workspace;
its rename/copy history and contents cannot be independently inspected. That remains unresolved.

## Procedure examined and corrected

docs/review_handoff_standard.md and tools/build_review_handoff.py require explicit source configuration.
build_handoff writes CURRENT_REVIEW.md, REVIEW_MANIFEST.json, and CURRENT_REVIEW.zip together in the
selected output directory. It does not automatically synchronize exports generated elsewhere or
create a timestamped stable-root copy. Existing configuration/export are preserved as historical evidence.

This recovery uses a new explicit configuration in artifacts/pr_play_adjacent_regression_recovery/.
Generate directly to handoff with --no-history, preserving prior history. Copy the freshly generated
stable ZIP to CURRENT_REVIEW(YYYYMMDD-HHMMSS).zip using America/New_York time. Open that exact new
archive; enumerate members; read both internal CURRENT_REVIEW.md and support/docs/NEXT_SESSION.md;
verify all eight reports, 12 matrix entries, canonical hashes, and absence of prior-package identity.
Record external archive SHA-256 and verification JSON after sealing. Archive hashes cannot be embedded
in the archive they hash without a circular dependency. Packaging failure alone does not rerun tests.
''')

inventory = ['# Failure inventory', '',
    'The 12 records below are the actual stopping failures, not every unexecuted assertion later in each test.',
    'All are HTTP 200 call-phase failures; the two missing transition keys are KeyErrors, not collection/environment errors.',
    'Full requests/responses, pre-projection bodies, routing and before/after session/character/world/log are in http_capture.json.',
    'Complete traceback and fixture names are in failures.json and repeated in classification_matrix.json.', '']
for row in rows:
    inventory += [f"## F{row['id']:02d} — {row['test'].split('::')[-1]}", '',
        f"- Test/file: `{row['test']}`.", f"- Failing assertion: {row['assertion']}.",
        f"- Expected: {row['expected']!r}. Actual: {row['actual']!r}.",
        f"- Classification: **{row['classification']} — {row['classification_name']}**. Confidence: {row['confidence']}.",
        f"- Fixture: {row['fixture_description']} Pytest fixtures: {', '.join(row['fixtures'])}.",
        f"- Production path: {', '.join('`'+p+'`' for p in row['production_paths'])}.",
        '- Supporting evidence: '+' '.join(row['supporting_evidence']),
        '- Contradictory evidence: '+' '.join(row['contradictory_evidence']),
        '- Player significance: '+str(row['player_facing'])+'. '+row['remaining_uncertainty'], '']
    for i,event in enumerate(row['http_events'],1):
        res = event['engine_resolution']
        inventory += [f"HTTP event {i}: `{json.dumps(event['request'])}`; status {event['status']}; public resolution `{event['public_resolution']}`.",
            f"Published: {event['published_text']}",
            f"Routing: `{json.dumps(event['routing'],default=str)}`. Engine kind `{res.get('kind')}`; "
            f"authority `{(res.get('metadata') or {}).get('referenced_surface_authority')}`; "
            f"state_changes `{json.dumps(res.get('state_changes'),default=str)}`.",
            'Changed persisted top-level fields: '+', '.join(owner+': '+(', '.join(delta) or '(none)')
            for owner,delta in event['state_changes'].items())+'. Full old/new values remain in machine evidence.', '']
    inventory += ['Traceback: `'+PREFIX+'failures.json#'+row['test']+'`; full text also in matrix row.', '']
write('FAILURE_INVENTORY.md', '\n'.join(inventory))

write('BASELINE_RECONSTRUCTION.md', '''# Baseline reconstruction

HEAD d40f1ed198236c604085f1c842ead267a8104ce2 is not a complete pre-repair baseline: the worktree
contains substantial uncommitted modules. HEAD orchestration lacks authored_travel_admission.
No checkout, reset, stash, import editing, module mixing, or historical execution was performed.

Historical evidence inspected: post-NPC SUMMARY, ROOT_CAUSE, REGRESSION_RESULTS,
TWELVE_TURN_COMPARISON, INTEGRITY, implementation.diff and adjacent_focus_junit.xml; previous
adjacent audit reports, overlay_manifest, both capture JSON files, and JUnit; existing local
dated and stable review ZIPs; the surviving temporary build_overlay.py/capture_failures.py sources.
The predecessor explicitly says it did not obtain a pre-edit adjacent run. Its JUnit is post-repair.
The earlier 118-test passing slice is a different selection and does not establish these twelve as passing.

The prior adjacent audit copied current game, substituted three HEAD files and manually removed
handoff insertions from orchestration while retaining authored travel. Its captures match each other.
This supports a preexisting-failure hypothesis but is a reconstructed counterfactual, not an
authenticated source state immediately before repair. The saved overlay has no exact pre-edit
dirty-tree hash or patch provenance proving all remaining modules' temporal compatibility.
We read this evidence, did not rebuild or execute that mixed-source package, and do not promote
its equality into confirmation that the three prose failures predate the repair.

Read-only source comparison is recorded in source_comparison.json: current hashes, HEAD hashes,
git-diff hashes/statistics and preserved repair diff hash. Current source paths are hashed at entry
and exit. PR-PLAY-67's written public-resolution contract independently establishes C for nine
stopping assertions without needing an exact temporal baseline. Three prose defects remain E as
to origin; their current manifestation is not uncertain.

Fresh unchanged tests reproduce the same twelve identities against the current working source.
183 collected (176 adjacent + 7 controls), 171 passed, 12 failed, zero errors/skips. Full command,
nodes, JUnit and tracebacks are recorded. Initial instrumentation run incorrectly blocked Windows
asyncio loopback socketpairs: 20 failures and 7 setup errors. That invalid product run is retained
under instrumentation_failed and excluded from classifications. After allowing loopback, external
connections remain fail-closed and all environmental failures disappear. No protected files changed.

Limitation: this audit supports a meaningful conditional judgment, not full temporal regression
attribution. Preserve and authenticate coherent source snapshots and exact commands before future
edits; do not replace dirty working modules with HEAD. Baseline work is the selected next action.
''')

write('CONTRACT_ANALYSIS.md', '''# Contract analysis

## Public HTTP metadata

PR-PLAY-67/05_PLAYER_SAFE_RESPONSE_CONTRACT.md explicitly states that resolution is an empty
compatibility placeholder. PR-PLAY-67/09_FRONTEND_COMPATIBILITY.md confirms optional details
display {}; 10_DEVELOPMENT_TESTS.md records migrating analogous metadata assertions to server logs.
artifacts/pr_play_67/response_contract.json documents the same field. These are established
contracts, not an inference from current code. game/player_http_projection.py:project_player_response
implements them; game/api.py applies the projection at the final runtime HTTP boundary.

F01/F02/F04/F06/F07/F09/F10 require a public resolution.kind; F11/F12 require a public
resolved_transition. All nine conflict with that contract and are C. The engine still records
kind/authority/transition. No test was modified. C classifies only each actual stopping assertion;
later assertions about meaningful prose may remain valid and are not declared obsolete.
This corrects the previous adjacent audit's unresolved contract analysis and all-B matrix.

## Non-invention and authority

Naming a hidden object cannot grant discovery/retrieval authority; an abstract shipping-record
reference cannot license invented crews; an unsupported schedule cannot instantiate overseers.
F03/F05/F08 publish the supplied model stubs. State remains governed by structured resolution,
but prose makes unsupported claims. They are current publication defects, E only for historical
origin. They are not C merely because current code emits them, nor D merely because text is stubbed:
unchanged HTTP tests intentionally exercise validation against those stubs.

game/perception_grounding.py:apply_perception_non_invention_to_gm checks
game/immutable_valid_response.py:leave_text_unchanged before replacement. Captures preserve
accepted-response/skipped-mutator metadata. The earliest demonstrated bypass is that a sealed
accepted sentence survives while the perception correction abstains. Whether the earlier acceptance
owner should have rejected each sentence requires a separate scoped investigation; no repair or
new authority is inferred here. Wrong-scene observe stock in other captures is separately concerning.

## Routing, publication and refusal

Post-NPC ROUTING_CONTRACT keeps local board approach separate from travel, current object inspection
separate from previous NPC overlap replay, explicit repetition available, and unsupported physical
actions as non-completed refusals. T04/T06 route correctly but do not perform touch or writing.
T05 discloses notice_patrol_route with contamination. T09 recalls only disclosed content.
Real patrol travel changes active_scene_id to old_milestone even though HTTP hides the internal flag.
Unsupported retreat is an operational refusal, not a completed gameplay publication. The focused
tests check last-publication preservation and completed flags using server log/session authority.

Ambiguities: exact temporal origin of three prose defects; unexecuted later assertions masked by
obsolete public-metadata assertions; upstream acceptance ownership of unsupported immutable text.
No live-model behavior, benchmark, or broad gameplay acceptance is established.
''')

control_nodes = {n: ts for n,ts in turns.items() if 'test_pr_play_post_npc_handoff.py' in n}
assert len(control_nodes) == 7
control_rows=[]
for node,events in control_nodes.items():
    for t in events:
        raw=engine(t); res=raw.get('resolution') or {}; session=t['after'].get('session') or {}
        control_rows.append({'test':node,'request':t['request'],'http_status':t['http_status'],
            'text':(t['response'].get('gm_output') or {}).get('player_facing_text'),
            'resolution':res,'routing':t['routing'],'active_scene_id':session.get('active_scene_id'),
            'last_publication':session.get('last_publication'),
            'character_changed':t['before'].get('character') != t['after'].get('character')})
(OUT/'targeted_controls.json').write_text(json.dumps(control_rows,indent=2,default=str))
controltext='''# Targeted repair verification

Seven unchanged tests in tests/test_pr_play_post_npc_handoff.py pass through real in-process
TestClient /api/chat with provider dispatch disabled. No live campaign is opened; synthetic already-started
sessions are seeded in isolated storage. Full captured responses and before/after state are retained.

| Turn/control | Intent recognition and routing | Gameplay authority | Publication | Usefulness |
|---|---|---|---|---|
| T04 board approach | Local current-scene object; no unknown-destination route | No travel, touch mechanic or clue granted | Local limitation; previous publication preserved | Grounded limitation; touch not completed |
| T05 notice inspection | Inspection, not captain replay | notice_patrol_route disclosed, scene unchanged | Authorized northwest clue plus stock jab sentence | Useful clue; contamination remains |
| T06 sleeve copying | Physical attempt, not NPC repetition | Unsupported; no inventory change | Non-completed refusal | Clear limitation; writing not completed |
| T09 recall | Grounded notice inspection, not unaddressed NPC ask | Already-disclosed content only | Northwest clue recall | Useful grounded recall |
| Explicit NPC repetition | Three repeat forms retain captain | No notice discovery | Prior authorized statement | Preserved |
| Genuine NPC follow-up | Return to captain after notice | Grounded NPC owner | Captain response | Preserved within fixture |
| Unknown destination/object | Reject unestablished observatory | No invented location/clue/scene change | Grounded refusal | Preserved |
| Hidden-information protection | Hidden signal and unknown cloak color not invented | No hidden notice facts granted | Protected facts absent | Preserved within these cases |
| Genuine travel | Missing-patrol route reaches movement resolver | Scene becomes old_milestone | Arrival text | Preserved |
| Publication refusal | Unsupported retreat stops before completion | No scene movement or completed gameplay | Operational refusal | Correct boundary, not successful play |

The four targeted improvements remain demonstrated. T05 is still not clean publication. These tests
were authored with the repair, so passing them is reproduced/focused evidence, not an independent
holdout or proof of generalized conversation quality. No live play or Gameplay Benchmark was run.

## Exact fresh control publications
'''
for c in control_rows:
    controltext += '\n- '+str(c['request'])+' → '+str(c['text'])+' (scene '+str(c['active_scene_id'])+').\n'
write('TARGETED_REPAIR_VERIFICATION.md',controltext)

write('NEXT_STEP_DECISION.md', '''# Next-step decision

**Previous repair acceptance: B — Conditional acceptance.** All four targeted intent/routing
improvements remain demonstrated, and the controls pass. Nine failures are obsolete public-metadata
expectations, not new gameplay regressions. Three adjacent publication defects have unresolved
historical origin, so full acceptance is not supported. No new regression is confirmed; no claim
is made that none exists. The baseline is sufficient for this bounded judgment, so status is not BLOCKED.

**Exactly one selected action: Option C — Baseline-integrity correction.** Authenticate a coherent
pre-repair source/evidence baseline or resolve its provenance explicitly, preserving all dirty work.
Tie the exact 176-test selection and three publication captures to that source state. Preserve the
PR-PLAY-67 HTTP privacy contract and distinguish persisted resolution from client DTO assertions.
If no exact historical source survives, record that fact and obtain an explicit acceptance/provenance
decision rather than presenting a hand-edited overlay as the historical working tree.

Option A (T05 stock-sentence repair) is deferred pending that reconciliation. Option B is not selected
because no confirmed new regression has been attributed to the repair. Token retrieval prose,
Glassport crews, overseers, and wrong-scene stock remain reported defects, not silently repaired.

This recovery is audit-complete A/PASS independently of conditional product acceptance. No production
changes, test expectation changes, prompts, models, provider budgets, gameplay features or new cycle
are authorized by this recommendation. Stop after verified handoff; do not open PR-PLAY-80 or AT-OPT-07.
''')

write('INTEGRITY.md', f'''# Integrity

- Branch: feature/product-realization. HEAD: d40f1ed198236c604085f1c842ead267a8104ce2.
- Entry worktree was substantially dirty; exact status is entry_git_status.txt. HEAD is not the dirty baseline.
- {integrity['protected_files']} source/test/data/static/prompt files hashed before and after execution: zero changed, zero added.
- No production or test expectation edits. No checkout, reset, clean, stash, revert, commit or push.
- No historical reports, evidence or handoff history were overwritten. Older archive contents/hashes inspected read-only.
- No historical module package was executed or rebuilt. Prior overlay claims are explicitly qualified.
- Live provider calls: **0**. External socket/DNS attempts blocked: {len(integrity['network_attempts_blocked'])} in the valid run.
- Windows loopback allowed for asyncio wakeup sockets; TestClient is in process. No campaign openings or live gameplay.
- Focused and adjacent tests ran sequentially in one process, with isolated storage and protected-data audit guard.
- Initial guard instrumentation failure is preserved separately, excluded from product counts; protected files also unchanged there.
- Created: eight recovery reports under {RP}, runner, classification matrix, HTTP/traceback/JUnit evidence,
  control capture, archive diagnosis, source comparison, command/node/status/hash integrity records,
  explicit review config, and final external archive verification/SHA-256 under {PREFIX}.
- Authorized updates: prepended docs/NEXT_SESSION.md; regenerated handoff/CURRENT_REVIEW.md,
  REVIEW_MANIFEST.json and CURRENT_REVIEW.zip; created a fresh timestamped ZIP. Historical handoff entries preserved.
- See files_created.json for exact file inventory and final archive verification for sealed contents/hash.
''')

# Preserve historical handoff entries verbatim below the new orientation.
nextfile=ROOT/'docs/NEXT_SESSION.md'
heading='# NEXT_SESSION — PR-PLAY Adjacent Regression Reconciliation recovery (2026-11-08)'
previous=nextfile.read_text(encoding='utf-8')
assert not previous.startswith(heading), 'Do not prepend duplicate recovery entry'
intro=f'''{heading}

**Audit A/PASS; previous repair B — Conditional acceptance.** Milestone `pr_play_adjacent_regression`.
Recovery reports: `{RP}`. Evidence: `{PREFIX}`. Branch `feature/product-realization`,
HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`; substantial dirty work preserved. No commits/pushes.

Same 176 adjacent tests: 164 passed / 12 failed, zero errors/skips; seven focused controls pass.
Classification A=0/B=0/C=9/D=0/E=3. PR-PLAY-67 explicitly makes public resolution empty: nine stopping
assertions are obsolete. Glassport crews, brass-token retrieval prose and four overseers remain
current defects with unresolved pre-repair origin. This supersedes the earlier audit's all-B/full-acceptance
claims; its reconstructed overlay is supporting evidence, not an authenticated exact pre-edit source.

T04 local approach, T05 clue inspection, T06 unsupported copying and T09 grounded recall still hold.
T04/T06 do not complete physical actions; T05 still appends the stock jab sentence. Controls pass for
repetition, NPC follow-up, unknown destination, hidden information, travel and publication refusal.
Game playability/generalization not established. Live provider calls: **0**; no campaign opened.

Stale local stable ZIP was identical to the previous repair package while Markdown/manifest advanced.
Dated 174500 ZIP already contained the earlier audit. User-named 232824 ZIP is absent; its provenance
remains unresolved. Recovery generates and independently opens the new stable and timestamped archive;
sealed member checks and SHA-256 are in `{PREFIX}archive_verification.json` and `archive_sha256.txt`.

**Exactly one next action: Option C — Baseline-integrity correction.** Authenticate coherent source/run
provenance for the three publication failures before full acceptance. Defer the T05 repair. Do not
start the next action, PR-PLAY-80, AT-OPT-07, live play, or a new repair from this handoff.
Minimum reading: recovery SUMMARY, FAILURE_INVENTORY, BASELINE_RECONSTRUCTION, HANDOFF_RECOVERY,
NEXT_STEP_DECISION and the matrix; PR-PLAY-67/05_PLAYER_SAFE_RESPONSE_CONTRACT.md.

---

'''
nextfile.write_text(intro+previous,encoding='utf-8')

config=copy.deepcopy(json.loads((ROOT/'artifacts/pr_play_adjacent_regression/review_handoff.json').read_text()))
config.update(campaign_name='PR-PLAY Adjacent Regression Reconciliation — Verified Recovery',
    executive_summary='Audit A/PASS; previous repair B — Conditional acceptance. Same 176 adjacent tests: '
    '164 passed, 12 failed, zero errors/skips; seven focused controls pass. Classifications A=0/B=0/C=9/D=0/E=3. '
    'Nine obsolete public-resolution assertions are grounded in PR-PLAY-67; three prose defects have unresolved origin. '
    'Local stable ZIP was the prior repair package while Markdown/manifest had advanced. New archive independently verified. '
    'No production/test changes, live provider calls, or campaign openings.',
    purpose='Recover handoff integrity and individually investigate twelve adjacent HTTP failures.',
    primary_report=RP+'SUMMARY.md', objective_status='A/PASS')
config['changes']={'production':[],'validation':['Unchanged tests; fresh isolated evidence only.'],
    'tooling':[],'documentation':['Eight recovery reports; prepended NEXT_SESSION preserving historical entries.'],
    'generated_artifacts':['Fresh evidence and coherent standard review bundle; historical reports preserved.']}
config['testing']={'focused':'7 passed; T04/T05/T06/T09 and negative controls.',
    'broader':'176 tests: 164 passed, same 12 failures, zero errors/skips. C=9/E=3.',
    'full_suite':'Not run.', 'runtime_validation':'In-process provider-free TestClient; synthetic already-started sessions only.',
    'model_runtime_boundary':'Live provider calls 0. No external network attempts in valid run.',
    'new_regressions':'None confirmed; three origins unresolved.',
    'pre_existing_failures':'No B classifications claimed without exact baseline. Nine C assertions conflict with PR-PLAY-67.'}
config['known_problems']={'campaign_specific':['T05 clue plus stock sentence remains.'],
    'pre_existing':['Dirty worktree; exact pre-repair baseline absent. Three publication defects have unresolved origin.']}
config['decisions_requiring_human_review']=['Conditional repair acceptance; authenticate baseline/provenance before full acceptance.']
config['missing_concepts']=['Authenticated exact pre-repair dirty source snapshot.']
config['does_not_prove']=['No broad playability, independent holdout, live-model evaluation or Gameplay Benchmark.',
    'Historical origin of three prose defects remains unresolved. No authorization for a new repair cycle.']
config['recommended_next_step']='Option C — Baseline-integrity correction. Stop here; defer T05 repair.'
config['self_contained_review_test']='Exact new ZIP opened after generation; reports, 12-row matrix, canonical hashes and both handoffs verified; external seal record retained.'
support = [RP+n for n in ['HANDOFF_RECOVERY.md','FAILURE_INVENTORY.md','BASELINE_RECONSTRUCTION.md',
    'CONTRACT_ANALYSIS.md','TARGETED_REPAIR_VERIFICATION.md','NEXT_STEP_DECISION.md','INTEGRITY.md']]
support += [PREFIX+n for n in ['classification_matrix.json','http_capture.json','failures.json',
    'recovery_junit.xml','targeted_controls.json','archive_diagnosis.json','source_comparison.json',
    'execution_integrity.json','command.json','collected_nodes.json','entry_hashes.json',
    'entry_git_status.txt','run_audit.py']]
support += contract_paths + ['docs/NEXT_SESSION.md','artifacts/pr_play_adjacent_regression/overlay_manifest.json',
    'artifacts/pr_play_adjacent_regression/current_capture.json',
    'artifacts/pr_play_adjacent_regression/historical_capture.json',
    'artifacts/pr_play_post_npc/implementation.diff',
    'development/campaigns/product_realization/pr_play_post_npc/REGRESSION_RESULTS.md',
    'development/campaigns/product_realization/pr_play_post_npc/ROUTING_CONTRACT.md',
    'game/player_http_projection.py','game/perception_grounding.py','game/immutable_valid_response.py',
    'tests/test_referenced_surface_grounding_inspection_resolution.py',
    'tests/test_pr_play_39_action_admission.py','tests/test_pr_play_post_npc_handoff.py']
config['supporting_files']=[{'path':p,'role':'audit_evidence','why':'Supports recovered audit claims and review provenance.',
    'behavioral_evidence':p.endswith(('.xml','.json')), 'human_review_required':True} for p in support]
(OUT/'review_handoff.json').write_text(json.dumps(config,indent=2))
print(json.dumps({'reports':str(REPORT),'matrix_rows':len(rows),'classifications':matrix['totals']}))
