"""Generate the eight campaign reports from retained evidence."""
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/pr_play_05'
REPORT=ROOT/'development/campaigns/product_realization/pr_play_05'
REPORT.mkdir(parents=True,exist_ok=True)
historical=ROOT/'artifacts/pr_play_02/manual-20261026-201939.zip'
with zipfile.ZipFile(historical) as z:
    ledger_name=next(n for n in z.namelist() if n.endswith('provider_usage.jsonl'))
    rows=[json.loads(line) for line in z.read(ledger_name).decode().splitlines()]
    completion=next(r for r in rows if r.get('event')=='completed')
    log_name=next(n for n in z.namelist() if n.endswith('session_log.jsonl'))
    log=z.read(log_name).decode()
    fact={'source_zip':str(historical.relative_to(ROOT)), 'ledger_member':ledger_name,
          'admissions':sum(r.get('event')=='admitted' for r in rows),
          'input_tokens':completion['input_tokens'],'output_tokens':completion['output_tokens'],
          'total_tokens':completion['total_tokens'],
          'missing_structured_envelope_in_original_log':'missing_structured_envelope' in log,
          'provider_finish_metadata_retained':False,'raw_provider_content_retained':False,
          'interpretation':'600/600 is consistent with possible truncation, not proof.'}
    (OUT/'historical_facts.json').write_text(json.dumps(fact,indent=2))

intro='PR-PLAY-05 · 2026-10-27 (America/New_York) · evidence_scope: structural_only. Synthetic provider controls; no live generation or gameplay-quality claim.\n\n'
reports={
'01_baseline_and_failure_reproduction.md':'''# 01 — Baseline and Failure Reproduction

HEAD remains `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`, branch feature/product-realization. The tree was extensively dirty on entry. `artifacts/pr_play_05/status_before.txt`, `head.txt`, `entry_hashes.json` and `entry/` retain the exact baseline. Git HEAD alone does not represent the tested source. No reset, discard, commit or push occurred.

PR-PLAY-04 changes were uncommitted: opening rejection before persistence, preventing generic answer adoption for rejected openings, `_OpeningScope` rollback/serialization, and opening tests. Its recorded `artifacts/pr_play_04/source.diff`, eight reports and original HTTP output were inspected. Preexisting unrelated edits include other provider/interpretation owners, runtime saves, audit artifacts and documentation. They were preserved. The pass-specific diff is against entry snapshots, not cumulative Git HEAD.

Read the Constitution, canonical NEXT_SESSION, validation evidence standard, Product Realization validation, review standard, PR-PLAY-01 findings, PR-PLAY-02 controls/manual, PR-PLAY-03 causal evidence and PR-PLAY-04 implementation/regression reports. `support/docs/NEXT_SESSION.md` is absent in the workspace; support/ is the review ZIP prefix. Used canonical `docs/NEXT_SESSION.md`. No applicable AGENTS.md was found.

Original manual ZIP was opened directly: one admitted request, 26,593 input / 600 output / 27,193 total tokens; original log contains missing_structured_envelope. Neither raw provider output nor authoritative finish metadata survives. `historical_facts.json` preserves this limited finding. Usage at a 600-token limit is possible-truncation evidence only.

## Five original tests, run individually

All use disposable `_seed_campaign_start_storage`, TestClient, New Campaign, then Start; call_gpt is replaced with a fixture. No SDK dispatch occurs in these five tests. Tests 1–3 use legacy rich response dictionaries; tests 4–5 use `[Narration]`.

| Test in tests/test_start_campaign_api.py | Expected / original actual | Final classification |
|---|---|---|
| test_start_campaign_emits_opening_and_sets_started | 200 and rich text/persistence; actual 200, substring assertion fails | Confirmed preexisting defect; excluded |
| test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text | forced reconciliation cannot shorten accepted text; actual 200, debug 781 > 800 fails | Confirmed preexisting defect; excluded |
| test_start_campaign_promotes_valid_upstream_prepared_scene_opening | prepared rich candidate replaces short text; actual 200, short text persists | Confirmed preexisting defect; excluded |
| test_start_campaign_frontier_gate_uses_journal_seed_facts_when_opening_seed_absent | 200 with selected journal facts; actual 422 scene_opening_not_scene_establishing | Resolved obsolete fixture |
| test_start_campaign_opening_fallback_basis_uses_journal_seed_not_visible_facts | 200 and journal basis; actual 422 same placeholder reason | Resolved obsolete fixture |

The historical output's first/third failures are substring assertions, not length assertions. `entry_1..5.txt/json` reproduce all five on preserved PR-PLAY-05 entry source; `fixed_1..5` contain final individual runs. `http/entry_*/` and `http/fixed_*/` retain relevant response bodies, emitted text and application metadata. Reproduction is consistent across the historical report, entry runs and current rich cases. Group A now passes individually.

Each run is capped at 55 seconds. Initial setup lacked the pytest temp parent; corrected without product changes. Sandboxed TestClient executions then timed out; those subprocesses were killed by subprocess timeout. Outside-sandbox, guarded offline HTTP runs completed in seconds. Their provider guard remained active. `baseline_*` and `repeat_*` preserve environment failures rather than hiding them.

## Isolated comparison

`prepare_comparison.py` copied source/tests/static/data/docs to ignored development/tmp/pr_play_05/pre04, reconstructed API from PR-PLAY-02 saved source plus its recorded delta, and verified the exact SHA-256 against PR-PLAY-03's source attestation. Other production owners match entry. No active source was overwritten. `comparison_provenance.json` records the matching pre-PR-PLAY-04 API hash. All five ran individually there (`pre04_1..5`): 1–3 fail identically; 4 passes; 5 already fails its journal-text assertion. After pre04 boundary capture, the isolated API was replaced by the saved PR-PLAY-05 entry API for entry baseline tests. This is a source-overlay comparison, not a claim that Git HEAD represents pre04.
''',
'02_placeholder_test_closure.md':'''# 02 — Placeholder Test Closure

The two tests protect journal-source selection and campaign-opening integration, not invalid-output rejection. Their old `[Narration]` fixture cannot establish a scene and must not be accepted. Changing their expected status to 422 would erase their intended coverage.

Added `_structured_opening_fixture`, which invokes the actual `_safe_json` production parser with a declared_claims/narration JSON envelope. Where a consequential journal proposition is narrated, the fixture declares it with its actual source_claim_id from the supplied gm_resolution_decision. No declaration requirement is bypassed. The second test uses one natural scene-setting journal proposition instead of the opaque uppercase marker; a distinct visible-fact sentinel still must not appear.

Both tests still execute New Campaign and successful HTTP Start, read persisted GM output, and assert nonempty/journal-source curated facts. The second asserts the exact selected/curated journal fact, exclusion of visible facts, and final selector mirrors. A valid immutable response does not select a fallback, so the former unconditional fallback-only metadata assertion was obsolete too. The test now exercises the real `opening_context_from_gm_output` and `build_opening_fallback_result_meta` owners and asserts their exact basis/equality. It does not manufacture fallback metadata in production.

Final individual results: both pass (`fixed_4.txt`, `fixed_5.txt`). HTTP regression: these remain green. No production acceptance, schema or parser validation rule was relaxed.

Separate negative controls retain invalid `[Narration]`: real call_gpt with synthetic SDK output produces 422, no gm_output and gameplay_committed false. `placeholder_http.json` records the actual HTTP failure body, state before/after and diagnostics. The diagnostic matrix's placeholder case additionally compares all persisted gameplay values, world/factions/time/turn/latch and log. One admission is consumed, no retry occurs. Full-payload equality accounts explicitly for preexisting save timestamps, empty-log creation and scene-addressability trace bookkeeping; no progression changes are ignored. See report 06.
''',
'03_rich_text_emission_investigation.md':'''# 03 — Rich-Text Emission Investigation

Three independent original tests were reproduced individually on current, preserved entry and hash-verified pre04 API source. All return 200, and all three fail before the new diagnostics existed. Classification: **Confirmed preexisting defect**, explicitly excluded from PR-PLAY-05 acceptance. The existing tests remain failing and unskipped; no threshold was lowered and no filler added.

Exact fixture inputs and every captured boundary are in `emission/{rich,reconcile,prepared}.json`, with corresponding `emission_pre04/` files. Exact original-test response bodies are separately in `http/entry_1..3/` and `http/fixed_1..3/`. `emission_comparison.json` makes counts directly comparable.

| Case | Fixture / prepared chars | Accepted realization chars | Local sanitize/gate debug chars | Final response/log chars | Pre04 |
|---|---:|---:|---:|---:|---|
| rich | 1218 / none | 899 | 781 | 899 | Same |
| forced reconcile | 1218 / none | 899 | 781 | 899 | Same |
| short plus prepared rich | 111 / 1218 | 111 | 1100 | 111 | Same |

These tests bypass SDK extraction and `_safe_json`: their supplied dictionaries are legacy normalized GM stubs, without a declared_claims envelope. There is no provider-generated or parsed structured envelope to count in this path. Before acceptance is the fixture text; after acceptance is the immutable realization; final response and persisted log are separately captured. They must not be called the same boundary.

## Earliest demonstrated transformations

`immutable_valid_response.run_preserve_if_valid` and its `_bounded_keep` path check structural narration units against the decision authority, preserve hard-valid units, then seal. In the rich stub, 1218 becomes 899 before final emission: the player-location/crowd sentence and townhouse/noble-colors sentence disappear. This is substantive deletion, not merely whitespace normalization. It cannot be blamed on PR-PLAY-04, whose pre04 comparison produces the same deletion. The fixture lacks declarations and is not evidence that the deleted consequential claims were authorized. This pass does not weaken that authority check.

`api_turn_support._finalize_player_facing_for_turn` then runs strip-only sanitization and the final gate. Its local `pre_gate_text_len`, `post_final_emission_gate_text_len` and reconciliation lengths show 781, while restoration of the immutable accepted response yields 899 at delivery. Thus the previous report's approximately 781 characters describes local telemetry, not the final rich emitted string. The forced-reconcile case restores accepted output, but its old debug-length assertion remains false.

In the prepared case, the initial 111-character response is accepted/sealed before the later prepared candidate is considered. The prepared 1218 characters are recognized and local sanitized/gate telemetry shows 1100, yet immutable restoration delivers 111. The existing promotion flag therefore does not establish final promotion. Earlier immutable acceptance is the responsible boundary; changing its precedence is a separate repair requiring authority review, not a length patch.

## Purpose and disposition

Test 1 protects scene establishment, successful start and response/log/reload fidelity. Test 2 protects a valid post-gate candidate from an unrelated reconciliation overwrite. Test 3 protects adoption of an upstream prepared rich candidate. Those purposes remain meaningful. An 800-character minimum is not stated by `candidate_satisfies_scene_opening_contract` or the opening contract; it is a historical test proxy for preserving richness. Length alone cannot test semantic preservation, and is especially misleading when a debug boundary differs from final emission.

No production repair was made for these preexisting emission/fixture/telemetry conflicts. Nor were meaningful assertions replaced merely to obtain green. A later bounded owner repair should use declared authorized details, assert their preservation at acceptance/delivery, and resolve prepared-candidate precedence and telemetry meaning. This report does not claim all rich fixture sentences should be authorized or preserved. PR-PLAY-05's contract/diagnostic readiness excludes these three tests explicitly.
''',
'04_provider_diagnostic_implementation.md':'''# 04 — Provider Diagnostic Implementation

The existing provider budget ledger remains the single diagnostic persistence owner. No parallel logger, gameplay schema or world-state authority was added. Opt in with ASHEN_GENERATION_DIAGNOSTICS=1 and the existing ASHEN_PROVIDER_USAGE_PATH/accounting settings. Default operation records no new diagnostic events; raw provider content is never stored by this mode.

## Production path and owners

1. API narration construction builds messages using the existing route, response policy, authority decision and provider-envelope projection.
2. gm.call_gpt selects the existing model, host-retry guard and budget admission. OpenAI construction retains key/timeout and existing sdk_retry_options.
3. Request uses existing model/input; accounting mode retains max_output_tokens=600. No API response-format setting is added; envelope instructions are already in the prompt. No prompt or schema edit.
4. RequestAttempt.dispatch performs the existing durable admission/dispatch/completion accounting around client.responses.create. Token accounting precedes parser work.
5. `_extract_provider_response_text` reads output_text, with fallback to SDK output message/output_text segments. It replaces unsafe object stringification with supported content extraction. Other representations fail closed; refusal content is not treated as narration.
6. Existing `_safe_json` / classify_model_output performs the actual required structured parse. Diagnostic syntax inspection separately records whether JSON parses (including the parser's supported fenced JSON). A JSON object alone does not establish the required envelope.
7. Existing decision/claim validation, recovery, immutable adoption and final emission execute unchanged. Structural parsing does not grant gameplay authority.
8. Existing `_opening_response_rejection` governs final opening acceptance. The diagnostic observer records its rejection and recovery provenance. `_OpeningScope.close` records commit disposition after commit or rollback in the same ledger.

## Changed functions and fields

gm.py: new extraction/structural observation helpers; call_gpt attaches structural ledger events after real extraction and parse, and sanitized provider_error observations on exception. provider_budget.py: opt-in helpers and an ephemeral ContextVar correlate provider attempts with one opening operation; existing _append supplies durable writes. api.py: opening scope begin/end, final validation observation, budget-admission and repeated-start dispositions. tools/atgb/accounting.py: explicitly recognizes diagnostic observations without altering admission/completion state; still rejects unknown stages/unknown attempt references and reconciles the complete event list.

Provider-response events include logical operation, requested response type, configured provider model (returned model remains in completion), SDK request ID when exposed as _request_id, distinct response ID, provider status, incomplete/finish reason, requested output cap, reported input/output/total tokens, usage-at-limit flag, segment count, content/extraction presence, extraction source/length/empty status, JSON status, known envelope keys, expected-envelope presence, parser form, parser/structured result and rejection reason. Null means unavailable, not zero.

Categories include provider_error, empty_provider_content, extraction_failure, json_parse_failure, missing_structured_envelope, structured_validation_failure and accepted_structured_response. A separate possible_output_truncation flag requires limit-reaching invalid output; authoritative provider max_output_tokens exhaustion is recorded separately. It never converts usage equality into proven truncation or suppresses the actual failure category.

Opening-outcome events record accepted_structured_opening or opening_rejected, final validation, recovery provenance, rejection reason and gameplay_committed. Admission refusal records provider_budget_refused. Related events share opening_attempt_id; provider events also carry attempt_id. No provider operation is added. An interrupted process can lack an outcome: that is unknown and must be reconciled with snapshots.

## Safety and export

Only explicit structural fields are constructed: no raw SDK repr, request payload, narration, declarations, key, header, exception message, arbitrary JSON keys or environment dump. Known envelope keys and safe identifier tokens only; unknown finish values are unavailable. Provider exception diagnostic contains a category without the exception message. Existing unrelated application logging behavior was not redesigned.

Ledger I/O failure stops future admissions and does not retrospectively turn committed gameplay into a failed opening. Diagnostic writes use existing lock/fsync. Default-off behavior is tested. Export is the existing provider_usage.jsonl plus existing campaign snapshots, copied/ZIPped with PowerShell; the ledger reader now tolerates these explicit observations without double-counting tokens/attempts. Unknown raw-output ambiguity remains a limitation; no unrestricted raw-capture mode was introduced.
''',
'05_diagnostic_validation_matrix.md':'''# 05 — Diagnostic Validation Matrix

The final integrated suite runs real production call_gpt, RequestAttempt admission/dispatch, extraction, `_safe_json`, claim/response validation, API endpoint functions and persistence. Only OpenAI transport is replaced with synthetic SDK objects; the standard test guard prevents live calls. This is not a standalone classifier test. The separate HTTP placeholder control exercises actual TestClient transport.

| Control | Result / HTTP | Extraction, parse, validation evidence |
|---|---|---|
| D1 valid opening envelope | 200 accepted | text extracted; JSON/envelope/structured valid; final accepted; committed once |
| D2 valid JSON, no envelope | 422 | JSON true, envelope false; missing_structured_envelope diagnostic; actual parser malformed_envelope rejection preserved |
| D3 malformed JSON | 422 | JSON false; json_parse_failure; no progression |
| D4 empty text | 422 | extracted empty; empty_provider_content; no progression |
| D5 SDK message content instead of convenience attribute | 200 | typed output_text segment fields recovered; no object stringification; final accepted |
| D6 truncated structured JSON | 422 | JSON false; usage reaches 600; explicit status incomplete/reason max_output_tokens records provider-reported exhaustion |
| D7 provider exception | 422 | provider_error; no invented finish/request/usage metadata; one consumed admission |
| D8 missing usage | 200 | all token fields null; accounting correctly marks usage unavailable/stops future admission; no invented zeros |
| D9 missing finish metadata | 200 | provider_status/finish_reason null; no inferred completion reason |
| D10 output limit reached, completed JSON lacking envelope | 422 | output_limit_reached true, possible_output_truncation true, provider_output_limit_exhausted null; primary cause remains missing envelope |

Additional controls cover refusal/unextractable segments (extraction_failure), structurally invalid declarations (structured_validation_failure), literal `[Narration]`, default-off events, SDK repr prohibition and the actual installed OpenAI Response/ResponseOutputMessage/ResponseOutputText classes with two segments and distinct request/response IDs. D5's shape uses only the SDK's supported message/output_text fields. Native SDK validation confirms the same extraction/parser boundary, without network.

Each generated response control verifies its endpoint status, player text/error, acceptance, campaign latch, turn/time/factions, one admission, persistent gameplay values and ledger export/reconciliation. Synthetic narration/exception/refusal sentinels are absent from diagnostic ledger output. The existing accounting inspector reports exactly one admission even with diagnostic rows present.

`artifacts/pr_play_05/diagnostics/D1..D10.json` contain lifecycle, diagnostic and state observations. Other named JSONs retain negative, retry, repeated, concurrency and budget controls. `integrated.txt/xml` is the final executable result. No assertion claims the original live model's text, statistical reliability, or confirmed historical truncation.
''',
'06_integrated_regression_and_performance.md':'''# 06 — Integrated Regression and Performance

Final focused suite: **39 passed** (21 PR-PLAY-05 checks plus 18 retained PR-PLAY-04 checks). `integrated.xml/txt` retains results. Offline HTTP positive/journal tests pass individually; HTTP negative placeholder is in this suite. Raw transport is synthetic, no provider/network trial.

## Opening matrix

| Scenario | Endpoint / visible result | Progression / requests / diagnostics |
|---|---|---|
| valid | 200, exact valid narration | latch true; turn/time 1; faction agendas +1; one request; accepted_structured_opening |
| placeholder | 422, explicit error, no gm_output | latch false; no turn/time/faction/log progression; one request; JSON failure + rejected opening |
| missing envelope | 422 | same rollback; one request; missing envelope |
| malformed / empty / truncated | 422 | same rollback; one request each; precise distinct diagnostics |
| provider exception | 422 | same rollback; one request; provider_error and rejected outcome |
| budget exhausted | 409 blocked | no dispatch/admission, no progression; provider_budget_refused |
| failure, failure, success | 422,422,200 | three admissions; two rejected outcomes and one commit; turn/time/faction increment once |
| repeated successful Start | 200 then 409 already_started | one provider request total, no second progression; repeated-start diagnostic |
| concurrent Starts | one 200, one 409 | existing persistence lock serializes; one request/commit; no duplicate progression |

Retained PR-PLAY-04 controls also cover chat-start parity, pipeline/pre-dispatch/save exceptions, retry after exception, independent market vocabulary and ordinary information fallback. Focused payload checks materialize normal initialization defaults before measurement. Failed attempts preserve all gameplay JSON values; exceptions are explicitly limited to existing save timestamps, empty-log materialization and duplicated scene-addressability initialization trace rows. Those bookkeeping writes are not represented as byte-for-byte file identity. Normal user saves were never used as the test sandbox.

## Broader slice

| Group | Passing | Failing |
|---|---:|---:|
| HTTP opening/seam/scene canon | 23 | 3 preexisting rich cases |
| Provider controls/accounting | 88 | 1 preexisting attestation |
| Structured/narration-only/retry/immutable boundary | 60 | 1 preexisting conversation assertion |
| Retry, ordinary conversation, pending action, authority | 56 | 0 |
| Review exporter | 11 | 0 |
| Total broader | 238 | 5 |

Full repository suite was not run. Groups are individually capped at 90 seconds; required original cases at 55. No test is skipped to obtain these counts. Logs/command JSONs identify exact suite files. Initial sandbox HTTP timeouts and one sandbox atomic-replace permission error were environment limitations; clean outside-sandbox guarded reruns passed the scoped checks. An isolated baseline accounting collection first lacked tools/; supplied those dependencies, reran and retained the failed setup record.

All remaining broader failures are demonstrated on earlier source: rich cases on hash-matched pre04; `test_readiness_acceptance_is_not_live_execution` and `test_raw_chat_stub_preserves_valid_and_contains_invalid` on saved entry source (`entry_remaining.txt`). The attestation remains fail-closed because reviewed source fingerprints are stale, not because admission ceased to work. The conversation case expects a stew-price limitation but gets the authored runner line. Neither is repaired or silently claimed green. No unknown failure is called preexisting.

## Performance and accounting

Synthetic local medians: parser alone 0.0047 ms; parser plus structural diagnostic construction 0.0146 ms; durable ledger observation 0.8789 ms (p95 1.2156 ms), 100 fsync writes. See performance.json for scope/iterations; this is not provider/UI latency. Durable writes can cost more on another disk. Zero provider admissions in the measurement.

No interpretation/narration operation, retry, model, prompt, output cap, response schema, persistent gameplay structure or gameplay-state mutation was added. Existing request kwargs and 600 cap are asserted in synthetic dispatch tests. All gm top-level prompt/config literals compare equal to entry. 437 protected data/experiment hashes, including normal saves and frozen ATGB, remain unchanged. No PR-EG integration. Ledger lifecycle reconciliation still bounds admissions and avoids counting diagnostic copies of token usage. Frozen source-attestation readiness remains separately red; the manual procedure uses the existing budget owner and does not claim ATGB worker readiness.
''',
'07_live_test_readiness.md':'''# 07 — Live-Test Readiness

Deterministic evidence is sufficient for a bounded, diagnostic operator trial after external review, with the exclusions in reports 03/06. It is not evidence that the existing live model generates acceptable openings or is statistically reliable. Original provider failure remains unexplained; prompt size/output adequacy, actual finish status, generated syntax and external connectivity are live uncertainties. Raw content is deliberately not captured, so some content-specific ambiguity may remain even after the next trial.

The exact executable PowerShell procedure is `PR_PLAY_05_LIVE_OPENING_TEST.txt` in this report directory. It supersedes PR-PLAY-02 for this next operation. It contains fresh disposable data setup, existing zero SDK/host retries and six-admission ceiling, opt-in diagnostics/ledger activation, offline startup configuration verification, single-worker launch on 8765, New Campaign, before snapshot, exactly one Start, success/failure expectations, all stop conditions, exact evidence extraction/ZIP commands and normal-environment restoration. It must not be executed during this pass.

One Start is a user operation, not a promise of one provider request. Count admitted/dispatch_attempted/completed events, and sum usage only once from completed records; missing values are unavailable. All supported callers retain the existing budget guard. Do not restart a process or change ledger/limits to continue. No normal campaign file is reset or overwritten.

Provider-response rows answer whether content/extraction/JSON/envelope/parsing succeeded and retain provider status/finish evidence separately from the host accounting completion. Opening-outcome rows answer final validation/recovery/acceptance and commit disposition, even when a failed opening leaves no gameplay log. Before/after state and campaign directories permit independent turn/time/faction/latch verification. A missing outcome after interruption is explicitly unknown. The export retains ledger originals, diagnostic/completion extracts, notes and screenshots, plus before/after data and local state JSON where responsive.

Stop and export after success or failure, generic answer fallback, budget exhaustion, unexpected retry, unresponsiveness or progression after failure. No NPC conversation or gameplay action follows success. The procedure's error UI may offer retry; the operator must not use it. A single success demonstrates one sample, not broad reliability. Request no raw response capture or general prompt compression in this pass.
''',
'08_final_verdict_and_handoff.md':'''# 08 — Final Verdict and Handoff

**B — Conditionally ready for one controlled live opening after external review.**

The two obsolete placeholder fixtures are repaired without accepting placeholders or weakening declarations. Three rich-emission failures are proven preexisting by an isolated, hash-matched pre-PR-PLAY-04 comparison and are explicitly excluded from acceptance. Their assertions remain in place; no artificial length increase or threshold reduction. Existing rich preservation/promotion/telemetry conflicts remain a separate product/evaluation issue.

39 focused checks pass, including actual extraction/parser/validation/commit boundaries, native SDK content forms, D1–D10, HTTP placeholder rejection, retry/repeated/concurrent/budget controls and all 18 retained PR-PLAY-04 cases. Broader regression is 238 passed / 5 demonstrated preexisting failures. Three additional boundary controls pass on current and pre04 source. No full-suite, browser UI, live-provider, statistical-reliability, held-out generalization or gameplay-benchmark claim is made.

What changed: supported SDK text extraction replaces object stringification; opt-in structural observations extend the existing provider ledger; final opening disposition is correlated and persisted after commit/rollback; its existing reader accepts explicit observations without altering admission counts; two journal tests now provide valid structured fixtures. Reports/manual/evidence and canonical NEXT_SESSION were updated. No new logging framework or gameplay owner was introduced.

PR-PLAY-04 remains valid within its deterministic acceptance/commit-integrity scope. Its guards were retained and its focused suite passes. Existing save timestamps and scene-initialization diagnostic rows can change during rollback; no turn/time/world/faction progression is committed on explicit failure. The original live missing_structured_envelope cause remains unknown. Historical 600/600 usage is consistent with possible truncation and is not proof.

The user may conduct only the prepared one-Start test **after external review accepts this package**. This pass did not execute or schedule it. Recommended next action: external reviewer evaluates this ZIP and the documented preexisting exclusions, then approves or declines the operator procedure.

Confirmed: no live provider calls; no provider connectivity diagnostics; no prompt changes; no provider/gameplay schema changes; no model changes; no output-token-limit changes; no additional provider operations or automatic retries; no new persistent gameplay structures; no experimental PR-EG integration; frozen ATGB baseline unchanged; no unauthorized gameplay-state mutations; no secrets included; no commit or push. Additive diagnostic-event fields are the intentional ledger extension, not a provider/gameplay schema change. Normal saves and unrelated prior work were preserved.

Stop after producing CURRENT_REVIEW(YYYYMMDD-HHMMSS).zip. Await external review before any live opening trial.
'''
}
for name,body in reports.items():
    (REPORT/name).write_text(intro+body,encoding='utf-8')

# Canonical continuity preserves the entire previous orientation below the new entry.
next_session=ROOT/'docs/NEXT_SESSION.md'
previous=(OUT/'entry/docs/NEXT_SESSION.md').read_text(encoding='utf-8')
previous=previous.replace('Updated 2026-10-26 / PR-PLAY-04.','Updated 2026-10-27 / PR-PLAY-05.',1)
insertion='''## Latest closure and diagnostics — PR-PLAY-05

2026-10-27: **B — Conditionally ready for one operator opening after external
review.** Two obsolete journal/placeholder HTTP fixtures now use valid declared
structured openings. Three rich emission cases reproduce on hash-verified pre04
source, remain failing and are excluded; no threshold/acceptance relaxation.
Opt-in ASHEN_GENERATION_DIAGNOSTICS=1 extends the existing provider usage ledger
with extraction/JSON/envelope/finish/validation and final commit observations.
No raw-response logging; SDK text segments replace response-object stringification.
39 focused checks pass, including all 18 PR-PLAY-04 checks; broader 238 pass / 5
demonstrated preexisting failures. Original live failure cause remains unknown;
600/600 is possible-truncation evidence only. Frozen attestation remains stale.
Reports and one-Start manual: development/campaigns/product_realization/pr_play_05/.
Evidence: artifacts/pr_play_05/; review: handoff/CURRENT_REVIEW.md and timestamped
ZIP. PR_PLAY_05_LIVE_OPENING_TEST.txt supersedes PR-PLAY-02 for the next trial.
Stop after review package; no live trial until external review accepts it.
No live/connectivity calls, prompt/schema/model/cap changes, extra provider
operations, normal-save/frozen/experiment changes, commit or push. Dirty entry
work retained. PR-PLAY-04 acceptance/commit-integrity repair remains valid in
its deterministic scope. No benchmark or broad gameplay-quality claim.

'''
marker='## Latest repair — PR-PLAY-04'
next_session.write_text(previous.replace(marker,insertion+marker,1),encoding='utf-8')
print('Eight reports and canonical orientation written.')
