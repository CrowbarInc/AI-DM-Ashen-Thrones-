"""Persistence layer: campaign/world vs session separation.

Campaign templates (scenes, locations, clues, NPCs, summaries) are stored separately
from session state. Session holds only playthrough state and is safe to reset.

Campaign/world layer (immutable during session reset):
- campaign.json: metadata, gm_guidance
- world.json: settlements, factions, projects, event_log, world_state
- data/scenes/<id>.json: scene templates (location, visible_facts, discoverable_clues,
  hidden_facts, exits, enemies)

Session layer (playthrough state only):
- session.json: active_scene_id, visited_scene_ids, scene_runtime (discovered_clues,
  pending_leads, etc.), clocks, turn_counter, response_mode, last_action_debug

Scene activation: load_active_scene() reads active_scene_id from session, then loads
scene content from data/scenes/<id>.json (disk), never from session.

Persistence layer. Campaign/world data and session playthrough state are strictly separated.

Campaign data (immutable during session reset):
  - campaign.json: metadata (title, premise, gm_guidance, etc.)
  - world.json: settlements, factions, assets, projects, event_log, world_state
  - data/scenes/*.json: scene templates (location, summary, visible_facts, discoverable_clues,
    hidden_facts, exits, enemies) — loaded via load_scene(), never stored in session

Session playthrough state only (resettable):
  - active_scene_id, visited_scene_ids, turn_counter, response_mode
  - clocks (suspicion, unrest, time_pressure, etc.)
  - scene_runtime: per-scene playthrough (discovered_clues, pending_leads, repeated_action_count)
  - last_action_debug

Scene activation reads scene content from data/scenes/{id}.json, not from session.

Persistence layer. Data separation:

Campaign/world (immutable during session reset):
  - campaign.json: premise, tone, gm_guidance, etc.
  - world.json: settlements, factions, assets, projects, event_log, world_state
  - data/scenes/*.json: scene templates (location, summary, visible_facts,
    discoverable_clues, hidden_facts, exits, enemies)

Session (playthrough state only):
  - session.json: active_scene_id, visited_scene_ids, turn_counter, clocks,
    scene_runtime (discovered_clues, pending_leads, repeated_action_count, etc.)
  - Session does NOT store scenes, locations, npcs, or clue templates.
  - load_active_scene() reads scene_id from session, loads scene from disk.

Persistence layer: campaign vs session data separation.

Campaign/world data (immutable during session reset):
  - campaign.json: title, premise, gm_guidance, etc.
  - world.json: settlements, factions, projects, event_log, world_state
  - data/scenes/*.json: scene templates (location, visible_facts, discoverable_clues,
    hidden_facts, exits, enemies)

Session data (playthrough state only; safe to reset):
  - session.json: active_scene_id, visited_scene_ids, turn_counter, response_mode,
    clocks, scene_runtime (discovered_clues per scene, pending_leads, etc.)

Scene activation: uses session.active_scene_id then load_scene() from disk;
scenes are never stored in session.

Persistence layer. Campaign/world data separate from session playthrough state.

Campaign data (immutable during session reset):
  - campaign.json: title, premise, gm_guidance, etc.
  - world.json: settlements, factions, projects, event_log, world_state
  - data/scenes/*.json: scene templates (location, summary, visible_facts,
    discoverable_clues, hidden_facts, exits, enemies)

Session (playthrough state only):
  - active_scene_id, visited_scene_ids, turn_counter, response_mode, clocks
  - scene_runtime[scene_id]: discovered_clues, pending_leads, repeated_action_count
  - Session never stores scenes, locations, npcs, or clue templates.
"""
from __future__ import annotations
from pathlib import Path
import copy
import hashlib
import json
import secrets
from typing import Any, Dict, List, Optional

from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.utils import utc_iso_now
from game.validation import validate_all_scenes

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
SCENES_DIR = DATA_DIR / 'scenes'

CHARACTER_PATH = DATA_DIR / 'character.json'
CAMPAIGN_PATH = DATA_DIR / 'campaign.json'
SESSION_PATH = DATA_DIR / 'session.json'
WORLD_PATH = DATA_DIR / 'world.json'
COMBAT_PATH = DATA_DIR / 'combat.json'
CONDITIONS_PATH = DATA_DIR / 'conditions.json'
SESSION_LOG_PATH = DATA_DIR / 'session_log.jsonl'
SNAPSHOTS_DIR = DATA_DIR / 'snapshots'
SNAPSHOT_VERSION = 1


def _load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, indent=2), encoding='utf-8')
        return copy.deepcopy(default)
    text = path.read_text(encoding='utf-8').strip()
    if not text:
        raise ValueError(f'JSON file is empty: {path}')
    return json.loads(text)


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


def scene_path(scene_id: str) -> Path:
    return SCENES_DIR / f'{scene_id}.json'


def ensure_data_files_exist() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    load_campaign()
    load_character()
    load_session()
    load_world()
    load_combat()
    load_conditions()
    # seed base scenes
    for sid in ['frontier_gate', 'market_quarter']:
        path = scene_path(sid)
        if not path.exists():
            _save_json(path, default_scene(sid))
    # validate all scenes before serving
    validate_all_scenes(SCENES_DIR, list_scene_ids)
    # ensure active scene exists
    load_active_scene()
    if not SESSION_LOG_PATH.exists():
        SESSION_LOG_PATH.write_text('', encoding='utf-8')


def load_campaign() -> Dict[str, Any]:
    return _load_json(CAMPAIGN_PATH, default_campaign())


def save_campaign(data: Dict[str, Any]) -> None:
    existing = load_campaign()
    existing.update(data)
    _save_json(CAMPAIGN_PATH, existing)


def load_character() -> Dict[str, Any]:
    return _load_json(CHARACTER_PATH, default_character())


def save_character(data: Dict[str, Any]) -> None:
    _save_json(CHARACTER_PATH, data)


def load_session() -> Dict[str, Any]:
    return _load_json(SESSION_PATH, default_session())


def save_session(data: Dict[str, Any]) -> None:
    """Persist session to disk. Sets last_saved_at timestamp for save summary."""
    data = dict(data)
    data['last_saved_at'] = utc_iso_now()
    _save_json(SESSION_PATH, data)


def load_world() -> Dict[str, Any]:
    return _load_json(WORLD_PATH, default_world())


def save_world(data: Dict[str, Any]) -> None:
    _save_json(WORLD_PATH, data)


def load_combat() -> Dict[str, Any]:
    return _load_json(COMBAT_PATH, default_combat())


def save_combat(data: Dict[str, Any]) -> None:
    _save_json(COMBAT_PATH, data)


def load_conditions() -> Dict[str, Any]:
    return _load_json(CONDITIONS_PATH, default_conditions())


def load_scene(scene_id: str) -> Dict[str, Any]:
    scene = _load_json(scene_path(scene_id), default_scene(scene_id))
    # Backward-compatible normalization: older scenes may not have discoverable_clues.
    scene.setdefault('scene', {})
    scene['scene'].setdefault('visible_facts', [])
    scene['scene'].setdefault('discoverable_clues', [])
    scene['scene'].setdefault('hidden_facts', [])
    # Optional structured actions; legacy scenes may omit or use suggested_actions
    scene['scene'].setdefault('actions', [])
    # Interactables (id, type, reveals_clue?, leads_to?); default empty for scenes without them
    scene['scene'].setdefault('interactables', [])
    # Optional objects (id, label?, type?) for auto-generated affordances
    scene['scene'].setdefault('objects', [])
    return scene


def save_scene(scene: Dict[str, Any]) -> None:
    _save_json(scene_path(scene['scene']['id']), scene)


def load_active_scene() -> Dict[str, Any]:
    session = load_session()
    return load_scene(session['active_scene_id'])


def activate_scene(scene_id: str) -> Dict[str, Any]:
    session = load_session()
    session['active_scene_id'] = scene_id
    if scene_id not in session['visited_scene_ids']:
        session['visited_scene_ids'].append(scene_id)
    save_session(session)
    return session


def list_scene_ids() -> List[str]:
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    return sorted([p.stem for p in SCENES_DIR.glob('*.json')])


def is_known_scene_id(scene_id: str) -> bool:
    """Return True if a scene file exists for this ID; used to validate activate_scene_id."""
    if not scene_id or not isinstance(scene_id, str):
        return False
    return scene_id.strip() in list_scene_ids()


def append_log(entry: Dict[str, Any]) -> None:
    with SESSION_LOG_PATH.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def load_log() -> List[Dict[str, Any]]:
    if not SESSION_LOG_PATH.exists():
        return []
    entries = []
    for line in SESSION_LOG_PATH.read_text(encoding='utf-8').splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def clear_log() -> None:
    SESSION_LOG_PATH.write_text('', encoding='utf-8')


def _ensure_scene_runtime_root(session: Dict[str, Any]) -> Dict[str, Any]:
    if 'scene_runtime' not in session or not isinstance(session['scene_runtime'], dict):
        session['scene_runtime'] = {}
    return session['scene_runtime']


def get_interaction_context(session: Dict[str, Any]) -> Dict[str, Any]:
    """Return mutable interaction context, initializing deterministic default keys."""
    ctx = session.get("interaction_context")
    if not isinstance(ctx, dict):
        ctx = {}
        session["interaction_context"] = ctx
    for key in (
        "active_interaction_target_id",
        "active_interaction_kind",
        "interaction_mode",
        "engagement_level",
        "conversation_privacy",
        "player_position_context",
    ):
        if key not in ctx:
            if key in ("interaction_mode", "engagement_level"):
                ctx[key] = "none"
            else:
                ctx[key] = None
        elif ctx[key] is not None:
            ctx[key] = str(ctx[key]).strip() or None
    if ctx.get("interaction_mode") is None:
        ctx["interaction_mode"] = "none"
    if ctx.get("engagement_level") is None:
        ctx["engagement_level"] = "none"
    return ctx


def clear_interaction_context(session: Dict[str, Any]) -> Dict[str, Any]:
    """Backward-compatible clear helper; delegates to owner API."""
    from game.interaction_context import clear_for_scene_change

    return clear_for_scene_change(session)


def get_scene_runtime(session: Dict[str, Any], scene_id: str) -> Dict[str, Any]:
    """Return mutable runtime dict for a given scene, initializing if needed."""
    root = _ensure_scene_runtime_root(session)
    scene_rt = root.get(scene_id)
    if not isinstance(scene_rt, dict):
        scene_rt = {}
        root[scene_id] = scene_rt
    scene_rt.setdefault('discovered_clues', [])
    scene_rt.setdefault('discovered_clue_ids', [])  # Structured clue ids for world progression
    scene_rt.setdefault('pending_leads', [])
    scene_rt.setdefault('revealed_hidden_facts', [])
    scene_rt.setdefault('suspicion_flags', [])
    # Discovery memory: per-target search state
    scene_rt.setdefault('searched_targets', [])  # target ids (interactable id or action_id) already investigated
    scene_rt.setdefault('resolved_interactables', [])  # interactable ids that yielded discover_clue (one-time)
    # Anti-stall: repeated same exploration action in same scene
    scene_rt.setdefault('last_exploration_action_key', None)
    scene_rt.setdefault('repeated_action_count', 0)
    scene_rt.setdefault('last_resolution_kind', None)
    scene_rt.setdefault('last_description_hash', None)
    scene_rt.setdefault('consumed_action_ids', [])
    # Scene momentum (anti-stall) tracking:
    # - momentum_exchanges_since: number of completed exchanges since last momentum beat
    # - momentum_next_due_in: next window size (2 or 3) for requiring a momentum beat
    # - momentum_last_kind: last momentum kind tag applied (debug/telemetry)
    scene_rt.setdefault('momentum_exchanges_since', 0)
    scene_rt.setdefault('momentum_next_due_in', 2)
    scene_rt.setdefault('momentum_last_kind', None)
    return scene_rt


SCENE_MOMENTUM_TAG_PREFIX = "scene_momentum:"
SCENE_MOMENTUM_KINDS: tuple[str, ...] = (
    "new_information",
    "new_actor_entering",
    "environmental_change",
    "time_pressure",
    "consequence_or_opportunity",
)


def update_scene_momentum_runtime(session: Dict[str, Any], scene_id: str, gm: Dict[str, Any]) -> Dict[str, Any]:
    """Update per-scene momentum counters based on GM output tags.

    Deterministic rule:
    - If the GM includes exactly one scene_momentum:<kind> tag, reset exchanges_since=0
      and toggle next_due_in between 2 and 3.
    - Otherwise, increment exchanges_since by 1.
    """
    rt = get_scene_runtime(session, scene_id)
    tags = gm.get("tags") if isinstance(gm, dict) else None
    tags_list = tags if isinstance(tags, list) else []
    found: list[str] = []
    for t in tags_list:
        if not isinstance(t, str):
            continue
        t = t.strip()
        if not t.startswith(SCENE_MOMENTUM_TAG_PREFIX):
            continue
        kind = t[len(SCENE_MOMENTUM_TAG_PREFIX):].strip()
        if kind in SCENE_MOMENTUM_KINDS and kind not in found:
            found.append(kind)

    if len(found) == 1:
        rt["momentum_exchanges_since"] = 0
        rt["momentum_last_kind"] = found[0]
        # Toggle 2 ↔ 3 to enforce a 2–3 beat cadence without randomness.
        prev = int(rt.get("momentum_next_due_in", 2) or 2)
        rt["momentum_next_due_in"] = 3 if prev == 2 else 2
        return rt

    rt["momentum_exchanges_since"] = int(rt.get("momentum_exchanges_since", 0) or 0) + 1
    return rt


def hash_text(text: str) -> str:
    """MD5 hash of text for detecting repeated narration."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


REPEATED_DESCRIPTION_SUMMARY = "You find nothing new beyond what you have already observed."


def apply_repeated_description_guard(
    gm: Dict[str, Any], session: Dict[str, Any], scene_id: str
) -> None:
    """If narration matches the last description for this scene, replace with short summary.
    Mutates gm in place. Updates last_description_hash when narration changes."""
    text = gm.get('player_facing_text')
    if not isinstance(text, str) or not text.strip():
        return
    new_hash = hash_text(text)
    rt = get_scene_runtime(session, scene_id)
    last_hash = rt.get('last_description_hash')
    if last_hash is not None and new_hash == last_hash:
        gm['player_facing_text'] = REPEATED_DESCRIPTION_SUMMARY
    else:
        rt['last_description_hash'] = new_hash


def _add_unique_to_list(lst: List[str], value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if value in lst:
        return False
    lst.append(value)
    return True


def mark_clue_discovered(session: Dict[str, Any], scene_id: str, clue_text: str) -> bool:
    """Mark a clue as discovered; return True only if newly added."""
    rt = get_scene_runtime(session, scene_id)
    return _add_unique_to_list(rt['discovered_clues'], clue_text)


def add_pending_lead(session: Dict[str, Any], scene_id: str, lead: Dict[str, Any]) -> bool:
    """Add a pending lead from a discovered clue. Returns True if newly added. Lead shape: {clue_id, text, leads_to_scene?, leads_to_npc?, leads_to_rumor?}."""
    if not lead or not isinstance(lead, dict):
        return False
    clue_id = str(lead.get('clue_id', '')).strip()
    if not clue_id:
        return False
    rt = get_scene_runtime(session, scene_id)
    pending = rt.get('pending_leads') or []
    if not isinstance(pending, list):
        rt['pending_leads'] = []
        pending = []
    for p in pending:
        if isinstance(p, dict) and p.get('clue_id') == clue_id:
            return False
    clean = {k: v for k, v in lead.items() if v is not None and v != ''}
    rt['pending_leads'] = pending + [clean]
    return True


def mark_hidden_fact_revealed(session: Dict[str, Any], scene_id: str, hidden_text: str) -> bool:
    """Mark a hidden fact as explicitly revealed; return True only if newly added."""
    rt = get_scene_runtime(session, scene_id)
    return _add_unique_to_list(rt['revealed_hidden_facts'], hidden_text)


def mark_action_consumed(session: Dict[str, Any], scene_id: str, action_id: str) -> bool:
    """Mark an affordance as consumed (completed). Actions in consumed_action_ids are hidden from affordances.
    Returns True only if newly added."""
    if not action_id or not isinstance(action_id, str):
        return False
    action_id = action_id.strip()
    if not action_id:
        return False
    rt = get_scene_runtime(session, scene_id)
    consumed = rt.get('consumed_action_ids') or []
    if not isinstance(consumed, list):
        rt['consumed_action_ids'] = []
        consumed = []
    if action_id in consumed:
        return False
    consumed.append(action_id)
    rt['consumed_action_ids'] = consumed
    return True


def add_suspicion_flag(session: Dict[str, Any], scene_id: str, flag: str) -> bool:
    """Add a suspicion flag; return True only if newly added."""
    rt = get_scene_runtime(session, scene_id)
    return _add_unique_to_list(rt['suspicion_flags'], flag)


def is_target_searched(session: Dict[str, Any], scene_id: str, target_id: str) -> bool:
    """Return True if the target (interactable id or action_id) has been searched."""
    if not target_id or not isinstance(target_id, str):
        return False
    rt = get_scene_runtime(session, scene_id)
    searched = rt.get('searched_targets') or []
    return str(target_id).strip() in [str(x).strip() for x in searched if x]


def is_interactable_resolved(session: Dict[str, Any], scene_id: str, interactable_id: str) -> bool:
    """Return True if the interactable already yielded discover_clue (one-time exhausted)."""
    if not interactable_id or not isinstance(interactable_id, str):
        return False
    rt = get_scene_runtime(session, scene_id)
    resolved = rt.get('resolved_interactables') or []
    return str(interactable_id).strip() in [str(x).strip() for x in resolved if x]


def mark_target_searched(session: Dict[str, Any], scene_id: str, target_id: str) -> bool:
    """Mark a target as searched. Returns True only if newly added."""
    if not target_id or not isinstance(target_id, str):
        return False
    target_id = str(target_id).strip()
    if not target_id:
        return False
    rt = get_scene_runtime(session, scene_id)
    return _add_unique_to_list(rt['searched_targets'], target_id)


def mark_interactable_resolved(session: Dict[str, Any], scene_id: str, interactable_id: str) -> bool:
    """Mark an interactable as resolved (clue discovered). Returns True only if newly added."""
    if not interactable_id or not isinstance(interactable_id, str):
        return False
    interactable_id = str(interactable_id).strip()
    if not interactable_id:
        return False
    rt = get_scene_runtime(session, scene_id)
    added = _add_unique_to_list(rt['resolved_interactables'], interactable_id)
    if added:
        _add_unique_to_list(rt['searched_targets'], interactable_id)
    return added


def _ensure_npc_runtime_root(session: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure session has npc_runtime dict. Returns mutable npc_runtime."""
    if 'npc_runtime' not in session or not isinstance(session['npc_runtime'], dict):
        session['npc_runtime'] = {}
    return session['npc_runtime']


def get_npc_runtime(session: Dict[str, Any], npc_id: str) -> Dict[str, Any]:
    """Return mutable runtime dict for an NPC, initializing if needed.

    NPC runtime tracks: attitude, trust, fear, suspicion, known_topics, revealed_topics,
    last_interaction_turn. Lives in session.npc_runtime[npc_id].
    """
    root = _ensure_npc_runtime_root(session)
    npc_rt = root.get(npc_id)
    if not isinstance(npc_rt, dict):
        npc_rt = {}
        root[npc_id] = npc_rt
    npc_rt.setdefault('attitude', 0)
    npc_rt.setdefault('trust', 0)
    npc_rt.setdefault('fear', 0)
    npc_rt.setdefault('suspicion', 0)
    npc_rt.setdefault('known_topics', [])
    npc_rt.setdefault('revealed_topics', [])
    npc_rt.setdefault('last_interaction_turn', None)
    return npc_rt


def _ensure_world_state(world: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure world has world_state with flags, counters, clocks. Returns world_state dict."""
    if 'world_state' not in world or not isinstance(world['world_state'], dict):
        world['world_state'] = {'flags': {}, 'counters': {}, 'clocks': {}}
    ws = world['world_state']
    ws.setdefault('flags', {})
    ws.setdefault('counters', {})
    ws.setdefault('clocks', {})
    return ws


def get_world_flag(world: Dict[str, Any], key: str) -> Any:
    """Get the value of a world flag. Returns None if not set."""
    ws = _ensure_world_state(world)
    return ws['flags'].get(key)


def set_world_flag(world: Dict[str, Any], key: str, value: Any) -> None:
    """Set a world flag. Value must be JSON-serializable."""
    if not key or not isinstance(key, str):
        return
    ws = _ensure_world_state(world)
    ws['flags'][key] = value


def increment_world_counter(world: Dict[str, Any], key: str, amount: int = 1) -> int:
    """Increment a world counter and return the new value."""
    if not key or not isinstance(key, str):
        return 0
    ws = _ensure_world_state(world)
    current = int(ws['counters'].get(key, 0) or 0)
    new_val = current + int(amount)
    ws['counters'][key] = new_val
    return new_val


DEBUG_TRACE_MAX = 20


def append_debug_trace(session: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Append a debug trace and keep only the most recent DEBUG_TRACE_MAX traces."""
    if 'debug_traces' not in session or not isinstance(session['debug_traces'], list):
        session['debug_traces'] = []
    session['debug_traces'].append(trace)
    session['debug_traces'] = session['debug_traces'][-DEBUG_TRACE_MAX:]


def get_save_summary() -> Dict[str, Any]:
    """Return a summary of the persisted playthrough state for UI display.

    Reflects what is on disk (session, world, character, log). Playthrough state
    is auto-saved on every action/chat. Save buttons (Save Campaign, Save Scene)
    persist campaign metadata and scene templates only.
    """
    session = load_session()
    world = load_world()
    character = load_character()
    log_entries = load_log()

    # Aggregate discovered clues across all scene runtimes (discovered_clues only; ids overlap)
    discovered_total = 0
    rt = session.get('scene_runtime') or {}
    if isinstance(rt, dict):
        for scene_rt in rt.values():
            if isinstance(scene_rt, dict):
                discovered_total += len(scene_rt.get('discovered_clues') or [])

    ws = _ensure_world_state(world)
    flags_count = len(ws.get('flags') or {})
    counters_count = len(ws.get('counters') or {})
    world_clocks_count = len(ws.get('clocks') or {})

    player_name = (
        session.get('character_name')
        or (character.get('name') or '').strip()
        or 'You'
    )

    return {
        'saved_at': session.get('last_saved_at'),
        'active_scene_id': session.get('active_scene_id', ''),
        'chat_messages': len(log_entries),
        'discovered_clues': discovered_total,
        'world_flags_count': flags_count,
        'world_counters_count': counters_count,
        'world_clocks_count': world_clocks_count,
        'player_name': player_name,
        'save_data_exists': bool(
            session.get('last_saved_at')
            or session.get('turn_counter', 0) > 0
            or (isinstance(rt, dict) and len(rt) > 0)
            or len(session.get('visited_scene_ids', [])) > 1
        ),
    }


def advance_world_clock(world: Dict[str, Any], clock_name: str, amount: int = 1) -> int:
    """Advance a world clock by amount. Creates clock if missing (max=10). Returns new progress (clamped to max)."""
    if not clock_name or not isinstance(clock_name, str):
        return 0
    ws = _ensure_world_state(world)
    clocks = ws['clocks']
    entry = clocks.get(clock_name)
    if not isinstance(entry, dict):
        entry = {'progress': 0, 'max': 10}
        clocks[clock_name] = entry
    progress = int(entry.get('progress', 0) or 0)
    max_val = max(1, int(entry.get('max', 10) or 10))
    new_progress = min(max_val, progress + int(amount))
    entry['progress'] = new_progress
    entry['max'] = max_val
    return new_progress


# -----------------------------------------------------------------------------
# Snapshot / Save Slots
# -----------------------------------------------------------------------------
# Lightweight named save slots for playtesting and branching. Each snapshot
# captures session, world, combat, character, and log. Does not touch
# campaign or scene templates. Default persistence is unchanged.
# -----------------------------------------------------------------------------


def _snapshot_path(snapshot_id: str) -> Path:
    """Return path for a snapshot file. ID must be safe (alphanumeric, underscore, hyphen)."""
    safe = "".join(c for c in snapshot_id if c.isalnum() or c in "_-")
    if not safe:
        raise ValueError("Invalid snapshot id")
    return SNAPSHOTS_DIR / f"{safe}.json"


def create_snapshot(label: Optional[str] = None) -> Dict[str, Any]:
    """Create a snapshot of current runtime state. Returns snapshot meta (id, created_at, label)."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_id = f"{utc_iso_now().replace(':', '-').replace('.', '-')[:19]}_{secrets.token_hex(4)}"
    created_at = utc_iso_now()
    label_clean = (label or "").strip() or None

    session = load_session()
    world = load_world()
    combat = load_combat()
    character = load_character()
    log_entries = load_log()

    bundle: Dict[str, Any] = {
        "version": SNAPSHOT_VERSION,
        "created_at": created_at,
        "label": label_clean,
        "session": copy.deepcopy(session),
        "world": copy.deepcopy(world),
        "combat": copy.deepcopy(combat),
        "character": copy.deepcopy(character),
        "log_entries": copy.deepcopy(log_entries),
    }
    _save_json(_snapshot_path(snapshot_id), bundle)
    return {"id": snapshot_id, "created_at": created_at, "label": label_clean}


def list_snapshots() -> List[Dict[str, Any]]:
    """List all snapshots. Returns [{id, created_at, label}] sorted by created_at descending."""
    if not SNAPSHOTS_DIR.exists():
        return []
    result: List[Dict[str, Any]] = []
    for path in sorted(SNAPSHOTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                result.append({
                    "id": path.stem,
                    "created_at": data.get("created_at", ""),
                    "label": data.get("label"),
                })
        except (json.JSONDecodeError, OSError):
            continue
    return result


def load_snapshot(snapshot_id: str) -> Optional[Dict[str, Any]]:
    """Restore state from snapshot. Overwrites session, world, combat, character, log.
    Returns snapshot meta on success, None if not found."""
    path = _snapshot_path(snapshot_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None

    session = data.get("session")
    world = data.get("world")
    combat = data.get("combat")
    character = data.get("character")
    log_entries = data.get("log_entries")

    if not isinstance(session, dict):
        return None
    if not isinstance(world, dict):
        return None
    if not isinstance(combat, dict):
        return None
    if not isinstance(character, dict):
        return None
    if not isinstance(log_entries, list):
        log_entries = []

    session["last_saved_at"] = utc_iso_now()
    _save_json(SESSION_PATH, session)
    _save_json(WORLD_PATH, world)
    _save_json(COMBAT_PATH, combat)
    _save_json(CHARACTER_PATH, character)
    clear_log()
    for entry in log_entries:
        if isinstance(entry, dict):
            append_log(entry)

    return {"id": data.get("id", snapshot_id), "created_at": data.get("created_at"), "label": data.get("label")}
