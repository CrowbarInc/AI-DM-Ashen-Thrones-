"""Detect and repair mismatches between deterministic resolution and final narration."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.clues import (
    _scan_text_for_actionable_leads,
    _social_resolution_carries_information,
    apply_socially_revealed_leads,
    extract_actionable_social_leads,
)
from game.gm import extract_contextual_leads_from_text
from game.social import SOCIAL_KINDS
from game.utils import slugify

_DIRECTIONAL_PHRASES = re.compile(
    r"\b(?:go\s+to|head\s+to|make\s+for|ask\s+around|start\s+at|try\s+the|"
    r"speak\s+(?:with|to)|talk\s+(?:with|to)|find\s+the|seek\s+(?:the|out)|"
    r"visit\s+the|check\s+(?:the|at)|"
    r"near\s+the|by\s+the)\b",
    re.IGNORECASE,
)

# Stronger than geographic "near the …" — only clear player-facing redirect verbs.
_ESCALATION_EXHAUSTION_REDIRECT_VERBS = re.compile(
    r"\b(?:go\s+to|head\s+to|make\s+for|ask\s+around|start\s+at|try\s+the|"
    r"speak\s+(?:with|to)|talk\s+(?:with|to)|find\s+the|seek\s+(?:the|out)|"
    r"visit\s+the|check\s+(?:the|at))\b",
    re.IGNORECASE,
)

_OPERATIONAL_TOKENS = re.compile(
    r"\b(?:shipment|shipments|patrol|crossroads|stronghold|caravan|route|"
    r"convoy|warehouse|smuggl|rival|faction|rumor|missing\s+patrol|"
    r"notice\s+board|dead\s+drop)\b",
    re.IGNORECASE,
)

_HOUSE_FACTION = re.compile(r"\bhouse\s+[a-z][a-z]+(?:\s+[a-z]+)?\b", re.IGNORECASE)

_NO_NEW_INFO_SNIPPET = "no new information was revealed"


def _subject_is_active_interlocutor(subject: str, npc_name: str | None, npc_id: str | None) -> bool:
    """True when a contextual-lead subject is just the speaking NPC (not a new hook)."""
    s = str(subject or "").strip().lower()
    if not s:
        return False
    nn = str(npc_name or "").strip().lower()
    nid = str(npc_id or "").strip().lower().replace("_", " ")
    if nn and s == nn:
        return True
    if nn:
        nn_parts = nn.split()
        if len(nn_parts) > 1 and s in nn_parts and len(s) >= 4:
            return True
        if nn.startswith(s + " ") or nn.endswith(" " + s):
            return True
    if nid and s == nid:
        return True
    if nid and nid.replace("_", " ") == s:
        return True
    return False


def _scene_inner(scene: Dict[str, Any]) -> Dict[str, Any]:
    return scene.get("scene") if isinstance(scene.get("scene"), dict) else {}


def _scene_id(scene: Dict[str, Any]) -> str:
    return str(_scene_inner(scene).get("id") or "").strip()


def _final_text(gm_output: Dict[str, Any] | None) -> str:
    if not isinstance(gm_output, dict):
        return ""
    return str(gm_output.get("player_facing_text") or "").strip()


def _emergent_actor_hint_detected(
    text: str,
    *,
    npc_id: str | None,
    npc_name: str | None,
) -> bool:
    for c in extract_contextual_leads_from_text(text):
        if not isinstance(c, dict) or not c.get("named"):
            continue
        subj = str(c.get("subject") or "").strip()
        if not subj:
            continue
        if _subject_is_active_interlocutor(subj, npc_name, npc_id):
            continue
        return True
    return False


def _text_indicates_new_information(
    text: str,
    *,
    scene_id: str,
    npc_id: str | None,
    npc_name: str | None,
) -> tuple[bool, str]:
    """Return (has_hooks, probe_kind) for narration that should contradict an empty social payload."""
    if not text.strip():
        return False, ""

    scanned = _scan_text_for_actionable_leads(scene_id, npc_id, text, extraction_source_prefix="mismatch_probe")
    if scanned:
        return True, "operational_pattern"

    ctx = extract_contextual_leads_from_text(text)
    for c in ctx:
        if not isinstance(c, dict):
            continue
        if not c.get("named"):
            continue
        subj = str(c.get("subject") or "").strip()
        if _subject_is_active_interlocutor(subj, npc_name, npc_id):
            continue
        return True, "contextual_lead"

    if _DIRECTIONAL_PHRASES.search(text):
        return True, "directional_phrase"

    if _OPERATIONAL_TOKENS.search(text):
        return True, "operational_token"

    if _HOUSE_FACTION.search(text):
        return True, "faction_reference"

    return False, ""


def _escalation_blocks_fact_repair_from_narration(
    social: Dict[str, Any], probe_kind: str, narration_text: str
) -> bool:
    """When the engine marked the NPC topic-exhausted, do not mint structured clues from invented 'intel' prose.

    Redirects (places to go, people to ask) remain repairable so true ignorance can surface as a lead.
    """
    esc = social.get("social_escalation") if isinstance(social.get("social_escalation"), dict) else {}
    if not esc.get("topic_exhausted"):
        return False
    if esc.get("force_partial_answer"):
        return False
    if _ESCALATION_EXHAUSTION_REDIRECT_VERBS.search(str(narration_text or "")):
        return False
    if probe_kind in ("operational_pattern", "operational_token", "faction_reference"):
        return True
    return False


def _resolution_claims_no_information(resolution: Dict[str, Any]) -> bool:
    kind = str(resolution.get("kind") or "").strip().lower()
    if kind not in SOCIAL_KINDS:
        return False
    if resolution.get("success") is False:
        return False
    if not _social_resolution_carries_information(resolution):
        return True
    return False


def _social_turn_ineligible_for_reconcile(resolution: Dict[str, Any]) -> bool:
    """True when structured social state must not be upgraded from narration."""
    if resolution.get("requires_check"):
        return True
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    if social.get("offscene_target"):
        return True
    if not social.get("target_resolved", True):
        return True
    return False


def _debug_text_claims_no_new_information(gm_output: Dict[str, Any] | None) -> bool:
    if not isinstance(gm_output, dict):
        return False
    dbg = gm_output.get("debug_notes")
    if not isinstance(dbg, str) or not dbg.strip():
        return False
    low = dbg.lower()
    return _NO_NEW_INFO_SNIPPET in low or "no new information" in low


def _scrub_gm_debug_no_new_info_claim(gm_output: Dict[str, Any] | None) -> bool:
    if not isinstance(gm_output, dict):
        return False
    dbg = gm_output.get("debug_notes")
    if not isinstance(dbg, str) or not dbg.strip():
        return False
    if not _debug_text_claims_no_new_information(gm_output):
        return False
    cleaned = dbg
    cleaned = re.sub(re.escape(_NO_NEW_INFO_SNIPPET), "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bno\s+new\s+information\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*\|\s*", " | ", cleaned)
    cleaned = re.sub(r"^\s*\|\s*|\s*\|\s*$", "", cleaned).strip()
    suffix = "narration_reconcile:gm_debug_scrubbed_misleading_no_new_info_claim"
    gm_output["debug_notes"] = (cleaned + " | " if cleaned else "") + suffix
    return True


def _infer_upgraded_reply_kind(*, prior: str, text: str) -> str:
    low = prior.strip().lower()
    if low != "refusal":
        return prior
    if _DIRECTIONAL_PHRASES.search(text):
        return "explanation"
    return "answer"


def reconcile_final_text_with_structured_state(
    *,
    session: dict,
    scene: dict | None,
    world: dict | None,
    resolution: dict | None,
    gm_output: dict | None,
) -> dict:
    """Canonical step after final ``player_facing_text`` is known: align structured resolution and session.

    Runs before narration-driven lead supplements, event log persistence consumers, and session/world save
    (caller should invoke this from the finalization pipeline before those steps).

    Authority direction (PR-AJ / RC-21): an authorized structured or scene-anchored extraction may
    upgrade empty social state. Ordinary narration, named-figure hints, and operational-sounding
    prose are not provenance. Unsourced contextual extraction is diagnostic only and must not mint
    ``narration_ctx_…`` gameplay authority.

    Mutates ``resolution``, ``session``, optionally ``world`` (via lead landing), and ``gm_output`` when
    a repair is applied. Returns diagnostic dict including ``mismatch_repairs_applied`` (list).
    """
    base: Dict[str, Any] = {
        "narration_state_mismatch_detected": False,
        "mismatch_kind": "",
        "mismatch_repair_applied": "none",
        "mismatch_repairs_applied": [],
        "repaired_discovered_clue_texts": [],
        "emergent_actor_hint_detected": False,
        "scene_opening_reconcile_telemetry_only": False,
    }

    if not isinstance(resolution, dict) or not isinstance(session, dict) or not isinstance(scene, dict):
        return base

    if str(resolution.get("kind") or "").strip().lower() == "scene_opening":
        text = _final_text(gm_output if isinstance(gm_output, dict) else None)
        base["scene_opening_reconcile_telemetry_only"] = True
        base["scene_opening_text_len"] = len(text)
        base["scene_opening_text_empty"] = not bool(text.strip())
        nmeta = resolution.setdefault("metadata", {})
        if isinstance(nmeta, dict):
            nmeta["narration_state_consistency"] = dict(base)
        return base

    if not _resolution_claims_no_information(resolution):
        return base
    if _social_turn_ineligible_for_reconcile(resolution):
        return base

    text = _final_text(gm_output if isinstance(gm_output, dict) else None)
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip() or None
    npc_name = str(social.get("npc_name") or "the NPC").strip()
    sid = _scene_id(scene)
    if not sid:
        return base

    has_hooks, probe_kind = _text_indicates_new_information(
        text, scene_id=sid, npc_id=npc_id, npc_name=npc_name if npc_name else None
    )
    if not has_hooks:
        return base
    if _escalation_blocks_fact_repair_from_narration(social, probe_kind, text):
        return base

    repairs: List[str] = []
    base["narration_state_mismatch_detected"] = True
    rk = str(social.get("reply_kind") or "").strip().lower()
    if rk == "refusal":
        base["mismatch_kind"] = f"refusal_or_empty_payload_vs_narration:{probe_kind}"
    else:
        base["mismatch_kind"] = f"empty_social_payload_vs_narration:{probe_kind}"

    base["emergent_actor_hint_detected"] = _emergent_actor_hint_detected(
        text, npc_id=npc_id, npc_name=npc_name if npc_name else None
    )

    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), dict) else None
    w = world if isinstance(world, dict) else {}

    extracted = extract_actionable_social_leads(
        scene_id=sid,
        npc_id=npc_id,
        topic_payload=topic,
        social_resolution=resolution,
        player_facing_text=text,
        scene=scene if isinstance(scene, dict) else None,
        session=session,
        primary_clue_id=str(resolution.get("clue_id") or "").strip() or None,
        extraction_pass="full",
        narration_text_is_reconciled=True,
    )

    syn_topic_id = f"narration_repair_{slugify(sid)}_{slugify(probe_kind)}"

    if extracted:
        repairs.append("structured_from_extracted_actionable_leads")
        L0 = extracted[0]
        first_id = str(L0.get("lead_id") or "").strip()
        first_label = str(L0.get("label") or "").strip()
        if first_id:
            resolution["clue_id"] = first_id
        resolution.setdefault("discovered_clues", [])
        dc = resolution.get("discovered_clues")
        if isinstance(dc, list):
            if first_label and first_label not in dc:
                dc.append(first_label)
        soc = resolution.setdefault("social", {})
        if isinstance(soc, dict):
            tp: Dict[str, Any] = {
                "id": syn_topic_id,
                "text": first_label or text[:200],
                "clue_text": first_label or text[:200],
                "clue_id": first_id or None,
            }
            ts = str(L0.get("target_scene_id") or "").strip()
            tn = str(L0.get("target_npc_id") or "").strip()
            tr = str(L0.get("rumor_text") or "").strip()
            if ts:
                tp["leads_to_scene"] = ts
            if tn:
                tp["leads_to_npc"] = tn
            if tr:
                tp["leads_to_rumor"] = tr
            soc["topic_revealed"] = tp
        base["mismatch_repair_applied"] = "extracted_actionable_leads"
    else:
        # PR-AJ: narration may communicate a consequence; it is not provenance.
        # Contextual extraction remains available for non-authoritative continuity
        # (see remember_recent_contextual_leads). It must not mint gameplay
        # authority when no authorized structured/scene-anchored lead exists.
        repairs.append("fail_closed_no_authoritative_provenance")
        base["mismatch_repair_applied"] = "fail_closed_no_authoritative_provenance"
        base["prose_derived_authority_suppressed"] = True
        base["mismatch_repairs_applied"] = repairs
        nmeta = resolution.setdefault("metadata", {})
        if isinstance(nmeta, dict):
            nmeta["narration_state_consistency"] = dict(base)
        return base

    prior_reply = str((resolution.get("social") or {}).get("reply_kind") or "")
    soc2 = resolution.setdefault("social", {})
    if isinstance(soc2, dict):
        new_rk = _infer_upgraded_reply_kind(prior=prior_reply, text=text)
        if new_rk != prior_reply:
            soc2["reply_kind"] = new_rk
            repairs.append("reply_kind_upgraded_from_refusal")

    resolution["success"] = True
    repairs.append("success_set_true")

    hint = str(resolution.get("hint") or "")
    low_hint = hint.lower()
    if _NO_NEW_INFO_SNIPPET in low_hint:
        resolution["hint"] = (
            f"Player spoke with {npc_name}. Narration introduced investigatively relevant detail; "
            f"treat as partial answer or redirect consistent with the spoken reply."
        )
        repairs.append("engine_hint_no_new_info_replaced")
    elif hint.strip():
        resolution["hint"] = (
            hint.rstrip()
            + " Engine note: narration carried hooks; state upgraded to match (narration/state consistency)."
        )
        repairs.append("engine_hint_appended_reconcile_note")

    if _scrub_gm_debug_no_new_info_claim(gm_output if isinstance(gm_output, dict) else None):
        repairs.append("gm_debug_notes_scrubbed")

    if isinstance(gm_output, dict):
        dbg_after = gm_output.get("debug_notes") if isinstance(gm_output.get("debug_notes"), str) else ""
        if "narration_state_consistency:repaired" not in (dbg_after or ""):
            extra = "narration_state_consistency:repaired_empty_payload_to_match_text"
            gm_output["debug_notes"] = (dbg_after + " | " if dbg_after else "") + extra

    added_texts = apply_socially_revealed_leads(
        session,
        sid,
        w,
        resolution,
        player_facing_text=text,
        player_facing_text_is_reconciled=True,
        scene=scene,
    )
    repairs.append("canonical_social_lead_landing")

    meta = resolution.setdefault("metadata", {})
    if isinstance(meta, dict):
        ll = meta.get("lead_landing") if isinstance(meta.get("lead_landing"), dict) else {}
        merged_ll = dict(ll)
        merged_ll["narration_mismatch_repair"] = True
        meta["lead_landing"] = merged_ll

    base["mismatch_repairs_applied"] = repairs
    base["repaired_discovered_clue_texts"] = list(added_texts)
    nmeta = resolution.setdefault("metadata", {})
    if isinstance(nmeta, dict):
        nmeta["narration_state_consistency"] = dict(base)
    return base


def detect_narration_state_mismatch(
    *,
    resolution: dict | None,
    gm_output: dict | None,
    session: dict,
    scene: dict,
    world: dict | None = None,
) -> dict:
    """Backward-compatible alias for :func:`reconcile_final_text_with_structured_state`."""
    return reconcile_final_text_with_structured_state(
        session=session,
        scene=scene,
        world=world,
        resolution=resolution,
        gm_output=gm_output,
    )


_PLAYER_STAYED_RE = re.compile(
    r"\b(?:you|your)\s+(?:stay|remain|do\s+not\s+leave|aren't\s+leaving)\b",
    re.IGNORECASE,
)
_PLAYER_DEPARTED_RE = re.compile(
    r"\b(?:you|your)\s+(?:leave|left|head|follow|set\s+(?:out|off)|take\s+the|"
    r"act\s+on\s+that|position\s+changes|walk|depart|enter|arrive|"
    r"turn\s+away|make\s+(?:your\s+)?way|start\s+(?:back|toward|towards|for)|"
    r"return(?:s|ed)?)\b",
    re.IGNORECASE,
)
_FALSE_ARRIVAL_RE = re.compile(
    r"\b(?:you|your)\s+(?:arrive|arrived|enter|entered|return(?:s|ed)?\s+to|"
    r"are\s+(?:now\s+)?(?:at|in|back))\b",
    re.IGNORECASE,
)
# Engine arrival-stock phrasing that asserts a spatial change without you/arrive verbs.
_IMPLIED_TRANSITION_STOCK_RE = re.compile(
    r"\bthe new ground shows itself\b",
    re.IGNORECASE,
)


def _resolution_supports_travel_success(resolution: dict | None) -> bool:
    """True only when authoritative gameplay state performed a scene transition."""
    if not isinstance(resolution, dict):
        return False
    if resolution.get("resolved_transition") is True:
        return True
    state_changes = resolution.get("state_changes")
    if isinstance(state_changes, dict):
        if (
            state_changes.get("scene_transition_occurred")
            or state_changes.get("scene_changed")
            or state_changes.get("arrived_at_scene")
        ):
            return True
    return False


def apply_stay_leave_narration_agreement_to_gm(
    gm_output: dict | None,
    *,
    resolution: dict | None = None,
    origin_scene_id: str | None = None,
) -> dict | None:
    """PR-AE local guarantee: stay/leave/pursuit narration must match the authoritative outcome.

    Does not invent destinations or NPCs. Uses only the resolved action result.
    """
    if not isinstance(gm_output, dict) or not isinstance(resolution, dict):
        return gm_output
    text = str(gm_output.get("player_facing_text") or "").strip()
    kind = str(resolution.get("kind") or "").strip().lower()
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    lane = str(meta.get("parser_lane") or "")
    intent = str(meta.get("intent") or "")
    prae_turn = lane in {
        "explicit_stay",
        "legacy_follow_exit_match",
        "unresolved_actionable_travel",
        "actionable_stay_leave_or_pursuit",
        "authored_exit_resolution",
    } or intent in {"stay", "leave_or_pursuit"}
    stay_turn = lane == "explicit_stay" or intent == "stay"
    resolved = resolution.get("resolved_transition") is True
    target_id = str(resolution.get("target_scene_id") or "").strip()
    origin = str(origin_scene_id or "").strip()
    tags = list(gm_output.get("tags") or []) if isinstance(gm_output.get("tags"), list) else []

    def _mark() -> None:
        if "stay_leave_narration_agreement" not in tags:
            tags.append("stay_leave_narration_agreement")
        gm_output["tags"] = tags

    if stay_turn:
        if _PLAYER_DEPARTED_RE.search(text):
            gm_output["player_facing_text"] = "You remain where you are."
            _mark()
        return gm_output

    departed = bool(resolved and target_id and (not origin or target_id != origin))
    if prae_turn and departed:
        if not text or _PLAYER_STAYED_RE.search(text) or not _PLAYER_DEPARTED_RE.search(text):
            gm_output["player_facing_text"] = "You act on that decision and leave along the available path."
            _mark()
        return gm_output

    if kind in {"travel", "scene_transition"} and not _resolution_supports_travel_success(resolution):
        if (
            _FALSE_ARRIVAL_RE.search(text)
            or _PLAYER_DEPARTED_RE.search(text)
            or _IMPLIED_TRANSITION_STOCK_RE.search(text)
        ):
            gm_output["player_facing_text"] = "That destination is not available from here."
            _mark()
    return gm_output


_STUB_SCENE_PHRASE = "blank scene awaiting definition"
_UNGROUNDED_DESTINATION_STOCK = (
    "nothing new locks in yet; you keep the scene's weight without stepping backward.",
    "the exchange doesn't resolve cleanly—you hold your ground while the moment stays sharp between you.",
    "you get an immediate read on what is there",
    "the scene answers with an immediate change",
)


def scene_has_usable_destination_content(scene: dict | None) -> bool:
    """True when an authored destination has more than the default stub placeholder."""
    inner = _scene_inner(scene or {})
    summary = str(inner.get("summary") or "").strip()
    if summary and _STUB_SCENE_PHRASE not in summary.lower():
        return True
    facts = inner.get("visible_facts") or []
    if isinstance(facts, list):
        for fact in facts:
            text = str(fact or "").strip()
            if text and _STUB_SCENE_PHRASE not in text.lower():
                return True
    return False


def apply_destination_arrival_realization_to_gm(
    gm_output: dict | None,
    *,
    resolution: dict | None = None,
    scene: dict | None = None,
    player_text: str = "",
) -> dict | None:
    """PR-AF local guarantee: a defined destination must not present the stub placeholder.

    Uses existing arrival/observe fallback helpers. Does not invent NPCs, exits, or fate.
    Does not replace PR-AE stock movement lines that already agree with departure.
    """
    if not isinstance(gm_output, dict) or not isinstance(resolution, dict):
        return gm_output
    text = str(gm_output.get("player_facing_text") or "").strip()
    low = text.lower()
    ungrounded = _STUB_SCENE_PHRASE in low or any(stock in low for stock in _UNGROUNDED_DESTINATION_STOCK)
    if not ungrounded:
        return gm_output
    if not scene_has_usable_destination_content(scene):
        return gm_output

    from game.diegetic_fallback_narration import (
        render_observe_perception_fallback_line,
        render_travel_arrival_fallback_line,
    )

    kind = str(resolution.get("kind") or "").strip().lower()
    travel_succeeded = _resolution_supports_travel_success(resolution)
    seed = str(player_text or resolution.get("prompt") or "destination").strip() or "destination"
    if kind in {"scene_transition", "travel"} and not travel_succeeded:
        # Unresolved travel is not an arrival. Scene stock must not mint a transition.
        return gm_output
    if travel_succeeded:
        replacement = render_travel_arrival_fallback_line(scene, seed_key=f"praf|arr|{seed}")
    else:
        replacement = render_observe_perception_fallback_line(
            scene,
            seed_key=f"praf|obs|{seed}",
            player_text=str(player_text or ""),
            resolution=resolution,
        )
    if not replacement:
        return gm_output
    gm_output["player_facing_text"] = replacement
    tags = list(gm_output.get("tags") or []) if isinstance(gm_output.get("tags"), list) else []
    if "destination_arrival_realization" not in tags:
        tags.append("destination_arrival_realization")
    gm_output["tags"] = tags
    return gm_output
