"""Bounded, read-only intention interpretation over existing public context.

Returns the existing conversation contract. Execution proposals still cross the
normal interpretation bridge and authoritative resolver. No persistence or AI.
"""
from __future__ import annotations

import os
import re

GATE = "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE"


def decide(player_text, *, scene, world, session):
    from game.authored_consequences import enabled_for_session
    if os.environ.get(GATE) != "1" or not enabled_for_session(session or {}):
        return None
    from game.conversational_orchestration import (
        ConversationalDecision, ConversationalDecisionCategory as C, _operation_record,
    )
    from game.player_interpretation_bridge import visible_catalog

    text = re.sub(r"\s+", " ", player_text or "").strip()
    low = text.casefold().replace("’", "'")
    current = (scene or {}).get("scene", scene or {})

    def result(category, reason, message="", operation=None, target=None):
        return ConversationalDecision(
            category=category, primary_intention=text, intent_family="player_initiative",
            proposed_operation=operation, proposed_target=target,
            proposed_record=_operation_record(operation=operation, target_id=target, player_text=text)
                if operation and target else None,
            requires_authoritative_execution=category == C.EXECUTE,
            confidence=0.9 if category != C.CLARIFY else 0.4,
            ambiguity="unresolved_target" if category == C.CLARIFY else None,
            missing_information=["target"] if category == C.CLARIFY else [],
            reason="initiative_" + reason, player_facing_text=message,
        )

    # Never adopt the player's presupposition as a world fact.
    if re.search(r"\b(gm\s+notes?|hidden\s+(?:facts?|clues?|information)|secret\s+(?:future|events?|plans?|motivations?))\b", low):
        return result(C.DECLINE, "hidden_information", "You can ask about what you have seen or learned; concealed facts remain unknown.")
    if re.search(r"\b(teleport|rewrite\s+reality|delete\s+the\s+world|become\s+a\s+god)\b", low):
        return result(C.DECLINE, "impossible", "That cannot be carried out with your available abilities and routes.")
    if re.search(r"\b(?:order|command|force|make)\b.*\b(?:guards?|watch|soldiers?)\b|\b(?:send|dispatch)\b.*\b(?:patrol|search\s+party|soldiers?)\b", low):
        return result(C.DECLINE, "npc_authority", "You cannot decide the watch's deployment. You can speak to a guard here or review what you have already reported.")
    if re.search(r"\b(?:follow|pursue|chase)\b.*\b(?:tracks?|footprints?|prints|whoever)\b", low):
        return result(C.DECLINE, "unsupported_pursuit", "No onward pursuit is established from these prints. You can examine accessible evidence or use a known route; no destination or encounter has been determined.")

    memory = bool(re.search(
        r"\b(?:what\s+(?:do\s+(?:i|we)\s+know|(?:have|did)\s+(?:i|we)|happened|did\s+(?:our|the)\s+survey)|"
        r"tell\s+me\s+what|remind\s+me|who\s+(?:have|did)\s+(?:i|we)\s+(?:told|tell)|"
        r"(?:have|has|was|did)\b.*\b(?:warn|warned|warning|report)|check\s+(?:whether|if)|"
        r"what\s+did\s+the\s+survey)\b", low))
    if memory:
        from game.journal import build_player_journal
        # Journal trace annotations are local to this detached copy, never truth.
        import copy
        journal = build_player_journal(copy.deepcopy(session or {}), world, scene)
        facts = list(dict.fromkeys(journal.get("discovered_clues", []) + journal.get("known_facts", [])))
        from game.authored_consequences import FIXTURE
        import json
        definitions = json.loads(FIXTURE.read_text(encoding="utf-8"))
        flags = (world or {}).get("world_state", {}).get("flags", {})
        # Only committed effects publish their existing authored disclosures.
        committed = [a["consequence"]["text"] for actions in definitions.values() for a in actions
                     if all(flags.get(k) is True for k in a["consequence"]["set_flags"])]
        message = " ".join(facts + committed) or "You have not established any discoveries about that yet."
        if re.search(r"\b(?:guards?|watch|report|warning|warned|search)\b", low):
            message += " You have no established report of further guard activity."
        return result(C.ANSWER, "known_information", message)

    # Match an attempt to the finite server-authored choice surface. The bridge
    # revalidates scene, enrollment and prerequisites before the resolver runs.
    verbs = {"record": r"\b(?:record|log|write\s+down)\b", "report": r"\b(?:report|warn|give)\b",
             "survey": r"\b(?:survey)\b"}
    attempt = re.match(r"^(?:(?:please|can i|could i|i want to|i will|i|we|let me)\s+)*(record|log|write down|report|warn|give|survey)\b", low)
    requested = next((v for v, pattern in verbs.items() if attempt and re.search(pattern, attempt.group(1))), None)
    if requested and not re.search(r"\b(?:if|unless|then|and|don't|do\s+not)\b", low):
        from game.affordances import _affordance_passes_conditions
        candidates = []
        for action in current.get("actions", []):
            if not isinstance(action, dict) or "consequence" not in action:
                continue
            label = action.get("label", "").casefold()
            label_verb = "record" if re.search(verbs["record"], label) else "report" if re.search(verbs["report"], label) else "survey"
            # The action verb is not evidence of its subject: "report a bug"
            # must never select a patrol report merely by sharing "report".
            nouns = (set(re.findall(r"[a-z]+", label)) & {"survey", "trail", "watch", "patrol", "report"}) - {requested}
            if label_verb == requested and nouns & set(re.findall(r"[a-z]+", low)):
                candidates.append(action)
        available = [a for a in candidates if _affordance_passes_conditions(a, current.get("id", ""), session, world)]
        if len(available) == 1:
            return result(C.EXECUTE, "authored_choice", operation="CUSTOM", target=available[0]["id"])
        if candidates:
            return result(C.DECLINE, "unavailable_choice", "That choice cannot be taken here now. Review what you have already done or choose an available continuation.")
        return result(C.CLARIFY, "unknown_choice_subject", "Which known evidence or available choice do you mean? Nothing has been attempted.")

    inspect = re.search(r"\b(?:inspect|examine|reexamine|scrutinize|study|read|look\s+at|take\s+(?:another|a)\s+look|check)\b", low)
    speak = re.search(r"\b(?:speak|talk|ask|question)\b", low)
    if (inspect or speak) and re.search(r"\b(?:if|unless|provided|while|then|and|don't|do\s+not|never)\b", low):
        return result(C.CLARIFY, "qualified_attempt", "What single action do you want to attempt now? Nothing has been attempted.")
    if re.fullmatch(r"(?:can\s+i\s+)?(?:check\s+it\s+again|ask\s+them\s+about\s+it|see\s+what\s+happened|go\s+back\s+there|follow\s+up\s+on\s+what\s+happened)[.!?]*", low):
        return result(C.CLARIFY, "ambiguous_reference", "Which person, place, or piece of evidence do you mean?")
    if not inspect and not speak:
        return None
    catalog = visible_catalog(scene, world)
    operation = "INSPECT" if inspect else "ASK"
    kinds = {"inspect_target", "perceive_target"} if inspect else {"npc"}

    def words(value):
        tokens = re.findall(r"[a-z]+", value.casefold())
        synonyms = {"tracks": "track", "footprints": "print", "footprint": "print", "prints": "print",
                    "ground": "mud", "notices": "notice", "guards": "guard"}
        return {synonyms.get(t, t) for t in tokens}

    input_words = words(text)
    matches = []
    for tid, item in catalog.items():
        if item["kind"] not in kinds:
            continue
        row = item["row"]
        names = [row.get("label", ""), row.get("name", ""), *row.get("aliases", [])]
        score = max((len(words(name)) for name in names if words(name) and words(name) <= input_words), default=0)
        if score:
            matches.append((score, tid))
    if matches:
        best = max(score for score, _ in matches)
        ids = {tid for score, tid in matches if score == best}
        if len(ids) == 1:
            return result(C.EXECUTE, "grounded_" + operation.lower(), operation=operation, target=ids.pop())
    if matches:
        return result(C.CLARIFY, "ambiguous_target", "Which of those visible targets do you mean?")
    if inspect and re.search(r"\b(?:tracks?|footprints?|prints|milestone)\b", low):
        return result(C.DECLINE, "inaccessible_target", "That evidence is not accessible in your current scene. Use a known route to return before examining it.")
    if speak and re.search(r"\b(?:watch|guards?)\b", low):
        names = [str(i["row"].get("name")) for i in catalog.values() if i["kind"] == "npc"]
        return result(C.CLARIFY, "ambiguous_addressee", "Who do you want to speak to" + (": " + ", ".join(names) if names else " when you reach them") + "?")
    return result(C.CLARIFY, "unknown_target", "Which visible person or object do you mean? Name the target so I can check the attempt.")
