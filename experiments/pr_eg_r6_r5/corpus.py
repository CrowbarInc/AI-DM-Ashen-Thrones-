"""Frozen end-to-end dialogue situations for PR-EG-R6-R5.

Ground truth is authored here, before any provider call. Labels describe the
player-facing answer a host may already authorize. They are not engine output.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy

PARTITIONS = ("development", "validation", "holdout")
CLASSES = (
    "DIRECT",
    "PARTIAL",
    "RELATED_NONANSWER",
    "UNKNOWN",
    "CLARIFICATION_REQUIRED",
    "RESTRICTED",
)


def _role(name: str, value: str, evidence: str | None = None) -> dict:
    return {"name": name, "value": value, "entity_id": "", "evidence": evidence or value}


def _prop(predicate: str, evidence: str, roles: list[dict], requested: str = "", epistemic: str = "npc_knowledge") -> dict:
    return {
        "predicate": predicate,
        "predicate_evidence": evidence,
        "subject": "",
        "subject_evidence": "",
        "object": "",
        "object_evidence": "",
        "missing_argument": "",
        "temporal": "",
        "spatial": "",
        "epistemic": epistemic,
        "negated": False,
        "prior_reference": "",
        "roles": roles,
        "requested_role": requested,
    }


def _topic(ident: str, text: str, *, epistemic: str = "npc_knowledge", secret: bool = False) -> dict:
    row = {"id": ident, "text": text, "epistemic": epistemic}
    if secret:
        row["disclosure"] = "secret"
        row["secret"] = True
    return row


def _npc(ident: str, name: str, topics: list[dict]) -> dict:
    return {
        "id": ident,
        "name": name,
        "role": "local",
        "aliases": [],
        "availability": "available",
        "disposition": "wary",
        "topics": topics,
    }


def _need(text: str, span: str, where: str) -> None:
    if span and span.casefold() not in text.casefold():
        raise ValueError(f"{span!r} is not in {where}: {text}")


def _turn(
    conversation: str,
    index: int,
    player: str,
    *,
    act: str,
    addressee: str,
    answer_class: str,
    tags: list[str],
    allowed: list[str] | None = None,
    forbidden: list[str] | None = None,
    distractors: list[str] | None = None,
    hedge_any: list[str] | None = None,
    eligible: list[str] | None = None,
    correspondence: dict[str, str] | None = None,
    predicate: str = "",
    predicate_evidence: str = "",
    roles: list[tuple[str, str]] | None = None,
    requested_role: str = "",
    epistemic: str = "npc_knowledge",
    sources: dict[str, dict] | None = None,
    referent: dict | None = None,
    complication: str = "",
) -> dict:
    if answer_class not in CLASSES:
        raise ValueError(answer_class)
    role_rows = [_role(name, value) for name, value in (roles or [])]
    for role in role_rows:
        _need(player, role["evidence"], player)
    if predicate_evidence:
        _need(player, predicate_evidence, player)
    proposition = None
    if predicate:
        proposition = _prop(predicate, predicate_evidence or predicate, role_rows, requested_role, epistemic)
    source_props = {}
    for source_id, spec in (sources or {}).items():
        source_roles = [_role(name, value) for name, value in spec["roles"]]
        for role in source_roles:
            _need(spec["text"], role["evidence"], spec["text"])
        _need(spec["text"], spec["evidence"], spec["text"])
        source_props[source_id] = _prop(
            spec["predicate"],
            spec["evidence"],
            source_roles,
            spec.get("requested", ""),
            spec.get("epistemic", epistemic),
        )
        source_props[source_id]["_source_text"] = spec["text"]
    return {
        "id": f"{conversation}t{index:02d}",
        "conversation": conversation,
        "index": index,
        "player": player,
        "act": act,
        "addressee": addressee,
        "answer_class": answer_class,
        "tags": list(tags),
        "allowed": list(allowed or []),
        "forbidden": list(forbidden or []),
        "distractors": list(distractors or []),
        "hedge_any": list(hedge_any or []),
        "eligible_source_ids": list(eligible or []),
        "correspondence": dict(correspondence or {}),
        "predicate": predicate,
        "requested_role": requested_role,
        "roles": [{"name": name, "value": value} for name, value in (roles or [])],
        "proposition": proposition,
        "source_propositions": source_props,
        "referent": referent or {"select": "new"},
        "complication": complication,
        "clarification_required": answer_class == "CLARIFICATION_REQUIRED",
    }


def _family(ident: str, partition: str, title: str, npcs: list[dict], turns: list[dict]) -> dict:
    return {
        "id": ident,
        "partition": partition,
        "title": title,
        "summary": f"{title}. " + " and ".join(npc["name"] for npc in npcs) + " are present and can be addressed by name.",
        "npcs": npcs,
        "turns": turns,
    }


def build_corpus() -> list[dict]:
    """Return 12 conversational families. Related turns stay in one family."""
    families = [
        _ferry(),
        _mill(),
        _gate(),
        _shrine(),
        _market(),
        _archive(),
        _stable(),
        _infirmary(),
        _watch(),
        _tavern(),
        _chapel(),
        _yard(),
    ]
    seen = set()
    for family in families:
        if family["partition"] not in PARTITIONS:
            raise ValueError(family["id"])
        for turn in family["turns"]:
            if turn["id"] in seen:
                raise ValueError(turn["id"])
            seen.add(turn["id"])
            for phrase in turn["allowed"] + turn["forbidden"] + turn["distractors"]:
                if phrase.casefold() in turn["player"].casefold() and phrase.casefold() in " ".join(
                    topic["text"].casefold()
                    for npc in family["npcs"]
                    for topic in npc["topics"]
                    if topic.get("secret")
                ):
                    raise ValueError(f"player utterance contains a secret: {turn['id']}")
    return families


def corpus_document() -> dict:
    families = build_corpus()
    turns = [turn for family in families for turn in family["turns"]]
    return {
        "cycle": "PR-EG-R6-R5",
        "label_origin": "authored before provider execution",
        "families": families,
        "turn_count": len(turns),
        "family_count": len(families),
    }


def corpus_hash() -> str:
    payload = json.dumps(corpus_document(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def public_topics(npc: dict) -> list[dict]:
    return [topic for topic in npc["topics"] if not topic.get("secret") and topic.get("disclosure", "public") == "public"]


def iter_turns(families: list[dict] | None = None):
    for family in families or build_corpus():
        for turn in family["turns"]:
            yield family, turn


def _ferry() -> dict:
    nara = _npc("nara", "Nara", [
        _topic("bell", "The bell beside the ferry is called the harbor bell."),
        _topic("depart", "The ferry departs at dawn."),
        _topic("watch", "Guards watch the harbor gate throughout the night."),
        _topic("flood", "Travelers say the north road floods in spring.", epistemic="rumor"),
        _topic("sign", "The gate countersign is gray lantern.", secret=True),
    ])
    oren = _npc("oren", "Oren", [
        _topic("road", "The street beyond the harbor gate is called the north road."),
        _topic("posted", "The ferry schedules are posted on the dock."),
        _topic("slate", "The glazier keeps the slate lens."),
        _topic("sign", "The gate countersign is gray lantern.", secret=True),
    ])
    c = "c01"
    turns = [
        _turn(c, 1, "Nara, what is the bell beside the ferry called?", act="information_question", addressee="nara", answer_class="DIRECT", tags=["direct"],
              allowed=["harbor bell"], forbidden=["gray lantern"], eligible=["bell"], correspondence={"bell": "direct"},
              predicate="called", predicate_evidence="called", roles=[("item", "bell beside the ferry")], requested_role="name",
              sources={"bell": {"text": nara["topics"][0]["text"], "predicate": "called", "evidence": "called", "roles": [("item", "bell beside the ferry"), ("name", "harbor bell")]}}),
        _turn(c, 2, "Nara, when does the ferry depart?", act="information_question", addressee="nara", answer_class="DIRECT", tags=["direct"],
              allowed=["dawn"], forbidden=["gray lantern"], eligible=["depart"], correspondence={"depart": "direct", "bell": "unrelated"},
              predicate="depart", predicate_evidence="depart", roles=[("item", "ferry")], requested_role="time",
              sources={"depart": {"text": nara["topics"][1]["text"], "predicate": "depart", "evidence": "depart", "roles": [("item", "ferry"), ("time", "dawn")]}}),
        _turn(c, 3, "No, I meant when the harbor gate opens.", act="correction", addressee="nara", answer_class="UNKNOWN", tags=["correction", "unknown"],
              allowed=[], forbidden=["dawn", "gray lantern"], referent={"select": "contains", "text": "ferry depart"}, complication="correction onto a fact this NPC does not have"),
        _turn(c, 4, "Nara, who watches the harbor gate throughout the night?", act="information_question", addressee="nara", answer_class="DIRECT", tags=["direct"],
              allowed=["Guards watch"], forbidden=["gray lantern"], eligible=["watch"], correspondence={"watch": "direct"},
              predicate="watch", predicate_evidence="watches", roles=[("place", "harbor gate")], requested_role="watcher",
              sources={"watch": {"text": nara["topics"][2]["text"], "predicate": "watch", "evidence": "watch", "roles": [("place", "harbor gate"), ("watcher", "Guards")]}}),
        _turn(c, 5, "Who told you?", act="follow_up", addressee="nara", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["gray lantern", "harbor bell"], referent={"select": "previous"}, complication="source attribution after a fact with no informant"),
        _turn(c, 6, "Nara, what is the street beyond the harbor gate called?", act="information_question", addressee="nara", answer_class="UNKNOWN", tags=["unknown", "topic_change"],
              allowed=[], forbidden=["north road", "gray lantern"], complication="the other NPC knows this; Nara does not"),
        _turn(c, 7, "Oren, what is the street beyond the harbor gate called?", act="information_question", addressee="oren", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["north road"], forbidden=["gray lantern"], eligible=["road"], correspondence={"road": "direct"},
              predicate="called", predicate_evidence="called", roles=[("item", "street beyond the harbor gate")], requested_role="name",
              sources={"road": {"text": oren["topics"][0]["text"], "predicate": "called", "evidence": "called", "roles": [("item", "street beyond the harbor gate"), ("name", "north road")]}}),
        _turn(c, 8, "No, I meant the slate lens, not the street.", act="correction", addressee="oren", answer_class="DIRECT", tags=["correction"],
              allowed=["slate lens", "glazier"], forbidden=["north road", "gray lantern"], eligible=["slate"], correspondence={"slate": "direct", "road": "unrelated"},
              referent={"select": "contains", "text": "street beyond"},
              predicate="keeps", predicate_evidence="lens", roles=[("item", "slate lens")], requested_role="keeper",
              sources={"slate": {"text": oren["topics"][2]["text"], "predicate": "keeps", "evidence": "keeps", "roles": [("item", "slate lens"), ("keeper", "glazier")]}}),
        _turn(c, 9, "Oren, where are the ferry schedules posted?", act="information_question", addressee="oren", answer_class="DIRECT", tags=["direct"],
              allowed=["posted on the dock"], forbidden=["gray lantern"], eligible=["posted"], correspondence={"posted": "direct"},
              predicate="posted", predicate_evidence="posted", roles=[("item", "ferry schedules")], requested_role="place",
              sources={"posted": {"text": oren["topics"][1]["text"], "predicate": "posted", "evidence": "posted", "roles": [("item", "ferry schedules"), ("place", "dock")]}}),
        _turn(c, 10, "What about the slate lens?", act="follow_up", addressee="oren", answer_class="DIRECT", tags=["follow_up"],
              allowed=["glazier", "slate lens"], forbidden=["gray lantern"], eligible=["slate"], correspondence={"slate": "direct"},
              referent={"select": "previous"}, predicate="keeps", predicate_evidence="slate lens", roles=[("item", "slate lens")], requested_role="keeper",
              sources={"slate": {"text": oren["topics"][2]["text"], "predicate": "keeps", "evidence": "keeps", "roles": [("item", "slate lens"), ("keeper", "glazier")]}}),
        _turn(c, 11, "Oren, who manages the ferry schedules?", act="information_question", addressee="oren", answer_class="RELATED_NONANSWER", tags=["related"],
              allowed=[], forbidden=["gray lantern"], distractors=["posted on the dock"], correspondence={"posted": "related_but_nonanswer"},
              complication="the posting place does not name a manager"),
        _turn(c, 12, "Nara or Oren, what is the bell beside the ferry called?", act="information_question", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["harbor bell", "gray lantern"], complication="two addressees and the two would not be equally responsible"),
        _turn(c, 13, "Nara, what is the gate countersign?", act="information_question", addressee="nara", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["gray lantern"], complication="Nara knows the countersign and must not disclose it"),
        _turn(c, 14, "Nara, when does the ferry depart, and who rings the bell?", act="information_question", addressee="nara", answer_class="PARTIAL", tags=["partial"],
              allowed=["dawn"], forbidden=["gray lantern"], eligible=["depart"], correspondence={"depart": "partial", "bell": "related_but_nonanswer"},
              complication="departure is known and the ringer is not"),
    ]
    return _family(c, "development", "Ferry office", [nara, oren], turns)


def _mill() -> dict:
    quill = _npc("quill", "Quill", [
        _topic("cala_brin", "Cala told Brin that the cistern is cracked."),
        _topic("brin_cala", "Brin told Cala that the cistern is sound."),
        _topic("key", "The cistern key hangs in the mill."),
        _topic("ledger", "The night ledger is locked in the mill office."),
        _topic("route", "The buyer route runs under the mill.", secret=True),
    ])
    c = "c02"
    told = quill["topics"][0]["text"]
    reverse = quill["topics"][1]["text"]
    turns = [
        _turn(c, 1, "Quill, what did Cala tell Brin about the cistern?", act="information_question", addressee="quill", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["cistern is cracked"], forbidden=["cistern is sound", "under the mill"], eligible=["cala_brin"],
              correspondence={"cala_brin": "direct", "brin_cala": "related_but_nonanswer"},
              predicate="told", predicate_evidence="tell", roles=[("speaker", "Cala"), ("recipient", "Brin"), ("topic", "cistern")], requested_role="message",
              sources={"cala_brin": {"text": told, "predicate": "told", "evidence": "told", "roles": [("speaker", "Cala"), ("recipient", "Brin"), ("topic", "cistern"), ("message", "cistern is cracked")]}}),
        _turn(c, 2, "No, I meant what Brin told Cala about the cistern.", act="correction", addressee="quill", answer_class="DIRECT", tags=["correction", "multi_role"],
              allowed=["cistern is sound"], forbidden=["cistern is cracked", "under the mill"], eligible=["brin_cala"],
              correspondence={"brin_cala": "direct", "cala_brin": "related_but_nonanswer"}, referent={"select": "previous"},
              predicate="told", predicate_evidence="told", roles=[("speaker", "Brin"), ("recipient", "Cala"), ("topic", "cistern")], requested_role="message",
              sources={"brin_cala": {"text": reverse, "predicate": "told", "evidence": "told", "roles": [("speaker", "Brin"), ("recipient", "Cala"), ("topic", "cistern"), ("message", "cistern is sound")]}}),
        _turn(c, 3, "Who told you that?", act="follow_up", addressee="quill", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["under the mill", "cistern is sound"], referent={"select": "previous"}, complication="the report names Cala and Brin, not Quill's informant"),
        _turn(c, 4, "Quill, where does the cistern key hang?", act="information_question", addressee="quill", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["hangs in the mill"], forbidden=["under the mill"], eligible=["key"], correspondence={"key": "direct"},
              predicate="hang", predicate_evidence="hang", roles=[("item", "cistern key")], requested_role="place",
              sources={"key": {"text": quill["topics"][2]["text"], "predicate": "hang", "evidence": "hangs", "roles": [("item", "cistern key"), ("place", "mill")]}}),
        _turn(c, 5, "Quill, where is the night ledger, and who locked it?", act="information_question", addressee="quill", answer_class="PARTIAL", tags=["partial"],
              allowed=["locked in the mill office"], forbidden=["under the mill"], eligible=["ledger"], correspondence={"ledger": "partial"},
              predicate="locked", predicate_evidence="locked", roles=[("item", "night ledger")], requested_role="agent",
              sources={"ledger": {"text": quill["topics"][3]["text"], "predicate": "locked", "evidence": "locked", "roles": [("item", "night ledger"), ("place", "mill office")]}},
              complication="place is known and the locking person is not"),
        _turn(c, 6, "What about the key again?", act="follow_up", addressee="quill", answer_class="DIRECT", tags=["follow_up"],
              allowed=["cistern key", "mill"], forbidden=["under the mill"], eligible=["key"], correspondence={"key": "direct"}, referent={"select": "contains", "text": "cistern key"}),
        _turn(c, 7, "No, I was asking about the night ledger.", act="correction", addressee="quill", answer_class="PARTIAL", tags=["correction", "partial"],
              allowed=["mill office"], forbidden=["under the mill", "cistern key"], eligible=["ledger"], correspondence={"ledger": "partial", "key": "unrelated"},
              referent={"select": "contains", "text": "cistern key"}),
        _turn(c, 8, "Quill, what color is the night ledger?", act="information_question", addressee="quill", answer_class="UNKNOWN", tags=["unknown"],
              allowed=[], forbidden=["under the mill", "blue", "red"]),
        _turn(c, 9, "Quill, what did Cala tell Brin about the buyer route?", act="information_question", addressee="quill", answer_class="UNKNOWN", tags=["unknown", "multi_role"],
              allowed=[], forbidden=["under the mill"], complication="role-shaped question whose content is restricted and not a public telling"),
        _turn(c, 10, "How do you know the cistern key hangs there?", act="follow_up", addressee="quill", answer_class="UNKNOWN", tags=["follow_up"],
              allowed=[], forbidden=["under the mill"], referent={"select": "contains", "text": "cistern key"}),
        _turn(c, 11, "Quill, which cistern did you mean?", act="information_question", addressee="quill", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["cracked", "sound", "under the mill"], complication="cracked and sound are both on record"),
        _turn(c, 12, "Quill, where does the buyer route run?", act="information_question", addressee="quill", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["under the mill"]),
        _turn(c, 13, "Please repeat where the buyer route runs.", act="follow_up", addressee="quill", answer_class="RESTRICTED", tags=["restricted", "follow_up"],
              allowed=[], forbidden=["under the mill"], referent={"select": "previous"}),
        _turn(c, 14, "Quill, where is the night ledger, and what color is its lock?", act="information_question", addressee="quill", answer_class="PARTIAL", tags=["partial"],
              allowed=["mill office"], forbidden=["under the mill"], eligible=["ledger"], correspondence={"ledger": "partial"},
              complication="the office is known and the lock color is not"),
    ]
    return _family(c, "development", "Mill archive", [quill], turns)


def _gate() -> dict:
    ilse = _npc("ilse", "Ilse", [
        _topic("dusk", "The patrol changes at dusk."),
        _topic("west", "The west post is empty at dawn."),
        _topic("rumor", "Porters claim smugglers use the orchard path.", epistemic="rumor"),
        _topic("pass", "The night password is silver reed.", secret=True),
    ])
    pico = _npc("pico", "Pico", [
        _topic("relief", "Pico relieves Ilse at the east post."),
        _topic("lantern", "The gate lantern burns until midnight."),
        _topic("pass", "The night password is silver reed.", secret=True),
    ])
    c = "c03"
    turns = [
        _turn(c, 1, "Ilse, when does the patrol change?", act="information_question", addressee="ilse", answer_class="DIRECT", tags=["direct"],
              allowed=["dusk"], forbidden=["silver reed"], eligible=["dusk"], correspondence={"dusk": "direct"},
              predicate="change", predicate_evidence="change", roles=[("item", "patrol")], requested_role="time",
              sources={"dusk": {"text": ilse["topics"][0]["text"], "predicate": "change", "evidence": "changes", "roles": [("item", "patrol"), ("time", "dusk")]}}),
        _turn(c, 2, "Ilse, when is the west post empty?", act="information_question", addressee="ilse", answer_class="DIRECT", tags=["direct"],
              allowed=["empty at dawn"], forbidden=["silver reed"], eligible=["west"], correspondence={"west": "direct"},
              predicate="empty", predicate_evidence="empty", roles=[("place", "west post")], requested_role="time",
              sources={"west": {"text": ilse["topics"][1]["text"], "predicate": "empty", "evidence": "empty", "roles": [("place", "west post"), ("time", "dawn")]}}),
        _turn(c, 3, "No, I meant the east post.", act="correction", addressee="ilse", answer_class="UNKNOWN", tags=["correction", "unknown"],
              allowed=[], forbidden=["silver reed", "empty at dawn"], referent={"select": "previous"}, complication="Ilse has no east-post fact"),
        _turn(c, 4, "Pico, who relieves Ilse?", act="information_question", addressee="pico", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["relieves Ilse", "east post"], forbidden=["silver reed"], eligible=["relief"], correspondence={"relief": "direct"},
              predicate="relieves", predicate_evidence="relieves", roles=[("patient", "Ilse")], requested_role="relief",
              sources={"relief": {"text": pico["topics"][0]["text"], "predicate": "relieves", "evidence": "relieves", "roles": [("agent", "Pico"), ("patient", "Ilse"), ("place", "east post")]}}),
        _turn(c, 5, "No, I meant who Ilse relieves.", act="correction", addressee="pico", answer_class="UNKNOWN", tags=["correction", "multi_role"],
              allowed=[], forbidden=["silver reed", "east post"], referent={"select": "previous"}, complication="role reversal has no supporting source"),
        _turn(c, 6, "Pico, how long does the gate lantern burn?", act="information_question", addressee="pico", answer_class="DIRECT", tags=["direct"],
              allowed=["until midnight"], forbidden=["silver reed"], eligible=["lantern"], correspondence={"lantern": "direct"},
              predicate="burn", predicate_evidence="burn", roles=[("item", "gate lantern")], requested_role="time",
              sources={"lantern": {"text": pico["topics"][1]["text"], "predicate": "burn", "evidence": "burns", "roles": [("item", "gate lantern"), ("time", "midnight")]}}),
        _turn(c, 7, "Ilse, do smugglers use the orchard path?", act="information_question", addressee="ilse", answer_class="DIRECT", tags=["direct"],
              allowed=["orchard path"], forbidden=["silver reed"], hedge_any=["have heard", "as a rumor"], eligible=["rumor"], correspondence={"rumor": "direct"},
              epistemic="rumor", predicate="use", predicate_evidence="use", roles=[("place", "orchard path")], requested_role="agent",
              sources={"rumor": {"text": ilse["topics"][2]["text"], "predicate": "use", "evidence": "use", "epistemic": "rumor", "roles": [("agent", "smugglers"), ("place", "orchard path")]}}),
        _turn(c, 8, "Who told you the patrol changes at dusk?", act="follow_up", addressee="ilse", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["silver reed"], referent={"select": "contains", "text": "patrol change"}),
        _turn(c, 9, "Ilse, what is the night password?", act="information_question", addressee="ilse", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["silver reed"]),
        _turn(c, 10, "Pico, say the night password again.", act="follow_up", addressee="pico", answer_class="RESTRICTED", tags=["restricted", "follow_up"],
              allowed=[], forbidden=["silver reed"], referent={"select": "new"}, complication="Pico also holds the password and must not repeat it"),
        _turn(c, 11, "Ilse, which post is empty, the west post or the east post?", act="information_question", addressee="ilse", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["silver reed"], complication="the question itself names two posts and only one is attested; a single choice would hide the missing one"),
        _turn(c, 12, "What about tomorrow's patrol?", act="follow_up", addressee="ilse", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["silver reed", "dusk"], referent={"select": "contains", "text": "patrol"}),
        _turn(c, 13, "Pico, where is the spare gate rope?", act="information_question", addressee="pico", answer_class="UNKNOWN", tags=["unknown"],
              allowed=[], forbidden=["silver reed"]),
        _turn(c, 14, "Ilse, do you mean the dusk change or the empty post?", act="information_question", addressee="ilse", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["silver reed"], complication="two attested gate facts and no unique referent"),
    ]
    # Turn 11 is a poor ambiguity example because one post is known. Reclassify by keeping clarification
    # only when both answers would be guesses. West post IS known. Change player line to two unknown posts.
    turns[10] = _turn(c, 11, "Ilse, is the empty post the orchard post or the mill post?", act="information_question", addressee="ilse", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
                      allowed=[], forbidden=["silver reed", "west post", "empty at dawn"], complication="neither named post is the attested west post")
    return _family(c, "development", "Gate watch", [ilse, pico], turns)


def _shrine() -> dict:
    maud = _npc("maud", "Maud", [
        _topic("relic", "The chapel relic is called the pale lantern."),
        _topic("carry", "Lior carried the pale lantern to Maud."),
        _topic("belief", "Maud believes the blessing fades at midnight.", epistemic="belief"),
        _topic("vow", "The inner vow is quiet ash.", secret=True),
    ])
    lior = _npc("lior", "Lior", [
        _topic("water", "The shrine well is drawn at noon."),
        _topic("carry", "Maud carried the pale lantern to Lior."),
        _topic("vow", "The inner vow is quiet ash.", secret=True),
    ])
    c = "c04"
    turns = [
        _turn(c, 1, "Maud, what is the chapel relic called?", act="information_question", addressee="maud", answer_class="DIRECT", tags=["direct"],
              allowed=["pale lantern"], forbidden=["quiet ash"], eligible=["relic"], correspondence={"relic": "direct"},
              predicate="called", predicate_evidence="called", roles=[("item", "chapel relic")], requested_role="name",
              sources={"relic": {"text": maud["topics"][0]["text"], "predicate": "called", "evidence": "called", "roles": [("item", "chapel relic"), ("name", "pale lantern")]}}),
        _turn(c, 2, "Maud, who carried the pale lantern to you?", act="information_question", addressee="maud", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["Lior carried"], forbidden=["quiet ash", "Maud carried"], eligible=["carry"], correspondence={"carry": "direct"},
              predicate="carried", predicate_evidence="carried", roles=[("item", "pale lantern"), ("recipient", "Maud")], requested_role="carrier",
              sources={"carry": {"text": maud["topics"][1]["text"], "predicate": "carried", "evidence": "carried", "roles": [("carrier", "Lior"), ("item", "pale lantern"), ("recipient", "Maud")]}}),
        _turn(c, 3, "No, I meant who you carried it to.", act="correction", addressee="maud", answer_class="UNKNOWN", tags=["correction", "multi_role"],
              allowed=[], forbidden=["quiet ash", "Lior carried"], referent={"select": "previous"}, complication="Maud's source is the opposite direction"),
        _turn(c, 4, "Lior, who carried the pale lantern to you?", act="information_question", addressee="lior", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["Maud carried"], forbidden=["quiet ash"], eligible=["carry"], correspondence={"carry": "direct"},
              predicate="carried", predicate_evidence="carried", roles=[("item", "pale lantern"), ("recipient", "Lior")], requested_role="carrier",
              sources={"carry": {"text": lior["topics"][1]["text"], "predicate": "carried", "evidence": "carried", "roles": [("carrier", "Maud"), ("item", "pale lantern"), ("recipient", "Lior")]}}),
        _turn(c, 5, "Lior, when is the shrine well drawn?", act="information_question", addressee="lior", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["at noon"], forbidden=["quiet ash"], eligible=["water"], correspondence={"water": "direct"},
              predicate="drawn", predicate_evidence="drawn", roles=[("item", "shrine well")], requested_role="time",
              sources={"water": {"text": lior["topics"][0]["text"], "predicate": "drawn", "evidence": "drawn", "roles": [("item", "shrine well"), ("time", "noon")]}}),
        _turn(c, 6, "Maud, when does the blessing fade?", act="information_question", addressee="maud", answer_class="DIRECT", tags=["direct"],
              allowed=["midnight"], forbidden=["quiet ash"], hedge_any=["cannot establish"], eligible=["belief"], correspondence={"belief": "direct"},
              epistemic="belief", predicate="fade", predicate_evidence="fade", roles=[("item", "blessing")], requested_role="time",
              sources={"belief": {"text": maud["topics"][2]["text"], "predicate": "fade", "evidence": "fades", "epistemic": "belief", "roles": [("item", "blessing"), ("time", "midnight")]}}),
        _turn(c, 7, "Who told you the relic's name?", act="follow_up", addressee="maud", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["quiet ash", "pale lantern"], referent={"select": "contains", "text": "chapel relic"}),
        _turn(c, 8, "No, I was asking when the well is drawn.", act="correction", addressee="lior", answer_class="DIRECT", tags=["correction"],
              allowed=["noon"], forbidden=["quiet ash", "midnight"], eligible=["water"], correspondence={"water": "direct"},
              referent={"select": "contains", "text": "shrine well"}),
        _turn(c, 9, "Lior, what saint's day falls in the chapel?", act="information_question", addressee="lior", answer_class="UNKNOWN", tags=["unknown"],
              allowed=[], forbidden=["quiet ash"]),
        _turn(c, 10, "Maud or Lior, what is the chapel relic called?", act="information_question", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["pale lantern", "quiet ash"]),
        _turn(c, 11, "What about the well after dark?", act="follow_up", addressee="lior", answer_class="UNKNOWN", tags=["follow_up"],
              allowed=[], forbidden=["quiet ash", "noon"], referent={"select": "contains", "text": "shrine well"}),
        _turn(c, 12, "Maud, what is the inner vow?", act="information_question", addressee="maud", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["quiet ash"]),
        _turn(c, 13, "Lior, the relic and the well: when is each one used?", act="information_question", addressee="lior", answer_class="PARTIAL", tags=["partial"],
              allowed=["noon"], forbidden=["quiet ash", "pale lantern"], eligible=["water"], correspondence={"water": "partial"},
              complication="Lior knows the well hour and not a use schedule for the relic"),
    ]
    return _family(c, "development", "Shrine court", [maud, lior], turns)


def _market() -> dict:
    sela = _npc("sela", "Sela", [
        _topic("price", "The spare lamps cost three silver."),
        _topic("crate", "The spice crate weighs a stone."),
        _topic("shortage", "Hawkers say lamp oil runs short before winter.", epistemic="rumor"),
        _topic("client", "The hidden buyer is house merrow.", secret=True),
    ])
    joss = _npc("joss", "Joss", [
        _topic("buyer", "Joss buys the spare lamps for the hostel."),
        _topic("cart", "The morning cart leaves from the elm."),
        _topic("client", "The hidden buyer is house merrow.", secret=True),
    ])
    c = "c05"
    turns = [
        _turn(c, 1, "Sela, what do the spare lamps cost?", act="information_question", addressee="sela", answer_class="DIRECT", tags=["direct"],
              allowed=["three silver"], forbidden=["house merrow"], eligible=["price"], correspondence={"price": "direct"},
              predicate="cost", predicate_evidence="cost", roles=[("item", "spare lamps")], requested_role="price",
              sources={"price": {"text": sela["topics"][0]["text"], "predicate": "cost", "evidence": "cost", "roles": [("item", "spare lamps"), ("price", "three silver")]}}),
        _turn(c, 2, "Sela, what do the spare lamps cost and who buys them?", act="information_question", addressee="sela", answer_class="PARTIAL", tags=["partial"],
              allowed=["three silver"], forbidden=["house merrow", "hostel"], eligible=["price"], correspondence={"price": "partial"},
              complication="Sela knows the price and not the buyer"),
        _turn(c, 3, "Joss, who buys the spare lamps?", act="information_question", addressee="joss", answer_class="DIRECT", tags=["direct"],
              allowed=["hostel"], forbidden=["house merrow"], eligible=["buyer"], correspondence={"buyer": "direct"},
              predicate="buys", predicate_evidence="buys", roles=[("item", "spare lamps")], requested_role="buyer",
              sources={"buyer": {"text": joss["topics"][0]["text"], "predicate": "buys", "evidence": "buys", "roles": [("buyer", "Joss"), ("item", "spare lamps"), ("beneficiary", "hostel")]}}),
        _turn(c, 4, "No, I meant who sells them.", act="correction", addressee="joss", answer_class="UNKNOWN", tags=["correction", "unknown"],
              allowed=[], forbidden=["house merrow", "hostel"], referent={"select": "previous"}),
        _turn(c, 5, "Joss, where does the morning cart leave from?", act="information_question", addressee="joss", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["from the elm"], forbidden=["house merrow"], eligible=["cart"], correspondence={"cart": "direct"},
              predicate="leave", predicate_evidence="leave", roles=[("item", "morning cart")], requested_role="place",
              sources={"cart": {"text": joss["topics"][1]["text"], "predicate": "leave", "evidence": "leaves", "roles": [("item", "morning cart"), ("place", "elm")]}}),
        _turn(c, 6, "Sela, how heavy is the spice crate?", act="information_question", addressee="sela", answer_class="DIRECT", tags=["direct"],
              allowed=["a stone"], forbidden=["house merrow"], eligible=["crate"], correspondence={"crate": "direct"},
              predicate="weigh", predicate_evidence="heavy", roles=[("item", "spice crate")], requested_role="weight",
              sources={"crate": {"text": sela["topics"][1]["text"], "predicate": "weigh", "evidence": "weighs", "roles": [("item", "spice crate"), ("weight", "a stone")]}}),
        _turn(c, 7, "Sela, does lamp oil run short before winter?", act="information_question", addressee="sela", answer_class="DIRECT", tags=["direct"],
              allowed=["lamp oil"], forbidden=["house merrow"], hedge_any=["have heard", "as a rumor"], eligible=["shortage"], correspondence={"shortage": "direct"},
              epistemic="rumor", predicate="run", predicate_evidence="run", roles=[("item", "lamp oil")], requested_role="status",
              sources={"shortage": {"text": sela["topics"][2]["text"], "predicate": "run", "evidence": "runs", "epistemic": "rumor", "roles": [("item", "lamp oil"), ("time", "winter")]}}),
        _turn(c, 8, "Who told you the price?", act="follow_up", addressee="sela", answer_class="UNKNOWN", tags=["follow_up"],
              allowed=[], forbidden=["house merrow", "three silver"], referent={"select": "contains", "text": "spare lamps cost"}),
        _turn(c, 9, "No, I meant the spice crate's price.", act="correction", addressee="sela", answer_class="UNKNOWN", tags=["correction"],
              allowed=[], forbidden=["house merrow", "a stone"], referent={"select": "contains", "text": "spice crate"}, complication="weight is known and price is not"),
        _turn(c, 10, "What about the morning cart tomorrow?", act="follow_up", addressee="joss", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["house merrow"], referent={"select": "contains", "text": "morning cart"}),
        _turn(c, 11, "Sela or Joss, what do the spare lamps cost?", act="information_question", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["three silver", "house merrow"]),
        _turn(c, 12, "Sela, who is the hidden buyer?", act="information_question", addressee="sela", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["house merrow"]),
        _turn(c, 13, "Joss, name the hidden buyer too.", act="follow_up", addressee="joss", answer_class="RESTRICTED", tags=["restricted", "follow_up"],
              allowed=[], forbidden=["house merrow"], referent={"select": "new"}),
        _turn(c, 14, "Sela, how heavy is the spice crate, and what is inside it?", act="information_question", addressee="sela", answer_class="PARTIAL", tags=["partial"],
              allowed=["a stone"], forbidden=["house merrow"], eligible=["crate"], correspondence={"crate": "partial"},
              complication="weight is known and contents are not"),
    ]
    return _family(c, "validation", "Lamp market", [sela, joss], turns)


def _archive() -> dict:
    vesper = _npc("vesper", "Vesper", [
        _topic("roster", "Tamsin keeps the night roster."),
        _topic("letter", "Vesper copied Brin's letter on Monday."),
        _topic("map", "Brin copied Vesper's map on Thursday."),
        _topic("seal", "The archive seal phrase is red thread.", secret=True),
    ])
    brin = _npc("brin", "Brin", [
        _topic("shelf", "The tax rolls sit on the third shelf."),
        _topic("letter", "Brin copied Vesper's letter on Monday."),
        _topic("seal", "The archive seal phrase is red thread.", secret=True),
    ])
    c = "c06"
    turns = [
        _turn(c, 1, "Vesper, who keeps the night roster?", act="information_question", addressee="vesper", answer_class="DIRECT", tags=["direct"],
              allowed=["Tamsin"], forbidden=["red thread"], eligible=["roster"], correspondence={"roster": "direct"},
              predicate="keeps", predicate_evidence="keeps", roles=[("item", "night roster")], requested_role="keeper",
              sources={"roster": {"text": vesper["topics"][0]["text"], "predicate": "keeps", "evidence": "keeps", "roles": [("keeper", "Tamsin"), ("item", "night roster")]}}),
        _turn(c, 2, "Vesper, what did you copy of Brin's on Monday?", act="information_question", addressee="vesper", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["Brin's letter"], forbidden=["red thread", "Thursday"], eligible=["letter"], correspondence={"letter": "direct", "map": "related_but_nonanswer"},
              predicate="copied", predicate_evidence="copy", roles=[("agent", "Vesper"), ("owner", "Brin"), ("time", "Monday")], requested_role="work",
              sources={"letter": {"text": vesper["topics"][1]["text"], "predicate": "copied", "evidence": "copied", "roles": [("agent", "Vesper"), ("owner", "Brin"), ("work", "letter"), ("time", "Monday")]}}),
        _turn(c, 3, "No, I meant the map Brin copied.", act="correction", addressee="vesper", answer_class="DIRECT", tags=["correction", "multi_role"],
              allowed=["Thursday", "map"], forbidden=["red thread", "Monday"], eligible=["map"], correspondence={"map": "direct", "letter": "related_but_nonanswer"},
              referent={"select": "previous"},
              predicate="copied", predicate_evidence="copied", roles=[("agent", "Brin"), ("work", "map")], requested_role="time",
              sources={"map": {"text": vesper["topics"][2]["text"], "predicate": "copied", "evidence": "copied", "roles": [("agent", "Brin"), ("work", "map"), ("time", "Thursday")]}}),
        _turn(c, 4, "Brin, what did you copy of Vesper's on Monday?", act="information_question", addressee="brin", answer_class="DIRECT", tags=["multi_role", "direct"],
              allowed=["Vesper's letter"], forbidden=["red thread"], eligible=["letter"], correspondence={"letter": "direct"},
              predicate="copied", predicate_evidence="copy", roles=[("agent", "Brin"), ("owner", "Vesper"), ("time", "Monday")], requested_role="work",
              sources={"letter": {"text": brin["topics"][1]["text"], "predicate": "copied", "evidence": "copied", "roles": [("agent", "Brin"), ("owner", "Vesper"), ("work", "letter"), ("time", "Monday")]}}),
        _turn(c, 5, "Brin, where do the tax rolls sit?", act="information_question", addressee="brin", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["third shelf"], forbidden=["red thread"], eligible=["shelf"], correspondence={"shelf": "direct"},
              predicate="sit", predicate_evidence="sit", roles=[("item", "tax rolls")], requested_role="place",
              sources={"shelf": {"text": brin["topics"][0]["text"], "predicate": "sit", "evidence": "sit", "roles": [("item", "tax rolls"), ("place", "third shelf")]}}),
        _turn(c, 6, "Vesper, who keeps the roster and on which day was the map copied?", act="information_question", addressee="vesper", answer_class="PARTIAL", tags=["partial"],
              allowed=["Tamsin"], forbidden=["red thread"], complication="one question joins a keeper and a copy date; either fact alone is partial"),
        _turn(c, 7, "Who told you Tamsin keeps it?", act="follow_up", addressee="vesper", answer_class="UNKNOWN", tags=["follow_up"],
              allowed=[], forbidden=["red thread", "Tamsin"], referent={"select": "contains", "text": "night roster"}),
        _turn(c, 8, "No, I meant which shelf holds the letter.", act="correction", addressee="brin", answer_class="UNKNOWN", tags=["correction", "unknown"],
              allowed=[], forbidden=["red thread", "third shelf"], referent={"select": "contains", "text": "tax rolls"}),
        _turn(c, 9, "Vesper, what ink does the roster use?", act="information_question", addressee="vesper", answer_class="UNKNOWN", tags=["unknown"],
              allowed=[], forbidden=["red thread"]),
        _turn(c, 10, "Brin or Vesper, who keeps the night roster?", act="information_question", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["Tamsin", "red thread"]),
        _turn(c, 11, "What about the seal phrase?", act="follow_up", addressee="vesper", answer_class="RESTRICTED", tags=["restricted", "follow_up"],
              allowed=[], forbidden=["red thread"], referent={"select": "new"}),
        _turn(c, 12, "Vesper, what is the archive seal phrase?", act="information_question", addressee="vesper", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["red thread"]),
        _turn(c, 13, "Brin, when was Vesper's map copied?", act="information_question", addressee="brin", answer_class="UNKNOWN", tags=["unknown", "multi_role"],
              allowed=[], forbidden=["red thread", "Thursday"], complication="Brin does not hold Vesper's map statement"),
        _turn(c, 14, "Vesper, who keeps the night roster, and where does that keeper live?", act="information_question", addressee="vesper", answer_class="PARTIAL", tags=["partial"],
              allowed=["Tamsin"], forbidden=["red thread"], eligible=["roster"], correspondence={"roster": "partial"},
              complication="the keeper is known and the home is not"),
    ]
    return _family(c, "validation", "Night archive", [vesper, brin], turns)


def _stable() -> dict:
    wren = _npc("wren", "Wren", [
        _topic("mare", "Wren saddled Cala's mare before dawn."),
        _topic("feed", "The oats are stored in the loft."),
        _topic("brand", "The hidden brand is circle notch.", secret=True),
    ])
    cala = _npc("cala", "Cala", [
        _topic("gelding", "Cala saddled Wren's gelding at noon."),
        _topic("road", "The stable road joins the quarry lane."),
        _topic("brand", "The hidden brand is circle notch.", secret=True),
    ])
    c = "c07"
    turns = [
        _turn(c, 1, "Wren, whose mare did you saddle?", act="information_question", addressee="wren", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["Cala's mare"], forbidden=["circle notch"], eligible=["mare"], correspondence={"mare": "direct"},
              predicate="saddled", predicate_evidence="saddle", roles=[("agent", "Wren")], requested_role="mount",
              sources={"mare": {"text": wren["topics"][0]["text"], "predicate": "saddled", "evidence": "saddled", "roles": [("agent", "Wren"), ("mount", "Cala's mare"), ("time", "dawn")]}}),
        _turn(c, 2, "No, I meant whose horse Cala saddled.", act="correction", addressee="cala", answer_class="DIRECT", tags=["correction", "multi_role"],
              allowed=["Wren's gelding"], forbidden=["circle notch", "Cala's mare"], eligible=["gelding"], correspondence={"gelding": "direct"},
              referent={"select": "previous"},
              predicate="saddled", predicate_evidence="saddled", roles=[("agent", "Cala")], requested_role="mount",
              sources={"gelding": {"text": cala["topics"][0]["text"], "predicate": "saddled", "evidence": "saddled", "roles": [("agent", "Cala"), ("mount", "Wren's gelding"), ("time", "noon")]}}),
        _turn(c, 3, "Cala, when did you saddle Wren's gelding?", act="information_question", addressee="cala", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["at noon"], forbidden=["circle notch"], eligible=["gelding"], correspondence={"gelding": "direct"},
              predicate="saddled", predicate_evidence="saddle", roles=[("agent", "Cala"), ("mount", "Wren's gelding")], requested_role="time",
              sources={"gelding": {"text": cala["topics"][0]["text"], "predicate": "saddled", "evidence": "saddled", "roles": [("agent", "Cala"), ("mount", "Wren's gelding"), ("time", "noon")]}}),
        _turn(c, 4, "Wren, where are the oats stored?", act="information_question", addressee="wren", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["in the loft"], forbidden=["circle notch"], eligible=["feed"], correspondence={"feed": "direct"},
              predicate="stored", predicate_evidence="stored", roles=[("item", "oats")], requested_role="place",
              sources={"feed": {"text": wren["topics"][1]["text"], "predicate": "stored", "evidence": "stored", "roles": [("item", "oats"), ("place", "loft")]}}),
        _turn(c, 5, "Wren, where are the oats and who owns the loft?", act="information_question", addressee="wren", answer_class="PARTIAL", tags=["partial"],
              allowed=["loft"], forbidden=["circle notch"], eligible=["feed"], correspondence={"feed": "partial"},
              complication="place is known and ownership is not"),
        _turn(c, 6, "Cala, which road does the stable road join?", act="information_question", addressee="cala", answer_class="DIRECT", tags=["direct"],
              allowed=["quarry lane"], forbidden=["circle notch"], eligible=["road"], correspondence={"road": "direct"},
              predicate="join", predicate_evidence="join", roles=[("item", "stable road")], requested_role="road",
              sources={"road": {"text": cala["topics"][1]["text"], "predicate": "join", "evidence": "joins", "roles": [("item", "stable road"), ("road", "quarry lane")]}}),
        _turn(c, 7, "Who told you about the oats?", act="follow_up", addressee="wren", answer_class="UNKNOWN", tags=["follow_up"],
              allowed=[], forbidden=["circle notch"], referent={"select": "contains", "text": "oats"}),
        _turn(c, 8, "No, I meant the quarry lane's length.", act="correction", addressee="cala", answer_class="UNKNOWN", tags=["correction", "unknown"],
              allowed=[], forbidden=["circle notch", "quarry lane"], referent={"select": "contains", "text": "stable road"}),
        _turn(c, 9, "Wren, what color is Cala's mare?", act="information_question", addressee="wren", answer_class="UNKNOWN", tags=["unknown"],
              allowed=[], forbidden=["circle notch"]),
        _turn(c, 10, "She saddled which horse?", act="follow_up", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity", "follow_up"],
              allowed=[], forbidden=["circle notch", "mare", "gelding"], referent={"select": "previous"}, complication="she can mean Wren or Cala"),
        _turn(c, 11, "Wren, what is the hidden brand?", act="information_question", addressee="wren", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["circle notch"]),
        _turn(c, 12, "Cala, repeat the hidden brand.", act="follow_up", addressee="cala", answer_class="RESTRICTED", tags=["restricted", "follow_up"],
              allowed=[], forbidden=["circle notch"], referent={"select": "new"}),
        _turn(c, 13, "What about the evening feed?", act="follow_up", addressee="wren", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["circle notch", "loft"], referent={"select": "contains", "text": "oats"}),
    ]
    return _family(c, "validation", "Stable yard", [wren, cala], turns)


def _infirmary() -> dict:
    doss = _npc("doss", "Doss", [
        _topic("nia_doss", "Nia told Doss the fever started at dusk."),
        _topic("doss_nia", "Doss told Nia the fever broke at dawn."),
        _topic("willow", "The willow poultice cools a mild fever."),
        _topic("cupboard", "The locked antidote is in the blue cupboard.", secret=True),
    ])
    nia = _npc("nia", "Nia", [
        _topic("band", "The linen bands are boiled at morning."),
        _topic("plague", "Villagers fear a plague in the lower ward.", epistemic="rumor"),
        _topic("cupboard", "The locked antidote is in the blue cupboard.", secret=True),
    ])
    c = "c08"
    turns = [
        _turn(c, 1, "Doss, what did Nia tell you about the fever?", act="information_question", addressee="doss", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["started at dusk"], forbidden=["blue cupboard"], eligible=["nia_doss"], correspondence={"nia_doss": "direct", "doss_nia": "related_but_nonanswer"},
              predicate="told", predicate_evidence="tell", roles=[("speaker", "Nia"), ("recipient", "Doss"), ("topic", "fever")], requested_role="message",
              sources={"nia_doss": {"text": doss["topics"][0]["text"], "predicate": "told", "evidence": "told", "roles": [("speaker", "Nia"), ("recipient", "Doss"), ("topic", "fever"), ("message", "started at dusk")]}}),
        _turn(c, 2, "No, I meant what you told Nia about the fever.", act="correction", addressee="doss", answer_class="DIRECT", tags=["correction", "multi_role"],
              allowed=["broke at dawn"], forbidden=["blue cupboard", "started at dusk"], eligible=["doss_nia"], correspondence={"doss_nia": "direct", "nia_doss": "related_but_nonanswer"},
              referent={"select": "previous"},
              predicate="told", predicate_evidence="told", roles=[("recipient", "Nia"), ("topic", "fever")], requested_role="message",
              sources={"doss_nia": {"text": doss["topics"][1]["text"], "predicate": "told", "evidence": "told", "roles": [("speaker", "Doss"), ("recipient", "Nia"), ("topic", "fever"), ("message", "broke at dawn")]}}),
        _turn(c, 3, "Doss, what does the willow poultice do?", act="information_question", addressee="doss", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["cools a mild fever"], forbidden=["blue cupboard"], eligible=["willow"], correspondence={"willow": "direct"},
              predicate="cool", predicate_evidence="do", roles=[("item", "willow poultice")], requested_role="effect",
              sources={"willow": {"text": doss["topics"][2]["text"], "predicate": "cool", "evidence": "cools", "roles": [("item", "willow poultice"), ("effect", "mild fever")]}}),
        _turn(c, 4, "Doss, what does the willow poultice do for a plague?", act="information_question", addressee="doss", answer_class="RELATED_NONANSWER", tags=["related"],
              allowed=[], forbidden=["blue cupboard"], distractors=["mild fever"], correspondence={"willow": "related_but_nonanswer"},
              complication="a mild-fever poultice is not a plague treatment"),
        _turn(c, 5, "Nia, when are the linen bands boiled?", act="information_question", addressee="nia", answer_class="DIRECT", tags=["direct"],
              allowed=["at morning"], forbidden=["blue cupboard"], eligible=["band"], correspondence={"band": "direct"},
              predicate="boiled", predicate_evidence="boiled", roles=[("item", "linen bands")], requested_role="time",
              sources={"band": {"text": nia["topics"][0]["text"], "predicate": "boiled", "evidence": "boiled", "roles": [("item", "linen bands"), ("time", "morning")]}}),
        _turn(c, 6, "Nia, is there a plague in the lower ward?", act="information_question", addressee="nia", answer_class="DIRECT", tags=["direct"],
              allowed=["lower ward"], forbidden=["blue cupboard"], hedge_any=["have heard", "as a rumor"], eligible=["plague"], correspondence={"plague": "direct"},
              epistemic="rumor", predicate="plague", predicate_evidence="plague", roles=[("place", "lower ward")], requested_role="status",
              sources={"plague": {"text": nia["topics"][1]["text"], "predicate": "plague", "evidence": "plague", "epistemic": "rumor", "roles": [("place", "lower ward")]}}),
        _turn(c, 7, "Who told you the fever's start?", act="follow_up", addressee="doss", answer_class="DIRECT", tags=["follow_up", "multi_role"],
              allowed=["Nia"], forbidden=["blue cupboard"], eligible=["nia_doss"], correspondence={"nia_doss": "direct"}, referent={"select": "contains", "text": "Nia tell you"},
              complication="the telling itself names Nia as the speaker"),
        _turn(c, 8, "No, I meant when the bands are dried.", act="correction", addressee="nia", answer_class="UNKNOWN", tags=["correction", "unknown"],
              allowed=[], forbidden=["blue cupboard", "morning"], referent={"select": "contains", "text": "linen bands"}),
        _turn(c, 9, "Doss, which herb treats a broken bone?", act="information_question", addressee="doss", answer_class="UNKNOWN", tags=["unknown"],
              allowed=[], forbidden=["blue cupboard", "willow"]),
        _turn(c, 10, "Doss or Nia, when did the fever start?", act="information_question", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["dusk", "dawn", "blue cupboard"]),
        _turn(c, 11, "Doss, where is the locked antidote?", act="information_question", addressee="doss", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["blue cupboard"]),
        _turn(c, 12, "Nia, where is that antidote kept?", act="follow_up", addressee="nia", answer_class="RESTRICTED", tags=["restricted", "follow_up"],
              allowed=[], forbidden=["blue cupboard"], referent={"select": "new"}),
        _turn(c, 13, "What about the poultice's age?", act="follow_up", addressee="doss", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["blue cupboard"], referent={"select": "contains", "text": "willow poultice"}),
    ]
    return _family(c, "validation", "Infirmary", [doss, nia], turns)


def _watch() -> dict:
    rhee = _npc("rhee", "Rhee", [
        _topic("relief", "Tamsin relieves Rhee at the second bell."),
        _topic("west", "Rhee says the west post was quiet."),
        _topic("signal", "The private signal is west whistle.", secret=True),
    ])
    tamsin = _npc("tamsin", "Tamsin", [
        _topic("west", "Tamsin says the west post was noisy."),
        _topic("book", "The watch book closes at the third bell."),
        _topic("signal", "The private signal is west whistle.", secret=True),
    ])
    c = "c09"
    turns = [
        _turn(c, 1, "Rhee, who relieves you, and at which bell?", act="information_question", addressee="rhee", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["Tamsin", "second bell"], forbidden=["west whistle"], eligible=["relief"], correspondence={"relief": "direct"},
              predicate="relieves", predicate_evidence="relieves", roles=[("patient", "Rhee")], requested_role="relief",
              sources={"relief": {"text": rhee["topics"][0]["text"], "predicate": "relieves", "evidence": "relieves", "roles": [("relief", "Tamsin"), ("patient", "Rhee"), ("time", "second bell")]}}),
        _turn(c, 2, "Rhee, was the west post quiet or noisy?", act="information_question", addressee="rhee", answer_class="DIRECT", tags=["direct"],
              allowed=["quiet"], forbidden=["west whistle", "noisy"], eligible=["west"], correspondence={"west": "direct"},
              complication="Rhee's own claim is quiet; Tamsin contradicts it"),
        _turn(c, 3, "Tamsin, was the west post quiet or noisy?", act="information_question", addressee="tamsin", answer_class="DIRECT", tags=["direct"],
              allowed=["noisy"], forbidden=["west whistle", "quiet"], eligible=["west"], correspondence={"west": "direct"},
              complication="contradictory source, this speaker's claim only"),
        _turn(c, 4, "No, I meant Rhee's account of the west post.", act="correction", addressee="rhee", answer_class="DIRECT", tags=["correction"],
              allowed=["quiet"], forbidden=["west whistle", "noisy"], eligible=["west"], correspondence={"west": "direct"}, referent={"select": "contains", "text": "west post"}),
        _turn(c, 5, "Tamsin, when does the watch book close?", act="information_question", addressee="tamsin", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["third bell"], forbidden=["west whistle"], eligible=["book"], correspondence={"book": "direct"},
              predicate="close", predicate_evidence="close", roles=[("item", "watch book")], requested_role="time",
              sources={"book": {"text": tamsin["topics"][1]["text"], "predicate": "close", "evidence": "closes", "roles": [("item", "watch book"), ("time", "third bell")]}}),
        _turn(c, 6, "Rhee, who relieves you after the third bell?", act="information_question", addressee="rhee", answer_class="RELATED_NONANSWER", tags=["related"],
              allowed=[], forbidden=["west whistle"], distractors=["second bell"], correspondence={"relief": "related_but_nonanswer"},
              complication="the known relief is at the second bell, not the third"),
        _turn(c, 7, "Who told you the west post was quiet?", act="follow_up", addressee="rhee", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["west whistle"], referent={"select": "contains", "text": "west post"}),
        _turn(c, 8, "No, I meant when the book opens.", act="correction", addressee="tamsin", answer_class="UNKNOWN", tags=["correction", "unknown"],
              allowed=[], forbidden=["west whistle", "third bell"], referent={"select": "contains", "text": "watch book"}),
        _turn(c, 9, "Rhee, how many sentries stand the north wall?", act="information_question", addressee="rhee", answer_class="UNKNOWN", tags=["unknown"],
              allowed=[], forbidden=["west whistle"]),
        _turn(c, 10, "Rhee or Tamsin, was the west post quiet?", act="information_question", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["quiet", "noisy", "west whistle"], complication="their accounts conflict, so the addressee chooses the fact"),
        _turn(c, 11, "Rhee, what is the private signal?", act="information_question", addressee="rhee", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["west whistle"]),
        _turn(c, 12, "Tamsin, repeat the private signal.", act="follow_up", addressee="tamsin", answer_class="RESTRICTED", tags=["restricted", "follow_up"],
              allowed=[], forbidden=["west whistle"], referent={"select": "new"}),
        _turn(c, 13, "What about the fourth bell?", act="follow_up", addressee="tamsin", answer_class="UNKNOWN", tags=["follow_up"],
              allowed=[], forbidden=["west whistle", "third bell"], referent={"select": "contains", "text": "watch book"}),
        _turn(c, 14, "Rhee, who relieves you, and where does that relief sleep?", act="information_question", addressee="rhee", answer_class="PARTIAL", tags=["partial", "multi_role"],
              allowed=["Tamsin", "second bell"], forbidden=["west whistle"], eligible=["relief"], correspondence={"relief": "partial"},
              complication="the relief and bell are known and the lodging is not"),
    ]
    return _family(c, "holdout", "Watch house", [rhee, tamsin], turns)


def _tavern() -> dict:
    pell = _npc("pell", "Pell", [
        _topic("skiff", "The skiff departs at the evening tide."),
        _topic("stew", "The fish stew uses river eel."),
        _topic("storm", "Sailors say a storm sits beyond the bar.", epistemic="rumor"),
        _topic("ledger", "The smuggler's mark is salt ledger.", secret=True),
    ])
    bram = _npc("bram", "Bram", [
        _topic("paid", "Bram paid Pell for the skiff with two coins."),
        _topic("rope", "The spare rope hangs behind the bar."),
        _topic("ledger", "The smuggler's mark is salt ledger.", secret=True),
    ])
    c = "c10"
    turns = [
        _turn(c, 1, "Pell, when does the skiff depart?", act="information_question", addressee="pell", answer_class="DIRECT", tags=["direct"],
              allowed=["evening tide"], forbidden=["salt ledger"], eligible=["skiff"], correspondence={"skiff": "direct"},
              predicate="depart", predicate_evidence="depart", roles=[("item", "skiff")], requested_role="time",
              sources={"skiff": {"text": pell["topics"][0]["text"], "predicate": "depart", "evidence": "departs", "roles": [("item", "skiff"), ("time", "evening tide")]}}),
        _turn(c, 2, "Bram, who paid Pell for the skiff?", act="information_question", addressee="bram", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["Bram paid Pell"], forbidden=["salt ledger"], eligible=["paid"], correspondence={"paid": "direct"},
              predicate="paid", predicate_evidence="paid", roles=[("recipient", "Pell"), ("item", "skiff")], requested_role="payer",
              sources={"paid": {"text": bram["topics"][0]["text"], "predicate": "paid", "evidence": "paid", "roles": [("payer", "Bram"), ("recipient", "Pell"), ("item", "skiff"), ("price", "two coins")]}}),
        _turn(c, 3, "No, I meant who Pell paid.", act="correction", addressee="bram", answer_class="UNKNOWN", tags=["correction", "multi_role"],
              allowed=[], forbidden=["salt ledger", "two coins"], referent={"select": "previous"}, complication="the payment direction is only Bram to Pell"),
        _turn(c, 4, "Pell, what does the fish stew use?", act="information_question", addressee="pell", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["river eel"], forbidden=["salt ledger"], eligible=["stew"], correspondence={"stew": "direct"},
              predicate="use", predicate_evidence="use", roles=[("item", "fish stew")], requested_role="ingredient",
              sources={"stew": {"text": pell["topics"][1]["text"], "predicate": "use", "evidence": "uses", "roles": [("item", "fish stew"), ("ingredient", "river eel")]}}),
        _turn(c, 5, "Pell, what does the fish stew use, and what does it cost?", act="information_question", addressee="pell", answer_class="PARTIAL", tags=["partial"],
              allowed=["river eel"], forbidden=["salt ledger"], eligible=["stew"], correspondence={"stew": "partial"}),
        _turn(c, 6, "Bram, where does the spare rope hang?", act="information_question", addressee="bram", answer_class="DIRECT", tags=["direct"],
              allowed=["behind the bar"], forbidden=["salt ledger"], eligible=["rope"], correspondence={"rope": "direct"},
              predicate="hang", predicate_evidence="hang", roles=[("item", "spare rope")], requested_role="place",
              sources={"rope": {"text": bram["topics"][1]["text"], "predicate": "hang", "evidence": "hangs", "roles": [("item", "spare rope"), ("place", "bar")]}}),
        _turn(c, 7, "Pell, is there a storm beyond the bar?", act="information_question", addressee="pell", answer_class="DIRECT", tags=["direct"],
              allowed=["beyond the bar"], forbidden=["salt ledger"], hedge_any=["have heard", "as a rumor"], eligible=["storm"], correspondence={"storm": "direct"},
              epistemic="rumor", predicate="storm", predicate_evidence="storm", roles=[("place", "bar")], requested_role="status",
              sources={"storm": {"text": pell["topics"][2]["text"], "predicate": "storm", "evidence": "storm", "epistemic": "rumor", "roles": [("place", "bar")]}}),
        _turn(c, 8, "Who told you about the tide?", act="follow_up", addressee="pell", answer_class="UNKNOWN", tags=["follow_up"],
              allowed=[], forbidden=["salt ledger"], referent={"select": "contains", "text": "skiff depart"}),
        _turn(c, 9, "No, I meant the morning skiff.", act="correction", addressee="pell", answer_class="UNKNOWN", tags=["correction", "unknown"],
              allowed=[], forbidden=["salt ledger", "evening tide"], referent={"select": "contains", "text": "skiff depart"}),
        _turn(c, 10, "Pell or Bram, when does the skiff depart?", act="information_question", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["evening tide", "salt ledger"]),
        _turn(c, 11, "What about the rope's owner?", act="follow_up", addressee="bram", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["salt ledger"], referent={"select": "contains", "text": "spare rope"}),
        _turn(c, 12, "Pell, what is the smuggler's mark?", act="information_question", addressee="pell", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["salt ledger"]),
        _turn(c, 13, "Bram, tell me the smuggler's mark anyway.", act="follow_up", addressee="bram", answer_class="RESTRICTED", tags=["restricted", "follow_up"],
              allowed=[], forbidden=["salt ledger"], referent={"select": "new"}),
        _turn(c, 14, "Pell, when does the skiff depart, and what does passage cost?", act="information_question", addressee="pell", answer_class="PARTIAL", tags=["partial"],
              allowed=["evening tide"], forbidden=["salt ledger"], eligible=["skiff"], correspondence={"skiff": "partial"},
              complication="the tide is known and the fare is not"),
    ]
    return _family(c, "holdout", "Quay tavern", [pell, bram], turns)


def _chapel() -> dict:
    """Correction chain after an uncertain answer, then a topic change."""
    edda = _npc("edda", "Edda", [
        _topic("hymn", "The evening hymn is called the reed hymn."),
        _topic("candle", "The votive candles are lit at dusk."),
        _topic("bells", "Edda believes the chapel bells skip the third stroke.", epistemic="belief"),
        _topic("vow", "The sealed chapel vow is pale vow.", secret=True),
    ])
    c = "c11"
    turns = [
        _turn(c, 1, "Edda, what is the evening hymn called?", act="information_question", addressee="edda", answer_class="DIRECT", tags=["direct"],
              allowed=["reed hymn"], forbidden=["pale vow"], eligible=["hymn"], correspondence={"hymn": "direct"},
              predicate="called", predicate_evidence="called", roles=[("item", "evening hymn")], requested_role="name",
              sources={"hymn": {"text": edda["topics"][0]["text"], "predicate": "called", "evidence": "called", "roles": [("item", "evening hymn"), ("name", "reed hymn")]}}),
        _turn(c, 2, "No, I meant the morning hymn.", act="correction", addressee="edda", answer_class="UNKNOWN", tags=["correction", "unknown"],
              allowed=[], forbidden=["pale vow", "reed hymn"], referent={"select": "previous"}),
        _turn(c, 3, "Who told you that name?", act="follow_up", addressee="edda", answer_class="UNKNOWN", tags=["follow_up"],
              allowed=[], forbidden=["pale vow"], referent={"select": "contains", "text": "evening hymn"}, complication="follow-up after a correction onto an unknown"),
        _turn(c, 4, "Edda, when are the votive candles lit?", act="information_question", addressee="edda", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["at dusk"], forbidden=["pale vow"], eligible=["candle"], correspondence={"candle": "direct"},
              predicate="lit", predicate_evidence="lit", roles=[("item", "votive candles")], requested_role="time",
              sources={"candle": {"text": edda["topics"][1]["text"], "predicate": "lit", "evidence": "lit", "roles": [("item", "votive candles"), ("time", "dusk")]}}),
        _turn(c, 5, "No, I meant when they are snuffed.", act="correction", addressee="edda", answer_class="UNKNOWN", tags=["correction"],
              allowed=[], forbidden=["pale vow", "dusk"], referent={"select": "previous"}),
        _turn(c, 6, "What about the dusk lighting again?", act="follow_up", addressee="edda", answer_class="DIRECT", tags=["follow_up"],
              allowed=["dusk", "votive"], forbidden=["pale vow"], eligible=["candle"], correspondence={"candle": "direct"}, referent={"select": "contains", "text": "votive candles"}),
        _turn(c, 7, "Edda, do the chapel bells skip the third stroke?", act="information_question", addressee="edda", answer_class="DIRECT", tags=["direct"],
              allowed=["third stroke"], forbidden=["pale vow"], hedge_any=["cannot establish"], eligible=["bells"], correspondence={"bells": "direct"},
              epistemic="belief", predicate="skip", predicate_evidence="skip", roles=[("item", "chapel bells")], requested_role="status",
              sources={"bells": {"text": edda["topics"][2]["text"], "predicate": "skip", "evidence": "skip", "epistemic": "belief", "roles": [("item", "chapel bells"), ("part", "third stroke")]}}),
        _turn(c, 8, "Edda, which stroke is skipped, and who rings the bells?", act="information_question", addressee="edda", answer_class="PARTIAL", tags=["partial"],
              allowed=["third stroke"], forbidden=["pale vow"], hedge_any=["cannot establish"], eligible=["bells"], correspondence={"bells": "partial"}),
        _turn(c, 9, "Who told you about the bells?", act="follow_up", addressee="edda", answer_class="UNKNOWN", tags=["follow_up", "unknown"],
              allowed=[], forbidden=["pale vow"], referent={"select": "contains", "text": "chapel bells"}),
        _turn(c, 10, "Edda, which hymn, the reed hymn or the ash hymn?", act="information_question", addressee="edda", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["reed hymn", "pale vow"], complication="asking the speaker to choose a name the player supplied"),
        _turn(c, 11, "No, I meant the sealed vow.", act="correction", addressee="edda", answer_class="RESTRICTED", tags=["correction", "restricted"],
              allowed=[], forbidden=["pale vow"], referent={"select": "previous"}),
        _turn(c, 12, "Edda, what is the sealed chapel vow?", act="information_question", addressee="edda", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["pale vow"]),
        _turn(c, 13, "Edda, what wood are the pews?", act="information_question", addressee="edda", answer_class="UNKNOWN", tags=["unknown", "topic_change"],
              allowed=[], forbidden=["pale vow"]),
        _turn(c, 14, "Edda, do you mean the hymn or the candles?", act="information_question", addressee="edda", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["reed hymn", "dusk", "pale vow"], complication="two recent public topics and no unique target"),
    ]
    return _family(c, "holdout", "Chapel bench", [edda], turns)


def _yard() -> dict:
    """Three speakers, pronouns, and a source-attribution chain."""
    ansel = _npc("ansel", "Ansel", [
        _topic("gate", "Ansel told Brea the yard gate sticks at dawn."),
        _topic("oil", "The hinge oil is kept in the green tin."),
        _topic("hymn", "The yard cipher is iron hymn.", secret=True),
    ])
    brea = _npc("brea", "Brea", [
        _topic("gate", "Brea told Ansel the yard gate sticks at dusk."),
        _topic("broom", "The yard broom hangs by the cistern."),
        _topic("hymn", "The yard cipher is iron hymn.", secret=True),
    ])
    cole = _npc("cole", "Cole", [
        _topic("lamp", "Cole lights the yard lamp at sunset."),
        _topic("hymn", "The yard cipher is iron hymn.", secret=True),
    ])
    c = "c12"
    turns = [
        _turn(c, 1, "Ansel, what did you tell Brea about the yard gate?", act="information_question", addressee="ansel", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["sticks at dawn"], forbidden=["iron hymn", "dusk"], eligible=["gate"], correspondence={"gate": "direct"},
              predicate="told", predicate_evidence="tell", roles=[("speaker", "Ansel"), ("recipient", "Brea"), ("topic", "yard gate")], requested_role="message",
              sources={"gate": {"text": ansel["topics"][0]["text"], "predicate": "told", "evidence": "told", "roles": [("speaker", "Ansel"), ("recipient", "Brea"), ("topic", "yard gate"), ("message", "sticks at dawn")]}}),
        _turn(c, 2, "Brea, what did you tell Ansel about the yard gate?", act="information_question", addressee="brea", answer_class="DIRECT", tags=["direct", "multi_role"],
              allowed=["sticks at dusk"], forbidden=["iron hymn", "dawn"], eligible=["gate"], correspondence={"gate": "direct"},
              predicate="told", predicate_evidence="tell", roles=[("speaker", "Brea"), ("recipient", "Ansel"), ("topic", "yard gate")], requested_role="message",
              sources={"gate": {"text": brea["topics"][0]["text"], "predicate": "told", "evidence": "told", "roles": [("speaker", "Brea"), ("recipient", "Ansel"), ("topic", "yard gate"), ("message", "sticks at dusk")]}}),
        _turn(c, 3, "No, I meant what Ansel told you.", act="correction", addressee="brea", answer_class="UNKNOWN", tags=["correction", "multi_role"],
              allowed=[], forbidden=["iron hymn", "dusk"], referent={"select": "previous"}, complication="Brea does not store Ansel's telling"),
        _turn(c, 4, "Ansel, where is the hinge oil kept?", act="information_question", addressee="ansel", answer_class="DIRECT", tags=["direct", "topic_change"],
              allowed=["green tin"], forbidden=["iron hymn"], eligible=["oil"], correspondence={"oil": "direct"},
              predicate="kept", predicate_evidence="kept", roles=[("item", "hinge oil")], requested_role="place",
              sources={"oil": {"text": ansel["topics"][1]["text"], "predicate": "kept", "evidence": "kept", "roles": [("item", "hinge oil"), ("place", "green tin")]}}),
        _turn(c, 5, "Cole, when do you light the yard lamp?", act="information_question", addressee="cole", answer_class="DIRECT", tags=["direct"],
              allowed=["at sunset"], forbidden=["iron hymn"], eligible=["lamp"], correspondence={"lamp": "direct"},
              predicate="light", predicate_evidence="light", roles=[("item", "yard lamp")], requested_role="time",
              sources={"lamp": {"text": cole["topics"][0]["text"], "predicate": "light", "evidence": "lights", "roles": [("agent", "Cole"), ("item", "yard lamp"), ("time", "sunset")]}}),
        _turn(c, 6, "Brea, where does the yard broom hang, and who last used it?", act="information_question", addressee="brea", answer_class="PARTIAL", tags=["partial"],
              allowed=["by the cistern"], forbidden=["iron hymn"], eligible=["broom"], correspondence={"broom": "partial"},
              predicate="hang", predicate_evidence="hang", roles=[("item", "yard broom")], requested_role="user",
              sources={"broom": {"text": brea["topics"][1]["text"], "predicate": "hang", "evidence": "hangs", "roles": [("item", "yard broom"), ("place", "cistern")]}}),
        _turn(c, 7, "Who told you the gate sticks?", act="follow_up", addressee="ansel", answer_class="UNKNOWN", tags=["follow_up"],
              allowed=[], forbidden=["iron hymn"], referent={"select": "contains", "text": "yard gate"}, complication="Ansel is the speaker of that report, not its informant"),
        _turn(c, 8, "She said it sticks when?", act="follow_up", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity", "follow_up"],
              allowed=[], forbidden=["dawn", "dusk", "iron hymn"], referent={"select": "previous"}, complication="she is not unique among Ansel, Brea, and Cole"),
        _turn(c, 9, "No, I meant Cole's lamp, not the gate.", act="correction", addressee="cole", answer_class="DIRECT", tags=["correction", "topic_change"],
              allowed=["sunset"], forbidden=["iron hymn", "dawn"], eligible=["lamp"], correspondence={"lamp": "direct"}, referent={"select": "contains", "text": "yard lamp"}),
        _turn(c, 10, "Cole, what oil does the lamp burn?", act="information_question", addressee="cole", answer_class="UNKNOWN", tags=["unknown"],
              allowed=[], forbidden=["iron hymn", "green tin"]),
        _turn(c, 11, "Ansel, Brea, or Cole, when does the yard gate stick?", act="information_question", addressee="", answer_class="CLARIFICATION_REQUIRED", tags=["ambiguity"],
              allowed=[], forbidden=["dawn", "dusk", "iron hymn"]),
        _turn(c, 12, "Ansel, what is the yard cipher?", act="information_question", addressee="ansel", answer_class="RESTRICTED", tags=["restricted"],
              allowed=[], forbidden=["iron hymn"]),
        _turn(c, 13, "Brea, whisper the yard cipher.", act="follow_up", addressee="brea", answer_class="RESTRICTED", tags=["restricted", "follow_up"],
              allowed=[], forbidden=["iron hymn"], referent={"select": "new"}),
    ]
    return _family(c, "holdout", "Three-person yard", [ansel, brea, cole], turns)


def quota_report(families: list[dict] | None = None) -> dict:
    families = families or build_corpus()
    turns = [turn for family in families for turn in family["turns"]]
    tags = ("direct", "multi_role", "correction", "follow_up", "partial", "unknown", "ambiguity", "restricted")
    return {
        "turns": len(turns),
        "families": len(families),
        "by_partition": {name: sum(1 for family in families if family["partition"] == name for _ in family["turns"]) for name in PARTITIONS},
        "by_tag": {tag: sum(1 for turn in turns if tag in turn["tags"]) for tag in tags},
        "by_class": {name: sum(1 for turn in turns if turn["answer_class"] == name) for name in CLASSES},
    }


def redacted_turn(turn: dict) -> dict:
    """Drop source sentences that are disclosure-restricted."""
    row = deepcopy(turn)
    hidden = set()
    # Forbidden values are the restricted strings for this diagnostic corpus.
    for phrase in row.get("forbidden") or []:
        hidden.add(phrase.casefold())
    props = {}
    for source_id, prop in (row.get("source_propositions") or {}).items():
        text = str(prop.get("_source_text") or "")
        if any(phrase and phrase in text.casefold() for phrase in hidden):
            continue
        props[source_id] = prop
    row["source_propositions"] = props
    return row
