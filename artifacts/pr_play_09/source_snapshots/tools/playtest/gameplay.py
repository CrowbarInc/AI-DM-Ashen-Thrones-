"""Bounded observation/evaluation of production turns; never a gameplay authority.

Missing native evidence stays unknown. Quality probes are not semantic validators.
Future offline judges may implement QualityReviewer; no provider client belongs here.
"""
from __future__ import annotations

import json
import hashlib
import time
from typing import Protocol

from tools.playtest.analysis import normalized_document, classify


class QualityReviewer(Protocol):
    def review(self, action: dict, text: str, prior: list[str]) -> dict: ...


def document(docs, name):
    return normalized_document(name, docs.get(name, {}))[0]


def prerequisite_failure(action, state):
    scene_id = document(state, 'session.json').get('active_scene_id')
    if scene_id != action['required_scene']:
        return 'Required scene no longer active'
    if action.get('required_npc'):
        npc = next((n for n in document(state, 'world.json').get('npcs', []) if n.get('id') == action['required_npc']), None)
        if not npc or npc.get('location') != scene_id:
            return 'Required NPC no longer present'
    if action.get('required_object'):
        scene = document(state, 'scenes/'+scene_id+'.json').get('scene', {})
        if not any(o.get('id') == action['required_object'] for o in scene.get('interactables', [])):
            return 'Required object no longer present'
    return None


def diff(before, after, path=''):
    if isinstance(before, dict) and isinstance(after, dict):
        return [item for key in sorted(before.keys() | after.keys())
                for item in diff(before.get(key), after.get(key), path+'/'+key)]
    def bounded(value):
        raw = json.dumps(value, ensure_ascii=True)
        return value if len(raw) <= 2048 else {'preview': raw[:2048], 'truncated': True,
                                             'characters': len(raw), 'sha256': hashlib.sha256(raw.encode()).hexdigest()}
    return [] if before == after else [{'path': path, 'before': bounded(before), 'after': bounded(after)}]


def quality(action, text, prior):
    probes = {'response_exists': bool(text.strip()),
              'requested_subject_mentioned': any(w.casefold() in text.casefold() for w in action['subject_terms']),
              'repeated_exact_response': bool(text and text in prior),
              'generic_marker': 'No one here can answer that from what is settled here.' in text}
    concerns = []
    if not text:
        concerns.append('insufficient_response_evidence')
    if text and not probes['requested_subject_mentioned']:
        concerns.append('possibly_irrelevant_response')
    if probes['repeated_exact_response']:
        concerns.append('repetitive_narration')
    if probes['generic_marker']:
        concerns.append('generic_nonresolution')
    dimensions = {}
    for key, label in [('Q1', 'Responsiveness'), ('Q2', 'Grounding'), ('Q3', 'Continuity'),
                       ('Q4', 'Actionability'), ('Q5', 'Narrative quality'), ('Q6', 'Agency and consequences')]:
        na = key in action.get('inapplicable_dimensions', [])
        dimensions[key] = {'dimension': label, 'score': None,
                           'status': 'N/A' if na else 'REQUIRES_HUMAN_REVIEW',
                           'evidence': text[:2000], 'method': 'human_review_pending',
                           'confidence': 'not_assessed',
                           'explanation': 'No immediate consequence required.' if na else
                           'Automated presence/subject/repetition probes cannot establish this 0–4 judgment.'}
    return {'rubric_version': 'pr-play-09-quality-v1', 'scale': {'0': 'Complete failure', '1': 'Major deficiency',
            '2': 'Partially adequate', '3': 'Good', '4': 'Strong'},
            'dimensions': dimensions, 'probes': probes, 'concerns': concerns,
            'method': 'deterministic presence and exact markers; heuristic relevance and repetition',
            'status': 'REQUIRES_HUMAN_REVIEW'}


def accounting(events):
    dispatched = [e for e in events if e.get('event') == 'dispatch_attempted']
    completions = [e for e in events if e.get('event') == 'completed']
    totals = {}
    for key in ('input_tokens', 'output_tokens', 'total_tokens'):
        values = [e.get(key) for e in completions]
        totals[key] = sum(values) if len(values) == len(dispatched) and all(isinstance(v, int) for v in values) else None
    return {'request_count': len(dispatched), **totals, 'retry_count': 0,
            'operations': [{k: e.get(k) for k in ('attempt_id', 'owner', 'purpose', 'configured_model',
                           'model', 'input_tokens', 'output_tokens', 'total_tokens', 'latency_ms',
                           'completion_status')} for e in completions],
            'provider_latency_ms': sum(e['latency_ms'] for e in completions) if all(isinstance(e.get('latency_ms'), (int, float)) for e in completions) else None,
            'provider_latency_status': 'native latency_ms only; unavailable remains null'}


def evaluate(action, status, body, before, after, events, prior=()):
    gm = body.get('gm_output') or {}
    text = gm.get('player_facing_text') or ''
    metadata = gm.get('metadata') or {}
    session_before, session_after = (document(d, 'session.json') for d in (before, after))
    changes = diff({k: document(before, k) for k in before}, {k: document(after, k) for k in after})
    resolution = body.get('resolution') or {}
    findings = []
    def finding(category, kind, evidence, source):
        findings.append({'category': category, 'kind': kind, 'evidence': evidence, 'source': source,
                         'step_id': action['step_id'], 'player_input': action['player_input'],
                         'dm_response': text[:8192], 'diagnostics': f"turns/{action['step_id']}/evaluation.json#diagnostics",
                         'state_comparison': f"turns/{action['step_id']}/evaluation.json#state_diff"})
    if status != 200:
        finding('http_failure', 'confirmed_mechanical_failure', status, 'production HTTP outcome')
    if session_after.get('campaign_started') is not True:
        finding('campaign_not_started', 'confirmed_mechanical_failure', session_after.get('campaign_started'), 'game.api.start_campaign')
    scene_before, scene_after = session_before.get('active_scene_id'), session_after.get('active_scene_id')
    if scene_after != scene_before and (action['interaction_category'] != 'movement' or scene_after not in action.get('allowed_destinations', [])):
        finding('unauthorized_scene_transition', 'confirmed_mechanical_failure', [scene_before, scene_after], 'pinned scene exits and player intent')
    for change in changes:
        path = change['path']
        if any(path == p or path.startswith(p+'/') for p in action['forbidden_state_changes']):
            finding('unauthorized_state_mutation', 'confirmed_mechanical_failure', change, 'scenario forbidden changes; docs/state_authority_model.md')
    turn_delta = int(session_after.get('turn_counter') or 0)-int(session_before.get('turn_counter') or 0)
    log_delta = len(after.get('session_log.jsonl') or [])-len(before.get('session_log.jsonl') or [])
    if turn_delta not in (0, 1) or log_delta not in (0, 1) or (turn_delta == 1 and log_delta != 1):
        finding('invalid_progression', 'confirmed_mechanical_failure', [turn_delta, log_delta], 'game.api chat nonmutating/resolved turn contracts')
    old_world, new_world = (document(d, 'world.json') for d in (before, after))
    unknown_world_roots = set(new_world)-set(old_world)
    if unknown_world_roots:
        finding('unauthorized_state_mutation', 'confirmed_mechanical_failure', sorted(unknown_world_roots), 'pinned world schema; no new persistent gameplay structures')
    # Observe authoritative validations, including original rejected candidates, separately from final recovery.
    validations = {k: metadata.get(k) for k in ('hard_validation_attempt_1', 'hard_validation_attempt_2', 'accepted_response') if k in metadata}
    for key, value in validations.items():
        if isinstance(value, dict) and value.get('hard_valid') is False:
            finding('semantic_validation_failure', 'confirmed_semantic_failure', {key: value}, 'game.immutable_valid_response native validation')
    bad = [e for e in events if e.get('classification') in {'provider_error', 'json_parse_failure', 'missing_structured_envelope', 'structured_validation_failure', 'empty_provider_content'} or e.get('provider_status') in {'incomplete', 'failed', 'cancelled'}]
    if bad:
        finding(classify(bad)['category'], 'confirmed_mechanical_failure', bad, 'native provider/parser diagnostic')
    if any(e.get('event') == 'rejected' for e in events):
        finding('provider_budget_exhaustion', 'scenario_limitation', accounting(events), 'game.provider_budget admission')
    accepted = metadata.get('accepted_response') or {}
    hard_validation = accepted.get('hard_validation') or {}
    if hard_validation.get('hard_valid') is False:
        finding('semantic_validation_failure', 'confirmed_semantic_failure', hard_validation, 'native accepted_response.hard_validation')
    # No reconstruction of dice/rules. Compare only explicit native resolution and emission evidence.
    rules = {'status': 'uncertain', 'evidence': resolution, 'source': 'production resolution; no independent adjudication'}
    if resolution:
        rules['status'] = 'recorded_requires_review'
    # This is the engine's canonical noncombat contract, not a narration-quality audit.
    nc = resolution.get('noncombat_resolution') or {}
    if nc:
        contradictions = []
        if nc.get('requires_check') is True and not nc.get('check_request'):
            contradictions.append('required_check_request_missing')
        expected = {'success': True, 'failure': False}.get(nc.get('success_state'))
        if expected is not None and isinstance(resolution.get('success'), bool) and resolution['success'] != expected:
            contradictions.append('success_disagrees_with_engine_contract')
        if contradictions:
            finding('invalid_rules_adjudication', 'confirmed_mechanical_failure', contradictions, 'game.noncombat_resolution canonical engine contract')
            rules['status'] = 'FAIL'
        elif nc.get('deterministic_resolved') is True or nc.get('outcome_type') == 'pending_check':
            rules['status'] = 'PASS'
        rules['canonical_contract'] = nc
    if scene_after != scene_before and resolution and (resolution.get('resolved_transition') is not True or resolution.get('target_scene_id') != scene_after):
        finding('invalid_movement_resolution', 'confirmed_mechanical_failure', resolution, 'native resolved_transition/target_scene_id')
    if any(e.get('event') == 'completed' and (e.get('error') or e.get('completion_status') in {'failed', 'interrupted'}) for e in events):
        finding('provider_transport_failure', 'confirmed_mechanical_failure', events, 'native completed ledger record')
    tags = gm.get('tags') or []
    if 'provider_budget_refused' in tags:
        finding('provider_budget_exhaustion', 'scenario_limitation', tags, 'native provider_budget_refused tag')
    live = (resolution.get('metadata') or {}).get('live_chat_interpretation') or {}
    if live.get('reason') in {'malformed_json', 'invalid_json', 'malformed_response', 'malformed_interpretation', 'malformed_communication'}:
        finding('invalid_interpretation_response', 'confirmed_mechanical_failure', live, 'production interpretation validation')
    if (resolution.get('metadata') or {}).get('authoritative_mutation') is False:
        # Conversation bookkeeping/logging may change, but explicit nonmutating responses cannot alter world truth.
        if old_world != new_world or scene_before != scene_after or turn_delta:
            finding('nonmutating_contract_violation', 'confirmed_mechanical_failure', changes, 'resolution.metadata.authoritative_mutation=false')
    if scene_after != scene_before and not resolution:
        finding('movement_authority_unavailable', 'unknown', [scene_before, scene_after], 'resolution absent from response')
    q = quality(action, text, list(prior))
    for concern in q['concerns']:
        finding(concern, 'unknown' if not text else 'heuristic_quality_concern', q['probes'], 'pr-play-09-quality-v1')
    provider_records = [e for e in events if e.get('stage') == 'provider_response']
    technical = [f for f in findings if f['kind'] == 'confirmed_mechanical_failure']
    semantic = [f for f in findings if f['kind'] == 'confirmed_semantic_failure']
    completion = not technical and not any(f['category'] == 'provider_budget_exhaustion' for f in findings) and bool(text)
    return {'step_id': action['step_id'], 'player_input': action['player_input'], 'dm_response': text[:8192],
            'response_truncated': len(text) > 8192, 'http_status': status,
            'outcome_classification': {'kind': 'legitimate_gameplay_outcome' if hard_validation.get('hard_valid') is True and resolution.get('success') is False and not technical else 'unknown',
                                       'evidence': 'native accepted response and resolution; no invented success condition'},
            'state_diff': changes, 'state_before': f"turns/{action['step_id']}/before/documents.json",
            'state_after': f"turns/{action['step_id']}/after/documents.json",
            'diagnostics': events, 'provider_usage': accounting(events),
            'mechanical': {'status': 'FAIL' if technical else 'PASS' if text else 'INCONCLUSIVE',
                           'completed_interaction': completion,
                           'turn_delta': turn_delta, 'log_delta': log_delta, 'scene_before': scene_before,
                           'scene_after': scene_after, 'rules': rules,
                           'mutation_authority': 'REQUIRES_HUMAN_REVIEW for changes not covered by explicit invariants'},
            'semantic': {'status': 'FAIL' if semantic else 'RECORDED' if validations else 'UNKNOWN',
                         'final_hard_validation': hard_validation.get('hard_valid'),
                         'native_validation': validations, 'nonresolution': accepted.get('provenance'),
                         'gameplay_acceptance': body.get('ok', body.get('status') == 'ok'),
                         'provider_stages': provider_records,
                         'extraction': [e.get('extraction_succeeded') for e in provider_records],
                         'json_parsing': [e.get('json_parsing_succeeded') for e in provider_records],
                         'structured_validation': [e.get('structured_validation_result') for e in provider_records]},
            'quality': q, 'findings': findings,
            'stop': bool(technical or semantic or any(f['category'] == 'provider_budget_exhaustion' for f in findings))}


def read_events(run):
    path = run/'diagnostics/provider_usage.jsonl'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()] if path.exists() else []


def execute_turn(run, action, base, timeout, request, snapshot, prior):
    deadline = time.monotonic()+timeout
    def remaining():
        value = deadline-time.monotonic()
        if value <= 0:
            raise TimeoutError('Turn deadline')
        return value
    folder = run/'turns'/action['step_id']
    folder.mkdir(parents=True)
    (folder/'before').mkdir()
    (folder/'after').mkdir()
    before = snapshot(run, f"turns/{action['step_id']}/before", base, remaining())
    offset = len(read_events(run))
    started = time.monotonic()
    try:
        status, body = request(base, 'POST', '/api/chat', remaining(), {'text': action['player_input'], 'ui_mode': 'player'})
    except Exception as exc:
        # Controller finally shuts down worker before preserving interrupted state.
        (folder/'interruption.json').write_text(json.dumps({'step_id': action['step_id'], 'player_input': action['player_input'],
            'error_type': type(exc).__name__, 'elapsed_seconds': time.monotonic()-started, 'stop': True}), encoding='utf-8')
        raise
    after = snapshot(run, f"turns/{action['step_id']}/after", base, min(remaining(), 10))
    row = evaluate(action, status, body, before, after, read_events(run)[offset:], prior)
    row['application_latency_seconds'] = round(time.monotonic()-started, 4)
    row['ok'] = not row['stop']
    row['action'] = 'player_turn'
    (folder/'api_response.json').write_text(json.dumps(body, indent=2), encoding='utf-8')
    (folder/'evaluation.json').write_text(json.dumps(row, indent=2), encoding='utf-8')
    return row


def finalize(result):
    turns = [r for r in result['steps'] if r['action'] == 'player_turn']
    findings = [f for t in turns for f in t.get('findings', [])]
    result.update(attempted_turns=len(turns), completed_turns=sum(t.get('mechanical', {}).get('status') == 'PASS' for t in turns),
                  gameplay_turns=turns, state_integrity_findings=[f for f in findings if f['kind'] == 'confirmed_mechanical_failure'])
    result['completed_turns'] = sum(t.get('mechanical', {}).get('completed_interaction', False) for t in turns)
    result['earliest'] = {name: next((f for f in findings if f['kind'] == kind), None)
                          for name, kind in [('mechanical_failure', 'confirmed_mechanical_failure'),
                                             ('semantic_failure', 'confirmed_semantic_failure'), ('quality_concern', 'heuristic_quality_concern')]}
    if result['opening_acceptance'] is False or result.get('opening_state_comparison', {}).get('integrity') is False:
        row = next((r for r in result['steps'] if r['action'] == 'start_campaign'), {})
        evidence = {'step_id': 'opening', 'player_input': '[Start Campaign]',
                    'dm_response': ((row.get('response') or {}).get('gm_output') or {}).get('player_facing_text'),
                    'category': (result.get('failure_classification') or {}).get('category', 'opening_rejected'),
                    'source': 'native opening acceptance/state comparison', 'diagnostics': 'diagnostics/provider_usage.jsonl',
                    'state_comparison': result['state_comparison']}
        result['earliest']['mechanical_failure'] = evidence
        if evidence['category'] == 'semantic_validation_failure':
            result['earliest']['semantic_failure'] = evidence
    if result['verdict'] != 'BLOCKED':
        if result['opening_acceptance'] is False or any(f['kind'].startswith('confirmed_') for f in findings):
            result['verdict'] = 'FAIL'
        elif result.get('stop_reason') == 'provider_budget_exhaustion' or any(f['category'] == 'provider_budget_exhaustion' for f in findings):
            result['verdict'] = 'BLOCKED'
        elif result.get('stop_reason') == 'scenario_divergence':
            result['verdict'] = 'PARTIAL'
        elif len(turns) != 5 or any(t.get('semantic', {}).get('status') == 'UNKNOWN' for t in turns):
            result['verdict'] = 'INCONCLUSIVE'
    result['stop_reason'] = result.get('stop_reason') or ('completed' if len(turns) == 5 and all(t.get('ok') for t in turns) else (result.get('failure_classification') or {}).get('category') or 'opening_or_execution_stopped')
    result['skipped_turns'] = [{'step_id': a['step_id'], 'reason': result['stop_reason']} for a in result['scenario']['actions']
                             if a['kind'] == 'player_turn' and a['step_id'] not in {t.get('step_id') for t in turns}]
    result['five_meaningful_interactions'] = 'REQUIRES_HUMAN_REVIEW' if result['completed_turns'] == 5 and result['stop_reason'] == 'completed' else 'NOT_ESTABLISHED'
    usage = result['provider_usage']
    lines = ['# GAMEPLAY REPORT', '', f"Scenario: {result['scenario']['id']} v{result['scenario']['version']}; mode: {result['mode']}",
             f"Opening: {result['opening_acceptance']}; turns completed: {result['completed_turns']}/5; mechanical verdict: {result['verdict']}",
             f"Usage: {usage.get('dispatched_requests')} requests; input/output/total {usage.get('input_tokens')}/{usage.get('output_tokens')}/{usage.get('total_tokens')}; cumulative application time {result['elapsed_seconds']} seconds.",
             'Narrative quality: REQUIRES_HUMAN_REVIEW; no authoritative automatic scores.', '']
    for t in turns:
        lines += [f"## {t.get('step_id', 'Interrupted turn')}", '', 'Player: '+t.get('player_input', ''), '',
                  'DM: '+t.get('dm_response', '[response unavailable]'), '',
                  'Changed paths: '+', '.join(c['path'] for c in t.get('state_diff', [])),
                  'Mechanical: '+str(t.get('mechanical', {}).get('status'))+'; semantic: '+str(t.get('semantic', {}).get('status')),
                  'Quality concerns: '+', '.join(t.get('quality', {}).get('concerns', []))+'; dimensions require human review.',
                  f"Performance: {t.get('application_latency_seconds')} application seconds; {json.dumps(t.get('provider_usage'))}",
                  f"Evidence: turns/{t.get('step_id')}/evaluation.json; before/; after/; api_response.json", '']
    lines += ['## Failure analysis', '', json.dumps({k: {'step_id': v['step_id'], 'category': v['category'], 'source': v['source']} if v else None for k, v in result['earliest'].items()}, indent=2),
              'Root cause: not established. Evidence paths: turns/<step>/; diagnostics/provider_usage.jsonl.',
              '## Final assessment', '', 'Did the game sustain five meaningful interactions? '+result['five_meaningful_interactions'],
              'Synthetic transport validates instrumentation, not live AI-DM competence. Unknown native rules/state authority requires review.',
              'Stop: '+str(result['stop_reason']), '']
    return '\n'.join(lines)
