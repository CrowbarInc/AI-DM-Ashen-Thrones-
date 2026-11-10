"""Generate the requested eighteen reports from captured evidence."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/pr_play_64';REPORT=ROOT/'development/campaigns/product_realization/pr_play_64';REPORT.mkdir(parents=True,exist_ok=True)
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
baseline=read('baseline.json');dev=read('development_results.json');hold=read('holdout_results.json');live=read('live_summary.json');reg=read('regression_summary_final.json');fault=read('failure_injection_assessed.json')
focused=reg['focused'];broader=reg['broader_hard_validation'];hist=read('historical_before.json')['original']['raw_provider_text'];gate=read('gate_before.json')['original']['raw_provider_text'];new=read('gameplay_actions.json')[0]['full_trace']['raw_provider_text']
metrics={'verdict':'B — PARTIAL / TARGETED REPAIR INCOMPLETE','baseline':baseline['commit'],'development_matrix':{'cases':len(dev),'matched':sum(r['matches'] for r in dev)},'new_tests':37,'holdout_cases':hold['cases'],'holdout_full_matches':hold['matched'],'holdout_decisions_correct':sum(r['actual']==r['expected_decision'] for r in hold['rows']),'holdout_publication_correct':sum(r['publication']==r['expected_publication'] for r in hold['rows']),'critical_false_acceptances':len(hold['false_acceptances']),'false_rejections':len(hold['false_rejections']),**live,'provider_usage':{'provider':'openai','model':'gpt-4.1-mini-2025-04-14','requests':2,'input_tokens':895,'output_tokens':44,'total_tokens':939,'retries':0},'focused_regression':focused,'broader_regression':broader,'failure_injection_passed':fault['passed'],'failure_injection_cases':fault['cases'],'next_step':'Close the newly captured finite information-carrier wording gap: study ... carefully and discover that ..., with a new preimplementation holdout. Do not start broader validator or mechanics work.'}
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf-8')
reports=[
('01_EXECUTIVE_SUMMARY',f'''**{metrics['verdict']}.** The exact historical authorized narration is repaired (FAIL → PASS), as is the exact historical gate observation. A fresh live candidate uses a further introductory variant and safely falls back; some legitimate discovery language therefore remains rejected.

Development matrix: 30/30. New tests: 37 passed. One-shot developer-authored holdout: 40/40 final decisions and publication expectations, 39/40 full expectations; zero false acceptances and zero false rejections. H18 correctly rejects contradictory coverage, contrary to its frozen coverage expectation. Expectations remain unchanged.

Three consecutive supported HTTP application actions, including two live attempts: two provider requests, one validated and published AI response, two deterministic fallbacks. State matches disabled controls. Failure injections: {fault['passed']}/{fault['cases']}. Focused regression: {focused['passed']} passed, {focused['failed']} known failures; broader: {broader['failed']} known failures. No significant new suite regression.

Primary next step: {metrics['next_step']}

No commit or push. Browser-originated gameplay and natural branching remain deferred.'''),
('02_BASELINE_AND_SCOPE',f'''Commit: `{baseline['commit']}`. Extensive dirty entry tree, including existing modified canonical/protected files, untracked validator modules and PR55–63 evidence. Exact status is in `artifacts/pr_play_64/baseline.json`; this cycle does not adopt those changes as its own.

Read governance: `docs/review_handoff_standard.md`, `docs/testing/protected_replay_manifest.md`, `docs/testing/replay_governance_contract.md`, and `development/reports/atgb_05_baseline_preservation.md`. No AGENTS.md found in the repository and `.agents` contained no guidance files. Protected ATGB evidence remains historical; no new ATGB benchmark claim.

Production files changed: `game/consequential_narration_validation.py`, `game/mechanical_claims.py`, `game/integrated_investigation_narration.py`. New test files: `tests/pr_play_64_development.py`, `tests/test_pr_play_64_discovery_language.py`. Additional files are scoped evidence/scripts, eighteen reports, and standard handoff exports. Scoped delta: `implementation.diff`. Mechanical entry source was reconstructed using the exact inverse insertion, explicitly disclosed in `entry_source_manifest.json`.

No fixtures, protected acceptance rules, mechanics or provider dependencies changed. No browser investigation or commit/push.'''),
('03_PR_PLAY_63_REPRODUCTION',f'''Original action: `I examine the notice board.` Resolver: `discover_clue`, success true. Mandatory discovery: “The missing patrol was last seen taking the northwest mud track past the crates.” Prior continuity: empty. Original post-resolution authority and publication are preserved in `historical_original_gameplay.json`.

Exact candidate:

> {hist}

Baseline complete-pipeline replay: FAIL, semantic reason `unauthorized_discovery`; mandatory coverage PASS. Legacy audit is initially valid and is then marked false by the consequential gate. Original fallback: “You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.” Exact original and reproduced traces: `historical_before.json`. No substitute narration was used.'''),
('04_DISCOVERY_LANGUAGE_ROOT_CAUSE','''PR63 added a historical movement frame to `_route_assertion`. Its regex sees “was last seen taking”, but `_covered` checks every token in the entire clause against authority. The fact is authorized; introductory “study” and “learn” are not world-fact tokens. The exact baseline claim has no subject/relation detail because it comes from this route extractor, not `_learned` (which requires “you learn”).

Development found a separate legacy rejection of “You learn that <fact>”: the exact mechanical matcher compared “that <fact>” with “<fact>”. It also projected current disclosures without prior disclosed information. These are demonstrated in development execution before the final repair; final development traces are retained. Information communication is neither an inventory delta nor permission for another discovery.

No general ontology or grammatical parser was introduced. Unrecognized carrier wording remains conservatively rejected, as the live trace demonstrates.'''),
('05_PRIMARY_REPAIR','''`_route_assertion` removes only anchored, finite information-carrier prefixes when checking an existing reported-movement frame. The full complement stays intact, including its subject, direction, landmarks and any appended additions. Other extractors still inspect the original text. No discovery verb is exempted globally and no authority is inferred from prose.

The legacy mechanical audit strips the complementizer “that” for revealed-information comparisons only, then requires equality with a complete current or previously disclosed authorized fact. Inventory, currency and other effects keep their original checks. Prior disclosed information enters through a separate engine-owned field in integrated validation, without becoming a resolver disclosure.

Mandatory coverage code was unchanged. Exact scoped changes are in `implementation.diff`; final hashes are in `implementation_freeze.json`.'''),
('06_GATE_OBSERVATION_ANALYSIS',f'''The bare phrase “You take a careful look.” already avoids acquisition rejection at entry: `_head` ends in “look”, a surface noun. The real historical extended candidate fails because the greedy captured object continues past “look” through the trailing examination words, so its final head is not “look”.

Exact recovered candidate:

> {gate}

This candidate reproduces FAIL → PASS. The acquisition regex now excludes the finite idioms “take a careful look” and “take a closer look” at the verb-object boundary, before greedy capture. `take note` was already uncaptured. Physical “take the iron key”, “take the key and examine it”, “take the gate's key”, and observation plus a separate item acquisition remain rejected. No broad take-prefix exemption.'''),
('07_AUTHORITY_PROJECTION','''Current resolver facts remain mandatory. `contract.outcome.known` enters the legacy validator in `previously_disclosed_information`, separately from `discovered_clues`. It does not enter `must_communicate`, produce a new clue or grant inventory. The consequential validator already receives known facts. Narration and request text cannot manufacture this field's content: the integrated adapter derives it from the authorized contract.

Development covers accurate prior reference, prior omission on unrelated action, mandatory omission, detached fresh context and structured item grants. Frozen prior-context controls and historical PR63 disclosure tests remain intact. Hidden fields are absent from narration projection; explicit hidden identifiers and unsupported caches remain blocked. This does not prove arbitrary hidden-fact paraphrase detection.'''),
('08_DEVELOPMENT_TESTS','''30/30 requested development categories match their expected complete-pipeline decisions. All thirty record hook authority, candidate, projected request, claims, semantic/legacy/coverage decisions, final decision, fallback and input immutability in `development_results.json`. `tests/pr_play_64_development.py` is the fixture source.

37 pytest tests pass: thirty matrix cases, six additional expansion/acquisition controls and the bare careful-look control. D30 tests detached authority; actual session-bound publication isolation is separately exercised by the gameplay harness. Provider errors and malformed output are injected, never described as live provider failures.

The first development execution found three legacy false rejections; these drove the legacy complement and prior-authority repair before the final source freeze. The holdout was not evaluated during development.'''),
('09_FROZEN_HOLDOUT',f'''Frozen before implementation: 40 cases (10 authorized discovery, 10 unauthorized expansion, 5 observation, 5 item acquisition, 5 prior context, 5 mandatory disclosure). Input hash: `{hold['hash']}`. Fixtures, decisions, coverage expectations and publication behavior remain byte-identical.

Executed once after source freeze. Final decisions: 40/40 correct. Publication choices: 40/40 correct. Full frozen expectations: 39/40. H18 appends a southeast contradiction to the authorized northwest report; FAIL was expected and observed, while coverage was frozen as PASS but correctly returned REVIEW_REQUIRED. No expected value or code was altered after evaluation.

False acceptances: 0. False rejections: 0. Critical false acceptances: 0. Every fallback validates. This developer-authored holdout is not independent blind validation. `holdout_results.json` includes all traces.'''),
('10_HISTORICAL_CANDIDATE_REPLAY',f'''Exact historical candidate:

> {hist}

Entry: FAIL. Final: PASS across semantic validation, legacy hard validation and mandatory coverage. Replay assembly uses the unchanged raw historical string, no fallback. Hook input remains unchanged. `historical_before.json` and `historical_after.json` preserve original/reproduced decisions and claims.

This deterministic replay is distinct from newly generated live wording. It makes no historical live-publication claim.'''),
('11_LIVE_PROVIDER_RESULTS',f'''Provider: OpenAI. Model: `gpt-4.1-mini-2025-04-14`. Existing configured adapter; two requests, zero retries. 895 input + 44 output = 939 total tokens. Provider latencies: 3937.757 ms and 1369.010 ms. No regeneration to chase PASS.

Discovery candidate:

> {new}

Result: FAIL in `_route_assertion` because this finite prefix adds “carefully” and uses “discover that”. Mandatory coverage PASS; deterministic fallback published. Follow-up barrel response: PASS and published. Live validated AI responses: 1; AI publications: 1. Raw outputs, model metadata, usage and publication decisions are in `gameplay_actions.json`, `provider_usage.jsonl`, and `provider_snapshot.json`.

The broad API provider switch remains disabled to isolate this existing experimental narration adapter. Upstream preflight was skipped as in the established harness; recorded adapter metadata and usage establish these two actual requests only.'''),
('12_PLAYER_FACING_PUBLICATION','''Three consecutive supported actions through FastAPI TestClient HTTP `/api/chat?ui_mode=player`: notice discovery, barrel investigation, notice repeat. HTTP statuses 200 throughout. Two initial actions use the live experimental provider. The third injects provider timeout and publishes deterministic repeat fallback in the same session.

One AI response published; two fallbacks. Initial discovery fallback contains the mandatory route; the unrelated barrel publication does not unnecessarily repeat it. Third action confirms session continuity and fallback availability. This exercises the application HTTP route in process; no external TCP listener or browser was used. Evidence: `gameplay_actions.json`, `state_snapshots.json`.'''),
('13_DISCLOSURE_REGRESSION','''New disclosure omission remains REVIEW_REQUIRED and falls back with the exact route. Prior disclosure is accurately referenceable and optional for unrelated actions. Repeat status remains mandatory. Hidden identifier disclosure, unsupported hidden cache and unauthorized detached route assertions remain blocked.

All PR63 disclosure tests are included in the focused regression. The holdout has five prior-context and five mandatory cases. None of the code in `game/mandatory_outcome_coverage.py` changed. H18's stricter coverage result is retained as a frozen expectation mismatch.'''),
('14_FAILURE_INJECTION',f'''{fault['passed']}/{fault['cases']} assessed HTTP publication faults pass: provider unavailable, timeout, empty, malformed, FAIL, REVIEW_REQUIRED, VALIDATION_ERROR, unauthorized discovery, persistent consequence, item acquisition, missing mandatory disclosure and hidden identifier disclosure.

Each uses deterministic fallback, preserves mandatory route text, validates the fallback, matches the feature-disabled resolver/authority control, and accepts a subsequent repeat action. No fault calls the provider.

The original harness's `stable_authority` boolean is false because it incorrectly assumed npc_runtime could not be initialized on the first resolver turn. Exact raw assertions remain in `failure_injection.json`; `failure_injection_assessed.json` explains the correction. Complete bounded authority equals the disabled control in all cases, including the initialized NPC records and normal time-pressure tick. No production change was made to improve this assessment.'''),
('15_STATE_AND_CONTINUITY','''All three live/fault sequence outcomes match the feature-disabled control for bounded authoritative state and mechanical resolution. Full initial and per-action session/character snapshots are captured. Pure validator/development inputs remain unchanged. Narration hooks expose no state writer and record no state write attempt.

No unsupported HP, inventory, equipment, NPC, quest, scene, condition, combat, world flag or clock effect occurs. Initial resolver initialization and deterministic time ticks are matched against control rather than mistaken for narration mutation. Session binding mismatch yields no experimental publication. Canonical data and ATGB evidence hashes are checked in `protected_integrity.json`; source hashes remain frozen after holdout.'''),
('16_REGRESSION_RESULTS',f'''Focused: {focused['passed']} passed, {focused['failed']} failures, {focused['errors']} errors, {focused['skipped']} skipped. New failures: {focused.get('new_failures',[])}. The three historical failures are provider-readiness acceptance and two narration-state-consistency tests. PR55 wrapper: {reg['holdout']['passed']} passed. Broader authority assurance: {broader['passed']} passed, {broader['failed']} known `hard_validation_attempt_1` failures. Full suite not run.

H41 historical exposed fixture replay: FAIL; exact complete-pipeline trace in `h41_regression.json`. PR55–63 safety, persistent consequences, inventory, coverage, disclosure, fallback, fast path and isolation are included. Tests that generate old campaign reports are restored byte-for-byte by the existing regression harness convention.

Initial focused launch collected no tests due to an erroneous copied filename; its collection error is preserved. The filename was corrected and the complete focused suite rerun. Broader and PR55 results were retained without unnecessary rerun. Test commands, node IDs, XML and logs are included.'''),
('17_LIMITATIONS_AND_OPEN_RISKS',f'''Partial outcome: exact historical regression and gate observation are repaired, but a newly generated legitimate discovery carrier remains falsely rejected. Raw wording: “{new}” No tuning followed the frozen holdout.

Finite deterministic validators are heuristic, not semantic proof. Shortened discovery paraphrases must still preserve all mandatory subject/path/landmark details. No claim of universal learn/read/study/recognize/reveal support. Developer-authored holdout has one coverage expectation error; all final decisions and publication choices are correct.

Browser-originated gameplay, natural choice/follow-up mechanics, arbitrary hidden paraphrase safety, human quality assessment, general RPG playability and ATGB competence remain unverified. Three focused and nine broader historical failures remain. Evidence has one explicitly reconstructed mechanical entry source; no fabricated prior hash or provider execution.'''),
('18_NEXT_SESSION',f'''Exactly one primary next step: {metrics['next_step']}

Use the captured live candidate as a new development regression and preserve the already repaired historical candidate, unsupported expansion rejection and state boundaries. Do not rerun or relabel this cycle's holdout. PR-PLAY-65 meaningful choice work remains deferred while this smallest remaining blocker is unresolved. No broad parser campaign, mechanics expansion, commit or push is authorized by this recommendation.'''),
]
for name,body in reports:(REPORT/(name+'.md')).write_text('# '+name.replace('_',' ')+'\n\n'+body+'\n',encoding='utf-8')
print(json.dumps({'reports':len(reports),'verdict':metrics['verdict'],'focused':focused['passed']}))
