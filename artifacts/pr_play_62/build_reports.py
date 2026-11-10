"""Generate reports from captured evidence. Never dispatches a provider request."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/pr_play_62'
REPORT = ROOT / 'development/campaigns/product_realization/pr_play_62'
REPORT.mkdir(parents=True, exist_ok=True)


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def write(name, text):
    (REPORT / name).write_text(text.strip() + '\n', encoding='utf-8')


m = read('metrics.json')
rows = read('browser_actions.json')
latency = read('latency.json')
quality = read('quality_scores.json')
regression = read('regression_summary_final.json')
failures = read('failure_injection_assessed.json')
baseline = read('baseline.json')
focused = regression['focused']
holdout = regression['holdout']
broader = regression['broader_hard_validation']
regtext = (
    f"Focused: {focused['passed']}/{focused['collected']} passed, {focused['failed']} failures, "
    f"{focused['errors']} errors; {len(focused['new_failures'])} new failures. "
    f"Additional failed-examination boundary: 1 passed. PR55 holdout wrapper: "
    f"{holdout['passed']}/{holdout['collected']} passed. Broader authority assurance: "
    f"{broader['failed']}/{broader['collected']} failures involving hard_validation_attempt_1. "
    "Full suite NOT TESTED."
)

write('01_EXECUTIVE_SUMMARY.md', f"""# PR-PLAY-62 — Investigation loop quality and responsiveness

**{m['verdict']}.** Five consecutive actions completed over real localhost HTTP.
One live narration passed all validation layers and reached the player response.
Two rejected candidates used action-specific fallback; two resolved repeats used
a separately opted-in deterministic fast path. Browser-originated actions: zero.
The browser webview failed to attach twice; frontend rendering was NOT TESTED.

The demonstrated improvement is recovery wording: the barrel fallback addresses
the barrel and no-new-clue result, omitting the whole-scene catalogue. Required
prior route information remains explicit. New live candidates were shorter, but
only 1/3 published. No generalized acceptance-rate improvement is established.

HTTP mean {m['average_http_ms']/1000:.3f}s, maximum {m['maximum_http_ms']/1000:.3f}s,
versus PR61's 2.601s/3.331s. The first provider adapter interval included substantial
setup before admission. Parallel regression activity confounds this comparison.
Shorter output did not establish faster responses. Fast-path turns took 1.533s
and 1.721s with zero provider requests.

OpenAI gpt-4.1-mini-2025-04-14: 3 requests, 1,412 input + 113 output = 1,525 tokens,
zero retries. All five authority projections match deterministic control except
campaign identity. Canonical data hashes are unchanged. Ten required fault cases
recover, preserving deterministic authority and permitting another action.
Quality judgments are PROVISIONAL automated assessments, not human or ATGB scores.

{regtext}

No commit or push. Existing dirty work is preserved. Primary next step: restore
browser webview attachment and run this same sequence through the existing UI.
Do not start PR-PLAY-63 yet.
""")

write('02_BASELINE_AND_SCOPE.md', f"""# Baseline and scope

Commit: `{baseline['commit']}`. Entry working-tree status is preserved in
artifacts/pr_play_62/baseline.json. There were extensive existing tracked and
untracked changes, including already-dirty protected data/baselines. No AGENTS.md
was found in the workspace; .agents contained no files. Entry source copies and
an entry-to-current implementation.diff distinguish this work from prior edits.

Read: Development Constitution, NEXT_SESSION, Validation Evidence Standard,
Product Realization Validation, Review Handoff Standard, ATGB-05 baseline
preservation, and relevant PR61 evidence/reports. No frozen ATGB corpus edit,
benchmark execution or score claim. Canonical campaign fixtures are not rewritten.

Relevant owners: game/api.py resolution/publication; game/exploration.py outcome
resolution; quarantine and integrated investigation modules context, provider,
validation and fallback; anchored/offline projection modules authority views;
legacy, consequential, persistent and mandatory validators. static/app.js
sendChat posts to /api/chat and reloads state/log. game/storage.py persists.

Changed production files: game/integrated_investigation_narration.py and
game/quarantined_investigation_narration.py. Also added PR62 tests, tooling,
reports/evidence and a NEXT_SESSION entry. game/api.py was already dirty and was
not edited here. No frontend redesign or new gameplay mechanic.

Existing configuration: exact quarantine=1, mode=integrated, live=1, publication=1
with matching campaign_run_id, retries disabled. Existing expression output cap
80 retained. Experiment bound: 8 requests / 15,000 tokens. New repeat-fast-path
flag is process-local and default off. server_config.json records nonsecret flags.
No .env or credential export. Known baseline failures: 3 focused, 9 broader.

Supported categories: discover_clue, investigate, observe, already_searched.
Native inventory-taking remains unsupported. The governed frontier_gate fixture
was copied with private canaries into disposable storage using the PR61 helper.
""")

write('03_PR_PLAY_61_RECONSTRUCTION.md', """# PR61 reconstruction

Sources: original experiment_results.json, replay_results.json, provider ledger,
and quarantine records 001–004. Full original candidates, per-layer traces,
outcomes, publication, provider/HTTP timings and authoritative projections are
preserved in restricted pr_play_61_reconstruction.json. No missing evidence is
reconstructed by inference.

| Action | Deterministic result | Semantic | Legacy hard-valid | Coverage | Combined |
|---|---|---|---|---|---|
| Notice board | discover_clue, true; route disclosed | PASS | true | PASS | PASS |
| Rain barrel | investigate, true; no discovery | FAIL | false after semantic gate | REVIEW_REQUIRED | FAIL |
| Board again | already_searched, false; prior route | PASS | true | PASS | PASS |
| Gate | observe, null; no discovery | PASS | true | REVIEW_REQUIRED | REVIEW_REQUIRED |

Both passing narrations published in the original live capture. Both rejected
ones originally left a provider-disabled stub. PR61's later repaired saved-text
replay published broad deterministic fallback instead. This distinction is
preserved: repaired replay publication is not original live publication evidence.
Four requests consumed 1,926 tokens, HTTP mean 2.601s/max 3.331s.
""")

write('04_FALLBACK_ROOT_CAUSES.md', """# Original fallback root causes

Barrel: persistent validation parsed the adjective phrase “this close inspection”
as an access transition. The active close frame accepted a subject ending in s;
entity_key reduced `this` to `thi`, producing access=closed. This is a FALSE
REJECTION component: no closure was asserted. The semantic FAIL propagated into
legacy hard_valid=false; it was not a separate legacy rejection.

Independently, mandatory coverage found the previously-known route partial:
the candidate shortened it and omitted “mud track.” This is a TRUE REJECTION
under the full authorized-route contract. Fixing only the false persistent
frame would not authorize publication. Invented object surface detail also shows
why the prompt should stop encouraging incidental embellishment.

Gate: semantic PASS and legacy hard-valid=true, coverage REVIEW_REQUIRED on the
known route. Again, “mud track” was omitted. TRUE REJECTION for incomplete
mandatory route coverage, not a demonstrated persistent or legacy failure.

Origins: a validator lexical false frame, generation compressing mandatory facts,
and response assembly repeating the whole scene. The context already supplied
the full route. This cycle changes prompting/assembly, retains all mandatory
facts, and leaves validators unchanged. Original narration and outcome text are
preserved verbatim in restricted machine evidence, not republished to players.
""")

write('05_NON_DISCOVERY_CONTRACT.md', """# Non-discovery contract

Existing projection precedence: known (already_searched), failed (success false),
discovered (new disclosure), otherwise observed. Repeat success=false must not
be mistaken for a failed skill check. Ordinary observation can have success=null.
First ordinary barrel inspection is observed; the second becomes known because
the engine records searched targets even without discovery.

First non-discovery observation and ordinary scene observation share observed;
no new mechanical distinction is invented. Previously-known information has its
own anchors. Public description is optional, not a mechanical grant. Failure
does not authorize stale resolution discoveries. An explicit failed-examination
boundary test uses an unrelated amber sundial.

When observed/failed has prior knowledge, existing anchors could omit the
no-new-result status. The integrated request now adds that mandatory engine
status when absent, retaining every existing required fact. Fallback states the
actual result and never turns completion success into discovery success.

Target wording comes only from a short exact examination target also present in
public visible facts. Raw normalized action IDs and invented player objects do
not grant a label. Unknown forms receive generic wording. Filtering all prior
knowledge by relevance remains outside this change: mandatory anchors are kept.
""")

write('06_FALLBACK_IMPROVEMENTS.md', """# Fallback improvements

The existing integrated fallback leads with action, public target and status,
then verbatim mandatory discovery/prior-information anchors and any explicitly
projected consequences. Optional scene-catalogue observations are omitted.
No second provider call, cache, truth owner or narration subsystem is introduced.

The actual barrel response is 24 words, begins with examining the rain barrel,
states no new clue, and retains the full known route. Board repeat acknowledges
another examination; gate names the gate. Rejected prose/private canaries never
enter this response.

New wording is limited to experimental publication=1. Offline quarantine-only
previews retain their established fallback. Publication still requires existing
gates and matching session identity. Recovery retains PR61's disabled-provider
stub replacement semantics; ordinary validated GM text keeps existing precedence.
This does not rewrite every ordinary-GM fallback in the application.
""")

write('07_NARRATION_PROMPT_CHANGES.md', """# Prompt changes

Removed the uniform 35–65 word target and incidental-sensory-texture allowance.
Routine observations/repeats request one or two concise sentences; discoveries
may need more. Prompt explicitly asks for no-new-clue clarity, omission of
unrelated scene/prior details, and descriptions limited to supplied observations
without invented object condition or environmental state. Full must_communicate
meaning, uncertainty and natural prose remain required.

No large example catalogue, grammatical workaround, new AI validator, output-cap
increase or model change. New discovery candidate: 22 words versus 48. Barrel and
gate: 37/42 versus 61/63. Exact counts in latency.json. This does not establish a
length-latency relationship.

Both new non-discovery candidates remained REVIEW_REQUIRED. Barrel used a
cross-sentence pronoun the bounded coverage recognizer did not bind to the full
route. Gate reformulated a sighting as a route and added unsupported “only lead”
exclusivity. Neither candidate was published. Reliability remains partial.
""")

write('08_PROVIDER_INVOCATION_POLICY.md', """# Invocation policy

ASHEN_INTEGRATED_REPEAT_FAST_PATH is exact-1 and off by default. Inside the
existing integrated hook it skips only a resolved known/repeated outcome with
no newly revealed facts or inventory effects, when live narration would otherwise
run. Records deterministic_fast_path=true and
provider_skip_reason=resolved_repeat_without_new_information. Requests and
generator calls are zero; response shape and fallback marker remain unchanged.

Explicit generators and injected faults are never bypassed. Leaving the flag
unset preserves live repeat exercise. Discoveries, first no-new-information
observations and ordinary scene observations are not automatically skipped.
Unavailable provider and deterministic-only behavior retain existing recovery.
No retry, cache or cross-session information reuse was added.

Turns 3 and 5 skipped requests because resolution marked already_searched,
including the second barrel action without the word “again.” Session-bound
publication remains a separate requirement; no global enablement changed.
""")

lat_table = '\n'.join(
    f"| {r['turn']} | {r['resolution_ms']} | {r['projection_build_ms']} | "
    f"{r['context_and_fallback_build_ms']} | {r['provider_adapter_ms']} | "
    f"{r['validation_ms']} | {r['publication_assembly_ms']} | {r['server_ms']} | {r['http_client_ms']} |"
    for r in latency)
write('09_LATENCY_ANALYSIS.md', f"""# Latency analysis

Milliseconds. None means absent/not applicable, not an inferred zero.

| Turn | Resolution seam | Projection | Context+fallback | Provider adapter | Validation | Publication assembly | Server | HTTP client |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{lat_table}

HTTP mean {m['average_http_ms']:.3f}, max {m['maximum_http_ms']:.3f}. Frontend render
time NOT TESTED. Client-minus-server includes transport and JSON decoding,
not isolated network latency. Resolver timing covers the noncombat seam; normal
orchestration/persistence and uninstrumented work remain in the total.

First adapter interval: 10,846.592ms; admission/completion ledger: 3,453.994ms.
Different scopes: adapter includes setup before admission. Neither is claimed
as isolated network latency. Later adapter intervals: 2,428.251/2,542.266ms.
Concurrent regression makes PR61 comparison uncontrolled; mean/max worsened
despite shorter candidates. Fast paths remove two requests but still take
1.533s/1.721s. No broad optimization or causal speedup claim.

Live context_build_ms includes fallback assembly. Final instrumentation splits
assembly_ms for future runs; no more live calls were made after that telemetry
change or the offline-preview scope fix. With publication=1, final fallback
wording is the same as the captured live run, covered by offline tests.
""")

write('10_BROWSER_ORIGINATED_GAMEPLAY.md', """# Browser evidence — BLOCKED

CUA inventory exposed an in-app browser and no external browser session. Tab
creation at http://127.0.0.1:8762/ timed out waiting for webview attachment.
listTabs returned empty. A second supported attempt with visible=false failed
the same way. Documented troubleshooting was consulted. Trace is recorded in
browser_automation_trace.json. No UI action was submitted.

UI campaign load, input entry, frontend submission/rendering, conversation order,
duplicates, post-fallback input usability and render latency are NOT TESTED.
No prior screenshot substitutes for current browser-originated interaction.
No second frontend or interface redesign was made.

Fallback execution uses urllib over real localhost HTTP to the application's
existing /api/chat?ui_mode=player route. State and all five actions returned 200.
These are HTTP/API actions, explicitly not browser actions. The smallest missing
capability is a working local-app browser webview attachment.
""")

seq = '\n'.join(
    f"| {n} | {r['input']} | {r['quarantine']['authorized_outcome_contract']['resolved_outcome']['status']} | "
    f"{r['quarantine'].get('diagnostic')} | {r['quarantine'].get('provider_requests')} |"
    for n, r in enumerate(rows, 1))
write('11_GAMEPLAY_SEQUENCE.md', f"""# Five-action sequence

Disposable governed frontier_gate campaign; state loaded over HTTP first.

| Turn | Input | Authoritative category | Narration result | Requests |
|---|---|---|---|---:|
{seq}

All five actions returned HTTP 200 in one campaign/scene. One discovery, first
barrel non-discovery, original-target repeat, gate follow-up and barrel follow-up
were exercised. No artificial discovery or additional mechanic was introduced.
No branching-choice or broad RPG playability claim.

Machine evidence: browser_actions.json is a historical filename for **HTTP/API**
capture, not browser evidence. It contains responses and per-turn before/after
authoritative projections. http_client_actions.json records client timing.
final_session.json contains full terminal conversation/action history. Separate
complete raw-session snapshots after every turn were not captured.
""")

write('12_LIVE_PROVIDER_RESULTS.md', """# Live provider results

OpenAI existing expression adapter, gpt-4.1-mini-2025-04-14. Three dispatched
requests, no retries; 1,412 input + 113 output = 1,525 tokens. Budget 8 requests /
15,000 tokens; existing output cap 80 retained. Credentials are not exported.

| Turn | Decision | Input/output/total tokens | Publication |
|---|---|---|---|
| 1 | PASS | 436/24/460 | AI |
| 2 | REVIEW_REQUIRED | 488/41/529 | Deterministic fallback |
| 4 | REVIEW_REQUIRED | 488/48/536 | Deterministic fallback |

Turns 3/5 are zero-call fast paths, not AI acceptance samples. Validated/published
AI 1/1; rejection fallbacks 2; fast paths 2. No favorable-output retries.
Original candidates, complete validation traces and ledger remain restricted
machine evidence. New barrel/gate semantic and legacy layers passed, mandatory
route coverage did not. Gate “only lead” is also unsupported on manual inspection.
Validation PASS is not semantic proof.
""")

responses = '\n\n'.join(
    f"## Turn {n}: {r['input']}\n\n{r['published']}\n\n"
    f"Publication: {'validated live AI' if r['quarantine'].get('player_facing_published') else 'deterministic fast path' if r['quarantine'].get('deterministic_fast_path') else 'deterministic fallback'}."
    for n, r in enumerate(rows, 1))
write('13_PLAYER_FACING_RESPONSES.md',
      '# Published responses\n\nOnly actually published text. Rejected candidates remain restricted.\n\n' + responses)

qtable = '\n'.join('| ' + str(r['turn']) + ' | ' + ' | '.join(str(v) for v in r['scores'].values()) + ' |' for r in quality)
write('14_GAMEPLAY_QUALITY.md', f"""# Quality — PROVISIONAL automated subjective assessment

0 failed, 1 poor, 2 acceptable, 3 good. Not human scoring or an ATGB result.
Responsiveness: 3 <=1s, 2 <=3s, 1 <=6s, 0 >6s; a cycle-local judgment.

| Turn | Relevance | Clarity | Continuity | Naturalness | Concision | Agency | Accuracy | Responsiveness | Recovery | State |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{qtable}

Live discovery is direct and concise. Deterministic output now names the target
and result, with less irrelevant repetition; naturalness remains acceptable
because mandatory prior route text repeats. Agency remains limited: the engine
offers little decision-making depth. Recovery and control-state evidence are
assessed separately from validation. Poor latency scores remain even on PASS.

PR61 whole-scene barrel/gate fallback is provisionally relevance 1, naturalness 1,
concision 0. Updated relevance/concision 3 reflects inspectable published text,
not a green validator result. There is no independent unseen generalization or
composite benchmark score.
""")

faulttable = '\n'.join(
    f"| {x['name']} | {(x['action'].get('quarantine') or {}).get('diagnostic')} | "
    f"{x['action'].get('published_marker')} | {x['continuation'].get('status_code')} | {x['result']} |"
    for x in failures)
write('15_FAILURE_HANDLING.md', f"""# Failure handling

Fault injection, no live calls. Each required case deterministically resolves the
notice-board clue, withholds the candidate, publishes action-focused fallback,
and accepts another action. Full traces: failure_injection_assessed.json and
quarantine_evidence. RuntimeError retains existing VALIDATION_ERROR diagnostics;
timeout records provider_timeout. Both errors are recorded, not successful AI.

| Case | Diagnostic | Marker | Continuation HTTP | Result |
|---|---|---|---:|---|
{faulttable}

All ten required cases PASS. Malformed narration supplies validation-error
recovery; focused PR57 tests additionally inject validator exceptions/decisions.
Take-key is an extra unsupported-action boundary, not a discovery action. No
inventory was added; it correctly differs from a notice-board discovery control.

Fresh fixture NPCs can initialize from absent to runtime defaults. All required
fault post-action authority matches the ordinary no-provider discovery control,
including NPC initialization, clocks and world state. Before/after hash equality
would be an incorrect state-integrity requirement here.
""")

write('16_STATE_AND_CONTINUITY.md', """# State and continuity

Zero protected canonical data/baseline hash changes relative to entry. Storage
is patched to disposable directories before initialization. before_initialization
records absent disposable storage; after_initialization captures authority.
Per-turn projections, final complete session and final authority are preserved.

All five per-action mechanical resolutions and authority projections match the
deterministic control, excluding campaign_run_id. Campaign/player/scene remain
stable within each run. Compared: visited scenes, clues, inventory, equipment,
HP, conditions, NPC runtime, quests, world flags, clocks and combat. The route is
recorded once and retained across repeats/fallbacks. Full terminal session records
conversation/history; intermediate projections are not complete raw-session dumps.

Deterministic changes: turn 1 route disclosure; time_pressure +1 per action in
game/api.py; at pressure 3 the existing game/world.py faction agenda update sets
the same three flags in control and experiment. Normal runtime initialization
and action/conversation history are host changes, never candidate instructions.
All required faults match deterministic first-action authority too.

A distinct session received no experimental marker. Default/off and session
binding regressions are rerun. No narration-to-state write channel was introduced.
State equality does not establish open-ended narration safety.
""")

matrix = [
    ('A Flag disabled', 'PASS', 'Five-action control'),
    ('B Flag enabled', 'PASS', 'Session-bound HTTP run'),
    ('C Discovery', 'PASS', 'Notice-board route'),
    ('D No new information', 'PASS', 'Accurate fallback; AI acceptance remains partial'),
    ('E Repeat', 'PASS', 'Known resolution; zero-call fast path'),
    ('F Follow-up', 'PASS', 'Gate then barrel'),
    ('G Continuity sequence', 'PASS', 'Five HTTP 200 responses'),
    ('H Valid AI publication', 'PASS', 'Turn 1'),
    ('I Invalid rejection', 'PASS', 'Live REVIEW and injected FAIL'),
    ('J Relevant fallback', 'PASS', 'Turns 2/4 and faults'),
    ('K Fast path', 'PASS', 'Turns 3/5'),
    ('L Timeout recovery', 'PASS', 'Injected timeout and continuation'),
    ('M Provider error', 'PASS', 'Injected error and continuation'),
    ('N Validation recovery', 'PASS', 'FAIL/REVIEW/shape and exception controls'),
    ('O Browser submission', 'BLOCKED', 'Attachment timeout twice; zero UI actions'),
    ('P Frontend rendering', 'NOT TESTED', 'No attached tab'),
    ('Q State integrity', 'PASS', 'Per-turn control agreement'),
    ('R Provider accounting', 'PASS', '3 requests / 1525 tokens'),
    ('S Latency measured', 'PASS', 'Measured; speed improvement not established'),
    ('T Gameplay quality', 'PARTIAL', 'Provisional fallback gain; live no-discovery unreliable'),
    ('U Regression', 'PASS' if not focused['new_failures'] else 'FAIL', regtext),
]
(OUT / 'experiment_matrix.json').write_text(json.dumps([
    {'case': a, 'status': b, 'evidence': c} for a, b, c in matrix], indent=2), encoding='utf-8')
write('17_EXPERIMENT_MATRIX.md', '# Experiment matrix\n\n| Case | Status | Evidence / limit |\n|---|---|---|\n' +
      '\n'.join('| ' + ' | '.join(x) + ' |' for x in matrix) +
      '\n\nMeasurement PASS does not imply improved latency. Overall verdict remains B.')

write('18_REGRESSION_RESULTS.md', f"""# Regression results

{regtext}

Historical focused baseline: 741 passed / 3 known failures. PR62 focused selection
adds five tests; one failed-examination boundary runs separately. Coverage spans
PR55–61, authority, geography, mandatory coverage, authorized inventory projection,
persistent effects, isolation, fallback and accounting. H41 and unauthorized
inventory/persistent controls retain rejection. Legitimate paraphrase and
authorized inventory expectations retain their existing assertions.

Initial iteration: 739 passed / 10 failures. Six exposed unintended offline
preview wording changes; fixed by limiting new fallback to experimental
publication. One new test incorrectly required fresh-runtime initialization to
stay identical before/after; corrected to compare full completed authority with
ordinary deterministic control. Existing tests/validators were not weakened.
Three other failures are the recorded baseline. Initial log/XML are preserved.
The earlier target-label allowlist error was fixed before the live run.

Exact commands/failure IDs are in regression_summary_final.json and XML/logs.
The established runner snapshots/restores protected generated historical evidence
that tests touch. Nine broader hard_validation_attempt_1 failures remain unrelated
and unrepaired. No full-suite or independent unseen-generalization claim.
""")

write('19_LIMITATIONS_AND_OPEN_RISKS.md', """# Limitations and risks

- Browser-originated gameplay/rendering unavailable; no new screenshot.
- Only 1/3 live candidates published; both no-new-information candidates fell back.
  Bounded route coverage misses pronoun/paraphrase support. Original adjective/
  access false rejection remains unchanged.
- Mean/max latency worsened; setup and concurrent regression confound comparison.
  No isolated network or frontend-render measurement, no causal speedup claim.
- Mandatory prior anchors still cause repetition. Target extraction handles simple
  English examination forms only; unsupported forms use generic wording.
- Separate fast-path opt-in retains the existing fallback marker and default-off
  semantics. Recovery retains PR61 disabled-provider-stub replacement behavior.
- Per-turn authority projections are not full raw-session snapshots. Pre-init
  capture is absent disposable storage; final full raw session is available.
- Quality scores are PROVISIONAL. Three known focused and nine broader metadata
  failures persist. No broad playability, ATGB score, inventory, travel, NPC change
  or branching-choice claim.
- No critical authority/state failure was observed in this bounded run; equality
  of state does not prove arbitrary narration safe.
""")

write('20_NEXT_SESSION.md', f"""# Next session

Verdict: {m['verdict']}.

Exactly one primary next step: **restore working browser webview attachment and
execute this same five-action restricted investigation sequence through the
existing UI**. Retain session-bound publication, deterministic fallback, provider
budgets and validators. This addresses the smallest missing execution capability;
no frontend redesign or PR-PLAY-63 implementation follows from this recommendation.

Read reports 01, 04, 09, 10, 16, 18, 19 and metrics.json, latency.json,
browser_automation_trace.json, state_integrity.json, failure_injection_assessed.json,
regression_summary_final.json. Rejected candidates stay restricted. No favorable
output retries. Existing dirty work remains. No commit or push.
""")
print('Wrote 20 PR62 reports')
