"""Prompt compression layer for GPT narration.

Builds a concise, structured context from full game state before constructing
the narration prompt. Reduces token usage and keeps narration coherent by
including only relevant elements.
"""
from __future__ import annotations

from typing import Any, Dict, List
import re

# Configurable limits for deterministic, inspectable compression
MAX_RECENT_LOG = 5
MAX_RECENT_EVENTS = 5
MAX_GM_GUIDANCE = 3
MAX_WORLD_PRESSURES = 3
MAX_LOG_ENTRY_SNIPPET = 200
MAX_FOLLOW_UP_TOPIC_TOKENS = 6
MAX_RECENT_CONTEXTUAL_LEADS = 4

SOCIAL_REPLY_KINDS = frozenset({
    'question',
    'persuade',
    'intimidate',
    'deceive',
    'barter',
    'recruit',
    'social_probe',
})
NPC_REPLY_KIND_VALUES = frozenset({'answer', 'explanation', 'reaction', 'refusal'})

# Single source of truth for narration-rule precedence. Prompting and
# deterministic enforcement both read this so conflicts resolve the same way.
RESPONSE_RULE_PRIORITY: tuple[tuple[str, str], ...] = (
    ("must_answer", "ANSWER THE PLAYER"),
    ("forbid_state_invention", "DO NOT CONTRADICT AUTHORITATIVE STATE"),
    ("forbid_secret_leak", "DO NOT LEAK HIDDEN FACTS / SECRETS"),
    ("allow_partial_answer", "IF FULL CERTAINTY IS UNAVAILABLE, GIVE A BOUNDED PARTIAL ANSWER"),
    ("diegetic_only", "MAINTAIN DIEGETIC VOICE (no validator/system voice)"),
    ("prefer_scene_momentum", "PRESERVE SCENE MOMENTUM"),
    ("prefer_specificity", "ADD SPECIFICITY / FLAVOR / POLISH"),
)

RULE_PRIORITY_COMPACT_INSTRUCTION = (
    "When rules conflict, resolve them in this order: answer the player; preserve authoritative "
    "state; avoid leaking hidden facts; if certainty is incomplete, give a bounded partial answer; "
    "remain diegetic; maintain scene momentum; then add specificity."
)
NO_VALIDATOR_VOICE_RULE = (
    "Never speak as a validator, analyst, referee of canon, or system. Do not mention what is or "
    "is not established, available to the model, visible to tools, or answerable by the system. "
    "If uncertainty exists, express it as in-world uncertainty from people, circumstances, clues, "
    "distance, darkness, rumor, missing access, or incomplete observation."
)
NO_VALIDATOR_VOICE_PROHIBITIONS: tuple[str, ...] = (
    "canon_validation",
    "evidence_review",
    "system_limitation",
    "tool_access",
    "model_identity",
    "rules_explanation_outside_oc_or_adjudication",
)
UNCERTAINTY_CATEGORIES: tuple[str, ...] = (
    "unknown_identity",
    "unknown_location",
    "unknown_motive",
    "unknown_method",
    "unknown_quantity",
    "unknown_feasibility",
)
UNCERTAINTY_ANSWER_SHAPE: tuple[str, ...] = (
    "known_edge",
    "unknown_edge",
    "next_lead",
)

_TOPIC_TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z']{2,}")
_TOPIC_STOPWORDS = frozenset({
    "what", "where", "when", "why", "how", "who", "which",
    "tell", "said", "says", "know", "knew", "think", "heard",
    "about", "again", "still", "really", "actually", "just",
    "there", "here", "them", "they", "their", "then", "than",
    "with", "from", "into", "onto", "over", "under", "near",
    "this", "that", "these", "those", "your", "you're", "youre",
    "have", "has", "had", "can", "could", "would", "should",
    "does", "did", "is", "are", "was", "were", "will",
})
_FOLLOW_UP_PRESS_TOKENS: tuple[str, ...] = (
    "again",
    "still",
    "okay but",
    "ok but",
    "but",
    "be specific",
    "details",
    "name",
    "names",
    "where exactly",
    "who exactly",
)


def _topic_tokens(text: str) -> List[str]:
    low = " ".join(str(text or "").strip().lower().split())
    if not low:
        return []
    toks = [t for t in _TOPIC_TOKEN_PATTERN.findall(low) if len(t) >= 4 and t not in _TOPIC_STOPWORDS]
    seen: set[str] = set()
    out: List[str] = []
    for t in toks:
        if t in seen:
            continue
        out.append(t)
        seen.add(t)
        if len(out) >= MAX_FOLLOW_UP_TOPIC_TOKENS:
            break
    return out


def _overlap_ratio(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa = set(a)
    sb = set(b)
    inter = len(sa & sb)
    denom = min(len(sa), len(sb))
    return float(inter) / float(denom or 1)


def _compute_follow_up_pressure(recent_log_compact: List[Dict[str, Any]], user_text: str) -> Dict[str, Any] | None:
    """Detect when the player is pressing the same topic over consecutive turns.

    This is intentionally lightweight and prompt-scoped: it uses only the recent
    log slice already passed to the model (no new persistence/memory subsystem).
    """
    if not recent_log_compact:
        return None
    last = recent_log_compact[-1] if isinstance(recent_log_compact[-1], dict) else {}
    prev_player = str(last.get("player_input") or "").strip()
    prev_gm = str(last.get("gm_snippet") or "").strip()
    if not prev_player or not prev_gm:
        return None

    cur = str(user_text or "").strip()
    if not cur:
        return None

    cur_low = cur.lower()
    press_marker = any(tok in cur_low for tok in _FOLLOW_UP_PRESS_TOKENS)
    cur_tokens = _topic_tokens(cur)
    prev_tokens = _topic_tokens(prev_player)
    overlap = _overlap_ratio(cur_tokens, prev_tokens)

    pressed = (overlap >= 0.55 and len(cur_tokens) >= 2) or (press_marker and overlap >= 0.35 and len(cur_tokens) >= 1)
    if not pressed:
        return None

    press_depth = 1
    for entry in reversed(recent_log_compact[:-1]):
        if not isinstance(entry, dict):
            break
        txt = str(entry.get("player_input") or "").strip()
        if not txt:
            break
        if _overlap_ratio(cur_tokens, _topic_tokens(txt)) < 0.35:
            break
        press_depth += 1
        if press_depth >= 3:
            break

    return {
        "pressed": True,
        "press_depth": press_depth,
        "topic_tokens": cur_tokens,
        "previous_player_input": prev_player[:240],
        "previous_answer_snippet": prev_gm[:240],
        "overlap_ratio": round(overlap, 3),
    }


def build_response_policy(*, narration_obligations: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build the inspectable response policy for the current turn.

    This keeps the precedence ladder explicit in one place so prompt assembly
    and post-generation enforcement can share it instead of re-encoding order.
    """
    obligations = narration_obligations if isinstance(narration_obligations, dict) else {}
    return {
        "rule_priority_order": [label for _, label in RESPONSE_RULE_PRIORITY],
        "must_answer": True,
        "forbid_state_invention": True,
        "forbid_secret_leak": True,
        "allow_partial_answer": True,
        "diegetic_only": True,
        "prefer_scene_momentum": True,
        "prefer_specificity": True,
        "no_validator_voice": {
            "enabled": True,
            "applies_to": "standard_narration",
            "rule": NO_VALIDATOR_VOICE_RULE,
            "prohibited_perspectives": list(NO_VALIDATOR_VOICE_PROHIBITIONS),
            "rules_explanation_only_in": ["oc", "adjudication"],
        },
        "scene_momentum_due": bool(obligations.get("scene_momentum_due")),
        "uncertainty": {
            "enabled": True,
            "categories": list(UNCERTAINTY_CATEGORIES),
            "answer_shape": list(UNCERTAINTY_ANSWER_SHAPE),
            "context_inputs": ["turn_context", "speaker", "scene_snapshot"],
        },
    }


def _resolve_active_interaction_target_name(
    session: Dict[str, Any],
    world: Dict[str, Any],
    public_scene: Dict[str, Any],
) -> str | None:
    """Resolve active interaction target id to an in-scene NPC name when available."""
    interaction_ctx = session.get('interaction_context') or {}
    if not isinstance(interaction_ctx, dict):
        return None
    target_id = str(interaction_ctx.get('active_interaction_target_id') or '').strip()
    if not target_id:
        return None

    scene_id = str(public_scene.get('id') or '').strip()
    npcs = world.get('npcs') or []
    if not isinstance(npcs, list):
        return None

    target_id_low = target_id.lower()
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        npc_id = str(npc.get('id') or '').strip()
        if not npc_id or npc_id.lower() != target_id_low:
            continue
        npc_loc = str(npc.get('location') or npc.get('scene_id') or '').strip()
        if scene_id and npc_loc and npc_loc != scene_id:
            continue
        npc_name = str(npc.get('name') or '').strip()
        return npc_name or None
    return None


def _compress_campaign(campaign: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize campaign to essential narration context. No hidden/secret fields."""
    if not campaign or not isinstance(campaign, dict):
        return {'title': '', 'premise': '', 'character_role': '', 'gm_guidance': [], 'world_pressures': []}

    gm_guidance = campaign.get('gm_guidance') or []
    if isinstance(gm_guidance, list):
        gm_guidance = gm_guidance[:MAX_GM_GUIDANCE]
    else:
        gm_guidance = []

    world_pressures = campaign.get('world_pressures') or []
    if isinstance(world_pressures, list):
        world_pressures = world_pressures[:MAX_WORLD_PRESSURES]
    else:
        world_pressures = []

    return {
        'title': str(campaign.get('title', '') or '')[:200],
        'premise': str(campaign.get('premise', '') or '')[:500],
        'tone': str(campaign.get('tone', '') or '')[:200],
        'character_role': str(campaign.get('character_role', '') or '')[:300],
        'gm_guidance': gm_guidance,
        'world_pressures': world_pressures,
        'magic_style': str(campaign.get('magic_style', '') or '')[:300],
    }


def _compress_world(world: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize world: world_state + recent events + faction names. No full dumps."""
    if not world or not isinstance(world, dict):
        return {'world_state': {'flags': {}, 'counters': {}, 'clocks_summary': []}, 'recent_events': [], 'faction_names': []}

    ws = world.get('world_state') or {}
    if not isinstance(ws, dict):
        ws = {}
    flags = {k: v for k, v in (ws.get('flags') or {}).items() if isinstance(k, str) and not k.startswith('_')}
    counters = {k: v for k, v in (ws.get('counters') or {}).items() if isinstance(k, str) and not k.startswith('_')}
    clocks_raw = ws.get('clocks') or {}
    clocks_summary = [
        f"{k}: {int(c.get('progress', 0))}/{int(c.get('max', 10))}"
        for k, c in clocks_raw.items()
        if isinstance(k, str) and not k.startswith('_') and isinstance(c, dict)
    ]
    world_state_view = {'flags': flags, 'counters': counters, 'clocks_summary': clocks_summary}

    event_log = world.get('event_log') or []
    recent_events: List[str] = []
    if isinstance(event_log, list):
        for entry in event_log[-MAX_RECENT_EVENTS:]:
            if isinstance(entry, dict) and isinstance(entry.get('text'), str):
                recent_events.append(entry['text'][:200])
            elif isinstance(entry, str):
                recent_events.append(entry[:200])

    factions = world.get('factions') or []
    faction_names: List[str] = []
    if isinstance(factions, list):
        for f in factions[:10]:
            if isinstance(f, dict) and isinstance(f.get('name'), str):
                faction_names.append(f['name'])

    return {
        'world_state': world_state_view,
        'recent_events': recent_events,
        'faction_names': faction_names,
    }


def _compress_session(
    session: Dict[str, Any],
    world: Dict[str, Any],
    public_scene: Dict[str, Any],
) -> Dict[str, Any]:
    """Summarize session to minimal fields. No chat_history, debug_traces, etc."""
    if not session or not isinstance(session, dict):
        return {'active_scene_id': '', 'response_mode': 'standard', 'turn_counter': 0}

    visited = session.get('visited_scene_ids') or []
    visited_count = len(visited) if isinstance(visited, list) else 0
    interaction_ctx = session.get('interaction_context') or {}
    if not isinstance(interaction_ctx, dict):
        interaction_ctx = {}

    active_target = interaction_ctx.get('active_interaction_target_id')
    active_kind = interaction_ctx.get('active_interaction_kind')
    interaction_mode = interaction_ctx.get('interaction_mode')
    engagement_level = interaction_ctx.get('engagement_level')
    convo_privacy = interaction_ctx.get('conversation_privacy')
    position_ctx = interaction_ctx.get('player_position_context')

    return {
        'active_scene_id': str(session.get('active_scene_id', '') or ''),
        'response_mode': str(session.get('response_mode', 'standard') or 'standard'),
        'turn_counter': int(session.get('turn_counter', 0) or 0),
        'visited_scene_count': visited_count,
        'active_interaction_target_id': str(active_target).strip() if isinstance(active_target, str) and active_target.strip() else None,
        'active_interaction_target_name': _resolve_active_interaction_target_name(session, world, public_scene),
        'active_interaction_kind': str(active_kind).strip() if isinstance(active_kind, str) and active_kind.strip() else None,
        'interaction_mode': str(interaction_mode).strip() if isinstance(interaction_mode, str) and interaction_mode.strip() else 'none',
        'engagement_level': str(engagement_level).strip() if isinstance(engagement_level, str) and engagement_level.strip() else 'none',
        'conversation_privacy': str(convo_privacy).strip() if isinstance(convo_privacy, str) and convo_privacy.strip() else None,
        'player_position_context': str(position_ctx).strip() if isinstance(position_ctx, str) and position_ctx.strip() else None,
    }


def _compress_recent_log(recent_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Trim log entries to player input + short GM snippet. Take last N only."""
    if not recent_log or not isinstance(recent_log, list):
        return []

    trimmed: List[Dict[str, Any]] = []
    for entry in recent_log[-MAX_RECENT_LOG:]:
        if not isinstance(entry, dict):
            continue
        log_meta = entry.get('log_meta') or {}
        player_input = str(log_meta.get('player_input', '') or entry.get('request', {}).get('chat', '') or '')[:300]
        gm_output = entry.get('gm_output') or {}
        gm_text = gm_output.get('player_facing_text', '') if isinstance(gm_output, dict) else ''
        if isinstance(gm_text, str):
            gm_snippet = gm_text[:MAX_LOG_ENTRY_SNIPPET]
        else:
            gm_snippet = ''
        trimmed.append({'player_input': player_input, 'gm_snippet': gm_snippet})
    return trimmed


def _compress_combat(combat: Dict[str, Any]) -> Dict[str, Any] | None:
    """Include combat only when active; otherwise minimal/null."""
    if not combat or not isinstance(combat, dict):
        return None
    if not combat.get('in_combat'):
        return {'in_combat': False}
    return combat


def _compress_scene_runtime(runtime: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only essential runtime fields to avoid bloat."""
    if not runtime or not isinstance(runtime, dict):
        return {}
    recent_contextual_leads: List[Dict[str, Any]] = []
    raw_leads = runtime.get("recent_contextual_leads")
    if isinstance(raw_leads, list):
        for item in raw_leads[-MAX_RECENT_CONTEXTUAL_LEADS:]:
            if not isinstance(item, dict):
                continue
            subject = str(item.get("subject") or "").strip()
            key = str(item.get("key") or "").strip()
            if not subject or not key:
                continue
            recent_contextual_leads.append(
                {
                    "key": key,
                    "kind": str(item.get("kind") or "").strip(),
                    "subject": subject,
                    "position": str(item.get("position") or "").strip(),
                    "named": bool(item.get("named")),
                    "mentions": int(item.get("mentions", 1) or 1),
                    "last_turn": int(item.get("last_turn", 0) or 0),
                }
            )
    return {
        'discovered_clues': list(runtime.get('discovered_clues', []) or [])[:20],
        'pending_leads': list(runtime.get('pending_leads', []) or []),
        'recent_contextual_leads': recent_contextual_leads,
        'repeated_action_count': runtime.get('repeated_action_count', 0) or 0,
        'last_exploration_action_key': runtime.get('last_exploration_action_key'),
        'momentum_exchanges_since': int(runtime.get('momentum_exchanges_since', 0) or 0),
        'momentum_next_due_in': int(runtime.get('momentum_next_due_in', 2) or 2),
        'momentum_last_kind': runtime.get('momentum_last_kind'),
    }


def derive_narration_obligations(
    session_view: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    intent: Dict[str, Any] | None,
    recent_log_for_prompt: List[Dict[str, Any]] | None,
    scene_runtime: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Derive compact, engine-owned narration obligations for this turn."""
    turn_counter = int(session_view.get('turn_counter', 0) or 0)
    visited_scene_count = int(session_view.get('visited_scene_count', 0) or 0)
    recent_turns = len(recent_log_for_prompt or [])
    is_opening_scene = (
        turn_counter <= 1
        or (turn_counter == 0 and visited_scene_count <= 1 and recent_turns == 0)
    )

    res = resolution if isinstance(resolution, dict) else {}
    res_kind = str(res.get('kind') or '').strip().lower()
    state_changes = res.get("state_changes") if isinstance(res.get("state_changes"), dict) else {}
    scene_transition_occurred = bool(res.get("resolved_transition")) or bool(state_changes.get("scene_transition_occurred"))
    arrived_at_scene = bool(state_changes.get("arrived_at_scene"))
    new_scene_context_available = bool(state_changes.get("new_scene_context_available"))
    must_advance_scene = bool(scene_transition_occurred or arrived_at_scene or new_scene_context_available)

    active_target_id = str(session_view.get('active_interaction_target_id') or '').strip()
    active_kind = str(session_view.get('active_interaction_kind') or '').strip().lower()
    interaction_mode = str(session_view.get('interaction_mode') or '').strip().lower()
    has_active_target = bool(active_target_id)
    should_answer_active_npc = has_active_target and (
        interaction_mode == 'social'
        or active_kind in SOCIAL_REPLY_KINDS
        or active_kind == 'social'
    )

    labels = intent.get('labels') if isinstance(intent, dict) and isinstance(intent.get('labels'), list) else []
    labels_low = {str(label).strip().lower() for label in labels if isinstance(label, str) and label.strip()}
    has_social_resolution = isinstance(res.get('social'), dict) or res_kind in SOCIAL_REPLY_KINDS
    social_payload = res.get('social') if isinstance(res.get('social'), dict) else {}
    explicit_reply_expected = social_payload.get('npc_reply_expected') if isinstance(social_payload.get('npc_reply_expected'), bool) else None
    explicit_reply_kind_raw = str(social_payload.get('reply_kind') or '').strip().lower()
    explicit_reply_kind = explicit_reply_kind_raw if explicit_reply_kind_raw in NPC_REPLY_KIND_VALUES else None

    has_pending_check_prompt = bool(
        res.get('requires_check')
        and not isinstance(res.get('skill_check'), dict)
        and isinstance(res.get('check_request'), dict)
    )
    active_npc_reply_expected_fallback = has_active_target and (
        has_social_resolution
        or 'social_probe' in labels_low
    )
    active_npc_reply_expected = (
        False
        if has_pending_check_prompt
        else (explicit_reply_expected if explicit_reply_expected is not None else active_npc_reply_expected_fallback)
    )
    active_npc_reply_kind = explicit_reply_kind
    if active_npc_reply_expected and active_npc_reply_kind is None:
        if res_kind in {'persuade', 'intimidate', 'deceive', 'barter', 'recruit'}:
            active_npc_reply_kind = 'reaction'
        elif res_kind in {'question', 'social_probe'}:
            active_npc_reply_kind = 'answer'
        else:
            active_npc_reply_kind = 'reaction'
    if not active_npc_reply_expected:
        active_npc_reply_kind = None

    rt = scene_runtime if isinstance(scene_runtime, dict) else {}
    exchanges_since = int(rt.get("momentum_exchanges_since", 0) or 0)
    next_due_in = int(rt.get("momentum_next_due_in", 2) or 2)
    if next_due_in not in (2, 3):
        next_due_in = 2
    # If last momentum was 1 exchange ago and next_due_in=2, momentum is due now.
    # This ensures a strict "every 2–3 exchanges" cadence with a hard ceiling of 3.
    due_threshold = (next_due_in - 1)
    if due_threshold < 1:
        due_threshold = 1
    if due_threshold > 2:
        due_threshold = 2
    scene_momentum_due = exchanges_since >= due_threshold

    return {
        'is_opening_scene': bool(is_opening_scene),
        'must_advance_scene': bool(must_advance_scene),
        'should_answer_active_npc': bool(should_answer_active_npc),
        'avoid_input_echo': True,
        'avoid_player_action_restatement': True,
        'prefer_structured_turn_summary': True,
        'active_npc_reply_expected': bool(active_npc_reply_expected),
        'active_npc_reply_kind': active_npc_reply_kind,
        'scene_momentum_due': bool(scene_momentum_due),
        'scene_momentum_exchanges_since': exchanges_since,
        'scene_momentum_next_due_in': next_due_in,
    }


def _build_turn_summary(
    user_text: str,
    resolution: Dict[str, Any] | None,
    intent: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Build a compact, structured summary of this turn for narration anchoring."""
    res = resolution if isinstance(resolution, dict) else {}
    res_kind = str(res.get('kind') or '').strip()
    res_label = str(res.get('label') or '').strip()
    res_action_id = str(res.get('action_id') or '').strip()
    res_prompt = str(res.get('prompt') or '').strip()

    labels = intent.get('labels') if isinstance(intent, dict) and isinstance(intent.get('labels'), list) else []
    labels = [str(label).strip() for label in labels if isinstance(label, str) and str(label).strip()]

    if res_kind:
        descriptor = res_label or res_kind.replace('_', ' ')
    elif labels:
        descriptor = labels[0].replace('_', ' ')
    else:
        descriptor = 'general_action'

    return {
        'action_descriptor': descriptor,
        'resolution_kind': res_kind or None,
        'action_id': res_action_id or None,
        'resolved_prompt': res_prompt or None,
        'intent_labels': labels,
        'raw_player_input': str(user_text or ''),
        'raw_player_input_usage': (
            'Retain for exact wording and disambiguation only. '
            'Prefer action_descriptor + resolution_kind + mechanical_resolution for narration framing.'
        ),
    }


def build_narration_context(
    campaign: Dict[str, Any],
    world: Dict[str, Any],
    session: Dict[str, Any],
    character: Dict[str, Any],
    scene: Dict[str, Any],
    combat: Dict[str, Any],
    recent_log: List[Dict[str, Any]],
    user_text: str,
    resolution: Dict[str, Any] | None,
    scene_runtime: Dict[str, Any] | None,
    *,
    public_scene: Dict[str, Any],
    discoverable_clues: List[str],
    gm_only_hidden_facts: List[str],
    gm_only_discoverable_locked: List[str],
    discovered_clue_records: List[Dict[str, Any]],
    undiscovered_clue_records: List[Dict[str, Any]],
    pending_leads: List[Any],
    intent: Dict[str, Any],
    world_state_view: Dict[str, Any],
    mode_instruction: str,
    recent_log_for_prompt: List[Dict[str, Any]],
    uncertainty_hint: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a compressed narration context payload for GPT.

    Caller must precompute scene layers (public_scene, clues, hidden, etc.)
    and pass them in. This avoids duplicating _scene_layers logic and ensures
    hidden facts stay in gm_only only.

    Returns a dict suitable for JSON serialization as the user message content.
    """
    runtime = _compress_scene_runtime(scene_runtime or {})
    session_view = _compress_session(session, world, public_scene)
    narration_obligations = derive_narration_obligations(
        session_view=session_view,
        resolution=resolution,
        intent=intent,
        recent_log_for_prompt=recent_log_for_prompt,
        scene_runtime=runtime,
    )
    response_policy = build_response_policy(narration_obligations=narration_obligations)
    res = resolution if isinstance(resolution, dict) else {}
    state_changes = res.get("state_changes") if isinstance(res.get("state_changes"), dict) else {}
    scene_advancement = {
        "scene_transition_occurred": bool(res.get("resolved_transition")) or bool(state_changes.get("scene_transition_occurred")),
        "arrived_at_scene": bool(state_changes.get("arrived_at_scene")),
        "new_scene_context_available": bool(state_changes.get("new_scene_context_available")),
    }
    has_scene_change_context = any(bool(v) for v in scene_advancement.values())
    interaction_continuity = {
        'active_interaction_target_id': session_view.get('active_interaction_target_id'),
        'active_interaction_target_name': session_view.get('active_interaction_target_name'),
        'active_interaction_kind': session_view.get('active_interaction_kind'),
        'interaction_mode': session_view.get('interaction_mode'),
        'engagement_level': session_view.get('engagement_level'),
        'conversation_privacy': session_view.get('conversation_privacy'),
        'player_position_context': session_view.get('player_position_context'),
    }
    has_active_interlocutor = bool(str(interaction_continuity.get('active_interaction_target_id') or '').strip())

    clue_records_all: List[Dict[str, Any]] = list(discovered_clue_records) + list(undiscovered_clue_records)
    clue_visibility = {
        'implicit': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'implicit'],
        'explicit': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'explicit'],
        'actionable': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'actionable'],
    }

    instructions: List[str] = (
        [
            'Prioritize the active conversation over general scene recap.',
            'Do not fall back to base scene description unless the location materially changes, a new threat emerges, the player explicitly surveys the environment, or the scene needs a transition beat.',
        ]
        if has_active_interlocutor
        else []
    ) + [
        RULE_PRIORITY_COMPACT_INSTRUCTION,
        'Always answer the player. Prefer partial truth over refusal. Never output meta explanations.',
        NO_VALIDATOR_VOICE_RULE,
        'Follow response_policy.rule_priority_order strictly. Higher-priority rules override later ones.',
        'Treat response_policy.no_validator_voice as a hard narration-lane rule for standard narration.',
        (
            "SCENE MOMENTUM RULE (HARD RULE): Every 2–3 exchanges, you MUST introduce exactly one of: "
            "new_information, new_actor_entering, environmental_change, time_pressure, consequence_or_opportunity. "
            "When you do, include exactly one tag in tags: "
            "scene_momentum:<kind> where kind is one of those five identifiers. "
            "If narration_obligations.scene_momentum_due is true, this turn MUST include a momentum beat and MUST include that tag."
        ),
        'Use campaign and world state to keep political and strategic continuity.',
        'Avoid generic dramatic filler and repeated warning phrases. Make NPC replies specific to the speaker and current situation.',
        'Forbidden generic phrases are disallowed: "In this city...", "Times are tough...", "Trust is hard to come by...", "You\'ll need to prove yourself..." — rewrite into specific names/locations/events.',
        'QUESTION RESOLUTION RULE (HARD RULE): Every direct player question MUST be answered explicitly before any additional dialogue. Structure: (1) Direct answer (first sentence), (2) Optional elaboration, (3) Optional hook. The GM/NPC MUST NOT deflect, generalize, or ask a new question before answering.',
        'If certainty is incomplete, classify the uncertainty with response_policy.uncertainty.categories and compose it from response_policy.uncertainty.answer_shape: known_edge, unknown_edge, next_lead.',
        'Ground uncertainty with response_policy.uncertainty.context_inputs: uncertainty_hint.turn_context, uncertainty_hint.speaker, and uncertainty_hint.scene_snapshot.',
        'If uncertainty_hint.speaker.role is npc, keep the reply attributable to that NPC and limited to what they could plausibly know, hear, point to, or direct the player toward.',
        'If there is no active NPC speaker, keep uncertainty in diegetic narrator voice but anchor it to visible scene circumstances rather than generic omniscient wording.',
        'Frame uncertainty as world-facing limits only: who knows, what can be seen, what distance, darkness, rumor, missing witnesses, or incomplete clues prevent right now.',
        'Vary sentence count and cadence naturally; do not stamp the same three-sentence rhythm onto every uncertain answer.',
        'If no strong next lead exists, choose the strongest visible handle already in scene rather than giving generic investigative advice.',
        'PERCEPTION / INTENT ADJUDICATION RULE (HARD RULE): When the player asks for behavioral insight (e.g., nervous, lying, controlled), choose ONE dominant state (not mixed), give 1–2 concrete observable tells, and optionally map to a skill interpretation (Sense Motive, etc.). Failure: "mix of"/"seems like both" or pure emotional summary with no cues.',
        'If the player meaningfully moves to a new location, you may provide a new_scene_draft and/or activate_scene_id.',
        'If the player meaningfully changes the world, you may provide world_updates.',
        'If the player text implies a clear mechanical action, suggested_action may be filled for UI assistance, but narration remains primary.',
        'When interaction_continuity has an active target, treat that NPC as the default conversational counterpart.',
        'Non-addressed NPCs should not casually interject; if they interrupt, present it as a notable event with scene justification.',
        'If conversation_privacy or player_position_context implies private exchange (for example lowered_voice), reduce casual eavesdropping/interjection unless scene facts justify otherwise.',
        'Follow authoritative engine state for who is present, player positioning, scene transitions, and check outcomes; narrate outcomes without inventing structured results.',
        'Treat player input as an action declaration: default to third-person phrasing and preserve the user\'s expression format instead of rewriting it.',
        'Quoted in-character dialogue is valid inside an action declaration (for example: Galinor says, "Keep your voice down."); do not treat the quote alone as the entire action when surrounding action context exists.',
        'Follow narration_obligations as output requirements only: they shape wording and focus, but never grant authority to mutate state or decide mechanics.',
        'If narration_obligations.is_opening_scene is true, establish immediate environment plus actionable social/world hooks the player can engage now.',
        'If narration_obligations.must_advance_scene is true, do not stop at movement text alone; narrate arrival, changed state, and at least one concrete opportunity or pressure in the destination context.',
        'If narration_obligations.active_npc_reply_expected is true, complete the active NPC\'s substantive in-turn reply now unless a pending engine check prompt already takes precedence, or authoritative state indicates refusal/evasion/interruption/inability.',
        'If narration_obligations.should_answer_active_npc is true, prioritize the active interlocutor\'s reply and the immediate exchange over general scene recap.',
        'Use narration_obligations.active_npc_reply_kind as a compact reply-shape hint (answer, explanation, reaction, refusal).',
        'If narration_obligations.active_npc_reply_kind is refusal, make it substantive (clear boundary, brief reason, redirect, or consequence) rather than empty stalling.',
        'If the player asks a direct question, answer concretely (name, place, fact, or direction); if certainty is incomplete, provide the best grounded partial answer and state uncertainty in-character through witnesses, conditions, rumor, access, or incomplete observation; do not repeat prior information.',
        'NPC response contract: when an NPC is asked a question, include at least one of: (a) a specific person/place/faction, (b) a concrete next step the player can take, (c) directly usable info (time/location/condition/requirement). If the NPC lacks full information, give partial specifics or direct the player to a concrete source.',
        'When answering a player question, give a direct answer first. Do not replace the answer with narrative description.',
        'Use turn_summary and mechanical_resolution as primary narration anchors; treat player_input as supporting evidence for disambiguation, not as the sentence structure to mirror.',
        "Do not restate or paraphrase the player's input. Always continue forward with new information.",
        "Do not repeat the player's spoken line. React to it instead.",
        'If narration_obligations.avoid_input_echo or narration_obligations.avoid_player_action_restatement is true, do not restate or lightly paraphrase player_input (for example, "Galinor asks...") unless wording is required to disambiguate the target, quote, or procedural request.',
        'If narration_obligations.prefer_structured_turn_summary is true, continue from resolved world state, scene advancement, and NPC intent/reply obligations rather than narrating that "the player asks/says X."',
        'Keep the narration to 1-4 concise paragraphs.',
        mode_instruction,
    ]
    if has_scene_change_context:
        instructions.append(
            'When transitioning scenes, include a brief bridge from the prior location before describing the new one.'
        )

    recent_log_compact = _compress_recent_log(recent_log_for_prompt) if recent_log_for_prompt else []
    follow_up_pressure = _compute_follow_up_pressure(recent_log_compact, user_text)
    if follow_up_pressure:
        instructions = list(instructions) + [
            (
                "FOLLOW-UP ESCALATION RULE (HARD RULE): The player is pressing the same topic again (see follow_up_pressure). "
                "Do NOT recycle the same core lead from the previous answer. Escalate by doing AT LEAST TWO of the following: "
                "(1) add one new concrete detail (time, place, condition, count, or observable), "
                "(2) introduce a named person/place/faction/witness tied to the topic (with an in-world source), "
                "(3) narrow the boundary of the unknown (what is ruled out; what is now most likely; what would confirm it), "
                "(4) produce a more actionable immediate next step that uses the new detail. "
                "Preserve uncertainty, but uncertainty must evolve. Preserve speaker grounding."
            ),
            "Allowed repetition: one short anchor clause for continuity. Not allowed: re-stating the same underlying lead as the whole answer.",
        ]

    payload: Dict[str, Any] = {
        'instructions': instructions,
        'interaction_continuity': interaction_continuity,
        'turn_summary': _build_turn_summary(user_text, resolution, intent),
        'recent_log': recent_log_compact,
        'player_input': str(user_text or ''),
        'follow_up_pressure': follow_up_pressure,
        'response_policy': response_policy,
        'uncertainty_hint': uncertainty_hint,
        'narration_obligations': narration_obligations,
        'mechanical_resolution': resolution,
        'scene_advancement': scene_advancement,
        'session': session_view,
        'character': {
            'name': str(character.get('name', '') or ''),
            'role': str(campaign.get('character_role', '') or ''),
            'hp': character.get('hp'),
            'ac': character.get('ac'),
            'conditions': character.get('conditions', []),
            'attacks': character.get('attacks', []),
            'spells': character.get('spells', {}),
            'skills': character.get('skills', {}),
        }
        if character and isinstance(character, dict)
        else {'name': '', 'role': '', 'hp': {}, 'ac': {}, 'conditions': [], 'attacks': [], 'spells': {}, 'skills': {}},
        'combat': _compress_combat(combat),
        'world_state': world_state_view,
        'world': _compress_world(world),
        'campaign': _compress_campaign(campaign),
        'scene': {
            'public': public_scene,
            'discoverable_clues': discoverable_clues,
            'gm_only': {
                'hidden_facts': gm_only_hidden_facts,
                'discoverable_clues_locked': gm_only_discoverable_locked,
            },
            'clue_records': {'discovered': discovered_clue_records, 'undiscovered': undiscovered_clue_records},
            'visible_clues': discovered_clue_records,
            'discovered_clues': discovered_clue_records,
            'clue_visibility': clue_visibility,
            'pending_leads': pending_leads,
            'runtime': runtime,
            'intent': intent,
            'layering_rules': {
                'visible_facts': 'Narrate freely.',
                'discoverable_clues': 'Reveal only when player investigates/searches/questions/observes closely.',
                'hidden_facts': 'Never reveal directly; use only for implications, NPC behavior, atmosphere, indirect clues.',
            },
        },
        'player_expression_contract': {
            'default_action_style': 'third_person',
            'quoted_speech_allowed': True,
            'preserve_user_expression_format': True,
            'example': 'Galinor asks, "What changed at the north gate?" while examining the notice board.',
        },
    }
    return payload
