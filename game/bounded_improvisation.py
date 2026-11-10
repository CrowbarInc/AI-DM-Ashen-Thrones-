"""Bounded improvisational authority for low-consequence DM invention.

This module owns the typed proposal lane for model-created incidental facts
and NPC claims. Accepted entries are runtime state, not authored world truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from typing import Any, Mapping


LEDGER_KEY = "bounded_improvisation"
LEDGER_VERSION = 1

IMPROVISATION_PROPOSAL_KEY = "improvisation_proposals"
IMPROVISATION_AUTHORITY_KEY = "bounded_improvisation_authority"

ACCEPTED_STATUSES = frozenset({"accepted", "promoted"})
INCIDENTAL_KIND = "incidental_fact"
NPC_CLAIM_KIND = "npc_claim"
CONSEQUENTIAL_KIND = "consequential_proposal"

ALLOWED_INCIDENTAL_CATEGORIES = frozenset(
    {
        "sensory_detail",
        "food_composition",
        "mundane_service_detail",
        "background_npc_detail",
        "mannerism",
        "local_color",
        "environmental_elaboration",
        "social_connective",
        "ordinary_personal_detail",
    }
)
ALLOWED_NPC_CLAIM_CATEGORIES = frozenset(
    {
        "rumor",
        "hearsay",
        "uncertain_claim",
        "speculation",
        "opinion",
        "social_connective",
    }
)
ALLOWED_EPISTEMIC_STATUSES = frozenset({"known", "grounded", "rumor", "hearsay", "uncertain", "speculative"})
LOW_CONSEQUENCE_LEVELS = frozenset({"none", "low", "incidental"})
PERMITTED_SCOPES = frozenset({"turn", "scene", "session"})

CONSEQUENTIAL_TERMS = re.compile(
    r"\b("
    r"secret|hidden|quest|clue|conspiracy|traitor|allegiance|faction|army|military|"
    r"passage|tunnel|vault|artifact|relic|curse|prophecy|murderer|monster|spy|cult|"
    r"king|duke|baron|captain|major|war|invasion|assassin|"
    r"bootprints?|footprints?|tracks?|broken twigs?|snapped branches?|watchtower|fork"
    r")\b",
    re.IGNORECASE,
)
MECHANICAL_TERMS = re.compile(
    r"\b("
    r"roll|dc|damage|hit points?|hp|"
    r"inventory|condition|spell slot|initiative|armor class|ac|success|failure"
    r")\b",
    re.IGNORECASE,
)
HIDDEN_INFO_TERMS = re.compile(r"\b(secretly|unknown to you|hidden motive|true motive|in truth|really works for)\b", re.IGNORECASE)


@dataclass(frozen=True)
class BoundedImprovisationDecision:
    proposal: dict[str, Any]
    accepted: bool
    reason_codes: list[str] = field(default_factory=list)
    entry: dict[str, Any] | None = None


def _clean_text(value: Any, *, limit: int = 500) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:limit]


def _clean_token(value: Any, *, default: str = "") -> str:
    if not isinstance(value, str):
        return default
    cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
    return cleaned or default


def _scene_id_from_scene(scene: Mapping[str, Any] | None, session: Mapping[str, Any] | None) -> str:
    if isinstance(scene, Mapping):
        inner = scene.get("scene")
        if isinstance(inner, Mapping):
            sid = str(inner.get("id") or "").strip()
            if sid:
                return sid
        sid = str(scene.get("id") or "").strip()
        if sid:
            return sid
    if isinstance(session, Mapping):
        return str(session.get("active_scene_id") or "").strip()
    return ""


def ensure_bounded_improvisation_ledger(session: dict[str, Any]) -> dict[str, Any]:
    ledger = session.get(LEDGER_KEY)
    if not isinstance(ledger, dict):
        ledger = {}
        session[LEDGER_KEY] = ledger
    ledger.setdefault("version", LEDGER_VERSION)
    if not isinstance(ledger.get("entries"), list):
        ledger["entries"] = []
    if not isinstance(ledger.get("rejected"), list):
        ledger["rejected"] = []
    return ledger


def _entry_id(kind: str, scene_id: str, content: str, speaker_id: str = "") -> str:
    basis = f"{kind}|{scene_id}|{speaker_id}|{content}".lower()
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]
    return f"bi_{digest}"


def _existing_entries(session: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    ledger = session.get(LEDGER_KEY) if isinstance(session, Mapping) else None
    entries = ledger.get("entries") if isinstance(ledger, Mapping) else None
    return [e for e in entries if isinstance(e, dict)] if isinstance(entries, list) else []


def accepted_bounded_improvisation_entries(
    session: Mapping[str, Any] | None,
    *,
    scene_id: str | None = None,
    include_session: bool = True,
) -> list[dict[str, Any]]:
    sid = str(scene_id or "").strip()
    out: list[dict[str, Any]] = []
    for entry in _existing_entries(session):
        if str(entry.get("status") or "").strip() not in ACCEPTED_STATUSES:
            continue
        scope = str(entry.get("scope") or "").strip()
        entry_scene = str(entry.get("scene_id") or "").strip()
        if sid and scope == "scene" and entry_scene != sid:
            continue
        if sid and scope == "turn":
            continue
        if not include_session and scope == "session":
            continue
        out.append(dict(entry))
    return out


def _authoritative_text_pool(scene: Mapping[str, Any] | None, world: Mapping[str, Any] | None) -> set[str]:
    pool: set[str] = set()
    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
    if isinstance(inner, Mapping):
        for key in ("visible_facts", "opening_seed_facts", "journal_seed_facts"):
            vals = inner.get(key)
            if isinstance(vals, list):
                pool.update(_clean_text(v).lower() for v in vals if _clean_text(v))
    if isinstance(world, Mapping):
        for npc in world.get("npcs") or []:
            if isinstance(npc, Mapping):
                name = _clean_text(npc.get("name"))
                role = _clean_text(npc.get("role"))
                if name:
                    pool.add(name.lower())
                if role:
                    pool.add(role.lower())
    return {p for p in pool if p}


def _contradicts_existing(content: str, session: Mapping[str, Any] | None, scene: Mapping[str, Any] | None, world: Mapping[str, Any] | None) -> bool:
    low = content.lower()
    existing_contents = {_clean_text(e.get("content")).lower() for e in _existing_entries(session)}
    if low in existing_contents:
        return False
    # Conservative first-cycle contradiction check: reject explicit negation of an existing fact/entry.
    for fact in existing_contents | _authoritative_text_pool(scene, world):
        if len(fact) < 8:
            continue
        if fact in low and re.search(r"\b(no|not|never|isn't|wasn't|aren't|cannot|can't)\b", low):
            return True
        neg_normalized = re.sub(r"\b(is|are|was|were)\s+not\b", r"\1", low)
        neg_normalized = re.sub(r"\b(isn't|aren't|wasn't|weren't)\b", "is", neg_normalized)
        if fact in " ".join(neg_normalized.split()) and re.search(
            r"\b(not|isn't|aren't|wasn't|weren't)\b",
            low,
        ):
            return True
    return False


def normalize_improvisation_proposal(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, Mapping):
        return None
    kind = _clean_token(raw.get("kind") or raw.get("type") or raw.get("authority_type") or raw.get("category"))
    category = _clean_token(raw.get("category"), default=kind)
    if kind in {"incidental", "bounded_incidental", "fact"}:
        kind = INCIDENTAL_KIND
    if kind in {"claim", "rumor", "npc_rumor", "npc_hearsay"}:
        kind = NPC_CLAIM_KIND
    if kind in {"consequential", "unauthorized", "world_fact", "mechanical_outcome"}:
        kind = CONSEQUENTIAL_KIND
    content = _clean_text(raw.get("content") or raw.get("text") or raw.get("claim"))
    if not content:
        return None
    epistemic_status = _clean_token(raw.get("epistemic_status") or raw.get("epistemic"), default="")
    normalized = {
        "kind": kind,
        "category": category,
        "content": content,
        "scope": _clean_token(raw.get("scope"), default="scene"),
        "consequence_level": _clean_token(raw.get("consequence_level"), default="low"),
        "source": _clean_text(raw.get("source"), limit=160) or "dm_improvisation",
        "speaker_id": _clean_text(raw.get("speaker_id") or raw.get("speaker"), limit=80),
        "epistemic_status": epistemic_status,
    }
    contract_id = _clean_text(raw.get("satisfies_contract_id"), limit=80)
    dimension = _clean_token(raw.get("requested_dimension"), default="")
    if contract_id:
        normalized["satisfies_contract_id"] = contract_id
    if dimension:
        normalized["requested_dimension"] = dimension
    return normalized


def validate_bounded_improvisation_proposal(
    proposal: Mapping[str, Any],
    *,
    session: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None = None,
) -> BoundedImprovisationDecision:
    norm = normalize_improvisation_proposal(proposal)
    if norm is None:
        return BoundedImprovisationDecision({}, False, ["proposal:not_object_or_empty"])
    reasons: list[str] = []
    kind = str(norm.get("kind") or "")
    content = str(norm.get("content") or "")
    category = str(norm.get("category") or "")
    scope = str(norm.get("scope") or "")
    consequence = str(norm.get("consequence_level") or "")
    epistemic = str(norm.get("epistemic_status") or "")
    if scope not in PERMITTED_SCOPES:
        reasons.append("scope:not_permitted")
    if consequence not in LOW_CONSEQUENCE_LEVELS:
        reasons.append("consequence:not_low")
    if kind == CONSEQUENTIAL_KIND:
        reasons.append("kind:consequential")
    if MECHANICAL_TERMS.search(content):
        reasons.append("content:mechanical_authority")
    from game.proposition_authority import PRICE_OFFICIAL, price_class

    if price_class(content) == PRICE_OFFICIAL and kind == INCIDENTAL_KIND:
        reasons.append("content:official_levy")
    if price_class(content) == PRICE_OFFICIAL and kind == NPC_CLAIM_KIND and epistemic in {"known", "grounded"}:
        reasons.append("npc_claim:grounded_consequential_claim")
    if HIDDEN_INFO_TERMS.search(content):
        reasons.append("content:hidden_information")
    if kind == INCIDENTAL_KIND:
        if category not in ALLOWED_INCIDENTAL_CATEGORIES:
            reasons.append("category:not_incidental")
        if CONSEQUENTIAL_TERMS.search(content):
            reasons.append("content:consequential_terms")
    elif kind == NPC_CLAIM_KIND:
        if category not in ALLOWED_NPC_CLAIM_CATEGORIES:
            reasons.append("category:not_npc_claim")
        if epistemic not in ALLOWED_EPISTEMIC_STATUSES:
            reasons.append("epistemic:not_supported")
        if epistemic in {"known", "grounded"} and CONSEQUENTIAL_TERMS.search(content):
            reasons.append("npc_claim:grounded_consequential_claim")
    else:
        reasons.append("kind:not_supported")
    if _contradicts_existing(content, session, scene, world):
        reasons.append("content:contradicts_existing")
    if isinstance(resolution, Mapping):
        kind_res = str(resolution.get("kind") or "").strip().lower()
        if kind_res in {"attack", "spell", "skill_check", "enemy_attack"} and kind != NPC_CLAIM_KIND:
            reasons.append("resolution:mechanical_lane")
        metadata = resolution.get("metadata")
        contract = metadata.get("resolution_contract") if isinstance(metadata, Mapping) else None
        if (
            isinstance(contract, Mapping)
            and contract.get("epistemic_mode") == "consequential_protected"
            and kind == INCIDENTAL_KIND
        ):
            reasons.append("contract:consequential_protected")
    accepted = not reasons
    scene_id = _scene_id_from_scene(scene, session)
    entry = None
    if accepted:
        status = "accepted"
        entry = {
            "id": _entry_id(kind, scene_id, content, str(norm.get("speaker_id") or "")),
            "kind": kind,
            "category": category,
            "content": content,
            "scope": scope,
            "scene_id": scene_id if scope in {"scene", "turn"} else None,
            "consequence_level": consequence,
            "source": str(norm.get("source") or "dm_improvisation"),
            "speaker_id": str(norm.get("speaker_id") or "") or None,
            "epistemic_status": epistemic if kind == NPC_CLAIM_KIND else None,
            "status": status,
            "authority": "bounded_improvisation",
            "truth_status": "not_world_truth" if kind == NPC_CLAIM_KIND else "runtime_incidental",
        }
        if norm.get("satisfies_contract_id"):
            entry["satisfies_contract_id"] = norm.get("satisfies_contract_id")
        if norm.get("requested_dimension"):
            entry["requested_dimension"] = norm.get("requested_dimension")
    return BoundedImprovisationDecision(dict(norm), accepted, reasons, entry)


def evaluate_improvisation_proposals(
    gm: Mapping[str, Any] | None,
    *,
    session: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    proposals = gm.get(IMPROVISATION_PROPOSAL_KEY) if isinstance(gm, Mapping) else None
    raw_items = proposals if isinstance(proposals, list) else []
    decisions = [
        validate_bounded_improvisation_proposal(
            raw,
            session=session,
            scene=scene,
            world=world,
            resolution=resolution,
        )
        for raw in raw_items
    ]
    accepted = [d.entry for d in decisions if d.accepted and isinstance(d.entry, dict)]
    rejected = [
        {
            "proposal": d.proposal,
            "reason_codes": list(d.reason_codes),
        }
        for d in decisions
        if not d.accepted
    ]
    return {
        "version": LEDGER_VERSION,
        "proposal_count": len(raw_items),
        "accepted": accepted,
        "rejected": rejected,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "has_valid_bounded_improvisation": bool(accepted),
    }


def attach_bounded_improvisation_evaluation(
    gm: dict[str, Any],
    *,
    session: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(gm, dict):
        return gm
    evaluation = evaluate_improvisation_proposals(
        gm,
        session=session,
        scene=scene,
        world=world,
        resolution=resolution,
    )
    if int(evaluation.get("proposal_count") or 0) <= 0:
        gm.pop(IMPROVISATION_AUTHORITY_KEY, None)
        return gm
    gm[IMPROVISATION_AUTHORITY_KEY] = evaluation
    md = gm.setdefault("metadata", {})
    if isinstance(md, dict):
        em = md.setdefault("emission_debug", {})
        if isinstance(em, dict):
            em[IMPROVISATION_AUTHORITY_KEY] = {
                "proposal_count": evaluation["proposal_count"],
                "accepted_count": evaluation["accepted_count"],
                "rejected_count": evaluation["rejected_count"],
                "has_valid_bounded_improvisation": evaluation["has_valid_bounded_improvisation"],
            }
    return gm


def gm_has_valid_bounded_improvisation(gm: Mapping[str, Any] | None) -> bool:
    if not isinstance(gm, Mapping):
        return False
    ev = gm.get(IMPROVISATION_AUTHORITY_KEY)
    if isinstance(ev, Mapping):
        return bool(ev.get("has_valid_bounded_improvisation"))
    return bool(evaluate_improvisation_proposals(gm, session=None, scene=None, world=None).get("accepted_count"))


def promote_accepted_bounded_improvisation(
    gm: Mapping[str, Any] | None,
    *,
    session: dict[str, Any],
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from game.immutable_valid_response import accepted_record, effects_allowed

    if accepted_record(gm) is not None and not effects_allowed(gm):
        return {
            "promoted_count": 0,
            "rejected_count": 0,
            "accepted_count": 0,
            "promoted_ids": [],
            "blocked_reason": "rejected_or_unaccepted_candidate",
        }
    evaluation = (
        gm.get(IMPROVISATION_AUTHORITY_KEY)
        if isinstance(gm, Mapping) and isinstance(gm.get(IMPROVISATION_AUTHORITY_KEY), Mapping)
        else evaluate_improvisation_proposals(gm, session=session, scene=scene, world=world, resolution=resolution)
    )
    ledger = ensure_bounded_improvisation_ledger(session)
    entries = ledger.setdefault("entries", [])
    rejected_bucket = ledger.setdefault("rejected", [])
    existing_ids = {str(e.get("id") or "") for e in entries if isinstance(e, Mapping)}
    promoted: list[dict[str, Any]] = []
    for entry in evaluation.get("accepted") or []:
        if not isinstance(entry, dict):
            continue
        eid = str(entry.get("id") or "")
        if eid and eid not in existing_ids:
            stored = dict(entry)
            stored["status"] = "promoted"
            entries.append(stored)
            existing_ids.add(eid)
            promoted.append(stored)
    for rejected in evaluation.get("rejected") or []:
        if isinstance(rejected, dict):
            rejected_bucket.append(dict(rejected))
    if len(rejected_bucket) > 50:
        del rejected_bucket[:-50]
    return {
        "promoted_count": len(promoted),
        "rejected_count": int(evaluation.get("rejected_count") or 0),
        "accepted_count": int(evaluation.get("accepted_count") or 0),
        "promoted_ids": [str(e.get("id") or "") for e in promoted],
    }


def prompt_projection_for_bounded_improvisation(
    session: Mapping[str, Any] | None,
    *,
    scene_id: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    entries = accepted_bounded_improvisation_entries(session, scene_id=scene_id)
    compact: list[dict[str, Any]] = []
    for entry in entries[-max(1, limit):]:
        compact.append(
            {
                "id": entry.get("id"),
                "kind": entry.get("kind"),
                "category": entry.get("category"),
                "content": entry.get("content"),
                "scope": entry.get("scope"),
                "scene_id": entry.get("scene_id"),
                "speaker_id": entry.get("speaker_id"),
                "epistemic_status": entry.get("epistemic_status"),
                "truth_status": entry.get("truth_status"),
            }
        )
    return {
        "version": LEDGER_VERSION,
        "entries": compact,
        "instructions": [
            "Accepted bounded incidental facts may be reused for consistency but are not authored world truth.",
            "NPC claims remain claims with epistemic status; do not promote rumors/hearsay/speculation into world truth.",
            "Reject contradictions, mechanical outcomes, hidden information, and consequential world changes.",
        ],
    }

# PR-PLAY-74: persistent public facts use the existing bounded ledger. The
# constrained proposal vocabulary is intentional: arbitrary provider prose
# cannot be made safe by a keyword blacklist.
WORLD_FACT_GATE = 'ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION'
WORLD_FACT_FIELDS = frozenset({'family', 'campaign_id', 'scene_id', 'anchor', 'quality', 'visibility'})


def controlled_enabled(session):
    import os
    from game.authored_consequences import enabled_for_session
    return (os.environ.get(WORLD_FACT_GATE) == '1'
            and os.environ.get('ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE') == '1'
            and enabled_for_session(session or {}))


def controlled_facts(session, scene_id=None):
    campaign = str((session or {}).get('campaign_run_id') or '')
    return [e for e in _existing_entries(session)
            if e.get('authority') == 'controlled_world_fact'
            and e.get('campaign_id') == campaign and e.get('visibility') == 'public'
            and e.get('status') == 'accepted'
            and (scene_id is None or e.get('scene_id') == scene_id)]


def validate_world_fact(raw, *, session, scene, world):
    """Pure validation. Text/properties/identity come from engine policy only."""
    def reject(reason, category='E'):
        return {'accepted': False, 'reason': reason, 'category': category}
    if not isinstance(raw, dict) or set(raw) != WORLD_FACT_FIELDS:
        return reject('schema')
    if (type(raw['anchor']) is not int or not all(isinstance(raw[k], str) for k in WORLD_FACT_FIELDS - {'anchor'})
            or raw['visibility'] != 'public'):
        return reject('schema')
    inner = scene.get('scene', scene) if isinstance(scene, dict) else {}
    campaign = str((session or {}).get('campaign_run_id') or '')
    sid = str(inner.get('id') or '')
    if not campaign or not sid or raw['campaign_id'] != campaign or raw['scene_id'] != sid or (session or {}).get('active_scene_id') != sid:
        return reject('context')
    family, quality = raw['family'], raw['quality']
    if (family, quality) not in {('environment', 'rough'), ('object', 'seat')}:
        return reject('unsupported', 'D')
    facts = inner.get('visible_facts') or []
    index = raw['anchor']
    if not 0 <= index < len(facts) or not isinstance(facts[index], str):
        return reject('anchor')
    anchor = facts[index]
    # Only public, affirmative stone/furniture support. Never infer from hidden
    # state, journal history, a destination, or a negated scene feature.
    if re.search(r'\b(no|not|without|empty|absent|imagined|painted|picture|dead)\b', anchor, re.I):
        return reject('scene_support')
    if not re.search(r'\b(stone|stonework|rock|rocks|boulder|boulders)\b', anchor, re.I):
        return reject('scene_support')
    category = 'B' if family == 'environment' else 'C'
    label = 'rough stone surface' if family == 'environment' else 'ordinary stone seat'
    description = ('The stone has a rough, uneven surface.' if family == 'environment'
                   else 'An ordinary low stone beside the established stonework offers a place to sit.')
    basis = f'{campaign}|{sid}|{family}|{anchor}'
    eid = 'wf_' + hashlib.sha256(basis.encode()).hexdigest()[:20]
    existing = controlled_facts(session)
    for e in existing:
        if e['id'] == eid:
            return {'accepted': True, 'reason': 'established', 'category': 'A', 'entry': dict(e)}
        if e.get('scene_id') == sid and e.get('family') == family:
            return reject('duplicate_identity')
    for item in inner.get('interactables') or []:
        if isinstance(item, dict) and label.casefold() in {str(item.get('label', '')).casefold(), *[str(a).casefold() for a in item.get('aliases', [])]}:
            return reject('authored_identity')
    entry = {'id': eid, 'campaign_id': campaign, 'scene_id': sid, 'category': category,
             'family': family, 'entity_type': 'surface' if family == 'environment' else 'object',
             'label': label, 'content': description, 'canonical_description': description,
             'properties': {'material': 'stone', 'texture': 'rough'} if family == 'environment' else {'material': 'stone', 'use': 'seat'},
             'anchor': anchor, 'provenance': 'accepted_improvisation', 'source': 'validated_proposal',
             'creation_turn': int((session or {}).get('turn_counter') or 0), 'visibility': 'public',
             'status': 'accepted', 'authority': 'controlled_world_fact', 'truth_status': 'runtime_incidental',
             'scope': 'scene', 'persistence_status': 'campaign', 'interactions': []}
    return {'accepted': True, 'reason': 'accepted', 'category': category, 'entry': entry}


def controlled_request(text, *, session, scene, world):
    """Read-only planning for the existing initiative/bridge/exploration path."""
    if not controlled_enabled(session):
        return None
    inner = scene.get('scene', scene)
    sid = inner.get('id')
    low = text.casefold()
    entries = controlled_facts(session, sid)
    if entries and re.search(r'\b(?:move|take|lift|sit on|climb|destroy|break)\s+(?:it|that|this)\b', low):
        return {'mode': 'decline', 'message': 'That interaction has no configured mechanic or authority. Nothing has been attempted.'}
    # A reference never grants authority, movement, treasure or NPC knowledge.
    named = [e for e in entries if (('seat' in low and e['family'] == 'object')
             or ('surface' in low and e['family'] == 'environment') or e['label'] in low)]
    pronoun = bool(re.search(
        r'\b(?:inspect|examine|check|search|study|look at|sit on|move|take|lift)\s+'
        r'(?:it|that|this)(?:\s+again)?[.!?]*$', low
    ) or re.fullmatch(r'\s*(?:is|was)\s+(?:it|that|this)\s+(?:still there|magical)[.!?]*', low))
    if not named and pronoun:
        focus = (session or {}).get('bounded_improvisation', {}).get('focus')
        named = [e for e in entries if e['id'] == focus]
    if named:
        if len(named) != 1:
            return {'mode': 'clarify', 'message': 'Which established detail do you mean?'}
        e = named[0]
        if re.search(r'\b(secret|treasure|quest|magic|magical|weapon|move|take|lift|sit|climb|destroy|break)\b', low):
            return {'mode': 'decline', 'message': 'That interaction has no configured mechanic or authority. The established detail is unchanged.'}
        if re.match(r'\s*(is|are|what|where|does|do|was|were)\b', low):
            return {'mode': 'answer', 'message': e['content'], 'id': e['id']}
        if re.search(r'\b(inspect|examine|check|search|look|study)\b', low):
            if re.search(r'\b(if|unless|then|and|never|not)\b', low):
                return {'mode': 'clarify', 'message': 'What single action do you want to attempt?'}
            return {'mode': 'interact', 'id': e['id']}
    family = None
    if re.search(r'\b(anything|something|place|object)\b.*\b(sit|seat|rest)\b', low):
        family = 'object'
    elif re.search(r'\b(describe|texture|surface detail|environmental detail)\b', low):
        family = 'environment'
    if family is None:
        return None
    if re.search(r'\b(secret|hidden|treasure|quest|magic|weapon|passage|tunnel|if|unless|then)\b', low):
        return {'mode': 'decline', 'message': 'That proposal exceeds the permitted ordinary detail policy.'}
    if family == 'environment' and re.match(r'\s*(what|is|are|do|does)\b', low):
        return {'mode': 'answer', 'message': ' '.join(e['content'] for e in entries) or 'No additional detail has been established.'}
    existing = [e for e in entries if e['family'] == family]
    if existing:
        return {'mode': 'answer', 'message': existing[0]['content'], 'id': existing[0]['id']}
    for index, _fact in enumerate(inner.get('visible_facts') or []):
        raw = {'family': family, 'campaign_id': session.get('campaign_run_id'), 'scene_id': sid,
               'anchor': index, 'quality': 'rough' if family == 'environment' else 'seat', 'visibility': 'public'}
        verdict = validate_world_fact(raw, session=session, scene=scene, world=world)
        if verdict['accepted']:
            return {'mode': 'propose', 'id': verdict['entry']['id'], 'proposal': raw}
    return {'mode': 'decline', 'message': 'The public scene does not support that ordinary detail. Nothing has been added.'}


def resolve_controlled_fact(scene, session, world, action, *, prompt, action_id, label):
    """Called only by the exploration resolver; session persists in its transaction."""
    import copy
    from game.models import ExplorationEngineResult
    plan = controlled_request(prompt, session=session, scene=scene, world=world)
    if not plan or plan.get('mode') not in {'propose', 'interact'} or plan.get('id') != action.get('target_id'):
        return None
    if plan['mode'] == 'propose':
        verdict = validate_world_fact(plan['proposal'], session=session, scene=scene, world=world)
        if not verdict['accepted']:
            return None
        entry = copy.deepcopy(verdict['entry'])
        ledger = ensure_bounded_improvisation_ledger(session)
        if not any(e.get('id') == entry['id'] for e in ledger['entries']):
            ledger['entries'].append(entry)
        ledger['focus'] = entry['id']
        publication = entry['content']
    else:
        entry = next(e for e in session[LEDGER_KEY]['entries'] if e.get('id') == plan['id'])
        # Reuse PR73 physical-search result; no discovery, loot, movement or DC.
        from game.general_purpose_actions import exploration_outcome, FAMILY_SEARCH
        projected = copy.deepcopy(scene)
        inner = projected.get('scene', projected)
        inner.setdefault('interactables', []).append({'id': entry['id'], 'label': entry['label']})
        search = dict(action, metadata={'general_purpose_family': FAMILY_SEARCH})
        result = exploration_outcome(projected, search, prompt=prompt, action_id=action_id, label=label)
        event = {'turn': int(session.get('turn_counter') or 0), 'action': 'physical_search'}
        if event not in entry['interactions']:
            entry['interactions'].append(event)
        session[LEDGER_KEY]['focus'] = entry['id']
        result['metadata']['engine_publication'] = entry['content'] + ' ' + result['metadata']['engine_publication']
        result['metadata']['controlled_entity_id'] = entry['id']
        result['metadata']['publication_contract'] = 'FINAL_ENGINE_RESPONSE'
        result['metadata']['skip_primary_narration'] = True
        return result
    return ExplorationEngineResult(kind='observe', action_id=action_id, label=label, prompt=prompt,
        success=True, resolved_transition=False, target_scene_id=None, clue_id=None, discovered_clues=[], state_changes={'controlled_entity_id': entry['id']},
        metadata={'engine_publication': publication, 'controlled_entity_id': entry['id'],
                  'publication_contract': 'FINAL_ENGINE_RESPONSE',
                  'skip_unrelated_clue_discovery': True, 'skip_primary_narration': True}).to_dict()


def provider_world_fact_proposal(*, session, scene, world, family, invoke=None):
    """Single bounded shadow proposal using the existing provider/accounting stack.

    No retries, no state mutation, no automatic publication. Callers can pass a
    deterministic transport for development. Normal gameplay uses local policy.
    """
    import json
    import time
    started = time.perf_counter()
    inner = scene.get('scene', scene)
    schema = {'type': 'object', 'additionalProperties': False, 'required': sorted(WORLD_FACT_FIELDS),
              'properties': {'family': {'type': 'string', 'enum': [family]},
                'campaign_id': {'type': 'string'}, 'scene_id': {'type': 'string'},
                'anchor': {'type': 'integer'}, 'quality': {'type': 'string', 'enum': ['rough' if family == 'environment' else 'seat']},
                'visibility': {'type': 'string', 'enum': ['public']}}}
    messages = [{'role': 'system', 'content': 'Propose one ordinary detail using only public stone support. Return the constrained proposal. Do not invent effects.'},
                {'role': 'user', 'content': json.dumps({'family': family, 'campaign_id': session.get('campaign_run_id'),
                  'scene_id': inner.get('id'), 'visible_facts': inner.get('visible_facts', [])})}]
    try:
        if invoke is not None:
            raw = invoke(messages, schema)
        else:
            from openai import OpenAI
            from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
            from game.provider_budget import admit_request, sdk_retry_options
            attempt = admit_request(purpose='controlled_improvisation', owner='bounded_improvisation',
                        model=DEFAULT_MODEL_NAME, estimated_input=len(json.dumps(messages)) // 4 + 250, max_output=300)
            if attempt.refusal:
                raise RuntimeError('provider_admission_refused')
            client = OpenAI(api_key=get_openai_api_key(), timeout=30, **sdk_retry_options())
            response = attempt.dispatch(client.responses.create, model=DEFAULT_MODEL_NAME, input=messages,
                       max_output_tokens=300, text={'format': {'type': 'json_schema', 'name': 'world_fact_proposal',
                                                              'strict': True, 'schema': schema}})
            raw = response.output_text
        proposal = json.loads(raw) if isinstance(raw, str) else raw
        verdict = validate_world_fact(proposal, session=session, scene=scene, world=world)
        return {'proposal': proposal, 'validation': verdict, 'committed': False, 'published_text': '',
                'latency_ms': (time.perf_counter()-started)*1000, 'retries': 0}
    except Exception as exc:
        return {'proposal': None, 'validation': {'accepted': False, 'reason': type(exc).__name__},
                'committed': False, 'published_text': '', 'latency_ms': (time.perf_counter()-started)*1000, 'retries': 0}

# PR-PLAY-75: NPC proposals share the bounded world-fact ledger and resolver.
NPC_GATE = 'ASHEN_EXPERIMENTAL_DYNAMIC_NPCS'
NPC_FIELDS = frozenset({'campaign_id', 'scene_id', 'anchor', 'role', 'name', 'appearance', 'demeanor', 'visibility'})
NPC_ROLES = ('traveler', 'resident', 'merchant', 'bystander', 'laborer', 'patron')
NPC_APPEARANCES = ('plain wool coat', 'weathered cloak', 'simple linen clothes', 'patched work clothes')
NPC_DEMEANORS = ('reserved', 'friendly', 'tired', 'matter-of-fact')


def dynamic_npcs(session, scene_id=None):
    return [e for e in _existing_entries(session)
            if e.get('authority') == 'accepted_background_npc' and e.get('status') == 'accepted'
            and e.get('campaign_id') == (session or {}).get('campaign_run_id')
            and e.get('visibility') == 'public' and (scene_id is None or e.get('scene_id') == scene_id)]


def _population_anchor(scene):
    inner = scene.get('scene', scene)
    facts = inner.get('visible_facts') or []
    # Absence anywhere in the public scene wins over positive snippets.
    if re.search(r'\b(empty|deserted|uninhabited|inaccessible|abandoned|no people|nobody|no one)\b', ' '.join(str(f) for f in facts), re.I):
        return None
    for i, fact in enumerate(facts):
        if isinstance(fact, str) and re.search(r'\b(crowd|refugees|travelers|travellers|patrons|residents|workers|customers|people|marketplace)\b', fact, re.I):
            return i
    return None


def validate_npc_proposal(raw, *, session, scene, world):
    """Pure, fail-closed authority. Provider wording is never an NPC record."""
    def reject(reason):
        return dict(accepted=False, reason=reason)
    if not isinstance(raw, dict) or set(raw) != NPC_FIELDS:
        return reject('schema')
    if type(raw['anchor']) is not int or any(type(raw[k]) is not str for k in NPC_FIELDS - {'anchor'}):
        return reject('schema')
    inner = scene.get('scene', scene); sid = inner.get('id'); cid = session.get('campaign_run_id')
    if not cid or not sid or raw['campaign_id'] != cid or raw['scene_id'] != sid or session.get('active_scene_id') != sid:
        return reject('context')
    anchor = _population_anchor(scene)
    if anchor is None or raw['anchor'] != anchor:
        return reject('population')
    if raw['visibility'] != 'public' or raw['role'] not in NPC_ROLES or raw['appearance'] not in NPC_APPEARANCES or raw['demeanor'] not in NPC_DEMEANORS:
        return reject('ordinary_scope')
    name = raw['name']
    if name and (not re.fullmatch(r'[A-Z][a-z]{1,17}', name) or _consequential_name(name)):
        return reject('name')
    # One background identity per scene in this bounded cycle, regardless of aliases.
    existing = dynamic_npcs(session, sid)
    if existing:
        return dict(accepted=True, reason='existing_identity', entry=existing[0])
    for npc in world.get('npcs') or []:
        if isinstance(npc, dict) and name and str(npc.get('name', '')).casefold() == name.casefold():
            return reject('authored_identity')
    label = 'ordinary ' + raw['role']
    roster = inner.get('addressables') or []
    if any(isinstance(n, dict) and (str(n.get('name', '')).casefold() in {name.casefold(), label}
           or str(n.get('label', '')).casefold() == label) for n in roster):
        return reject('authored_identity')
    eid = 'npc_' + hashlib.sha256(f'{cid}|{sid}|background'.encode()).hexdigest()[:20]
    entry = dict(id=eid, campaign_id=cid, scene_id=sid, location=sid, entity_type='npc', family='npc',
        label=label, name=name, role=raw['role'], appearance=raw['appearance'], demeanor=raw['demeanor'],
        visibility='public', provenance='accepted_improvisation', source='validated_provider_proposal',
        creation_turn=int(session.get('turn_counter') or 0), status='accepted', authority='accepted_background_npc',
        scope='scene', persistence_status='campaign', interaction_available=True, knowledge=[], social_receipts=[],
        content=f"An {label} in {raw['appearance']} is among the people here.")
    return dict(accepted=True, reason='accepted', entry=entry)


def _consequential_name(name):
    return bool(CONSEQUENTIAL_TERMS.search(name) or MECHANICAL_TERMS.search(name) or name.lower() in
                {'sentinel', 'canary', 'system', 'admin', 'god', 'emperor', 'queen', 'prince', 'questgiver'})


def provider_npc_proposal(*, session, scene, world, invoke=None):
    """One proposal through the existing SDK admission/usage owner; no writes/retry."""
    import json, time
    started = time.perf_counter(); inner = scene.get('scene', scene)
    properties = {k: {'type': 'string'} for k in NPC_FIELDS - {'anchor'}}
    properties['anchor'] = {'type': 'integer'}
    for key, values in [('role', NPC_ROLES), ('appearance', NPC_APPEARANCES), ('demeanor', NPC_DEMEANORS), ('visibility', ['public'])]:
        properties[key]['enum'] = list(values)
    schema = dict(type='object', additionalProperties=False, required=sorted(NPC_FIELDS), properties=properties)
    view = dict(campaign_id=session.get('campaign_run_id'), scene_id=inner.get('id'), anchor=_population_anchor(scene),
                visible_facts=inner.get('visible_facts', []))
    messages = [{'role':'system','content':'Propose one ordinary background person supported by this public population. Use a short ordinary first name or empty name. No authority, biography, knowledge, quest, effects or secrets.'},
                {'role':'user','content':json.dumps(view)}]
    attempt = None
    try:
        if view['anchor'] is None:
            raise ValueError('population')
        if invoke is not None:
            raw = invoke(messages, schema)
        else:
            from openai import OpenAI
            from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
            from game.provider_budget import admit_request, sdk_retry_options
            attempt = admit_request(purpose='background_npc_proposal', owner='bounded_improvisation', model=DEFAULT_MODEL_NAME,
                                    estimated_input=len(json.dumps(messages))//4+400, max_output=250)
            if attempt.refusal:
                raise RuntimeError('provider_admission_refused')
            response = attempt.dispatch(OpenAI(api_key=get_openai_api_key(), timeout=30, **sdk_retry_options()).responses.create,
                model=DEFAULT_MODEL_NAME, input=messages, max_output_tokens=250,
                text={'format':{'type':'json_schema','name':'background_npc','strict':True,'schema':schema}})
            raw = response.output_text
            usage = response.usage
            attempt.finish(dict(purpose='background_npc_proposal',sent=True,model=response.model,
                request_id=response.id,input_tokens=usage.input_tokens,output_tokens=usage.output_tokens,total_tokens=usage.total_tokens))
            attempt = None
        proposal = json.loads(raw) if isinstance(raw, str) else raw
        verdict = validate_npc_proposal(proposal, session=session, scene=scene, world=world)
        return dict(proposal=proposal, validation=verdict, latency_ms=(time.perf_counter()-started)*1000,retries=0)
    except Exception as exc:
        if attempt is not None:
            attempt.finish(dict(purpose='background_npc_proposal',sent=not bool(attempt.refusal),error=type(exc).__name__,
                                input_tokens=None,output_tokens=None,total_tokens=None))
        return dict(proposal=None,validation=dict(accepted=False,reason=type(exc).__name__),latency_ms=(time.perf_counter()-started)*1000,retries=0)


_NOT_NPC_TURN = re.compile(
    r"\b(?:notice board|where am i|where are we|what do i see|what can i see|what is here|"
    r"what (?:do|did|have) (?:i|we) know|remind me|my (?:inventory|journal))\b",
    re.I,
)


def focused_present_npc(session, scene, world):
    """The focused NPC only while that person is still in this scene and campaign."""
    ledger = session.get(LEDGER_KEY) if isinstance(session, dict) else None
    focus = (ledger or {}).get("npc_focus") if isinstance(ledger, dict) else None
    if not focus or not isinstance(scene, dict):
        return None
    inner = scene.get("scene", scene)
    sid = inner.get("id") if isinstance(inner, dict) else None
    campaign = session.get("campaign_run_id")

    def usable(row):
        if not isinstance(row, dict) or row.get("id") != focus:
            return False
        marked = row.get("campaign_id")
        if marked and marked != campaign:
            return False
        scene_id = str(row.get("scene_id") or "")
        location = str(row.get("location") or "")
        if scene_id and sid and scene_id != sid:
            return False
        if location and sid and location != sid:
            return False
        return True

    found = None
    for entry in dynamic_npcs(session, sid):
        if usable(entry):
            found = entry
            break
    addressed = (ledger or {}).get("addressed_npcs") if isinstance(ledger, dict) else None
    if found is None and isinstance(addressed, dict) and usable(addressed.get(focus)):
        found = addressed.get(focus)
    if found is None:
        for npc in (world or {}).get("npcs") or []:
            if usable(npc):
                found = npc
                break
    if found is None and isinstance(inner, dict):
        for item in inner.get("addressables") or []:
            if isinstance(item, dict) and item.get("id") == focus:
                found = item
                break
    conv = session.get("conversational_context") if isinstance(session, dict) else None
    slot = conv.get("active_interlocutor") if isinstance(conv, dict) else None
    if isinstance(slot, dict):
        marked_campaign = slot.get("campaign_id")
        if marked_campaign and campaign and marked_campaign != campaign:
            found = None
    if found is not None:
        return found
    if isinstance(ledger, dict):
        ledger["npc_focus"] = None
    conv = session.get("conversational_context") if isinstance(session, dict) else None
    slot = conv.get("active_interlocutor") if isinstance(conv, dict) else None
    if isinstance(slot, dict) and slot.get("npc_id") == focus:
        slot["status"] = "inactive"
        slot["npc_id"] = None
    return None


def npc_request(text, *, session, scene, world):
    import os
    if os.environ.get(NPC_GATE) != '1' or not controlled_enabled(session):
        return None
    low = text.casefold().replace('’', "'"); sid = scene.get('scene', scene).get('id')
    if sid != session.get('active_scene_id'):
        return None
    if _NOT_NPC_TURN.search(low):
        return None
    focused = bool((session.get(LEDGER_KEY) or {}).get("npc_focus"))
    if not focused and re.search(r'\b(?:what (?:have|did|do) (?:i|we)|my (?:inventory|journal|spells|character)|what happened|remind me)\b', low):
        return None
    entries = dynamic_npcs(session, sid)
    request = bool(re.search(r'\b(introduce|find|meet|look for|speak (?:with|to)|talk (?:with|to))\b', low)
                   and re.search(r'\b(ordinary|background|someone|local resident)\b', low))
    # Authored names always retain the existing social route.
    if any(isinstance(n, dict) and n.get('name') and str(n['name']).casefold() in low for n in world.get('npcs') or []):
        return None
    def mentions(value):
        return bool(value and re.search(r'(?<!\w)' + re.escape(value.casefold()) + r'(?!\w)', low))
    named = [e for e in entries if mentions(e.get('name')) or mentions(e['role']) or mentions(e['label'])]
    if not named and len(entries) == 1 and re.search(r"\boffer\b", low):
        named = entries
    focus = (session.get(LEDGER_KEY) or {}).get('npc_focus')
    reference = bool(re.search(r'\b(that traveler|person by|person i spoke|ask (?:her|him|them)|talk to (?:her|him|them)|speak with (?:her|him|them))\b', low)
                     or (focus and re.search(r'\b(?:does|do)\s+(?:he|she|they)\b', low)))
    direct = bool(focus and re.match(r'^(?:hello|hi\b|greetings|who\b|what\b|why\b|have you\b|can you\b|could you\b|thanks\b|thank you\b|tell me\b|i tell\b|give me\b|offer me\b|promise\b|when\b|do you\b|goodbye\b|farewell\b)', low))
    if named or reference or direct or (request and entries):
        person = focused_present_npc(session, scene, world) if (direct or reference) and not named else None
        if (direct or reference) and not named:
            if person is None:
                return None
            targets = [person]
        else:
            targets = named or [e for e in entries if e.get('id') == focus] or entries
        if len(targets) != 1:
            return dict(mode='clarify', message='Which available person do you mean?')
        npc = targets[0]
        if re.search(r'\b(?:seem|nervous|worried|demeanor|manner)\b', low):
            return dict(mode='answer', message=f"{npc.get('name') or npc['label']} seems {npc.get('demeanor') or 'ordinary'}. Nothing establishes a hidden motive.")
        if re.match(r'^(?:is|was|where is|who is|what is|does)\b', low) and not re.search(r'\byou\b',low) and npc.get('content'):
            return dict(mode='answer',message=npc['content'])
        if re.search(r'\b(bribe|persuade|bluff|intimidate|threaten|attack|steal|force|command)\b', low):
            return dict(mode='decline',message='That requires an established social or combat mechanic; this background conversation cannot grant compliance.')
        return dict(mode='interact',id=npc['id'],npc_mode='conversation')
    if request:
        if re.search(r'\b(secret|quest|treasure|noble|spy|hidden|captain|king|soldier|passage|magic)\b', low):
            return dict(mode='decline',message='No person with that knowledge or authority is established here.')
        if _population_anchor(scene) is None:
            return dict(mode='decline',message='The established public scene does not support introducing another person here.')
        eid = 'npc_' + hashlib.sha256(f"{session.get('campaign_run_id')}|{sid}|background".encode()).hexdigest()[:20]
        return dict(mode='propose',id=eid,npc_mode='creation')
    if reference:
        return dict(mode='clarify',message='Which available person do you mean?')
    return None


_ordinary_detail_request = controlled_request

def controlled_request(text, *, session, scene, world):
    from game.integrated_play import plan_integrated
    mixed = plan_integrated(text, session=session, scene=scene, world=world)
    if mixed is not None:
        return mixed
    plan = npc_request(text,session=session,scene=scene,world=world)
    if plan is not None:
        return plan
    from game.physical_adjudication import plan_physical
    physical = plan_physical(text, session=session, scene=scene, world=world)
    if physical is not None:
        return physical
    # Routine sitting reuses an accepted seat, without a check or an invented object.
    if __import__('os').environ.get(NPC_GATE) == '1' and controlled_enabled(session) and re.search(r'\b(?:sit|rest)\s+(?:on\s+)?', text, re.I):
        sid = scene.get('scene',scene).get('id')
        seats = [e for e in controlled_facts(session,sid) if e.get('properties',{}).get('use')=='seat']
        if len(seats)==1 and re.search(r'\b(seat|it|that|this)\b',text,re.I) and not re.search(r'\b(if|unless|and|throne|imaginary|magic)\b',text,re.I):
            return dict(mode='interact',id=seats[0]['id'],routine='sit')
    return _ordinary_detail_request(text,session=session,scene=scene,world=world)


_resolve_ordinary_detail = resolve_controlled_fact

def resolve_controlled_fact(scene, session, world, action, *, prompt, action_id, label):
    from game.models import ExplorationEngineResult
    plan = controlled_request(prompt,session=session,scene=scene,world=world)
    if plan and plan.get('integrated') and plan.get('mode') == 'interact':
        if plan.get('id') != action.get('target_id'):
            return None
        from game.integrated_play import commit_integrated
        return commit_integrated(scene, session, world, action, prompt=prompt, action_id=action_id, label=label)
    if not plan or plan.get('id') != action.get('target_id'):
        return None
    publication = ''; success = True
    if plan.get('npc_mode') == 'creation':
        proposed = provider_npc_proposal(session=session,scene=scene,world=world)
        verdict = proposed['validation']
        ledger = ensure_bounded_improvisation_ledger(session)
        # Private bounded diagnostics, never in the publication DTO.
        ledger['npc_last_proposal'] = proposed
        if not verdict['accepted']:
            ledger['rejected'] = (ledger['rejected'] + [dict(kind='background_npc',reason=verdict['reason'],turn=session.get('turn_counter'))])[-24:]
            publication = 'No additional person could be established here. You can still speak to the people already present.'
            success = False
        else:
            import copy
            entry = copy.deepcopy(verdict['entry'])
            if not any(e.get('id')==entry['id'] for e in ledger['entries']):
                ledger['entries'].append(entry)
            ledger['npc_focus'] = entry['id']
            publication = entry['content']
    elif plan.get('npc_mode') == 'conversation':
        from game.expressive_dialogue import background_conversation
        from game.integrated_play import _npc_from_text, remember_interlocutor
        entry = next((e for e in session[LEDGER_KEY]['entries'] if e.get('id')==plan['id']), None)
        npc = _npc_from_text(prompt, session, scene, world) or entry or focused_present_npc(session, scene, world)
        if npc is None:
            publication = 'That person is not here. The conversation has ended.'
            success = False
        else:
            publication = background_conversation(npc,session=session,scene=scene,player_text=prompt)
            remember_interlocutor(session, npc, scene, prompt, publication)
            adopted = bool((session.get('last_background_expression') or {}).get('adopted'))
            session['last_narration'] = {
                'adopted': False, 'requested': False, 'reasons': ['dialogue_already_final'], 'candidate': '',
            }
            session['last_publication'] = {
                'owner': 'bounded_improvisation.conversation',
                'contract': 'FINAL_ENGINE_RESPONSE',
                'final': True,
                'dialogue_generated': bool(publication),
                'dialogue_accepted': adopted,
                'dialogue_composed': bool(publication),
                'dialogue_published': bool(publication),
                'narration_requested': False,
                'narration_accepted': False,
                'narration_published': False,
                'visible': publication,
            }
    elif plan.get('physical'):
        from game.physical_adjudication import commit_physical
        result = commit_physical(scene, session, world, action, prompt=prompt, action_id=action_id, label=label)
        if result and __import__('os').environ.get('ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION') == '1':
            from game.integrated_play import maybe_narrate
            narrated = maybe_narrate(result['metadata'].get('engine_publication') or '', session=session, scene=scene)
            if narrated:
                result['metadata']['engine_publication'] = narrated['text']
                result['metadata']['live_narration'] = True
            from game.publication_contract import stamp, FINAL_ENGINE_RESPONSE
            result['metadata']['bounded_expression_attempted'] = True
            result['metadata']['live_expression_published'] = bool(narrated)
            stamp(result['metadata'], FINAL_ENGINE_RESPONSE,
                  publication=result['metadata'].get('engine_publication'))
        return result
    elif plan.get('routine') == 'sit':
        ledger = ensure_bounded_improvisation_ledger(session)
        # A posture receipt, not a movement/inventory or social effect.
        ledger['posture'] = {'kind':'sitting','seat_id':plan['id'],'scene_id':session.get('active_scene_id')}
        publication = 'You sit on the accessible ordinary stone seat.'
    else:
        return _resolve_ordinary_detail(scene,session,world,action,prompt=prompt,action_id=action_id,label=label)
    return ExplorationEngineResult(kind='interact',action_id=action_id,label=label,prompt=prompt,success=success,
        resolved_transition=False,target_scene_id=None,clue_id=None,discovered_clues=[],
        metadata={'engine_publication':publication,'publication_contract':'FINAL_ENGINE_RESPONSE','skip_unrelated_clue_discovery':True,'skip_primary_narration':True}).to_dict()

