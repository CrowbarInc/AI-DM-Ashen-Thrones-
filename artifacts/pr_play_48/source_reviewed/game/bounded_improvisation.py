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
