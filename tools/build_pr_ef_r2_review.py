"""Build PR-EF-R2 evidence index and the established CURRENT_REVIEW package."""
from __future__ import annotations
import ast, difflib, hashlib, json, re, statistics, sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/pr_ef_r2'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def save(name, value):
    (OUT / name).write_text(value.strip()+'\n' if isinstance(value, str) else
                          json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def cases(name):
    rows = {}
    for c in ET.parse(OUT / name).iter('testcase'):
        failure = c.find('failure')
        if failure is None:
            failure = c.find('error')
        rows[c.get('classname')+'::'+c.get('name')] = {
            'passed': failure is None and c.find('skipped') is None,
            'signature': re.sub(r'0x[0-9a-fA-F]+', '<address>', failure.get('message','')) if failure is not None else '',
            'trace': failure.text if failure is not None else '',
        }
    return rows


def main():
    from tools.build_review_handoff import build_handoff
    sources = ['game/ordinary_semantic_ownership.py', 'game/live_chat_interpretation.py',
               'game/conversational_orchestration.py', 'game/immutable_valid_response.py',
               'tests/test_pr_du_player_pipeline.py', 'tests/test_turn_pipeline_shared.py',
               'tests/test_pr_ef_r2_social_authority.py', 'tools/validate_pr_ef_r2.py',
               'tools/build_pr_ef_r2_review.py']
    baseline, final = cases('baseline_junit.xml'), cases('final5_junit.xml')
    old = {k for k,v in baseline.items() if not v['passed']}
    new = {k for k,v in final.items() if not v['passed']}
    comparison = dict(baseline_passed=len(baseline)-len(old), baseline_failed=len(old),
                      final_passed=len(final)-len(new), final_failed=len(new),
                      resolved=sorted(old-new), new_failures=sorted(new-old),
                      inherited=sorted(old & new), added_tests=sorted(final.keys()-baseline.keys()),
                      changed_signatures={k:{'before':baseline[k]['signature'], 'after':final[k]['signature']}
                                          for k in old & new if baseline[k]['signature'] != final[k]['signature']},
                      baseline=baseline, final=final)
    save('regression_comparison.json', comparison)
    preservation = read('active_data_hashes_before.json')
    after = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (ROOT/'data').rglob('*') if p.is_file()}
    diffs = {k:{'before':preservation.get(k),'after':after.get(k)} for k in preservation.keys()|after.keys()
             if preservation.get(k)!=after.get(k)}
    save('active_data_preservation.json', dict(unchanged=not diffs, checked_files=len(preservation), differences=diffs))
    hashes = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
    save('source_hashes.json', hashes)
    patches=[]
    for p in sources[:4]:
        previous=(OUT/'source_before'/Path(p).name).read_text(encoding='utf-8')
        current=(ROOT/p).read_text(encoding='utf-8')
        patches.extend(difflib.unified_diff(previous.splitlines(True), current.splitlines(True), fromfile='before/'+p, tofile='after/'+p))
    save('pr_ef_r2_production_only.patch',''.join(patches))

    cluster=[]
    for key in sorted(old):
        filename=ROOT/(key.split('::')[0].replace('.','/')+'.py')
        func=key.split('::')[1].split('[')[0]
        text=filename.read_text(encoding='utf-8'); lines=text.splitlines()
        node=next((n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name==func),None)
        if key in old-new:
            category='A' if 'notice' not in func and 'pr_du_four' not in func else 'B'
            reason='Resolved by carrying social identity/operation into emission and rejecting unrelated scene prose; retired postseal-mutator assertions updated to the current validation boundary.'
            if 'pr_du_four' in func: reason='Authored notice-board wording is semantically clear; canonical action and disclosed clue content replace literal noun-phrase assertion.'
        elif 'exploration' in key or 'quarterstaff' in key or 'endpoint_specific' in func or 'social_pressure_line' in func:
            category='D'; reason='Examined signature concerns legacy endpoint resolution shape, exploration routing or absent combat mechanics, rather than resolved social identity crossing emission.'
        else:
            category='C'
            if 'retry' in func or 'known_follow_up' in func:
                reason='Legacy retry-call-count/debug-strategy expectations differ from current immutable generation lifecycle; not a contradictory validated target result.'
            elif 'mixed_' in func:
                reason='Embedded roll_requirement_query metadata absent in mixed dialogue; separate routing/metadata defect, unchanged signature.'
            elif 'direct_npc_question' in func:
                reason='Known runner target returns reply_kind=unknown; assertion excludes unknown. Distinct answer-classification contract, not identity loss.'
            elif 'active_target_direct' in func:
                reason='Question versus social_probe classification mismatch; separate social action taxonomy.'
            elif 'repeated_questioning' in func:
                reason='Refusal smoke expects a closed lexical list; current inability wording is outside that list. Separate refusal presentation/test contract.'
            elif 'interruption' in func:
                reason='Repeated interruption text does not progress; separate repeated-question/interruption policy.'
            elif 'sanitizer' in func:
                reason='Internal planner: scaffold survives output; separate output sanitization defect and release risk.'
            else:
                reason='Generic/advisory stock wording survives older social policy path; separate response-quality/validation coverage defect. It is retained as a known limitation, not declared safe by aggregate counts.'
        cluster.append(dict(test=key, category=category, reason=reason, baseline_signature=baseline[key]['signature'],
                            final_signature=final.get(key,{}).get('signature'), resolved=key not in new,
                            source=str(filename.relative_to(ROOT)), line=node.lineno if node else None,
                            examined_test_source='\n'.join(lines[node.lineno-1:node.end_lineno]) if node else ''))
    save('social_cluster_classification.json',cluster)

    semantic=[]
    for name in ['holdouts_1.json','holdouts_2.json','holdouts_3.json','holdouts_4.json','behavior_1.json']:
        sample=read(name); rows=[]
        for r in sample['rows']:
            live=r.get('isolated_interpretation') or (r['resolution'].get('metadata') or {}).get('live_chat_interpretation') or {}
            raw=live.get('raw_interpretation')
            if not raw and r.get('wire') and isinstance(r['wire'][0],dict): raw=r['wire'][0].get('text')
            try: parsed=json.loads(raw or '{}')
            except (ValueError,TypeError): parsed={}
            expected=r['expected']; comm=parsed.get('communication') or {}
            actual=comm.get('purpose') if expected in ['CORRECTION','WITHDRAWAL','CONFIRMATION'] else comm.get('recipient')
            rows.append(dict(turn=r['turn'],player=r['player'],expected=expected,raw_label=actual,
                             strict_raw_pass=actual==expected if parsed else None,
                             strict_normalized_pass=r.get('strict_pass'),behavior_pass=r['behavior_pass'],
                             response=r['response'],state_violation=r['critical']))
        # The explicit ambiguous expression must obtain clarification. The
        # implicit continuation must preserve NPC ownership, not just quote it.
        semantic.append(dict(sample=name, fresh_provider=sample['fresh_provider'], rows=rows,
                             original_24_behavior=sum(r['behavior_pass'] for r in rows[:24]),
                             additional_behavior=sum(r['behavior_pass'] for r in rows[24:]),
                             strict_raw_agreement=sum(r['strict_raw_pass'] is True for r in rows),
                             raw_labels_available=sum(r['strict_raw_pass'] is not None for r in rows),
                             state_integrity_violations=sum(r['state_violation'] for r in rows)))
    save('semantic_audit.json',semantic)

    transcripts=[]; perf=[]
    for name in ['conversation_1.json','conversation_2.json','conversation_3.json','originals_1.json','originals_2.json']:
        sample=read(name); turns=[]; cursor=0
        for r in sample['rows']:
            usage=sample['provider']['records'][cursor:cursor+r['provider_calls']];cursor+=r['provider_calls']
            md=r['resolution'].get('metadata') or {}; live=md.get('live_chat_interpretation') or {}
            gm_md=r['gm_output'].get('metadata') or {}
            turns.append(dict(turn=r['turn'],player=r['player'],response=r['response'],
                              raw_interpretation=live.get('raw_interpretation') or [w.get('text') for w in r['wire'] if isinstance(w,dict)],
                              normalized_interpretation=live.get('record'), decision=md.get('conversational_decision'),
                              authoritative_result=md.get('authoritative_result'),resolver_result=r['resolution'],
                              final_validation=gm_md.get('accepted_response'),state_changes=r['state_changes'],
                              provider_records=usage,provider_calls=r['provider_calls'],elapsed_ms=r['elapsed_ms'],
                              behavior_pass=r['behavior_pass'],save_load_context_equal=r.get('save_load_context_equal')))
        transcripts.append(dict(sample=name,exact_final_code=name in ['conversation_3.json','originals_2.json'],turns=turns))
        perf.append(dict(sample=name,requests=sample['provider']['requests'],input_tokens=sample['provider']['input_tokens'],
                         output_tokens=sample['provider']['output_tokens'],total_tokens=sample['provider']['total_tokens'],
                         retries=sum(str(x.get('purpose','')).startswith('retry') for x in sample['provider']['records']),
                         median_ms=statistics.median(r['elapsed_ms'] for r in sample['rows'])))
    save('transcript_audit.json',transcripts); save('performance_comparison.json',perf)
    usage=[json.loads(line) for p in OUT.glob('*.usage.jsonl') for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
    totals=dict(requests=sum(r.get('sent') is True for r in usage),input_tokens=sum(r.get('input_tokens') or 0 for r in usage),
                output_tokens=sum(r.get('output_tokens') or 0 for r in usage),total_tokens=sum(r.get('total_tokens') or 0 for r in usage))
    save('provider_totals.json',totals)
    final_conversation=next(t for t in transcripts if t['sample']=='conversation_3.json')
    live_sem=semantic[-1]; final_recorded=semantic[-2]
    recommendation='C — PR-EF REQUIRES FURTHER REPAIR'
    summary=f'''# 01 — Executive Summary

**{recommendation}. Stop before PR-EG.**

The three original social failures are repaired in recorded replay and fresh final-code production requests. A continuous eleven-turn final-code /api/chat conversation passes: GM observation/follow-up, explicit and implicit NPC questions, knowledge limitation, GM clarification of the latest NPC reply, incidental gesture, inspection, withdrawal and established movement. This is real production ASGI HTTP with fresh interpretation/narration, no provider fixtures, and one persistent initialized disposable campaign.

The existing contract now consumes validated bridge ASK identity and resolver identity; unknown knowledge stays separate from unknown target. Terminal fallbacks are validated and cannot manufacture a passing seal. Conservative posture normalization preserves consequential secondary operations. Notice-board test now validates canonical referent and disclosed content.

Fresh production holdouts pass {live_sem['original_24_behavior']}/24 original and {live_sem['additional_behavior']}/9 additional expressions. Explicit NPC ownership, implicit continuation, correction and ambiguous addressee failures in the additional set prevent acceptance. The ambiguous request incorrectly consumes a turn and advances passive world state, a critical authorization/state-integrity failure. These are preserved as failures, not removed or rewritten. Final recorded replay is {final_recorded['original_24_behavior']}/24 original, {final_recorded['additional_behavior']}/9 additional. Existing regression family: {comparison['baseline_passed']} pass/{comparison['baseline_failed']} fail → {comparison['final_passed']} pass/{comparison['final_failed']} fail, with {len(old-new)} resolved and {len(new-old)} new failing identities. Twenty-two added targeted checks pass. Active campaign preservation: {not diffs}.

The work supports continued bounded repair, not architectural replacement. Do not begin PR-EG. Broader dialogue defects and performance limitations remain documented.
'''
    reports={'01_EXECUTIVE_SUMMARY.md':summary}
    reports['02_BASELINE_AND_ENVIRONMENT.md']=f'''# 02 — Baseline and Environment

Revision: { (OUT/'revision.txt').read_text().strip() }. Starting working tree is extensively dirty; status_before.txt and source_before preserve it. No AGENTS.md found in relevant source/test/tool directories; R1 also recorded none. Existing changes were retained; no Git reset, branch switch, commit, active campaign reset or dependency upgrade.

Current baseline re-established before production changes: 293 passing / 26 failing. Exact test IDs, stack signatures, command and JUnit are in baseline_command.json, baseline_output.txt, baseline_junit.xml and regression_comparison.json. Final command final5_command.json adds the R2 test file to the same eighteen-file comparison family. Run: .venv/Scripts/python.exe -m pytest [files in command JSON] --tb=line -q --override-ini=addopts= --basetemp=development/tmp/<unique> --junitxml=<artifact>. Full repository suite was not run.

Provider availability verified by one request; configured gpt-4.1-mini, observed gpt-4.1-mini-2025-04-14. Interpretation output cap 320; narration cap 1600; harness timeout 25 seconds. PR-ED provider_budget.begin_request/finish_request, usage JSONL, retry purposes, token totals and model identity retained. Secrets and .env excluded. Budget revisions are explicit in budget.json; actual totals {totals}. Disposable campaign uses the existing PR-DQ fixture; live tests patch only storage paths, never provider outputs. Test/replay doubles are explicitly labeled.

Sandbox attempts hung in Windows asyncio socketpair before HTTP dispatch. Repeated production/test commands outside the sandbox completed. This is an execution-environment limitation, not a gameplay failure. The initial 21-row replay accidentally paired new expressions with old captured outputs after row 12; holdouts_0.json is invalid beyond row 12 and excluded from scores. Corrected baseline holdouts_1.json reuses the unchanged prior 24.
'''
    reports['03_SOCIAL_FAILURE_RECONSTRUCTION.md']='''# 03 — Social Failure Reconstruction

Diagnosis preceded production edits: DIAGNOSIS_BEFORE_IMPLEMENTATION.md. Full before traces: original_failure_traces.json, holdouts_1.json; full after: holdouts_2.json, holdouts_4.json, originals_2.json. Each contains raw message/provider JSON, normalized record, ownership, primary/incidental metadata, bridge, social result, emission validation, response and complete state before/after.

| Case | Exact condition | Before | Final |
|---|---|---|---|
| I ask Mara what troubles her. | Bridge and social resolver bind sergeant_mara, but legacy entity_binding remains unresolved with interlocutor_id=null. Invalid invented answer is correctly rejected; safe_nonresolution incorrectly consults stale binding. | Person cannot be identified. | Known Sergeant Mara accurately cannot answer. |
| I tell the sergeant to describe the courtyard. | Legacy operation=unresolved and no interlocutor despite validated ASK and successful speaker binding. generic_ask_completion cannot find a speaker. | No one here can answer. | Known Sergeant Mara accurately cannot answer from available knowledge. |
| I turn to Mara and ask about the north road. | SOCIAL_SIGNAL treated as unsupported consequential component and topic north road treated as unresolved reference. Bridge/compound eligibility blocks supported ASK. | No social resolver invocation; false compound refusal. | One ASK, gesture retained as incidental; authorized north-road statement. |

A and B share lost contract authority but differ in stale target versus lost operation. C fails before resolver. The original narration double invents a road answer for questions without an authored answer; rejecting that text remains correct. Fixing its rejection by permitting invented NPC knowledge would be wrong.
'''
    reports['04_AUTHORITY_CONTRACT_AUDIT.md']='''# 04 — Authority Contract Audit

The production interpreter proposes ASK and a canonical visible ID. The existing player_interpretation_bridge validates ID, visibility and compatible NPC type. establish_ordinary_gameplay_contract retains that validated binding in the existing resolution_contract before specialized resolver selection; it does not infer target from raw text again. Explicit bound conflicts become authority_conflict; old unbound interlocutors cannot override a validated new target.

The social resolver owns addressability, final NPC, selected topic, reply kind, social state and information authority. carry_authoritative_contract adds compact metadata.authoritative_result with operation, target ID/label/status, outcome, state changes, selected public fact, information authority and response constraints. It reconciles an unbound legacy contract only when there is no unresolved explicit addressee or conflicting bound target. The full social result remains the source of topic/knowledge details. Pre-bridge/pre-social binding metadata preserves audit provenance. No additional provider or parallel interpretation pipeline is introduced.

Emission consumes this shared contract plus resolution.social. A resolved NPC cannot become no-one/unidentified prose. Known target/unknown answer receives a speaker-attributed inability. Wrong speakers, unauthorized facts, failed actions narrated successful, hidden information and unrequested speech continue to fail validation. Conflicting authoritative sources do not silently select an NPC: terminal candidates remain rejected, no fabricated passing seal, effects_allowed=false. The conflict tests cover both retry and no-retry paths.

Remaining risks: legacy non-bridge paths may expose stale explicit binding conflicts and require clarification; speaker recognition is conservative for complex speech syntax; upstream provider ownership may still suppress the resolver before this contract can apply. These are not fixed by trusting every resolver field without context.
'''
    reports['05_PRIMARY_INCIDENTAL_INTENT_AUDIT.md']='''# 05 — Primary/Incidental Intent Audit

normalize_social_scope operates within the existing production interpretation normalization. It accepts one INTERPRETED, NPC-owned ASK with a target; only a wholly described orientation/attention gesture to that same canonical target is incidental. Its nominal must match target words, and sequencing/weapon/conditional terms cannot enter the gesture grammar. Original raw provider output remains intact; normalized incidental_context preserves the description. Malformed record shapes remain adapter errors.

Unresolved phrases contained in the declared question subject may be treated as topics only when the remaining operation is that single targeted ASK. A missing target, explicit clarification status, unrelated unresolved person, independent MOVE, weapon draw, threat or unlocking prerequisite remains represented and unexecuted until existing compound validation permits it. Tests include draw sword, unlock door, then leave, unknown addressee and secondary movement. Clarification now retains proposed secondary intentions even when a provider labels a conditional request SESSION rather than MIXED.

An additional captured gesture exposed head (body noun) being matched by the existing movement shortcut. Possessive body-part uses of head no longer count as the movement verb. The existing semantic call can then classify the whole request; bounded head orientation normalizes like facing/glancing. No exact holdout sentence or NPC name is a production key. The original PR-EC sequence/dependency and save/load tests remain in the comparison family.

Additional semantic ownership errors remain: incorrect GM labels, implicit NPC context, correction purpose and ambiguity. Preserving a consequential request during clarification is behavioral success even if the strict label is not MIXED; label metrics are reported separately.
'''
    reports['06_FINAL_RESPONSE_CONSISTENCY_AUDIT.md']='''# 06 — Final-Response Consistency Audit

| Class | Authority → consumer | Disposition / coverage |
|---|---|---|
| A resolved target becomes unresolved | Bridge/social → legacy contract/fallback | Repaired; three captured production cases and unknown-answer test. |
| B success becomes generic refusal | Social identity/topic → final construction | Known identity retained; selected-topic projection still validates. Unknown knowledge is a valid outcome, not falsely claimed answer success. |
| C failure narrated success | Mechanics → hard validation | Existing mechanical_success/adjudication/combat checks retained; positive/negative test. |
| D NPC statement becomes contradictory GM exposition | Emitted log → public recall | Latest NPC reply, including inability, now has explicit public evidence; final live turn 6 repeats latest inability rather than older road topic. Broader implicit-owner failure remains. |
| E grounded information becomes generic uncertainty | Selected social topic → projection and final seal | Authorized north-road fact survives original C and implicit follow-up in final conversation. |
| F primary replaced by incidental action | Normalization → eligibility/orchestration | Conservative posture scope and possessive-head noun repair; compound actions preserved. |
| G unauthorized facts | Decision/topic/visibility → hard validators | Invented concern/road claims rejected in raw live attempt traces; hidden-information and wrong-speaker tests retained. No new state authority granted. |

Known social requests with unrelated scene prose are incomplete. Two legacy terminal branches previously manufactured hard_valid=true when even the terminal fallback failed validation; these now return controlled rejection and effects_allowed=false. This tightens validation rather than suppressing it. Existing imperfect linguistic validators can still overreject complex attribution; that is a remaining quality/coverage limit, not evidence of an authorized answer.
'''
    reports['07_NOTICE_BOARD_REGRESSION.md']='''# 07 — Notice-Board Regression

Category A: brittle exact wording in a context with adequate referential clarity. experiments/pr_dq/world.py authors NOTICE_TEXT as “The board names the north road past the waystation.” The player explicitly requests the notice board, the action_id remains notice_board, prior arrival introduces a notice board, and state records the inspected interactable/clue. No established contract requires repeating “notice board” in the clue.

The PR-DU test now requires canonical action_id=NOTICE_ID, board, north road and waystation plus its existing movement, turn count, resolved-interactable and log assertions. This checks successful grounded reading without rewriting authored content. The inherited failure resolves; no production text was changed for this assertion. Exact before/after signature is in regression_comparison.json.
'''
    reports['08_SOCIAL_REGRESSION_CLUSTER.md']='# 08 — Social Regression Cluster\n\nEvery baseline failure was inspected using its signature and test body; social_cluster_classification.json retains full source excerpts and reasons. A = same root; B = direct dependency; C = separate conversational defect/test contract; D = unrelated inherited failure. Categories C/D remain visible and are not acceptance evidence.\n\n| Exact test | Class | Final | Reason |\n|---|---|---|---|\n'+ '\n'.join(f"| {r['test']} | {r['category']} | {'resolved' if r['resolved'] else 'fails'} | {r['reason']} |" for r in cluster)
    reports['09_SEMANTIC_REQUALIFICATION.md']='# 09 — Semantic Requalification\n\nThe original 24 are the unchanged PR-EF holdouts plus R1 independent holdouts. Nine additional expressions were frozen before production changes (additional_holdouts.json). No expression was removed/reworded. Strict raw labels, normalized labels and end-to-end behavior are distinct. In fresh production original 24: 24 behavioral passes, zero detected authority/state violations or authoritative-result contradictions. In additional nine: five passes, four intent/ownership failures, one critical ambiguous-target authorization/state violation, zero identified disclosures or contradictions of an already validated target. Critical turn and full state evidence are retained in behavior_1.json. Holdouts replay interpretation while stubbing narration; behavior_1 uses fresh production interpretation AND narration. Deterministic fast paths have no raw provider label and are excluded from label denominator.\n\n| Sample | Original behavior /24 | Additional /9 | Raw strict agreement / available | State violations |\n|---|---:|---:|---:|---:|\n'+ '\n'.join(f"| {r['sample']} | {r['original_24_behavior']} | {r['additional_behavior'] if len(r['rows'])>24 else 'not sampled'} | {r['strict_raw_agreement']}/{r['raw_labels_available']} | {r['state_integrity_violations']} |" for r in semantic)+'''

Fresh isolated holdouts_3 were collected before the final topic-containment/head-noun/secondary-retention refinements. Final holdouts_4 is explicitly recorded replay of those outputs. Additional implicit-context isolated row 27 was evaluated without conversation log due to the harness's prior log=[] input; do not treat that row as a valid context-aware isolated qualification. Fresh production behavior_1 uses actual persisted setup and log and is final-code evidence. Its four additional failures are preserved in the detailed table below. Core final-code fresh 24 behavioral result is independently demonstrated; final fresh isolated remeasurement of all 33 was not performed.

Behavior checks include attribution, resolver identity and actual state as appropriate; they remain bounded assertions and do not establish all language semantics. One additional fresh production ambiguous-target holdout (turn 33) executed a social turn and advanced time/faction state when clarification was required: a critical authorization/state-integrity failure. No hidden-information disclosure or contradiction of an already validated final social target was identified; rejected provider drafts contain unauthorized claims and remain evidence of successful rejection, not emitted authority violations. Ownership/response relevance failures are correctness defects and block acceptance.

'''+ '\n'.join(f"- Turn {r['turn']}: {r['player']} → {r['response']}" for r in live_sem['rows'] if not r['behavior_pass'])
    lines=['# 10 — Fresh Live Conversation Evidence','', 'Three continuous eleven-turn production conversations are preserved. Samples 1/2 preceded final refinements; conversation_3 and originals_2 use exact final production code. The campaign remains initialized and persistent within each conversation; no reset between turns, no rewritten messages, no recorded provider outputs. HTTP uses FastAPI TestClient over actual /api/chat routing with storage redirected to disposable files. Every turn saves and reloads state; turn 6 explicitly round-trips conversational context. This is in-process ASGI HTTP, not a separately hosted server.','', 'Full per-turn raw/normalized interpretation, routing, resolver, final seal, usage and state: transcript_audit.json and original JSON files.','']
    for t in transcripts:
        lines += [f"## {t['sample']} — exact final code={t['exact_final_code']}",'']
        for r in t['turns']:
            lines += [f"### Turn {r['turn']} — {'PASS' if r['behavior_pass'] else 'FAIL'}",'', 'Player: '+r['player'],'','Response: '+r['response'],'',f"Result={r['resolver_result'].get('kind')}; NPC={(r['resolver_result'].get('social') or {}).get('npc_id')}; provider calls={r['provider_calls']}; latency={r['elapsed_ms']}ms. Full state changes and final-validation evidence are linked by this sample/turn in transcript_audit.json.",'']
    reports['10_FRESH_LIVE_CONVERSATION_EVIDENCE.md']='\n'.join(lines)
    reports['11_AUTHORITY_AND_PERSISTENCE_AUDIT.md']=f'''# 11 — Authority and Persistence Audit

Active data files checked: {len(preservation)}; unchanged={not diffs}. active_data_preservation.json contains actual hash comparisons. All experiments used disposable initialized campaigns.

Actual before/after session/world/character/combat objects and key/value diffs are retained for every turn. Final conversation informational turns 1,2,6,9 leave world, character, combat, scene and turn counter unchanged; logs/context/timestamps may change. Social turns 3,4,5,7,10 consume one turn and existing passive faction pressure, social runtime/interaction context and authorized disclosure. Their world faction/event_log changes are existing deterministic tick effects, not unauthorized provider mutations. Tests compare other world domains/NPC knowledge exactly. Inspection reveals lantern_mark once; movement enters authored waystation_street once. Character/combat remain unchanged throughout.

Hidden/public boundary tests, stale confirmation, withdrawal, pending sequence, save/load and movement families remain passing. A separate additional semantic holdout (behavior_1 turn 33) incorrectly advances one turn/time_pressure and world faction pressure/agenda under an unresolved plural target; this is a critical qualification failure outside the successful conversation. The 22 R2 tests add speaker identity, unknown answer, wrong speaker, unknown target, hidden information, failed/success mechanical narration, incidental/consequential scope, public latest reply, fail-closed conflicts and save/load (ignoring only last_saved_at). No duplicate resolver execution was observed; one-turn increments are asserted. Unknown targets cannot be silently replaced by a fallback NPC. These are bounded observations, not proof of every possible state mutation.
'''
    reports['12_PERFORMANCE_COMPARISON.md']='# 12 — Performance Comparison\n\n| Sample | Calls | Input tokens | Output | Total | Retry-purpose calls | Median turn ms |\n|---|---:|---:|---:|---:|---:|---:|\n'+'\n'.join(f"| {p['sample']} | {p['requests']} | {p['input_tokens']} | {p['output_tokens']} | {p['total_tokens']} | {p['retries']} | {p['median_ms']} |" for p in perf)+f'''

Whole cycle provider totals: {totals}. Raw request/model/token/latency records are in usage JSONL; missing fields remain unknown, not silently zeroed per request. End-to-end latency is perf_counter across actual HTTP. Retry totals count stamped provider purposes; summarized retry_count can underreport compared with request records. Some narration usage records lack provider latency, so HTTP time is the reliable per-turn timing here.

Matched original-24 recorded baseline/final provider-free HTTP timings are in recorded_performance.json; both use the same captured interpretation workload but are single local runs, not controlled benchmarks.

Historical R1 ten-turn observation was about 40,755 tokens and 2.74s median. Final R2 has eleven turns and three knowledge-limited/request patterns provoking large strict-social prompts and bounded retry; its roughly 200k-token conversation is substantially more expensive in observed totals. Workloads are different, so this is not a controlled speed/cost comparison and no improvement is claimed. The repair adds no mandatory interpretation call, no new narration route, no broad retry or unbounded memory; it preserves the one-retry ceiling and deterministic PR-ED skip seams. Existing strict-social context size/overrejection/retry behavior remains an important efficiency limitation. A default budget increase was explicitly recorded after measuring prompt size; there was no silent cap bypass.
'''
    reports['13_REGRESSION_COMPARISON.md']=f'''# 13 — Regression Comparison

Baseline: {comparison['baseline_passed']} pass / {comparison['baseline_failed']} fail. Final: {comparison['final_passed']} pass / {comparison['final_failed']} fail. Added tests: {len(comparison['added_tests'])}. Resolved: {len(old-new)}. New failing IDs: {len(new-old)}. Changed inherited signatures: {len(comparison['changed_signatures'])}. Exact command JSON, XML and output files preserved, with full identity/signature comparison in regression_comparison.json. This is the established comparison family, not the entire repository suite. An unchanged intermediate run (final4) hit WinError 5 during atomic session-file replacement; the isolated persistence test passed, and final5 repeated the complete suite with that identity passing. Both runs are retained.

Resolved identities:
'''+ '\n'.join('- '+x for x in sorted(old-new))+'\n\nNew failing identities:\n'+ ('\n'.join('- '+x for x in sorted(new-old)) or '- None.')+'\n\nRemaining inherited identities:\n'+'\n'.join('- '+x for x in sorted(new))+'\n\nChanged signatures (before → after):\n'+json.dumps(comparison['changed_signatures'],indent=2)
    reports['14_REMAINING_ISSUES.md']='''# 14 — Remaining Issues

Critical conversational qualification gaps remain in additional fresh production holdouts: an explicitly asked NPC question is answered by GM uncertainty; an implicit NPC follow-up is routed through GM exposition; a correction becomes an informational answer; an ambiguous target is treated as a resolved Mara interaction. The ambiguous-target request consumed a turn and advanced passive faction state instead of clarifying: a critical authorization/state-integrity failure. No hidden disclosure was identified. These fail intent/ownership correctness and prohibit acceptance. Existing ambiguous-target input has only one named visible NPC, yet the plural request still merits focused clarification; its unresolved reference and silently chosen NPC are retained for review.

Twenty inherited regression IDs remain, individually classified in report 08. In particular scaffold/advisory leakage and repeated-interruption behavior need independent repair; legacy retry metadata assertions require lifecycle reconciliation; mixed embedded-rules metadata and action taxonomy remain separate defects. Conservative speech attribution can reject syntactically valid NPC narration and increase generic inability fallbacks. Current GM uncertainty and “what is settled here” dialogue are mechanically safe but low quality. Large social contexts and retries dominate cost.

PR-EG depends on external review and further conversational correctness repair; it was not started. Formal campaign creation, combat/exploration routing expansion, campaign lifecycle and overall dialogue style redesign were not implemented. No evidence requires architectural replacement; extending the existing contract demonstrably repaired original failures.
'''
    reports['15_FINAL_RECOMMENDATION.md']=f'''# 15 — Final Recommendation

**{recommendation}.**

Original A/B/C repairs and final-code continuous live qualification are established, so UNVERIFIED would be inaccurate. Acceptance A/B would also be inaccurate: additional fresh production ownership/correction/ambiguity failures and inherited final-response defects remain. Architecture D is not supported: narrow existing-contract changes preserve validated social decisions without a parallel pipeline.

Submit CURRENT_REVIEW for external review. Stop after PR-EF-R2; do not begin PR-EG. Recommended next work is a separately authorized bounded ownership/clarification repair and context-cost audit using the preserved failing messages, without exact-phrase handlers or weakened safeguards.
'''
    purposes=['Carry validated ASK/social identity and compact authoritative result.', 'Normalize bounded incidental scope and public latest-reply guidance.', 'Retain incidental/secondary context and latest emitted NPC reply; avoid body-head movement.', 'Validate known identity/interaction and fail closed on invalid terminal fallback.', 'Check notice-board semantics/canonical target.', 'Reconcile two retired speaker-mutator assertions with current sealed validation.', 'Twenty-two new authority/intent/persistence tests.', 'Bounded replay/fresh interpretation/production conversation harness.', 'Generate reproducible review and exact identity/signature audits.']
    reports['16_CHANGED_FILE_INVENTORY.md']='# 16 — Changed-File Inventory\n\nOnly these files were intentionally edited/created for R2; starting dirty state is separate. Production-only diff compares source_before with final files, not Git HEAD. Artifact snapshots and generated reports live in artifacts/pr_ef_r2; CURRENT_REVIEW uses the established builder and archives its predecessor.\n\n| File | Purpose | SHA-256 |\n|---|---|---|\n'+'\n'.join(f'| {p} | {purpose} | {hashes[p]} |' for p,purpose in zip(sources,purposes))+ '\n\nValidation commands: baseline_command.json; final5_command.json; focused_final.xml; tools/validate_pr_ef_r2.py --mode holdouts --variant 4 --replay artifacts/pr_ef_r2/holdouts_3.json; --mode behavior --variant 1; --mode conversation --variant 3; --mode originals --variant 2. Existing outputs are protected against overwrite for live runs. Relevant authority source: player_interpretation_bridge.py, social.py, resolution_contract.py, gm_resolution_decision.py, provider_budget.py. These existing files were inspected; no edits attributed to this cycle.\n'
    for name,value in reports.items(): save(name,value)
    save('REVIEW.md','# PR-EF-R2 — Social Authority & Final-Response Consistency\n\n**'+recommendation+'**\n\n'+'\n'.join(f'- [{n}]({n})' for n in reports))
    files=[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='handoff_config.json'
           and ('source_before' not in p.parts or p.name in {Path(s).name for s in sources[:4]})]
    extra=['artifacts/pr_ef_r1/holdouts_1.json','artifacts/pr_ef_r1/independent_holdouts.json','artifacts/pr_ef_gm_authority/holdouts.json',
           'tests/test_pr_ef_gm_authority.py','experiments/pr_dq/world.py']
    config=dict(campaign_id='pr_ef_r2_social_authority_20261016',campaign_name='PR-EF-R2 — Social Authority & Final-Response Consistency',
                campaign_date='2026-10-16',purpose='Bounded repair and final-code qualification; stop before PR-EG.',
                objective_status='REQUIRES FURTHER REPAIR',executive_summary=summary,
                changes={'production':purposes[:4],'validation':purposes[4:8],'documentation':[purposes[8]]},
                testing={'focused':'22 R2 checks pass.','broader':f"{comparison['baseline_passed']}/{comparison['baseline_failed']} → {comparison['final_passed']}/{comparison['final_failed']} pass/fail.",
                         'full_suite':'Established family only; full suite not run.', 'runtime_validation':'Final-code 11-turn continuous conversation and three original expressions pass.',
                         'model_runtime_boundary':f"gpt-4.1-mini; {totals['requests']} requests; recorded runs labeled separately.",
                         'new_regressions':str(sorted(new-old)), 'pre_existing_failures':str(len(new & old))},
                known_problems={'campaign_specific':['Four additional fresh production ownership/correction/ambiguity failures, including one unauthorized turn/state advance.','Large strict-social prompts and retry cost.'],
                                'pre_existing':['Twenty inherited regression failures; see exact signatures/classification.']},
                decisions_requiring_human_review=['Review C recommendation; do not begin PR-EG.'],
                does_not_prove=['Universal semantic reliability.','Fresh isolated final-code interpretation score for all 33.','Controlled performance improvement.','Full repository regression safety.'],
                recommended_next_step='External PR-EF-R2 review; further bounded repair before PR-EG.',
                primary_report='artifacts/pr_ef_r2/REVIEW.md',max_file_bytes=24*1024*1024,evidence_packets=[],
                supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='source' if p.relative_to(ROOT).as_posix() in sources else 'evidence',
                                       why='R2 review report, raw trace, baseline, final evidence or reproducible source.',
                                       behavioral_evidence=p.suffix in ['.json','.jsonl'],human_review_required=p.suffix=='.md')
                                  for p in [*files,*(ROOT/p for p in sources+extra)]],
                self_contained_review_test='Sixteen reports, before/final authority traces, exact-final live HTTP/provider/state evidence, frozen expressions, JUnit, source snapshots/diff and manifest included. No .env, active saves or dependencies.')
    save('handoff_config.json',config)
    result=build_handoff(config,root=ROOT,output_dir=ROOT/'handoff',archive_history=True)
    print(json.dumps({k:result[k] for k in ['summary_path','zip_path','file_count','zip_size_bytes']}))


if __name__=='__main__': main()
