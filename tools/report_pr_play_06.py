"""Generate the eight scoped reports and explicit review source selection."""
import ast
import difflib
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
O=ROOT/'artifacts/pr_play_06'
R=ROOT/'development/campaigns/product_realization/pr_play_06'


def report(name, title, text):
    (R/name).write_text('# '+title+'\n\nPR-PLAY-06 · 2026-10-28 America/New_York · evidence_scope: structural_only.\n\n'+text.strip()+'\n',encoding='utf-8')


def main():
    results={}
    for group in ['focused','provider','structured','ordinary','opening','world','export','entry_failures']:
        suite=next(ET.parse(O/(group+'.xml')).getroot().iter('testsuite'))
        row={key:int(suite.attrib[key]) for key in ['tests','failures','errors','skipped']}
        row['passed']=row['tests']-row['failures']-row['errors']-row['skipped']
        row['seconds']=float(suite.attrib['time'])
        row['failing_cases']=[c.attrib['classname']+'::'+c.attrib['name'] for c in suite.iter('testcase') if c.find('failure') is not None]
        results[group]=row
    (O/'test_summary.json').write_text(json.dumps(results,indent=2))
    broad=[results[k] for k in ['provider','structured','ordinary','opening','world','export']]
    passes=sum(r['passed'] for r in broad); failures=sum(r['failures'] for r in broad)
    assert results['focused']['passed']==58 and results['focused']['failures']==0
    assert failures==5 and results['entry_failures']['failures']==5
    assert set(sum([r['failing_cases'] for r in broad],[]))==set(results['entry_failures']['failing_cases'])
    measurements=[json.loads(p.read_text()) for p in sorted((O/'measurements').glob('*.json'))]
    inventory=json.loads((O/'prompt_inventory.json').read_text())
    performance=json.loads((O/'performance.json').read_text())
    status=subprocess.check_output(['git','status','--porcelain=v1'],text=True)
    (O/'final_status.txt').write_text(status,encoding='utf-8')
    head=(O/'entry_head.txt').read_text(encoding='utf-8-sig').strip()
    report('01_baseline_and_historical_evidence.md','01 — Baseline and Historical Evidence',f'''
Baseline HEAD: `{head}`. The entry tree already contained extensive modified and
untracked work; `entry_status.txt` records it. This pass changes only the current
opening ceiling/status boundary, targeted tests, offline evidence tools and handoff.
Task-relative diff compares the saved entry files, rather than claiming the full
dirty-tree Git diff as this pass. No commit/push.

Read the Constitution, canonical docs/NEXT_SESSION.md, validation evidence standard,
Product Realization validation, review-handoff standard and PR-PLAY-02–05 reports,
source owners and controls. Requested support/docs/NEXT_SESSION.md is absent; used
the canonical docs/NEXT_SESSION.md named by the Constitution. No authority change.

The historical directory `artifacts/pr_play_05/manual-20261028-214900/` is present.
Its durable ledger confirms one admission/dispatch, SDK retries 0, host retries
disabled; model gpt-4.1-mini-2025-04-14, 26,593 input, 600 output, ceiling 600,
provider_status incomplete, finish max_output_tokens, extracted length 2,275,
JSON false, envelope false, opening accepted false, gameplay committed false.
Host accounting completion_status=completed is distinct from provider completion.
`historical_evidence.json` preserves ledger rows, SHA-256 and original public
snapshots. Historical PowerShell state encoding requires cp1252 fallback.
Before and after public snapshots both show turn 0, campaign_started false and
time_pressure 0; world (including factions), scene and character compare equal.
No original raw response is available; no reconstruction of its contents is claimed.

Primary failure class: implementation/configuration. The earliest demonstrated
constraint is a shared controlled narration ceiling exhausted by the structured
opening. Offline evidence separately demonstrates complete JSON marked incomplete
could previously be committed; this pass closes that status-admission hole.
Baseline tests show both incomplete positive fragments accepted before the change.
The baseline aggregate-output case admitted under 600 and is correctly refused
after reserving 3000. Its initial expected HTTP assertion was corrected to the
existing 409 budget-refusal contract. The historical rich fixture remains rejected;
that baseline failure was retained as an explicit negative control.

Authority: limited implementation, no live/provider-connectivity authority. Existing
opening completion, validation, rollback, repetition/concurrency controls, admission,
retry suppression, diagnostics, hidden-information and deterministic state owners
are preserved. 257 protected data/experiment files and inventory remain unchanged.
''')
    table='\n'.join(f"| {m['name']} | {m['serialized_output']['characters']} | {m['serialized_output']['estimated_tokens_chars_div_4']} | {m['structural_characters_including_escaping_whitespace']} | {m['narration']['characters']} | {m['declarations']['characters']} | {m['declaration_count']} | {m['host_status']} |" for m in measurements)
    report('02_structured_output_requirements.md','02 — Structured Output Requirements',f'''
The provider must emit JSON with declared_claims (list) and narration (nonempty
string). Each declaration is audited against gm_resolution_decision claims,
relation/authority and authored corpus; parsing alone grants no acceptance.
The scene_opening response must still satisfy opening-specific completion and
final emission gates. Empty declarations are legal for these existing accepted
controls; no declaration requirement was weakened. No schema change.

| Fixture | Serialized chars/ASCII bytes | Estimated tokens | Envelope/escaping chars | Narration chars | Declaration chars | Declarations | Host HTTP |
|---|---:|---:|---:|---:|---:|---:|---:|
{table}

All token values are ceil(characters/4) ESTIMATES. tiktoken is unavailable locally;
no tokenizer/model download was attempted. Synthetic SDK usage fields deliberately
use these estimates to exercise accounting; they are not actual provider usage.
Raw fixtures, measurements, requests and lifecycle observations are included.

Reuse: MARKET_NARRATION and VALID_NARRATION from PR-PLAY-04; typical text from
test_start_campaign_api; declarations use that test's claim projection. Rich and
over_600 reuse the existing _decl helper from structured-realization tests, with
the same authorized narration and eight real source_claim_id references. They
are deliberately the same response representation under two matrix labels,
not independent samples. Richness here is declaration detail. Multi-detail, NPC
and declaration cases also share the existing gate fixture; no new lore.

Smallest accepted sampled output: 190 chars (~48 tokens); market opening with
three explicit declarations: 626 chars (~157). These are fixture minima, not a
proof of the mathematically shortest valid opening. The serialized empty shell
{{"declared_claims": [], "narration": ""}} occupies 38 chars and is invalid until
nonempty adequate scene text exists. Eight short declarations plus narration
occupy 2142 chars (~536); fuller supported declarations occupy 3726 (~932).
Historical verbose 1258-char narration parses but fails gameplay authority; see
historical_rich_rejection.json. More tokens do not make that fixture acceptable.

Practical allowance: 3000, about 3.2x the richest sampled estimate, accommodates
JSON keys/IDs, declarations, narration and serialization/generation variability.
It is a bounded trial hypothesis, not proof of live adequacy or token-exact fit.
The output allowance does not require longer narration; prompts/style unchanged.

Production source map (all functions retain existing ownership):

| Boundary | Module/function | Input → output | Relevant configuration | Existing/new tests |
|---|---|---|---|---|
| Start | game.api.start_campaign / _start_campaign_after_admission | player Request + initialized stores → one opening result/failure | request gate, persistence lock, isolated ASHEN_DATA_DIR | PR-PLAY-04 matrix, start_campaign_api |
| Opening seed | game.api._opening_scene_normalized_action_and_resolution / _build_opening_scene_resolution | scene + internal bootstrap → scene_opening resolution | existing scene content | PR-PLAY-04, opening seam |
| Prompt | game.gm.build_messages / collect_narration_context_call_kwargs; game.prompt_context.build_narration_context | state + resolution → system/user JSON messages | existing prompt profile/policy | captured two-scene inventory, AST identity |
| Response type | game.api._derive_response_type_contract_for_turn / _attach_response_type_contract_to_resolution | action/resolution → required scene_opening | response_type_contract.required_response_type | opening/type tests |
| Realization | game.gm_resolution_decision.audit_realization_envelope_against_decision | declarations + decision + corpus → authority audit | unchanged structured realization contract | structured envelope suite |
| Provider request | game.gm.call_gpt; game.provider_budget.admit_request / RequestAttempt.dispatch | messages/route → admitted SDK kwargs or refusal | existing model, retries, aggregate reservations | PR-PLAY-02, accounting, new budget selection |
| Limit | game.gm._requested_response_type_from_messages / _opening_max_output_tokens | host response contract/env → 3000 opening allowance | ASHEN_OPENING_MAX_OUTPUT_TOKENS 1..4096 | new bounded/config tests |
| Extraction | game.gm._extract_provider_response_text | SDK output_text or content segments → text + extraction observations | diagnostics flag only affects recording | PR-PLAY-05 native SDK/segment controls |
| Parsing | game.gm._safe_json; structured_player_output.classify_model_output | JSON/fenced JSON → normalized response or contract failure | existing provider envelope selection | PR-PLAY-05 + structured suite |
| Envelope/acceptance | immutable_valid_response.run_preserve_if_valid; game.api._opening_response_rejection | parsed/audited opening → accepted seal or explicit failure | unchanged opening/type/authority gates | PR-PLAY-04, invalid/incomplete controls |
| Commit | game.api._complete_opening_turn_persistence_like_chat / _restore_opening_baseline | accepted opening + baseline → persisted single progression or rollback | existing storage/world/faction owners | PR-PLAY-04 concurrency/repeat/retry/persistence |

The map names current functions; historical PR-PLAY-03 line numbers are not used
as current source locations. Raw current source snapshot is in the review ZIP.
''')
    report('03_output_budget_implementation.md','03 — Output-Budget Implementation','''
600 originates in game.gm.call_gpt via ASHEN_NARRATION_MAX_OUTPUT_TOKENS, default
600. It is operation-shared, environment-configurable and not model-specific.
Before this pass it was sent only when provider accounting was active; outside
accounting ordinary calls had no explicit max_output_tokens. No documented
historical rationale for choosing 600 was found; do not invent one.

The existing host-authored response_type_contract now selects an opening-only
cap through _requested_response_type_from_messages and _opening_max_output_tokens.
Default 3000; ASHEN_OPENING_MAX_OUTPUT_TOKENS accepts 1..4096 and fails before
admission on malformed/out-of-range values. Opening calls always explicitly send
this bound, with or without accounting. Ordinary calls retain 600 (or their
existing override) when accounting is active, and the existing absent-cap behavior
otherwise. No model or response-format option changes.

The selected cap is reserved by the existing atomic admission owner before SDK
construction and passed unchanged to Responses.create and the completion/diagnostic
records. Aggregate request/input/output/total budgets remain authoritative. SDK
and host retries stay disabled under the existing controlled flags. No new call,
retry or larger-budget retry path was added. The manual aggregate ceilings stay
6 requests / 200000 input / 20000 output / 220000 total.

An opening with explicit status incomplete/failed/cancelled/queued/in_progress now
fails using existing _structured_contract_failure after normal parsing diagnostics.
Complete JSON cannot override an explicitly unfinished provider response. Missing
status retains SDK compatibility and still requires all existing validation.
Diagnostic classification provider_not_completed distinguishes valid JSON on an
unfinished response; malformed exhausted responses retain json_parse_failure plus
provider status/finish/limit fields. Final opening_outcome records rejected commit.

Cost exposure: default maximum per opening rises by 2400 output tokens, 5x the
former 600 ceiling. At the configurable hard maximum, exposure is 4096 per request.
Aggregate ceilings do not increase: six 3000-token openings could reserve/use
18000 output tokens if independently authorized, within 20000; other usage reduces
remaining room. Six 4096-token reservations cannot all pass a 20000 aggregate
ceiling. This is not cost-neutral. No monetary quote or current pricing claim.
''')
    component_tables=[]
    for inv in inventory:
        rows='\n'.join(f"| {c['component']} | {c['characters']} | {c['estimated_tokens_chars_div_4']} | {c['class']} |" for c in inv['components'])
        component_tables.append(f"## {inv['fixture']}\n\nSystem {inv['system']['characters']} chars; user {inv['user']['characters']} chars.\n\n| Component | Chars | Estimated tokens | Class |\n|---|---:|---:|---|\n"+rows)
    report('04_opening_prompt_inventory.md','04 — Opening Prompt Inventory','''
Current production messages captured immediately before the synthetic SDK dispatch
for frontier_gate and market_quarter. Historical 26593-token input is measured
provider evidence; current sizes below are reconstruction character counts and
chars/4 estimates, not a replay of original provider tokens. No original full
request was retained in the October 28 package.

A required: opening/scene/character/campaign identity, structured response and
declaration contracts, authorized facts, visibility/hidden protection, rules,
state-authority and mechanical resolution. B conditional: NPC/social/combat/clue,
lead and memory context when relevant; retain because opening can include NPCs.
E uncertain: overlapping response_policy, decision, recipe, plan, world views,
turn packet/session summaries. Large size alone supplies no removal authority.
The system includes response contract/structured instructions; user.instructions
and response_policy supply rules/authority; scene/opening realization and clue
views supply visible and protected knowledge; character supplies identity; world
and world_state carry distinct views; decision/recipe/plan convey claims and
completion requirements. Inventory is top-level disjoint serialization size;
JSON separators/outer keys add overhead. Do not sum overlapping nested views as
independent additions to the system/user total.

C exact repeated-string candidates are enumerated with both source paths and
lengths in prompt_inventory.json. Their location may convey independent validation
or authority semantics. No major component was established safe to remove. D
unused: none proven. Exact duplicate values do not prove redundant instructions.
No reductions proposed or implemented. Thus no removal loses an alternative
authority source, and no fabricated removal evidence is supplied.

Before/after: system 9568/9568 chars for both fixtures; frontier user
102796/102796; market user 79071/79071. Reduction 0 chars / 0 estimated tokens.
AST comparisons prove build_messages, context collection, parser and envelope
selection plus all module-level contract assignments unchanged. Prompt-integrity
matrix preserves scene, character, NPC, visible facts, hidden protection,
declarations, gameplay authority and opening instructions for both scene fixtures.
This is structural preservation evidence, not a semantic model test.

'''+'\n\n'.join(component_tables))
    report('05_deterministic_validation.md','05 — Deterministic Validation','''
58 focused checks pass: 19 new + all 18 PR-PLAY-04 + 21 PR-PLAY-05. SDK/network
provider access is synthetic or blocked by the existing live-model guard.

| Control | Result/evidence |
|---|---|
| B1 minimal | market three-declaration opening accepted; measurements/minimal.json |
| B2 typical | existing gate opening accepted; measurements/typical.json |
| B3 rich | full existing declaration representation accepted; measurements/rich.json |
| B4 former-ceiling excess | 3726 chars/~932 estimated tokens accepted under requested 3000; synthetic usage only |
| B5 ordinary | accounting 600; no-accounting absent-cap compatibility; explicit opening override 2800 tested |
| B6 incomplete at ceiling | valid JSON with incomplete/max_output_tokens rejected; content_filter also rejected; truncated JSON rejected |
| B7 invalid JSON | malformed/missing/incomplete/empty shapes rejected with rollback |
| B8 provider exception | one dispatch failure, no gameplay commit; later user retry succeeds once |
| B9 aggregate exhaustion | 1000 aggregate output ceiling refuses 3000 reservation, HTTP 409, zero admissions/dispatch, state equal |
| B10 failed then successful | retained failure/failure/success and exception/success tests commit once |

The response fixture over_600 uses existing full declaration fields, without added
lore or whitespace inflation. Its token size is estimated; neither estimated SDK
usage nor host acceptance proves a live model can finish within 3000.

Retained PR-PLAY-04 controls cover accepted opening exactly one turn/time/faction
increment, rejected opening no progression, retryability, repeated Start 409,
concurrent Start serialization (one 200/one 409), chat-start parity, pre-dispatch,
pipeline and save exceptions. PR-PLAY-05 controls compare persisted JSON values and
file inventory. Existing saved_at/last_saved_at, addressability debug traces and
empty session_log materialization are bookkeeping; byte identity is not claimed.
Raw before/after gameplay snapshots and lifecycle/diagnostic rows accompany the
new fixture cases, aggregate refusal, incomplete statuses, repeated/retry/concurrent
controls and retained diagnostic negative controls.

Prompt integrity: unchanged producer/contracts plus before/after component sizes
on gate and market fixtures; zero reductions. Hidden-protection strings and
authorized claim IDs remain in their established request owners. No broad gameplay
quality or independent generalization claim. Frozen benchmark was not rerun.

Provider budget controls: one dispatch per synthetic initial generation; no extra
provider operations, admission ceilings, six-request concurrency and SDK max_retries
0 remain enforced. Aggregate usage uses completed lifecycle rows only; diagnostic
copies are not summed. Existing PR-PLAY-05 ledger reconciliation assertions pass.
Opening ceiling 3000 is visible in request, completed record and diagnostics.
Complete JSON on incomplete status retains JSON/envelope observations but fails
final host acceptance/commit; no automatic retry. Historical rich unsupported
claims continue to fail rather than gaining authority from a larger allowance.
''')
    rows='\n'.join(f"| {k} | {results[k]['passed']} | {results[k]['failures']} | {results[k]['seconds']:.3f} |" for k in ['focused','provider','structured','ordinary','opening','world','export'])
    report('06_regression_and_performance.md','06 — Regression and Performance',f'''
| Bounded group | Passed | Failed | Pytest seconds |
|---|---:|---:|---:|
{rows}

Broader total: {passes} passed / {failures} failed. Focused 58 passed is separate;
the 57-pass non-HTTP subset is overlapping evidence, not added to totals. Every
driver group is bounded at 90 seconds. Commands, run records, XML and text logs
are retained. Full repository suite and live benchmark not run.

Five failures are preexisting, reproduced individually with the saved entry
game.gm source using tests.helpers.pr_play_06_entry_source: stale accounting source
attestation; raw-chat stew-price assertion; three rich opening emission preservation
assertions. Identical failing IDs match the broader runs. Earlier PR-PLAY-05
reports independently retain the same families. No unrelated repair or updated
attestation. New regressions: none observed in completed scope. Unresolved new
failures: none. Those preexisting player-facing limitations justify verdict B.

Sandbox attempts stalled at the placeholder HTTP check and raw-chat check; capped
at 90 seconds. Bounded outside-sandbox reruns complete, including all 58 focused
tests. No provider access permitted. A prior unbounded-shell focused invocation
was interrupted after stall; it is not counted as a completed test result.
No claim that a sandbox timeout is a product pass or a product failure.

Regression scope includes initialization, opening/structured parsing and final
response preservation, provider dispatch/accounting/retries, rollback, world/faction
progression, ordinary narration/conversation/authority and R2 interpretation/participant
grounding. This is a relevant slice, not all ATGB scenarios or statistical reliability.

Prompt size change: zero for both recorded fixtures. Local new contract parse and
setting selection: median {performance['median_ms']:.4f} ms, maximum
{performance['max_ms']:.4f} ms over 200 iterations. This measures only the added
local selection work on a ~103k-character user payload, not network/UI latency.
No latency or monetary cost-neutral claim. Protected integrity: all 257 baseline
data/experiment files and file inventory match. Frozen ATGB content unchanged;
its source attestation remains stale and fail-closed.
''')
    report('07_live_test_readiness.md','07 — Live-Test Readiness','''
Deterministic configuration readiness established, with conditional limitations:
token estimates rather than exact model tokenization, unproven model generation,
and retained unrelated rich-emission/ordinary-dialogue defects. Provider completion
and valid JSON remain uncertain until an authorized operator trial. No live calls
or connectivity diagnostics were performed here.

The exact executable Windows PowerShell procedure is the accompanying
PR_PLAY_06_LIVE_OPENING_TEST.txt, included in full in the review package. It uses
timestamped isolated frozen seed copies, a shared active-test-path artifact to
discover $playRoot in window two, one worker/no reload, SDK and host retries zero,
six admissions, unchanged aggregate ceilings, existing usage journal and generation
diagnostics, explicit 3000 opening/600 ordinary assertions, before/after HTTP
snapshots and data copies, evidence ZIP export, and process-local cleanup.
All seven extracted command blocks parse in PowerShell; manual_syntax.json records
zero syntax errors. No commands were executed as a live test. HTTP state reads
have 15-second timeouts. No placeholders or manual long-path substitution.

One user-initiated Start only, after New Campaign and before-state capture. Stop
after success OR failure, unexpected retry, budget refusal, fallback, or 60-second
unresponsive UI; no gameplay continuation, automatic retry or provider probe.
If an HTTP snapshot times out, record absence and export files/ledger after server
stop. A pending or interrupted call remains unknown, never inferred successful.

Success requires completed provider status, valid JSON/envelope, displayed opening,
campaign_started true and exactly one authorized progression, with no retries.
Failure requires explicit rejection, unchanged gameplay values, completion and
validation diagnostics, retained accounting and exportable evidence. Compare
bookkeeping separately. One success establishes one functional sample only.
External review must accept this package before the user runs that procedure.
''')
    confirmations='''No live provider calls. No provider connectivity diagnostics. No model changes.
No response-schema changes. No additional provider operations. No automatic retries.
No unauthorized gameplay-state mutations. No new persistent gameplay structures.
No experimental PR-EG integration. Frozen ATGB baseline unchanged. No secrets included.
No commit or push performed.'''
    report('08_final_verdict_and_handoff.md','08 — Final Verdict and Handoff',f'''
**B — Conditionally ready.** The primary bounded repair is implemented: openings
request 3000 output tokens (hard configurable bound 4096), ordinary controlled
narration remains 600, and explicitly unfinished responses fail regardless of
whether a JSON fragment parses. Admission/aggregate ceilings, model/schema,
authority, retries, diagnostics and rollback remain intact. No prompt reduction.

58 focused checks pass; broader {passes} pass and five confirmed preexisting failures.
All five reproduce against saved entry GM source. 257 protected files and inventory
match. Structured measurements and two-scene prompt inventory support a bounded
trial. The representative rich declaration fixture is ~932 estimated tokens,
not evidence that live generation will complete in 3000. Exact tokenizer absent.

Original live reproduction is NOT rerun or claimed repaired in provider behavior.
Implementation/host acceptance is established deterministically. Existing fixture
variations are related synthetic controls; no held-out generalization or gameplay
benchmark claim. Three old verbose-rich emission assertions, stale source attestation
and one ordinary conversation assertion remain. No unrelated fixes.

Should the user run a live test? Only after external review accepts this conditional
package, using the supplied procedure for one Start and immediate export/stop.
Recommended next action: external review of this ZIP and the opening-budget/status
diff. That next action is not implemented. No further live attempt is authorized by
unused admission/token capacity. Stop after packaging and await external review.

{confirmations}
''')
    # Task-relative source diff and snapshots avoid attribution of existing dirty work.
    paths=['game/gm.py','tests/test_pr_play_05_diagnostics.py','tests/test_pr_play_06_opening_budget.py',
           'tests/helpers/pr_play_06_entry_source.py',*['tools/'+p.name for p in ROOT.glob('tools/*pr_play_06*.py')]]
    diff=[]
    for path in paths:
        base=O/'entry'/Path(path).name
        old=base.read_text(encoding='utf-8-sig').splitlines(True) if base.exists() else []
        new=(ROOT/path).read_text(encoding='utf-8-sig').splitlines(True)
        diff.extend(difflib.unified_diff(old,new,fromfile='entry/'+path,tofile='current/'+path))
    (O/'source_diff.patch').write_text(''.join(diff),encoding='utf-8')
    # All selected paths are explicit task-owned artifacts; no environment files.
    support=[p.relative_to(ROOT).as_posix() for p in sorted(R.glob('*')) if p.is_file()]
    support += paths+['docs/NEXT_SESSION.md']
    support += [p.relative_to(ROOT).as_posix() for p in sorted(O.rglob('*'))
                if p.is_file() and p.suffix in {'.json','.jsonl','.txt','.xml','.patch','.py'}
                and p.name not in {'review_config.json','package_verification.json'}]
    config={
        'campaign_id':'pr_play_06','campaign_name':'PR-PLAY-06 — Structured Opening Output Budget and Contract Efficiency',
        'campaign_date':'2026-10-28','purpose':'Bounded offline repair; no live/connectivity authority. Stop after ZIP.',
        'objective_status':'B — Conditionally ready',
        'executive_summary':f'Opening-only 3000-token default (hard configurable bound 4096), explicit incomplete-status rejection. Ordinary controlled output 600; aggregate limits and retries unchanged. 58 focused pass; {passes} broader pass / 5 entry-reproduced failures. No prompt reductions. Structural-only evidence; live adequacy unproven. '+confirmations,
        'primary_report':'development/campaigns/product_realization/pr_play_06/08_final_verdict_and_handoff.md',
        'supporting_files':[{'path':p,'role':'source' if p in paths else 'evidence',
                             'why':'PR-PLAY-06 scoped source, report, manual or deterministic evidence.'} for p in dict.fromkeys(support)],
        'changes':{'production':['Opening-specific bounded setting and unfinished-opening status rejection in existing GM owner.'],
                   'validation':['19 new deterministic tests; existing diagnostic fixture ceilings updated.'],
                   'tooling':['Offline bounded test driver, measurement, inventory, manual/report preparation.'],
                   'documentation':['Eight reports, executable operator procedure, canonical session handoff.'],
                   'generated_artifacts':['Explicit review ZIP, provenance manifest, snapshots, source diff and measurements.']},
        'testing':{'focused':'58 passed, zero live calls.', 'broader':f'{passes} passed / 5 confirmed preexisting failures.',
                   'full_suite':'Not run; bounded relevant slices only.',
                   'runtime_validation':'Synthetic SDK responses through existing endpoint/acceptance/persistence path; local HTTP control passed.',
                   'model_runtime_boundary':'No provider generation. Token estimates; 3000 is a defensible trial allowance.',
                   'new_regressions':'None observed in completed scope.',
                   'pre_existing_failures':'Five matching IDs reproduced with saved entry GM source; see entry_failures.xml.'},
        'self_contained_review_test':'ZIP entries/provenance hashes, eight reports, source diff, required manual and verdict checked by package finalizer.',
        'decisions_requiring_human_review':['External reviewer to accept/redirect conditional readiness before any one-Start operator test.'],
        'known_problems':{'campaign_specific':['Exact tokenizer unavailable; live structured generation remains unproven.'],
                          'pre_existing':['Three verbose-rich emission assertions, stale source attestation and stew-price conversation assertion.']},
        'does_not_prove':['Live success, statistical reliability, independent generalization or gameplay benchmark improvement.',
                          'Cost neutrality: opening ceiling rises 600 to 3000 (+2400).'],
        'recommended_next_step':'External review of this package. Do not run another live opening until accepted.',
        'configuration_source':'artifacts/pr_play_06/review_config.json'}
    (O/'review_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__': main()
