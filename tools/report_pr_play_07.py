"""Generate bounded PR-PLAY-07 reports and explicit review selection; offline only."""
from pathlib import Path
import json
import subprocess
import hashlib
import difflib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
O = ROOT / 'artifacts/pr_play_07'
R = ROOT / 'development/campaigns/product_realization/pr_play_07'


def write(name, value):
    (O / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def report(name, title, body):
    (R / name).write_text('# ' + title + '\n\nPR-PLAY-07 · 2026-10-29 America/New_York. Synthetic-provider evidence only.\n\n' + body.strip() + '\n', encoding='utf-8')


def main():
    results = {}
    for group in ['focused_final', 'provider_final', 'entry_accounting', 'structured_direct', 'ordinary_direct', 'world', 'export']:
        suite = next(ET.parse(O / (group + '.xml')).getroot().iter('testsuite'))
        row = {k: int(suite.attrib[k]) for k in ['tests', 'failures', 'errors', 'skipped']}
        row['passed'] = row['tests'] - row['failures'] - row['errors'] - row['skipped']
        row['failing_cases'] = [c.attrib['classname'] + '::' + c.attrib['name'] for c in suite if c.find('failure') is not None]
        results[group] = row
    assert results['focused_final']['failures'] == 0
    assert results['entry_accounting']['failures'] == 1
    passes = sum(v['passed'] for k, v in results.items() if k != 'entry_accounting')
    write('test_summary.json', results)
    matrix = []
    table = '| Fixture | Structural | Semantic / opening reason | Expected / actual acceptance | Commit | Result |\n|---|---|---|---|---|---|\n'
    for n in range(1, 13):
        value = json.loads((O / f'matrix/S{n}.json').read_text())
        provider, outcome = value['provider'], value['outcome']
        row = {'fixture': f'S{n}', 'structural': provider['classification'], 'semantic': outcome.get('semantic_classification'), 'reason': outcome.get('rejection_reason'), 'semantic_reasons': outcome.get('semantic_reasons'), 'acceptance': outcome['opening_accepted'], 'gameplay_commit': outcome['gameplay_committed'], 'expected': value['expected_accepted'], 'actual_http': value['status'], 'pass': value['pass']}
        matrix.append(row)
        table += f"| S{n} | {row['structural']} | {row['reason'] or 'valid opening'} | {row['expected']} / {row['acceptance']} | {row['gameplay_commit']} | PASS |\n"
    write('semantic_acceptance_matrix.json', matrix)
    (O / 'semantic_acceptance_matrix.md').write_text(table, encoding='utf-8')
    decisions = '''| Condition | Boundary / classification | Evidence category |
|---|---|---|
| Bad JSON, missing required claims list, empty narration, nested envelope | gm._safe_json -> structured_contract_failure -> API rejection | A: correct structural rejection, S3/S4 |
| Complete JSON with explicit provider incomplete/failed status | gm.call_gpt -> provider_opening_not_completed | A: incomplete operation, PR06 controls |
| Grounded valid opening; optional proposal/NPC fields absent | hard valid -> initial_generation; opening predicate passes | Accepted, S1/S5/S8 |
| Provider metadata says fallback but actual content satisfies contract | Unknown metadata discarded by parser; no host safe provenance | Accepted, S6; arbitrary metadata grants no authority |
| Host accepted_response provenance or authorization is safe_nonresolution | API rejects before persistence even with plausible prose | A: actual host safety result is disqualifying; separate metadata control |
| Model emits literal generic answer inside valid JSON | May seal initial_generation; API text-marker check rejects | A: model nonresolution, S2 |
| Unauthorized state changes, hidden disclosure or invalid consequential realization | immutable _check fails; no valid recovery -> _terminal_after_fidelity -> safe provenance | A when audit is correct; S9 proves unauthorized change case |
| Missing consequential declaration or unmatched source claim | Decision/claim audit can fail despite a structurally valid list | A if obligation applies; empty list alone is legal. S12 audit rejects rich text |
| Alleged valid opening rejected by unrelated ordinary-action rule | Could produce same terminal provenance | B only if content satisfies opening authority; not established historically |
| scene_opening response type alongside unresolved/answer/referent-ambiguity contract | Conflicting guidance in projected resolution contract/answer recipe | C: residual conflict observed; historical influence unknown |
| Historical structural success then safe_nonresolution without original output/reasons | Same sequence compatible with correct rejection, incorrect rejection or guidance conflict | D: insufficient evidence; no cause selected |
| Empty, generic, question-only or non-scene final text | candidate_satisfies_scene_opening_contract rejects | A: opening-specific failure |
| Budget refusal, disabled provider, fast fallback | API failure, no successful opening commit | A: generation unavailable, no retry |
| Repeated Start after successful opening | already_started 409 before provider dispatch | Correct duplicate prevention, S10 |
'''
    (O / 'classification_decision_table.md').write_text(decisions, encoding='utf-8')
    head = (O / 'entry_head.txt').read_text().strip()
    report('01_historical_evidence_and_baseline.md', '01 — Historical Evidence and Baseline', f'''
Baseline HEAD `{head}`. Extensive dirty/untracked production, normal gameplay,
governance and historical evidence predates this pass; see entry_status.txt.
Task-relative source diff uses saved dirty entry bytes, not HEAD alone. No commit/push.
Read Constitution, NEXT_SESSION, validation evidence, Product Realization validation,
review-handoff, state authority/feature-lane guidance and relevant PR-PLAY-02–06
reports/source/tests. No applicable AGENTS.md was discovered.

Historical ZIP exists: artifacts/pr_play_06/manual-20261029-201037-EVIDENCE.zip.
Its hash, inventory, ledger and normalized state comparison are in this pass's artifacts.
One admitted/dispatched request; SDK retries 0, host retries disabled. Returned model
gpt-4.1-mini-2025-04-14; input 26,593, output 1,370, total 27,963, ceiling 3,000.
Provider status completed, extracted length 5,570, JSON true, envelope true, structured
validation true; recognized declared_claims, narration, player_facing_text. Provider
classification accepted_structured_response; opening_outcome opening_rejected,
reason/recovery safe_nonresolution, gameplay_committed false.

The old opening_outcome structured_validation_result=false represented final acceptance,
not the earlier parser result. This diagnostic conflation is repaired. Before/after
persistent payloads show campaign_started false, turn 0, all clocks 0, active scene
frontier_gate. World including factions, character, combat, campaign, conditions and
transcript compare equal. Timestamps/debug bookkeeping are separate from gameplay.
ZIP screenshots folder is empty, notes are empty, after_state.json is absent; persisted
before/after copies exist. Task screenshot observations were not independently inspected.

Complete generated text and first semantic-rejection reasons are absent. Exact semantic
reproduction is impossible. No content was invented and no provider/connectivity call
was made. Historical primary failure class stays unresolved. UI erasure and diagnostic
gaps are separately confirmed implementation defects, not proof of historical cause.
''')
    lifecycle = '''| Stage | Module / function | Input -> output | Contract / failure behavior | Tests |
|---|---|---|---|---|
| 1 POST admission | game/api.py start_campaign, _start_campaign_after_admission | Request/ui_mode + saved state -> opening scope or 409/503 | Mode, preflight, budget, empty transcript/latch; one persistence lock; refusal before dispatch | PR04 admission/repeat/concurrency |
| 2 Opening bundle | game/api.py _opening_scene_normalized_action_and_resolution, _build_opening_scene_resolution | Active scene + internal bootstrap -> normalized type/kind scene_opening | Engine opening flags; no fabricated player action; tracked exceptions rollback | PR04, start_campaign_api |
| 3 Response type | game/api.py _run_resolved_turn_pipeline; game/response_type_gating.py derive_response_type_contract | Action/resolution -> scene_opening, decision/recipe/policy | Opening overrides question heuristics; strict_answer_expected false; failure grants no commit | S7, response-type tests |
| 4 Presentation plan | game/opening_scene_realization.py build_opening_scene_realization, merge_opening_instructions; game/api.py _build_gpt_narration_from_authoritative_state | Visible facts/scene/decision -> grounded plan/prompt | Authorized presentation, hidden/consequential authority retained; no synthetic opening success | opening_scene_realization, scene_opening_narrative_plan |
| 5 Request/envelope | game/gm.py build_messages, _provider_response_contract_from_payload, call_gpt | Payload -> structured_realization messages + 3000 request | Model/schema unchanged; narration_only only for eligible incidental dialogue | PR06 and structured suites |
| 6 Dispatch/completion | game/provider_budget.py admit_request, RequestAttempt; game/gm.py call_gpt | One Responses request -> metered SDK response/exception | Atomic admission, controlled zero retries, aggregate budgets; failure accounted without added requests | PR02, provider accounting |
| 7 Extraction | game/gm.py _extract_provider_response_text | SDK response -> output_text or message segments | No object repr; empty/extraction failures distinguished | PR05 extraction/native SDK |
| 8 JSON/envelope | game/gm.py _safe_json; game/structured_player_output.py classify_model_output | Text -> normalized GM/realization_envelope or rejection | Claims list + nonempty narration; no nested envelope; rejection flags survive | PR05, structured direct |
| 9 Structural observation | game/gm.py _generation_response_diagnostic; game/provider_budget.py record_generation_diagnostic, capture_opening_response | Text/parser/SDK status -> shape classification + opt-in parsed evidence | accepted_structured_response grants no semantic authority; explicit unfinished status fails; capture failure cannot change acceptance | Capture controls, PR06 |
| 10 Semantic interpretation | game/api.py narration catch-all -> game/immutable_valid_response.py run_preserve_if_valid._check, validate_generated_response | Text/claims + decision/authored corpus -> hard validity/reasons | Decision facts, disclosure, attribution and realization authority enforced | S9/S12, immutable/social regression |
| 11 Nonresolution selection | game/immutable_valid_response.py _terminal_after_fidelity, safe_nonresolution, seal_accepted_response, _finish | Rejected candidate/no authorized recovery -> sealed host fallback | regenerate=None here; fallback never grants opening success; original reasons retained | S9/S12, immutable boundary |
| 12 Opening acceptance | game/api.py _complete_opening_turn_persistence_like_chat, _opening_response_rejection; game/final_emission_validators.py candidate_satisfies_scene_opening_contract | Final GM/meta/text/required type -> None or reason | Reject structured/provider/safe/generic/inadequate scene; 422 failure, budget 409, no gm_output | S1–S12, PR04 |
| 13 Commit/rollback | game/api.py persistence completion, _OpeningScope.close, _restore_opening_baseline | Eligible result + baseline -> one turn/log/start latch or restored gameplay | Engine owns world/factions; restore session/world/combat/transcript on failure; diagnostics outside saves | PR04 persistence/retry/concurrent, world |
| 14 API/UI | game/api.py _opening_failure_response; static/app.js Start handler, loadState/loadLog | 200/422/provider/transport failure -> narration or visible feedback | No auto-retry; failure state-only refresh; safe catches; state controls button | U1–U7, network/JSON controls |
'''
    (O / 'opening_source_map.md').write_text(lifecycle, encoding='utf-8')
    report('02_opening_execution_and_classification_map.md', '02 — Opening Execution and Classification Map', lifecycle + '''
The exact transition is AFTER parsing/structural diagnostics: API's unresolved/no-
interlocutor catch-all invokes run_preserve_if_valid; _check can reject structured
content. With regenerate=None and no authorized recovery, _terminal_after_fidelity
calls safe_nonresolution, seal_accepted_response stores PROVENANCE_SAFE, _finish seals
delivery. API reads provenance and rejects. This is application-assigned provenance,
not an enum emitted by the provider. S9/S12 reproduce that path. S2 instead retains
initial_generation for the provider's literal fallback and fails the API marker check.

Producer/consumer inventory: artifacts/pr_play_07/classification_inventory.txt.
Producers include safe_nonresolution and host terminal safety/sealing; consumers include
API rejection/recovery, immutable final-delivery enforcement, emission/provenance audits
and ordinary unresolved handling. lifecycle_applies excludes scene_opening; the API
catch-all still explicitly preserves valid structured openings. PR04 blocks it only
when structured failure is already set. The semantic validator receives resolution kind
and decision authority but no required_response_type parameter. It inspects content,
claims, disclosure and attribution; the opening predicate is separate. Empty narration
fails earlier in parsing. Missing authoritative answers, unsupported actions, unresolved
interpretation and invalid realization are distinct causes that safe provenance can hide.

''' + decisions)
    report('03_semantic_contract_analysis.md', '03 — Semantic Contract Analysis', '''
Structural validity: structured_realization JSON, declared_claims list, nonempty narration,
supported envelope, no nested wrapper. Temporary player_facing_text compatibility grants
no authority. Empty declarations are legal when no declaration-requiring claim is made.

Semantic validity: narration survives decision/claim/proposition, authored world truth,
hidden-disclosure and attribution checks, then satisfies the existing opening predicate:
nonempty, scene-establishing, no generic fallback/filler, no question-only ending. Plans
request grounded player placement, observable context, sensory detail, pressure and
actionable affordances. Those are presentation obligations, not additional mandatory
JSON fields. Active scene supplies identity/character placement; model prose cannot
relocate the character. Authorized visible NPC introductions are allowed (S8 runner/
guards); new NPC IDs/records are not prerequisites. Optional scene/world proposals grant
no persistent mutation authority. No new paragraph, length, NPC-count or action-count
acceptance gate was invented; validate_opening_output was not substituted as stricter gate.

Commit eligibility: structural validity AND completed generation AND semantic/opening
acceptance AND no provider/fallback/budget failure, under locked first-start scope, then
normal persistence. Engine owns turn/time/faction progression. Failed opening restores
gameplay; save timestamps/debug/lazy initialization are bookkeeping, not progression.

Response type is scene_opening through bootstrap, derivation and provider observation;
structured_realization is its envelope, not an information-answer type. S7 shows explicit
opening identity overrides question-shaped input. Residual guidance conflict remains:
generic resolution projection says operation unresolved, expected_resolution answer and
'referent is not unambiguous'; recipe says 'Answer the unresolved about the current
subject', alongside authorized consequential scene realization. Existing saved PR06
request confirms this C conflict. Its influence on October 29 is a hypothesis, not a
causal finding. System/opening instructions also permit authored scene presentation and
harmless sensory texture while forbidding arbitrary consequential invention/hidden facts.

S4 omits required declared_claims entirely and fails structurally; S1/S5 empty lists are
valid. S12 rich text with an empty list fails the existing decision-fact audit; missing
declarations alone does not prove every rich opening invalid. Prior declared-rich PR06
controls still pass. Existing scene-establishing checks are heuristic, not a comprehensive
natural-language meaning proof. B incorrect rejection is unestablished historically;
C guidance conflict is observed, causality unknown; D missing text/reasons prevents a
historical choice. No speculative prompt, parser, authority or acceptance change.
''')
    report('04_root_cause_and_implementation.md', '04 — Root Cause and Implementation', '''
Historical semantic cause UNRESOLVED. Completed JSON/envelope does not establish semantic
validity. S9/S12 demonstrate unauthorized_resolution_decision_fact can correctly produce
the observed sequence. Hidden disclosure, invalid declaration/realization or attribution
could select the same fallback. An acceptable opening rejected by an unrelated generic
rule or a guidance-induced model fallback remains possible, not selected without evidence.

Confirmed defects repaired: diagnostic loss of first semantic reasons/provenance;
mislabeling final acceptance as structural validation; absence of bounded opt-in response
evidence; UI error erased by reloadAll -> loadLog -> chatLog.innerHTML=''; no fetch/JSON catch.

Modified functions: gm._generation_response_diagnostic adds presence/length/counts;
gm.call_gpt invokes opening-only capture after parsing. provider_budget existing record/
observe/end opening diagnostics retain independent provider/parser/semantic/final outcomes;
observe_opening_semantics and capture_opening_response are helpers in that existing owner.
immutable_valid_response.run_preserve_if_valid observes first _check and final _finish
without changing decisions/text. tools.atgb.accounting.inspect_ledger recognizes three new
observation stages while retaining request-lifecycle/token rules. static/app.js campaign-
start handler preserves failure feedback via state-only refresh and safe error handling.

No new logger/gameplay authority. No semantic/prompt/schema/model/output-limit changes,
extra provider requests/retries, state structures, gameplay mechanics, PR-EG integration
or unrelated refactoring. API acceptance/rollback/lock and progression contracts unchanged.
Existing PR05 tests caught a development-only accounting-consumer stage mismatch; fixed
before final validation. This does not explain the historical rejection.
''')
    example = json.loads((O / 'matrix/S12.json').read_text())
    write('diagnostic_examples.json', {'provider_response': example['provider'], 'opening_outcome': example['outcome'], 'semantic_events': [r for r in example['events'] if r.get('stage') in {'opening_semantics', 'opening_validation'}], 'capture_schema': {'sensitive_game_content': True, 'opening_attempt_id': 'synthetic-id', 'provider_attempt_id': 'synthetic-attempt', 'parsed_response': {'declared_claims': [], 'narration': 'You stand beside the gate.'}, 'truncated': False}})
    report('05_diagnostic_improvements.md', '05 — Diagnostic Improvements', '''
The existing generation_diagnostic ledger remains the event infrastructure. Opening ID
correlates provider_response, opening_semantics, opening_validation, opening_response_capture
and opening_outcome. Provider attempt/status, logical operation/type, parser validity,
independent final validation, semantic reasons/source/reason, field presence/length/claim
count, rejection stage and actual commit are separate. Outcome runs after commit/rollback.
Old structured_validation_result conflation is removed; final_validation_passed is separate.

First semantics event identifies _check and actual hard reasons; second identifies _finish,
adoption provenance/reason. API opening_validation identifies independent final predicate.
Outcome retains semantic source and rejection_stage=API acceptance. nonresolution_origin
application means host selected safety fallback; model means unchanged initial_generation
plus the exact generic fallback marker. This does not infer intent for every refusal;
inspect preserved response content for other cases. Actual stub records/schema examples:
artifacts/pr_play_07/diagnostic_examples.json.

ASHEN_OPENING_RESPONSE_CAPTURE=1 is separate, disabled by default. Requires generation
diagnostics, active accounting/opening scope, both explicit retry-disable flags, absolute
isolated ASHEN_DATA_DIR matching active storage and a noncanonical data directory. Only
opening GM output is collected: no prompts, SDK object dumps, credentials, headers or
unrelated request/configuration. JSON is parsed independently from original text before
application normalization/recovery; whole JSON fences supported. All original JSON fields
and values, including differing narration/player_facing_text, declarations and proposals,
remain preserved. No silent rewrite/redaction.

Files: <isolated-root>/opening_response_evidence/<opening-ID>-N.json; sensitive_game_content
marker and provider linkage. Six artifacts per scope maximum; each <=65,536 bytes.
Oversize explicitly marks truncated and preserves an 8,000-character serialized prefix
and original serialized length. Malformed JSON yields capture_failed because a parsed
object is unavailable; normal parser diagnostics remain. Exclusive writes avoid replacement;
resolved capture directory must remain within isolated parent. Normal production logging
and campaign saves never receive these files. Manual evidence export includes them only
when explicitly enabled; share sensitive game content with intended reviewers only.

Capture errors are caught, emit content-free capture_failed where possible, and cannot
change acceptance, gameplay or retries. Existing ledger write failure policy stops future
admissions but a current valid opening still completes, verified by synthetic failure.
Capture count/size, enabled/default/off gates, exact parsed content, oversize, filesystem
failure, ledger failure and metering reconciliation are tested. This review includes
synthetic schema/examples, not nonexistent original October 29 output.
''')
    report('06_ui_failure_feedback.md', '06 — UI Failure Feedback', '''
The old handler indirectly recognized HTTP 422 via ok=false and read data.error, then
called reloadAll. loadLog erased chatLog and rebuilt from saved entries. Failed opening
has no narration/log entry, so its error disappeared. State refresh caused silent failure;
422 recognition itself existed. Fetch/JSON exceptions escaped with no useful feedback.

Localized handler now explicitly recognizes HTTP errors/422/ok=false and shows safe text:
campaign did not start, no gameplay commit, retry available. Failure refresh calls loadState
only; refresh failure keeps feedback visible. Already-started 409 gets truthful separate
feedback. Existing upstream/budget blocked presentation remains. Provider internal error
text is not exposed in the new player failure path. Network/JSON errors instead say the
request could not be confirmed and require state refresh, because transport loss cannot
prove the server did not commit. Finally restores busy/button state from authoritative UI.
Success retains normal narration and log reload. No fabricated narration, auto-retry,
false success, duplicate initialization or backend gameplay change.

U1 success/log/started state; U2 semantic rejection visible; U3 HTTP provider exception
without raw detail; U4 explicit 422; U5 same handler failure->successful manual retry;
U6 repeated Start after success/initial started state sends no duplicate; U7 failed state
refresh retains feedback. Transport and invalid JSON controls also pass. Nine cases in
artifacts/pr_play_07/ui_results.json. tests/helpers/pr_play_07_ui.cjs executes the actual
localized handler in Node vm with browser-boundary stubs; existing frontend source-contract
tests also pass. This is not rendered-browser/screenshots evidence. Backend tests separately
prove rollback for rejected opening and exactly one commit on valid retry.
''')
    report('07_deterministic_validation.md', '07 — Deterministic Validation', table + f'''
S1–S12 use existing schema and real endpoint/pipeline with synthetic SDK responses.
Exact fixture, before/after, expected/actual, structural/semantic/outcome events are in
matrix/S*.json. S5 lacks optional proposals; S6 ignores unknown provider fallback metadata,
while actual host safe-provenance separately rejects. S7 confirms type derivation despite
question-shaped input, followed by normal endpoint start; not an intentionally broken router.
S8 reuses authored guards/runner introduction, creates no NPC record. S9 appends unauthorized
key/gold acquisition and rejects. S10 repeats Start, one dispatch/commit. S11 first fails
without progression then succeeds once, two attempts total. S12 existing rich fixture gives
structural success then safe provenance with unauthorized_resolution_decision_fact.
These are related synthetic controls, not exact historical or held-out reproduction.

Focused {results['focused_final']['passed']} pass/0 failure: matrix, optional capture/default/
oversize/count/control/write failures, ledger failure, PR04 integrity, PR05 diagnostics,
PR06 budgets and frontend source checks. Broader: provider {results['provider_final']['passed']}
pass/1 failure; structured {results['structured_direct']['passed']} pass; ordinary/NPC direct
{results['ordinary_direct']['passed']} pass; world/factions/opening planning/ATGB interpretation
{results['world']['passed']} pass; review/export {results['export']['passed']} pass.
Total completed nonduplicate current-source checks: {passes} pass / 1 failure, plus 9 Node
UI cases. Entry-source comparator separately reproduces the same one failure. Full suite,
live behavior, ATGB performance and independent generalization not run/claimed.

State regressions: invalid/nonresolution no commit; valid once; repeated/concurrent Start;
failure->success; persistence exception rollback; world/faction consistency and ordinary
fallback intact. PR05 compares full persisted JSON values/inventory allowing documented
save/debug/empty-log bookkeeping. Diagnostics live outside gameplay state. Provider controls
verify atomic admission, no extra request/retry, unchanged 3000 opening/600 ordinary limits,
aggregate accounting and explicit incomplete-status rejection. New stages reconcile without
double counting diagnostic usage copies. See XML, command/duration manifests, UI JSON and
test_summary.json; integrity.json verifies protected normal/frozen/experiment hashes.

Failure classes:
- Preexisting: test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution
  asserts current frozen source attestation, which is stale. Reproduced using saved dirty
  entry GM/API/immutable/budget source via pr_play_07_entry_source. Not repaired.
- Environment-blocked/unresolved transport coverage: bounded 90-second HTTP-bearing focused,
  structured raw_chat_stub, ordinary, opening and scene-canon attempts timed out. Partial dots
  are not counted. Completed direct slices exclude blocking HTTP cases. Prior PR06 rich
  emission/conversation assertion failures are documented history, not newly reproduced here.
- Tool setup: initial missing --basetemp parent caused FileNotFoundError; driver now creates
  parent. Initial logs retained, not counted as product failures.
- Development-only regression: new diagnostic stages initially rejected by accounting reader;
  fixed and PR05 reconciliation/final focused checks pass. No relevant new completed-scope failure.

Rendered UI, full HTTP transport and live provider semantic adequacy remain unproven.
''')
    manual_archive = 'support/development/campaigns/product_realization/pr_play_07/PR_PLAY_07_LIVE_OPENING_TEST.txt'
    report('08_live_test_readiness.md', '08 — Live-Test Readiness', f'''
B — Conditionally ready for external reviewer consideration, not live success. Deterministic
acceptance/state/budget/capture/UI-handler checks pass. Historical content/rejection cause
remains unknown; new evidence makes a later result diagnosable. HTTP/browser transport remains
environment-blocked here and is not green. Stale source attestation is preserved.

Complete procedure: PR_PLAY_07_LIVE_OPENING_TEST.txt beside these reports; supersedes PR06 for
a FUTURE reviewed one-Start test. Fresh isolated frontier-gate-v1 authoritative fixture;
one Uvicorn worker; zero SDK/host retries; six requests; unchanged 200000/20000/220000 aggregate
ceilings; verified 3000 opening/600 ordinary; generation diagnostics + bounded response capture;
usage journal; before/after state/data; screenshots/notes; 15-second local HTTP snapshots;
stopped-server evidence ZIP. Each terminal sets location and discovers root through pointer
file; no long-path reconstruction/cross-window variable assumptions or provider preflight.

Stop after success OR failure of one manual Start. No gameplay action, automatic retry,
resend, restart, model/cap change or connectivity probe. Also stop after 60 seconds without
reply, unexpected retry, budget refusal or state anomaly. Retain partial/missing evidence
honestly; capture failure never authorizes another request. Success requires completed
provider/JSON/envelope/semantic acceptance, visible narration, started latch, one engine commit
and zero unexpected retry. Failure requires explicit UI rejection, rollback, semantic reasons/
origin, bounded parsed evidence, completion/accounting and export. No statistical claim.

Manual exact review archive-relative path: `{manual_archive}`.
Next action: external review. Operator should consider the procedure only after conditional
acceptance. This pass does not perform it or implement a follow-on repair.
''')
    confirmations = 'No live provider calls; no provider connectivity diagnostics; no model changes; no output-budget increases; no automatic retries; no additional provider operations; no unauthorized gameplay-state mutations; no new persistent gameplay structures; no experimental PR-EG integration; frozen ATGB baseline unchanged; no secrets included; no commit or push performed.'
    report('09_final_verdict_and_handoff.md', '09 — Final Verdict and Handoff', f'''
**B — Conditionally ready.** Historical semantic cause stays unresolved; no speculative
semantic or prompt repair. Confirmed diagnostics/capture/UI visibility gaps repaired.
S1–S12 pass; {passes} completed current checks pass / one entry-reproduced stale-attestation
assertion fails; 9 UI boundary cases pass. HTTP-bearing suites timed out; rendered/live
success unclaimed. Exact October 29 output cannot be recovered. Residual unresolved-answer
guidance conflict is documented without causal attribution.

Changes: first semantic reasons/final provenance, independent parser/final outcome, bounded
explicit original parsed-response evidence, compatible accounting observation stages,
state-refresh-safe player feedback and safe network/JSON errors. Authority/budgets/model/
schema/retries/rollback/world/faction progression unchanged. Remaining risks: model may
again fail semantic requirements; valid and invalid audit decisions can share safe provenance;
guidance conflict influence unknown; HTTP/browser integration unvalidated in this environment.
No broad conversation-quality, benchmark, reliability or held-out generalization claim.

Should user run live test? Not before external review. After conditional acceptance, one
operator opening would provide inspectable evidence for either result. One recommended next
action: external review of this ZIP and task-relative diff. Do not implement a further
semantic/prompt repair or perform an opening in this pass.

Manual exact archive-relative path: `{manual_archive}`.
Standard review: handoff/CURRENT_REVIEW.md, REVIEW_MANIFEST.json, CURRENT_REVIEW.zip;
timestamped CURRENT_REVIEW(YYYYMMDD-HHMMSS).zip is the same package. Bundle includes nine
reports, source diff/snapshots, tests, matrix, decision/source maps, diagnostic examples,
UI/state results, status/integrity and complete manual. Sources selected explicitly.

{confirmations}

Stop after generating review ZIP and await external review.
''')
    paths = ['game/gm.py', 'game/provider_budget.py', 'game/immutable_valid_response.py', 'static/app.js', 'tools/atgb/accounting.py', 'tests/test_pr_play_07_semantic_acceptance.py', 'tests/helpers/pr_play_07_ui.cjs', 'tests/helpers/pr_play_07_entry_source.py', 'tools/validate_pr_play_07.py', 'tools/report_pr_play_07.py', 'docs/NEXT_SESSION.md']
    diff = []
    for path in paths:
        old = O / 'entry' / path
        diff.extend(difflib.unified_diff(old.read_text(encoding='utf-8-sig').splitlines(True) if old.exists() else [], (ROOT / path).read_text(encoding='utf-8-sig').splitlines(True), fromfile='entry/' + path, tofile='current/' + path))
    (O / 'source_diff.patch').write_text(''.join(diff), encoding='utf-8')
    (O / 'final_status.txt').write_bytes(subprocess.check_output(['git', 'status', '--short']))
    protected = json.loads((O / 'protected.json').read_text())
    current = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for root in ['data', 'experiments'] for p in Path(root).rglob('*') if p.is_file()}
    write('integrity.json', {'count': len(protected), 'changed': [p for p, h in protected.items() if current.get(p) != h], 'added': sorted(set(current) - set(protected))})
    assert protected == current, 'Protected state/inventory changed'
    support = paths + [p.relative_to(ROOT).as_posix() for p in R.glob('*') if p.is_file()]
    support += [p.relative_to(ROOT).as_posix() for p in O.rglob('*') if p.is_file() and p.name not in {'review_config.json', 'package_verification.json'} and p.suffix in {'.md', '.txt', '.json', '.jsonl', '.xml', '.patch', '.py', '.cjs'}]
    config = {'campaign_id': 'pr_play_07', 'campaign_name': 'PR-PLAY-07 — Opening Semantic Acceptance and Safe-Nonresolution Investigation', 'campaign_date': '2026-10-29', 'purpose': 'Offline investigation and bounded diagnostics/UI repair; stop after review ZIP.', 'objective_status': 'B — Conditionally ready', 'executive_summary': f'Historical cause unresolved; no speculative semantic/prompt change. Repaired missing diagnostics/capture and erased UI failure feedback. S1–S12 pass; {passes} checks pass / one entry-reproduced preexisting failure; 9 UI boundary checks pass. HTTP coverage bounded timeout. ' + confirmations, 'primary_report': (R / '09_final_verdict_and_handoff.md').relative_to(ROOT).as_posix(), 'supporting_files': [{'path': p, 'role': 'source' if p in paths else 'evidence', 'why': 'Scoped PR-PLAY-07 source, reports, manual and deterministic validation.'} for p in dict.fromkeys(support)], 'changes': {'production': ['Opening diagnostics/capture and localized player failure feedback.'], 'validation': ['S1–S12, bounded capture/ledger controls and actual JS handler tests.'], 'tooling': ['Accounting observational stages; bounded driver/report generator.'], 'documentation': ['Nine reports, PowerShell manual, canonical session handoff.'], 'generated_artifacts': ['Explicit diff/matrices/source/decision maps, status/integrity and review.']}, 'testing': {'focused': f"{results['focused_final']['passed']} passed.", 'broader': f'{passes} total current checks pass / one preexisting failure; report 07 gives disjoint counts.', 'full_suite': 'Not run; bounded relevant slices.', 'runtime_validation': 'Synthetic SDK through actual endpoint/semantic/persistence owners; 9 Node boundary cases; HTTP suites timed out.', 'model_runtime_boundary': 'No live provider or connectivity calls.', 'new_regressions': 'None in completed scope. Development diagnostic-consumer mismatch fixed.', 'pre_existing_failures': 'Stale source attestation reproduced with saved dirty entry production sources.'}, 'decisions_requiring_human_review': ['Accept/redirect conditional readiness before any future one-Start operator test.'], 'known_problems': {'campaign_specific': ['Historical response/reasons absent; unresolved-answer guidance conflict; HTTP coverage timed out.'], 'pre_existing': ['Frozen attestation stale; historical rich-emission/conversation failures not newly reproduced.']}, 'does_not_prove': ['Exact historical semantic cause, live/rendered success, reliability, independent generalization or ATGB performance.'], 'recommended_next_step': 'External review; stop without further implementation or live opening.', 'configuration_source': 'artifacts/pr_play_07/review_config.json', 'self_contained_review_test': 'Verify nine reports, exact manual path, diff/matrices/status and ZIP manifest hashes.'}
    write('review_config.json', config)
    print('Reports ready:', passes, 'passing checks; protected files:', len(protected))


if __name__ == '__main__':
    main()
