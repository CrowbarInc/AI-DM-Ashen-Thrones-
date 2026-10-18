"""Generate the bounded R1 review and portable CURRENT_REVIEW handoff."""
from __future__ import annotations
import difflib
import hashlib
import json
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/pr_ef_r1'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def save(name, value):
    text = value.strip() + '\n' if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
    (OUT / name).write_text(text, encoding='utf-8')


def cases(name):
    result = {}
    for c in ET.parse(OUT / name).iter('testcase'):
        failure = c.find('failure')
        result[c.get('classname') + '::' + c.get('name')] = {
            'passed': failure is None and c.find('error') is None,
            'signature': re.sub(r'0x[0-9a-fA-F]+', '<address>', failure.get('message', '')) if failure is not None else '',
        }
    return result


def main():
    from tools.build_review_handoff import build_handoff
    baseline, final = cases('baseline_junit.xml'), cases('final_junit.xml')
    old = {k for k, v in baseline.items() if not v['passed']}
    new = {k for k, v in final.items() if not v['passed']}
    regression = {
        'baseline_passed': len(baseline) - len(old), 'baseline_failed': len(old),
        'final_passed': len(final) - len(new), 'final_failed': len(new),
        'inherited': sorted(old & new), 'new_failures': sorted(new - old), 'resolved': sorted(old - new),
        'added_tests': sorted(set(final) - set(baseline)),
        'changed_failure_signatures': {k: {'before': baseline[k]['signature'], 'after': final[k]['signature']} for k in old & new if baseline[k]['signature'] != final[k]['signature']},
        'baseline': baseline, 'final': final,
    }
    save('regression_comparison.json', regression)
    before = read('active_data_hashes_before.json')
    after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'data').rglob('*') if p.is_file()}
    differences = {k: {'before': before.get(k), 'after': after.get(k)} for k in set(before) | set(after) if before.get(k) != after.get(k)}
    save('active_data_preservation.json', {'unchanged': not differences, 'checked_files': len(before), 'differences': differences, 'after_hashes': after})

    transcripts, handoffs, perf = [], [], []
    for n in range(1, 6):
        sample = read(f'conversation_{n}.json')
        cursor, turns = 0, []
        for r in sample['rows']:
            usage = sample['provider']['records'][cursor:cursor + r['provider_calls']]
            cursor += r['provider_calls']
            md = r['resolution'].get('metadata') or {}
            live = md.get('live_chat_interpretation') or {}
            traces = [t for t in r['state_after']['session'].get('debug_traces', []) if isinstance(t, dict) and t.get('raw_input') == r['player'] and 'normalized_action' in t]
            trace = traces[-1] if traces else {}
            passed = r['behavior_pass'] and (r['turn'] != 7 or 'mark' in r['response'].lower())
            turn = {
                'turn': r['turn'], 'player': r['player'], 'raw_provider_interpretation': [w.get('text') for w in r['wire']],
                'normalized_interpretation': live.get('record'), 'deterministic_decision': r['deterministic_decision'],
                'ownership': ((live.get('record') or {}).get('communication') or {}).get('recipient') or (r['deterministic_decision'] or {}).get('communication_owner'),
                'answer_decision': md.get('conversational_decision'), 'normalized_resolver_inputs': trace.get('normalized_action'),
                'selected_resolver': md.get('selected_resolver') or (md.get('conversational_decision') or {}).get('category'),
                'resolver_result': r['resolution'], 'response': r['response'], 'state_changes': r['state_changes'],
                'provider_requests': usage, 'provider_calls': r['provider_calls'], 'latency_ms': r['elapsed_ms'],
                'input_tokens': sum(u.get('input_tokens') or 0 for u in usage), 'output_tokens': sum(u.get('output_tokens') or 0 for u in usage),
                'total_tokens': sum(u.get('total_tokens') or 0 for u in usage),
                'provider_retry_requests': sum(str(u.get('purpose') or '').startswith('retry') for u in usage),
                'behavior_pass': bool(passed), 'critical': r['critical'], 'save_load_context_equal': r.get('save_load_context_equal'),
            }
            turns.append(turn)
            if r['turn'] in [4, 5, 7, 10]:
                handoffs.append({'sample': n, **turn})
        transcripts.append({'sample': n, 'passed': sum(t['behavior_pass'] for t in turns), 'exact_final_code': n == 5, 'turns': turns})
        perf.append({'sample': n, **{k: sample['provider'][k] for k in ['requests', 'input_tokens', 'output_tokens', 'total_tokens']}, 'median_turn_ms': statistics.median(r['elapsed_ms'] for r in sample['rows']), 'retry_stamped_requests': sum(str(r.get('purpose') or '').startswith('retry') for r in sample['provider']['records'])})
    save('transcript_audit.json', transcripts)
    save('operation_handoff_audit.json', handoffs)

    semantic = []
    for name in ['holdouts_1.json', 'holdouts_3.json']:
        rows = []
        for r in read(name)['rows']:
            raw = json.loads(r['isolated_interpretation'].get('raw_interpretation') or '{}')
            comm = raw.get('communication') or {}
            label = comm.get('purpose') if r['expected'] in ['CORRECTION', 'WITHDRAWAL', 'CONFIRMATION'] else comm.get('recipient')
            strict = label == r['expected']
            behavior = r['behavior_pass'] and r['turn'] not in [3, 11]
            note = {3: 'Social resolver binds Mara, but final emission says the person cannot be identified.', 11: 'NPC ownership is retained in resolution, but generic no-one prose does not deliver NPC communication.', 15: 'Unsupported ancillary SOCIAL_SIGNAL and unresolved dialogue topic block a supported ASK.'}.get(r['turn'], '')
            impact = 'agreement, correct behavior' if strict and behavior else 'A: incorrect label, correct behavior' if behavior else 'D: correct label, incorrect downstream behavior' if strict else 'B: incorrect label, inappropriate response'
            rows.append({'turn': r['turn'], 'player': r['player'], 'expected': r['expected'], 'raw_label': label, 'normalized_label': r['actual'], 'strict_raw_pass': strict, 'strict_normalized_pass': r['strict_pass'], 'routing_check_pass': r['behavior_pass'], 'reviewed_behavior_pass': behavior, 'impact': impact, 'note': note, 'critical': r['critical'], 'raw_interpretation': raw, 'normalized_interpretation': r['isolated_interpretation'].get('record'), 'resolution': r['resolution'], 'response': r['response'], 'state_changes': r['state_changes']})
        groups = []
        for label, start in [('frozen', 0), ('independent', 12)]:
            group = rows[start:start + 12]
            groups.append({'set': label, 'total': len(group), 'strict_raw': sum(r['strict_raw_pass'] for r in group), 'strict_normalized': sum(r['strict_normalized_pass'] for r in group), 'routing_checks': sum(r['routing_check_pass'] for r in group), 'reviewed_behavior': sum(r['reviewed_behavior_pass'] for r in group), 'critical': sum(r['critical'] for r in group)})
        semantic.append({'source': name, 'fresh_final_prompt': False, 'description': 'Fresh isolated provider after first repair, before later refinements' if name == 'holdouts_1.json' else 'Final-code replay of the same outputs; NOT fresh final-prompt holdouts', 'groups': groups, 'rows': rows})
    save('semantic_audit.json', semantic)
    usage = [json.loads(s) for p in OUT.glob('*.usage.jsonl') for s in p.read_text().splitlines() if s.strip()]
    totals = {k: sum(r.get(k) or 0 for r in usage if r.get('sent')) for k in ['input_tokens', 'output_tokens', 'total_tokens']}
    totals['requests'] = sum(r.get('sent') is True for r in usage)
    save('performance_comparison.json', {'cycle_totals': totals, 'live_samples': perf, 'historical_pr_ef_tokens': [85242, 87739], 'disabled_baseline': read('baseline_profile.json'), 'disabled_final': read('final_profile.json'), 'limits': read('budget.json'), 'comparability': 'Workloads, prompts, code and response outcomes differ. No controlled live speedup claim.'})

    modified, patch = [], []
    for snap in (OUT / 'source_before').iterdir():
        target = ROOT / 'game' / snap.name
        if target.exists() and target.read_bytes() != snap.read_bytes():
            rel = target.relative_to(ROOT).as_posix()
            modified.append(rel)
            patch.extend(difflib.unified_diff(snap.read_text(encoding='utf-8').splitlines(True), target.read_text(encoding='utf-8').splitlines(True), fromfile='before/' + rel, tofile='after/' + rel))
    save('pr_ef_r1_only.patch', ''.join(patch))
    sources = modified + ['tests/test_pr_ef_r1_semantic_handoff.py', 'tools/validate_pr_ef_r1.py', 'tools/build_pr_ef_r1_review.py', 'tools/replay_pr_ef_r1_baseline.py']
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    save('source_hashes.json', hashes)
    reports = {}
    reports['01_EXECUTIVE_SUMMARY.md'] = f'''# 01 — Executive Summary

**C — REQUIRES FURTHER REPAIR. Stop before PR-EG.**

Repaired same-call semantic ownership guidance/normalization, structured pending continuation, movement handoff, speech-versus-travel scope abstention, GM clarification, ambiguity safety and causal answer relevance. Successful authoritative clue discovery now uses its existing public result without redundant narration/retry, through the retained final-emission path.

Exact-final-code sample 5 passes all ten turns using fresh provider outputs through production /api/chat, one continuous disposable campaign, including NPC follow-up, inspection, causal explanation, withdrawal, save/load and reachable movement. Samples 3 and 4 also pass, with meaningfully different phrasing, before a subsequent ambiguity-only gate fix. Earlier failed attempts remain preserved. This establishes the formerly missing scenario evidence, not universal competence.

Remaining correctness failures include a resolved NPC receiving unidentified-person prose, generic no-one response to another NPC request and a captured ancillary gesture blocking supported dialogue. Final-prompt holdouts were not freshly resampled after later refinements: final holdout behavior is recorded-provider evidence. These gaps and a new presentation assertion prevent an unqualified acceptance claim.

Regression: {regression['baseline_passed']} passing / {regression['baseline_failed']} failing before; {regression['final_passed']} passing / {regression['final_failed']} failing after, including {len(regression['added_tests'])} new passing R1 checks. Five inherited failures resolve; one new wording-sensitive failure remains. No new authority/persistence failing ID in the final comparison. Active data unchanged: {not differences}.
'''
    reports['02_BASELINE_AND_ENVIRONMENT.md'] = (OUT / 'BASELINE.md').read_text() + f'''

Fresh pre-edit probe reproduced NPC/ASK for the GM expression question. Credential configuration was checked without exposing it. Returned model gpt-4.1-mini-2025-04-14; configured interpretation and narration gpt-4.1-mini. Production timeout 45s; validation 25s, interpretation cap 320 and narration cap 1600. Instrumentation active via provider_budget.

Actual cycle usage: {totals}. Self-imposed budget revisions 64 -> 68 -> 80 requests reserved additional final qualification after newly evidenced defects; token ceilings stayed 430000 input / 22000 output / 452000 total. No budget exhaustion or pre-repair acceptance substitution.

Commands: baseline_command.json and final_command.json; python tools/validate_pr_ef_r1.py --mode conversation --variant 5; --mode holdouts (fresh); --mode holdouts --variant 3 --replay artifacts/pr_ef_r1/holdouts_1.json (zero external requests). Provider-disabled HTTP tests run outside the Windows sandbox for local socketpair support; live-model test guards remain enabled. Representative comparison family only, not full repository suite.
'''
    reports['03_SEMANTIC_OWNERSHIP_DIAGNOSIS.md'] = '''# 03 — Semantic Ownership Diagnosis

Fresh pre-edit expression question becomes NPC/QUESTION/ASK. Frozen recorded production baseline reproduces 10/12 routing checks: expression initiates social/world progression; grounded movement finishes with a lantern fact. availability.json and baseline_recorded_holdouts.json preserve actual records and responses.

Confirmed causes: operation-first schema presentation with appended ownership instructions; recipient/function ambiguity; ACTION normalization overwriting NPC ownership; pending projection containing only kind; lexical continuity shortcuts bypassing semantic evidence selection; ordinary contract reparsing a grounded action without normalized input; GM clarification conflated with unresolved reference; causal questions answered by outcome repetition.

Repairs stay in the existing schema, prompt, normalization, decision, bridge and contract. No phrase catalog, independent ownership classifier, new provider layer or mandatory second call. semantic_audit.json records raw/normalized interpretations, decisions, responses, state effects and A/B/D impact for every disagreement. No label-induced unintended operation (C) observed in R1 holdout samples; the unchanged original PR-EF expression record still reproduces the known risk when replayed. Zero observed critical failures is a bounded result, not a universal guarantee.
'''
    reports['04_INTERPRETATION_CONTRACT_CHANGES.md'] = '''# 04 — Interpretation Contract Changes

Existing communication fields/enums retained. Property order selects communication before legacy operation fields. Descriptions and same-call instructions distinguish people discussed from people addressed, physical declarations from table procedure, pending control from actions, conditional/mixed intentions, ancillary orientation and dialogue topics from target references. Output cap remains 320.

Pending projection supplies at most four steps/choices, original support status and scene scope, plus existing public context. No private topic/clue evidence or independent transcript reconstruction. NPC/ACTION is no longer overwritten as CHARACTER. Inconsistent GM/SESSION ACTION with one physical component reconciles to CHARACTER; multiple components conservatively become MIXED. GM questions containing independent actions retain them without execution. Outcomes and eligibility remain engine-owned. Raw and normalized strict labels are measured separately.
'''
    reports['05_CONTINUATION_AND_CONTEXT_AUDIT.md'] = '''# 05 — Continuation and Context Audit

Semantic CONFIRMATION delegates to the existing pending owner and revalidates scene/bridge eligibility. Context updates retain remaining steps rather than deleting them. No-context assent clarifies; stale-scene assent expires. After persisted withdrawal, repeated assent cannot execute canceled movement. Corrections with one grounded replacement and a current compound revise its first unexecuted step, preserve later steps and request approval; invalid replacement does not execute. Without relevant context, correction asks for a restated action. Withdrawal never rolls back committed facts.

Ambiguous reference with selected scene evidence still clarifies if status is non-INTERPRETED or references remain unresolved. An interpreted GM clarification with public answer evidence is answered. Final recorded audit exposed this narrow distinction; a regression test and exact-final-code fresh full conversation follow the gate repair. Tests cover disk round-trip, nonduplication, stale context, new explicit intentions and missing context.
'''
    reports['06_PRODUCTION_HANDOFF_AUDIT.md'] = '''# 06 — Production Handoff Audit

Original MOVE grounds courtyard_gate -> authored waystation_street and passes the bridge. Ordinary contract construction receives normalized_action=None, reparses make-for wording as unresolved and rejects movement; clocks already advance and final fallback repeats a lantern fact. Correct interpretation alone did not imply resolution.

Repair passes validated normalized action into the existing contract constructor. The canonical movement operation and authored label supply contract processing text. Original raw input and bridge processing text remain in provenance. Accepted bridge action is selected directly, preventing peer-parser replacement. Existing authored destinations, compatibility checks, resolver preconditions and final emission remain authoritative.

Unchanged frozen movement and fresh original/alternate movement now transition once to the established street. Unknown destination test clarifies with unchanged world/time/scene. No invented destination or travel bypass. Overlapping speech/movement cues make the deterministic shortcut abstain so the existing semantic owner handles scope. operation_handoff_audit.json records each consequential turn's interpretations, normalized resolver inputs, selected resolver, complete result, state changes and final text; original JSON retains full sessions/traces.
'''
    reports['07_GROUNDED_ANSWER_RELEVANCE.md'] = '''# 07 — Grounded Answer Relevance

The recent-visible-answer shortcut formerly repeated an outcome for Why did I find that mark? It now defers live evidence selection to the existing semantic call. Public cause evidence is derived from a successful logged inspection/discovery: inspecting the target revealed the detail; that alone does not establish origin/purpose. Undiscovered clues remain excluded.

Exact-final answer: Your inspection of courtyard lantern revealed the detail. That explains how you found it; its origin or purpose has not been established by that discovery. NPC concern questions use public observation and acknowledge unknown cause. GM clarification selects an already disclosed NPC topic without starting dialogue.

Alternate live inspection exposed successful clue resolution followed by scene-only narration after retries. Successful discover_clue now takes the existing resolver-owned fact text through the PR-ED skip seam and retained final emission. Final live output includes the maker's mark. No new answer provider or broad narration redesign.

Limits: repeated scene summaries, conservative causal suffixes, unknown-ruling replies and legacy Word is framing. Held-out NPC fallback wording is still wrong. Rules answers admit lack of an established ruling rather than supplying unrelated interface guidance, but do not implement new rules advice. These are explicit response-quality limitations.
'''
    lines = ['# 08 — Semantic Holdout Results', '', 'Both original frozen 12 and independent 12 expressions are unchanged. Independent expressions froze before production edits. Metric A: strict label agreement. Metric B: reviewed player-facing behavior. Routing-only assertions are NOT behavioral correctness.', '']
    for sample in semantic:
        lines += ['## ' + sample['source'], '', sample['description'], '', '| Set | Raw strict | Normalized strict | Routing | Reviewed behavior | Critical observed |', '|---|---:|---:|---:|---:|---:|']
        for g in sample['groups']:
            lines.append(f"| {g['set']} | {g['strict_raw']}/12 | {g['strict_normalized']}/12 | {g['routing_checks']}/12 | {g['reviewed_behavior']}/12 | {g['critical']} |")
        lines += ['', '| Expression | Expected | Raw / normalized | Behavioral | Impact |', '|---|---|---|---|---|']
        for r in sample['rows']:
            lines.append(f"| {r['player']} | {r['expected']} | {r['raw_label']} / {r['normalized_label']} | {'PASS' if r['reviewed_behavior_pass'] else 'FAIL'} | {r['impact']}. {r['note']} |")
        lines += ['']
    lines += ['No fresh final-prompt holdout accuracy is claimed. The first fresh sample informed refinements; final replay is containment/regression evidence, not an unseen requalification. Original failed messages and outputs are preserved.']
    reports['08_SEMANTIC_HOLDOUT_RESULTS.md'] = '\n'.join(lines)
    lines = ['# 09 — Fresh Live Conversation Transcripts', '', 'All samples use production POST /api/chat?ui_mode=player, one initialized disposable campaign per conversation, no resets between turns, no changed player messages mid-run and fresh provider outputs whenever production calls them. Deterministic provider-free turns count as zero. Samples 1/2 fail and remain retained; 3/4 pass before the final ambiguity-only gate repair; 5 passes on exact final code. Sample 4 uses alternate phrasing. No records reused between live samples.', '', 'Raw/normalized interpretations, ownership, complete resolver results/inputs, per-request usage, state diffs and verdicts: transcript_audit.json plus original conversation JSON. Every sample explicitly round-trips save/load at turn six.', '']
    for t in transcripts:
        lines += [f"## Sample {t['sample']} — {t['passed']}/10; exact final code={t['exact_final_code']}", '']
        for r in t['turns']:
            lines += [f"### Turn {r['turn']} — {'PASS' if r['behavior_pass'] else 'FAIL'}", '', 'Player: ' + r['player'], '', 'Response: ' + r['response'], '', f"Owner={r['ownership']}; path={r['selected_resolver']}; result={r['resolver_result'].get('kind')}; calls={r['provider_calls']}; tokens={r['input_tokens']} in/{r['output_tokens']} out; latency={r['latency_ms']}ms. Changed state domains: {', '.join(k for k,v in r['state_changes'].items() if v)}.", '']
    reports['09_FRESH_LIVE_CONVERSATION_TRANSCRIPTS.md'] = '\n'.join(lines)
    reports['10_AUTHORITY_AND_PERSISTENCE_AUDIT.md'] = f'''# 10 — Authority and Persistence Audit

Exact-final informational turns 1/2/3/6/8/9 leave world, character, combat, turn counter and scene unchanged. Context, timestamps and logs may change; actual key/value differences are retained. NPC turns change existing social runtime/clocks/disclosure. Inspection reveals authored lantern_mark through exploration; movement changes courtyard to authored street once.

Tests cover pending assent, replacement, persisted cancellation, no-context and stale-scene confirmation, duplicate prevention after withdrawal, explicit new intentions and unknown destinations. Public evidence excludes undiscovered clues/private topics. Final-emission validators remain unchanged. Active campaign hashes: {len(before)} files; unchanged={not differences}. No active save was used as provider context.

Intermediate Windows atomic-replace permission failures match the inherited platform signature. intermediate_final_junit.xml preserves concurrent persistence failure; focused_final.xml shows isolated rechecks passing. Latest full comparison contains no new authority/persistence failing ID. Bounded state comparisons do not imply universal semantic safety.
'''
    lines = ['# 11 — Performance Comparison', '', '| Live sample | Calls | Input | Output | Total | Median turn ms | Retry-stamped requests |', '|---|---:|---:|---:|---:|---:|---:|']
    for r in perf:
        lines.append(f"| {r['sample']} | {r['requests']} | {r['input_tokens']} | {r['output_tokens']} | {r['total_tokens']} | {r['median_turn_ms']} | {r['retry_stamped_requests']} |")
    lines += ['', f'Cycle totals including availability/holdouts: {totals}. Budget revisions and actual limits in budget.json; no exhaustion. Request-level records are authoritative; missing usage is not zero. Retry count uses explicit retry_escalation provider purposes, not inferred response wording. Existing summary telemetry can report retry_count=0 despite a sent retry_escalation request; that instrumentation discrepancy is retained in raw resolutions and corrected only in this evidence aggregation.', '', 'Historical PR-EF sequences: 85,242 / 87,739 tokens and 9 calls each. Different code, prompts, phrasing and outcomes preclude a controlled live speedup claim. Same PR-ED disabled profiler: baseline median 89ms and 6 narration entries; final measured median 97ms and 5 entries. Single-run machine load differs; no latency improvement claim. The last ambiguity-only gate does not affect that profiler workload.', '', 'No mandatory second interpretation, new retry loop, model switch or full-transcript injection. Existing caps/timeouts/retry controls retained. Successful clue discovery skips redundant narration while NPC dialogue still uses its provider.']
    reports['11_PERFORMANCE_COMPARISON.md'] = '\n'.join(lines)
    lines = ['# 12 — Regression Comparison', '', f"Baseline {regression['baseline_passed']} pass/{regression['baseline_failed']} fail; final {regression['final_passed']} pass/{regression['final_failed']} fail. Added R1 checks: {len(regression['added_tests'])}, all passing. Inherited failing IDs {len(old & new)}; resolved {len(old-new)}; new {len(new-old)}; changed normalized inherited signatures {len(regression['changed_failure_signatures'])}.", '', 'Commands, exact IDs/signatures and raw results: baseline/final_command.json, JUnit and regression_comparison.json. Historical 256/30 -> 271/30 remain historical. This is the established representative family, not the entire repository suite.', '', 'New failing IDs:'] + ['- ' + k for k in sorted(new - old)]
    lines += ['', 'New PR-DU assertion expects literal notice board. State/inspection are correct, but final text says The board names the north road past the waystation. This presentation regression is retained and counted, not silently reclassified as a test pass. No new authority/persistence failure in the latest full comparison.', '', 'Resolved inherited IDs:'] + ['- ' + k for k in sorted(old - new)]
    lines += ['', 'Remaining inherited failing IDs:'] + ['- ' + k for k in sorted(old & new)]
    reports['12_REGRESSION_COMPARISON.md'] = '\n'.join(lines)
    reports['13_REMAINING_ISSUES.md'] = '''# 13 — Remaining Issues

Resolved visible NPC can still receive unidentified-person fallback. immutable_valid_response.safe_nonresolution checks a contradictory legacy contract addressee after social authority binds the speaker. Another captured request ends with generic no-one prose. Captured ancillary SOCIAL_SIGNAL and unresolved topic can block a supported ASK. Final prompt narrows ancillary/topic scope, but that failed output has not been freshly remeasured.

Strict raw labels remain inconsistent for correction, confirmation, ambiguity and mixed intention. Structured context contains several errors; final successful conversations do not establish universal holdout competence. Fresh final-prompt holdout scores remain unavailable. One new notice-board wording assertion fails; 25 inherited failures remain. Intermittent Windows concurrent persistence errors remain platform debt.

Limits: repeated public summaries, conservative explanations, unknown-ruling replies and legacy NPC framing. PR-EG dialogue quality, bounded improvisation and formal New Campaign workflow are deferred. PR-EH dependencies were not investigated or implemented; no new scope inferred. No evidence here requires an architectural rewrite.
'''
    reports['14_FINAL_RECOMMENDATION.md'] = '''# 14 — Final Recommendation

**C — REQUIRES FURTHER REPAIR.**

Exact-final-code sample 5 demonstrates the complete fresh-provider ten-turn scenario through production /api/chat. Original and alternate phrasing also passed before the final ambiguity-only gate repair. NPC continuation, inspection delivery, causal explanation, withdrawal, persistence and established movement now have live evidence. This is not UNVERIFIED due to unavailable access.

Conservative C retains the unresolved end-to-end NPC response and blocked-dialogue defects, incomplete final-prompt semantic requalification and new presentation regression for external review. Do not promote routing-only success or one successful scenario into broad acceptance. No claim of critical mutation in R1 is made; the remaining core communication correctness is the reason to withhold acceptance.

Next bounded review: carry resolver-validated interlocutor through the existing immutable response path; freshly requalify ancillary dialogue and control/ambiguous/mixed semantics; resolve or explicitly accept the presentation regression. No parallel interpreter or fundamental redesign indicated. Stop after PR-EF-R1; await external review before PR-EG.
'''
    purposes = {'game/live_chat_interpretation.py': 'Schema presentation, prompt/context and conservative label reconciliation.', 'game/conversational_orchestration.py': 'Semantic continuation, ambiguity/scope and public causal evidence.', 'game/api.py': 'Retain bridge action/context and successful discovery emission.', 'game/ordinary_semantic_ownership.py': 'Consume grounded normalized movement in existing contract.', 'game/player_interpretation_bridge.py': 'Carry authored visible target labels.'}
    lines = ['# 15 — Changed-File Inventory', '', 'Relative to the dirty pre-edit snapshots, not HEAD. status_before.txt and source_before preserve prior work. pr_ef_r1_only.patch contains bounded production changes. No unrelated user changes reverted.', '']
    for rel in sources:
        lines.append(f"- {rel}: {purposes.get(rel, 'R1 tests or reproducible validation/review tooling.')} SHA-256 {hashes[rel]}.")
        if rel in modified:
            for i, line in enumerate((ROOT / rel).read_text(encoding='utf-8').splitlines(), 1):
                if line.startswith('def ') and any(s in line for s in ['production_interpretation_schema', 'interpret_production_turn', '_communication_decision', 'public_conversation_evidence', '_analyze_clause', '_recent_visible_answer', 'deterministic_provider_skip_line', 'establish_ordinary_gameplay_contract', 'normalized_action_from_interpretation', 'decision_from_interpretation_record']):
                    lines.append(f"  Source: {rel}:{i} — {line.split('(')[0]}.")
    lines += ['', 'Generated: artifacts/pr_ef_r1 (15 reports, raw HTTP/provider/state evidence, baseline/final tests, profiles, audits, hashes and bounded patch); handoff/CURRENT_REVIEW.md, REVIEW_MANIFEST.json and CURRENT_REVIEW.zip. Existing builder archives previous handoff.']
    reports['15_CHANGED_FILE_INVENTORY.md'] = '\n'.join(lines)
    for name, body in reports.items():
        save(name, body)
    save('REVIEW.md', '# PR-EF-R1 — Semantic Ownership & Production Handoff Repair\n\n**C — REQUIRES FURTHER REPAIR.** Exact-final live conversation passes; semantic/final-response failures and a new presentation regression remain.\n\n' + '\n'.join(f'- [{n}]({n})' for n in reports) + '\n\nFull raw audits are adjacent. Stop before PR-EG.')
    request = Path('C:/Users/Master Mandalcio/.codex/attachments/113a17c8-1f56-45b6-9c39-fe813eb22307/Pasted text.txt')
    if request.exists():
        save('ORIGINAL_REQUEST.md', request.read_text(encoding='utf-8'))
    files = [p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc' and p.name != 'handoff_config.json']
    config = {
        'campaign_id': 'pr_ef_r1_semantic_handoff_20261016', 'campaign_name': 'PR-EF-R1 — Semantic Ownership & Production Handoff Repair',
        'campaign_date': '2026-10-16', 'purpose': 'Bounded repair and fresh production qualification; stop before PR-EG.',
        'objective_status': 'REQUIRES FURTHER REPAIR', 'executive_summary': reports['01_EXECUTIVE_SUMMARY.md'],
        'changes': {'production': list(purposes.values()), 'validation': ['18 R1 checks; 24 fresh semantic holdouts and final recorded audit; five continuous fresh-provider HTTP conversations.'], 'documentation': ['15 required reports, full evidence, exact test comparison and bounded source diff.']},
        'testing': {'focused': '18 R1 tests pass.', 'broader': f"{len(baseline)-len(old)} pass/{len(old)} fail -> {len(final)-len(new)} pass/{len(new)} fail; 5 inherited failures resolved, 1 new presentation failure.", 'full_suite': 'Not run; established comparison family only.', 'runtime_validation': 'Exact-final sample 5 passes 10/10; 3/4 also pass before final ambiguity-only gate. Failed samples retained.', 'model_runtime_boundary': f"gpt-4.1-mini; {totals['requests']} requests within 80 ceiling; disposable authored data only.", 'new_regressions': str(sorted(new-old)), 'pre_existing_failures': '25 inherited failing IDs remain.'},
        'known_problems': {'campaign_specific': ['Resolved NPC sometimes receives unidentified-person or generic no-one fallback.', 'Captured ancillary gesture blocks ASK; final-prompt holdouts not freshly resampled.', 'New notice-board presentation assertion.'], 'pre_existing': ['25 inherited failures and intermittent Windows file replacement denial.']},
        'decisions_requiring_human_review': ['Review conservative C recommendation and remaining correctness defects before PR-EG.'],
        'missing_concepts': ['Formal campaign-start workflow and PR-EG dialogue quality deferred.'],
        'does_not_prove': ['General conversational competence.', 'Fresh final-prompt holdout accuracy.', 'No regressions outside the comparison family.'],
        'recommended_next_step': 'External review of PR-EF-R1. Repair remaining conversational defects before PR-EG.',
        'primary_report': 'artifacts/pr_ef_r1/REVIEW.md', 'evidence_packets': [], 'max_file_bytes': 16 * 1024 * 1024,
        'supporting_files': [{'path': p.relative_to(ROOT).as_posix(), 'role': 'source' if p.relative_to(ROOT).as_posix() in sources else 'evidence', 'why': 'PR-EF-R1 report, reproducible source, baseline or raw evidence.', 'behavioral_evidence': p.suffix in ['.json', '.jsonl'], 'human_review_required': p.suffix == '.md'} for p in [*files, *(ROOT / s for s in sources)]],
        'self_contained_review_test': 'ZIP includes all 15 reports, complete exact-final raw/provider/HTTP/state records, earlier failures, usage, JUnit, snapshots, bounded diff and changed source/tests/tools with SHA-256 manifest. No dependencies, .env or active saves.',
    }
    save('handoff_config.json', config)
    result = build_handoff(config, root=ROOT, output_dir=ROOT / 'handoff', archive_history=True)
    print(json.dumps({k: result[k] for k in ['summary_path', 'zip_path', 'file_count', 'zip_size_bytes']}))


if __name__ == '__main__':
    main()
