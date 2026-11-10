"""Build the requested twenty reports from actual machine-readable evidence."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/campaigns/product_realization/pr_play_67';REPORT.mkdir(parents=True,exist_ok=True)
def read(name):return json.loads((OUT/name).read_text())
metrics=read('metrics.json');reg=read('regression_summary.json');hold=read('holdout_summary.json')
assert metrics['hidden_sentinel_exposures']==0 and read('protected_integrity.json')['passed']
assert read('raw_authority_audit.json')['passed'] and read('freeze_integrity.json')['unchanged']
boundary=reg['boundary'];focused=reg['focused'];new=reg['new_focused_failures']
verdict='A — PASS / PLAYER-SAFE HTTP BOUNDARY ESTABLISHED' if not new and not boundary['failed'] else 'B — PARTIAL / PROJECTION INCOMPLETE'
next_step='PR-PLAY-68: AI PRESENTATION ACCEPTANCE & NATURALNESS' if verdict.startswith('A') else 'Complete the remaining HTTP-boundary regression compatibility checks; preserve the allowlist and frozen holdout.'
common='No commit or push. Zero live-provider requests. Existing narration validators, deterministic resolution and persistence owners were not changed. '
reports={
'01_EXECUTIVE_SUMMARY':f'''{verdict}

The critical leak reproduced through real localhost TCP with experimental narration disabled and enabled. Explicit source-specific nested DTOs now exclude internal state from all registered /api JSON responses. 78 endpoint/fault HTTP requests and 50 one-shot developer-authored holdout cases contain zero hidden sentinel exposures; a separate ten-request raw-authority comparison passes for all five actions. The exact milestone sentence survives the final chat HTTP response; server stores and snapshots retain hidden information.

Development: 42 passed. Frozen holdout: {hold['passed']}/50 (developer-authored, not independent external validation). Focused: {focused['passed']} passed / {focused['failed']} failed. Boundary/frontend/persistence: {boundary['passed']} passed / {boundary['failed']} failed. Broader: 9 historical failures. New focused failures: {len(new)}. See regression report for identities and contract-test migration.

Browser verifies initial scene, structured investigation, existing exit travel, character/inventory and discovered-clue journal. Its milestone action button still displays a legacy refusal, while the exact fact appears in the journal. An offline entry-source comparison reproduces the identical refusal: preexisting and outside this projection repair. Five-action chat replay passes. This is not a claim of natural narration or universal semantic safety.

{common}Primary next step: {next_step}.
''',
'02_BASELINE_AND_SCOPE':'''Commit d40f1ed198236c604085f1c842ead267a8104ce2. Entry worktree was extensively dirty. baseline.json retains the exact status and content hashes for data/, artifacts/atgb/ and prior PR66 evidence. entry_source/ retains relevant dirty source and subsequently migrated tests. implementation.diff compares against these entry copies, not HEAD. Prior evidence and protected baseline data are not authorized repair targets.

Read the Development Constitution, NEXT_SESSION, state-authority doctrine, validation-evidence standard, review-handoff standard, Product Realization bootstrap, PR66 baseline/replay/incident/regression source and the relevant runtime/tests. No applicable AGENTS.md was found. No delegation used. Experimental gates remain default off/session-bound; this cycle uses isolated test-process opt-ins only.

Primary failure class: implementation. The existing classifier explicitly defaulted unknown keys to public. A player HTTP DTO owner replaces that classification at the HTTP boundary, without changing the shared key-channel utilities used by internal tools/prompts.
''',
'03_ORIGINAL_LEAK_REPRODUCTION':'''original_leak_reproduction.json captures GET /api/state and POST /api/chat {"text":"I examine the notice board."} over actual localhost TCP, flags disabled and enabled; all return 200. The complete JSON schemas and redacted values are retained. All five original paths reproduce: session.gm_notes[0], world.gm_only.motivation, scene.scene.discoverable_clues[].text, scene.scene.gm_notes[0], scene.scene.private_notes. Representative synthetic values: CANARY_GM_NOTE, CANARY_NPC_MOTIVE, CANARY_UNDISCOVERED_CLUE. They are unauthorized. The frontend does not require these fields.

Other exposed structures include the internal quest journal, unrelated world state, undiscovered clue identifiers, faction plans, NPC topics, internal resolver objects and future scene IDs. Existing authored fixtures were used; no new defect was invented. Prior incident evidence remains at artifacts/pr_play_66/critical_incident.json and was not rewritten. Redacted complete parsed JSON bodies preserve schema; serialized_http_payloads.json explicitly labels reserialized JSON rather than claiming original wire formatting.
''',
'04_ENDPOINT_INVENTORY':'''endpoint_inventory.json enumerates registered routes, methods, handlers, boundary class, observed HTTP counts and statuses. Player state/session/scene refresh and resume share GET /api/state. Player history uses GET /api/log. Runtime routes include /api/chat, /api/action, /api/start_campaign, /api/new_campaign, /api/reset_session, /api/scene/activate, /api/character, /api/import_sheet, /api/response_mode, /api/reset_combat, /api/clear_log and /api/snapshots (GET/POST), /api/snapshots/load.

/api/campaign, /api/scene and /api/world writes require privileged mode and are denied to player HTTP; /api/debug_trace is denied. Requests for author/debug HTTP modes remain 403 under the existing policy; no new authentication framework was added. Root/static UI and generated docs/OpenAPI serve no runtime campaign state. No distinct campaign-load endpoint exists: snapshot load is the existing loading/continuation operation.

Every registered /api handler receives the shared PlayerHTTPRoute final allowlist boundary. Successful, rejection, initialization failure, validation failure, exception and fallback paths were inspected. Multipart import covers valid sheet and malformed JSON.
''',
'05_PLAYER_SAFE_RESPONSE_CONTRACT':'''response_contract.json documents each allowlisted leaf's source, purpose, visibility rule, frontend consumer, optionality, safe default and JSON behavior. The executable schemas live in game/player_http_projection.py. State envelopes keep public_state; runtime action responses retain the existing flat shape. No internal object is copied wholesale to the player.

Allowed: session/run IDs; current/visited scene identity; public scene description and visible facts; player-sheet stats, finite numeric skill ranks, explicit inventory and spell records; existing published journal facts/clues/leads; server-filtered affordances with public labels/prompts/targets; current public NPC roster; status/save-slot summaries; final published narration; player log input and narration. Resolution is an empty compatibility placeholder. Unknown nested fields are omitted. Wrong-typed object leaves become empty safe primitives, never stringified objects.

Absent optional fields are omitted. Invalid strings/lists/numbers/booleans become empty string/list/zero/false. Empty world {} intentionally represents missing per-item visibility contracts. Numeric skills are a documented player-sheet identifier namespace, not an arbitrary nested JSON exception. Safe statuses/errors are finite allowlists; unexpected diagnostic errors become actionable generic copy.
''',
'06_PROJECTION_ARCHITECTURE':'''Authoritative storage → compose_state / existing publication owners → explicit player-state DTO → response composition → player-response DTO → final PlayerHTTPRoute JSON allowlist → client. Existing action/chat/start helpers project before ordinary serialization; the route also decodes the locally staged JSON response and reprojects before any body reaches the network. This last defense covers other existing endpoints and explicit JSONResponse failures. It incurs local reencoding; measured total HTTP times include this.

The pure projector allocates fresh containers, performs no I/O, resolves no actions, calls no provider and owns no persistence. Raw authoritative state remains available to server resolvers, future scenes and snapshots. Legacy internal compose_state and local Python author/debug projections retain their separate tooling contracts; HTTP privileged modes remain blocked.

The API router class is the existing response-adapter seam: a narrow shared boundary avoids independent per-endpoint blacklists. FastAPI request-validation exceptions and ordinary exceptions get safe status/error objects; detailed diagnostics remain server-side.
''',
'07_NESTED_DATA_PROTECTION':'''Explicit schemas protect inventory items, attacks/damage, hit points, spells/slots, NPC roster, interaction context, affordances, known clues, journal leads/effects, save slots and response envelopes. No arbitrary dictionaries/lists are accepted as a leaf. Hidden values under innocuous future keys, inventory descriptions, lead private notes, optional metadata and object-valued public-looking scalars are excluded.

Sentinel cases inspect complete JSON, not narration alone. The original five fields, undiscovered catalog and event triggers, private motives/objectives, provider prompts, validation traces and state diffs do not cross the boundary. Safe narration remains the output of the preexisting publication/validation owners: the DTO is not a semantic validator for arbitrary text in a legitimately authorized scalar.
''',
'08_DISCOVERY_VISIBILITY':'''The scene discoverable_clues catalog never crosses HTTP. Journal discovered_clues and ui.clues are sourced from the existing authoritative knowledge/publication owners. Newly selected information enters these views after deterministic resolution; repeats preserve known facts without adding a new discovery. Existing revealed_hidden_facts publication into journal known_facts remains with game.journal.

Only current/visited scene IDs populate the scene picker, replacing the complete future-scene catalog. Server-filtered affordances remain available for supported exits. World factions/projects/events lack a reliable item-level player-publication contract: omit them rather than guessing. NPC private role/trust/attitude are omitted. No new discovery or world authority was introduced.
''',
'09_FRONTEND_COMPATIBILITY':'''static/app.js was inspected and left unchanged. It reads character.hp/ac/attacks/spells/skills/inventory, public scene header/summary, session response_mode/active_scene_id, save summaries/snapshots, player name, ui affordances/living enemies/NPCs/interaction, and journal facts/clues/leads/status. These have explicit projected representations. Optional resolution details now display {}; internal GM metadata has no legitimate player display purpose.

World factions/projects/events were convenience reads of raw internal structures; they now render existing empty-state UI because visibility is not established. The scene picker lists known locations only. No UI redesign was introduced. Existing frontend static contract tests, backend mode tests and snapshot tests run in the boundary lane.

Browser-originated smoke observed the real app rendering current scene, character/inventory, notice-board action, existing patrol exit and exact discovered milestone journal text. A structured milestone action narration refusal reproduces unchanged in the entry source; browser_entry_comparison.json and browser_smoke.png preserve evidence. HTTP separately verifies campaign reset/start, load/resume and safe errors; those were not browser-verified.
''',
'10_DEVELOPMENT_TESTS':'''42 new focused development tests pass (development.xml). They exercise twenty internal/unknown source paths, six object-valued public scalar probes, both experimental flag modes over complete gameplay/state HTTP, six failure forms, and eight player-field/authority/discovery/repeat/isolation cases. The previous 45 PR66 publication tests and PR55–65 consequence/disclosure/isolation tests run in the aggregate lane.

All assertions for hidden data inspect serialized complete responses. Existing tests that asserted server-only resolver or GM publication metadata through HTTP were migrated to persisted server log assertions, adding explicit assertions that HTTP metadata/resolution are absent/empty. No authoritative assertion was removed. Unknown-mode error wording now expects safe generic copy without request echo. Initial failures and final reruns are preserved separately.
''',
'11_ADVERSARIAL_LEAKAGE_TESTS':'''Existing CANARY_* fixtures carry GM notes, private NPC motives, hidden destination/clue identifiers, quest twists and unrelated world data. Frozen HOLDOUT_SENTINEL_* cases add internal fields and nested objects. Synthetic exception/import/request sentinels exercise error serialization. Full-body scans detect zero exposures after repair. Source sentinels remain in server state and serialized snapshot storage.

Fixtures and schema paths are in frozen_holdout.json and tests/test_pr_play_67_player_projection.py. Leakage checks do not infer privacy from key names alone: unknown leaf values under innocuous nested keys are excluded by source-specific schemas. An actual player-authorized narration/string field still relies on its established upstream authority; this cycle does not claim universal semantic information-flow proof.
''',
'12_FROZEN_HOLDOUT':f'''50/50 cases pass; zero failures. Distribution: 15 hidden-field, 10 nested-object, five each discovery/error/frontend/isolation/preservation. Frozen before implementation in frozen_holdout.json with SHA-256 {hold['sha256']}. Implementation freeze was recorded before the single holdout execution; source/frozen development-test hashes remain unchanged. Regression-test migrations occurred later without changing frozen production code.

Every case uses actual TCP /api responses and inspects complete serialized output; preservation cases compare authoritative state independently. Nested cases place an innocuously keyed object under the named field to challenge scalar/object confusion. Results are developer-authored evaluation, not independent external or blind validation. No tuning against holdout failures occurred; none failed. Raw result records remain unchanged.
''',
'13_REAL_HTTP_INTEGRATION':'''78 endpoint/fault requests (70 primary plus eight supplemental) use actual Uvicorn/FastAPI localhost TCP and urllib, not solely TestClient. Fifty holdout cases and ten raw-authority control requests are separate. Requests, status, complete redacted JSON, wire-byte counts, timings and leakage scans are preserved in http_integration.json, failure_injection.json, supplemental_http.json, gameplay_replay.json and serialized_http_payloads.json.

Modes enabled and disabled cover state refresh, actions, log, scene activation, character updates, response mode, snapshot list/save/load, reset, new/start campaign, author/debug denial, unsupported action and request validation. Supplemental multipart imports exercise valid and malformed input. Initialization/resolution/encoding exceptions return safe 500 rather than fabricated successful gameplay. All servers were ephemeral and stopped after capture. Holdout figures count cases; some cases issue multiple HTTP requests.
''',
'14_GAMEPLAY_REPLAY':'''Both narration flag modes complete five consecutive HTTP chat actions: investigate the notice board; follow the missing patrol rumor; investigate the weathered milestone; repeat; investigate again. Authoritative movement reaches old_milestone. The exact milestone sentence appears in the enabled final narration and journal: "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear."

No unauthorized new repeat discovery. Disabled-provider control narration can remain the existing stub/refusal; authorized clues remain in final HTTP journal state. Enabled PR66 publication recovers trusted mandatory discoveries and does not replay resolution/provider effects. Request/status/full body, narration, authority before/after and latency are retained per action. Raw authority comparison passes 5/5, including clocks and turn counts.
''',
'15_FAILURE_INJECTION':'''Injected unavailable provider, timeout, FAIL, REVIEW_REQUIRED, VALIDATION_ERROR, malformed/empty candidate, authoritative resolution failure, campaign initialization failure, error object metadata, response serialization failure, unexpected nested/future fields, public-looking objects, session mismatch, disabled/enabled gates, session/campaign reload and malformed request/import.

Recoverable narration failures retain the exact mandatory discovery. Authoritative/serialization failures return safe errors; a serialization failure may occur after state commit and is not a client-delivery acknowledgement. No provider retry or duplicate resolution was added. Optional absent fields have safe defaults; unknown fields fail closed. See failure_injection.json, supplemental_http.json, holdout_results.json and development.xml for the scope actually executed.
''',
'16_STATE_AND_PERSISTENCE':'''Projection is pure and does not delete or rewrite GM state. Both modes retain session GM notes, world private motives and original scene-template canaries. Full snapshot files retain synthetic hidden values; snapshot load restores them while the player response excludes them. Projection tests independently compare source objects before/after and mutate a projected item to verify container detachment.

raw_authority_audit.json compares unredacted in-memory authoritative world/character/combat, scene, visited locations, runtime discovery/overlays, clocks, turn counter and GM notes across identical five-action enabled/disabled runs: 5/5 equal. Earlier full-session comparisons differ in session IDs, latency/debug stamps and presentation-memory snippets; those raw results are preserved, not relabeled as complete session equality. Protected hashes are in protected_integrity.json.

Existing explicit new-campaign/session reset semantics still clear runtime state by design; projection does not perform those resets. The app has one active persisted campaign store, not a multi-tenant session model; session-bound experiment tests do not prove a new concurrent authorization system.
''',
'17_REGRESSION_RESULTS':f'''Completed focused aggregate: {focused['passed']} passed / {focused['failed']} failed / {focused['errors']} errors, {focused['collected']} collected. Boundary/frontend/persistence: {boundary['passed']} passed / {boundary['failed']} failed. Broader: {reg['broader']['passed']} passed / {reg['broader']['failed']} failed. New focused failures: {json.dumps(new)}.

Historical known focused failures: provider accounting readiness not live execution; two narration-state-consistency clue-update cases. Broader nine hard_validation_attempt_1 authority-assurance failures are unchanged historical failures. PR66's obsolete PR49 static assertion and malformed-output aggregate failure are evaluated by this completed run, not assumed clean. Initial PR67 aggregate was 870 passed / 26 failed; 23 new assertions read deliberately private HTTP metadata, plus one boundary error-wording assertion. Contract-test migrations retain server assertions against persisted logs and explicitly check the safe HTTP shape.

regression_summary_initial.json and initial logs preserve the first run. An intermediate rerun completed 891 passed / five failures: the three historical failures and two newly observed WinError 5 failures in atomic session-file replacement (before projection). Both affected tests pass in a separate diagnostic. The focused retry is recorded separately; neither Windows error is silently relabeled historical, and it does not conclusively explain PR66's older malformed-output 500. Final logs and XML preserve the rerun; no full repository suite or official ATGB was run. No interrupted run is reported as completed. Generated protected replay evidence is restored to entry bytes after each regression lane.
''',
'18_PERFORMANCE':f'''300 local projection/serialization samples: mean projection {metrics['projection_mean_ms']:.3f} ms (max {metrics['projection_max_ms']:.3f} ms); projected JSON encoding mean {metrics['serialization_mean_ms']:.3f} ms. Primary 70 TCP requests: mean {metrics['http_mean_ms']:.3f} ms, max {metrics['http_max_ms']:.3f} ms. Ten replay gameplay actions average {metrics['gameplay_mean_ms']:.3f} ms. Supplemental/holdout/control requests are separate datasets and are not silently mixed into these latency statistics.

Matched first-action wire sizes, disabled/enabled: before {metrics['before_action_bytes']} bytes; after {metrics['after_action_bytes']} bytes. Actual measurements include local safe response reencoding in the route adapter. These data show payload reduction, not a controlled throughput/latency improvement. No provider calls, extra resolution or database round trips were introduced.
''',
'19_LIMITATIONS_AND_OPEN_RISKS':'''No universal semantic safety claim, official ATGB score, live-provider naturalness evaluation or external independent holdout. Browser smoke covers core rendered flow; reset/load/error UI paths have HTTP rather than browser verification. Single active persisted campaign architecture remains unchanged. No delivery ACK guarantee after disconnect/encoding failure.

Private world factions/projects/events and NPC numeric trust/private roles have no usable public visibility contract and fail closed; UI shows its existing empty states. This is deliberate visibility restriction, not proof that all future content can be safely published. Authorized text fields rely on existing content/publication semantics; storing a secret directly in a field contractually designated public remains an authoring/authority error.

Preexisting structured milestone button narration refusal persists in entry and repaired source; the exact clue remains visible in journal and chat replay publication works. Three focused and nine broader historical failures remain. See regression_summary.json for any additional unresolved final failures; no new failures are relabeled historical.
''',
'20_NEXT_SESSION':f'''Verdict: {verdict}. Primary next step (exactly one): {next_step}.

Read reports 01/05/09/17/19 and artifacts/pr_play_67/{{endpoint_inventory,response_contract,holdout_summary,raw_authority_audit,regression_summary,protected_integrity}}.json. Check archive_path.txt for the exact dated CURRENT_REVIEW bundle. Preserve the HTTP allowlist boundary, server authority, PR66 mandatory publication, provider-free controls and default-off/session-bound flags. Do not rerun or tune this frozen holdout. No commit or push was authorized.
'''}
for name,body in reports.items():(REPORT/(name+'.md')).write_text('# '+name[3:].replace('_',' ')+'\n\n'+body,encoding='utf-8')
(OUT/'verdict.json').write_text(json.dumps(dict(verdict=verdict,next_step=next_step),indent=2)+'\n')
print(verdict)
