"""Open-ended actions that existing mechanics can resolve from established facts.

Classification is read-only. It does not write session, world, or scene state.
Accepted proposals still cross the interpretation bridge and the exploration or
social resolver. Bounded improvisation is recognized and refused: a proposed
detail is not stored and is not treated as a later fact.

Climbing, jumping, and balancing have no configured check in the existing
skill-check owner. Those attempts are reported as missing mechanics. No
difficulty class is invented for them.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

FAMILY_OBSERVATION = "environmental_observation"
FAMILY_SEARCH = "physical_search"
FAMILY_SOCIAL = "social_initiative"
SUPPORTED_FAMILIES = (FAMILY_OBSERVATION, FAMILY_SEARCH, FAMILY_SOCIAL)

_STOP = {
    "a", "an", "the", "i", "we", "you", "to", "of", "on", "in", "at", "for", "and", "or",
    "my", "our", "some", "any", "this", "that", "these", "those", "it", "them", "there",
    "here", "up", "down", "over", "from", "with", "into", "onto", "want", "like", "please",
    "can", "could", "would", "should", "just", "really", "more", "again", "now", "then",
}
_CONSEQUENTIAL = re.compile(
    r"\b(?:secret\s+passage|hidden\s+tunnel|secret\s+tunnel|concealed\s+door|"
    r"buried\s+treasure|hidden\s+treasure|new\s+(?:npc|quest|faction|enemy)|"
    r"summon\s+(?:a|an|the)|create\s+(?:a|an|the)\s+(?:tunnel|passage|npc|quest))\b",
    re.I,
)
_CLIMB = re.compile(r"\b(?:climb|clamber|scale|jump\s+onto|balance\s+on|scramble\s+up)\b", re.I)
_MANIPULATE = re.compile(
    r"\b(?:search|move\b.*\b(?:aside|away)|shove\s+aside|shift|pry|dig|look\s+under|check\s+under|"
    r"underneath|beneath|lift\s+(?:the|some|a))\b",
    re.I,
)
_SOCIAL = re.compile(r"\b(?:persuade|convince|urge|plead|appeal\s+to|implore)\b", re.I)
_OBSERVE = re.compile(
    r"\b(?:see|peer|scan|view|gaze|look\s+(?:down|farther|ahead|along|out|over)|"
    r"farther\s+down|from\s+up\s+here|better\s+view)\b",
    re.I,
)
_DETAIL = re.compile(r"\b(?:handhold|texture|rough\s+surface|stable\s+grip|footing)\b", re.I)
_READONLY = re.compile(
    r"^\s*(?:what\s+(?:can|do)\s+(?:i|we)\s+see|what\s+is\s+visible|what\s+do\s+(?:i|we)\s+know|"
    r"where\s+am\s+i|where\s+are\s+we|what\s+does\s+the\s+(?:notice\s+board|sign|board)\s+say)\b",
    re.I,
)
_AMBIGUOUS = re.compile(
    r"^\s*(?:please\s+)?(?:climb|move|shift|ask|look)\s+(?:that|it|them|over\s+there)\b",
    re.I,
)
_ELEVATED = re.compile(r"\b(?:from\s+up\s+here|from\s+above|once\s+i(?:'m| am)\s+up)\b", re.I)
_PURPOSE = re.compile(r"\bto\s+(?:get|see|have|find|make|take|reach)\b", re.I)
_PROVIDER_GATE = "ASHEN_GP_PROVIDER_INTERPRETATION"
_PROVIDER_REQUESTS = 0
_PROVIDER_TOKENS = 0
_PROVIDER_LOG: list[dict[str, Any]] = []
_MAX_REQUESTS = 8
_MAX_TOKENS = 16000


def provider_budget_open() -> bool:
    return (
        os.environ.get(_PROVIDER_GATE) == "1"
        and os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS", "").strip() != "1"
        and _PROVIDER_REQUESTS < _MAX_REQUESTS
        and _PROVIDER_TOKENS < _MAX_TOKENS
    )


def provider_usage() -> dict[str, Any]:
    return {
        "requests": _PROVIDER_REQUESTS,
        "tokens": _PROVIDER_TOKENS,
        "log": list(_PROVIDER_LOG),
    }


def _inner(scene: dict | None) -> dict:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    return inner if isinstance(inner, dict) else scene


def _tokens(text: str) -> set[str]:
    return {tok for tok in re.findall(r"[a-z0-9]+", (text or "").casefold()) if tok not in _STOP}


def _facts(scene: dict | None) -> list[str]:
    inner = _inner(scene)
    rows = []
    for key in ("visible_facts", "opening_seed_facts", "journal_seed_facts"):
        for item in inner.get(key) or []:
            if isinstance(item, str) and item.strip() and item not in rows:
                rows.append(item.strip())
    summary = str(inner.get("summary") or "").strip()
    if summary and summary not in rows:
        rows.append(summary)
    return rows


def _surfaces(scene: dict | None) -> list[dict[str, Any]]:
    inner = _inner(scene)
    rows = []
    for index, fact in enumerate(_facts(scene)):
        rows.append({
            "id": f"visible-fact-{index}",
            "label": fact,
            "kind": "fact",
            "tokens": _tokens(fact),
            "index": index,
            "text": fact,
        })
    for item in inner.get("interactables") or []:
        if not isinstance(item, dict) or item.get("hidden") or item.get("visible") is False:
            continue
        names = [str(item.get("label") or ""), str(item.get("id") or "").replace("_", " ")]
        names.extend(str(alias) for alias in item.get("aliases") or [])
        tokens = set()
        for name in names:
            tokens |= _tokens(name)
        rows.append({
            "id": str(item.get("id") or ""),
            "label": str(item.get("label") or item.get("id") or ""),
            "kind": "interactable",
            "tokens": tokens,
            "text": str(item.get("label") or ""),
        })
    return [row for row in rows if row["id"] and row["tokens"]]


def _match_surface(text: str, scene: dict | None) -> dict[str, Any] | None:
    words = _tokens(text)
    if not words:
        return None
    best = None
    best_score = 0
    for row in _surfaces(scene):
        overlap = len(words & row["tokens"])
        if overlap > best_score or (
            overlap == best_score and overlap and best is not None
            and row["kind"] == "interactable" and best["kind"] != "interactable"
        ):
            best = row
            best_score = overlap
    return best if best_score else None


def _npcs(scene, world) -> list[dict[str, Any]]:
    from game.player_interpretation_bridge import visible_catalog
    catalog = visible_catalog(scene, world)
    return [
        {"id": tid, "row": item["row"]}
        for tid, item in catalog.items() if item.get("kind") == "npc"
    ]


def _npc_match(text: str, npcs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    words = _tokens(text)
    scored = []
    for npc in npcs:
        row = npc["row"]
        phrases = [str(row.get("name") or ""), str(npc["id"]).replace("_", " ")]
        phrases.extend(str(alias) for alias in row.get("aliases") or [])
        best = 0
        for phrase in phrases:
            tokens = _tokens(phrase)
            if tokens and tokens <= words:
                best = max(best, len(tokens))
        if best:
            scored.append((best, npc))
    if not scored:
        return []
    top = max(score for score, _npc in scored)
    return [npc for score, npc in scored if score == top]


def _proposal(**kwargs) -> dict[str, Any]:
    base = {
        "category": "E",
        "family": "",
        "outcome": "cannot_attempt",
        "operation": None,
        "target": None,
        "message": "",
        "mechanic": None,
        "requires_check": False,
        "mutation": False,
    }
    base.update(kwargs)
    return base


def _elevated(session) -> bool:
    state = (session or {}).get("scene_state") if isinstance(session, dict) else None
    if not isinstance(state, dict):
        return False
    return bool(state.get("elevated_position"))


def classify(player_text: str, *, scene, world, session) -> dict[str, Any] | None:
    """Classify an unauthored attempt. Returns None when an existing path owns it."""
    text = re.sub(r"\s+", " ", player_text or "").strip()
    low = text.casefold().replace("’", "'")
    if not text:
        return None
    if _READONLY.search(low) and not _CLIMB.search(low) and not _MANIPULATE.search(low) and not _SOCIAL.search(low):
        facts = _facts(scene)
        message = " ".join(facts[:3]) if facts else "Nothing further is established from where you are."
        if re.search(r"\bwhere\s+am\s+i|where\s+are\s+we\b", low):
            inner = scene.get("scene", scene) if isinstance(scene, dict) else {}
            place = str((inner or {}).get("location") or (inner or {}).get("id") or "")
            if place:
                message = place + ". " + message
        if _ELEVATED.search(low) and not _elevated(session):
            message = "No elevated position is established. " + message
        return _proposal(category="RO", family="information", outcome="read_only", message=message)
    if _AMBIGUOUS.search(low):
        return _proposal(
            category="E", outcome="clarify",
            message="Which visible person, object, or direction do you mean? Nothing has been attempted.",
        )
    if re.search(r"\b(?:look for|search for|determine|which direction)\b", low) and not _CONSEQUENTIAL.search(low):
        opened = _open_ended(text, low, scene)
        if opened is not None:
            return opened
    if re.search(r"\bwait\b", low) and not re.search(r"\b(?:report|warn|tell the watch|give the watch)\b", low):
        return _proposal(
            category="RO", family=FAMILY_OBSERVATION, outcome="read_only",
            message="You wait. Nothing new approaches, and no encounter is created.",
        )
    if _CONSEQUENTIAL.search(low):
        return _proposal(
            category="D", family="world_expansion", outcome="needs_authority",
            message=(
                "That would establish new authoritative content. "
                "No passage, treasure, person, or destination has been created."
            ),
        )
    if _DETAIL.search(low) and not _CLIMB.search(low):
        known = _match_surface(text, scene)
        grounded = f" What is established: {known['text']}" if known and known["kind"] == "fact" else ""
        return _proposal(
            category="C", family="bounded_detail", outcome="not_promoted",
            message=(
                "That descriptive detail is not established and has not been added."
                + grounded
            ),
        )
    if _CLIMB.search(low):
        surface = _match_surface(_PURPOSE.split(text, maxsplit=1)[0], scene)
        if surface is None:
            return _proposal(
                category="D", family="physical_positioning", outcome="cannot_attempt",
                message=(
                    "That feature is not established. It has not been added, "
                    "and your position is unchanged."
                ),
            )
        return _proposal(
            category="E", family="physical_positioning", outcome="missing_mechanic",
            mechanic="climb",
            message=(
                f"{surface['label']} is here, but no climbing check is configured, "
                "so the climb is not resolved and your position is unchanged."
            ),
        )
    if _MANIPULATE.search(low) and not re.search(r"\b(?:route|direction|tracks?|prints|trail)\b", low):
        surface = _match_surface(_PURPOSE.split(text, maxsplit=1)[0], scene)
        if surface is None or (surface["kind"] == "fact" and not (_tokens(text) & _tokens(surface["text"]))):
            return _proposal(
                category="D", family=FAMILY_SEARCH, outcome="cannot_attempt",
                message=(
                    "Those objects are not established. Nothing was moved, "
                    "and no concealed contents were created."
                ),
            )
        return _proposal(
            category="B", family=FAMILY_SEARCH, outcome="success_without_discovery",
            operation="SEARCH_ESTABLISHED", target=surface["id"],
            mechanic="investigate",
            message="Search the established object without granting concealed contents.",
        )
    if _SOCIAL.search(low):
        present = _npcs(scene, world)
        named = _npc_match(text, present)
        pool = named or ([] if present and _tokens(text) & {"watch", "guard", "guards"} else present[:0])
        if not named and _tokens(text) & {"watch", "guard", "guards"}:
            pool = present
        if len(pool) == 1:
            return _proposal(
                category="B", family=FAMILY_SOCIAL, outcome="check",
                operation="PERSUADE", target=pool[0]["id"],
                mechanic="diplomacy", requires_check=True,
                message="Resolve persuasion with the existing diplomacy check. Do not grant compliance.",
            )
        if len(pool) > 1:
            return _proposal(
                category="E", family=FAMILY_SOCIAL, outcome="clarify",
                message="Which person here do you want to persuade? Nothing has been attempted.",
            )
        return _proposal(
            category="E", family=FAMILY_SOCIAL, outcome="cannot_attempt",
            message="Nobody here can be persuaded. No compliance or new order has been established.",
        )
    if _OBSERVE.search(low):
        rows = [row for row in _surfaces(scene) if row["kind"] == "fact"]
        surface = _match_surface(text, scene)
        if re.search(r"\b(?:farther|distance|view|road|ahead)\b", low):
            limited = next((row for row in rows if re.search(r"unclear|track continues|rainwater", row["text"], re.I)), None)
            if limited is not None:
                surface = limited
        if surface is None or surface.get("kind") != "fact":
            if not rows:
                return _proposal(
                    category="E", family=FAMILY_OBSERVATION, outcome="cannot_attempt",
                    message="Nothing established here matches that view. No distant encounter was created.",
                )
            surface = rows[0]
        return _proposal(
            category="B", family=FAMILY_OBSERVATION, outcome="success_without_discovery",
            operation="OBSERVE_FACT", target=surface["id"],
            mechanic="observe",
            message="Observe only the established fact.",
        )
    open_ended = _open_ended(text, low, scene)
    if open_ended is not None:
        return open_ended
    return None


def _trace_fact(scene):
    for row in _surfaces(scene):
        if row["kind"] == "fact" and re.search(r"\b(?:track|tracks|print|prints|trail|road)\b", row["text"], re.I):
            return row
    return None


def _open_ended(text: str, low: str, scene) -> dict[str, Any] | None:
    """Reasonable unauthored intentions. No new route, person, clue, or marker is created."""
    if re.search(r"\b(?:leave|place|set|make)\b", low) and re.search(r"\b(?:marker|cairn|blaze)\b", low):
        return _proposal(
            category="E", family="physical_positioning", outcome="missing_mechanic",
            mechanic="mark",
            message="No lasting marker can be placed with the actions available here. Nothing was left behind.",
        )
    if re.search(r"\bwait\b|\bwatch the\b", low) and not re.search(r"\b(?:report|warn|tell the watch|give the watch|look for|search for)\b", low):
        return _proposal(
            category="RO", family=FAMILY_OBSERVATION, outcome="read_only",
            message="You wait. Nothing new approaches, and no encounter is created.",
        )
    trace = _trace_fact(scene)
    pursuing = bool(re.search(r"\b(?:follow|pursue|chase|trace)\b", low) and re.search(r"\b(?:tracks?|footprints?|prints|trail)\b", low))
    seeking = bool(re.search(r"\b(?:look for|search for|determine|which direction|another route)\b", low))
    addressed = bool(re.search(r"\b(?:ask|tell|speak|talk)\b", low))
    if (pursuing or seeking) and not addressed:
        if trace is not None and (pursuing or re.search(r"\b(?:tracks?|prints|trail|direction|road|patrol|route)\b", low)):
            return _proposal(
                category="B", family=FAMILY_OBSERVATION, outcome="success_without_discovery",
                operation="OBSERVE_FACT", target=trace["id"], mechanic="observe",
                message="Observe the established trace. No onward route is established.",
            )
        return _proposal(
            category="E", family=FAMILY_OBSERVATION, outcome="cannot_attempt",
            message="Nothing established here answers that. No route, clue, or encounter was created.",
        )
    if re.search(r"\b(?:before|instead of|rather than|not yet)\b", low) and re.search(r"\b(?:report|survey)\b", low):
        return _proposal(
            category="RO", family="information", outcome="read_only",
            message="No survey or report has been chosen. You can keep examining what is already here.",
        )
    return None


def decision_fields(proposal: dict[str, Any], player_text: str) -> dict[str, Any]:
    """Map a proposal onto the existing conversational decision fields."""
    from game.conversational_orchestration import ConversationalDecisionCategory as C, _operation_record
    category = {
        "RO": C.ANSWER, "clarify": C.CLARIFY, "check": C.EXECUTE,
        "success_without_discovery": C.EXECUTE,
    }.get(proposal["outcome"], C.DECLINE if proposal["outcome"] != "read_only" else C.ANSWER)
    if proposal["outcome"] in {"success_without_discovery", "check"}:
        category = C.EXECUTE
    elif proposal["outcome"] in {"clarify"}:
        category = C.CLARIFY
    elif proposal["outcome"] in {"read_only"}:
        category = C.ANSWER
    else:
        category = C.DECLINE
    operation = proposal.get("operation")
    target = proposal.get("target")
    record = None
    if category == C.EXECUTE and operation and target:
        record = _operation_record(operation=operation, target_id=target, player_text=player_text)
        record["general_purpose"] = {
            "category": proposal["category"],
            "family": proposal["family"],
            "outcome": proposal["outcome"],
            "mechanic": proposal["mechanic"],
        }
    reason = "gp_" + (proposal["family"] or proposal["outcome"])
    return {
        "category": category,
        "operation": operation,
        "target": target,
        "record": record,
        "reason": reason,
        "message": proposal["message"],
        "execute": category == C.EXECUTE,
    }


def remember_general_resolution(session, scene_envelope, prompt: str, result: dict) -> None:
    """Record an investigation result on the existing ledger. No new clue is created."""
    if not isinstance(session, dict) or not isinstance(result, dict):
        return
    meta = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    publication = str(meta.get("engine_publication") or "").strip()
    if not publication:
        return
    from game.bounded_improvisation import ensure_bounded_improvisation_ledger
    ledger = ensure_bounded_improvisation_ledger(session)
    notes = ledger.setdefault("investigation_notes", [])
    scene_id = ""
    inner = scene_envelope.get("scene") if isinstance(scene_envelope, dict) else None
    if isinstance(inner, dict):
        scene_id = str(inner.get("id") or "")
    elif isinstance(scene_envelope, dict):
        scene_id = str(scene_envelope.get("id") or "")
    note = {
        "scene_id": scene_id,
        "prompt": str(prompt or "")[:180],
        "result": publication[:240],
        "turn": int(session.get("turn_counter") or 0),
    }
    if note not in notes:
        notes.append(note)
    del notes[:-24]


def fact_by_id(scene, fact_id: str) -> str:
    if not str(fact_id or "").startswith("visible-fact-"):
        return ""
    try:
        index = int(str(fact_id).rsplit("-", 1)[-1])
    except ValueError:
        return ""
    facts = _facts(scene)
    if index < 0 or index >= len(facts):
        return ""
    return facts[index]


def exploration_outcome(scene_envelope, normalized_action, *, prompt, action_id, label):
    """Authoritative no-discovery result for a validated general-purpose exploration action."""
    from game.models import ExplorationEngineResult
    meta = normalized_action.get("metadata") if isinstance(normalized_action, dict) else None
    if not isinstance(meta, dict):
        return None
    family = str(meta.get("general_purpose_family") or "")
    if family not in {FAMILY_OBSERVATION, FAMILY_SEARCH}:
        return None
    scene = _inner(scene_envelope)
    target = str(normalized_action.get("target_id") or normalized_action.get("id") or "")
    publication = ""
    kind = "observe" if family == FAMILY_OBSERVATION else "investigate"
    if family == FAMILY_OBSERVATION:
        fact = fact_by_id(scene_envelope, target)
        if not fact:
            publication = "That view is not established. No distant encounter was created."
            success = False
            outcome = "cannot_attempt"
        else:
            prefix = ""
            if meta.get("elevated_claim") and not meta.get("elevated_established"):
                prefix = "No elevated position is established, so this is the view from where you already are. "
            publication = prefix + fact + " Nothing farther is established."
            if re.search(r"\b(?:follow|pursue|chase|trace|look for|search for|unnoticed|marker|direction|route)\b", prompt or "", re.I):
                publication += " No new route, hiding place, or marker was created."
            success = True
            outcome = "success_without_discovery"
    else:
        surface = next((row for row in _surfaces(scene_envelope) if row["id"] == target), None)
        if surface is None:
            publication = "That object is not established. Nothing was moved or created."
            success = False
            outcome = "cannot_attempt"
        else:
            label_text = surface["label"] if surface["kind"] == "interactable" else "that"
            publication = (
                f"You check {label_text}. Nothing concealed is established there. "
                "No passage, treasure, or new evidence is revealed."
            )
            success = True
            outcome = "success_without_discovery"
    result = ExplorationEngineResult(
        kind=kind,
        action_id=action_id,
        label=label,
        prompt=prompt,
        success=success,
        resolved_transition=False,
        target_scene_id=None,
        clue_id=None,
        discovered_clues=[],
        world_updates=None,
        state_changes={"general_purpose_family": family, "action_outcome": outcome},
        hint="General-purpose resolution used only established facts. Do not add discoveries.",
        metadata={
            "general_purpose_family": family,
            "action_outcome": outcome,
            "engine_publication": publication,
            "general_purpose_category": "B" if success else "E",
            "skip_unrelated_clue_discovery": True,
            "publication_contract": "FINAL_ENGINE_RESPONSE",
            "skip_primary_narration": True,
        },
    )
    return result.to_dict()


def resolve_social_check_publication(resolution, character, session) -> str:
    """Finish a pending diplomacy check without granting NPC compliance.

    The difficulty and skill come from the existing social check request.
    The roll uses the existing deterministic skill-check owner.
    """
    if not isinstance(resolution, dict):
        return ""
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    family = str(meta.get("general_purpose_family") or social.get("general_purpose_family") or "")
    if family != FAMILY_SOCIAL:
        return ""
    check = resolution.get("check_request") if isinstance(resolution.get("check_request"), dict) else {}
    skill = str(check.get("skill") or check.get("check_type") or "")
    difficulty = check.get("difficulty")
    npc_name = str(social.get("npc_name") or "them")
    if not skill or not isinstance(difficulty, int):
        text = (
            f"No configured persuasion check is available for {npc_name}. "
            "No new order or compliance is established."
        )
        meta = dict(meta)
        meta["engine_publication"] = text
        meta["action_outcome"] = "missing_mechanic"
        meta["publication_contract"] = "UNSUPPORTED_ACTION"
        meta["skip_primary_narration"] = True
        resolution["metadata"] = meta
        resolution["success"] = False
        return text
    from game.skill_checks import resolve_skill_check
    scene_id = str((session or {}).get("active_scene_id") or "")
    turn = int((session or {}).get("turn_counter") or 0)
    rolled = resolve_skill_check(skill, int(difficulty), character or {}, {
        "seed_parts": [turn, scene_id, FAMILY_SOCIAL, str(social.get("npc_id") or ""), skill, str(difficulty)],
    })
    outcome = "mechanical_success" if rolled["success"] else "mechanical_failure"
    text = (
        f"{skill.title()} check: d20 {rolled['roll']} + {rolled['modifier']} = {rolled['total']} "
        f"against DC {rolled['difficulty']}. The attempt "
        f"{'succeeds' if rolled['success'] else 'fails'}. "
        f"No new order or compliance is established for {npc_name}."
    )
    resolution["skill_check"] = rolled
    resolution["success"] = bool(rolled["success"])
    meta = dict(meta)
    meta["general_purpose_family"] = FAMILY_SOCIAL
    meta["action_outcome"] = outcome
    meta["engine_publication"] = text
    meta["npc_compliance_granted"] = False
    meta["publication_contract"] = "FINAL_ENGINE_RESPONSE"
    meta["skip_primary_narration"] = True
    resolution["metadata"] = meta
    state = dict(resolution.get("state_changes") or {})
    state["action_outcome"] = outcome
    state["npc_compliance_granted"] = False
    resolution["state_changes"] = state
    return text


def validate_provider_proposal(proposal: Any, *, scene, world) -> dict[str, Any]:
    """Accept only a family hint that still has to be grounded. Never an outcome."""
    if not isinstance(proposal, dict):
        return {"accepted": False, "reason": "malformed"}
    forbidden = {
        "success", "roll", "dc", "difficulty", "discovered_clues", "world_updates",
        "npc_complies", "compliance", "hidden_fact", "gm_notes", "player_facing_text",
    }
    if forbidden & set(proposal):
        return {"accepted": False, "reason": "invented_outcome_or_hidden_field"}
    family = str(proposal.get("family") or "")
    if family not in SUPPORTED_FAMILIES:
        return {"accepted": False, "reason": "unsupported_family"}
    target = str(proposal.get("target_ref") or "")
    if target:
        known = {row["id"] for row in _surfaces(scene)}
        known.update(npc["id"] for npc in _npcs(scene, world))
        if target not in known:
            return {"accepted": False, "reason": "invented_target"}
    blob = json.dumps(proposal).casefold()
    if "sentinel_" in blob or "hidden_facts" in blob:
        return {"accepted": False, "reason": "hidden_information"}
    return {"accepted": True, "reason": "family_only", "family": family, "target_ref": target}


def proposal_from_interpretation_record(record: Any) -> dict[str, Any]:
    """Reduce an existing interpreter record to a family hint. Outcomes are dropped."""
    if not isinstance(record, dict):
        return {}
    components = record.get("action_components")
    if not isinstance(components, list) or len(components) != 1 or not isinstance(components[0], dict):
        return {"family": "", "target_ref": ""}
    operation = str(components[0].get("operation_class") or "").upper()
    family = {
        "PERCEIVE": FAMILY_OBSERVATION,
        "INSPECT": FAMILY_SEARCH,
        "ASK": FAMILY_SOCIAL,
    }.get(operation, "")
    return {"family": family, "target_ref": str(components[0].get("target_ref") or "")}


def consider_provider_record(record: Any, *, player_text: str, scene, world, session) -> dict[str, Any]:
    """Validate a provider record against deterministic grounding. Does not save."""
    global _PROVIDER_REQUESTS, _PROVIDER_TOKENS
    proposal = proposal_from_interpretation_record(record)
    verdict = validate_provider_proposal(proposal, scene=scene, world=world)
    grounded = classify(player_text, scene=scene, world=world, session=session)
    if verdict["accepted"] and (grounded is None or grounded.get("family") != verdict.get("family")):
        verdict = {"accepted": False, "reason": "deterministic_disagreement", "family": verdict.get("family")}
    _PROVIDER_REQUESTS += 1
    _PROVIDER_LOG.append({
        "player_text": player_text,
        "result": "accepted" if verdict["accepted"] else "rejected",
        "reason": verdict["reason"],
        "proposal": proposal,
        "committed": False,
    })
    return verdict
