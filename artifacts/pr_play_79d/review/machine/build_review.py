"""Generate the closeout review from retained evidence; never synthesize missing measurements."""
import hashlib, json, shutil, subprocess, zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
REVIEW=OUT/'review'
REVIEW.mkdir(exist_ok=True)
def load(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
metrics=load('provider_metrics.json')
baseline=load('baseline.json')
protected=load('protected_after.json')
reg=load('final_audit/regression_results.json')
holdout=load('holdout_results.json')
manifest=load('holdout_manifest.json')
transcript=load('browser_transcript.json')
new=[identity for lane in reg.values() for identity in lane['new_vs_pr_play_78a']]
assert not protected['changed'], 'STOP: protected file mismatch'
assert len(reg)==3, 'Historical regression incomplete'
verdict='B/PARTIAL — publication regressions repaired; final live deduplication verification incomplete'
summary=f'''# PR-PLAY-79D

**{verdict}.** The five original identities pass. Source-bound recall restores previously disclosed information without rediscovery. The renderer selector no longer modifies a repeat resolution. Completed player-safe responses now have one authoritative record at the existing HTTP serialization boundary, including handled errors and direct engine publication.

The browser completed topic change/return, approach, first examination, repeat recall, snapshot, reload, load, and new live NPC dialogue after reload. Five new live NPC lines and one live narration were published across eight typed submissions. No authored-action buttons were clicked. This is a developer acceptance script, not independent external validation.

The physical action exposed one redundant **bounded expression** request. It was repaired and both accepted/fallback development cases pass. The repaired action was not rerun live: the run reached 12 requests. Browser stages span three host revisions; only the post-reload turn exercised the final HTTP publication boundary. Therefore this is not a single uninterrupted final-source browser PASS, and no A/PASS is awarded.

Final source development: **147/147**, including **59 PR79D checks**, the inherited 82 PR79C checks, and six closeout checks. Separate source-oracle/order/isolation checks: 6/6. Frozen developer holdout: **{holdout['passed']}/{holdout['total']}**, run once, hash `{manifest['sha256']}`. It primarily covers recall/projection and trace helpers; the requested broader frozen integrated dialogue/action/renderer coverage remains incomplete.

Historical final-source: focused {reg['focused']['passed']} passed / {reg['focused']['failed_count']} failed; boundary {reg['boundary']['passed']} / {reg['boundary']['failed_count']}; broader {reg['broader']['passed']} / {reg['broader']['failed_count']}. Skipped: {sum(v['skipped'] for v in reg.values())}. New identities vs PR78A: **{len(new)}**. Historical failures are retained, not called clean.

Protected runtime files: **{protected['preserved']}/{protected['count']} unchanged**. Branch `{baseline['branch']}`, HEAD `{baseline['head']}`. Extensive entry dirt is preserved. No commit or push.

Provider: **{metrics['requests']} requests**, **{metrics['input_tokens']} input + {metrics['output_tokens']} output = {metrics['total_tokens']} tokens**, zero new openings, zero retries. Six useful published live responses: {metrics['tokens_per_published_live_response']} tokens/response. This workload is not directly comparable with 79C's 663-token reference. Server gameplay mean {metrics['mean_gameplay_server_ms']} ms, P95/max {metrics['p95_gameplay_server_ms']} ms. Browser paint/completion latency was not instrumented; server time is not substituted.

Next action: one small restored-fixture final-source browser check of an ordinary physical action, its single bounded narration attempt, and its final publication record. No new opening and no large provider cycle. AT-OPT-01 remains deferred until closeout is verified.
'''
docs={
'01_EXECUTIVE_SUMMARY.md':summary,
'02_REPOSITORY_BASELINE.md':f'''# Repository baseline

Branch: `{baseline['branch']}`. HEAD: `{baseline['head']}`. See machine/baseline.json for complete entry status, including unrelated modified/deleted/untracked files. No branch checkout, commit, push, reset or restoration of user data occurred.

Read Development Constitution, NEXT_SESSION, state-authority model, Product Realization validation, review-handoff standard, and portfolio entry guidance. NEXT_SESSION was stale at 79B; current 79C artifacts and the supplied task established the newer baseline. No AGENTS.md or nonempty .agents guidance was found in the inspected project paths.

Runtime changes: game/api.py, exploration.py, publication_contract.py, quarantined_investigation_narration.py, player_http_boundary.py, bounded_improvisation.py. Tests: PR61, PR62 and PR69 assertion corrections, new PR79D closeout/holdout drivers. Session orientation updated. No campaign templates changed.

machine/task_source.diff is cycle-scoped. Tracked preimages were reconstructed from HEAD plus the entry diff; untracked preimages reverse the recorded edits. machine/entry.diff retains the original tracked worktree diff. No claim is made that untracked preimage hashes were captured before editing.
''',
'03_TEST_DATA_ISOLATION.md':f'''# Test-data isolation

tests/conftest.py installs storage isolation before game imports. It configures campaign/session/save/provider locations, disables live test transports and installs a fail-closed audit guard on production data and historical artifacts. Every executed lane has its own basetemp/evidence root. Individual HTTP fixtures seed their own mutable data. Snapshots were explicitly isolated in the new persistence check.

Browser data is a copy of the existing 79C browser campaign. Existing provider ledger is excluded; each host process owns a new exclusive execution ledger outside copied gameplay state. Separate localhost origins isolate browser storage. No provider responses, routing, adjudication, validation or publication were stubbed for the browser.

Initial reproduction attempts using pytest's fixed default basetemp collided; their setup errors are retained and excluded from product verdicts. Unique-root reproductions then established all five failures. A legacy 79C holdout driver attempted to overwrite its historical RESULTS file; the audit guard blocked it. The original archive was not overwritten, and that failed attempted export is retained in gate_final.xml. The new frozen holdout was not rerun.

Protected data: {protected['preserved']}/{protected['count']} entry hashes unchanged. See protected_after.json.
''',
'04_REGRESSION_INVENTORY.md':(OUT/'04_REGRESSION_INVENTORY.md').read_text()+'''

Final exact original identities: all five PASS in final_source_development.xml. PR61's later AI-publication assertion and wording assertion were corrected as documented below; its original missing-recall assertion now passes.
''',
'05_REGRESSION_ROOT_CAUSES.md':'''# Root causes and changed assertions

1. PR61 recall: exploration._repeat_publication emitted only a no-new-information sentence. It never retrieved already explicit source knowledge. Repaired in the existing resolver, using current source binding, known clue identity/text, explicit disclosure, scene provenance and validity checks. No global memory or provider rediscovery was added.
2. PR66 no_new/continuity/fast_path: API finalization copied engine_publication then returned before legacy publication verification. Request-local direct-engine verification now fills the PR66 invariant record without generation. Actual completed publications are recorded separately at PlayerHTTPRoute, after serialization/projection.
3. PR47 matrix[5]: narration_skip stamped the caller's repeat-resolution metadata. The read-only repeat selector now returns its sentence without modifying resolution. The original row == original assertion is unchanged and passes.
4. Browser approach: bounded_improvisation expressed an adjudication, then left its contract eligible for another bounded expression. It now stamps the settled final contract after its one expression opportunity, including rejection/fallback. Two targeted tests protect this.

Changed assertions (none deleted):

- PR61: [True,True,True,True] AI-published flags becomes [True,True,False,True]. Replacement checks engine owner, PASS invariant and recalled ROUTE in actual text. The repeat provider candidate was accepted but was not the published expression, so counting it as visible AI would be incorrect. Resume wording now names the notice board and additionally requires ROUTE.
- PR62: exact no-fact repeat sentence becomes target prefix + known ROUTE + nothing-new status. The exclusion assertion still prohibits ROUTE in unrelated barrel/gate responses; only the legitimate source repeat may contain it.
- PR69 structured/chat: exact no-recall sentence becomes target prefix + no-new status + every originally disclosed clue. Existing unchanged journal equality, no-canary checks, four resolver calls and generation bounds remain. Both new-oracle identities pass in reclassified_and_ordering.xml and the final historical lane.

PR62 and PR69 were passing at entry, reproducing the three later 79C repairs. The new recall contract invalidated their literal no-recall assertions. These are explicit contract/oracle changes, not tests weakened to hide hidden-fact or state failures.
''',
'06_DISCLOSED_FACT_RECALL.md':'''# Disclosed-fact recall

New discovery still uses authoritative adjudication and the existing knowledge ledger. Source provenance is attached to a matching discovered clue record during first discovery. Repetition reads explicit/actionable discovered knowledge; inferred, implicit, invalid, stale, superseded, mismatched-scene and unrelated-source entries are excluded. Catalog text verifies current validity but never supplies output text. Only the stored disclosed text is published.

Historical records without object provenance require same scene, same clue identity, exact text match and a unique current source mapping. Insufficient provenance produces the safe no-new line. There is no LLM reconstruction, discovery reset or global fact dump.

The browser repeat showed the exact northwest mud-track clue and said the examination added nothing new. Knowledge remained byte-equivalent as JSON before/after the repeat. First examination changed knowledge as expected. Resolver-level repeat is read-only. Normal HTTP turns may still update transcript/turn/interaction bookkeeping.

No provider was used to rediscover or reword recall. The existing upstream semantic interpreter still consumed one request on the browser repeat. Removing such interpretation costs is deferred to AT-OPT-01, not hidden as zero total provider use.
''',
'07_SOURCE_BOUNDARIES.md':'''# Source boundaries and validity

Development cases cover two unrelated vocabularies plus the frozen four-source corpus. Tests exclude hidden clues, other source knowledge, other scene/campaign knowledge, modified/contradictory current text, stale/invalid records and ambiguous legacy bindings. Partial/failed discovery never derives an undisclosed remainder from the catalog.

Removal is safe because the production resolver only enters recall after matching a still-addressable source; a removed source is not recovered from player prose. Tests cover helper exclusion and the original source resolver. Source-specific validity depends on structured validity markers and exact current content; arbitrary semantic changes elsewhere in world state are not a new memory/invalidation subsystem.

Player projection strips resolver metadata. Browser exact hidden-fact/canary scan found no exposures; this is exercised-path evidence, not a universal semantic claim. See player_safe_scan.json.
''',
'08_PUBLICATION_TRACES.md':'''# Publication trace ownership

PlayerHTTPRoute is the authoritative completion boundary. It projects and constructs the actual JSON response, then records one completed publication. The same boundary handles direct engine responses, accepted expression, grounded fallback, request validation and sanitized errors. Ordered-turn duplicate replays explicitly skip a new publication event.

Each record contains a unique turn identifier, owner/category/source handler, provider involvement and attempt references, hashes for actually published accepted expressions, hash of the final text, exact final player-facing response, status and validation outcome. Rejected/unpublished candidate text and hidden resolver payloads are excluded. No credentials are recorded. Contract-aware categories distinguish clarification, unsupported action and failure when the resolver supplies the contract.

The PR66 legacy publication object remains a server-body invariant observation, with client_received unknown; it is not a second completed-publication event. Direct-engine verification consumes its request-local binding once. It does not revive the optional narrator.

Eight browser submissions produced eight records. The earliest place-answer record missed alternate-owner provider provenance; original evidence is preserved. That defect was repaired using actual completed provider deltas plus a matching publication context. The final-source post-reload record correctly references its live provider attempt and published dialogue. No retrospective trace rewrite was made.

Final-source development verifies actual 422 error recording, duplicate HTTP replay, provider provenance, accepted-but-unpublished exclusion and category contracts. Trace-write OSError is logged without undoing an already committed gameplay turn.
''',
'09_CONTROLLED_RENDERER.md':'''# Controlled-renderer regression

Original test: tests.test_pr_play_47_controlled_renderer::test_matrix[5]. Input: I examine the rubbing. The test constructs a known-outcome resolution with previously visible mason-mark text, previews three controlled rendering plans, and invokes deterministic narration selection. Starting state and expected payload are the unchanged row snapshot.

The unexpected payload consisted of publication-contract metadata added by narration_skip during its repeat fast path, not a new discovery, renderer state write or provider proposal. Reproduction: renderer_before.xml. Repair: no mutation in the repeat selector. Original row == original and all authority/hidden-exclusion assertions pass unchanged in final_source_development.xml and full historical regression. The offline renderer remains outside gameplay wiring.
''',
'10_DIALOGUE_PRESERVATION.md':'''# NPC dialogue preservation

Five new browser NPC answers were accepted and published verbatim, including topic change to the gate district, return to patrol, and a new patrol follow-up after reload. Existing 79C conversation loaded visibly. Final post-reload output was Gate Guard speech expressing limited knowledge; it did not absorb the player's newly read route clue into NPC knowledge.

Accepted speech was never replaced with third-person narration in the exercised dialogue. Active speaker and campaign context remained scoped. Inherited 79C checks pass, including other-campaign speaker exclusion. Browser evidence is real UI submission, not inferred from HTTP-only traffic.
''',
'11_ACTION_RESULT_FIDELITY.md':'''# Physical-action fidelity

Browser input: I approach the notice board. Visible result: You walk over and stand beside the Notice board. The authoritative physical ledger recorded approach and the source identifier. No scene transition, reward, check or mechanical success was invented. Full session before/after is retained per browser turn; overall character/world/combat before/after is retained separately.

The provider expressed the committed action. The extra bounded expression discovered here was an efficiency defect, not an uncommitted movement. It is repaired but was not rerun live under the exhausted 12-request ceiling. Final-source physical accepted/fallback dedup tests both pass.
''',
'12_NARRATION_DEDUPLICATION.md':'''# Narration deduplication

Zero redundant primary narration calls were observed. Provider purpose counts are five contract interpretations and seven bounded expressions, with no new opening. A complete engine recall remains final and does not invoke primary narration.

One redundant bounded expression occurred on the browser approach. The owning bounded physical path now marks its result settled after its first expression opportunity and stamps FINAL_ENGINE_RESPONSE. Accepted and rejected-first-expression tests each prove exactly one opportunity even when narration_skip is subsequently called. Live verification of that repaired physical path is the dominant remaining closeout blocker.
''',
'13_PROVIDER_LEDGER_ISOLATION.md':'''# Provider execution state

The existing provider-budget owner deliberately creates its ledger exclusively and refuses an inherited file. This is appropriate admission protection, not campaign truth. Production accounting was not changed or erased.

Fixture preparation excludes the copied provider_usage.jsonl while preserving gameplay files and snapshot provenance. Each browser host revision uses its own newly named execution ledger. The later phase limit was reduced to one request so combined actual usage could not exceed the remaining allowance. Original phase ledgers remain retained. Snapshot restore does not replace the process ledger.

The browser resumed the restored campaign and completed new live dialogue with a fresh process-owned ledger. No admission, token-budget, retry or ordering controls were bypassed.
''',
'14_DEVELOPMENT_TESTS.md':'''# Development checks

Final_source_development.xml: 147/147 (59 new PR79D cases, 82 inherited PR79C checks, six supporting/original checks). All original five identities pass, with PR61's documented provenance/wording oracle correction. Reclassified_and_ordering.xml: 6/6, including both PR69 source-repeat forms, overlapping reads/ordered writes, duplicate requests, independent campaigns and cross-campaign fact exclusion.

Retained intermediate failures include the initial five reproductions, the later PR61 wording/provenance assertion, two fixture-setup errors in the new physical test before an actual addressable object was supplied, and the blocked archived holdout export. None is silently replaced by a final count. No tests make real provider calls.
''',
'15_FROZEN_HOLDOUT.md':f'''# Frozen developer holdout

48 cases; {holdout['passed']}/48 pass in the original gate_final.xml. Manifest SHA256: `{manifest['sha256']}`. Frozen before implementation. The fixture was not edited, rerun or tuned after results. Per-case original results are in holdout_results.json.

Four unrelated source vocabularies exercise recall, provenance, hidden exclusion, modification/removal, stale/implicit facts and completed-trace composition. These are helper-level cases. Travel/conversation/reload conditions set or serialize fixture state; they are not 48 full campaign lifecycles. The matrix does not independently freeze dialogue, physical-action or controlled-renderer paths. Those paths have development/browser evidence, not a claim of equivalent frozen coverage. This limitation contributes to the conservative partial verdict.

The separately attempted inherited 79C holdout export was blocked from overwriting its original RESULTS file. It is not reported as an additional clean frozen holdout.
''',
'16_HISTORICAL_REGRESSION.md':f'''# Final historical regression

Final source and final assertion set: machine/final_audit. Same suites as the 79C regression runner, compared against archived PR78A exact failure identities.

```json
{json.dumps({k:{name:v[name] for name in ('passed','failed_count','skipped','new_vs_pr_play_78a','cleared_vs_pr_play_78a')} for k,v in reg.items()},indent=2)}
```

All historical failure identities remain listed in regression_results.json and individual XML. New identities: {json.dumps(new)}. Earlier intermediate full runs showed the two obsolete PR69 no-recall expectations; their literal assertions were replaced by stricter source-recall assertions and both were rerun before the final complete lane. Repeated runs occurred only after new source or assertion changes; they are retained as intermediate evidence, not substituted for the final lane.
''',
'17_BROWSER_ACCEPTANCE.md':'''# Browser acceptance

Actual in-app browser; isolated initialized 79C campaign; eight new typed chat submissions. No authored-action buttons. Sequence: load existing conversation; ask gate-district question; return to patrol; repeat that topic sequence after provenance repair; approach notice board; investigate; repeat; Create Snapshot; reload; Load the named snapshot; ask patrol follow-up. Five new NPC answers and one live action narration were published. The final post-reload turn used final source and final HTTP completion recording.

Screenshots: repeated_investigation.jpg and snapshot_saved.jpg. Exact typed inputs, exact returned responses, actual network status/server timing, session before/after and publication records are retained. Browser-visible post-reload speech was observed in the UI; its screenshot was not separately saved. Browser paint latency and exported UI timing were not captured.

Host phases used localhost ports 8098, 8099 and 8100. Campaign and snapshots were preserved; execution ledgers were new. This is a restored continuation, not a fresh opening. The whole acceptance sequence did not run again under one final-source host after the late boundary/dedup repairs. This is a substantive limitation and precludes an unqualified final-source browser PASS.
''',
'18_PROVIDER_EFFICIENCY.md':f'''# Provider efficiency

```json
{json.dumps(metrics,indent=2)}
```

Budget respected. There was no opening generation. Zero retry attempts/tokens were observed; retries were disabled. Rejected-output count/cost cannot be fully assigned because completed provider rows do not retain every expression validation outcome. It is explicitly unmeasured, not asserted zero.

Six useful live publications include five NPC answers and one action-result narration. The 1332.17-token figure includes semantic interpretation costs and the observed duplicate bounded expression. It is not a controlled improvement/regression comparison with 79C. Interpretation cost/routing attribution is documented for the deferred AT-OPT-01 audit, not optimized here.
''',
'19_AUTHORITY_AND_ISOLATION.md':f'''# Authority and isolation

Protected-file preservation: {protected['preserved']}/{protected['count']}. No user data was restored, overwritten or regenerated. Hidden-information exposures, exact canary matches, mandatory source-disclosure omissions and critical unsafe publications observed on the exercised browser outputs: zero. No provider committed authoritative state.

Repeat knowledge before/after is unchanged. Source clue disclosure remains separate from NPC knowledge. The browser snapshot restored campaign identity, knowledge and conversation context. Ordering, duplicate chat, independent campaigns and cross-campaign fact tests pass. Branch-choice isolation remains protected by the inherited PR79C suite; no authored branch was activated by browser actions.

Evidence is scoped: per-turn browser snapshots contain session state; full character/world/combat state is retained at overall fixture start/end, not at every turn. Exact scans do not prove universal absence of semantically paraphrased leaks.
''',
'20_LIMITATIONS_AND_RISKS.md':'''# Limitations and risks

- Final physical deduplication repair has deterministic accepted/fallback proof but no fresh live physical rerun.
- Browser sequence spans revisions; only the post-reload turn used the final HTTP boundary. The earliest trace's provider provenance was wrong and is preserved, not rewritten.
- Browser paint/completion latency was not measured. Server latency is separately labeled.
- New frozen holdout primarily covers recall and trace helpers; it is narrower than the requested complete integrated frozen matrix. No independent external validation claim.
- A legacy archived holdout output write was safely blocked. Its failed export remains evidence.
- Structured provenance/validity controls are conservative. Historical missing/ambiguous mappings, modified facts and invalid facts can yield no recalled text. No broad memory migration/invalidation redesign was introduced.
- Existing semantic interpretation still costs provider requests for some deterministic investigation/actions. This is deferred to AT-OPT-01.
- Historical baseline failures remain; no full-repository green claim.
- Detailed rejected-output cost is unavailable from the retained ledger; no fabricated zero.
''',
'21_NEXT_SESSION.md':'''# Next session

Keep PR-PLAY-79D open as a small closeout. Read executive summary, narration deduplication, browser acceptance, task_source.diff and final_audit results. Reuse the isolated initialized campaign and normal browser flow. Perform one final-source ordinary physical action with live provider enabled, verify one bounded expression attempt and one final completed publication record. Capture browser-visible completion timing. No new opening, no large live cycle, no commit/push.

Complete the requested broader frozen integrated coverage with a new explicitly frozen supplemental matrix before further implementation changes. Do not modify or rerun the existing 48-case holdout as if it were new evidence.

Only after verified closeout should AT-OPT-01 begin as a primarily read-only attribution/routing audit. Do not implement it automatically.
'''}
docs['09_CONTROLLED_RENDERER.md'] += '\nThe original standalone unexpected payload was not separately captured; its failed equality/diff is retained in renderer_before.xml. Final actual before/after payloads and the three controlled outputs are captured in controlled_renderer_payloads.json.\n'
for name,content in docs.items(): (REVIEW/name).write_text(content,encoding='utf-8')
machine=REVIEW/'machine';machine.mkdir(exist_ok=True)
names=['baseline.json','entry.diff','task_source.diff','final_source.json','protected_after.json','04_REGRESSION_INVENTORY.md',
       'renderer_before.xml','single.xml','repro_s.xml','repaired.xml','gate_final.xml','final_source_development.xml',
       'reclassified_and_ordering.xml','holdout.json','holdout_manifest.json','holdout_results.json',
       'browser_fixture.json','browser_network.jsonl','browser_publication.jsonl','browser_transcript.json',
       'provider_metrics.json','provider_completed.json','provider_retries.json','player_safe_scan.json','authoritative_before_after.json']
names += ['baseline.py','freeze_holdout.py','run_regression.py','browser_host.py','analyze_evidence.py','task_delta.py','build_review.py']
names += ['supplement_evidence.py','capture_renderer.py','controlled_renderer_payloads.json','regression_inventory.json',
          'source_provenance.json','provider_ledger_isolation.json','browser_snapshot.json','save_reload_evidence.json']
for path in OUT.glob('browser_provider_usage*.jsonl'):names.append(path.name)
for name in names:shutil.copy2(OUT/name,machine/name)
shutil.copy2(ROOT/'artifacts/pr_play_78a/review_pack/machine/regression_results.json',machine/'historical_baseline_pr78a.json')
shutil.copy2(ROOT/'artifacts/pr_play_79c/regression_results.json',machine/'historical_pr79c.json')
fixture=load('browser_fixture.json')
(machine/'browser_fixture_hash.json').write_text(json.dumps(dict(
    sha256=hashlib.sha256(json.dumps(fixture['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    method='SHA256 of canonical JSON file manifest; includes each copied gameplay file path and digest, excludes execution ledger'),indent=2))
target=machine/'final_audit';target.mkdir(exist_ok=True)
for name in ['regression_results.json','focused.xml','focused.txt','boundary.xml','boundary.txt','broader.xml','broader.txt']:
    shutil.copy2(OUT/'final_audit'/name,target/name)
shots=REVIEW/'screenshots';shots.mkdir(exist_ok=True)
for path in (OUT/'screenshots').glob('*.jpg'):shutil.copy2(path,shots/path.name)
sources=REVIEW/'source'
for entry in load('final_source.json'):
    path=sources/entry['path'];path.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/entry['path'],path)
try:
    local_zone=ZoneInfo('America/New_York')
except Exception:
    # This run's explicit client date is 2026-11-08, after the DST transition.
    local_zone=timezone(timedelta(hours=-5))
timestamp=datetime.now(local_zone).strftime('%Y%m%d-%H%M%S')
archive=ROOT/'handoff'/f'CURRENT_REVIEW({timestamp}).zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as bundle:
    for path in sorted(REVIEW.rglob('*')):
        if path.is_file():bundle.write(path,path.relative_to(REVIEW).as_posix())
(OUT/'archive_path.txt').write_text(str(archive),encoding='utf-8')
backup=OUT/'prior_handoff';backup.mkdir(exist_ok=True)
for name in ['CURRENT_REVIEW.md','CURRENT_REVIEW.zip','REVIEW_MANIFEST.json']:
    old=ROOT/'handoff'/name
    if old.exists() and not (backup/name).exists():shutil.copy2(old,backup/name)
(ROOT/'handoff/CURRENT_REVIEW.md').write_text(summary+'\nReview archive: '+str(archive)+'\n',encoding='utf-8')
shutil.copy2(archive,ROOT/'handoff/CURRENT_REVIEW.zip')
(ROOT/'handoff/REVIEW_MANIFEST.json').write_text(json.dumps(dict(campaign='PR-PLAY-79D',verdict=verdict,
    archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),files=[p.relative_to(REVIEW).as_posix() for p in REVIEW.rglob('*') if p.is_file()]),indent=2),encoding='utf-8')
handoff=ROOT/'docs/NEXT_SESSION.md'
prior=handoff.read_text(encoding='utf-8')
orientation='''# NEXT_SESSION — PR-PLAY-79D (2026-11-08)

**B/PARTIAL — five publication regressions repaired; final live deduplication check remains.** Source-bound recall and publication/error observability are repaired. Controlled-renderer repeat selection is read-only. Final development 147/147; separate oracle/order/isolation 6/6; frozen developer helper holdout 48/48, not external validation. Full historical final-source results and exact identity comparison are in artifacts/pr_play_79d/final_audit.

The real browser completed topic change/return, approach, investigation/repeat recall, snapshot/reload/load and new live dialogue after reload. Five new NPC lines and one live narration; 12 requests, 7,993 tokens; no opening. One duplicate bounded physical expression was observed and repaired, accepted/fallback checks pass, but it was not rerun live. Browser stages span revisions; paint latency is unavailable. No unqualified final-source browser PASS. Protected files 150/150; no unsafe publication or hidden exposure observed.

Next: one small restored-fixture final-source browser physical-action check proving one expression opportunity and one completed trace. Capture browser-visible latency; no new opening or large live cycle. Broader frozen integrated coverage is also still required; freeze a supplemental matrix before any further source tuning and keep the existing holdout unchanged. AT-OPT-01 remains deferred; do not implement it until closeout is verified. No commit/push.

Read artifacts/pr_play_79d/review/01_EXECUTIVE_SUMMARY.md, 12_NARRATION_DEDUPLICATION.md, 17_BROWSER_ACCEPTANCE.md, machine/task_source.diff and final_audit results. Current review archive is recorded in artifacts/pr_play_79d/archive_path.txt. Branch feature/product-realization at d40f1ed198236c604085f1c842ead267a8104ce2; extensive unrelated entry dirt remains preserved.

---

'''
if prior.startswith('# NEXT_SESSION — PR-PLAY-79D'):
    prior=prior.split('\n---\n\n',1)[1]
handoff.write_text(orientation+prior,encoding='utf-8')
print(archive)
