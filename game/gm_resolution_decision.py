"""Pre-narration GM resolution decision boundary.

This module decides what a turn may establish after the Resolution Contract
exists and before narration is trusted. The decision is source-owned: prose may
realize authored, runtime, mechanical, or bounded-improvisation facts, but prose
does not become the source of consequential world truth.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import re
from typing import Any, Mapping, Sequence

from game.bounded_improvisation import (
    INCIDENTAL_KIND,
    NPC_CLAIM_KIND,
    accepted_bounded_improvisation_entries,
)
from game.proposition_authority import classify_propositions, epistemic_frame
from game.resolution_contract import contract_mapping_from_resolution


DECISION_METADATA_KEY = "gm_resolution_decision"

PROVENANCE_AUTHORITATIVE = "authored_world_fact"
PROVENANCE_INCIDENTAL = "bounded_incidental"
PROVENANCE_NPC_CLAIM = "npc_claim"
PROVENANCE_OBSERVATION = "observation"
PROVENANCE_INFERENCE = "inference"
PROVENANCE_GM_INFERENCE = "gm_inference"
PROVENANCE_PLAYER_HYPOTHESIS = "player_hypothesis"
PROVENANCE_SPECULATION = "speculation"
PROVENANCE_GENERATED_PROPOSAL = "generated_proposal"

OUTCOME_ESTABLISHED = "established_or_retrieved"
OUTCOME_INCIDENTAL = "bounded_incidental"
OUTCOME_EPISTEMIC = "epistemically_qualified"
OUTCOME_PROTECTED = "consequential_protected"
OUTCOME_MUTATION = "state_mutation"
OUTCOME_NONRESOLUTION = "safe_nonresolution"
OUTCOME_AUTHORIZED_STATE = "authorized_state_outcome"
OUTCOME_UNRESOLVED = "consequentially_unresolved"

PERSIST_WORLD = "world_truth"
PERSIST_INCIDENTAL = "runtime_incidental"
PERSIST_CLAIM = "claim_only"
PERSIST_NONE = "do_not_persist"

AUTH_WORLD = "world_truth"
AUTH_RUNTIME = "runtime_fact"
AUTH_INCIDENTAL = "bounded_incidental"
AUTH_CLAIM = "claim_only"
AUTH_OBSERVATION = "observation"
AUTH_UNAUTHORIZED = "unauthorized"
AUTH_INFERENCE = "inference"

EPISTEMIC_ACT_ESTABLISH = "establish"
EPISTEMIC_ACT_INFER = "infer"
EPISTEMIC_ACT_LEAVE_UNRESOLVED = "leave_unresolved"

STATUS_ESTABLISHED = "established"
STATUS_INFERRED = "inferred"
STATUS_HYPOTHESIS = "hypothesis"
STATUS_UNRESOLVED = "unresolved"
STATUS_POSSIBLE = "possible"

REL_OBSERVATION = "observation"
REL_CAUSAL = "causal"
REL_EVIDENTIAL = "evidential"
REL_EPISTEMIC_STATUS = "epistemic_status"
REL_PREDICATE = "ordinary_predicate"
REL_GAMEPLAY_LEAD = "gameplay_lead"

ROLE_MUST_STATE = "MUST_STATE"
ROLE_MAY_STATE = "MAY_STATE"
ROLE_MAY_INFER = "MAY_INFER"
ROLE_MUST_PRESERVE_UNCERTAINTY = "MUST_PRESERVE_UNCERTAINTY"
ROLE_INCIDENTAL_TEXTURE = "INCIDENTAL_TEXTURE"

DECLARATION_MODE_REALIZE = "realize"
DECLARATION_MODE_PROPOSE = "propose"
STRUCTURED_ENVELOPE_VERSION = 1

TEMPORAL_PROVENANCE_KEY = "narration_temporal_provenance"
TEMPORAL_PROVENANCE_VERSION = 1


_SENTENCE_RE = re.compile(r"[^.!?]+(?:[.!?]+|$)")
_QUOTE_SPAN_RE = re.compile(r'["“][^"”]*["”]')
_CLAIM_FRAME_RE = re.compile(
    r"\b(?:says?|said|tells?|told|claims?|claimed|heard|rumou?r|word is|"
    r"recollects?|remembers?|believes?|thinks?|suspects?|guesses?|supposes?)\b",
    re.IGNORECASE,
)
_UNCERTAIN_FRAME_RE = re.compile(
    r"\b(?:might|may|could|perhaps|maybe|not sure|cannot verify|can't verify|"
    r"not certain|couldn't swear|could not swear|believes?|thinks?|suspects?|recollects?|remembers?|"
    r"heard|rumou?r|word is|hearsay|speculat(?:e|es|ion)|guess(?:es|ed)?|possibilit(?:y|ies)|can't rule out|cannot rule out)\b",
    re.IGNORECASE,
)
_NONASSERTION_FRAME_RE = re.compile(
    r"\b(?:no one(?: here)? can verify|cannot verify|can't verify|could not verify|"
    r"couldn't verify|cannot say|can't say|cannot establish|can't establish|"
    r"does not establish|doesn't establish|no reliable source can verify|no way to confirm)\b",
    re.IGNORECASE,
)
_INCIDENTAL_RE = re.compile(
    r"\b(?:smells?|sounds?|rain|mud|lantern|cloak|sleeve|shrugs?|nods?|"
    r"stew|broth|barley|onion|pepper|worn|weathered|scuffed|crowd|murmur|"
    r"torch(?:light)?|queue|cloth|wood|stone|dust|smoke|color|colour)\b",
    re.IGNORECASE,
)
_CONSEQUENTIAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "command_authority",
        re.compile(
            r"\b(?:Captain\s+[A-Z][a-z]+|[A-Z][a-z]+\s+[A-Z][a-z]+)\b[^.!?]{0,96}"
            r"\b(?:commands?|ordered|orders?|in charge|authority|reports? to|answers? to)\b"
            r"|\b(?:commands?|ordered|orders?|in charge|authority|reports? to|answers? to)\b[^.!?]{0,96}"
            r"\b(?:Captain\s+[A-Z][a-z]+|[A-Z][a-z]+\s+[A-Z][a-z]+)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "official_orders_or_procedures",
        re.compile(
            r"\b(?:official|posted|standing|formal|watch|gate|patrol|roster|seal|clerk|captain)\b"
            r"[^.!?]{0,80}\b(?:orders?|ordered|procedures?|protocol|requires?|must|assigned|detailed|posted|copied|annotated)\b"
            r"|\b(?:orders?|ordered|procedures?|protocol|roster|seal|annotation|posting)\b"
            r"[^.!?]{0,80}\b(?:official|watch|gate|patrol|captain|clerk|dated|copied|posted)\b",
            re.IGNORECASE,
        ),
    ),
    (
        # A route noun must already be in the match. `splits` and `forks` are
        # branch verbs of that noun. Copular "is split" is not a route head,
        # so nearby "evidence" does not make object damage into geography.
        "patrol_route_or_geography",
        re.compile(
            r"\b(?:patrol|tracks?|trail|route|road|path|fork|marker|watchtower|milestone|ridge|northwest|east road)\b"
            r"[^.!?]{0,90}\b(?:route|road|path|forks?|marker|watchtower|milestone|splits?|turn(?:ed)?|changed|last seen|sent)\b"
            r"|\b(?:route|road|path|fork|marker|watchtower|milestone)\b"
            r"[^.!?]{0,90}\b(?:patrol|tracks?|trail|broken twigs?|bootprints?|evidence)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "physical_investigative_evidence",
        re.compile(
            r"\b(?:bootprints?|footprints?|tracks?|broken twigs?|snapped branches?|blood|drag marks?|fresh mud|ash traces?)\b"
            r"|\b(?:a|an|fresh|deep|long|faint|new)\s+scrapes?\b"
            r"|\bscrapes?\s+(?:on|along|across|against|into|mark|marks)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "notice_roster_history",
        re.compile(
            r"\b(?:notice|posting|board|roster|seal|annotation|handwriting|ink|date|dated|chronology|yesterday|before dawn)\b"
            r"[^.!?]{0,100}\b(?:posted|copied|listed|names?|orders?|seal|annotated|changed|replaced|dated|issued|provenance)\b"
            r"|\b(?:posted|copied|listed|names?|orders?|seal|annotated|changed|replaced|dated|issued)\b"
            r"[^.!?]{0,100}\b(?:notice|posting|board|roster|seal|annotation|route|patrol)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "historical_causal_fact",
        re.compile(
            r"\b(?:used to|previously|earlier|last week|last month|changed after|because|since then|history|historical)\b"
            r"[^.!?]{0,100}\b(?:route|patrol|notice|orders?|road|watch|gate)\b",
            re.IGNORECASE,
        ),
    ),
)
_MOVEMENT_RE = re.compile(
    r"\byou\s+(?:leave|depart|travel|head|walk|go|follow|take|arrive|reach|come|cross|make your way)\b"
    r"[^.!?]{0,100}\b(?:road|path|trail|route|fork|marker|watchtower|milestone|gatehouse|crossroads|ridge|woods?|tower|mill)\b"
    r"|\barrive\s+(?:at|in|to)\s+(?:the\s+)?[A-Za-z][A-Za-z0-9 '\-]{2,60}\b",
    re.IGNORECASE,
)
_STATEFUL_ASSERTION_RE = re.compile(
    r"\b(?:"
    r"(?:is|are|was|were|has|have|had)\s+(?:secretly|actually|already|recently|now|no longer)\b"
    r"|(?:belongs?|belonged|controls?|controlled|contains?|contained|issued|ordered|"
    r"collapsed|burned|flooded|poisoned|departed|arrived|treated|hid|stole|killed|cut|"
    r"murders?|murdered|betrays?|betrayed|opens?|opened|closes?|closed|locks?|locked|"
    r"unlocks?|unlocked|buys?|bought|sells?|sold|gives?|grants?|issues?|allows?|owns?|owned)\b"
    r"|\blets?\s+you\s+pass\b"
    r"|\byou\s+(?:discover|find|spot|uncover)\b[^.!?]{0,80}\b(?:hidden|secret|map|clue|tunnel|passage|vault|cache|letter|ledger|evidence)\b"
    r"|\b(?:is|are|was|were)\s+(?:damaged|missing|ill|locked|unlocked|empty|burned|burnt|severed|abandoned)\b"
    r"|(?:there\s+is|there\s+are)\s+(?:a|an|the)\s+(?:hidden|secret|buried|sealed)\b"
    r"|\b(?:secret|hidden|buried|sealed)\s+(?:tunnel|passage|map|door|vault|route|cache|letter|ledger|clue|fact)\b"
    r")",
    re.IGNORECASE,
)
_LOW_STAKES_STATE_RE = re.compile(
    r"\b(?:smells?|sounds?|looks?|seems?|feels?|tastes?|is wet|is muddy|is worn|is scuffed|"
    r"rain|mud|lantern|cloak|sleeve|queue|crowd|murmur|dust|smoke|soot|hangs?|loosely|musty|cold|settled)\b",
    re.IGNORECASE,
)
# Present-tense forms of consequential acts. Existence coverage must not
# launder these into an "the NPC is here" observation.
_EXISTENCE_ACTION_RE = re.compile(
    r"\b(?:kills?|murders?|attacks?|stabs?|opens?|closes?|locks?|unlocks?|"
    r"departs?|arrives?|enters?|orders?|commands?|steals?|stole|buys?|bought|sells?|sold|gives?|grants?|issues?|allows?|"
    r"poisoned|betrayed|collapsed)\b",
    re.IGNORECASE,
)
_REALIZATION_WRAPPER_RE = re.compile(r"^(?:word is,\s*)", re.IGNORECASE)
# A preseal ignorance line is not a successful answer. It must not seal merely
# because the speaker is an existing NPC.
_IGNORANCE_SEAL_RE = re.compile(
    r"\b(?:i don't know|i do not know|i dont know|cannot answer|can't answer|do not know)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GMProposedFact:
    text: str
    provenance: str
    consequence: str
    authorized: bool
    reason_codes: list[str] = field(default_factory=list)
    authority: str = AUTH_UNAUTHORIZED
    persistence: str = PERSIST_NONE
    source_ref: str = ""
    outcome_classification: str = OUTCOME_UNRESOLVED
    semantic_identity: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NarratedClaim:
    text: str
    semantic_identity: dict[str, Any] = field(default_factory=dict)
    provenance: str = PROVENANCE_GENERATED_PROPOSAL
    authority: str = AUTH_UNAUTHORIZED
    epistemic_status: str = STATUS_UNRESOLVED
    relation_kind: str = REL_PREDICATE
    persistence: str = PERSIST_NONE
    authorized: bool = False
    source_ref: str = ""
    source_turn: int | None = None
    source_scene: str = ""
    reason_codes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RealizationClaim:
    claim_id: str
    semantic_identity: dict[str, Any] = field(default_factory=dict)
    provenance: str = PROVENANCE_GENERATED_PROPOSAL
    authority: str = AUTH_UNAUTHORIZED
    epistemic_status: str = STATUS_UNRESOLVED
    modality: str = ""
    realization_role: str = ROLE_MAY_STATE
    persistence: str = PERSIST_NONE
    source_ref: str = ""
    text: str = ""
    relation_kind: str = REL_PREDICATE
    premise_claim_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DeclaredRealizationClaim:
    declaration_id: str
    declaration_mode: str = DECLARATION_MODE_REALIZE
    semantic_identity: dict[str, Any] = field(default_factory=dict)
    provenance_requested: str = PROVENANCE_GENERATED_PROPOSAL
    epistemic_status: str = STATUS_UNRESOLVED
    modality: str = ""
    realization_role: str = ROLE_MAY_STATE
    relation_kind: str = REL_PREDICATE
    source_claim_id: str = ""
    text: str = ""
    premise_claim_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GMRealizationEnvelope:
    declared_claims: list[DeclaredRealizationClaim] = field(default_factory=list)
    narration: str = ""
    schema_version: int = STRUCTURED_ENVELOPE_VERSION
    legacy_fallback: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "declared_claims": [claim.as_dict() for claim in self.declared_claims],
            "narration": self.narration,
            "legacy_fallback": self.legacy_fallback,
        }


@dataclass(frozen=True)
class GMResolutionDecision:
    contract_id: str
    resolution_method: str
    outcome_classification: str
    established_fact_refs: list[str] = field(default_factory=list)
    proposed_facts: list[GMProposedFact] = field(default_factory=list)
    permitted_state_mutations: list[dict[str, Any]] = field(default_factory=list)
    persistence_policy: str = PERSIST_NONE
    narration_constraints: list[str] = field(default_factory=list)
    unresolved_consequential_questions: list[str] = field(default_factory=list)
    unresolved_qualifiers: list[str] = field(default_factory=list)
    answer_relations: list[dict[str, Any]] = field(default_factory=list)
    epistemic_acts: list[dict[str, Any]] = field(default_factory=list)
    realization_claims: list[RealizationClaim] = field(default_factory=list)
    executable_obligations: dict[str, Any] = field(default_factory=dict)
    authority_algorithm: str = "proposition_claim_control_v1"

    def as_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["proposed_facts"] = [fact.as_dict() for fact in self.proposed_facts]
        out["realization_claims"] = [claim.as_dict() for claim in self.realization_claims]
        return out


def _clean(value: Any, *, limit: int = 240) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:limit]


def _sentences(text: str | None) -> list[str]:
    raw = _clean(text, limit=4000)
    return [_clean(match.group(0), limit=600) for match in _SENTENCE_RE.finditer(raw) if _clean(match.group(0))]


def _outside_quotes(text: str) -> str:
    return _QUOTE_SPAN_RE.sub(" ", text or "")


def _authored_corpus(scene: Mapping[str, Any] | None, world: Mapping[str, Any] | None, extra: str = "") -> str:
    parts: list[str] = [str(extra or "")]
    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
    if isinstance(inner, Mapping):
        for key in ("visible_facts", "opening_seed_facts", "journal_seed_facts", "summary", "location"):
            value = inner.get(key)
            if isinstance(value, list):
                parts.extend(str(item) for item in value if str(item).strip())
            elif isinstance(value, str) and value.strip():
                parts.append(value)
        for exit_row in inner.get("exits") or []:
            if isinstance(exit_row, Mapping):
                parts.append(str(exit_row.get("label") or ""))
                parts.append(str(exit_row.get("target_scene_id") or exit_row.get("targetSceneId") or ""))
    if isinstance(world, Mapping):
        for npc in world.get("npcs") or []:
            if isinstance(npc, Mapping):
                parts.append(str(npc.get("name") or ""))
                parts.append(str(npc.get("role") or ""))
                for topic in npc.get("topics") or []:
                    from game.dialogue_authority import npc_source_permitted
                    if isinstance(topic, Mapping) and npc_source_permitted(npc, topic):
                        parts.append(str(topic.get("text") or ""))
    return "\n".join(part for part in parts if str(part).strip())


def _grounded(sentence: str, corpus: str) -> bool:
    norm = _clean(sentence, limit=500).lower().strip(" .!?")
    if not norm:
        return False
    if norm in str(corpus or "").lower():
        return True
    tokens = [tok for tok in re.findall(r"[a-z0-9']+", norm) if len(tok) >= 4]
    if len(tokens) < 2:
        return False
    corpus_tokens = set(re.findall(r"[a-z0-9']+", str(corpus or "").lower()))
    return bool(tokens and set(tokens).issubset(corpus_tokens))


def _token_set(text: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-z0-9']+", str(text or "").lower())
        if len(tok) >= 4 and tok not in {"that", "this", "with", "from", "into", "they", "their", "your", "there"}
    }


def _norm_phrase(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", str(value or "").lower()))


def _identity_terms(identity: Mapping[str, Any], key: str) -> list[str]:
    values: list[Any] = []
    value = identity.get(key)
    if isinstance(value, list):
        values.extend(value)
    elif value:
        values.append(value)
    aliases = identity.get(f"{key}_aliases")
    if isinstance(aliases, list):
        values.extend(aliases)
    terms: list[str] = []
    for item in values:
        norm = _norm_phrase(item).replace("_", " ")
        if norm and norm not in terms:
            terms.append(norm)
    return terms


def _qualifier_terms(identity: Mapping[str, Any], key: str) -> list[str]:
    qualifiers = identity.get("qualifiers")
    if not isinstance(qualifiers, Mapping):
        return []
    raw = qualifiers.get(key)
    values = raw if isinstance(raw, list) else [raw] if raw else []
    aliases = qualifiers.get(f"{key}_aliases")
    if isinstance(aliases, list):
        values.extend(aliases)
    out: list[str] = []
    for item in values:
        norm = _norm_phrase(item).replace("_", " ")
        if norm and norm not in out:
            out.append(norm)
    return out


def _text_has_any(text: str, terms: Sequence[str]) -> bool:
    norm = _norm_phrase(text)
    return any(term and term in norm for term in terms)


def _text_has_subject_or_head_with_value(text: str, subject_terms: Sequence[str], value_terms: Sequence[str]) -> bool:
    if _text_has_any(text, subject_terms):
        return True
    norm = _norm_phrase(text)
    if value_terms and not _text_has_any(text, value_terms):
        return False
    for term in subject_terms:
        parts = [part for part in term.split() if len(part) >= 4]
        if len(parts) >= 2 and re.search(rf"\b{re.escape(parts[-1])}\b", norm):
            return True
    return False


_CLAUSE_SPLIT_RE = re.compile(r"\s*(?:;|—|--|\s+but\s+|\s+yet\s+|,\s+(?:but\s+|yet\s+)?)\s*", re.IGNORECASE)
_NEGATION_ADVERB_RE = (
    r"(?:currently|still|yet|even|really|actually|clearly|now|already|presently)\s+"
)
_UNKNOWN_SLOT_RE = re.compile(
    r"\b(?:no one|nobody|nothing|no evidence)\b(?:\s+\w+){0,8}\b(?:knows?|knew|can say|can tell|saw|know)\b"
    r"|\b(?:don't|do not|can't|cannot)\s+know\s+(?:who|whom|when|why)\b"
    r"|\b(?:who|whom|when|why|what|cause|actor|timing)\b(?:\s+\w+){0,12}\b(?:unknown|unclear|unsettled|not established|not known|a mystery|remains unclear)\b"
    r"|\b(?:unknown|unclear|not established|not known)\b(?:\s+\w+){0,8}\b(?:who|whom|when|why|cause|actor|time)\b"
    r"|\bnothing (?:here )?establishes\b"
    r"|\b(?:the\s+)?(?:cause|actor|time|when it happened|who did it|what caused it)\b(?:\s+\w+){0,6}\b(?:is|remains|stays)\s+(?:not\s+)?(?:unknown|unclear|unsettled|not established|not known|unseen)\b"
    r"|\b(?:what|who|whom|when|why|cause|actor|time|timing)\b(?:\s+\w+){0,14}\b(?:remain|remains|stay|stays|is|are)\s+(?:unseen|unknown|unclear|unsettled|not known|not established)\b"
    r"|\bremain(?:s)?\s+unseen\b"
    r"|\bno one here knows\b"
    r"|\b(?:is|remains)\s+unclear\b"
    r"|\b(?:we|you|i)\s+(?:do not|don't|cannot|can't)\s+know\b"
    r"|\b(?:cause|actor|time|timing|sequence|explanation)\s+remains?\s+(?:unknown|unclear|unresolved)\b"
    r"|\bnothing\s+(?:(?:established\s+)?here\s+)?(?:identifies|establishes|tells?)\b"
    r"|\b(?:cannot|can't)\s+tell\s+from\s+(?:this|that|it)\b"
    r"|\bonly\s+a\s+possibility\b",
    re.IGNORECASE,
)
_AGENT_FILL_RE = re.compile(
    r"\b(?!The\b|A\b|An\b|This\b|That\b)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:cracked|broke|broken|damaged|caused|smashed|cut|opened|burned|struck)\b"
    r"|\b(?:cracked|broken|damaged|caused|smashed|broke)\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)
_TIME_FILL_RE = re.compile(
    r"\b(?:yesterday|last night|this morning|at dawn|at dusk|before dawn|days ago|last week)\b"
    r"|\b(?:overnight|during the night|before sunrise|after sunrise|a few hours old|few hours old|sometime before dawn)\b"
    r"|\b(?:cracked|broke|broken|happened|damaged|split|forced|done|came through)\s+(?:it\s+)?(?:yesterday|today|last night|at dawn|overnight|before sunrise)\b",
    re.IGNORECASE,
)
_CAUSE_FILL_RE = re.compile(
    r"\b(?:because|caused by|due to|as a result of)\b"
    r"|\b(?:possibly|perhaps|maybe)\s+from\b"
    r"|\b(?:died from|death came from|killed|finished|explains?|halted|fouled|sabotaged|ruined)\b",
    re.IGNORECASE,
)
_CAUSAL_RELATION_RE = re.compile(
    r"\b(?:because|caused by|due to|as a result of|therefore|so that|which caused|"
    r"causing|led to|leading to|responsible for|failed to|failure to|"
    r"(?:possibly|perhaps|maybe)\s+from|"
    r"(?:likely|possible|probable)\s+cause|seems?\s+(?:a\s+)?(?:likely|possible|probable)\s+cause|"
    r"(?:probably|likely|possibly)\s+(?:bent|broke|cracked|damaged|caused|left|opened))\b",
    re.IGNORECASE,
)
_EVIDENTIAL_RELATION_RE = re.compile(
    r"\b(?:shows?|showed|proves?|proved|indicates?|indicated|suggests?|suggested|"
    r"points? to|pointing to|establish(?:es|ed)?|makes? (?:it )?clear|"
    r"demonstrates?|confirms?|reveals?|means?)\b",
    re.IGNORECASE,
)
_CERTAINTY_UPGRADE_RE = re.compile(
    r"\b(?:proves?|proved|establish(?:es|ed)?|makes? (?:it )?clear|"
    r"points? conclusively to|confirms?|confirmed|demonstrates?|no doubt|now we know|clearly|"
    r"(?:cause|actor|time|timing|sequence|explanation|reason)\s+is\s+clear)\b",
    re.IGNORECASE,
)
_DEFINITE_HISTORY_RE = re.compile(
    r"\b(?:was|were|had been|has been|left|cut|removed|destroyed|burned|poisoned|"
    r"fired|unfired|never|overnight|last night|before dawn|to hide|in order to)\b",
    re.IGNORECASE,
)
# Location is an event-site only as the complement of the event verb.
# "happened here" counts. "when it happened ... unseen here" does not:
# the deictic belongs to the epistemic predicate, not the event.
_EVENT_SITE_RE = re.compile(
    r"\b(?:happened|occurred|befell|took place)\s+"
    r"(?:(?:right|just|still)\s+)?"
    r"(?:here|there|inside|in silence)\b"
    r"|\b(?:happened|occurred|befell|took place)\s+"
    r"(?:(?:right|just)\s+)?"
    r"(?:in|at|inside|within)\s+(?:the\s+|a\s+|an\s+)?[a-z]",
    re.IGNORECASE,
)
_ATTRIBUTED_SOURCE_RE = re.compile(
    r"\b(?:says?|said|tells?|told|claims?|claimed|rumou?rs?|word is|"
    r"i heard|i have heard|i've heard|they say|people say|someone said|"
    r"told me|i was told|from what i heard|"
    r"suspects?|believes?|thinks?|remembers?|recollects?|guesses?|supposes?)\b",
    re.IGNORECASE,
)
_NARRATOR_MODAL_RE = re.compile(
    r"\b(?:you|one)\s+(?:might|could|may)\b|\bperhaps\b|\bmaybe\b",
    re.IGNORECASE,
)
_EPISTEMIC_LIMIT_RE = re.compile(
    r"\b(?:"
    r"(?:we|you|i)\s+(?:do not|don't|cannot|can't)\s+know"
    r"|(?:cause|actor|time|timing|sequence|explanation)\s+(?:is|remains?)\s+(?:unknown|unclear|unresolved)"
    r"|(?:not|isn't|is\s+not)\s+established"
    r"|only\s+a\s+possibility"
    r"|nothing\s+(?:(?:established\s+)?here\s+)?(?:identifies|establishes|tells?)"
    r"|(?:cannot|can't)\s+tell\s+from\s+(?:this|that|it)"
    r"|does\s+not\s+(?:identify|establish|tell|prove|show)"
    r"|no\s+way\s+to\s+confirm"
    r"|supports?\s+(?:several|multiple)\s+possibilities?\s+but\s+no\s+confirmed"
    r")\b",
    re.IGNORECASE,
)
# Epistemic parent about an embedded proposition. The proposition itself is
# identified by premise_claim_ids, not by a domain noun list.
_EPISTEMIC_PARENT_REALIZATION_RE = re.compile(
    r"\b(?:cause|reason|actor|culprit|explanation|timing)\b.{0,80}\b(?:unknown|unresolved|uncertain|unclear|not known|is not known|isn't known|not established|cannot be determined|can't be determined|remains)\b"
    r"|\b(?:who|whom|when|why)\b.{0,80}\b(?:unknown|unresolved|uncertain|unclear|not known|is not known|not established|cannot be determined|can't be determined|cannot|can't)\b"
    r"|\b(?:cannot|can't)\s+be\s+(?:determined|established|known)\b"
    r"|\b(?:is|remains|stays)\s+(?:unknown|unresolved|uncertain|unclear|not known)\b",
    re.IGNORECASE,
)
_CONDITIONAL_MARKER_RE = re.compile(
    r"\b(?:if|assuming|assume|suppose|supposing|whether)\b",
    re.IGNORECASE,
)
_EPISTEMIC_BOILERPLATE = frozenset(
    {
        "about",
        "actor",
        "actors",
        "assume",
        "assuming",
        "because",
        "cannot",
        "cause",
        "caused",
        "causes",
        "certainty",
        "could",
        "determined",
        "does",
        "established",
        "evidence",
        "exact",
        "explanation",
        "happened",
        "here",
        "however",
        "identify",
        "identifies",
        "involved",
        "known",
        "matter",
        "maybe",
        "might",
        "nobody",
        "nothing",
        "occurred",
        "perhaps",
        "possible",
        "possibly",
        "precise",
        "produce",
        "produced",
        "reason",
        "reasons",
        "remain",
        "remains",
        "responsible",
        "should",
        "someone",
        "status",
        "suppose",
        "supposing",
        "tell",
        "tells",
        "thing",
        "things",
        "time",
        "timing",
        "uncertain",
        "unclear",
        "unknown",
        "unresolved",
        "visible",
        "what",
        "when",
        "where",
        "whether",
        "which",
        "whom",
        "would",
    }
)
# Generic semantic-category nouns already used by the interpretation recognizer.
# They are not embedded propositions by themselves.
_EPISTEMIC_FRAME_NOUNS = frozenset({"damage", "condition", "observation"})
_BELOW_CEILING_PROVENANCE = frozenset(
    {
        PROVENANCE_PLAYER_HYPOTHESIS,
        PROVENANCE_GM_INFERENCE,
        PROVENANCE_GENERATED_PROPOSAL,
        PROVENANCE_SPECULATION,
    }
)
_GENERATED_LEAD_RE = re.compile(
    r"\b(?:"
    r"(?:inspect|check|search|examine|study|look\s+(?:at|through|inside))\b[^.!?]{0,90}"
    r"\b(?:clue|evidence|useful|relevant|overlooked|answer|detail)"
    r"|(?:contains?|holds?|may\s+contain|might\s+contain|could\s+contain)\b[^.!?]{0,70}"
    r"\b(?:clue|evidence|message|answer|detail)"
    r"|(?:worth|useful)\s+(?:checking|inspecting|examining|investigating)"
    r")\b",
    re.IGNORECASE,
)
_QUALIFIED_INFERENCE_RE = re.compile(
    r"\b(?:might|may|could|perhaps|maybe|possibilit(?:y|ies)|"
    r"cannot rule out|can't rule out|suggests?|points? to|what can i infer)\b",
    re.IGNORECASE,
)
# Same unresolved-status idea as the unknown-slot and epistemic-parent recognizers.
# Used to classify the status operation. It does not exempt neighboring claims.
_UNRESOLVED_STATUS_EQUIVALENT_RE = re.compile(
    r"\b(?:is|are|remains?|stays?)\s+(?:unknown|unresolved|uncertain|unclear|not\s+known)\b"
    r"|\b(?:cannot|can't)\s+be\s+(?:determined|established|known)\b"
    r"|\b(?:cannot|can't)\s+determine\b",
    re.IGNORECASE,
)
# Verbs that license a qualified inference. They are not also evidential establishment.
_LICENSED_INFERENCE_HEDGE_VERB_RE = re.compile(
    r"\b(?:suggests?|suggested|points?\s+to|pointing\s+to|indicates?|indicated)\b",
    re.IGNORECASE,
)
# Epistemic-slot subjects of an unresolved-status predicate. They are the status
# claim, not a new consequential noun. "motive" is intentionally absent.
_UNRESOLVED_STATUS_SUBJECTS = frozenset(
    {
        "culprit",
        "culprits",
        "explanation",
        "explanations",
        "possibilities",
        "possibility",
        "sequence",
    }
)
# Modifiers that sit inside an unresolved-status predicate. They are not nouns.
_UNRESOLVED_STATUS_MODIFIERS = frozenset(
    {
        "already",
        "completely",
        "currently",
        "entirely",
        "fully",
        "merely",
        "presently",
        "quite",
        "really",
        "simply",
        "still",
        "truly",
        "wholly",
    }
)
_NEGATION_GOVERNS_RE = re.compile(
    r"\b(?:cannot|can't|can\s+not|could\s+not|couldn't|is\s+not|isn't|are\s+not|aren't|"
    r"was\s+not|wasn't|not|never|nothing|nobody|no\s+one|no)\b(?:\s+\w+){0,6}\s*$",
    re.IGNORECASE,
)
# "a possible cause" names a qualified possibility. It is not a cause connective.
_NAMED_POSSIBILITY_CAUSE_RE = re.compile(
    r"\b(?:seems?\s+(?:a\s+)?)?(?:likely|possible|probable)\s+cause\b",
    re.IGNORECASE,
)
_ORPHAN_DIALOGUE_ATTRIBUTION_RE = re.compile(
    r"\b(?:says|said|replies|replied|answers|answered|adds|added|asks|asked)"
    r"(?:\s+(?:quietly|softly|evenly|flatly|briefly))?\s*[,.!?]?\s*$",
    re.IGNORECASE,
)
_DEFINITE_PHRASE_RE = re.compile(
    r"\b(?:the|this|that)\s+((?:[a-z']+\s+){0,5}[a-z']+)",
    re.IGNORECASE,
)
_DEFINITE_STOP = frozenset(
    {
        "about",
        "after",
        "around",
        "before",
        "changes",
        "condition",
        "disruption",
        "further",
        "other",
        "same",
        "scene",
        "there",
        "thing",
        "things",
        "this",
        "those",
        "these",
        "what",
        "where",
        "which",
        "while",
        "with",
    }
)
_PRESENT_ONWARD_RE = re.compile(
    r"\b(?:leads?|leading|climbs?|continues?|runs)\s+(?:up|upward|upwards|onward|further|on)\b"
    r"|\bstill\s+(?:leads?|climbs?|continues?)\b"
    r"|\bfurther exploration\b",
    re.IGNORECASE,
)
_NO_ARRIVAL_CONSTRAINT = "Do not narrate arrival. The movement did not resolve."
_DEPARTURE_EXIT_CONSTRAINT = (
    "Facts marked departure belong to the scene being left. "
    "A departure exit is the route taken, not an onward exit from the destination."
)
_SUPPORTING_SOCIAL_CONSTRAINT = "Acknowledge the committed social act ({act}) in the narration."
_GROUP_PLACE_RE = re.compile(
    r"\b(?:known|said|reputed)\s+to\s+(?:gather|meet|assemble|congregate)\b"
    r"|\b(?:gathers?|meets?|assembles?|congregates?)\s+(?:at|in|by|near|on)\b"
    r"|\b(?:based|quartered|headquartered)\s+(?:at|in)\b",
    re.IGNORECASE,
)
_RESIDUE_ASSERT_RE = re.compile(
    r"\b(?:no|not|without)\s+(?:obvious\s+)?(?:splashes?|spills?|stains?|marks?)\b"
    r"|\b(?:splashes?|spills?|stains?)\s+(?:mar|mark|cover|stain)\b",
    re.IGNORECASE,
)
_NEGATIVE_EVIDENCE_RE = re.compile(
    r"\b(?:"
    r"no\s+(?:hint|sign|trace|evidence|mark|marks|footprints?|tracks?|blood|disturbance|reaction|movement|change)\b"
    r"|without\s+(?:any\s+)?(?:hint|sign|trace|evidence|footprints?|tracks?|blood|disturbance)"
    r"|nothing\s+(?:else\s+)?(?:[a-z'\s]{0,40}\s+)?(?:appears|seems|looks)\s+(?:moved|disturbed|changed|missing)"
    r"|nobody\s+(?:reacted|responded|noticed|saw|entered)"
    r"|no\s+one\s+(?:reacted|responded|noticed|saw|entered)"
    r")",
    re.IGNORECASE,
)
_SPECIFIC_LEAD_RE = re.compile(
    r"\b(?:"
    r"(?:ask|question|talk\s+to|speak\s+with|check(?:ing)?\s+with)\b[^.!?]{0,90}\b(?:who|what|where|when|why|whether|about|used|saw|knows?|happened|responsible)"
    r"|[a-z][a-z'\s]{1,60}\s+(?:may|might|could)\s+know\b"
    r"|(?:ledger|log|notes?|records?|register|roster)\s+(?:may|might|could)\s+(?:contain|show|name|identify|tell)"
    r")",
    re.IGNORECASE,
)
_UNDECLARED_CAUSAL_AGENT_RE = re.compile(
    r"\b[a-z][a-z'\-]{2,}\s+(?:cracked|broke|damaged|bent|sheared|poisoned|sabotaged|ruined)\b"
    r"|\b(?:cracked|broken|damaged|bent|sheared|poisoned|sabotaged|ruined)\s+by\s+[a-z]",
    re.IGNORECASE,
)
_CLAIM_CONTROL_DEICTIC_RE = re.compile(
    r"\b(?:it|this|that|the damage|the break-in|the death|their death|those two details|taken together)\b",
    re.IGNORECASE,
)
_ACTOR_ATTRIBUTION_RE = re.compile(
    r"\b(?:someone|whoever|two people|one person|the thieves|thieves|workers?|hands)\b"
    r"[^.!?]{0,80}\b(?:broke|cracked|cut|did|done|forced|searched|entered|came through|climbed|removed|took|carried|destroyed|worked|fled|responsible)\b"
    r"|\b(?:did this|did that|was responsible|were responsible|belongs? to|was\s+(?:the\s+)?[a-z][a-z'\s]{1,48}\s+work)\b"
    r"|\b(?:the|a|an)\s+[a-z][a-z']+\s+(?:cut|broke|destroyed|removed|took|fled|did)\b"
    r"|\b(?:the|a|an)\s+[a-z][a-z']+\s+(?:must\s+have|may\s+have|might\s+have|could\s+have)\s+(?:left|opened|closed|cut|broke|damaged|used|entered)\b"
    r"|\b[a-z][a-z']+(?:\s+(?:hands|workers?|knife))\s+(?:did|broke|cut|destroyed|removed|worked)\b",
    re.IGNORECASE,
)
_EVENT_CAUSE_ATTRIBUTION_RE = re.compile(
    r"\b(?:died from|death came from|killed (?:it|them|him|her)|what finished|finished (?:it|them|him|her)|explains? the|got into|"
    r"(?:seems?|appears?|looks?)\s+(?:a\s+)?(?:likely|possible|probable)\s+cause|"
    r"(?:likely|possible|probable)\s+cause|caused\s+(?:it|this|that|the|damage))\b",
    re.IGNORECASE,
)
_EVENT_HISTORY_ASSERTION_RE = re.compile(
    r"\b(?:break-in happened|happened overnight|used to\s+\w+|stood before|"
    r"removed during|took it after|carried it off|came through|climbed inside|"
    r"searched the|worked on it|fled toward|got into|destroyed it|forced sometime|was done|"
    r"only a few hours old|few hours old)\b",
    re.IGNORECASE,
)
_POLAR_Q_RE = re.compile(
    r"\b(?:is|are|was|were|does|do|did|has|have)\s+"
    r"(?:the\s+|a\s+|an\s+|this\s+|that\s+)?"
    r"(.+?)\s+"
    r"(?:still\s+|currently\s+|now\s+|already\s+)?"
    r"([a-z][a-z'\-]{2,})"
    r"(?:\s|$|[?.!,])",
    re.IGNORECASE,
)
_QUESTION_ACTOR_RE = re.compile(r"\bwho\b", re.IGNORECASE)
_QUESTION_TIME_RE = re.compile(r"\bwhen\b", re.IGNORECASE)
_QUESTION_CAUSE_RE = re.compile(r"\b(?:why|what caused|what happened|what befell)\b", re.IGNORECASE)


def _clauses(text: str) -> list[str]:
    parts = [part.strip() for part in _CLAUSE_SPLIT_RE.split(str(text or "")) if part.strip()]
    return parts or [str(text or "").strip()]


def _negation_scopes_over(text: str, terms: Sequence[str]) -> bool:
    """Negation applies only to the predicate it sits on, not every fact in the sentence."""
    usable = [term for term in terms if term]
    if not usable:
        return False
    for clause in _clauses(text):
        if _UNKNOWN_SLOT_RE.search(clause) and not any(
            re.search(rf"\b(?:not|isn't|is not|aren't|wasn't)\s+(?:{_NEGATION_ADVERB_RE})?{re.escape(term)}", clause, re.IGNORECASE)
            for term in usable
        ):
            continue
        norm = _norm_phrase(clause)
        if not any(term in norm for term in usable):
            continue
        for term in usable:
            if re.search(
                rf"\b(?:not|no|never|isn't|is not|aren't|are not|wasn't|was not|doesn't|does not|don't|do not|cannot|can't)\s+"
                rf"(?:{_NEGATION_ADVERB_RE})?{re.escape(term)}\w*",
                norm,
            ):
                return True
    return False


def _sentence_targets_identity(sentence: str, identity: Mapping[str, Any]) -> bool:
    """A subject mention is not a claim. A claim names or negates the authorized value."""
    value_terms = _identity_terms(identity, "value") or _identity_terms(identity, "object")
    if value_terms:
        return _text_has_any(sentence, value_terms) or _negation_scopes_over(sentence, value_terms)
    relation_terms = _identity_terms(identity, "relation")
    return bool(relation_terms and _text_has_any(sentence, relation_terms))


def _semantic_identity_matches(sentence: str, identity: Mapping[str, Any]) -> bool:
    if not identity:
        return False
    subject_terms = _identity_terms(identity, "subject") or _identity_terms(identity, "target_scene_id")
    value_terms = _identity_terms(identity, "value") or _identity_terms(identity, "object")
    kind = str(identity.get("kind") or "").strip()
    if (
        not subject_terms
        and kind != "movement"
        and not value_terms
        and not _identity_terms(identity, "speaker_id")
        and not _identity_terms(identity, "speaker_name")
    ):
        return False
    if subject_terms and not _text_has_subject_or_head_with_value(sentence, subject_terms, value_terms):
        speaker_terms = _identity_terms(identity, "speaker_id") + _identity_terms(identity, "speaker_name")
        if speaker_terms and not _text_has_any(sentence, speaker_terms):
            return False
        if not speaker_terms:
            return False
    if kind == "movement":
        return _movement_identity_matches(sentence, identity)
    relation_terms = _identity_terms(identity, "relation")
    if value_terms and not _text_has_any(sentence, value_terms):
        return False
    if relation_terms and not _text_has_any(sentence, relation_terms) and not value_terms:
        return False
    polarity = str(identity.get("polarity") or "positive").strip().lower()
    value_terms_for_polarity = value_terms or relation_terms
    negated_value = _negation_scopes_over(sentence, value_terms_for_polarity)
    if polarity in {"negative", "false", "negated"} and not negated_value:
        return False
    if polarity in {"positive", "true", ""} and negated_value:
        return False
    for key in ("time", "location", "identity", "certainty", "causality"):
        terms = _qualifier_terms(identity, key)
        if terms and not _text_has_any(sentence, terms):
            return False
    authority = str(identity.get("authority") or "").strip()
    epistemic = str(identity.get("epistemic_status") or "").strip().lower()
    if authority == AUTH_CLAIM or epistemic in {"rumor", "hearsay", "uncertain", "speculative", "belief", "suspected"}:
        if not _is_claim_or_uncertain(sentence):
            return False
    return not _semantic_overreach_reasons(sentence, identity)


def _movement_identity_matches(sentence: str, identity: Mapping[str, Any]) -> bool:
    target_terms = _identity_terms(identity, "target_scene_id") + _identity_terms(identity, "target_name")
    if target_terms and not _text_has_any(sentence, target_terms):
        return False
    low = sentence.lower()
    if re.search(r"\b(?:watchtower|tower|hidden trail|secret trail|undiscovered path|after discovering|new route)\b", low):
        allowed = set(target_terms + _identity_terms(identity, "source_scene_id") + _identity_terms(identity, "source_name"))
        mentioned = [
            term
            for term in ("watchtower", "tower", "hidden trail", "secret trail", "undiscovered path", "new route")
            if term in low
        ]
        if any(term not in allowed for term in mentioned):
            return False
    return True


def _semantic_overreach_reasons(sentence: str, identity: Mapping[str, Any]) -> list[str]:
    low = sentence.lower()
    reasons: list[str] = []
    value = str(identity.get("value") or "").strip().lower()
    relation = str(identity.get("relation") or "").strip().lower()
    if value == "damaged" and re.search(r"\b(?:collapsed|gave way|came down|destroyed)\b", low):
        reasons.append("semantic_strengthening:value")
    if relation in {"seen_near", "observation"} and re.search(r"\b(?:belongs?|member of|part of|smuggling ring)\b", low):
        reasons.append("semantic_strengthening:relation")
    if relation in {"status", "condition"} and value in {"tainted", "contaminated"} and re.search(r"\bpoisoned\b", low):
        reasons.append("semantic_strengthening:value")
    if relation in {"status", "condition"} and value == "standing" and re.search(r"\b(?:collapsed|fell|gave way|came down)\b", low):
        reasons.append("semantic_polarity:value")
    if value == "locked" and re.search(r"\bunlocked\b", low):
        reasons.append("semantic_polarity:value")
    if value == "unlocked" and re.search(r"\blocked\b", low):
        reasons.append("semantic_polarity:value")
    if str(identity.get("causal_authorized") or "").lower() not in {"true", "yes"}:
        if re.search(r"\b(?:because|caused by|after thieves|thieves broke|ordered by|discover(?:ed|ing) a hidden)\b", low):
            reasons.append("semantic_overreach:causality")
    epistemic = str(identity.get("epistemic_status") or "").strip().lower()
    if epistemic in {"rumor", "hearsay", "uncertain", "speculative", "belief", "suspected"} and not _is_claim_or_uncertain(sentence):
        reasons.append("epistemic_promotion")
    modality = str(identity.get("modality") or "").strip().lower()
    if modality in {"possible", "hypothetical", "likely", "uncertain"} and not _is_claim_or_uncertain(sentence):
        reasons.append("modality_strengthening")
    return reasons


def _structured_semantic_rejection(sentence: str, decision: Mapping[str, Any] | None) -> list[str]:
    rows = (decision or {}).get("proposed_facts") if isinstance(decision, Mapping) else None
    if not isinstance(rows, list):
        return []
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("authorized"):
            continue
        if str(row.get("authority") or "") != AUTH_WORLD:
            continue
        identity = row.get("semantic_identity")
        if isinstance(identity, Mapping) and identity and _semantic_identity_matches(sentence, identity):
            return []
    reasons: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("authorized"):
            continue
        identity = row.get("semantic_identity")
        if not isinstance(identity, Mapping) or not identity:
            continue
        if str(identity.get("kind") or "") == "entity":
            continue
        subject_terms = _identity_terms(identity, "subject") + _identity_terms(identity, "target_scene_id")
        if not subject_terms and not _sentence_targets_identity(sentence, identity):
            continue
        if subject_terms and not _text_has_any(sentence, subject_terms):
            continue
        if str(identity.get("kind") or "") != "movement" and not _sentence_targets_identity(sentence, identity):
            # A bare mention is not a claim. A stronger or inverted substitute still is.
            overreach = _semantic_overreach_reasons(sentence, identity)
            if overreach:
                reasons.extend(overreach)
            continue
        overreach = _semantic_overreach_reasons(sentence, identity)
        if overreach:
            reasons.extend(overreach)
            continue
        if not _semantic_identity_matches(sentence, identity):
            reasons.append("semantic_identity_mismatch")
    return sorted(set(reasons))


def _authorized_by_decision(sentence: str, decision: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """Return the pre-narration fact that authorizes this sentence, if any."""
    rows = _authorized_rows_for_sentence(sentence, decision)
    return rows[0] if rows else None


def _empty_identity_covers(sentence: str, fact: str) -> bool:
    """Lexical compatibility for an authored fact that has no semantic identity.

    The sentence may drop content words from the fact. It may add at most one
    content word. A second proposition does not inherit the fact's authority.
    This is token overlap, not synonym or entailment inference.
    """
    sentence_tokens = _token_set(sentence)
    fact_tokens = _token_set(fact)
    if len(fact_tokens) < 3 and len(sentence_tokens) < 3:
        return False
    extra = sentence_tokens - fact_tokens
    if len(sentence_tokens) >= 3 and not extra and sentence_tokens <= fact_tokens:
        return True
    if len(extra) > 1:
        return False
    normalized_fact = fact.lower().strip(" .!?")
    if len(fact_tokens) >= 3 and normalized_fact and normalized_fact in sentence.lower():
        return True
    if len(fact_tokens) >= 3 and fact_tokens <= sentence_tokens:
        return True
    return bool(
        len(fact_tokens) >= 4
        and len(fact_tokens & sentence_tokens) >= max(3, len(fact_tokens) - 1)
    )


def _authorized_rows_for_sentence(sentence: str, decision: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    """Return each pre-narration fact covered by this sentence.

    Structured identities match on their own fields. Free-text facts keep the
    lexical compatibility rule: a paraphrase may omit words, and it may not
    carry an additional content-word proposition.
    """
    rows = (decision or {}).get("proposed_facts") if isinstance(decision, Mapping) else None
    if not isinstance(rows, list):
        return []
    matched: list[Mapping[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("authorized"):
            continue
        identity = row.get("semantic_identity")
        if isinstance(identity, Mapping) and identity:
            if _semantic_identity_matches(sentence, identity):
                matched.append(row)
            continue
        text = _clean(row.get("text"), limit=600)
        if text and _empty_identity_covers(sentence, text):
            matched.append(row)
    return matched


def _row_relation_kind(row: Mapping[str, Any]) -> str:
    identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
    relation_kind = str(identity.get("relation_kind") or row.get("relation_kind") or "").strip()
    if relation_kind:
        return relation_kind
    relation = str(identity.get("relation") or "").strip().lower()
    if relation in {"cause", "causes", "causal", "because", "possible_cause", "event_cause"}:
        return REL_CAUSAL
    if relation in {"evidence", "evidential", "shows", "proves", "indicates"}:
        return REL_EVIDENTIAL
    if relation in {"lead", "actionable_lead", "gameplay_lead"}:
        return REL_GAMEPLAY_LEAD
    if relation in {"unknown", "unresolved", "epistemic_status"}:
        return REL_EPISTEMIC_STATUS
    return REL_OBSERVATION if identity else REL_PREDICATE


def _claim_from_row(sentence: str, row: Mapping[str, Any]) -> NarratedClaim:
    identity = dict(row.get("semantic_identity") or {}) if isinstance(row.get("semantic_identity"), Mapping) else {}
    epistemic = str(identity.get("epistemic_status") or row.get("epistemic_status") or "")
    if not epistemic:
        epistemic = STATUS_ESTABLISHED if str(row.get("authority") or "") == AUTH_WORLD else STATUS_UNRESOLVED
    return NarratedClaim(
        text=_clean(sentence, limit=600),
        semantic_identity=identity,
        provenance=str(row.get("provenance") or PROVENANCE_AUTHORITATIVE),
        authority=str(row.get("authority") or AUTH_WORLD),
        epistemic_status=epistemic,
        relation_kind=_row_relation_kind(row),
        persistence=str(row.get("persistence") or PERSIST_NONE),
        authorized=True,
        source_ref=str(row.get("source_ref") or ""),
        reason_codes=list(row.get("reason_codes") or ["authorized_by_pre_narration_decision"]),
    )


def _claim(
    text: str,
    *,
    reasons: Sequence[str],
    relation_kind: str,
    provenance: str = PROVENANCE_GENERATED_PROPOSAL,
    authority: str = AUTH_UNAUTHORIZED,
    epistemic_status: str = STATUS_UNRESOLVED,
    persistence: str = PERSIST_NONE,
    authorized: bool = False,
    semantic_identity: Mapping[str, Any] | None = None,
    source_ref: str = "",
) -> NarratedClaim:
    return NarratedClaim(
        text=_clean(text, limit=600),
        semantic_identity=dict(semantic_identity or {}),
        provenance=provenance,
        authority=authority,
        epistemic_status=epistemic_status,
        relation_kind=relation_kind,
        persistence=persistence,
        authorized=authorized,
        source_ref=source_ref,
        reason_codes=sorted(set(str(reason) for reason in reasons if str(reason).strip())),
    )


def _decision_authorizes_relation(sentence: str, decision: Mapping[str, Any] | None, relation_kind: str) -> bool:
    for row in _authorized_rows_for_sentence(sentence, decision):
        # A resolver-selected, public clue may itself state a relationship.
        # License only its exact authored sentence; overlap cannot authorize
        # a provider's additional causal/evidential assertion.
        if (row.get("source_ref") == "resolution.clue_text"
                and row.get("provenance") == PROVENANCE_AUTHORITATIVE
                and _norm_phrase(sentence) == _norm_phrase(str(row.get("text") or ""))):
            return True
        if _row_relation_kind(row) == relation_kind:
            return True
        identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
        if relation_kind == REL_CAUSAL and str(identity.get("causal_authorized") or "").lower() in {"true", "yes"}:
            return True
        if relation_kind == REL_EVIDENTIAL and str(identity.get("evidential_authorized") or "").lower() in {"true", "yes"}:
            return True
    return False


def _decision_authorizes_specific_lead(sentence: str, decision: Mapping[str, Any] | None) -> bool:
    for row in _authorized_rows_for_sentence(sentence, decision):
        if _row_relation_kind(row) == REL_GAMEPLAY_LEAD:
            return True
        identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
        relation = str(identity.get("relation") or "").strip().lower()
        kind = str(identity.get("kind") or "").strip().lower()
        if relation in {"lead", "actionable_lead", "gameplay_lead"} or kind == "gameplay_lead":
            return True
    return False


def _decision_authorizes_claim_family(
    sentence: str,
    decision: Mapping[str, Any] | None,
    families: set[str],
) -> bool:
    for row in _authorized_rows_for_sentence(sentence, decision):
        relation_kind = _row_relation_kind(row)
        identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
        relation = str(identity.get("relation") or "").strip().lower()
        kind = str(identity.get("kind") or "").strip().lower()
        if relation_kind in families or relation in families or kind in families:
            return True
        qualifiers = identity.get("qualifiers") if isinstance(identity.get("qualifiers"), Mapping) else {}
        if "actor" in families and (qualifiers.get("actor") or qualifiers.get("identity")):
            return True
        if "time" in families and qualifiers.get("time"):
            return True
        if "cause" in families and (qualifiers.get("cause") or qualifiers.get("causality")):
            return True
    return False


def _authorized_non_observation_claim(sentence: str, decision: Mapping[str, Any] | None) -> bool:
    for row in _authorized_rows_for_sentence(sentence, decision):
        if _row_relation_kind(row) != REL_OBSERVATION:
            return True
        identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
        relation = str(identity.get("relation") or "").strip().lower()
        if relation in {"actor_attribution", "agent_action", "event_actor", "cause", "causal", "event_cause", "time", "event_time", "history", "event_history", "state_transition", "evidence", "evidential"}:
            return True
    return False


def _decision_allows_epistemic_limit(decision: Mapping[str, Any] | None) -> bool:
    if not isinstance(decision, Mapping):
        return False
    if decision.get("unresolved_qualifiers"):
        return True
    for act in decision.get("epistemic_acts") or []:
        if isinstance(act, Mapping) and str(act.get("act") or "") == EPISTEMIC_ACT_LEAVE_UNRESOLVED:
            return True
    return False


def _authorized_epistemic_limit(sentence: str, decision: Mapping[str, Any] | None) -> bool:
    """Negative knowledge status is not a positive evidential/world assertion."""
    return bool(
        _EPISTEMIC_LIMIT_RE.search(sentence or "")
        and (_decision_allows_epistemic_limit(decision) or _attributed_epistemic_source(sentence))
    )


def _decision_allows_inference(decision: Mapping[str, Any] | None) -> bool:
    if not isinstance(decision, Mapping):
        return False
    return any(
        isinstance(act, Mapping) and str(act.get("act") or "") == EPISTEMIC_ACT_INFER
        for act in decision.get("epistemic_acts") or []
    )


def _marks_unresolved_status(text: str) -> bool:
    """True when this text marks a proposition unresolved.

    Equivalent forms share this predicate. A true result authorizes only that
    status operation.
    """
    return bool(_UNKNOWN_SLOT_RE.search(text or "") or _UNRESOLVED_STATUS_EQUIVALENT_RE.search(text or ""))


_UNRESOLVED_CAUSE_WH_RE = re.compile(r"\b(?:what|which|who|why)\b", re.IGNORECASE)
_UNRESOLVED_CAUSE_COORDINATOR_RE = re.compile(r"\b(?:and|but)\b", re.IGNORECASE)


def _clause_span_containing(text: str, index: int) -> tuple[int, int]:
    """Clause that contains index. Comma, semicolon, but, and yet split clauses."""
    start = 0
    for match in _CLAUSE_SPLIT_RE.finditer(text or ""):
        if match.start() > index:
            return start, match.start()
        start = match.end()
    return start, len(text or "")


def _causal_match_is_unresolved_cause(text: str, match: re.Match[str]) -> bool:
    """A causal verb inside an explicit unresolved-cause construction is not an attribution.

    The status marker comes from the shared unresolved-status recognizer.
    The verb has to be the wh-complement or the wh-subject of that marker,
    in the same clause. A neighboring attribution is left alone.
    """
    clause_start, clause_end = _clause_span_containing(text, match.start())
    clause = text[clause_start:clause_end]
    for status in _UNRESOLVED_STATUS_EQUIVALENT_RE.finditer(clause):
        status_start = clause_start + status.start()
        status_end = clause_start + status.end()
        if status_end <= match.start():
            between = text[status_end : match.start()]
            wh_text = between
        elif match.end() <= status_start:
            between = text[match.end() : status_start]
            wh_text = text[clause_start : match.start()]
        else:
            continue
        if _UNRESOLVED_CAUSE_COORDINATOR_RE.search(between):
            continue
        if len(re.findall(r"[A-Za-z']+", between)) > 12:
            continue
        if _UNRESOLVED_CAUSE_WH_RE.search(wh_text):
            return True
    return False


def _asserted_event_cause(text: str) -> bool:
    """True when an event-cause match is an attribution, not an unresolved cause."""
    for match in _EVENT_CAUSE_ATTRIBUTION_RE.finditer(text or ""):
        if _causal_match_is_unresolved_cause(text or "", match):
            continue
        return True
    return False


def _establishment_match_is_negated(text: str, match: re.Match[str]) -> bool:
    """True when a short negation governs this certainty or establishment match."""
    prefix = (text or "")[max(0, match.start() - 48) : match.start()]
    return bool(_NEGATION_GOVERNS_RE.search(prefix))


def _positive_pattern_match(pattern: re.Pattern[str], text: str) -> bool:
    """A pattern hit that is not inside an obvious negation of that hit."""
    for match in pattern.finditer(text or ""):
        if _establishment_match_is_negated(text or "", match):
            continue
        return True
    return False


def _evidential_text_beyond_inference_hedge(sentence: str, decision: Mapping[str, Any] | None) -> str:
    """Drop the hedge verb that licensed inference. Leave other evidential verbs."""
    if not (_decision_allows_inference(decision) and _QUALIFIED_INFERENCE_RE.search(sentence or "")):
        return sentence or ""
    return _LICENSED_INFERENCE_HEDGE_VERB_RE.sub(" ", sentence or "")


def _relationship_residual_claims(sentence: str, decision: Mapping[str, Any] | None) -> list[NarratedClaim]:
    """Causal, evidential, and certainty operations in this sentence.

    An unresolved-status marker or a licensed hedge does not cancel a separate
    operation in the same sentence.
    """
    claims: list[NarratedClaim] = []
    if _positive_pattern_match(_CAUSAL_RELATION_RE, sentence or "") and not _decision_authorizes_relation(sentence, decision, REL_CAUSAL):
        claims.append(
            _claim(
                sentence,
                reasons=["unauthorized_causal_relation"],
                relation_kind=REL_CAUSAL,
                semantic_identity={"relation_kind": REL_CAUSAL},
            )
        )
    evidential_text = _evidential_text_beyond_inference_hedge(sentence, decision)
    if _positive_pattern_match(_EVIDENTIAL_RELATION_RE, evidential_text) and not _decision_authorizes_relation(sentence, decision, REL_EVIDENTIAL):
        claims.append(
            _claim(
                sentence,
                reasons=["unauthorized_evidential_relation"],
                relation_kind=REL_EVIDENTIAL,
                semantic_identity={"relation_kind": REL_EVIDENTIAL},
            )
        )
    if _positive_pattern_match(_CERTAINTY_UPGRADE_RE, sentence or "") and not _decision_authorizes_relation(sentence, decision, REL_EVIDENTIAL):
        claims.append(
            _claim(
                sentence,
                reasons=["unauthorized_certainty_upgrade"],
                relation_kind=REL_EPISTEMIC_STATUS,
                semantic_identity={"relation_kind": REL_EPISTEMIC_STATUS, "epistemic_status": STATUS_ESTABLISHED},
            )
        )
    return claims


def _asserted_causal_relation(text: str) -> bool:
    """A cause connective or causal verb.

    ``a possible cause`` names a qualified possibility. ``due to`` and
    ``possibly from`` still assert a cause.
    """
    stripped = _NAMED_POSSIBILITY_CAUSE_RE.sub(" ", text or "")
    return _positive_pattern_match(_CAUSAL_RELATION_RE, stripped)


# Abstract slot names stay with the connective, actor, time, and history recognizers.
# The remaining entries are explanatory complements that qualified_possibilities_only
# already refuses. They are not a global word ban: a decision row or the authored
# corpus can still license the same phrase.
_ABSTRACT_QUALIFIED_CATEGORIES = frozenset(
    {
        "exact_cause",
        "actor",
        "time",
        "history",
        "gameplay_lead",
        "evidential_establishment",
        "certainty_upgrade_to_established",
        "inference_as_authored_world_fact",
    }
)


def _closed_explanatory_complement_phrases() -> tuple[str, ...]:
    phrases: list[str] = []
    for item in _QUALIFIED_FORBIDDEN:
        if item in _ABSTRACT_QUALIFIED_CATEGORIES:
            continue
        phrase = str(item).replace("_", " ").strip().lower()
        if phrase and phrase not in phrases:
            phrases.append(phrase)
    return tuple(phrases)


def _identity_string_bits(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        bits: list[str] = []
        for item in value.values():
            bits.extend(_identity_string_bits(item))
        return bits
    if isinstance(value, (list, tuple)):
        bits = []
        for item in value:
            bits.extend(_identity_string_bits(item))
        return bits
    return []


def _complement_phrase_is_authorized(
    phrase: str,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
) -> bool:
    """True when this decision, not the hedge, licenses the complement phrase.

    Authoritative facts, the authored corpus, a player hypothesis, and a
    decision-owned MAY_INFER claim count. A speculative proposed fact does not:
    the model cannot authorize a complement by proposing it.
    """
    if not phrase:
        return False
    parts = [str(authored_corpus or "")]
    for row in (decision or {}).get("proposed_facts") or []:
        if not isinstance(row, Mapping) or not row.get("authorized"):
            continue
        provenance = str(row.get("provenance") or "")
        if provenance != PROVENANCE_PLAYER_HYPOTHESIS and not _fact_can_ground_definite(row):
            continue
        parts.append(str(row.get("text") or ""))
        parts.extend(_identity_string_bits(row.get("semantic_identity")))
    for row in (decision or {}).get("realization_claims") or []:
        if not isinstance(row, Mapping):
            continue
        provenance = str(row.get("provenance") or "")
        authority = str(row.get("authority") or "")
        role = str(row.get("realization_role") or "")
        if provenance in {PROVENANCE_GENERATED_PROPOSAL, PROVENANCE_SPECULATION}:
            continue
        if authority != AUTH_WORLD and provenance != PROVENANCE_PLAYER_HYPOTHESIS and role != ROLE_MAY_INFER:
            continue
        parts.append(str(row.get("text") or ""))
        parts.extend(_identity_string_bits(row.get("semantic_identity")))
    blob = " ".join(parts).lower()
    return bool(re.search(rf"\b{re.escape(phrase)}\b", blob))


def _qualified_scope_closes_explanatory_complements(decision: Mapping[str, Any] | None) -> bool:
    return bool(_qualified_infer_acts(decision or {}))


def _unauthorized_inference_complements(
    text: str,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
) -> list[str]:
    """Closed explanatory complements of a licensed hedge.

    The hedge licenses the inference operation. It does not license the
    proposition that operation points to. A negated mention is not a complement
    assertion. The same phrase is authorized when the decision or corpus carries it.
    """
    if not _qualified_scope_closes_explanatory_complements(decision):
        return []
    if not _QUALIFIED_INFERENCE_RE.search(text or ""):
        return []
    found: list[str] = []
    for phrase in _closed_explanatory_complement_phrases():
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        for match in pattern.finditer(text or ""):
            if _establishment_match_is_negated(text or "", match):
                continue
            if _complement_phrase_is_authorized(phrase, decision, authored_corpus):
                continue
            if phrase not in found:
                found.append(phrase)
            break
    return found


def _hedge_does_not_authorize(
    text: str,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
) -> list[str]:
    """Consequential operations that stay unauthorized when the sentence is hedged."""
    reasons: list[str] = []
    for claim in _relationship_residual_claims(text, decision):
        for code in claim.reason_codes:
            if code == "unauthorized_causal_relation":
                continue
            reasons.append(code)
    if _asserted_causal_relation(text) and not _decision_authorizes_relation(text, decision, REL_CAUSAL):
        reasons.append("unauthorized_causal_relation")
    if _ACTOR_ATTRIBUTION_RE.search(text or "") and not _decision_authorizes_claim_family(
        text,
        decision,
        {"actor", "actor_attribution", "agent_action", "event_actor"},
    ):
        reasons.append("unauthorized_actor_attribution")
    if _EVENT_HISTORY_ASSERTION_RE.search(text or "") and not _decision_authorizes_claim_family(
        text,
        decision,
        {"history", "event_history", "state_transition", "event_actor", "event_time"},
    ):
        reasons.append("unauthorized_history_assertion")
    if _unauthorized_inference_complements(text, decision, authored_corpus):
        reasons.append("unauthorized_inference_complement")
    ordered: list[str] = []
    for reason in reasons:
        if reason not in ordered:
            ordered.append(reason)
    return ordered


def _ordinary_residual_reasons(
    sentence: str,
    decision: Mapping[str, Any] | None,
    covered_rows: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    if _UNKNOWN_SLOT_RE.search(sentence or "") or _is_interrogative(sentence):
        return []
    if epistemic_frame(sentence) in {"rumor", "hearsay", "uncertain", "speculative"}:
        return []
    if _is_claim_or_uncertain(sentence) and _attributed_epistemic_source(sentence):
        return []
    rows = (decision or {}).get("proposed_facts") if isinstance(decision, Mapping) else None
    if not isinstance(rows, list) or not rows:
        return []
    covered = list(covered_rows or _authorized_rows_for_sentence(sentence, decision))
    mentions_governed = _mentions_governed_subject(sentence, decision)
    deictic_anchor = bool(_CLAIM_CONTROL_DEICTIC_RE.search(sentence or "")) and bool(rows)
    slots = {str(item) for item in ((decision or {}).get("unresolved_qualifiers") or []) if str(item).strip()}
    has_structural_slot_fill = bool(
        slots
        and (
            _ACTOR_ATTRIBUTION_RE.search(sentence or "")
            or _EVENT_CAUSE_ATTRIBUTION_RE.search(sentence or "")
            or _TIME_FILL_RE.search(sentence or "")
            or _EVENT_HISTORY_ASSERTION_RE.search(sentence or "")
        )
    )
    has_structural_consequential = bool(
        _ACTOR_ATTRIBUTION_RE.search(sentence or "")
        or _EVENT_CAUSE_ATTRIBUTION_RE.search(sentence or "")
        or _TIME_FILL_RE.search(sentence or "")
        or _EVENT_HISTORY_ASSERTION_RE.search(sentence or "")
    )
    if (
        not mentions_governed
        and not deictic_anchor
        and not covered
        and not has_structural_slot_fill
        and not has_structural_consequential
    ):
        return []
    if _authorized_non_observation_claim(sentence, decision):
        return []
    reasons: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("authorized"):
            continue
        identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
        if _row_relation_kind(row) != REL_EPISTEMIC_STATUS:
            continue
        if (
            _text_has_any(sentence, _identity_terms(identity, "subject"))
            and not _is_claim_or_uncertain(sentence)
            and not re.match(r"\s*if\b", sentence or "", re.IGNORECASE)
        ):
            reasons.append("unauthorized_certainty_upgrade")
    if _ACTOR_ATTRIBUTION_RE.search(sentence or "") and not _decision_authorizes_claim_family(
        sentence,
        decision,
        {"actor", "actor_attribution", "agent_action", "event_actor"},
    ):
        if not slots or "actor" in slots or mentions_governed or deictic_anchor:
            reasons.append("unauthorized_actor_attribution")
    if _asserted_event_cause(sentence) and not (
        _decision_authorizes_relation(sentence, decision, REL_CAUSAL)
        or _decision_authorizes_claim_family(sentence, decision, {"cause", "causal", "event_cause"})
    ):
        if not slots or "cause" in slots or mentions_governed or deictic_anchor:
            reasons.append("unauthorized_cause_attribution")
    if _TIME_FILL_RE.search(sentence or "") and not _decision_authorizes_claim_family(
        sentence,
        decision,
        {"time", "event_time"},
    ):
        if not slots or "time" in slots or mentions_governed or deictic_anchor:
            reasons.append("unauthorized_time_attribution")
    if _EVENT_HISTORY_ASSERTION_RE.search(sentence or "") and not _decision_authorizes_claim_family(
        sentence,
        decision,
        {"history", "event_history", "state_transition", "event_actor", "event_time"},
    ):
        if covered or mentions_governed or deictic_anchor:
            reasons.append("unauthorized_history_assertion")
    return sorted(set(reasons))


def _structured_consequential_reasons(sentence: str) -> list[str]:
    """Structural consequential-world detection, independent of gate nouns."""
    if _UNKNOWN_SLOT_RE.search(sentence or "") or _EPISTEMIC_PARENT_REALIZATION_RE.search(sentence or ""):
        return []
    if _LOW_STAKES_STATE_RE.search(sentence or ""):
        return []
    if _is_claim_or_uncertain(sentence):
        return []
    reasons: list[str] = []
    if _NEGATIVE_EVIDENCE_RE.search(sentence or ""):
        reasons.append("unauthorized_negative_evidence")
    if _SPECIFIC_LEAD_RE.search(sentence or ""):
        reasons.append("unsupported_narrator_lead")
    if _STATEFUL_ASSERTION_RE.search(sentence or ""):
        reasons.append("unowned_stateful_world_assertion")
    prop_rows = classify_propositions(sentence, authored_corpus="")
    if any(row.get("consequential") and row.get("kind") not in {INCIDENTAL_KIND, NPC_CLAIM_KIND} for row in prop_rows):
        reasons.append("proposition_authority")
    return sorted(set(reasons))


def _consequential_reasons(sentence: str) -> list[str]:
    if _EPISTEMIC_PARENT_REALIZATION_RE.search(sentence or ""):
        return []
    reasons: list[str] = []
    for code, pattern in _CONSEQUENTIAL_PATTERNS:
        if pattern.search(sentence or ""):
            reasons.append(code)
    return reasons


def _quoted_proposition(sentence: str) -> str:
    """Speech inside quotes is the proposition. Attribution outside them is not."""
    parts: list[str] = []
    for match in _QUOTE_SPAN_RE.finditer(sentence or ""):
        inner = match.group(0).strip("\"“”").strip()
        inner = _REALIZATION_WRAPPER_RE.sub("", inner).strip()
        if inner:
            parts.append(inner)
    if parts:
        return " ".join(parts)
    return _REALIZATION_WRAPPER_RE.sub("", str(sentence or "")).strip()


def _authorized_statement_texts(decision: Mapping[str, Any] | None) -> list[str]:
    rows = (decision or {}).get("proposed_facts") if isinstance(decision, Mapping) else None
    if not isinstance(rows, list):
        return []
    texts: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("authorized"):
            continue
        text = _clean(row.get("text"), limit=600)
        if text and text not in texts:
            texts.append(text)
    return texts


def _proposition_restates_statement(sentence: str, statement: str) -> bool:
    """True when the sentence repeats an authorized statement without adding content words.

    Words may be dropped. A second proposition does not inherit the statement.
    Quoted speech is compared without the speaker frame or the realization wrapper.
    """
    proposition = _quoted_proposition(sentence) if _QUOTE_SPAN_RE.search(sentence or "") else str(sentence or "")
    proposition = _REALIZATION_WRAPPER_RE.sub("", proposition).strip()
    fact_tokens = _token_set(statement)
    prop_tokens = _token_set(proposition)
    if len(fact_tokens) < 3 or not prop_tokens:
        return False
    if prop_tokens <= fact_tokens and len(prop_tokens & fact_tokens) >= max(3, len(fact_tokens) - 1):
        return True
    return _norm_phrase(statement) == _norm_phrase(proposition)


def _pattern_licensed_by_statement(
    sentence: str,
    pattern: re.Pattern[str],
    decision: Mapping[str, Any] | None,
) -> bool:
    """A consequential pattern that is already true of an authorized statement.

    Restating that statement is not a new discovery. Added content words are.
    """
    if not pattern.search(sentence or ""):
        return False
    for statement in _authorized_statement_texts(decision):
        if pattern.search(statement) and _proposition_restates_statement(sentence, statement):
            return True
    return False


def _unlicensed_consequential_reasons(
    sentence: str,
    decision: Mapping[str, Any] | None = None,
) -> list[str]:
    if _EPISTEMIC_PARENT_REALIZATION_RE.search(sentence or ""):
        return []
    reasons: list[str] = []
    for code, pattern in _CONSEQUENTIAL_PATTERNS:
        if not pattern.search(sentence or ""):
            continue
        if _pattern_licensed_by_statement(sentence, pattern, decision):
            continue
        reasons.append(code)
    return reasons


def _existence_mention(row: Mapping[str, Any]) -> bool:
    identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
    return str(identity.get("kind") or "") == "entity" and str(identity.get("relation") or "").lower() == "exists"


def decision_with_selected_social_topic(
    decision: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Expose the resolver-selected topic to narration checks.

    The social resolver remains the owner. This copy lets finalization recognize
    the sentence it already selected. It does not add world-truth authority.
    """
    if not isinstance(decision, Mapping):
        return decision
    social = resolution.get("social") if isinstance(resolution, Mapping) else None
    topic = social.get("topic_revealed") if isinstance(social, Mapping) else None
    if not isinstance(topic, Mapping):
        return decision
    text = _clean(topic.get("text") or topic.get("clue_text"), limit=600)
    if not text:
        return decision
    facts = [dict(row) for row in (decision.get("proposed_facts") or []) if isinstance(row, Mapping)]
    norm = _norm_phrase(text)
    if any(_norm_phrase(row.get("text")) == norm for row in facts):
        return decision
    topic_id = _clean(topic.get("id"), limit=80)
    facts.append(
        {
            "text": text,
            "provenance": PROVENANCE_NPC_CLAIM,
            "consequence": "epistemic",
            "authorized": True,
            "reason_codes": ["resolver_selected_social_topic"],
            "authority": AUTH_CLAIM,
            "persistence": PERSIST_CLAIM,
            "source_ref": f"social.topic_revealed.{topic_id}" if topic_id else "social.topic_revealed",
            "outcome_classification": OUTCOME_EPISTEMIC,
            "semantic_identity": {},
        }
    )
    out = dict(decision)
    out["proposed_facts"] = facts
    return out


def _is_claim_or_uncertain(sentence: str) -> bool:
    frame = epistemic_frame(sentence)
    return bool(
        frame in {"rumor", "hearsay", "uncertain", "speculative"}
        or _CLAIM_FRAME_RE.search(sentence or "")
        or _UNCERTAIN_FRAME_RE.search(sentence or "")
    )


def _state_mutations_from_resolution(resolution: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(resolution, Mapping):
        return []
    mutations: list[dict[str, Any]] = []
    kind = str(resolution.get("kind") or "").strip().lower()
    target = _clean(resolution.get("target_scene_id") or resolution.get("targetSceneId"), limit=80)
    if kind in {"scene_transition", "travel"} and target:
        mutations.append({"type": "location", "target_scene_id": target})
    state_changes = resolution.get("state_changes")
    if isinstance(state_changes, Mapping):
        for key, value in state_changes.items():
            mutations.append({"type": "state_change", "key": str(key), "value": value})
    return mutations


def _fact(
    text: str,
    *,
    provenance: str,
    consequence: str,
    authorized: bool,
    authority: str,
    persistence: str,
    source_ref: str,
    outcome_classification: str,
    reason_codes: list[str] | None = None,
    semantic_identity: Mapping[str, Any] | None = None,
) -> GMProposedFact | None:
    cleaned = _clean(text, limit=600)
    if not cleaned:
        return None
    return GMProposedFact(
        text=cleaned,
        provenance=provenance,
        consequence=consequence,
        authorized=authorized,
        reason_codes=list(reason_codes or []),
        authority=authority,
        persistence=persistence,
        source_ref=source_ref,
        outcome_classification=outcome_classification,
        semantic_identity=dict(semantic_identity or {}),
    )


def _text_and_identity(item: Any) -> tuple[str, dict[str, Any]]:
    if isinstance(item, Mapping):
        text = _clean(item.get("text") or item.get("content") or item.get("fact"), limit=600)
        identity = item.get("semantic_identity")
        return text, dict(identity) if isinstance(identity, Mapping) else {}
    return str(item), {}


def _authored_fact_rows(scene: Mapping[str, Any] | None, world: Mapping[str, Any] | None) -> list[GMProposedFact]:
    rows: list[GMProposedFact] = []
    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
    if isinstance(inner, Mapping):
        for key in ("visible_facts", "opening_seed_facts", "journal_seed_facts"):
            value = inner.get(key)
            values = value if isinstance(value, list) else [value] if isinstance(value, str) else []
            for index, item in enumerate(values):
                text, semantic_identity = _text_and_identity(item)
                row = _fact(
                    text,
                    provenance=PROVENANCE_AUTHORITATIVE,
                    consequence="consequential",
                    authorized=True,
                    authority=AUTH_WORLD,
                    persistence=PERSIST_WORLD,
                    source_ref=f"scene.{key}.{index}",
                    outcome_classification=OUTCOME_ESTABLISHED,
                    reason_codes=["authored_state_source"],
                    semantic_identity=semantic_identity,
                )
                if row is not None:
                    rows.append(row)
    if isinstance(world, Mapping):
        for index, npc in enumerate(world.get("npcs") or []):
            if not isinstance(npc, Mapping):
                continue
            name = _clean(npc.get("name"), limit=120)
            role = _clean(npc.get("role"), limit=120)
            if name:
                content = f"{name} exists" + (f" as {role}" if role else "")
                row = _fact(
                    content,
                    provenance=PROVENANCE_AUTHORITATIVE,
                    consequence="consequential",
                    authorized=True,
                    authority=AUTH_WORLD,
                    persistence=PERSIST_WORLD,
                    source_ref=f"world.npcs.{index}",
                    outcome_classification=OUTCOME_ESTABLISHED,
                    reason_codes=["authored_world_npc"],
                    semantic_identity={
                        "kind": "entity",
                        "subject": str(npc.get("id") or name),
                        "subject_aliases": [name],
                        "relation": "exists",
                        "value": role or "present",
                        "authority": AUTH_WORLD,
                    },
                )
                if row is not None:
                    rows.append(row)
    return rows


def _runtime_fact_rows(session: Mapping[str, Any] | None, scene: Mapping[str, Any] | None) -> list[GMProposedFact]:
    scene_id = ""
    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
    if isinstance(inner, Mapping):
        scene_id = str(inner.get("id") or "").strip()
    if not scene_id and isinstance(session, Mapping):
        scene_id = str(session.get("active_scene_id") or "").strip()
    rows: list[GMProposedFact] = []
    for entry in accepted_bounded_improvisation_entries(session, scene_id=scene_id or None):
        content = _clean(entry.get("content"), limit=600)
        kind = str(entry.get("kind") or "")
        if kind == NPC_CLAIM_KIND:
            provenance = PROVENANCE_NPC_CLAIM
            authority = AUTH_CLAIM
            persistence = PERSIST_CLAIM
            outcome = OUTCOME_EPISTEMIC
            consequence = "epistemic"
            reason = "accepted_npc_claim_continuity"
            semantic_identity = {
                "kind": "npc_claim",
                "subject": content,
                "subject_aliases": [content],
                "relation": "claim",
                "value": content,
                "value_aliases": [content],
                "speaker_id": str(entry.get("speaker_id") or ""),
                "epistemic_status": str(entry.get("epistemic_status") or "uncertain"),
                "authority": AUTH_CLAIM,
            }
            if isinstance(entry.get("semantic_identity"), Mapping):
                semantic_identity.update(dict(entry["semantic_identity"]))
        else:
            provenance = PROVENANCE_INCIDENTAL
            authority = AUTH_INCIDENTAL
            persistence = PERSIST_INCIDENTAL
            outcome = OUTCOME_INCIDENTAL
            consequence = "low"
            reason = "accepted_bounded_incidental_continuity"
            semantic_identity = {}
        row = _fact(
            content,
            provenance=provenance,
            consequence=consequence,
            authorized=True,
            authority=authority,
            persistence=persistence,
            source_ref=str(entry.get("id") or ""),
            outcome_classification=outcome,
            reason_codes=[reason],
            semantic_identity=semantic_identity,
        )
        if row is not None:
            rows.append(row)
    return rows


def _temporal_provenance_rows(session: Mapping[str, Any] | None) -> list[GMProposedFact]:
    record = session.get(TEMPORAL_PROVENANCE_KEY) if isinstance(session, Mapping) else None
    if not isinstance(record, Mapping):
        return []
    rows: list[GMProposedFact] = []
    bucket_specs = (
        ("gm_inferences", PROVENANCE_GM_INFERENCE, AUTH_INFERENCE, PERSIST_NONE, STATUS_INFERRED, ROLE_MAY_INFER),
        ("player_hypotheses", PROVENANCE_PLAYER_HYPOTHESIS, AUTH_OBSERVATION, PERSIST_NONE, STATUS_HYPOTHESIS, ROLE_MAY_INFER),
        ("accepted_incidentals", PROVENANCE_INCIDENTAL, AUTH_INCIDENTAL, PERSIST_INCIDENTAL, STATUS_ESTABLISHED, ROLE_INCIDENTAL_TEXTURE),
    )
    for bucket, provenance, authority, persistence, status, _role in bucket_specs:
        for index, item in enumerate(record.get(bucket) or []):
            if not isinstance(item, Mapping):
                continue
            text = _clean(item.get("text"), limit=600)
            identity = dict(item.get("semantic_identity") or {}) if isinstance(item.get("semantic_identity"), Mapping) else {}
            if status and "epistemic_status" not in identity:
                identity["epistemic_status"] = status
            if authority == AUTH_INFERENCE and "modality" not in identity:
                identity["modality"] = identity.get("modality") or STATUS_POSSIBLE
            row = _fact(
                text,
                provenance=provenance,
                consequence="consequential" if bucket != "accepted_incidentals" else "low",
                authorized=True,
                authority=authority,
                persistence=persistence,
                source_ref=f"temporal.{bucket}.{index}",
                outcome_classification=OUTCOME_EPISTEMIC if bucket != "accepted_incidentals" else OUTCOME_INCIDENTAL,
                reason_codes=[f"temporal_{bucket}_ceiling"],
                semantic_identity=identity,
            )
            if row is not None:
                rows.append(row)
    return rows


def _claim_id_for(row: Mapping[str, Any], index: int) -> str:
    basis = f"{index}|{row.get('source_ref') or ''}|{row.get('text') or ''}|{row.get('semantic_identity') or {}}"
    return "rc_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]


def _realization_role_for_fact(row: GMProposedFact) -> str:
    if row.authority == AUTH_WORLD:
        return ROLE_MUST_STATE
    if row.provenance in {PROVENANCE_GM_INFERENCE, PROVENANCE_PLAYER_HYPOTHESIS}:
        return ROLE_MAY_INFER
    if row.authority == AUTH_INCIDENTAL:
        return ROLE_INCIDENTAL_TEXTURE
    return ROLE_MAY_STATE


def _id_list(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, (list, tuple)):
        return []
    out: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def _realization_claims_from_decision_parts(
    facts: Sequence[GMProposedFact],
    epistemic_acts: Sequence[Mapping[str, Any]],
) -> list[RealizationClaim]:
    claims: list[RealizationClaim] = []
    for index, row in enumerate(facts):
        identity = dict(row.semantic_identity or {})
        epistemic = str(identity.get("epistemic_status") or "")
        if not epistemic:
            epistemic = STATUS_ESTABLISHED if row.authority == AUTH_WORLD else STATUS_UNRESOLVED
        modality = str(identity.get("modality") or "")
        claims.append(
            RealizationClaim(
                claim_id=_claim_id_for(row.as_dict(), index),
                semantic_identity=identity,
                provenance=row.provenance,
                authority=row.authority,
                epistemic_status=epistemic,
                modality=modality,
                realization_role=_realization_role_for_fact(row),
                persistence=row.persistence,
                source_ref=row.source_ref,
                text=row.text,
                relation_kind=_row_relation_kind({"semantic_identity": identity}),
                premise_claim_ids=_id_list(identity.get("premise_claim_ids")),
            )
        )
    premise_ids = [
        claim.claim_id
        for claim in claims
        if claim.provenance in {PROVENANCE_PLAYER_HYPOTHESIS, PROVENANCE_GM_INFERENCE}
    ]
    offset = len(claims)
    for index, act in enumerate(epistemic_acts):
        if not isinstance(act, Mapping) or str(act.get("act") or "") != EPISTEMIC_ACT_LEAVE_UNRESOLVED:
            continue
        identity = dict(act.get("semantic_identity") or {}) if isinstance(act.get("semantic_identity"), Mapping) else {}
        linked = _id_list(identity.get("premise_claim_ids")) or list(premise_ids)
        claims.append(
            RealizationClaim(
                claim_id=_claim_id_for({"source_ref": "decision.epistemic_acts", "semantic_identity": identity}, offset + index),
                semantic_identity=identity,
                provenance=PROVENANCE_SPECULATION,
                authority=str(act.get("authority") or AUTH_OBSERVATION),
                epistemic_status=STATUS_UNRESOLVED,
                modality="unresolved",
                realization_role=ROLE_MUST_PRESERVE_UNCERTAINTY,
                persistence=PERSIST_NONE,
                source_ref="decision.epistemic_acts",
                text="Unresolved consequential slot",
                relation_kind=REL_EPISTEMIC_STATUS,
                premise_claim_ids=linked,
            )
        )
    return claims


def _question_text(contract: Mapping[str, Any]) -> str:
    return f"{contract.get('raw_input') or ''} {contract.get('conversational_subject') or ''}".strip()


def _unresolved_qualifiers_for(contract: Mapping[str, Any], facts: Sequence[GMProposedFact]) -> list[str]:
    question = _question_text(contract)
    wanted: list[str] = []
    if _QUESTION_ACTOR_RE.search(question):
        wanted.append("actor")
    if _QUESTION_TIME_RE.search(question):
        wanted.append("time")
    if _QUESTION_CAUSE_RE.search(question):
        wanted.append("cause")
    covered: set[str] = set()
    for row in facts:
        qualifiers = row.semantic_identity.get("qualifiers") if isinstance(row.semantic_identity, Mapping) else None
        if not isinstance(qualifiers, Mapping):
            continue
        if qualifiers.get("identity") or qualifiers.get("actor"):
            covered.add("actor")
        if qualifiers.get("time"):
            covered.add("time")
        if qualifiers.get("causality") or qualifiers.get("cause"):
            covered.add("cause")
    return [slot for slot in wanted if slot not in covered]


def _answer_relations_for(contract: Mapping[str, Any], facts: Sequence[GMProposedFact]) -> list[dict[str, Any]]:
    """Record the polar answer the contract can support from authorized values.

    A direct match is the authorized value itself. If the asked predicate is not
    an authorized value, the safe answer is to deny that predicate. Asserting it
    is an unsupported inference. This is not a general inference engine.
    """
    question = _question_text(contract)
    match = _POLAR_Q_RE.search(question)
    if not match:
        return []
    subject_span = _norm_phrase(match.group(1))
    predicate = _norm_phrase(match.group(2))
    if predicate in {"been", "being", "still", "currently", "there", "here", "that", "this", "into", "from"}:
        return []
    relations: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in facts:
        identity = row.semantic_identity if isinstance(row.semantic_identity, Mapping) else {}
        if not identity or str(identity.get("kind") or "") == "entity":
            continue
        subject_terms = _identity_terms(identity, "subject")
        if not subject_terms or not any(term in subject_span or subject_span in term for term in subject_terms):
            continue
        value_terms = _identity_terms(identity, "value")
        direct = any(predicate == term or predicate in term or term in predicate for term in value_terms)
        key = (subject_terms[0], predicate)
        if key in seen:
            continue
        seen.add(key)
        relations.append(
            {
                "subject": subject_terms[0],
                "subject_terms": subject_terms,
                "asked_predicate": predicate,
                "authorized_values": value_terms,
                "permitted_polarity": "positive" if direct else "negative",
                "kind": "direct_authorized_fact" if direct else "derived_denial",
            }
        )
    return relations


def _slot_fill_reasons(sentence: str, decision: Mapping[str, Any] | None) -> list[str]:
    slots = {str(item) for item in ((decision or {}).get("unresolved_qualifiers") or []) if str(item).strip()}
    if not slots:
        return []
    if epistemic_frame(sentence) in {"rumor", "hearsay", "uncertain", "speculative"}:
        return []
    unknown = bool(_UNKNOWN_SLOT_RE.search(sentence or ""))
    reasons: list[str] = []
    if "actor" in slots and _AGENT_FILL_RE.search(sentence or "") and not unknown:
        reasons.append("unauthorized_qualifier:actor")
    if "time" in slots and _TIME_FILL_RE.search(sentence or "") and not unknown:
        reasons.append("unauthorized_qualifier:time")
    if "cause" in slots and not unknown:
        if _CAUSE_FILL_RE.search(sentence or ""):
            reasons.append("unauthorized_qualifier:cause")
        if _EVENT_SITE_RE.search(sentence or ""):
            reasons.append("unauthorized_qualifier:location")
    return reasons


def _is_interrogative(sentence: str) -> bool:
    """A direct question is not a consequential assertion."""
    return str(sentence or "").rstrip().endswith("?")


def _attributed_epistemic_source(sentence: str, response_text: str = "") -> bool:
    """NPC testimony needs a speaker, quote, or hearsay frame. Narrator hedging is not a source.

    A sentence splitter can cut a quotation before its closing mark. An opening
    quote still counts when the full response contains the quotation.
    """
    if re.search(r"\b(?:you can tell|details tell the same story|tell the same story)\b", sentence or "", re.IGNORECASE):
        return False
    opened = str(sentence or "").lstrip().startswith(("\"", "“")) or bool(re.search(r"\b\w+\s+says?,\s*[\"“]", sentence or "", re.IGNORECASE))
    if opened and not _QUOTE_SPAN_RE.search(sentence or "") and _QUOTE_SPAN_RE.search(response_text or ""):
        return True
    outside = _outside_quotes(sentence or "")
    if _ACTOR_ATTRIBUTION_RE.search(outside) or _EVENT_HISTORY_ASSERTION_RE.search(outside):
        return False
    if _QUOTE_SPAN_RE.search(sentence or ""):
        return True
    return bool(_ATTRIBUTED_SOURCE_RE.search(sentence or ""))


def _fact_can_ground_definite(row: Mapping[str, Any]) -> bool:
    """Authoritative text can ground a definite. A speculative inference cannot.

    Accepted bounded inferences stay in proposed facts for persistence, but they
    are not pre-existing world ground. A hedge token copied from one cannot
    make a neighboring narration span look grounded.
    """
    provenance = str(row.get("provenance") or "")
    authority = str(row.get("authority") or "")
    if authority == AUTH_INFERENCE:
        return False
    if provenance in {PROVENANCE_GM_INFERENCE, PROVENANCE_SPECULATION, PROVENANCE_GENERATED_PROPOSAL}:
        return False
    return True


def _decision_ground(authored_corpus: str, decision: Mapping[str, Any] | None) -> str:
    parts = [str(authored_corpus or "")]
    rows = (decision or {}).get("proposed_facts") if isinstance(decision, Mapping) else None
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, Mapping) and _fact_can_ground_definite(row):
                parts.append(str(row.get("text") or ""))
    return " ".join(parts).lower()


def _definite_content_tokens(phrase: str) -> list[str]:
    tokens: list[str] = []
    for raw in re.findall(r"[a-z']+", phrase.lower()):
        token = raw.replace("'s", "").replace("'", "")
        if len(token) < 5 or token in _DEFINITE_STOP:
            continue
        tokens.append(token)
    return tokens


def _has_ungrounded_definite(sentence: str, ground: str) -> bool:
    for match in _DEFINITE_PHRASE_RE.finditer(sentence or ""):
        tokens = _definite_content_tokens(match.group(1))
        if tokens and not any(token in ground for token in tokens):
            return True
    return False


def _has_ungrounded_consequential_definite(sentence: str, ground: str, *, status_frame: bool) -> bool:
    """Ungrounded definite content, ignoring the subject of an unresolved-status frame.

    ``the explanation remains uncertain`` names the status slot. ``that motive
    remains uncertain`` still names motive. The status words do not ground it.
    """
    skip = (
        _EPISTEMIC_BOILERPLATE | _UNRESOLVED_STATUS_SUBJECTS | _UNRESOLVED_STATUS_MODIFIERS
        if status_frame
        else frozenset()
    )
    for match in _DEFINITE_PHRASE_RE.finditer(sentence or ""):
        tokens = [token for token in _definite_content_tokens(match.group(1)) if token not in skip]
        if tokens and not any(token in ground for token in tokens):
            return True
    return False


def _unsupported_narrator_lead(
    sentence: str,
    authored_corpus: str,
    decision: Mapping[str, Any] | None,
    response_text: str = "",
) -> bool:
    """A hedged lead with no epistemic source is still a generated proposal.

    Unresolved-status wording does not exempt a different ungrounded noun.
    """
    if _attributed_epistemic_source(sentence, response_text):
        return False
    unresolved = _marks_unresolved_status(sentence)
    if not (
        _NARRATOR_MODAL_RE.search(sentence or "")
        or _UNCERTAIN_FRAME_RE.search(sentence or "")
        or unresolved
    ):
        return False
    if _SPECIFIC_LEAD_RE.search(sentence or "") and not _decision_authorizes_specific_lead(sentence, decision):
        return True
    if _GENERATED_LEAD_RE.search(sentence or ""):
        rows = _authorized_rows_for_sentence(sentence, decision)
        authorized_lead = any(
            str((row.get("semantic_identity") or {}).get("relation") or "").lower()
            in {"lead", "actionable_lead", "gameplay_lead", "evidence", "evidential"}
            for row in rows
            if isinstance(row, Mapping) and isinstance(row.get("semantic_identity"), Mapping)
        )
        if not authorized_lead:
            return True
    return _has_ungrounded_consequential_definite(
        sentence,
        _decision_ground(authored_corpus, decision),
        status_frame=unresolved,
    )


def _harmless_qualified_npc_observation(
    sentence: str,
    decision: Mapping[str, Any] | None,
) -> bool:
    """Allow qualified, non-mutating NPC demeanor observations in incidental dialogue.

    This is intentionally narrower than "contains a hedge": it is limited to
    social ask decisions with no state mutation, a visible low-stakes/demeanor
    surface, and no structural consequential assertion.
    """
    text = sentence or ""
    if str((decision or {}).get("outcome_classification") or "") != OUTCOME_EPISTEMIC:
        return False
    if (decision or {}).get("permitted_state_mutations"):
        return False
    if not (_NARRATOR_MODAL_RE.search(text) or _UNCERTAIN_FRAME_RE.search(text)):
        return False
    if not _LOW_STAKES_STATE_RE.search(text):
        return False
    if _SPECIFIC_LEAD_RE.search(text) or _GENERATED_LEAD_RE.search(text):
        return False
    if _STATEFUL_ASSERTION_RE.search(text) or _MOVEMENT_RE.search(_outside_quotes(text)):
        return False
    if _GROUP_PLACE_RE.search(text) or _RESIDUE_ASSERT_RE.search(text):
        return False
    structural = set(_structured_consequential_reasons(text))
    structural.discard("unsupported_narrator_lead")
    structural.discard("unauthorized_negative_evidence")
    return not structural


def _content_tokens(text: str) -> set[str]:
    return {token for token in _token_set(text) if len(token) > 3}


def _departure_exit_reuse_reasons(sentence: str, decision: Mapping[str, Any] | None) -> list[str]:
    """A departure exit stated as a present onward route is not a destination fact."""
    if not _PRESENT_ONWARD_RE.search(sentence or ""):
        return []
    rows = (decision or {}).get("proposed_facts") if isinstance(decision, Mapping) else None
    if not isinstance(rows, list):
        return []
    departure: set[str] = set()
    destination: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
        role = str(identity.get("scene_role") or "")
        tokens = _content_tokens(str(row.get("text") or ""))
        if role == "departure_exit":
            departure |= tokens
        elif role in {"destination_fact", "destination_exit"}:
            destination |= tokens
    if not departure:
        return []
    overlap = _content_tokens(sentence) & departure
    if not overlap or overlap <= destination:
        return []
    return ["departure_exit_reused_as_destination_exit"]


def _executable_obligations(decision: Mapping[str, Any] | None, resolution: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(decision, Mapping):
        record = decision.get("executable_obligations")
        if isinstance(record, Mapping):
            return dict(record)
    contract = contract_mapping_from_resolution(resolution if isinstance(resolution, Mapping) else None)
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    record = construction.get("executable_obligations") if isinstance(construction, Mapping) else None
    return dict(record) if isinstance(record, Mapping) else {}


def narration_acknowledges_supporting(text: str | None, obligations: Mapping[str, Any] | None) -> bool:
    """True when each committed supporting social act is named, or there is none."""
    supporting = (obligations or {}).get("supporting") if isinstance(obligations, Mapping) else None
    if not isinstance(supporting, list):
        return True
    low = str(text or "").lower()
    aliases = {
        "thank": ("thank",),
        "farewell": ("farewell", "goodbye", "good-bye", "bye"),
        "tell": ("tell", "told"),
        "ask": ("ask", "asked"),
    }
    for item in supporting:
        if not isinstance(item, Mapping) or item.get("kind") != "social":
            continue
        act = str(item.get("act") or "")
        words = aliases.get(act, (act,))
        if act and not any(word and word in low for word in words):
            return False
    return True


def _mentions_governed_subject(sentence: str, decision: Mapping[str, Any] | None) -> bool:
    rows = (decision or {}).get("proposed_facts") if isinstance(decision, Mapping) else None
    if not isinstance(rows, list):
        return False
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        identity = row.get("semantic_identity")
        if not isinstance(identity, Mapping) or str(identity.get("kind") or "") == "entity":
            continue
        terms = _identity_terms(identity, "subject") + _identity_terms(identity, "target_scene_id")
        if terms and _text_has_any(sentence, terms):
            return True
    return False


def _predicate_asserted(sentence: str, predicate: str, subject_terms: Sequence[str]) -> bool:
    """The asked predicate as its own claim, not a token inside a subject alias."""
    masked = _norm_phrase(sentence)
    for term in sorted((term for term in subject_terms if term), key=len, reverse=True):
        masked = masked.replace(term, " ")
    return bool(re.search(rf"\b{re.escape(predicate)}\b", masked))


def _answer_relation_reasons(sentence: str, decision: Mapping[str, Any] | None) -> list[str]:
    rows = (decision or {}).get("answer_relations") if isinstance(decision, Mapping) else None
    if not isinstance(rows, list):
        return []
    reasons: list[str] = []
    for rel in rows:
        if not isinstance(rel, Mapping):
            continue
        subjects = [str(item) for item in (rel.get("subject_terms") or []) if str(item).strip()]
        if subjects and not _text_has_any(sentence, subjects):
            continue
        predicate = str(rel.get("asked_predicate") or "").strip()
        if not predicate or not _predicate_asserted(sentence, predicate, subjects):
            continue
        negated = _negation_scopes_over(sentence, [predicate])
        polarity = str(rel.get("permitted_polarity") or "")
        if polarity == "negative" and not negated:
            reasons.append("unsupported_consequential_inference")
        elif polarity == "positive" and negated:
            reasons.append("semantic_polarity:value")
    return reasons


def _proposition_rows_for_sentence(sentence: str, response_text: str, authored_corpus: str) -> list[dict[str, Any]]:
    """Classify against the whole reply so a later sentence can complete an authorized one."""
    rows = classify_propositions(response_text or sentence, authored_corpus=authored_corpus)
    wanted = _norm_phrase(sentence)
    matched = [row for row in rows if _norm_phrase(str(row.get("text") or "")) == wanted]
    if matched:
        return matched
    return [row for row in classify_propositions(sentence, authored_corpus=authored_corpus)]


def _unauthorized_fact(text: str, reasons: list[str]) -> GMProposedFact:
    return GMProposedFact(
        text=text,
        provenance=PROVENANCE_GENERATED_PROPOSAL,
        consequence="consequential",
        authorized=False,
        reason_codes=sorted(set(reasons)),
        authority=AUTH_UNAUTHORIZED,
        persistence=PERSIST_NONE,
        outcome_classification=OUTCOME_UNRESOLVED,
    )


def _decision_from_contract(
    contract: Mapping[str, Any],
    *,
    resolution: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
) -> GMResolutionDecision:
    operation = str(contract.get("operation") or "").strip().lower()
    dims = {str(item) for item in (contract.get("dimensions") or []) if str(item).strip()}
    if contract.get("dimension"):
        dims.add(str(contract.get("dimension")))
    mutations = _state_mutations_from_resolution(resolution)
    established = []
    corpus = _authored_corpus(scene, world)
    proposed_facts = _authored_fact_rows(scene, world)
    session_record = contract.get("session") if isinstance(contract.get("session"), Mapping) else None
    proposed_facts.extend(_runtime_fact_rows(session_record, scene))
    proposed_facts.extend(_temporal_provenance_rows(session_record))
    if corpus.strip():
        established.append("scene_world_authored_corpus")
    if str(contract.get("discourse_ref") or "").strip():
        established.append("contract_discourse_ref")

    if mutations:
        outcome = OUTCOME_MUTATION
        persistence = PERSIST_WORLD
        for mutation in mutations:
            if mutation.get("type") == "location":
                row = _fact(
                    f"Location changes to {mutation.get('target_scene_id')}",
                    provenance=PROVENANCE_AUTHORITATIVE,
                    consequence="consequential",
                    authorized=True,
                    authority=AUTH_WORLD,
                    persistence=PERSIST_WORLD,
                    source_ref="resolution.permitted_state_mutations.location",
                    outcome_classification=OUTCOME_AUTHORIZED_STATE,
                    reason_codes=["authorized_state_mutation"],
                    semantic_identity={
                        "kind": "movement",
                        "relation": "transition",
                        "source_scene_id": str((resolution or {}).get("source_scene_id") or contract.get("scene_id") or ""),
                        "target_scene_id": str(mutation.get("target_scene_id") or ""),
                        "target_name": str(mutation.get("target_scene_id") or "").replace("_", " "),
                        "target_name_aliases": [str(mutation.get("target_scene_id") or "").replace("_", " ")],
                        "authority": AUTH_WORLD,
                    },
                )
                if row is not None:
                    proposed_facts.append(row)
            elif mutation.get("type") == "state_change":
                row = _fact(
                    f"State {mutation.get('key')} changes to {mutation.get('value')}",
                    provenance=PROVENANCE_AUTHORITATIVE,
                    consequence="consequential",
                    authorized=True,
                    authority=AUTH_WORLD,
                    persistence=PERSIST_WORLD,
                    source_ref=f"resolution.state_changes.{mutation.get('key')}",
                    outcome_classification=OUTCOME_AUTHORIZED_STATE,
                    reason_codes=["authorized_state_mutation"],
                    semantic_identity={
                        "kind": "state_change",
                        "subject": str(mutation.get("key") or ""),
                        "relation": "state_change",
                        "value": str(mutation.get("value") or ""),
                        "authority": AUTH_WORLD,
                    },
                )
                if row is not None:
                    proposed_facts.append(row)
    elif operation in {"perceive", "inspect"} and dims & {"appearance", "sound", "smell", "wear", "use", "change"}:
        outcome = OUTCOME_INCIDENTAL
        persistence = PERSIST_INCIDENTAL
    elif dims & {"source", "confidence", "location", "time", "interpretation"} or operation in {"ask", "repeat"}:
        outcome = OUTCOME_EPISTEMIC if str(contract.get("interlocutor_id") or "") else OUTCOME_ESTABLISHED
        persistence = PERSIST_CLAIM if outcome == OUTCOME_EPISTEMIC else PERSIST_NONE
    elif operation in {"act", "follow", "confirm"}:
        outcome = OUTCOME_UNRESOLVED
        persistence = PERSIST_NONE
    else:
        outcome = OUTCOME_ESTABLISHED
        persistence = PERSIST_NONE

    constraints = [
        "Narration may not establish consequential world facts absent this decision.",
        "Generated proposals are not world truth unless already grounded or explicitly permitted.",
        "NPC claims remain claims; belief/hearsay/uncertainty does not promote them.",
        "Inference must not be narrated as physical evidence.",
    ]
    if not any(m.get("type") == "location" for m in mutations):
        constraints.append("Do not narrate authoritative travel/location change unless a location mutation is permitted.")
    if outcome == OUTCOME_INCIDENTAL:
        constraints.append("Harmless sensory, mannerism, and mundane connective detail may persist as bounded incidental continuity.")
    if outcome == OUTCOME_UNRESOLVED:
        constraints.append("Requested consequential result remains unresolved unless separately authorized by resolver/state.")

    unresolved_qualifiers = _unresolved_qualifiers_for(contract, proposed_facts)
    answer_relations = _answer_relations_for(contract, proposed_facts)
    if unresolved_qualifiers:
        constraints.append(
            "Cause, actor, and time may be called unknown. That does not deny an established condition."
        )
    if any(rel.get("kind") == "derived_denial" for rel in answer_relations):
        constraints.append(
            "The asked predicate is not an authorized value. It may be denied. It may not be asserted."
        )
    epistemic_acts: list[dict[str, Any]] = []
    for row in proposed_facts:
        epistemic_acts.append(
            {
                "act": EPISTEMIC_ACT_ESTABLISH if row.authority == AUTH_WORLD else EPISTEMIC_ACT_INFER,
                "source_ref": row.source_ref,
                "authority": row.authority,
                "semantic_identity": dict(row.semantic_identity or {}),
            }
        )
    if "interpretation" in dims:
        epistemic_acts.append(
            {
                "act": EPISTEMIC_ACT_INFER,
                "authority": AUTH_OBSERVATION,
                "semantic_identity": {
                    "relation_kind": REL_EPISTEMIC_STATUS,
                    "epistemic_status": STATUS_INFERRED,
                    "subject": str(contract.get("conversational_subject") or ""),
                    "scope": "qualified_possibilities_only",
                },
            }
        )
        constraints.append(
            "Qualified possibilities may be inferred from authorized observations; no cause, actor, or history is established."
        )
    if unresolved_qualifiers or outcome == OUTCOME_UNRESOLVED or "confidence" in dims:
        epistemic_acts.append(
            {
                "act": EPISTEMIC_ACT_LEAVE_UNRESOLVED,
                "authority": AUTH_OBSERVATION,
                "semantic_identity": {
                    "relation_kind": REL_EPISTEMIC_STATUS,
                    "epistemic_status": STATUS_UNRESOLVED,
                    "unresolved_qualifiers": list(unresolved_qualifiers),
                    "scope": "status_answer" if "confidence" in dims else "unresolved_qualifiers",
                },
            }
        )
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    obligations = construction.get("executable_obligations") if isinstance(construction, Mapping) else {}
    if not isinstance(obligations, Mapping):
        obligations = {}
    for item in obligations.get("supporting") or []:
        if isinstance(item, Mapping) and item.get("kind") == "social" and item.get("act"):
            constraints.append(_SUPPORTING_SOCIAL_CONSTRAINT.format(act=str(item.get("act"))))
    realization_claims = _realization_claims_from_decision_parts(proposed_facts, epistemic_acts)
    if any(claim.premise_claim_ids for claim in realization_claims):
        constraints.append(
            "An unresolved cause, actor, time, reason, or status does not establish its premise. "
            "A hypothetical or player-stated premise may be realized only conditionally."
        )

    return GMResolutionDecision(
        contract_id=str(contract.get("contract_id") or ""),
        resolution_method=str((resolution or {}).get("kind") or operation or "ordinary"),
        outcome_classification=outcome,
        established_fact_refs=established,
        proposed_facts=proposed_facts,
        permitted_state_mutations=mutations,
        persistence_policy=persistence,
        narration_constraints=constraints,
        unresolved_consequential_questions=["requested_consequence_not_established"] if outcome == OUTCOME_UNRESOLVED else [],
        unresolved_qualifiers=unresolved_qualifiers,
        answer_relations=answer_relations,
        epistemic_acts=epistemic_acts,
        realization_claims=realization_claims,
        executable_obligations=dict(obligations),
    )


def build_gm_resolution_decision(
    *,
    resolution: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    normalized_action: Mapping[str, Any] | None = None,
) -> GMResolutionDecision | None:
    """Build the decision from the existing Resolution Contract and state.

    ``session`` and ``normalized_action`` are accepted for call-site symmetry;
    raw player text is intentionally not an input.
    """
    contract = contract_mapping_from_resolution(resolution if isinstance(resolution, Mapping) else None)
    if not contract.get("contract_id"):
        return None
    if session is not None and isinstance(contract, dict):
        contract = {**contract, "session": session}
    return _decision_from_contract(contract, resolution=resolution, scene=scene, world=world)


def _scene_payload(scene: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(scene, Mapping):
        return {}
    inner = scene.get("scene")
    return inner if isinstance(inner, Mapping) else scene


def _scene_identity(scene: Mapping[str, Any] | None) -> str:
    return str(_scene_payload(scene).get("id") or "").strip()


def _fact_dict(
    text: str,
    *,
    source_ref: str,
    semantic_identity: Mapping[str, Any],
) -> dict[str, Any]:
    row = _fact(
        text,
        provenance=PROVENANCE_AUTHORITATIVE,
        consequence="consequential",
        authorized=True,
        authority=AUTH_WORLD,
        persistence=PERSIST_WORLD,
        source_ref=source_ref,
        outcome_classification=OUTCOME_ESTABLISHED,
        reason_codes=["authored_state_source"],
        semantic_identity=dict(semantic_identity),
    )
    return row.as_dict() if row is not None else {}


def _looks_like_departure_exit(text: str, departure: Mapping[str, Any], target_scene_id: str) -> bool:
    low = text.lower()
    target_name = target_scene_id.replace("_", " ").strip()
    if target_name and target_name in low:
        return True
    for exit_row in _scene_payload(departure).get("exits") or []:
        if not isinstance(exit_row, Mapping):
            continue
        label = str(exit_row.get("label") or "")
        shared = _content_tokens(label) & _content_tokens(text)
        if len(shared) >= 2:
            return True
        target = str(exit_row.get("target_scene_id") or exit_row.get("targetSceneId") or "")
        if target == target_scene_id and re.search(r"\b(?:stair|stairs|climb|door|path|road|arch|ladder|steps|gate)\b", low):
            return True
    return False


def reconcile_movement_decision(
    resolution: dict[str, Any],
    *,
    departure_scene: Mapping[str, Any] | None = None,
    destination_scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Copy an authoritative scene transition into the decision that will govern narration.

    The contract and decision are built before the travel resolver runs. This is a
    one-way update from the resolver result. It does not choose the destination.
    """
    if not isinstance(resolution, dict):
        return resolution
    metadata = resolution.get("metadata")
    if not isinstance(metadata, dict):
        return resolution
    decision = metadata.get(DECISION_METADATA_KEY)
    if not isinstance(decision, dict):
        return resolution
    kind = str(resolution.get("kind") or "").strip().lower()
    target = _clean(resolution.get("target_scene_id") or resolution.get("targetSceneId"), limit=80)
    resolved = bool(resolution.get("resolved_transition")) and bool(target)
    source = str(resolution.get("originating_scene_id") or _scene_identity(departure_scene) or "").strip()
    constraints = [str(item) for item in (decision.get("narration_constraints") or []) if str(item).strip()]
    facts = [dict(row) for row in (decision.get("proposed_facts") or []) if isinstance(row, dict)]
    mutations = [dict(row) for row in (decision.get("permitted_state_mutations") or []) if isinstance(row, dict)]

    if kind in {"scene_transition", "travel"} and not resolved:
        mutations = [row for row in mutations if row.get("type") != "location"]
        decision["permitted_state_mutations"] = mutations
        decision["outcome_classification"] = OUTCOME_UNRESOLVED
        decision["persistence_policy"] = PERSIST_NONE
        decision["unresolved_consequential_questions"] = ["movement_unresolved"]
        if _NO_ARRIVAL_CONSTRAINT not in constraints:
            constraints.append(_NO_ARRIVAL_CONSTRAINT)
        decision["narration_constraints"] = constraints
        metadata[DECISION_METADATA_KEY] = decision
        return resolution

    if not resolved:
        return resolution

    destination_id = _scene_identity(destination_scene) or target
    for row in facts:
        identity = dict(row.get("semantic_identity") or {}) if isinstance(row.get("semantic_identity"), Mapping) else {}
        if identity.get("scene_role"):
            row["semantic_identity"] = identity
            continue
        source_ref = str(row.get("source_ref") or "")
        if not source_ref.startswith("scene."):
            continue
        role = "departure_exit" if _looks_like_departure_exit(str(row.get("text") or ""), departure_scene or {}, target) else "departure_fact"
        identity.update({"kind": identity.get("kind") or "scene_fact", "scene_id": source, "scene_role": role})
        row["semantic_identity"] = identity

    present = {(str(row.get("text") or ""), str((row.get("semantic_identity") or {}).get("scene_role") or "")) for row in facts}
    destination = _scene_payload(destination_scene)
    for index, item in enumerate(destination.get("visible_facts") or []):
        text = item.get("text") if isinstance(item, Mapping) else str(item)
        key = (str(text or "").strip(), "destination_fact")
        if not key[0] or key in present:
            continue
        row = _fact_dict(
            str(text),
            source_ref=f"destination.visible_facts.{index}",
            semantic_identity={"kind": "scene_fact", "scene_id": destination_id, "scene_role": "destination_fact"},
        )
        if row:
            facts.append(row)
            present.add(key)
    for index, exit_row in enumerate(destination.get("exits") or []):
        if not isinstance(exit_row, Mapping):
            continue
        label = str(exit_row.get("label") or "").strip()
        exit_target = str(exit_row.get("target_scene_id") or exit_row.get("targetSceneId") or "").strip()
        if not label:
            continue
        key = (label, "destination_exit")
        if key in present:
            continue
        row = _fact_dict(
            label,
            source_ref=f"destination.exits.{index}",
            semantic_identity={
                "kind": "scene_fact",
                "scene_id": destination_id,
                "scene_role": "destination_exit",
                "exit_target_scene_id": exit_target,
            },
        )
        if row:
            facts.append(row)
            present.add(key)

    location = next((row for row in mutations if row.get("type") == "location"), None)
    if location is None:
        mutations.insert(0, {"type": "location", "source_scene_id": source, "target_scene_id": target})
    else:
        location["source_scene_id"] = location.get("source_scene_id") or source
        location["target_scene_id"] = target
    move_text = f"Location changes from {source or 'the current scene'} to {target}"
    already_movement = any(
        str((row.get("semantic_identity") or {}).get("kind") or "") == "movement"
        or str(row.get("source_ref") or "").startswith("resolution.permitted_state_mutations.location")
        for row in facts
    )
    if not already_movement:
        facts.append(
            {
                "text": move_text,
                "provenance": PROVENANCE_AUTHORITATIVE,
                "consequence": "consequential",
                "authorized": True,
                "reason_codes": ["authorized_state_mutation"],
                "authority": AUTH_WORLD,
                "persistence": PERSIST_WORLD,
                "source_ref": "resolution.permitted_state_mutations.location",
                "outcome_classification": OUTCOME_AUTHORIZED_STATE,
                "semantic_identity": {
                    "kind": "movement",
                    "relation": "transition",
                    "source_scene_id": source,
                    "target_scene_id": target,
                    "target_name": target.replace("_", " "),
                    "authority": AUTH_WORLD,
                },
            }
        )

    decision["proposed_facts"] = facts
    decision["permitted_state_mutations"] = mutations
    decision["outcome_classification"] = OUTCOME_MUTATION
    decision["persistence_policy"] = PERSIST_WORLD
    decision["resolution_method"] = kind or "scene_transition"
    decision["unresolved_consequential_questions"] = []
    kept = [
        item
        for item in constraints
        if "unless a location mutation is permitted" not in item
        and "remains unresolved unless separately authorized" not in item
        and item != _NO_ARRIVAL_CONSTRAINT
    ]
    if _DEPARTURE_EXIT_CONSTRAINT not in kept:
        kept.append(_DEPARTURE_EXIT_CONSTRAINT)
    kept.append(f"Destination scene is {target}. Narrate destination-authored facts as the place arrived at.")
    decision["narration_constraints"] = kept
    metadata[DECISION_METADATA_KEY] = decision
    return resolution


def decision_from_resolution(resolution: Mapping[str, Any] | None) -> dict[str, Any]:
    metadata = resolution.get("metadata") if isinstance(resolution, Mapping) else None
    decision = metadata.get(DECISION_METADATA_KEY) if isinstance(metadata, Mapping) else None
    return dict(decision) if isinstance(decision, Mapping) else {}


def attach_gm_resolution_decision(
    resolution: dict[str, Any],
    *,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    normalized_action: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(resolution, dict):
        return resolution
    decision = build_gm_resolution_decision(
        resolution=resolution,
        session=session,
        scene=scene,
        world=world,
        normalized_action=normalized_action,
    )
    if decision is None:
        return resolution
    md = resolution.setdefault("metadata", {})
    if isinstance(md, dict):
        md[DECISION_METADATA_KEY] = decision.as_dict()
    return resolution


def _classify_narrated_fact_legacy(
    sentence: str,
    *,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
    response_text: str = "",
) -> GMProposedFact | None:
    text = _clean(sentence, limit=600)
    if not text:
        return None
    if _NONASSERTION_FRAME_RE.search(text):
        if _CLAIM_FRAME_RE.search(text):
            return GMProposedFact(
                text=text,
                provenance=PROVENANCE_NPC_CLAIM,
                consequence="epistemic",
                authorized=True,
                reason_codes=["explicit_testimony_nonassertion"],
                authority=AUTH_CLAIM,
                persistence=PERSIST_CLAIM,
                outcome_classification=OUTCOME_EPISTEMIC,
            )
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_SPECULATION,
            consequence="epistemic",
            authorized=True,
            reason_codes=["explicit_nonassertion"],
            authority=AUTH_OBSERVATION,
            persistence=PERSIST_NONE,
            outcome_classification=OUTCOME_EPISTEMIC,
        )
    grounded = _grounded(text, authored_corpus)
    consequential = _unlicensed_consequential_reasons(text, decision)
    quoted_claim = _is_claim_or_uncertain(text)
    outside = _outside_quotes(text)
    movement = bool(_MOVEMENT_RE.search(outside))
    prop_rows = _proposition_rows_for_sentence(text, response_text or text, authored_corpus)
    slot_reasons = _slot_fill_reasons(text, decision)
    if slot_reasons and (
        "unauthorized_qualifier:location" in slot_reasons
        or _mentions_governed_subject(text, decision)
        or _AGENT_FILL_RE.search(text)
    ):
        return _unauthorized_fact(text, slot_reasons)
    relation_reasons = _answer_relation_reasons(text, decision)
    if relation_reasons:
        return _unauthorized_fact(text, relation_reasons)
    exit_reasons = _departure_exit_reuse_reasons(text, decision)
    if exit_reasons:
        return _unauthorized_fact(text, exit_reasons)
    if _harmless_qualified_npc_observation(text, decision):
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_SPECULATION,
            consequence="epistemic",
            authorized=True,
            reason_codes=["harmless_qualified_npc_observation"],
            authority=AUTH_OBSERVATION,
            persistence=PERSIST_NONE,
            outcome_classification=OUTCOME_EPISTEMIC,
        )
    if _unsupported_narrator_lead(text, authored_corpus, decision, response_text):
        return _unauthorized_fact(text, ["unsupported_narrator_lead"])
    if _is_interrogative(text):
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_SPECULATION,
            consequence="epistemic",
            authorized=True,
            reason_codes=["interrogative_not_assertion"],
            authority=AUTH_OBSERVATION,
            persistence=PERSIST_NONE,
            outcome_classification=OUTCOME_EPISTEMIC,
        )
    authorized_row = _authorized_by_decision(text, decision)
    if authorized_row is not None:
        return GMProposedFact(
            text=text,
            provenance=str(authorized_row.get("provenance") or PROVENANCE_AUTHORITATIVE),
            consequence=str(authorized_row.get("consequence") or "consequential"),
            authorized=True,
            reason_codes=list(authorized_row.get("reason_codes") or ["authorized_by_pre_narration_decision"]),
            authority=str(authorized_row.get("authority") or AUTH_WORLD),
            persistence=str(authorized_row.get("persistence") or PERSIST_NONE),
            source_ref=str(authorized_row.get("source_ref") or ""),
            outcome_classification=str(authorized_row.get("outcome_classification") or OUTCOME_ESTABLISHED),
            semantic_identity=dict(authorized_row.get("semantic_identity") or {}),
        )
    semantic_rejection = _structured_semantic_rejection(text, decision)
    if semantic_rejection:
        return _unauthorized_fact(text, semantic_rejection)
    if any(row.get("kind") == "authoritative_fact" and row.get("grounded") for row in prop_rows):
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_AUTHORITATIVE,
            consequence="consequential",
            authorized=True,
            reason_codes=["grounded_in_authored_corpus"],
            authority=AUTH_WORLD,
            persistence=PERSIST_WORLD,
            outcome_classification=OUTCOME_ESTABLISHED,
        )
    if _GROUP_PLACE_RE.search(text):
        return _unauthorized_fact(text, ["unauthorized_social_world_fact"])
    if _RESIDUE_ASSERT_RE.search(text) and _mentions_governed_subject(text, decision):
        return _unauthorized_fact(text, ["unauthorized_physical_residue"])
    if _UNKNOWN_SLOT_RE.search(text):
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_SPECULATION,
            consequence="epistemic",
            authorized=True,
            reason_codes=["unknown_cause_actor_or_time"],
            authority=AUTH_OBSERVATION,
            persistence=PERSIST_NONE,
            outcome_classification=OUTCOME_EPISTEMIC,
        )
    if any(row.get("consequential") and row.get("kind") not in {INCIDENTAL_KIND, NPC_CLAIM_KIND} for row in prop_rows):
        consequential.append("proposition_authority")
    consequential.extend(reason for reason in _structured_consequential_reasons(text) if reason not in consequential)
    if movement and not any((m or {}).get("type") == "location" for m in (decision or {}).get("permitted_state_mutations") or []):
        consequential.append("unpermitted_location_movement")
    if not consequential and _INCIDENTAL_RE.search(text):
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_INCIDENTAL,
            consequence="low",
            authorized=True,
            reason_codes=["bounded_incidental_texture"],
            authority=AUTH_INCIDENTAL,
            persistence=PERSIST_INCIDENTAL,
            outcome_classification=OUTCOME_INCIDENTAL,
        )
    if quoted_claim and _attributed_epistemic_source(text):
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_NPC_CLAIM,
            consequence="consequential" if consequential else "epistemic",
            authorized=True,
            reason_codes=sorted(set(consequential or ["epistemically_qualified"])),
            authority=AUTH_CLAIM,
            persistence=PERSIST_CLAIM,
            outcome_classification=OUTCOME_EPISTEMIC,
        )
    if not consequential and not prop_rows:
        return None
    if grounded:
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_AUTHORITATIVE,
            consequence="consequential" if consequential else "low",
            authorized=True,
            reason_codes=["grounded_in_authored_corpus"],
            authority=AUTH_WORLD,
            persistence=PERSIST_WORLD,
            outcome_classification=OUTCOME_ESTABLISHED,
        )
    if consequential:
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_GENERATED_PROPOSAL,
            consequence="consequential",
            authorized=False,
            reason_codes=sorted(set(consequential)),
            authority=AUTH_UNAUTHORIZED,
            persistence=PERSIST_NONE,
            outcome_classification=OUTCOME_UNRESOLVED,
        )
    if any(row.get("kind") == NPC_CLAIM_KIND for row in prop_rows) and _attributed_epistemic_source(text):
        return GMProposedFact(
            text=text,
            provenance=PROVENANCE_NPC_CLAIM,
            consequence="epistemic",
            authorized=True,
            reason_codes=["proposition_authority_claim"],
            authority=AUTH_CLAIM,
            persistence=PERSIST_CLAIM,
            outcome_classification=OUTCOME_EPISTEMIC,
        )
    return None


def audit_narrated_claims(
    sentence: str,
    *,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
    response_text: str = "",
) -> list[NarratedClaim]:
    """Return claim-level authority results for one narration unit.

    Authorized semantic-identity coverage is recorded as a claim, but it never
    licenses causal, evidential, temporal, actor, history, or certainty residuals
    in the rest of the same sentence.
    """
    text = _clean(sentence, limit=600)
    if not text:
        return []

    if _is_claim_or_uncertain(text) and _attributed_epistemic_source(text, response_text or text):
        return [
            _claim(
                text,
                reasons=["epistemically_qualified"],
                relation_kind=REL_EPISTEMIC_STATUS,
                provenance=PROVENANCE_NPC_CLAIM,
                authority=AUTH_CLAIM,
                epistemic_status=epistemic_frame(text) or STATUS_UNRESOLVED,
                persistence=PERSIST_CLAIM,
                authorized=True,
                semantic_identity={"relation_kind": REL_EPISTEMIC_STATUS, "epistemic_status": epistemic_frame(text) or STATUS_UNRESOLVED},
            )
        ]

    claims: list[NarratedClaim] = []
    covered_rows = _authorized_rows_for_sentence(text, decision)
    claims.extend(_claim_from_row(text, row) for row in covered_rows)

    if _harmless_qualified_npc_observation(text, decision):
        return [
            _claim(
                text,
                reasons=["harmless_qualified_npc_observation"],
                relation_kind=REL_EPISTEMIC_STATUS,
                provenance=PROVENANCE_SPECULATION,
                authority=AUTH_OBSERVATION,
                epistemic_status=STATUS_UNRESOLVED,
                persistence=PERSIST_NONE,
                authorized=True,
                semantic_identity={
                    "relation_kind": REL_EPISTEMIC_STATUS,
                    "epistemic_status": STATUS_UNRESOLVED,
                    "scope": "harmless_qualified_npc_observation",
                },
            )
        ]

    if _authorized_epistemic_limit(text, decision):
        claims.append(
            _claim(
                text,
                reasons=["authorized_epistemic_limit"],
                relation_kind=REL_EPISTEMIC_STATUS,
                provenance=PROVENANCE_SPECULATION,
                authority=AUTH_OBSERVATION,
                epistemic_status=STATUS_UNRESOLVED,
                authorized=True,
                semantic_identity={
                    "relation_kind": REL_EPISTEMIC_STATUS,
                    "epistemic_status": STATUS_UNRESOLVED,
                    "polarity": "negative_knowledge",
                },
            )
        )
        # A pure unresolved-status sentence stops here. A cause, actor, history,
        # certainty, or unauthorized inference complement in the same sentence does not.
        if not _hedge_does_not_authorize(text, decision, authored_corpus):
            return claims

    if _unsupported_narrator_lead(text, authored_corpus, decision, response_text):
        claims.append(_claim(text, reasons=["unsupported_narrator_lead"], relation_kind=REL_GAMEPLAY_LEAD))

    if (
        _decision_allows_inference(decision)
        and _QUALIFIED_INFERENCE_RE.search(text)
        and not _GENERATED_LEAD_RE.search(text)
        and not _SPECIFIC_LEAD_RE.search(text)
    ):
        claims.append(
            _claim(
                text,
                reasons=["authorized_qualified_inference"],
                relation_kind=REL_EPISTEMIC_STATUS,
                provenance=PROVENANCE_GM_INFERENCE,
                authority=AUTH_OBSERVATION,
                epistemic_status=STATUS_INFERRED,
                authorized=True,
                semantic_identity={
                    "relation_kind": REL_EPISTEMIC_STATUS,
                    "epistemic_status": STATUS_INFERRED,
                },
            )
        )
        # The inference claim covers the hedge only. The complement is a separate
        # proposition. Cause, history, actor, certainty, and that complement still run.

    if _NONASSERTION_FRAME_RE.search(text):
        provenance = PROVENANCE_NPC_CLAIM if _CLAIM_FRAME_RE.search(text) else PROVENANCE_SPECULATION
        claims.append(
            _claim(
                text,
                reasons=["explicit_testimony_nonassertion" if provenance == PROVENANCE_NPC_CLAIM else "explicit_nonassertion"],
                relation_kind=REL_EPISTEMIC_STATUS,
                provenance=provenance,
                authority=AUTH_CLAIM if provenance == PROVENANCE_NPC_CLAIM else AUTH_OBSERVATION,
                epistemic_status=STATUS_UNRESOLVED,
                persistence=PERSIST_CLAIM if provenance == PROVENANCE_NPC_CLAIM else PERSIST_NONE,
                authorized=True,
                semantic_identity={"relation_kind": REL_EPISTEMIC_STATUS, "epistemic_status": STATUS_UNRESOLVED},
            )
        )
        return claims

    early_slot_reasons = _slot_fill_reasons(text, decision)
    if _is_interrogative(text) and "unauthorized_qualifier:location" not in early_slot_reasons:
        claims.append(
            _claim(
                text,
                reasons=["interrogative_not_assertion"],
                relation_kind=REL_EPISTEMIC_STATUS,
                provenance=PROVENANCE_SPECULATION,
                authority=AUTH_OBSERVATION,
                epistemic_status=STATUS_UNRESOLVED,
                authorized=True,
            )
        )
        return claims

    if _marks_unresolved_status(text):
        claims.append(
            _claim(
                text,
                reasons=["unknown_cause_actor_or_time"],
                relation_kind=REL_EPISTEMIC_STATUS,
                provenance=PROVENANCE_SPECULATION,
                authority=AUTH_OBSERVATION,
                epistemic_status=STATUS_UNRESOLVED,
                authorized=True,
                semantic_identity={"relation_kind": REL_EPISTEMIC_STATUS, "epistemic_status": STATUS_UNRESOLVED},
            )
        )

    claims.extend(_relationship_residual_claims(text, decision))

    unsupported_complements = _unauthorized_inference_complements(text, decision, authored_corpus)
    if unsupported_complements:
        claims.append(
            _claim(
                text,
                reasons=["unauthorized_inference_complement"],
                relation_kind=REL_PREDICATE,
                semantic_identity={
                    "relation_kind": "history",
                    "unsupported_complement": unsupported_complements[0],
                },
            )
        )

    slot_reasons = early_slot_reasons
    if slot_reasons and (
        "unauthorized_qualifier:location" in slot_reasons
        or _mentions_governed_subject(text, decision)
        or _AGENT_FILL_RE.search(text)
        or _TIME_FILL_RE.search(text)
        or _CAUSE_FILL_RE.search(text)
    ):
        claims.append(_claim(text, reasons=slot_reasons, relation_kind=REL_PREDICATE))

    relation_reasons = _answer_relation_reasons(text, decision)
    if relation_reasons:
        claims.append(_claim(text, reasons=relation_reasons, relation_kind=REL_PREDICATE))

    exit_reasons = _departure_exit_reuse_reasons(text, decision)
    if exit_reasons:
        claims.append(_claim(text, reasons=exit_reasons, relation_kind=REL_PREDICATE))

    semantic_rejection = _structured_semantic_rejection(text, decision)
    if semantic_rejection:
        claims.append(_claim(text, reasons=semantic_rejection, relation_kind=REL_PREDICATE))

    if _NEGATIVE_EVIDENCE_RE.search(text or "") and not _decision_authorizes_claim_family(
        text,
        decision,
        {"negative_evidence", "absence", "evidence", "evidential"},
    ):
        claims.append(
            _claim(
                text,
                reasons=["unauthorized_negative_evidence"],
                relation_kind=REL_EVIDENTIAL,
                semantic_identity={"relation_kind": REL_EVIDENTIAL, "polarity": "negative"},
            )
        )

    consequential = _unlicensed_consequential_reasons(text, decision)
    consequential.extend(reason for reason in _ordinary_residual_reasons(text, decision, covered_rows) if reason not in consequential)
    consequential.extend(reason for reason in _structured_consequential_reasons(text) if reason not in consequential)
    if not _EPISTEMIC_PARENT_REALIZATION_RE.search(text):
        prop_rows = _proposition_rows_for_sentence(text, response_text or text, authored_corpus)
        if any(row.get("consequential") and row.get("kind") not in {INCIDENTAL_KIND, NPC_CLAIM_KIND} for row in prop_rows):
            consequential.append("proposition_authority")
    outside = _outside_quotes(text)
    if bool(_MOVEMENT_RE.search(outside)) and not any((m or {}).get("type") == "location" for m in (decision or {}).get("permitted_state_mutations") or []):
        consequential.append("unpermitted_location_movement")
    if _GROUP_PLACE_RE.search(text):
        consequential.append("unauthorized_social_world_fact")
    if _RESIDUE_ASSERT_RE.search(text) and _mentions_governed_subject(text, decision):
        consequential.append("unauthorized_physical_residue")
    if (
        _DEFINITE_HISTORY_RE.search(text)
        and covered_rows
        and not _is_claim_or_uncertain(text)
        and not (
            _decision_authorizes_relation(text, decision, REL_CAUSAL)
            or _decision_authorizes_relation(text, decision, REL_EVIDENTIAL)
        )
    ):
        # A history/action/time assertion riding alongside an observation is a
        # residual claim unless a matching decision fact covers it.
        if not any(_row_relation_kind(row) in {REL_CAUSAL, REL_EVIDENTIAL} for row in covered_rows):
            consequential.append("unauthorized_consequential_residual")

    if covered_rows and not any(not claim.authorized for claim in claims):
        consequential = [
            reason
            for reason in consequential
            if reason
            not in {
                "unowned_stateful_world_assertion",
                "proposition_authority",
                "unauthorized_consequential_residual",
            }
        ]
    if consequential:
        claims.append(_claim(text, reasons=consequential, relation_kind=REL_PREDICATE))

    if not claims:
        legacy = _classify_narrated_fact_legacy(
            text,
            decision=decision,
            authored_corpus=authored_corpus,
            response_text=response_text or text,
        )
        if legacy is not None:
            relation_kind = _row_relation_kind({"semantic_identity": legacy.semantic_identity})
            claims.append(
                _claim(
                    text,
                    reasons=legacy.reason_codes,
                    relation_kind=relation_kind,
                    provenance=legacy.provenance,
                    authority=legacy.authority,
                    epistemic_status=str(legacy.semantic_identity.get("epistemic_status") or ""),
                    persistence=legacy.persistence,
                    authorized=legacy.authorized,
                    semantic_identity=legacy.semantic_identity,
                    source_ref=legacy.source_ref,
                )
            )
    return claims


def classify_narrated_fact(
    sentence: str,
    *,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
    response_text: str = "",
) -> GMProposedFact | None:
    claims = audit_narrated_claims(
        sentence,
        decision=decision,
        authored_corpus=authored_corpus,
        response_text=response_text,
    )
    if not claims:
        return None
    bad = [claim for claim in claims if not claim.authorized]
    if bad:
        reasons: list[str] = []
        for claim in bad:
            reasons.extend(claim.reason_codes)
        return _unauthorized_fact(_clean(sentence, limit=600), reasons or ["unauthorized_claim_residual"])
    primary = claims[0]
    return GMProposedFact(
        text=_clean(sentence, limit=600),
        provenance=primary.provenance,
        consequence="consequential" if primary.authority == AUTH_WORLD else "epistemic" if primary.relation_kind == REL_EPISTEMIC_STATUS else "low",
        authorized=True,
        reason_codes=primary.reason_codes,
        authority=primary.authority,
        persistence=primary.persistence,
        source_ref=primary.source_ref,
        outcome_classification=OUTCOME_ESTABLISHED if primary.authority == AUTH_WORLD else OUTCOME_EPISTEMIC,
        semantic_identity=dict(primary.semantic_identity),
    )


def audit_narration_against_decision(
    text: str | None,
    *,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
) -> dict[str, Any]:
    rows: list[GMProposedFact] = []
    claim_rows: list[NarratedClaim] = []
    violations: list[dict[str, Any]] = []
    full = text or ""
    for sentence in _sentences(full):
        claims = audit_narrated_claims(
            sentence,
            decision=decision,
            authored_corpus=authored_corpus,
            response_text=full,
        )
        claim_rows.extend(claims)
        fact = classify_narrated_fact(
            sentence,
            decision=decision,
            authored_corpus=authored_corpus,
            response_text=full,
        )
        if fact is None:
            continue
        rows.append(fact)
        if not fact.authorized:
            violations.append(fact.as_dict())
    obligations = _executable_obligations(decision)
    if (
        isinstance(obligations.get("supporting"), list)
        and len((full or "").split()) >= 8
        and not narration_acknowledges_supporting(full, obligations)
    ):
        violations.append(
            _unauthorized_fact(full, ["supporting_obligation_unacknowledged"]).as_dict()
        )
    return {
        "decision_id": str((decision or {}).get("contract_id") or ""),
        "hard_valid": not violations,
        "violations": violations,
        "proposed_facts": [row.as_dict() for row in rows],
        "claim_results": [row.as_dict() for row in claim_rows],
    }


def _merged_raw_premise_ids(raw: Mapping[str, Any], identity: Mapping[str, Any]) -> list[str]:
    ids = _id_list(raw.get("premise_claim_ids"))
    for item in _id_list(identity.get("premise_claim_ids")):
        if item not in ids:
            ids.append(item)
    return ids


def _normalized_content(text: str) -> set[str]:
    out: set[str] = set()
    for token in _content_tokens(text):
        out.add(token)
        if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
            out.add(token[:-1])
    return out


def _premise_terms(text: str) -> set[str]:
    return _normalized_content(text) - _EPISTEMIC_BOILERPLATE


def _premise_is_established(row: Mapping[str, Any]) -> bool:
    """A premise's own ceiling. Parent uncertainty does not raise it."""
    if row.get("provisional_declaration"):
        return False
    provenance = str(row.get("provenance") or row.get("provenance_requested") or "")
    if provenance in _BELOW_CEILING_PROVENANCE:
        return False
    status = str(row.get("epistemic_status") or "")
    identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
    identity_status = str(identity.get("epistemic_status") or "")
    if status in {STATUS_HYPOTHESIS, STATUS_POSSIBLE, STATUS_INFERRED, "hypothetical"}:
        return False
    if identity_status in {STATUS_HYPOTHESIS, STATUS_POSSIBLE, STATUS_INFERRED, "hypothetical"}:
        return False
    if str(row.get("authority") or "") == AUTH_WORLD:
        return True
    return status == STATUS_ESTABLISHED and provenance in {PROVENANCE_AUTHORITATIVE, "authored_world_fact"}


def _stamp_premise_ids(payload: dict[str, Any], premise_ids: Sequence[str]) -> dict[str, Any]:
    ids = _id_list(premise_ids)
    payload["premise_claim_ids"] = ids
    identity = payload.get("semantic_identity")
    if isinstance(identity, dict):
        identity["premise_claim_ids"] = list(ids)
    return payload


def _merged_premise_ids(declared: DeclaredRealizationClaim, match: Mapping[str, Any]) -> list[str]:
    ids = _id_list(declared.premise_claim_ids)
    for item in _id_list(match.get("premise_claim_ids")):
        if item not in ids:
            ids.append(item)
    for item in _id_list(declared.semantic_identity.get("premise_claim_ids") if isinstance(declared.semantic_identity, Mapping) else None):
        if item not in ids:
            ids.append(item)
    match_identity = match.get("semantic_identity") if isinstance(match.get("semantic_identity"), Mapping) else {}
    for item in _id_list(match_identity.get("premise_claim_ids")):
        if item not in ids:
            ids.append(item)
    return ids


def _declaration_is_epistemic_parent(declared: DeclaredRealizationClaim, match: Mapping[str, Any]) -> bool:
    role = str(match.get("realization_role") or declared.realization_role or "")
    if role == ROLE_MUST_PRESERVE_UNCERTAINTY:
        return True
    relation = str(declared.relation_kind or match.get("relation_kind") or "")
    status = str(declared.epistemic_status or match.get("epistemic_status") or "")
    if relation == REL_EPISTEMIC_STATUS and status == STATUS_UNRESOLVED:
        return True
    return bool(_EPISTEMIC_PARENT_REALIZATION_RE.search(declared.text or ""))


def _row_is_epistemic_parent(row: Mapping[str, Any]) -> bool:
    if str(row.get("realization_role") or "") == ROLE_MUST_PRESERVE_UNCERTAINTY:
        return True
    relation = str(row.get("relation_kind") or "")
    status = str(row.get("epistemic_status") or "")
    if relation == REL_EPISTEMIC_STATUS and status == STATUS_UNRESOLVED:
        return True
    return bool(_EPISTEMIC_PARENT_REALIZATION_RE.search(str(row.get("text") or "")))


def _premise_catalog(
    decision: Mapping[str, Any] | None,
    declared_rows: Sequence[DeclaredRealizationClaim],
) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for row in ((decision or {}).get("realization_claims") or []):
        if not isinstance(row, Mapping):
            continue
        claim_id = str(row.get("claim_id") or "").strip()
        if claim_id:
            catalog[claim_id] = dict(row)
    for declared in declared_rows:
        if declared.declaration_id in catalog:
            continue
        catalog[declared.declaration_id] = {
            "claim_id": declared.declaration_id,
            "text": declared.text,
            "provenance": declared.provenance_requested,
            "epistemic_status": declared.epistemic_status,
            "authority": AUTH_UNAUTHORIZED,
            "semantic_identity": dict(declared.semantic_identity),
            "premise_claim_ids": list(declared.premise_claim_ids),
            "provisional_declaration": True,
        }
    return catalog


def _residual_embedded_tokens(text: str, catalog: Mapping[str, Mapping[str, Any]]) -> set[str]:
    tokens = _premise_terms(text) - _EPISTEMIC_FRAME_NOUNS
    established: set[str] = set()
    for row in catalog.values():
        if not _premise_is_established(row):
            continue
        established |= _normalized_content(str(row.get("text") or ""))
        identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
        for key in ("subject", "value"):
            established |= _normalized_content(str(identity.get(key) or ""))
    return {token for token in tokens if token not in established}


def _conditional_scopes_premise(sentence: str, premise_terms: set[str]) -> bool:
    marker = _CONDITIONAL_MARKER_RE.search(sentence or "")
    if not marker:
        return False
    positions: list[int] = []
    low = sentence.lower()
    for term in premise_terms:
        found = re.search(rf"\b{re.escape(term)}\b", low)
        if found:
            positions.append(found.start())
    if not positions:
        return False
    return marker.start() < min(positions)


def _accommodates_premise_as_fact(text: str, premise_text: str) -> bool:
    """True when an uncertainty sentence treats a below-ceiling premise as given."""
    terms = _premise_terms(premise_text)
    if not terms:
        return False
    needed = 1 if len(terms) == 1 else 2
    for sentence in _sentences(text) or ([text] if text else []):
        if not _EPISTEMIC_PARENT_REALIZATION_RE.search(sentence or ""):
            continue
        overlap = {term for term in terms if term in _normalized_content(sentence)}
        if len(overlap) < needed:
            continue
        if _conditional_scopes_premise(sentence, overlap):
            continue
        return True
    return False


def _embedded_premise_reasons(
    declared: DeclaredRealizationClaim,
    match: Mapping[str, Any],
    catalog: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    if not _declaration_is_epistemic_parent(declared, match):
        return []
    premise_ids = _merged_premise_ids(declared, match)
    if any(premise_id not in catalog for premise_id in premise_ids):
        return ["premise_claim_unresolved"]
    linked = [catalog[premise_id] for premise_id in premise_ids]
    covered: set[str] = set()
    for row in linked:
        covered |= _premise_terms(str(row.get("text") or ""))
    if _residual_embedded_tokens(declared.text, catalog) - covered:
        return ["embedded_premise_unlinked"]
    for row in linked:
        if _premise_is_established(row):
            continue
        if _accommodates_premise_as_fact(declared.text, str(row.get("text") or "")):
            return ["premise_ceiling_exceeded"]
    return []


def _narration_premise_ceiling_violations(
    narration: str | None,
    decision: Mapping[str, Any] | None,
    accepted_claims: Sequence[Mapping[str, Any]] | None,
    declared_claims: Sequence[Mapping[str, Any] | DeclaredRealizationClaim] | None = None,
) -> list[dict[str, Any]]:
    parsed: list[DeclaredRealizationClaim] = []
    if isinstance(declared_claims, Sequence) and not isinstance(declared_claims, (str, bytes)):
        for index, item in enumerate(declared_claims):
            if isinstance(item, DeclaredRealizationClaim):
                parsed.append(item)
            elif isinstance(item, Mapping):
                row = declared_claim_from_mapping(item, index)
                if row is not None:
                    parsed.append(row)
    catalog = _premise_catalog(decision, parsed)
    parents: list[Mapping[str, Any]] = [
        row for row in catalog.values() if _row_is_epistemic_parent(row)
    ]
    parents.extend(row for row in (accepted_claims or []) if isinstance(row, Mapping) and _row_is_epistemic_parent(row))
    seen: set[str] = set()
    violations: list[dict[str, Any]] = []
    for parent in parents:
        for premise_id in _id_list(parent.get("premise_claim_ids")):
            premise = catalog.get(premise_id)
            if not isinstance(premise, Mapping) or _premise_is_established(premise):
                continue
            if premise_id in seen:
                continue
            if not _accommodates_premise_as_fact(narration or "", str(premise.get("text") or "")):
                continue
            seen.add(premise_id)
            violations.append(
                _claim(
                    str(premise.get("text") or narration or ""),
                    reasons=["premise_ceiling_exceeded"],
                    relation_kind=REL_EPISTEMIC_STATUS,
                    provenance=str(premise.get("provenance") or PROVENANCE_PLAYER_HYPOTHESIS),
                    authority=AUTH_UNAUTHORIZED,
                    epistemic_status=str(premise.get("epistemic_status") or STATUS_HYPOTHESIS),
                    authorized=False,
                ).as_dict()
            )
    return violations


def declared_claim_from_mapping(raw: Mapping[str, Any], index: int = 0) -> DeclaredRealizationClaim | None:
    """Coerce one model declaration. Malformed rows are rejected by the caller."""
    if not isinstance(raw, Mapping):
        return None
    mode = str(raw.get("declaration_mode") or raw.get("mode") or DECLARATION_MODE_REALIZE).strip().lower()
    if mode not in {DECLARATION_MODE_REALIZE, DECLARATION_MODE_PROPOSE}:
        mode = ""
    identity = raw.get("semantic_identity")
    if not isinstance(identity, Mapping):
        identity = {}
    relation_kind = str(raw.get("relation_kind") or identity.get("relation_kind") or "").strip()
    if not relation_kind:
        relation_kind = _row_relation_kind({"semantic_identity": identity})
    epistemic = str(raw.get("epistemic_status") or identity.get("epistemic_status") or "").strip()
    if not epistemic:
        epistemic = STATUS_UNRESOLVED
    declaration_id = str(raw.get("declaration_id") or raw.get("id") or "").strip() or f"d{index + 1}"
    return DeclaredRealizationClaim(
        declaration_id=declaration_id,
        declaration_mode=mode,
        semantic_identity=dict(identity),
        provenance_requested=str(raw.get("provenance_requested") or raw.get("provenance") or PROVENANCE_GENERATED_PROPOSAL).strip(),
        epistemic_status=epistemic,
        modality=str(raw.get("modality") or identity.get("modality") or "").strip(),
        realization_role=str(raw.get("realization_role") or raw.get("role") or ROLE_MAY_STATE).strip(),
        relation_kind=relation_kind,
        source_claim_id=str(raw.get("source_claim_id") or "").strip(),
        text=_clean(raw.get("text") or raw.get("claim_text"), limit=600),
        premise_claim_ids=_merged_raw_premise_ids(raw, identity),
    )


def realization_envelope_from_mapping(raw: Mapping[str, Any] | None) -> GMRealizationEnvelope | None:
    """Parse the structured one-call envelope.

    A prose-only response is intentionally represented as ``None`` by callers;
    this function handles only actual structured envelopes.
    """
    if not isinstance(raw, Mapping) or "declared_claims" not in raw:
        return None
    claims_raw = raw.get("declared_claims")
    narration = raw.get("narration") if "narration" in raw else raw.get("player_facing_text")
    if not isinstance(claims_raw, list) or not isinstance(narration, str) or not narration.strip():
        return None
    claims: list[DeclaredRealizationClaim] = []
    for index, item in enumerate(claims_raw):
        if not isinstance(item, Mapping):
            return None
        claim = declared_claim_from_mapping(item, index)
        if claim is None or not claim.declaration_mode:
            return None
        claims.append(claim)
    return GMRealizationEnvelope(declared_claims=claims, narration=narration.strip())


def _declared_identity_matches_realization(
    declared: DeclaredRealizationClaim,
    claim: Mapping[str, Any],
) -> bool:
    if declared.source_claim_id and declared.source_claim_id == str(claim.get("claim_id") or ""):
        return True
    identity = claim.get("semantic_identity") if isinstance(claim.get("semantic_identity"), Mapping) else {}
    if identity and declared.semantic_identity:
        text = " ".join(
            part
            for part in (declared.text, " ".join(str(v) for v in declared.semantic_identity.values() if isinstance(v, str)))
            if part
        )
        if text and _semantic_identity_matches(text, identity):
            return True
        if _identity_compatible(declared.semantic_identity, identity):
            return True
    claim_text = _clean(claim.get("text"), limit=600)
    if declared.text and claim_text and _norm_phrase(declared.text) == _norm_phrase(claim_text):
        return True
    return bool(declared.text and claim_text and (_empty_identity_covers(declared.text, claim_text) or _empty_identity_covers(claim_text, declared.text)))


def _identity_compatible(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if not left or not right:
        return False
    left_tokens = _content_tokens(" ".join(str(v) for v in left.values() if not isinstance(v, (dict, list))))
    right_tokens = _content_tokens(" ".join(str(v) for v in right.values() if not isinstance(v, (dict, list))))
    if left_tokens and right_tokens and len(left_tokens & right_tokens) >= min(len(left_tokens), len(right_tokens), 2):
        return True
    for key in ("subject", "relation", "value", "kind"):
        lv = _norm_phrase(left.get(key))
        rv = _norm_phrase(right.get(key))
        if lv and rv and (lv == rv or lv in rv or rv in lv):
            return True
    return False


def _modality_rank(value: str | None) -> int:
    low = str(value or "").strip().lower()
    if low in {"", STATUS_UNRESOLVED, "unknown", "unsettled"}:
        return 0
    if low in {"hypothetical", STATUS_HYPOTHESIS, "possible", "may", "might", "could", STATUS_POSSIBLE}:
        return 1
    if low in {"inferred", "likely", "probable"}:
        return 2
    if low in {"established", "certain", "world_truth", "true"}:
        return 3
    return 1


def _claim_modality_rank(row: Mapping[str, Any]) -> int:
    identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
    return max(
        _modality_rank(row.get("modality")),
        _modality_rank(row.get("epistemic_status")),
        _modality_rank(identity.get("modality")),
        _modality_rank(identity.get("epistemic_status")),
        3 if str(row.get("authority") or "") == AUTH_WORLD else 0,
    )


def _declaration_modality_rank(declared: DeclaredRealizationClaim) -> int:
    return max(
        _modality_rank(declared.modality),
        _modality_rank(declared.epistemic_status),
        _modality_rank(declared.semantic_identity.get("modality")),
        _modality_rank(declared.semantic_identity.get("epistemic_status")),
    )


def _realization_claim_to_narrated_claim(row: Mapping[str, Any], declared: DeclaredRealizationClaim) -> dict[str, Any]:
    identity = dict(row.get("semantic_identity") or {}) if isinstance(row.get("semantic_identity"), Mapping) else {}
    text = declared.text or _clean(row.get("text"), limit=600)
    payload = NarratedClaim(
        text=text,
        semantic_identity=identity,
        provenance=str(row.get("provenance") or PROVENANCE_AUTHORITATIVE),
        authority=str(row.get("authority") or AUTH_WORLD),
        epistemic_status=str(row.get("epistemic_status") or identity.get("epistemic_status") or STATUS_ESTABLISHED),
        relation_kind=str(row.get("relation_kind") or _row_relation_kind({"semantic_identity": identity})),
        persistence=str(row.get("persistence") or PERSIST_NONE),
        authorized=True,
        source_ref=str(row.get("source_ref") or row.get("claim_id") or ""),
        reason_codes=["accepted_declared_realization"],
    ).as_dict()
    return _stamp_premise_ids(payload, _merged_premise_ids(declared, row))


def _proposal_is_bounded_inference(declared: DeclaredRealizationClaim, decision: Mapping[str, Any] | None) -> tuple[bool, list[str]]:
    if not _decision_allows_inference(decision):
        return False, ["proposal_inference_not_permitted"]
    text = declared.text
    if str(declared.provenance_requested or "") in {PROVENANCE_AUTHORITATIVE, "world_truth", AUTH_WORLD}:
        return False, ["proposal_requested_world_truth"]
    relation_low = str(declared.relation_kind or declared.semantic_identity.get("relation") or "").lower()
    if relation_low in {REL_GAMEPLAY_LEAD, "lead", "gameplay_lead", "actor", "event_actor", "time", "event_time", "history", "state_mutation", "negative_evidence", "absence"}:
        return False, [f"proposal_forbidden_class:{relation_low}"]
    if _NEGATIVE_EVIDENCE_RE.search(text) or _SPECIFIC_LEAD_RE.search(text):
        return False, ["proposal_forbidden_consequential_class"]
    if _declaration_modality_rank(declared) >= 3:
        return False, ["proposal_modality_strengthening"]
    # A hedge licenses the inference operation. It does not license the
    # complement, or cause, history, actor, or certainty content in the same proposal.
    residual = _hedge_does_not_authorize(text, decision)
    if residual:
        return False, residual
    return True, []


def _accepted_proposal_claim(declared: DeclaredRealizationClaim) -> dict[str, Any]:
    identity = dict(declared.semantic_identity)
    identity.setdefault("modality", declared.modality or STATUS_POSSIBLE)
    identity.setdefault("epistemic_status", declared.epistemic_status or STATUS_INFERRED)
    relation_kind = declared.relation_kind or _row_relation_kind({"semantic_identity": identity})
    payload = NarratedClaim(
        text=declared.text,
        semantic_identity=identity,
        provenance=PROVENANCE_GM_INFERENCE,
        authority=AUTH_INFERENCE,
        epistemic_status=STATUS_INFERRED,
        relation_kind=relation_kind,
        persistence=PERSIST_NONE,
        authorized=True,
        source_ref=f"declared_claim:{declared.declaration_id}",
        reason_codes=["accepted_bounded_declared_inference"],
    ).as_dict()
    return _stamp_premise_ids(payload, list(declared.premise_claim_ids))


def validate_declared_claims_against_decision(
    declared_claims: Sequence[Mapping[str, Any] | DeclaredRealizationClaim] | None,
    *,
    decision: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate model-declared consequential semantics before prose authority.

    Declarations expose intent; they do not grant authority. Accepted output rows
    are the only declaration-derived claims eligible for temporal persistence.
    """
    if declared_claims is None:
        return {
            "schema_version": STRUCTURED_ENVELOPE_VERSION,
            "structured_contract_present": False,
            "hard_valid": True,
            "accepted_claims": [],
            "rejected_claims": [],
            "violations": [],
        }
    if not isinstance(declared_claims, Sequence) or isinstance(declared_claims, (str, bytes)):
        return {
            "schema_version": STRUCTURED_ENVELOPE_VERSION,
            "structured_contract_present": True,
            "hard_valid": False,
            "accepted_claims": [],
            "rejected_claims": [],
            "violations": [{"reason_codes": ["malformed_declared_claims"], "text": ""}],
        }
    realization_claims = [
        row for row in ((decision or {}).get("realization_claims") or []) if isinstance(row, Mapping)
    ]
    parsed_declared = [
        item if isinstance(item, DeclaredRealizationClaim) else declared_claim_from_mapping(item, index)
        for index, item in enumerate(declared_claims)
        if isinstance(item, (DeclaredRealizationClaim, Mapping))
    ]
    catalog = _premise_catalog(decision, [row for row in parsed_declared if isinstance(row, DeclaredRealizationClaim)])
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for index, item in enumerate(declared_claims):
        declared = item if isinstance(item, DeclaredRealizationClaim) else declared_claim_from_mapping(item, index) if isinstance(item, Mapping) else None
        if declared is None or not declared.declaration_mode:
            row = {"text": "", "reason_codes": ["malformed_declared_claim"], "authorized": False}
            rejected.append(row)
            violations.append(row)
            continue
        if declared.declaration_mode == DECLARATION_MODE_PROPOSE:
            allowed, reasons = _proposal_is_bounded_inference(declared, decision)
            premise_reasons = _embedded_premise_reasons(
                declared,
                {
                    "text": declared.text,
                    "relation_kind": declared.relation_kind,
                    "epistemic_status": declared.epistemic_status,
                    "premise_claim_ids": list(declared.premise_claim_ids),
                    "realization_role": declared.realization_role,
                },
                catalog,
            ) if allowed else []
            if allowed and not premise_reasons:
                accepted.append(_accepted_proposal_claim(declared))
            else:
                row = {
                    **declared.as_dict(),
                    "authorized": False,
                    "authority": AUTH_UNAUTHORIZED,
                    "reason_codes": premise_reasons or reasons or ["unauthorized_declared_proposal"],
                }
                rejected.append(row)
                violations.append(row)
            continue
        matches = [claim for claim in realization_claims if _declared_identity_matches_realization(declared, claim)]
        if not matches:
            row = {
                **declared.as_dict(),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": ["unauthorized_declared_claim"],
            }
            rejected.append(row)
            violations.append(row)
            continue
        match = matches[0]
        if _declaration_modality_rank(declared) > _claim_modality_rank(match):
            row = {
                **declared.as_dict(),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": ["modality_strengthening"],
                "matched_claim_id": match.get("claim_id"),
            }
            rejected.append(row)
            violations.append(row)
            continue
        if (
            str(match.get("provenance") or "") == PROVENANCE_PLAYER_HYPOTHESIS
            and _declaration_modality_rank(declared) >= 3
        ):
            row = {
                **declared.as_dict(),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": ["player_hypothesis_self_promotion"],
                "matched_claim_id": match.get("claim_id"),
            }
            rejected.append(row)
            violations.append(row)
            continue
        premise_reasons = _embedded_premise_reasons(declared, match, catalog)
        if premise_reasons:
            row = {
                **declared.as_dict(),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": premise_reasons,
                "matched_claim_id": match.get("claim_id"),
            }
            rejected.append(row)
            violations.append(row)
            continue
        accepted.append(_realization_claim_to_narrated_claim(match, declared))
    return {
        "schema_version": STRUCTURED_ENVELOPE_VERSION,
        "structured_contract_present": True,
        "hard_valid": not violations,
        "accepted_claims": accepted,
        "rejected_claims": rejected,
        "violations": violations,
    }


def _decision_with_accepted_declarations(
    decision: Mapping[str, Any] | None,
    accepted_claims: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    out = dict(decision or {})
    if not accepted_claims:
        return out
    facts = [dict(row) for row in out.get("proposed_facts") or [] if isinstance(row, Mapping)]
    existing = {
        (
            _norm_phrase(row.get("text")),
            str(row.get("provenance") or ""),
            str(row.get("authority") or ""),
        )
        for row in facts
    }
    for claim in accepted_claims:
        if not isinstance(claim, Mapping):
            continue
        key = (_norm_phrase(claim.get("text")), str(claim.get("provenance") or ""), str(claim.get("authority") or ""))
        if key in existing:
            continue
        facts.append(
            {
                "text": _clean(claim.get("text"), limit=600),
                "provenance": claim.get("provenance"),
                "consequence": "consequential",
                "authorized": True,
                "reason_codes": list(claim.get("reason_codes") or []),
                "authority": claim.get("authority"),
                "persistence": claim.get("persistence") or PERSIST_NONE,
                "source_ref": claim.get("source_ref") or "accepted_declared_claim",
                "outcome_classification": OUTCOME_EPISTEMIC if claim.get("authority") == AUTH_INFERENCE else OUTCOME_ESTABLISHED,
                "semantic_identity": dict(claim.get("semantic_identity") or {}) if isinstance(claim.get("semantic_identity"), Mapping) else {},
                "relation_kind": claim.get("relation_kind"),
            }
        )
        existing.add(key)
    out["proposed_facts"] = facts
    return out


def _undeclared_consequential_violations(
    narration_audit: Mapping[str, Any],
    accepted_claims: Sequence[Mapping[str, Any]] | None,
    narration: str | None = None,
    decision: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    accepted_texts = {
        _norm_phrase(row.get("text"))
        for row in (accepted_claims or [])
        if isinstance(row, Mapping) and _norm_phrase(row.get("text"))
    }
    violations: list[dict[str, Any]] = []
    for row in narration_audit.get("claim_results") or []:
        if not isinstance(row, Mapping) or row.get("authorized") is not True:
            continue
        text = _clean(row.get("text"), limit=600)
        if not text or _norm_phrase(text) in accepted_texts:
            continue
        authority = str(row.get("authority") or "")
        relation_kind = str(row.get("relation_kind") or "")
        consequential = []
        consequential.extend(_unlicensed_consequential_reasons(text, decision))
        consequential.extend(_structured_consequential_reasons(text))
        if _NEGATIVE_EVIDENCE_RE.search(text):
            consequential.append("negative_evidence")
        if _SPECIFIC_LEAD_RE.search(text):
            consequential.append("specific_gameplay_lead")
        if _UNDECLARED_CAUSAL_AGENT_RE.search(text):
            consequential.append("undeclared_causal_agent")
        existence_only = _existence_mention(row)
        restates_authorized = any(
            _proposition_restates_statement(text, statement) for statement in _authorized_statement_texts(decision)
        )
        if existence_only:
            if _EXISTENCE_ACTION_RE.search(_outside_quotes(text)):
                consequential.append("unauthorized_npc_action")
        elif restates_authorized and authority == AUTH_WORLD:
            pass
        elif authority == AUTH_WORLD or relation_kind in {REL_CAUSAL, REL_EVIDENTIAL, REL_GAMEPLAY_LEAD}:
            consequential.append("authorized_consequential_claim")
        if authority == AUTH_CLAIM and _STATEFUL_ASSERTION_RE.search(text) and not restates_authorized:
            consequential.append("consequential_npc_claim")
        if _IGNORANCE_SEAL_RE.search(text) and not restates_authorized:
            consequential.append("ignorance_not_authorized_answer")
        if not consequential:
            continue
        violations.append(
            {
                **dict(row),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": ["undeclared_consequential_claim"],
            }
        )
    for sentence in _sentences(narration):
        norm = _norm_phrase(sentence)
        if not norm or any(text and text in norm for text in accepted_texts):
            continue
        reasons: list[str] = []
        if _UNDECLARED_CAUSAL_AGENT_RE.search(sentence):
            reasons.append("undeclared_causal_agent")
        if _NEGATIVE_EVIDENCE_RE.search(sentence):
            reasons.append("undeclared_negative_evidence")
        if _SPECIFIC_LEAD_RE.search(sentence):
            reasons.append("undeclared_specific_gameplay_lead")
        if _IGNORANCE_SEAL_RE.search(sentence) and not any(
            _proposition_restates_statement(sentence, statement)
            for statement in _authorized_statement_texts(decision)
        ):
            reasons.append("ignorance_not_authorized_answer")
        if not reasons:
            continue
        violations.append(
            _claim(
                sentence,
                reasons=["undeclared_consequential_claim", *reasons],
                relation_kind=REL_PREDICATE,
            ).as_dict()
        )
    return violations


def audit_realization_envelope_against_decision(
    *,
    narration: str | None,
    declared_claims: Sequence[Mapping[str, Any] | DeclaredRealizationClaim] | None,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
) -> dict[str, Any]:
    declaration = validate_declared_claims_against_decision(declared_claims, decision=decision)
    if not declaration.get("hard_valid"):
        return {
            "decision_id": str((decision or {}).get("contract_id") or ""),
            "hard_valid": False,
            "declaration_validation": declaration,
            "narration_validation": None,
            "violations": list(declaration.get("violations") or []),
            "claim_results": list(declaration.get("accepted_claims") or []) + list(declaration.get("rejected_claims") or []),
            "accepted_realized_claims": [],
        }
    effective_decision = _decision_with_accepted_declarations(decision, declaration.get("accepted_claims"))
    narration_audit = audit_narration_against_decision(
        narration,
        decision=effective_decision,
        authored_corpus=authored_corpus,
    )
    undeclared = _undeclared_consequential_violations(
        narration_audit,
        declaration.get("accepted_claims") if isinstance(declaration, Mapping) else [],
        narration=narration,
        decision=effective_decision,
    )
    premise_violations = _narration_premise_ceiling_violations(
        narration,
        decision,
        declaration.get("accepted_claims") if isinstance(declaration, Mapping) else [],
        declared_claims,
    )
    narration_valid = bool(narration_audit.get("hard_valid")) and not undeclared and not premise_violations
    return {
        "decision_id": str((decision or {}).get("contract_id") or ""),
        "hard_valid": narration_valid,
        "declaration_validation": declaration,
        "narration_validation": narration_audit,
        "violations": list(narration_audit.get("violations") or []) + undeclared + premise_violations,
        "proposed_facts": list(narration_audit.get("proposed_facts") or []),
        "claim_results": list(declaration.get("accepted_claims") or []) + list(narration_audit.get("claim_results") or []) + undeclared + premise_violations,
        "accepted_realized_claims": [
            row for row in (declaration.get("accepted_claims") or []) if isinstance(row, Mapping)
        ],
    }


def audit_recursive_premise_consumption(
    *,
    session: Mapping[str, Any] | None,
    text: str | None,
) -> dict[str, Any]:
    """Detect player/prose reuse of rejected generated proposals."""
    ledger = session.get("bounded_improvisation") if isinstance(session, Mapping) else None
    rejected = ledger.get("rejected") if isinstance(ledger, Mapping) else None
    raw = _clean(text, limit=1000).lower()
    raw_norm = " ".join(re.findall(r"[a-z0-9']+", raw))
    raw_tokens = set(re.findall(r"[a-z0-9']+", raw))
    hits: list[dict[str, Any]] = []
    if isinstance(rejected, Sequence):
        for row in rejected:
            if not isinstance(row, Mapping):
                continue
            prop = row.get("proposal") if isinstance(row.get("proposal"), Mapping) else row
            content = _clean((prop or {}).get("content"), limit=300).lower() if isinstance(prop, Mapping) else ""
            content_norm = " ".join(re.findall(r"[a-z0-9']+", content))
            content_tokens = {
                tok
                for tok in re.findall(r"[a-z0-9']+", content)
                if len(tok) >= 4 and tok not in {"that", "this", "with", "from", "tonight"}
            }
            if len(content_norm) >= 12 and (
                content_norm in raw_norm
                or (len(content_tokens) >= 3 and len(content_tokens & raw_tokens) >= max(3, len(content_tokens) - 1))
            ):
                hits.append({"content": content, "reason": "rejected_generated_proposal_reused"})
    return {"hard_valid": not hits, "violations": hits}


def ensure_temporal_provenance(session: dict[str, Any]) -> dict[str, Any]:
    """Small cross-turn provenance buckets for non-authoritative narration.

    This is not a transcript database and does not duplicate authored world
    state. Buckets are capped so repetition can be recognized without becoming
    a permanent ban or promotion source.
    """
    record = session.get(TEMPORAL_PROVENANCE_KEY)
    if not isinstance(record, dict):
        record = {}
        session[TEMPORAL_PROVENANCE_KEY] = record
    record.setdefault("version", TEMPORAL_PROVENANCE_VERSION)
    for key in ("gm_inferences", "player_hypotheses", "accepted_incidentals", "rejected_consequential"):
        if not isinstance(record.get(key), list):
            record[key] = []
    return record


def remember_temporal_claims(
    session: dict[str, Any] | None,
    *,
    claims: Sequence[Mapping[str, Any]] | None,
    scene_id: str | None = None,
    source_turn: int | None = None,
    cap: int = 24,
) -> dict[str, Any]:
    """Persist claim status without promoting it to world truth."""
    if not isinstance(session, dict):
        return {}
    record = ensure_temporal_provenance(session)
    sid = _clean(scene_id or session.get("active_scene_id"), limit=80)
    turn = source_turn if isinstance(source_turn, int) else session.get("turn_counter")
    for claim in claims or []:
        if not isinstance(claim, Mapping):
            continue
        authority = str(claim.get("authority") or "")
        provenance = str(claim.get("provenance") or "")
        authorized = bool(claim.get("authorized"))
        item = {
            "semantic_identity": dict(claim.get("semantic_identity") or {}) if isinstance(claim.get("semantic_identity"), Mapping) else {},
            "text": _clean(claim.get("text"), limit=300),
            "authority": authority,
            "provenance": provenance,
            "epistemic_status": str(claim.get("epistemic_status") or ""),
            "relation_kind": str(claim.get("relation_kind") or ""),
            "scene_id": sid or None,
            "source_turn": turn if isinstance(turn, int) else None,
        }
        if authorized and authority == AUTH_INCIDENTAL:
            bucket = "accepted_incidentals"
        elif authorized and provenance == PROVENANCE_GM_INFERENCE:
            bucket = "gm_inferences"
        elif authorized and provenance == PROVENANCE_PLAYER_HYPOTHESIS:
            bucket = "player_hypotheses"
        elif not authorized:
            item["reason_codes"] = list(claim.get("reason_codes") or [])
            bucket = "rejected_consequential"
        else:
            continue
        fingerprint = (
            _norm_phrase(item.get("text")),
            str(item.get("provenance") or ""),
            str(item.get("authority") or ""),
            item.get("source_turn"),
        )
        if any(
            (
                _norm_phrase(existing.get("text")),
                str(existing.get("provenance") or ""),
                str(existing.get("authority") or ""),
                existing.get("source_turn"),
            )
            == fingerprint
            for existing in record[bucket]
            if isinstance(existing, Mapping)
        ):
            continue
        record[bucket].append(item)
        if len(record[bucket]) > max(1, cap):
            del record[bucket][:-max(1, cap)]
    return record


_PLAYER_HYPOTHESIS_RE = re.compile(
    r"\b(?:if|assuming|suppose|supposing|let's say|lets say|maybe|perhaps)\b"
    r"|\b(?:so|since)\b[^.!?]{0,100}\b(?:caused|did|was|were|means?|happened|sabotag\w*)\b",
    re.IGNORECASE,
)


def player_hypothesis_claims(text: str | None) -> list[dict[str, Any]]:
    """Material player suppositions stay hypotheses; repetition is not promotion."""
    raw = _clean(text, limit=1000)
    if not raw or not _PLAYER_HYPOTHESIS_RE.search(raw):
        return []
    return [
        NarratedClaim(
            text=raw,
            semantic_identity={"relation_kind": REL_EPISTEMIC_STATUS, "epistemic_status": STATUS_HYPOTHESIS},
            provenance=PROVENANCE_PLAYER_HYPOTHESIS,
            authority=AUTH_OBSERVATION,
            epistemic_status=STATUS_HYPOTHESIS,
            relation_kind=REL_EPISTEMIC_STATUS,
            persistence=PERSIST_NONE,
            authorized=True,
            reason_codes=["player_hypothesis_not_world_truth"],
        ).as_dict()
    ]


def sealed_temporal_claims(
    gm: Mapping[str, Any] | None,
    *,
    player_text: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return accepted exact-seal claims and rejected discarded proposals."""
    from game.immutable_valid_response import accepted_record

    record = accepted_record(gm)
    if not isinstance(record, Mapping) or record.get("immutable") is not True:
        return [], []
    hard = record.get("hard_validation") if isinstance(record.get("hard_validation"), Mapping) else {}
    audit = hard.get("gm_resolution_decision_audit") if isinstance(hard, Mapping) else {}
    accepted = [
        dict(row)
        for row in (audit.get("claim_results") if isinstance(audit, Mapping) else []) or []
        if isinstance(row, Mapping) and row.get("authorized") is True
    ]
    accepted.extend(player_hypothesis_claims(player_text))
    rejected: list[dict[str, Any]] = []
    metadata = gm.get("metadata") if isinstance(gm, Mapping) and isinstance(gm.get("metadata"), Mapping) else {}
    review = metadata.get("decision_review") if isinstance(metadata, Mapping) else {}
    for key in ("attempt_1", "attempt_2"):
        attempt = review.get(key) if isinstance(review, Mapping) and isinstance(review.get(key), Mapping) else {}
        attempt_audit = attempt.get("gm_resolution_decision_audit") if isinstance(attempt, Mapping) else {}
        for row in (attempt_audit.get("claim_results") if isinstance(attempt_audit, Mapping) else []) or []:
            if isinstance(row, Mapping) and row.get("authorized") is False:
                rejected.append(dict(row))
    return accepted, rejected


def prompt_projection_for_temporal_provenance(
    session: Mapping[str, Any] | None,
    *,
    scene_id: str | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    record = session.get(TEMPORAL_PROVENANCE_KEY) if isinstance(session, Mapping) else None
    if not isinstance(record, Mapping):
        return {"version": TEMPORAL_PROVENANCE_VERSION, "buckets": {}}
    active_scene = (session or {}).get("active_scene_id") if isinstance(session, Mapping) else ""
    sid = _clean(scene_id or active_scene, limit=80)
    buckets: dict[str, list[dict[str, Any]]] = {}
    for key in ("gm_inferences", "player_hypotheses", "accepted_incidentals", "rejected_consequential"):
        rows = [dict(row) for row in record.get(key) or [] if isinstance(row, Mapping)]
        if sid:
            rows = [row for row in rows if not row.get("scene_id") or row.get("scene_id") == sid]
        buckets[key] = rows[-max(1, limit):]
    return {
        "version": TEMPORAL_PROVENANCE_VERSION,
        "buckets": buckets,
        "instructions": [
            "Raw transcript continuity is not authority.",
            "GM inferences and player hypotheses remain non-world-truth until an establish act appears.",
            "Rejected consequential claims may be retried only if a later authoritative decision establishes them.",
        ],
    }


def decision_auditor_trace(text: str | None, *, decision: Mapping[str, Any] | None, authored_corpus: str = "") -> dict[str, Any]:
    basis = f"{(decision or {}).get('contract_id') or ''}|{text or ''}"
    return {
        "id": "gmrd_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12],
        "narration": audit_narration_against_decision(text, decision=decision, authored_corpus=authored_corpus),
    }


def sentences_without_decision_violations(text: str | None, audit: Mapping[str, Any] | None) -> str:
    """Drop only the sentences a decision audit rejected. Empty when nothing safe remains."""
    violations = (audit or {}).get("violations") if isinstance(audit, Mapping) else None
    if not isinstance(violations, list) or not violations:
        return ""
    bad = {_norm_phrase(row.get("text")) for row in violations if isinstance(row, Mapping)}
    source = _sentences(text)
    kept = [sentence for sentence in source if _norm_phrase(sentence) not in bad]
    if not kept or len(kept) == len(source):
        return ""
    return " ".join(kept)


def structural_narration_units(text: str | None) -> list[str]:
    """Sentence-like units that never split the interior of quoted speech."""
    raw = str(text or "").strip()
    if not raw:
        return []
    units: list[str] = []
    start = 0
    straight_open = False
    curly_open = False
    for index, char in enumerate(raw):
        if char == '"':
            straight_open = not straight_open
        elif char == "“":
            curly_open = True
        elif char == "”":
            curly_open = False
        if char not in ".!?" or straight_open or curly_open:
            continue
        next_char = raw[index + 1 : index + 2]
        if next_char and not next_char.isspace():
            continue
        unit = _clean(raw[start : index + 1], limit=1200)
        if unit:
            units.append(unit)
        start = index + 1
    remainder = _clean(raw[start:], limit=1200)
    if remainder:
        units.append(remainder)
    return units


def preservation_structure_valid(text: str | None) -> bool:
    """Minimal integrity guard for deletion-based preservation."""
    raw = str(text or "").strip()
    if not raw:
        return False
    if raw.count('"') % 2:
        return False
    if raw.count("“") != raw.count("”"):
        return False
    if _ORPHAN_DIALOGUE_ATTRIBUTION_RE.search(raw) and not any(mark in raw for mark in ('"', "“", "”")):
        return False
    if re.search(r"(?:^|\s)[,;:]\s*$", raw) or raw.endswith((",", ";", ":")):
        return False
    return True


def narration_authority_fields(resolution: Mapping[str, Any] | None) -> dict[str, Any]:
    """The contract, decision, and answer recipe narration is allowed to see.

    The recipe is a projection of the decision. It is not an authority source.
    """
    from game.resolution_contract import generation_projection

    fields: dict[str, Any] = {}
    full_contract = contract_mapping_from_resolution(resolution if isinstance(resolution, Mapping) else None)
    contract = generation_projection(full_contract)
    full_decision = decision_from_resolution(resolution if isinstance(resolution, Mapping) else None)
    decision = prompt_decision_projection(full_decision)
    if contract:
        if full_contract.get("contract_id") and "contract_id" not in contract:
            contract = {**contract, "contract_id": full_contract.get("contract_id")}
        fields["resolution_contract"] = contract
    if decision:
        fields["gm_resolution_decision"] = decision
    recipe = build_decision_facing_answer_recipe(full_decision, full_contract)
    if recipe:
        fields["decision_facing_answer_recipe"] = recipe
    return fields


def compact_decision_for_prompt(decision: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(decision, Mapping) or not str(decision.get("contract_id") or "").strip():
        return None
    facts: list[dict[str, Any]] = []
    for row in decision.get("proposed_facts") or []:
        if not isinstance(row, Mapping):
            continue
        facts.append(
            {
                "text": row.get("text"),
                "authorized": bool(row.get("authorized")),
                "authority": row.get("authority"),
                "provenance": row.get("provenance"),
                "epistemic_status": row.get("epistemic_status"),
                "relation_kind": row.get("relation_kind"),
                "semantic_identity": row.get("semantic_identity") or {},
            }
        )
    return {
        "contract_id": decision.get("contract_id"),
        "outcome_classification": decision.get("outcome_classification"),
        "proposed_facts": facts,
        "realization_claims": [
            dict(row)
            for row in (decision.get("realization_claims") or [])
            if isinstance(row, Mapping)
        ],
        "narration_constraints": list(decision.get("narration_constraints") or []),
        "unresolved_qualifiers": list(decision.get("unresolved_qualifiers") or []),
        "answer_relations": list(decision.get("answer_relations") or []),
        "epistemic_acts": list(decision.get("epistemic_acts") or []),
        "permitted_state_mutations": list(decision.get("permitted_state_mutations") or []),
        "executable_obligations": dict(decision.get("executable_obligations") or {}),
    }


RECIPE_SCHEMA = "decision_facing_answer_recipe_v1"
PROVIDER_ENVELOPE_STRUCTURED = "structured_realization"
PROVIDER_ENVELOPE_NARRATION_ONLY = "narration_only"
NARRATION_ONLY_RESPONSE_SCHEMA = {"narration": "player-facing response"}
QUALIFIED_POSSIBILITIES_SCOPE = "qualified_possibilities_only"
_QUALIFIED_UNRESOLVED = ("cause", "actor", "time", "history")
_QUALIFIED_FORBIDDEN = (
    "exact_cause",
    "actor",
    "time",
    "history",
    "neglect",
    "harsh_conditions",
    "safety_status",
    "unseen_damage",
    "gameplay_lead",
    "evidential_establishment",
    "certainty_upgrade_to_established",
    "inference_as_authored_world_fact",
)

# Turn-local projection labels. They summarize the decision. They do not authorize facts.
OP_BOUNDED_INTERPRETATION = "bounded_interpretation"
OP_INCIDENTAL_DIALOGUE = "incidental_dialogue"
OP_PLAYER_HYPOTHESIS = "player_hypothesis_discussion"
OP_CONSEQUENTIAL_REALIZATION = "consequential_realization"
OP_DIRECT_OBSERVATION = "direct_observation"
OP_REFUSAL_OR_LIMIT = "refusal_or_limit"
OP_LISTED_CLAIMS = "listed_claim_realization"

DECL_OPTIONAL_BOUNDED_INFERENCE = "optional_bounded_inference"
DECL_REPLY_NOT_REQUIRED = "reply_not_required"
DECL_HYPOTHESIS_NOT_REQUIRED = "hypothesis_discussion_not_required"
DECL_REQUIRED_FOR_AUTHORIZED = "required_for_authorized_realization"
DECL_OBSERVATIONS_ONLY = "observations_only"
DECL_PROHIBITED = "declaration_prohibited"
DECL_LISTED_ONLY = "listed_claims_only"
DECL_NONE = "no_additional_declaration"

CEIL_INTERPRET_NOT_EXPLAIN = "interpret_observations_not_unauthorized_cause"
CEIL_TRANSIENT_DIALOGUE = "transient_dialogue_not_durable_fact"
CEIL_CONDITIONAL_HYPOTHESIS = "conditional_hypothesis_not_established"
CEIL_AUTHORIZED_STATE = "authorized_consequential_state_only"
CEIL_DIRECT_OBSERVATION = "direct_observations_only"
CEIL_STATE_LIMIT = "state_the_limit_do_not_realize"
CEIL_LISTED_ONLY = "listed_claims_only"

_DIRECT_OBSERVATION_OPERATIONS = {"perceive", "inspect"}
_NON_OBSERVATION_DIMENSIONS = {"interpretation", "source", "confidence", "cause", "actor", "time", "history"}
_REFUSAL_OUTCOMES = {OUTCOME_NONRESOLUTION, OUTCOME_UNRESOLVED, OUTCOME_PROTECTED}
_TURN_OPERATION_MODEL_KEYS = (
    "projection_only",
    "authority_owner",
    "response_operation",
    "declaration_expectation",
    "semantic_ceiling",
    "instruction",
)

_INSTR_BOUNDED = (
    "Interpret what the listed observations may indicate. "
    "Do not explain an unauthorized cause, actor, time, or history. "
    "A bounded inference may be proposed as gm_inference, inferred, possible, or left in narration. "
    "Do not declare a new world fact merely to answer."
)
_INSTR_DIALOGUE = (
    "On this turn, reply in ordinary narration: answer, hesitate, deflect, joke, or refuse. "
    "The reply itself belongs in narration. Do not declare that reply as a world fact. "
    "Do not establish a durable preference or history merely to answer. "
    "Listed claims may still be realized if restated."
)
_INSTR_HYPOTHESIS = (
    "Discuss whether the player's hypothesis fits the listed observations, conditionally. "
    "Do not establish the hypothesis, an actor, a motive, a tool, or timing. "
    "No declaration is needed merely to discuss it. Realize only claims already listed."
)
_INSTR_CONSEQUENTIAL = (
    "Realize the consequential state this decision authorizes. "
    "Declare those authorized claims with source_claim_id and their provenance. "
    "Do not add a further cause, actor, or history."
)
_INSTR_OBSERVATION = (
    "State the authorized observations. Do not add an inference, a cause, or a new world fact. "
    "Realize only the listed observation claims."
)
_INSTR_REFUSAL = (
    "State the limit. The requested consequence is not authorized. Do not declare it as established."
)
_INSTR_LISTED = "Realize only claims this decision already lists. Do not add a new consequential fact."


def prompt_decision_projection(decision: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Model-facing decision rows.

    Drops prose constraints, proposed-fact copies, and epistemic acts. Those
    operational readings live on the answer recipe. Canonical decision state
    is unchanged. Realization claim texts stay here so realize-mode ids remain
    attached to the authorized wording.
    """
    compact = compact_decision_for_prompt(decision)
    if not compact:
        return None
    compact.pop("narration_constraints", None)
    compact.pop("proposed_facts", None)
    compact.pop("epistemic_acts", None)
    return compact


def _recipe_claim(row: Mapping[str, Any]) -> dict[str, Any]:
    projected = {
        "claim_id": row.get("claim_id"),
        "role": row.get("realization_role"),
        "text": row.get("text"),
        "provenance": row.get("provenance"),
        "epistemic_status": row.get("epistemic_status"),
        "relation_kind": row.get("relation_kind"),
    }
    modality = str(row.get("modality") or "").strip()
    if modality:
        projected["modality"] = modality
    premises = _id_list(row.get("premise_claim_ids"))
    if premises:
        projected["premise_claim_ids"] = premises
    return projected


def _contract_dimensions(contract: Mapping[str, Any]) -> list[str]:
    dims = [str(item) for item in (contract.get("dimensions") or []) if str(item).strip()]
    single = str(contract.get("dimension") or "").strip()
    if single and single not in dims:
        dims.append(single)
    return dims


def _contract_target(contract: Mapping[str, Any]) -> str:
    target_ref = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    return str(
        target_ref.get("id_or_text")
        or contract.get("target")
        or contract.get("conversational_subject")
        or contract.get("subject")
        or ""
    ).strip()


def _contract_interlocutor(contract: Mapping[str, Any]) -> str:
    return str(contract.get("interlocutor_id") or contract.get("interlocutor") or "").strip()


def _qualified_infer_acts(decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    acts: list[dict[str, Any]] = []
    for act in decision.get("epistemic_acts") or []:
        if not isinstance(act, Mapping) or str(act.get("act") or "") != EPISTEMIC_ACT_INFER:
            continue
        identity = act.get("semantic_identity") if isinstance(act.get("semantic_identity"), Mapping) else {}
        if str(identity.get("scope") or "") != QUALIFIED_POSSIBILITIES_SCOPE:
            continue
        acts.append(
            {
                "act": EPISTEMIC_ACT_INFER,
                "authority": str(act.get("authority") or AUTH_OBSERVATION),
                "epistemic_status": str(identity.get("epistemic_status") or STATUS_INFERRED),
                "scope": QUALIFIED_POSSIBILITIES_SCOPE,
                "subject": str(identity.get("subject") or ""),
                "relation_kind": str(identity.get("relation_kind") or REL_EPISTEMIC_STATUS),
            }
        )
    return acts


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _consequential_realization_authorized(decision: Mapping[str, Any]) -> bool:
    """True when this decision already authorizes creation of consequential state."""
    if _mapping_rows(decision.get("permitted_state_mutations")):
        return True
    if str(decision.get("outcome_classification") or "") in {OUTCOME_MUTATION, OUTCOME_AUTHORIZED_STATE}:
        return True
    obligations = decision.get("executable_obligations")
    if isinstance(obligations, Mapping) and str(obligations.get("mutation_owner") or "").strip():
        return True
    for row in _mapping_rows(decision.get("realization_claims")):
        source = str(row.get("source_ref") or "")
        if source.startswith("resolution.permitted_state_mutations") or source.startswith("resolution.state_changes"):
            return True
    return False


def _hypothesis_authority_fields(decision: Mapping[str, Any], contract: Mapping[str, Any]) -> list[str]:
    """Existing player-hypothesis signals. Does not add a claim."""
    fields: list[str] = []
    for key in ("realization_claims", "proposed_facts"):
        if any(str(row.get("provenance") or "") == PROVENANCE_PLAYER_HYPOTHESIS for row in _mapping_rows(decision.get(key))):
            fields.append(f"gm_resolution_decision.{key}.provenance")
    if player_hypothesis_claims(str(contract.get("raw_input") or "")):
        fields.append("resolution_contract.raw_input")
    return fields


def _operation_projection(
    response_operation: str,
    declaration_expectation: str,
    semantic_ceiling: str,
    instruction: str,
    source_authority_fields: list[str],
) -> dict[str, Any]:
    return {
        "projection_only": True,
        "authority_owner": "gm_resolution_decision",
        "response_operation": response_operation,
        "declaration_expectation": declaration_expectation,
        "semantic_ceiling": semantic_ceiling,
        "instruction": instruction,
        "source_authority_fields": list(source_authority_fields),
    }


def project_turn_local_operation(
    decision: Mapping[str, Any] | None,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Project what response to perform, whether to declare, and how far the answer may go.

    Derived only from the decision, the resolution contract, and the existing
    player-hypothesis classifier. Not an authority source. ``source_authority_fields``
    is for tests and review; the model-facing recipe omits it.
    """
    if not isinstance(decision, Mapping) or not str(decision.get("contract_id") or "").strip():
        return None
    contract = contract if isinstance(contract, Mapping) else {}
    qualified = _qualified_infer_acts(decision)
    hypothesis_fields = _hypothesis_authority_fields(decision, contract)
    consequential = _consequential_realization_authorized(decision)
    dims = _contract_dimensions(contract)
    interlocutor = _contract_interlocutor(contract)
    operation = str(contract.get("operation") or "")
    outcome = str(decision.get("outcome_classification") or "")

    if consequential:
        return _operation_projection(
            OP_CONSEQUENTIAL_REALIZATION,
            DECL_REQUIRED_FOR_AUTHORIZED,
            CEIL_AUTHORIZED_STATE,
            _INSTR_CONSEQUENTIAL,
            [
                "gm_resolution_decision.permitted_state_mutations",
                "gm_resolution_decision.outcome_classification",
                "gm_resolution_decision.realization_claims.source_ref",
                "gm_resolution_decision.executable_obligations.mutation_owner",
            ],
        )
    if qualified:
        instruction = _INSTR_BOUNDED
        if hypothesis_fields:
            instruction += " Do not establish a player hypothesis as fact."
        return _operation_projection(
            OP_BOUNDED_INTERPRETATION,
            DECL_OPTIONAL_BOUNDED_INFERENCE,
            CEIL_INTERPRET_NOT_EXPLAIN,
            instruction,
            [
                "gm_resolution_decision.epistemic_acts",
                "gm_resolution_decision.epistemic_acts.semantic_identity.scope",
            ],
        )
    if hypothesis_fields:
        return _operation_projection(
            OP_PLAYER_HYPOTHESIS,
            DECL_HYPOTHESIS_NOT_REQUIRED,
            CEIL_CONDITIONAL_HYPOTHESIS,
            _INSTR_HYPOTHESIS,
            hypothesis_fields,
        )
    if outcome in _REFUSAL_OUTCOMES:
        return _operation_projection(
            OP_REFUSAL_OR_LIMIT,
            DECL_PROHIBITED,
            CEIL_STATE_LIMIT,
            _INSTR_REFUSAL,
            ["gm_resolution_decision.outcome_classification"],
        )
    if interlocutor:
        return _operation_projection(
            OP_INCIDENTAL_DIALOGUE,
            DECL_REPLY_NOT_REQUIRED,
            CEIL_TRANSIENT_DIALOGUE,
            _INSTR_DIALOGUE,
            [
                "resolution_contract.interlocutor_id",
                "gm_resolution_decision.epistemic_acts",
                "gm_resolution_decision.permitted_state_mutations",
            ],
        )
    if operation in _DIRECT_OBSERVATION_OPERATIONS and not (set(dims) & _NON_OBSERVATION_DIMENSIONS):
        return _operation_projection(
            OP_DIRECT_OBSERVATION,
            DECL_OBSERVATIONS_ONLY,
            CEIL_DIRECT_OBSERVATION,
            _INSTR_OBSERVATION,
            [
                "resolution_contract.operation",
                "resolution_contract.dimensions",
                "gm_resolution_decision.epistemic_acts",
            ],
        )
    listed = any(
        str(row.get("realization_role") or "") in {ROLE_MUST_STATE, ROLE_MAY_STATE}
        for row in _mapping_rows(decision.get("realization_claims"))
    )
    return _operation_projection(
        OP_LISTED_CLAIMS,
        DECL_LISTED_ONLY if listed else DECL_NONE,
        CEIL_LISTED_ONLY,
        _INSTR_LISTED,
        ["gm_resolution_decision.realization_claims"],
    )


def select_provider_response_envelope(
    decision: Mapping[str, Any] | None,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose the model-facing response contract as a projection of authority.

    This is not a second authority source. It only decides whether the provider
    needs the structured declaration channel for this already-classified turn.
    Canonical internal responses still normalize to the structured representation.
    """
    projected = project_turn_local_operation(decision, contract)
    if not isinstance(projected, Mapping):
        return {
            "selected_envelope": PROVIDER_ENVELOPE_STRUCTURED,
            "projection_only": True,
            "authority_owner": "gm_resolution_decision",
            "selection_authority_source": ["gm_resolution_decision"],
            "declaration_channel_exposed": True,
            "reason": "missing_turn_operation_projection",
        }
    response_operation = str(projected.get("response_operation") or "")
    declaration_expectation = str(projected.get("declaration_expectation") or "")
    consequential = _consequential_realization_authorized(decision if isinstance(decision, Mapping) else {})
    eligible = (
        response_operation == OP_INCIDENTAL_DIALOGUE
        and declaration_expectation == DECL_REPLY_NOT_REQUIRED
        and not consequential
    )
    if not eligible:
        return {
            "selected_envelope": PROVIDER_ENVELOPE_STRUCTURED,
            "projection_only": True,
            "authority_owner": "gm_resolution_decision",
            "selection_authority_source": list(projected.get("source_authority_fields") or []),
            "declaration_channel_exposed": True,
            "reason": "structured_declaration_channel_still_available",
            "response_operation": response_operation,
            "declaration_expectation": declaration_expectation,
            "consequential_realization_required": consequential,
        }
    return {
        "selected_envelope": PROVIDER_ENVELOPE_NARRATION_ONLY,
        "projection_only": True,
        "authority_owner": "gm_resolution_decision",
        "selection_authority_source": list(projected.get("source_authority_fields") or []),
        "declaration_channel_exposed": False,
        "reason": "ordinary_incidental_dialogue_reply_requires_no_declaration",
        "response_operation": response_operation,
        "declaration_expectation": declaration_expectation,
        "consequential_realization_required": False,
    }


def _model_turn_operation(projected: Mapping[str, Any]) -> dict[str, Any]:
    return {key: projected[key] for key in _TURN_OPERATION_MODEL_KEYS}


def _align_answer_strategy(strategy: str, response_operation: str) -> str:
    """Keep the existing summary, and attach the projection where it would otherwise compete."""
    if response_operation == OP_BOUNDED_INTERPRETATION:
        clause = " Do not explain an unauthorized cause, actor, time, or history."
        return strategy if clause.strip() in strategy else strategy + clause
    if response_operation == OP_PLAYER_HYPOTHESIS:
        if "existing status" in strategy:
            clause = " Discuss that hypothesis only conditionally. Do not establish it."
            return strategy if "only conditionally" in strategy else strategy + clause
        return "Realize the listed claims. Discuss the player's hypothesis conditionally. Do not establish it."
    if response_operation == OP_CONSEQUENTIAL_REALIZATION:
        return (
            "Realize the authorized consequential claims and declare them with "
            "source_claim_id and their provenance."
        )
    if response_operation == OP_DIRECT_OBSERVATION:
        if "unresolved" in strategy:
            clause = " Do not add an inference or a new world fact."
            return strategy if clause.strip() in strategy else strategy + clause
        return "State the authorized observations directly. Do not add an inference or a new world fact."
    if response_operation == OP_REFUSAL_OR_LIMIT:
        return "State the limit. Do not realize the requested consequence."
    return strategy


def build_decision_facing_answer_recipe(
    decision: Mapping[str, Any] | None,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Project the current decision into operational answer guidance.

    Reads canonical decision and contract fields only. Does not authorize facts
    that are absent from those structures.
    """
    if not isinstance(decision, Mapping) or not str(decision.get("contract_id") or "").strip():
        return None
    contract = contract if isinstance(contract, Mapping) else {}
    projected = project_turn_local_operation(decision, contract)
    if projected is None:
        return None
    turn_operation = _model_turn_operation(projected)
    response_operation = str(turn_operation["response_operation"])
    claims = [row for row in (decision.get("realization_claims") or []) if isinstance(row, Mapping)]
    required = [_recipe_claim(row) for row in claims if str(row.get("realization_role") or "") == ROLE_MUST_STATE]
    permitted = [_recipe_claim(row) for row in claims if str(row.get("realization_role") or "") == ROLE_MAY_STATE]
    may_infer = [_recipe_claim(row) for row in claims if str(row.get("realization_role") or "") == ROLE_MAY_INFER]
    preserve = [_recipe_claim(row) for row in claims if str(row.get("realization_role") or "") == ROLE_MUST_PRESERVE_UNCERTAINTY]
    incidental_claims = [_recipe_claim(row) for row in claims if str(row.get("realization_role") or "") == ROLE_INCIDENTAL_TEXTURE]
    qualified = _qualified_infer_acts(decision)
    inference_allowed = bool(qualified or may_infer)
    dims = _contract_dimensions(contract)
    target = _contract_target(contract)
    interlocutor = _contract_interlocutor(contract)
    operation = str(contract.get("operation") or "request")
    question = _clean(contract.get("raw_input"), limit=160)
    unresolved = [str(item) for item in (decision.get("unresolved_qualifiers") or []) if str(item).strip()]
    for row in preserve:
        label = str(row.get("text") or "").strip()
        if label and label not in unresolved:
            unresolved.append(label)
    forbidden = ["unauthorized_consequential_fact", "generated_content_as_authored_world_fact"]
    if qualified:
        for slot in _QUALIFIED_UNRESOLVED:
            if slot not in unresolved:
                unresolved.append(slot)
        for item in _QUALIFIED_FORBIDDEN:
            if item not in forbidden:
                forbidden.append(item)
    elif interlocutor:
        forbidden.append("durable_preference_without_authorized_claim")
        forbidden.append("generated_dialogue_as_authored_world_fact")

    if "interpretation" in dims and qualified:
        requested = f"Answer the interpretation request about {target or 'the current subject'}."
    elif interlocutor:
        requested = f"Answer {interlocutor} in ordinary speech."
    elif dims:
        requested = f"Answer the {operation} about {target or 'the current subject'} ({', '.join(dims)})."
    else:
        requested = f"Answer the {operation} about {target or 'the current subject'}."
    if question:
        requested = f"{requested} Player asked: {question}"

    if qualified:
        strategy = (
            "Answer the interpretation with one qualified possibility grounded in the required observations. "
            "Use could, may, or might, and keep the wording tied to those observations."
        )
        modality = "possible"
    elif may_infer:
        modalities = {str(row.get("modality") or "").strip() for row in may_infer if str(row.get("modality") or "").strip()}
        modality = "hypothetical" if modalities == {"hypothetical"} else "inferred"
        strategy = (
            "Answer from the required claims. Keep listed inferences and player hypotheses at their existing status."
        )
    elif unresolved and not inference_allowed:
        strategy = "State the required claims, then say in ordinary speech that the unresolved part is not established."
        modality = "none"
    elif interlocutor:
        strategy = (
            f"Have {interlocutor} reply in ordinary dialogue: a direct answer, a refusal, a hesitation, "
            "or an admission that they do not know."
        )
        modality = "none"
    elif required:
        strategy = "Answer directly by realizing the required claims."
        modality = "none"
    else:
        strategy = "Realize only claims this decision already lists."
        modality = "none"
    strategy = _align_answer_strategy(strategy, response_operation)

    epistemic_claims = [
        row
        for row in claims
        if str(row.get("provenance") or "")
        in {PROVENANCE_PLAYER_HYPOTHESIS, PROVENANCE_NPC_CLAIM, PROVENANCE_SPECULATION, PROVENANCE_GM_INFERENCE}
        or _id_list(row.get("premise_claim_ids"))
        or str(row.get("realization_role") or "") == ROLE_MUST_PRESERVE_UNCERTAINTY
    ]
    if epistemic_claims:
        epistemic_line = (
            "Preserve epistemic status and premise_claim_ids. "
            "Do not promote a hypothesis, NPC claim, or unresolved premise into world truth."
        )
    elif response_operation == OP_PLAYER_HYPOTHESIS:
        epistemic_line = (
            "A player hypothesis on this turn may be discussed conditionally. "
            "It is not an authorized claim and it is not world truth."
        )
    else:
        epistemic_line = "No player hypothesis, NPC claim, or unresolved premise is authorized on this turn."
    if qualified:
        inference_line = (
            "propose only; provenance gm_inference; epistemic_status inferred; "
            "modality possible; relation_kind epistemic_status. Not authored_world_fact."
        )
    elif may_infer:
        inference_line = (
            "realize the listed may_infer claims at their existing status and modality. "
            "Do not propose a stronger inference."
        )
    else:
        inference_line = "not permitted on this turn"
    if interlocutor and not qualified:
        incidental = (
            "Ordinary refusal, hesitation, mannerism, and phrasing may stay plain narration "
            "or a bounded incidental improvisation. That speech is not authored world truth."
        )
    elif incidental_claims:
        incidental = "Incidental claims already listed may be realized as texture. Do not upgrade them to world truth."
    else:
        incidental = "Harmless sensory detail and mannerism may stay plain narration. They are not consequential claims."

    permitted_inference: dict[str, Any] = {
        "allowed": inference_allowed,
        "qualified_observations": qualified,
        "may_infer_claims": may_infer,
    }
    if response_operation == OP_INCIDENTAL_DIALOGUE:
        consequential_line = (
            "Listed claims may be realized with source_claim_id and their provenance. "
            "The turn-local reply is narration, not a new authored world fact."
            if required or permitted
            else "no additional consequential claim is authorized"
        )
    elif response_operation == OP_CONSEQUENTIAL_REALIZATION:
        consequential_line = (
            "realize the authorized consequential claims with source_claim_id and the claim provenance"
        )
    else:
        consequential_line = (
            "realize with source_claim_id and the claim provenance"
            if required or permitted
            else "no additional consequential claim is authorized"
        )
    return {
        "schema": RECIPE_SCHEMA,
        "projection_only": True,
        "authority_owner": "gm_resolution_decision",
        "turn_operation": turn_operation,
        "requested_answer": requested,
        "required_content": required,
        "permitted_content": permitted,
        "permitted_inference": permitted_inference,
        "inference_modality": modality,
        "unresolved_content": unresolved,
        "forbidden_upgrades": forbidden,
        "declaration_guidance": {
            "consequential_authorized_claim": consequential_line,
            "bounded_inference": inference_line,
            "epistemic_premise": epistemic_line,
            "epistemic_claims": [_recipe_claim(row) for row in epistemic_claims],
            "ordinary_incidental_expression": incidental,
        },
        "incidental_improvisation_guidance": incidental,
        "answer_strategy": strategy,
    }


def _free_text_question_overlap(question: str, fact: str) -> int:
    return len(_token_set(question) & _token_set(fact))


def authorized_observation_line(decision: Mapping[str, Any] | None, player_text: str | None = None) -> str:
    """State established observations instead of claiming that nothing is known.

    Structured facts are used on an established outcome. A free-text authored
    fact has no semantic identity, so an established or epistemic ask may quote
    that sentence when the question shares its content words. The quote is the
    authored text, not an inferred consequence.
    """
    if not isinstance(decision, Mapping):
        return ""
    outcome = str(decision.get("outcome_classification") or "")
    if outcome not in {OUTCOME_ESTABLISHED, OUTCOME_EPISTEMIC}:
        return ""
    question = _norm_phrase(player_text)
    chosen: list[str] = []
    free_text: list[tuple[int, str]] = []
    for row in decision.get("proposed_facts") or []:
        if not isinstance(row, Mapping) or not row.get("authorized"):
            continue
        if str(row.get("authority") or "") != AUTH_WORLD:
            continue
        identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), Mapping) else {}
        kind = str(identity.get("kind") or "")
        text = _clean(row.get("text"), limit=400)
        if not text:
            continue
        if not kind:
            score = _free_text_question_overlap(question, text)
            if score >= 2:
                free_text.append((score, text))
            continue
        if kind == "entity" or outcome != OUTCOME_ESTABLISHED:
            continue
        subjects = _identity_terms(identity, "subject")
        if question and subjects and not any(term in question for term in subjects):
            continue
        if text not in chosen:
            chosen.append(text)
    if not chosen and free_text:
        best = max(score for score, _text in free_text)
        for _score, text in free_text:
            if _score == best and text not in chosen:
                chosen.append(text)
    if not chosen:
        return ""
    line = " ".join(chosen[:3])
    quoted = {item[1] for item in free_text}
    used_free_text_only = bool(quoted) and all(text in quoted for text in chosen[:3])
    slots = [str(item) for item in (decision.get("unresolved_qualifiers") or []) if str(item).strip()]
    labels = {"actor": "who did it", "time": "when it happened", "cause": "what caused it"}
    parts = [labels[slot] for slot in slots if slot in labels]
    if parts and not used_free_text_only:
        line = f"{line} It is not established {' or '.join(parts)}."
    return line


def retry_authority_context(
    *,
    resolution: Mapping[str, Any] | None,
    reasons: Sequence[str] | None = None,
    audit: Mapping[str, Any] | None = None,
    provider_response_contract: str = PROVIDER_ENVELOPE_STRUCTURED,
) -> str:
    """Compact contract and decision for a repair turn. Not the full world state.

    Retry resends the original provider messages, which already carry
    ``decision_facing_answer_recipe``. This feedback must not add a second recipe.
    """
    import json

    from game.resolution_contract import generation_projection

    contract = contract_mapping_from_resolution(resolution if isinstance(resolution, Mapping) else None)
    decision = decision_from_resolution(resolution if isinstance(resolution, Mapping) else None)
    violations = []
    if isinstance(audit, Mapping):
        for row in audit.get("violations") or []:
            if not isinstance(row, Mapping):
                continue
            violations.append(
                {
                    "reason_codes": list(row.get("reason_codes") or []),
                    "text": _clean(row.get("text"), limit=240),
                }
            )
    compact = compact_decision_for_prompt(decision)
    declaration = audit.get("declaration_validation") if isinstance(audit, Mapping) else None
    rejected_declarations = []
    if isinstance(declaration, Mapping):
        rejected_declarations = [
            {
                "text": _clean(row.get("text"), limit=240),
                "reason_codes": list(row.get("reason_codes") or []),
                "declaration_mode": row.get("declaration_mode"),
            }
            for row in (declaration.get("rejected_claims") or [])
            if isinstance(row, Mapping)
        ]
    payload = {
        "resolution_contract": generation_projection(contract) or {
            "contract_id": contract.get("contract_id"),
            "operation": contract.get("operation"),
        },
        "gm_resolution_decision": compact,
        "accepted_realization_claims": list((compact or {}).get("realization_claims") or []),
        "rejected_declarations": rejected_declarations,
        "validation_failure": {
            "reasons": [str(reason) for reason in (reasons or []) if str(reason).strip()],
            "violations": violations,
        },
        "structured_envelope_schema": {
            "declared_claims": [
                {
                    "declaration_mode": "realize|propose",
                    "source_claim_id": "claim_id_from_gm_resolution_decision or null",
                    "premise_claim_ids": ["claim ids of propositions this epistemic claim depends on"],
                    "text": "short internal claim",
                    "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
                    "modality": "established|possible|hypothetical|unresolved",
                }
            ],
            "narration": "player-facing sentence",
        },
    }
    # The envelope was selected before generation. Retry must not choose another.
    if str(provider_response_contract or "") == PROVIDER_ENVELOPE_NARRATION_ONLY:
        payload.pop("rejected_declarations", None)
        payload.pop("structured_envelope_schema", None)
        payload["narration_only_response_schema"] = dict(NARRATION_ONLY_RESPONSE_SCHEMA)
    return "AUTHORITATIVE RETRY CONTEXT " + json.dumps(payload, ensure_ascii=False, default=str)
