"""Offline evidence analysis and packaging. Never imports application entry points."""
from pathlib import Path
from datetime import datetime
import subprocess
import ast
import difflib
import hashlib
import json
import shutil
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
LIVE = ROOT / 'artifacts/atgb/automated_playtests/20261101T153625Z-02fc6545bc28'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))


def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def report(name, value):
    (OUT/name).write_text(value.strip()+'\n', encoding='utf-8')


before = read(OUT/'before_request_local.json')
after = read(OUT/'assembled_request.json')
payload = json.loads(before['input'][-1]['content'])
compact = lambda v: json.dumps(v, ensure_ascii=True)
old_chars = sum(len(m['content']) for m in before['input'])
new_chars = sum(len(m['content']) for m in after['input'])
schema_chars = len(compact(after['text']['format']))
rows = []
for i, message in enumerate(before['input'][:-1]):
    rows.append({'category': f"system {i+1}: " + ('legacy narration' if i == 0 else 'selection instruction'),
                 'characters': len(message['content'])})
for key, value in payload.items():
    rows.append({'category': 'user.'+key, 'characters': len(compact({key: value}))-2})
# JSON object delimiters plus comma separators between the disjoint key slices.
rows.append({'category': 'user JSON separators', 'characters': 2+2*(len(payload)-1)})
assert sum(r['characters'] for r in rows) == old_chars
for row in rows:
    row.update(estimated_tokens=round(row['characters']/4, 1), percent=round(100*row['characters']/old_chars, 2))
rows.sort(key=lambda r: -r['characters'])
measurements = {'method': 'Content character counts; estimated tokens = characters / 4. No local tiktoken. Excludes provider framing; schema counted separately.',
    'observed_pr_play_17': {'input_tokens': 26986, 'output_tokens': 2050, 'total_tokens': 29036},
    'reconstructed_before': {'message_content_characters': old_chars, 'estimated_tokens': old_chars/4, 'schema_characters': 0, 'categories': rows},
    'reconstructed_after': {'message_content_characters': new_chars, 'schema_characters': schema_chars,
        'total_context_characters': new_chars+schema_chars, 'estimated_tokens': (new_chars+schema_chars)/4,
        'categories': [{'name': m['role'], 'characters': len(m['content'])} for m in after['input']]},
    'confirmed_duplicate': {'fields': ['opening_curated_facts', 'opening_selector_selected_facts'],
                           'equal': payload['opening_curated_facts'] == payload['opening_selector_selected_facts'],
                           'value_characters_each': len(compact(payload['opening_curated_facts']))}}
save('context_measurements.json', measurements)
save('before_request_sanitized.json', {'model': before['model'], 'max_output_tokens': before['max_output_tokens'],
    'input': [{'role': m['role'], 'content': m['content'] if m['role'] == 'system' else '[campaign payload redacted; see per-key character measurements]',
               'original_content_characters': len(m['content'])} for m in before['input']],
    'text_format': None, 'note': 'Deterministic current pre-repair reconstruction, not the missing original live request.'})

# Keep historical evidence bounded to structure/diagnostics, excluding campaign prose and hidden state.
captured = read(next((LIVE/'opening_response_evidence').glob('*.json')))
parsed = captured['parsed_response']
save('historical_response_structure.json', {'source': str(LIVE.relative_to(ROOT)),
    'root_keys': list(parsed), 'selected_entries_present': 'selected_entries' in parsed,
    'value_types': {k: type(v).__name__ for k,v in parsed.items()},
    'truncated': captured.get('truncated'), 'provider_attempt_id': captured['provider_attempt_id']})
for name in ['request_review.json', 'state_review.json', 'safe_configuration.json', 'opening_evidence_index.json']:
    shutil.copyfile(ROOT/'artifacts/pr_play_17'/name, OUT/('historical_'+name))
events = [json.loads(line) for line in (LIVE/'diagnostics/provider_usage.jsonl').read_text().splitlines()]
save('historical_diagnostics.json', [{k:v for k,v in e.items() if k in {
    'event','stage','attempt_id','purpose','classification','rejection_reason','provider_response_contract',
    'input_tokens','output_tokens','total_tokens','latency_ms','completion_status','opening_accepted','gameplay_committed',
    'provider_model','model','configured_model','request_count','provider_finish_reason'}} for e in events])

changed = ['game/gm.py', 'game/opening_presentation_renderer.py', 'tests/test_pr_play_13_opening_renderer.py']
diffs = []
for path in changed:
    old = (OUT/'source_before'/path).read_text(encoding='utf-8').splitlines(True)
    new = (ROOT/path).read_text(encoding='utf-8').splitlines(True)
    diffs.extend(difflib.unified_diff(old,new,fromfile='before/'+path,tofile='after/'+path))
for path in ['tests/test_pr_play_18_contract_alignment.py']:
    diffs.extend(difflib.unified_diff([], (ROOT/path).read_text().splitlines(True), fromfile='/dev/null',tofile='after/'+path))
report('source_changes.diff', ''.join(diffs))

def function_source(path, name):
    content = path.read_text(encoding='utf-8')
    node = next(n for n in ast.walk(ast.parse(content)) if isinstance(n, (ast.FunctionDef,ast.AsyncFunctionDef)) and n.name == name)
    return '\n'.join(content.splitlines()[node.lineno-1:node.end_lineno])

historical_source_agreement = {}
for path,name in [('game/gm.py','call_gpt'), ('game/opening_presentation_renderer.py','prepare_opening_renderer')]:
    historical_source_agreement[name] = function_source(ROOT/'artifacts/pr_play_17/source_snapshots'/path,name) == function_source(OUT/'source_before'/path,name)
save('historical_source_agreement.json', historical_source_agreement)

stages = [
('game/api.py','new_campaign','New Campaign request; isolated fixture storage','reset unstarted campaign','No provider call; engine authority'),
('game/api.py','start_campaign','Start Campaign request; readiness/admission','opening scope','ASHEN_OPENING_RENDERER evaluated later'),
('game/api.py','_start_campaign_after_admission','campaign, character, session, world, combat, scene','bootstrap resolution and provisional turn','synchronize addressability before opening_scope.track; provisional tick rolls back on rejection'),
('game/api.py','_opening_scene_normalized_action_and_resolution','internal_bootstrap=True; scene','scene-opening normalized action/resolution','scene_opening intent'),
('game/api.py','_run_resolved_turn_pipeline','authoritative game documents; normalized action','validated GM response and response contract','deterministic pipeline'),
('game/api.py','_build_gpt_narration_from_authoritative_state','narration bundle, scene and authority state','provider messages and validated candidate','response_type_contract scene_opening; bounded call_gpt'),
('game/gm.py','build_messages','narration context call kwargs and game state','legacy system + JSON user payload','shared construction remains unchanged'),
('game/prompt_context.py','build_narration_context','public scene, authority bundle, opening facts','narration payload including realization claims','opening public facts/curation supplied here'),
('game/gm.py','call_gpt','assembled messages; route; response type','rendered structured GM response or contract failure','only scene_opening reads renderer flag; enabled selects preparation before dispatch'),
('game/opening_presentation_renderer.py','prepare_opening_renderer','original messages','local catalog; public selection messages; strict text format','dedicated opening contract replaces legacy provider input'),
('game/opening_presentation_renderer.py','build_opening_public_catalog','original JSON payload','entries/by_id/required_ids or fail closed','public-only claims, curated coverage; authority stays local'),
('game/opening_presentation_renderer.py','opening_plan_text_format','public catalog','strict Responses API text.format','selected_entries required; per-ID variants; no additional properties'),
('game/provider_budget.py','dispatch','SDK method plus model/input/text/max_output_tokens','SDK response','admission and exactly-one dispatch; kwargs forwarded unchanged'),
('game/opening_presentation_renderer.py','realize_opening_provider_text','extracted SDK text; local catalog','render result or reason','JSON parser then renderer validator; no legacy fallback'),
('game/opening_presentation_renderer.py','validate_presentation_plan','plan + local catalog','approved choices or rejection','IDs, variants, unknown fields, required coverage, order, duplicates and bound'),
('game/opening_presentation_renderer.py','render_opening','validated choices','engine-authored text, declarations and trace','no model prose published'),
('game/opening_presentation_renderer.py','gm_response_from_render','successful render','structured response with immutable rendered metadata','engine declarations; null state proposals'),
('game/api.py','_complete_opening_turn_persistence_like_chat','validated result and tracked opening scope','200 publication/one commit or 422 rollback','acceptance-gated persistence'),
('game/opening_presentation_renderer.py','enforce_rendered_publication','GM response with render metadata','restored engine text; null update proposals','applied in API final publication path'),
]
traces=[]
for path,name,inputs,outputs,contract in stages:
    content=(ROOT/path).read_text(encoding='utf-8')
    node=next(n for n in ast.walk(ast.parse(content)) if isinstance(n,ast.FunctionDef) and n.name==name)
    traces.append({'source':path,'line':node.lineno,'function':name,'inputs':inputs,'outputs':outputs,'configuration_contract':contract})
save('request_path_trace.json',traces)

report('PR_PLAY_18_FAILURE_RECONSTRUCTION.md', '''# PR-PLAY-18 failure reconstruction

PR-PLAY-17 run 20261101T153625Z-02fc6545bc28 made one live request after New Campaign returned 200. Start Campaign invoked scene_opening through game.gm.call_gpt and the OpenAI Responses adapter (client.responses.create). GPT-4.1 mini returned a completed, parseable legacy envelope. Root fields are preserved in historical_response_structure.json: declared_claims, narration, player_facing_text, tags, improvisation_proposals, scene_update, activate_scene_id, new_scene_draft, world_updates, suggested_action, debug_notes. selected_entries is absent.

With ASHEN_OPENING_RENDERER=1, realize_opening_provider_text → render_opening → validate_presentation_plan rejected the top-level narration fields as arbitrary_narration_field. No rendering trace or opening publication resulted. Provider diagnostics additionally used missing_structured_envelope; downstream validation rejected structured_contract_failure. These broader labels do not override the precise renderer rejection.

The application returned 422; this is not a captured provider HTTP status. Usage was 26,986 input / 2,050 output / 29,036 total, latency 14,189.359 ms. Zero player turns completed. The original state review shows normalized gameplay documents unchanged, turn/log deltas zero, campaign_started false, inventory/world/overlays unchanged. Session/combat persistence bookkeeping changed. Provisional opening mutation occurs before the provider response, but acceptance-gated rollback prevents its gameplay commit. Rejection is before publication and commit, not literally before all in-memory mutation.

Evidence inspected directly: original run diagnostics/provider_usage.jsonl, opening_response_evidence capture, baseline/documents.json and after/documents.json with a fresh normalized baseline/after comparison (historical_state_verification.json), reports/result.json, plus artifacts/pr_play_17 request_review, state_review, safe_configuration, opening_evidence_index and source snapshots. Packaged historical evidence contains technical structure and state conclusions, excluding hidden campaign content.

Limitation: the exact original outgoing provider messages, public catalog and wire request were not captured. A source snapshot is not a request capture. Historical source functions call_gpt and prepare_opening_renderer are compared with the pre-repair current functions in historical_source_agreement.json. Deterministic current reconstruction confirms conflicting instructions and absence of a schema, but cannot reproduce the exact historical token breakdown or establish which instruction the live model followed. Model noncompliance is not independently established.
''')

table='\n'.join(f"| `{r['source']}:{r['line']}` / `{r['function']}` | {r['inputs']} | {r['outputs']} | {r['configuration_contract']} |" for r in traces)
report('PR_PLAY_18_REQUEST_PATH.md', '''# PR-PLAY-18 request path

The following stages trace actual code. Nested calls are described by inputs/outputs, not implied to be a single flat stack. build_messages calls build_narration_context; prepare_opening_renderer calls catalog construction and schema construction; renderer calls parsing/validation before response conversion. The next caller/consumer follows the output named in each row. request_path_trace.json preserves machine-readable locations.

| Source / function | Inputs | Outputs / downstream consumer | Configuration and contract |
| --- | --- | --- | --- |
'''+table+'''

Critical answer: **B — during provider request construction in call_gpt**, after shared legacy message construction and before SDK dispatch. Before repair, prepare_opening_renderer merely inserted a second system message while retaining the full legacy system and user payload. Selection was not deferred entirely to response time, but the outgoing requirements remained contradictory. After repair the same branch replaces provider-facing messages and attaches its text.format schema; the local authority catalog remains available to the response renderer.

OpenAI client construction uses existing API-key, timeout and SDK-retry settings. Model routing, pinning, admission/budgets and the opening output cap are unchanged. ProviderBudget.dispatch forwards keyword arguments to responses.create. The ordinary parser branch (_safe_json) is used only when opening_catalog is absent. The enabled branch extracts text with _extract_provider_response_text, then uses realize_opening_provider_text. Unsupported/incomplete responses still take existing failure handling. Publication enforcement is still applied in the API path; no new ordinary-turn renderer routing exists.
''')

report('PR_PLAY_18_CONTRACT_AUDIT.md', '''# PR-PLAY-18 contract audit

Pre-repair capture: before_request_sanitized.json and context_measurements.json are assembled through actual New Campaign → Start Campaign code with deterministic fixtures and mocked SDK transport. The full local payload was inspected for this audit but is excluded from review packaging because technical analysis needs sizes and contracts, not campaign secrets. No developer-role messages, tools, functions or structured-output definitions were present. Roles were system/system/user.

The first system message explicitly said: “Return valid JSON only with this one-call realization envelope”, followed by declared_claims, narration and player_facing_text. The second system message required selected_entries only. The JSON user payload also supplied legacy narration instructions, response_policy, narrative_plan and authority/declaration scaffolding. No text.format, response_format or schema was sent. This is contradictory instruction construction and missing schema enforcement, not substitution of a correct schema inside the adapter. There was no pre-existing provider JSON Schema for PR-PLAY-13; its contract was expressed in prompt text and the strict Python renderer validator.

| Contract element | Renderer expects | Before repair provider requirement | Result / repaired requirement |
| --- | --- | --- | --- |
| Response type | Presentation plan | Legacy system envelope plus plan system instruction | Mismatch → dedicated plan instruction |
| Selection field | selected_entries only | selected_entries versus declared_claims/narration/player_facing_text | Mismatch → selected_entries required in strict schema |
| Catalog identifiers | Local authorized public IDs | Plan instruction enumerates IDs; legacy source claims also present | Ambiguous → per-entry catalog_id enum |
| Presentation variants | Own entry's approved variant_id | Plan index enumerates variant_ids; no schema | Prompt-only → paired per-ID variant enums |
| Arbitrary narration | Prohibited | First system explicitly requires narration | Mismatch → excluded by prompt/schema and validator |
| Consequential outcomes | Engine-authorized only | Legacy narration/proposal lanes coexist | Conflicting lanes → only public selections; engine retains authority |

Repaired schema: opening_plan_text_format supplies Responses API text.format with type=json_schema, name=opening_presentation, strict=true. Root required=[selected_entries], additionalProperties=false; selected_entries is an array with minItems=1/maxItems=24. Each anyOf branch requires only catalog_id and variant_id, additionalProperties=false, with catalog_id constrained to one local public ID and variant_id to that entry's approved variants. Required coverage, duplicates, ordering and disclosure remain renderer checks. These semantic constraints deliberately remain engine-owned; schema validity alone never authorizes publication.

Repaired outgoing roles are system/user. The system contains the selection instruction plus required/order/variant index. The user contains only scene_opening response-type metadata and opening_public_choices (public IDs and approved text variants). No legacy narration payload is forwarded. Host-authored authority data is not exposed as provider-editable output. Parser, schema and renderer use the same catalog created once for this request. The SDK transport capture and separate real-SDK/in-memory-HTTP test establish schema preservation through serialization.

Root cause: incomplete integration of the opt-in renderer at the provider request boundary. High confidence for current/source-snapshotted integration defect; limited confidence about the exact historical wire contents because that capture is missing. The evidence supports an application contract defect, not a claim that the model ignored a coherent enforced contract.
''')

report('PR_PLAY_18_REPAIR_REPORT.md', '''# PR-PLAY-18 repair report

Changed production files:

- game/opening_presentation_renderer.py: prepare_opening_renderer now projects a dedicated public selection request instead of adding instructions to the legacy narration request. Added opening_plan_text_format to encode the existing plan field contract and per-entry allowed ID/variant pairs.
- game/gm.py: only when opening_catalog exists, pass prepared text_format as Responses API text.format.

Tests: added tests/test_pr_play_18_contract_alignment.py; updated the PR-PLAY-13 replay assertion because authority claims are now retained locally rather than sent in the user message. Existing unit replay/variant/authority tests still cover deterministic rendering; the new integration test compares published text to the exact selected public variants.

This is a necessary replacement of contradictory provider contract inputs, not a general prompt optimization. Public facts still come from the unchanged engine catalog. Validator, renderer, accepted publication authority and rollback logic are unchanged. No legacy prose conversion, fallback, unknown-ID allowance or error suppression was added.

Disabled openings retain their existing system prompt, authored-fact instruction, full payload, request kwargs, parser and validation. Ordinary turns retain their messages and parser and never attach the new schema; both branches are tested at the transport boundary. Model, limits, budgets and retries are unchanged. No commit/push was performed. Pre-existing unrelated working-tree changes are preserved; source_changes.diff is relative to snapshots taken at this pass's start, not Git HEAD.

Limitations: no live provider was used, so provider-side schema support and actual model selection behavior await an explicitly authorized experiment. The real SDK serializer was exercised with in-memory HTTP, but a mocked HTTP response cannot prove remote schema acceptance. A first unhydrated campaign synchronizes authored scene addressability before the rollback snapshot; negative tests compare against that exact authorized synchronization plus the established bookkeeping normalization. No attempt was made to redesign this pre-existing boundary.
''')

suite=ET.parse(OUT/'focused_tests.xml').getroot().find('testsuite')
contract=ET.parse(OUT/'contract_tests.xml').getroot().find('testsuite')
unique_tests = len({(n.get('classname'), n.get('name')) for xml in ['focused_tests.xml', 'contract_tests.xml'] for n in ET.parse(OUT/xml).getroot().iter('testcase')})
save('test_summary.json', {'focused_relevant_suite':dict(suite.attrib),'final_contract_suite':dict(contract.attrib),
    'unique_tests':unique_tests, 'note':'Final contract suite adds SDK serialization and hidden-context/variant-pair tests to the earlier relevant suite.',
    'live_provider_requests':0})
report('PR_PLAY_18_TEST_RESULTS.md', f'''# PR-PLAY-18 test results

Relevant suite: **{suite.attrib['tests']} passed**, failures={suite.attrib['failures']}, errors={suite.attrib['errors']}. Final contract suite: **{contract.attrib['tests']} passed**, failures={contract.attrib['failures']}, errors={contract.attrib['errors']}. The latter includes SDK serialization and hidden-context/variant-pair tests; **{unique_tests} unique tests** passed overall. JUnit XML captures are included.

Relevant suite command:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_pr_play_18_contract_alignment.py tests/test_pr_play_13_opening_renderer.py tests/test_pr_play_04_opening_integrity.py tests/test_pr_play_06_opening_budget.py tests/test_pr_play_11_claim_authority.py tests/test_opening_start_seam_regressions.py -q --basetemp=development/tmp/pr18_final --junitxml=artifacts/pr_play_18/focused_tests.xml
```

Final contract suite adds real OpenAI SDK serialization using httpx.MockTransport, a dummy credential and offline.invalid. All HTTP handling is in memory. It passes through actual application initialization, provider admission/dispatch, SDK serialization/deserialization, parser, renderer and publication. The other contract tests replace responses.create at the SDK boundary and inspect the actual kwargs.

| Required coverage | Result |
| --- | --- |
| A enabled instructions/schema | PASS: actual assembled request captured at transport |
| B disabled legacy | PASS: existing SYSTEM_PROMPT/authored-fact instructions and kwargs; accepted legacy opening |
| C ordinary-turn isolation | PASS: input messages unchanged, no text.format |
| D valid plan | PASS: actual New Campaign/Start Campaign path, authorized text published, one turn committed |
| E legacy narration | PASS: 422 arbitrary_narration_field, no publication |
| F unknown ID | PASS: 422 unknown_catalog_id |
| G unauthorized variant | PASS: 422 unknown_variant_id; approved alternate still passes existing renderer tests |
| H atomicity | PASS: gameplay documents equal authoritative pre-provider baseline; zero turn/log progression on rejection |
| I adapter preservation | PASS: strict schema reaches mocked SDK and real SDK in-memory HTTP body |
| J consistency | PASS: catalog index/variants, schema constraints, selected plan and published text agree |

Final eight contract tests perform seven mocked transport dispatches (one each), zero live provider requests. Valid opening and real SDK serialization both publish successfully; each negative attempt dispatches once and rejects before publication/commit. See offline_success.json, negative_*.json, assembled_request.json and sdk_serialized_request.json. The full relevant suite includes concurrency/repeat-start and historical acceptance/rejection regressions.

During test development, an optional jsonschema import was unavailable and removed; schema structure is checked directly and JSON is serialized by the installed SDK. The first stronger atomicity assertion uncovered documented bookkeeping plus authoritative scene-addressability hydration before opening_scope.track; final tests explicitly account for these existing operations and compare all remaining game documents. One overlapping pytest invocation hit a shared basetemp collision; final runs used dedicated paths. No production repair was made for these test setup issues. No remaining test failures. One pre-existing Starlette/httpx deprecation warning appeared in the relevant suite.
''')

distribution='\n'.join(f"| {r['category']} | {r['characters']:,} | {r['estimated_tokens']:,.1f} | {r['percent']}% |" for r in rows[:16])
report('PR_PLAY_18_CONTEXT_ANALYSIS.md', f'''# PR-PLAY-18 opening context analysis

Observed PR-PLAY-17 usage: **26,986 input / 2,050 output / 29,036 total tokens**. Exact historical request content was not captured, so no exact historical category breakdown can be established.

Deterministic current reconstruction before repair: **{old_chars:,} message-content characters**, approximately **{old_chars/4:,.0f} tokens**. Repaired request: **{new_chars:,} message-content characters + {schema_chars:,} schema-format characters = {new_chars+schema_chars:,}**, approximately **{(new_chars+schema_chars)/4:,.0f} tokens**. These are character/4 estimates, not tokenizer counts. tiktoken is unavailable locally. Provider framing, tokenization and output usage are not inferred. Fixtures differ from the historical live campaign; similar magnitude is not identity.

Pre-repair disjoint categories (percent of actual content characters; full distribution in context_measurements.json):

| Category | Characters | Estimated tokens | Share |
| --- | ---: | ---: | ---: |
{distribution}

The pre-repair first system is {len(before['input'][0]['content']):,} characters, selection system {len(before['input'][1]['content']):,}, and JSON user payload {len(before['input'][-1]['content']):,}. No developer messages, tool definitions or structured-output schema were present. Conversation/history fields are accounted for only where actually present in the measured keys. Campaign and character are roughly one thousand characters each; they are not the principal contributors. The dominant costs are response_policy, instructions, gm_resolution_decision, scene, turn_packet, answer recipe and narrative_plan.

Requiredness: the full narration policies, answer recipe, dialogue/social plans, character mechanics and legacy declaration protocol are not needed by a provider restricted to selecting public IDs/variants; their authority computations remain required locally. For the provider contract, the public catalog, allowed variants, required coverage/order and selection schema are needed. The dedicated request replaces conflicting narration context as part of alignment; no shared payload optimization was implemented.

Confirmed redundancy: opening_curated_facts equals opening_selector_selected_facts ({len(compact(payload['opening_curated_facts'])):,} value characters each). Public IDs and variant names appear in both the plan index and strict schema after repair; this overlap has distinct instruction/enforcement purposes. Multiple old fields refer to the same claims/facts and narration policy, but no exact duplication size is claimed beyond equality checks. The first legacy system conflicts with the inserted selection instruction; prompt size alone was not the basis for removal.

Up to three future opportunities (diagnostic only; none implemented beyond the required dedicated opening-contract replacement):

1. **Shared payload narration-policy projection**: response_policy (~21.6k chars) and instructions (~14.5k chars). Audit exact overlaps before removing anything from legacy consumers. Risk: priority/authority guidance loss. Validate disabled openings and ordinary/social-turn acceptance matrices; this is outside PR-PLAY-18.
2. **Duplicate curated fact list**: opening_curated_facts / opening_selector_selected_facts, one copy ~{len(compact(payload['opening_curated_facts'])):,} chars (~{len(compact(payload['opening_curated_facts']))/4:,.0f} estimated tokens). One list may suffice in a future shared projection. Risk: downstream source selection relies on these keys. Validate selectors, fallback and curated-fact attachment before removal.
3. **Shared decision/scene projection**: gm_resolution_decision (~10.7k), scene (~10.3k), turn_packet (~8.7k). They overlap conceptually in authority/fact references; no byte-for-byte duplication is asserted. Keep host authority complete and measure candidate public projections. Risk: removing evidence required by legacy narration or validation. Compare accepted/rejected replay cases before any change.

The repaired opening already forwards only public choices. These opportunities concern shared legacy/context construction and must not be treated as authorization for further optimization here.
''')

report('PR_PLAY_18_FINAL_VERDICT.md', '''# PR-PLAY-18 final verdict

**A — CONTRACT ALIGNED / PASS.** The actual assembled repaired provider request, strict schema, SDK serialization, parser and renderer agree; offline initialization publishes an authorized opening. This verdict is offline readiness, not a claim of live model success.

1. **Was the provider instructed to return a plan?** Pre-repair: yes, alongside contradictory legacy instructions. Repaired: yes, exclusively a presentation-selection plan. Exact original historical wire request is unavailable.
2. **Correct structured-output schema?** Pre-repair: none enforced. Repaired: strict opening_presentation text.format requires selected_entries.
3. **Adapter preserves schema?** Yes after repair, proved at mocked SDK boundary and real SDK/in-memory HTTP serialization. No old schema substitution point existed; schema attachment was missing.
4. **Legacy narration instructions present?** Yes before repair in both base system and full narration payload. None in repaired provider input.
5. **Cause of mismatch?** Incomplete request-boundary integration retained conflicting legacy contract and omitted schema enforcement. Historical source agreement supports this defect; missing original wire capture prevents stronger historical claims.
6. **Repair implemented?** Yes: dedicated public plan request and strict paired ID/variant schema, attached only in enabled opening branch.
7. **Request matches renderer?** Yes. Schema controls shape/ID/variant choices; renderer additionally enforces public authority, coverage, order and uniqueness.
8. **Legacy opening unchanged?** Yes; disabled branch code preserved and regressions pass.
9. **Ordinary turns unaffected?** Yes; unchanged request input/parser and no new schema attachment; regression evidence included.
10. **Mocked initialization succeeds?** Yes, through actual New Campaign and Start Campaign paths, plus real SDK serialization with in-memory HTTP.
11. **Incompatible responses rejected?** Yes: legacy narration, unknown catalog ID, unsupported variant; 422, no publication/commit.
12. **State authority preserved?** Yes. Authored scene addressability synchronization before the provider snapshot and documented bookkeeping are accounted for; rejected provider content cannot change gameplay documents. Engine-only rendering and accepted commit remain intact.
13. **Any provider requests made?** Zero live provider requests. Final eight contract tests made seven synthetic transport dispatches. Historical PR-PLAY-17 had one live dispatch, which was only inspected.
14. **Largest context contributors?** Legacy response_policy/instructions, authority decision/scene, turn packet and answer/narrative plans. Exact observed historical distribution remains unknown; deterministic measurements included.
15. **Ready for controlled live validation?** Yes after external review and separate explicit authorization. Provider-side schema acceptance and model behavior remain untested live.

Recommended next step: externally review this archive, then authorize one bounded opening-only live validation that preserves the sanitized final request/schema and provider response. No PR-PLAY-19 work is started. Stop for external review.
''')

# Exclude raw local reconstruction and broad historical data; include narrow diffs and source.
for path in changed+['tests/test_pr_play_18_contract_alignment.py']:
    dst=OUT/'source_after'/path
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/path,dst)
included = [p for p in OUT.rglob('*') if p.is_file() and p.name not in {
    'before_request_local.json','archive_verification.json','archive_path.txt','manifest.json'} and '__pycache__' not in p.parts]
save('manifest.json',[{'path':str(p.relative_to(OUT)).replace('\\','/'),'bytes':p.stat().st_size,
                       'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(included)])
included.append(OUT/'manifest.json')
stamp=subprocess.check_output(['powershell', '-NoProfile', '-Command',
    "[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMdd-HHmmss')"], text=True).strip()
archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in included:
        z.write(p, 'pr_play_18/'+str(p.relative_to(OUT)).replace('\\','/'))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == len(included)
    for name in ['FAILURE_RECONSTRUCTION','REQUEST_PATH','CONTRACT_AUDIT','REPAIR_REPORT','TEST_RESULTS','CONTEXT_ANALYSIS','FINAL_VERDICT']:
        assert f'pr_play_18/PR_PLAY_18_{name}.md' in z.namelist()
save('archive_verification.json',{'path':str(archive),'exists':archive.exists(),'bytes':archive.stat().st_size,
    'members':len(included),'crc_test':'PASS','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
    'excluded':'Raw full campaign request, historical narration/state, secrets, unrelated artifacts'})
(OUT/'archive_path.txt').write_text(str(archive),encoding='utf-8')
print(json.dumps({'archive':str(archive),'unique_tests':unique_tests,'old_chars':old_chars,
                  'new_context_chars':new_chars+schema_chars,'new_estimated_tokens':(new_chars+schema_chars)/4,
                  'historical_source_agreement':historical_source_agreement}))

