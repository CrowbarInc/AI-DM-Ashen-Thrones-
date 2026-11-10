"""Generate candid campaign reports from retained measurements, never invented results."""
import difflib,hashlib,json,statistics,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/campaigns/product_realization/pr_play_65';REPORT.mkdir(parents=True,exist_ok=True)
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
baseline=read('baseline.json');live=read('live_summary.json');hold=read('holdout_results.json')
reg=read('regression_summary_final.json');fault=read('failure_injection.json');actions=read('gameplay_actions.json')
freeze=read('implementation_freeze.json');state=read('state_integrity.json');protected=read('protected_integrity.json')
source_ok=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in freeze.items())
save('source_freeze_verification.json',dict(unchanged=source_ok,hashes=freeze,holdout_executions=1))
traces=[r['full_trace'] for r in actions if r['full_trace'] and r['full_trace'].get('live_provider')]
usage=dict(provider='openai',model=traces[0]['live_provider']['model'],requests=live['live_provider_requests'],
    input_tokens=sum(t['live_provider'].get('input_tokens') or 0 for t in traces),
    output_tokens=sum(t['live_provider'].get('output_tokens') or 0 for t in traces),
    total_tokens=sum(t['live_provider'].get('total_tokens') or 0 for t in traces),retries=0)
latencies=live['http_latency_ms']
metrics=dict(verdict='C — FAIL / CRITICAL DEFECT',baseline=baseline['commit'],development_tests=40,
    holdout_cases=40,holdout_matches=hold['matched'],critical_false_acceptances=len(hold['critical_false_acceptances']),
    false_rejections=hold['false_rejections'],offline_mandatory_omissions=hold['mandatory_omissions'],
    http_mandatory_omissions=1,**live,provider_usage=usage,
    average_response_ms=statistics.mean(latencies),maximum_response_ms=max(latencies),
    state_integrity=all(r['authority_equal'] and r['resolution_equal'] for r in state['per_action']),
    protected_integrity=protected['passed'],experimental_isolation=True,
    meaningful_transition=True,transition_presentation_complete=False,
    failure_injections=dict(cases=fault['cases'],passed=fault['passed'],scope='offline after critical stop'),
    focused_regression=reg['focused'],broader_regression=reg['broader_hard_validation'],
    next_step='Repair the existing publication seam so every current-action mandatory disclosure survives legacy rejection/failure, with publication-failure and interruption controls before any new live run.')
save('metrics.json',metrics)
latency=dict(http_ms=latencies,mean_ms=metrics['average_response_ms'],max_ms=max(latencies),
    deterministic_resolution_ms=[r['deterministic_resolution_ms'] for r in actions],
    trusted_render_ms=[t.get('trusted_disclosure_ms') for t in traces],
    provider_ms=[t['live_provider'].get('provider_latency_ms') for t in traces],
    validation_ms=[t.get('validation_ms') for t in traces],
    composition_ms_live='No accepted optional AI segment; no live composition sample',
    composition_ms_offline=[r['result']['validation'].get('composition_ms') for r in fault['rows'] if r.get('result') and r['result'].get('validation',{}).get('composition_ms') is not None],
    provider_free_hook_ms=[r['result'].get('total_integrated_ms') for r in fault['rows'] if r.get('result')],
    comparison='PR64 sample/categories/host conditions differ. No speed improvement claim. No additional provider request per action.')
save('latency.json',latency)
save('trusted_disclosure_fixtures.json',[dict(action=r['input'],trusted=(r['full_trace'] or {}).get('trusted_disclosure'),facts=(r['full_trace'] or {}).get('trusted_facts')) for r in actions])
save('ai_presentation_fixtures.json',[dict(action=r['input'],raw=t.get('raw_provider_text'),validation=t.get('validation'),assembled=t.get('assembled'),published=r['facing']) for r in actions if (t:=r['full_trace'])])
save('gameplay_transition.json',dict(destination='old_milestone',new_mechanic=False,action=actions[3],followup=actions[4],
    authoritative_success=actions[3]['authority']['scene']=='old_milestone' and actions[4]['mechanical']['kind']=='discover_clue',
    presentation_success=False,limitation='Existing authored exit works; arbitrary northwest-route wording was not newly enabled or guaranteed.'))
comparison={
 'A':dict(complexity='Lowest immediate change; recurring grammar repairs',reliability='Heuristic free-form coverage',consequences='Existing gates',hidden='Existing gates, known gaps',naturalness='High potential',duplication='Low',latency='One provider call',compatibility='Existing',reversibility='High',regression='Growing validator surface'),
 'B':dict(complexity='Small hook plus publication provenance',reliability='Engine segment deterministic; publication seam must guarantee delivery',consequences='All gates plus finite optional surface',hidden='No hidden projection; finite optional surface',naturalness='Limited but coherent introductions',duplication='Prompt responsibility plus whole-segment omission',latency='One provider call',compatibility='Reuses hook and publication helper',reversibility='Default-off flag',regression='Two production files'),
 'C':dict(complexity='New provider schema and segment orchestration',reliability='Strong if segment schema and publisher cooperate',consequences='Still needs segment and final gates',hidden='Still needs segment and final gates',naturalness='Potentially greater control',duplication='Explicit slots',latency='One call possible',compatibility='Additional response/schema surface',reversibility='Medium',regression='Larger than B')}
save('architectural_comparison.json',comparison)
diff=''
for n in freeze:
    p=ROOT/n;old=(OUT/'entry_source'/p.name).read_text(encoding='utf-8').splitlines(True)
    diff+=''.join(difflib.unified_diff(old,p.read_text(encoding='utf-8').splitlines(True),fromfile='entry/'+n,tofile=n))
(OUT/'implementation.diff').write_text(diff,encoding='utf-8')
(OUT/'final_worktree_status.txt').write_text(subprocess.check_output(['git','status','--short'],text=True),encoding='utf-8')
summary=f'''**{metrics['verdict']}**. The bounded hook experiment delivers mandatory facts offline, but a real HTTP milestone investigation committed a discovery while publishing “I cannot provide a validated response to that request.” The existing publication seam only replaces one provider-disabled stub. This is an implementation defect and a critical mandatory-disclosure omission. Experimental HTTP/provider execution stopped. Defaults remain off; no commit or push.

Forty development tests pass. Frozen holdout executed once: {hold['matched']}/40 expected publications, eight conservative false rejections, zero critical false acceptances, zero offline mandatory omissions, zero state mutations. These are hook-level results, not proof of the HTTP publication guarantee. Five consecutive supported HTTP actions ran with four real provider requests ({usage['total_tokens']} tokens), zero validated AI presentations, zero AI publications, four hook fallbacks (two explicitly substituted in HTTP). The authored exit reaches old_milestone and a subsequent investigation changes clue state; its presentation fails.

Focused regression: {reg['focused']['passed']} passed, {reg['focused']['failed']} known failures; broader: {reg['broader_hard_validation']['failed']} known failures. Authority matches disabled controls in all five actions. Protected hashes unchanged: {protected['passed']}. Exactly one next step: {metrics['next_step']}'''
def report(name,text):
    (REPORT/name).write_text('# '+name[3:-3].replace('_',' ')+'\n\n'+text.strip()+'\n',encoding='utf-8')
report('01_EXECUTIVE_SUMMARY.md',summary)
report('02_BASELINE_AND_SCOPE.md',f'''Commit: `{baseline['commit']}`. Substantial existing dirty/untracked work was retained. Full entry status and protected hashes: artifacts/pr_play_65/baseline.json. Source entry copies and scoped diff distinguish this cycle from prior uncommitted PR work.

Read Development Constitution, NEXT_SESSION orientation, state authority, validation-layer separation, ATGB evidence standard, Product Realization validation and review-export standard. User PR65 authorization supersedes stale historical stop recommendations; protected fixtures remain untouched. No applicable AGENTS.md found.

Relevant owners: integrated_investigation_narration.outcome_contract/run_integrated_hook; anchored authorization; consequential_narration_validation; mandatory_outcome_coverage; quarantine hook/publication; api._publish_experimental_integrated_narration; intent_parser and exploration; storage session/scene overlays. Frontend consumes gm_output.player_facing_text; no schema or frontend change. Existing API saves deterministic state before publication. Existing authored exit and nodes reused. No new movement mechanic.

Known baseline failures: three focused; nine hard_validation_attempt_1 broader. Details remain in baseline JSON. Existing dirty canonical data was hashed as found, not reset to HEAD.''')
table='| Dimension | A: free-form | B: engine plus AI | C: segments |\n|---|---|---|---|\n'
for k in comparison['A']:table+=f"| {k} | {comparison['A'][k]} | {comparison['B'][k]} | {comparison['C'][k]} |\n"
report('03_ARCHITECTURAL_OPTIONS.md',table+'\nSelected B before implementation: reuse the integrated owner; avoid another narrator, provider or response schema. Selection was based on bounded ownership and reversibility, not acceptance statistics. The live failure exposes an overlooked publisher precondition.')
report('04_SELECTED_RENDERING_APPROACH.md','''Default-off ASHEN_EXPERIMENTAL_AUTHORITATIVE_DISCLOSURE adds composition inside the existing integrated hook. Existing quarantine, integrated mode, publication opt-in and matching session binding remain required for HTTP publication. The flag is not set persistently. The affected experiment is stopped after its critical HTTP failure.

Engine renders current must_communicate text verbatim. Optional AI intro is separately validated; the final assembled string passes the unchanged integrated validator and mandatory coverage. At most one provider call per eligible action. Two production files changed; no second narration pipeline.

Offline initial negatives showed that general validators missed hidden/literal discovery assertions. Before freeze, an additional conservative finite presentation boundary was added. This is an experimental restriction, not a global grammar repair. Retained failure and correction: initial_offline_diagnosis.json.''')
report('05_DISCLOSURE_PROVENANCE.md','''Current resolver-selected disclosures remain mandatory even when already present in post-resolution state. Previously known facts are authorization/context, not mandatory redisclosure. Public observations are optional. Hidden content is excluded by the existing detached projection. Engine status and inventory consequences retain their existing outcome-contract roles. No parallel database or state ownership was introduced.

Trusted segment is derived solely from outcome_contract.must_communicate. Candidate provider arguments are JSON-detached; mutation cannot rewrite engine request or segment. Publication checks recomputed engine text, validated composition equality and provenance marker.

Existing discovery state records resolution, not acknowledged player delivery. player_facing_published records copying to a response, not transport success or receipt. There is no new ACK/retry mechanism. Interrupted/failed delivery therefore retains existing state semantics. The milestone case proves those semantics do not guarantee communication; no contrary success claim is made.''')
report('06_AI_PRESENTATION_BOUNDARY.md','''Existing legacy mechanics, consequential safety and final validation remain required. Coverage is evaluated on the trusted segment and final response; only the AI segment's coverage obligation is empty. Authority remains unchanged. Optional prose must also fit a finite action introduction or an exact authorized observation/prior proposition. Unknown clauses fall back. This closes the offline missed-hidden/literal-claim cases without broad semantic expansion.

The finite boundary reduces stylistic freedom and rejects some harmless introductions. It is not proof of universal English safety. AI cannot establish new routes, items, NPC outcomes, travel, world changes or discoveries. Duplicated mandatory facts cause entire optional-segment omission, never trusted-text removal. Exact-authorized historical context is validated but not mandatory.''')
report('07_VALIDATION_AND_COMPOSITION.md','''Trusted coverage PASS is necessary. Untrusted text passes existing safety with unchanged authoritative contract. Duplicate overlap is conservative REVIEW_REQUIRED. Unknown presentation clauses are REVIEW_REQUIRED. Valid optional text is joined with engine disclosure using one space; final whole-response validation checks safety and mandatory coverage. No second provider repair call.

Publication accepts composed text only under existing session gating, matching raw-plus-trusted text, validated-composition marker and provenance. Legacy behavior remains byte-for-byte selected when the new flag is absent. But fallback substitution in the pre-existing API helper is limited to a specific incoming stub. This incomplete publication integration defeats the final delivery guarantee; see critical_incident.json. Source frozen before holdout and not tuned afterward.''')
replay=read('exact_pr_play_64_replay.json')
report('08_PR_PLAY_64_REPLAY.md',f'''Exact candidate preserved: “{replay['candidate']}”

Legacy: FAIL. Experimental: FAIL on the same untrusted route assertion. Engine fallback retains mandatory route. The candidate was not relabeled safe. No need to make arbitrary AI discovery syntax carry coverage: a simple action introduction passes offline while engine text carries the fact. Extracted claims, full audits, trusted segment, assembled text and immutable hook snapshots: exact_pr_play_64_replay.json. This replay is offline, not another live call.''')
report('09_DEVELOPMENT_TESTS.md','''40 focused development tests pass, including engine provenance, multiple facts, mixed current/history, hidden and unauthorized claims, contradictions, direction/certainty changes, duplicates, provider faults, non-PASS validator gates, detached mutation, isolation and publication binding. Full case names/assertions: tests/test_pr_play_65_authoritative_disclosure.py; results in focused_final.xml. Initial development was 37/39 with two missed-safety cases; the bounded correction preceded source freeze. The later passing unit suite did not detect the legacy-publication suppression caught by HTTP.

Gameplay-transition and continuity authority are demonstrated through saved HTTP traces/control comparisons rather than fabricated unit mechanics. Network interruption acknowledgement is unsupported, explicitly reported. The requested 40-item development matrix is covered by these controls and traces with that limitation; passing unit count is not equivalent to forty independent gameplay capabilities.''')
report('10_FROZEN_HOLDOUT.md',f'''Frozen before implementation: 40 inputs and expectations; SHA-256 `{read('frozen_holdout_manifest.json')['sha256']}`. Distribution: 10 delivery, 10 unauthorized, 5 contradiction, 5 historical, 5 provider, 5 continuity. Actual transition cases were explicitly deferred before freezing, replaced by continuity, because support was not yet proven.

One execution after source freeze: 32/40 complete expectation matches; eight false rejections ({', '.join(hold['false_rejections'])}). Zero unsafe acceptances, mandatory omissions or state changes offline. All assembled hook responses remain safe and covered. No tuning/rerun. This developer-authored holdout is not independent blind evaluation and does not include the complete HTTP publisher; HTTP results are separately red and override any offline success claim.''')
lines='\n'.join(f"- {r['input']}: raw `{t['raw_provider_text']}`; {t['validation'].get('decision')}; published `{r['facing']}`." for r in actions if (t:=r['full_trace']) and t.get('validation'))
report('11_LIVE_PROVIDER_RESULTS.md',f'''Existing OpenAI adapter, model `{usage['model']}`. Four real requests, {usage['input_tokens']} input + {usage['output_tokens']} output = {usage['total_tokens']} tokens. Zero retries. Budget 6 requests / 12,000 tokens respected. All four candidates duplicated engine-owned outcomes; no accepted/published AI presentation. No favorable-result retries after failure. Provider responses, latency and usage are preserved in gameplay_actions.json, quarantine_evidence and provider ledger.

{lines}

No broad comparison with PR64: categories differ, and publication failed. Preflight skipped explicitly by the established isolated harness; actual adapter sent/usage records substantiate only these four live calls.''')
report('12_HTTP_GAMEPLAY.md','''Five consecutive supported HTTP application actions: examine board; examine barrel; repeat board; follow missing-patrol rumor; examine weathered milestone. FastAPI TestClient called the real /api/chat?ui_mode=player route; no browser or external TCP claim. Request text, deterministic mechanics, before/after session/character/authority, response and full hook are saved per action.

First route discovery reached the player through existing deterministic text. Four optional candidates fell back at hook level. Two HTTP responses have explicit fallback markers; first and milestone responses used other legacy pathways. The final milestone response omitted its mandatory clue despite hook fallback containing it. Therefore complete-pipeline delivery FAILS. Five disabled control actions and three provider-free transition-probe actions are additional separate HTTP evidence, not counted as live-sequence actions. Isolation helper performs an additional control request.''')
report('13_GAMEPLAY_TRANSITION.md','''Authoritative transition SUCCESS using existing content: frontier_gate exit “Follow the missing patrol rumor” resolves to existing old_milestone; active scene and visited nodes persist. Following investigation reveals existing milestone_mud_prints. This is an actual stateful transition, not narration-only movement. No destination/encounter/content invented; no new mechanic or general movement change.

Presentation of the resulting discovery FAILS. Explicit authored-exit wording is demonstrated; arbitrary northwest-route phrasing is not newly supported. The meaningful-transition authority result is separate from the failed overall experiment. See gameplay_transition.json and action traces.''')
report('14_FAILURE_INJECTION.md',f'''{fault['passed']}/{fault['cases']} offline failure controls pass. Provider unavailable/timeout, empty/malformed, unauthorized discoveries/persistent/inventory/hidden, route contradiction, duplicate and missing AI coverage preserve trusted hook fallback and no state mutation. Unsupported invented destination has no authored target; disabled flag uses legacy hook.

Detached publication-failure reproduction FAILS: legacy rejection suppresses fallback. No experimental HTTP/provider executions after the critical stop. Actual network disconnect/client receipt is unverified; there is no durable ACK. These results must not be described as fourteen successful end-to-end HTTP injections. Non-PASS validator statuses are also covered by development tests.''')
report('15_STATE_AND_CONTINUITY.md',f'''All five enabled actions have identical bounded authoritative state and mechanical outcomes to disabled controls (campaign UUID excluded). Scene transition and subsequent clue persist across storage reloads. Narration does not write state. Protected input hashes: {protected['checked']} files, changed {len(protected['changed'])}. Session binding prevents cross-session publication; fresh projection tests prevent cross-campaign authority accumulation. No disclosure database added.

Communication is not inferred from committed clue state. The final HTTP failure explicitly demonstrates that distinction. Client acknowledgement and redelivery remain absent. Evidence: state_integrity.json, protected_integrity.json, isolation.json, action snapshots.''')
report('16_LATENCY_AND_QUALITY.md',f'''Mean live-sequence HTTP response {statistics.mean(latencies):.3f} ms; maximum {max(latencies):.3f} ms. Per-action deterministic seam timing, trusted rendering, provider, validation and total HTTP timings: latency.json. No accepted live optional composition sample exists; offline positive composition is timed separately. Provider-free fallback hook timing excludes HTTP overhead. No extra provider request introduced.

Provisional rubric: action relevance mixed; route clarity good initially, milestone disclosure absent; naturalness limited; continuity authoritative but presentation incomplete; repetition avoided by omission; mechanical accuracy preserved in state; agency demonstrated through authored exit; responsiveness variable; recovery fails at publication; state consistency passes. No human rating and no official ATGB corpus run. Passing safety validation is not good-gameplay evidence.''')
report('17_REGRESSION_RESULTS.md',f'''Focused PR55–64 plus new controls: {reg['focused']['passed']} passed; {reg['focused']['failed']} failures, {reg['focused']['errors']} errors. New failed node IDs: {reg['focused']['new_failures']}. Existing three failures retained. PR55 wrapper: {reg['holdout']['passed']} passed / {reg['holdout']['failed']} failed. Broader authority-assurance: {reg['broader_hard_validation']['passed']} passed / {reg['broader_hard_validation']['failed']} known failures. Full repository suite not run. Old generated fixture reports touched by these tests are restored by established runner snapshots.

Source freeze verified: {source_ok}. No significant new suite regression does not negate the new experimental HTTP delivery defect. XML, commands, logs, exact failure IDs and messages are retained.''')
report('18_LIMITATIONS_AND_OPEN_RISKS.md','''Critical known defect: trusted disclosure can be suppressed by legacy rejection outside the one stub fallback condition. Experiment stopped/default off. Four live AI outputs duplicated mandatory text; zero validated/published AI presentations. Holdout has eight conservative false rejections and lacks HTTP publisher/actual transition cases. Finite optional grammar reduces naturalness. No network ACK or guaranteed redelivery. No browser/TCP or human quality/official ATGB claim. No generalized semantic safety or unrestricted movement claim. Canonical fixtures unchanged; prior dirty work retained.

No source tuning followed holdout. Evidence archive may contain prior tracked-source deltas only where explicitly scoped entry copies show current changes. Review the critical incident before any enablement. No new provider run is authorized by this report.''')
report('19_NEXT_SESSION.md',f'''Verdict: C — FAIL / CRITICAL DEFECT. Keep ASHEN_EXPERIMENTAL_AUTHORITATIVE_DISCLOSURE off. No more provider calls in this cycle. Exactly one primary next step: {metrics['next_step']}

Read critical_incident.json and api._publish_experimental_integrated_narration alongside the hook and disclosure provenance. Add a fresh preimplementation publisher-inclusive holdout; do not rerun/tune this frozen holdout. Preserve default-off/session isolation and exact original narration. Do not launch PR-PLAY-66 or a broad grammar repair. No commit or push was made.''')
print(json.dumps({k:metrics[k] for k in ['verdict','average_response_ms','maximum_response_ms','provider_usage']}))
