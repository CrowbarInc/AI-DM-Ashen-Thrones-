"""Typed resolution contract for one player turn.

The contract records what the player wants resolved. It does not decide what
the DM may invent, and it does not replace interaction obligations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import re
from typing import Any, Mapping, Sequence

from game.discourse_state import (
    SLOT_ACTION,
    SLOT_CLAIM,
    SLOT_INSPECTED,
    SLOT_INTERLOCUTOR,
    SLOT_LEAD,
    effective_discourse_focus,
    focus_summary,
)


REQUEST_INQUIRY = "inquiry"
REQUEST_ACTION = "action"
REQUEST_SOCIAL_ACTION = "social_action"
REQUEST_CLARIFICATION = "clarification"

OP_PERCEIVE = "perceive"
OP_INSPECT = "inspect"
OP_ASK = "ask"
OP_REPEAT = "repeat"
OP_CONFIRM = "confirm"
OP_FOLLOW = "follow"
OP_ACT = "act"

DIM_APPEARANCE = "appearance"
DIM_SOUND = "sound"
DIM_SMELL = "smell"
DIM_WEAR = "wear"
DIM_USE = "use"
DIM_CHANGE = "change"
DIM_SOURCE = "source"
DIM_CONFIDENCE = "confidence"
DIM_LOCATION = "location"
DIM_TIME = "time"
DIM_NEXT_STEP = "next_step"
DIM_CONTENT = "content"
DIM_INTERPRETATION = "interpretation"

PERCEPTION_DIMENSIONS = frozenset({DIM_APPEARANCE, DIM_SOUND, DIM_SMELL, DIM_WEAR, DIM_USE, DIM_CHANGE})
CLAIM_DIMENSIONS = frozenset({DIM_SOURCE, DIM_CONFIDENCE, DIM_LOCATION, DIM_TIME})

EXPECT_ANSWER = "answer"
EXPECT_ACTION = "action_outcome"
EXPECT_REFUSAL = "refusal"
EXPECT_CLARIFICATION = "clarification"
EXPECT_PARTIAL = "partial"

EPISTEMIC_AUTHORITATIVE = "authoritative"
EPISTEMIC_INCIDENTAL = "bounded_incidental"
EPISTEMIC_NPC_CLAIM = "npc_claim"
EPISTEMIC_UNKNOWN = "unknown_allowed"
EPISTEMIC_CONSEQUENTIAL = "consequential_protected"

PROVENANCE_EXPLICIT = "explicit_player"
PROVENANCE_INHERITED = "inherited_discourse"
PROVENANCE_UNRESOLVED = "unresolved"
PROVENANCE_AMBIGUOUS = "ambiguous"

# Provenance of an existing claim: speaker, hearing-from, learning, being told.
_SOURCE_RE = re.compile(
    r"\b(?:"
    r"who\s+(?:told|said|passed|gave)\b"
    r"|who\s+(?:was|is)\s+the\s+source"
    r"|source\s+of"
    r"|passed\s+it\s+to"
    r"|(?:who|where|how)\b[^.?!]{0,40}(?:hear|heard|hearing)\b[^.?!]{0,32}\bfrom\b"
    r"|(?:hear|heard)\s+(?:that|it|this|the\s+\w+)\s+from\b"
    r"|where\s+(?:\w+\s+){0,5}(?:hear|heard|learn(?:ed)?)"
    r"|how\s+(?:does|do|did|would|could)\s+\w+\s+know"
    r"|gave\s+(?:\w+\s+){0,4}information"
    r"|get\s+that\s+information"
    r"|where\s+did\s+(?:you|they|he|she|him|her)\s+get"
    r"|(?:been|was|were)\s+told"
    r"|learn(?:ed)?\s+(?:that|it|this)\s+from"
    r"|who\s+would\s+know"
    r"|what(?:'s| is)\s+(?:your|his|her|their|the)\s+source\b"
    r"|who(?:'s| is)\s+(?:your|his|her|their)\s+source\b"
    r"|who\s+says\b"
    r"|\bdid\b[^.?!]{0,48}\b(?:tell|told)\b[^.?!]{0,24}\bthat\b"
    r")\b",
    re.IGNORECASE,
)
# Belief, certainty, trust, and doubt about an existing claim. Not a sentence list.
_CONFIDENCE_RE = re.compile(
    r"\b(?:"
    r"how\s+(?:sure|certain|confident)"
    r"|how\s+much\s+(?:\w+\s+){0,4}believe"
    r"|are\s+you\s+sure"
    r"|confidence"
    r"|(?:does|do|did|is|are)\s+(?:\w+\s+){0,3}(?:believe|trust|doubt)"
    r"|whether\s+(?:he|she|they|you|him|her)(?:'s| is| are)?\s+(?:sure|certain|confident)"
    r"|(?:is|are|was|were)\s+(?:he|she|they|you)\s+(?:sure|certain|confident)"
    r"|how\s+sure\s+(?:is|are|was)"
    r"|sure\s+about\s+(?:that|this|it|him|her|them)"
    r"|do\s+you\s+trust"
    r"|ask(?:s|ed)?\s+(?:him|her|them|you)\b[^.?!]{0,48}\b(?:sure|certain)"
    r"|(?:sound|sounds|seem|seems)\s+(?:sure|certain|confident)"
    r"|(?:do|does|did)\s+(?:the\s+)?(?:\w+\s+){0,4}(?:sound|seem)\s+(?:sure|certain|confident)"
    r"|believe\s+(?:it|that|them|him|her|the|this)"
    r"|trust(?:s|ed)?\s+(?:it|that|them|him|her|the|this)"
    r"|think(?:s)?\s+it(?:'s| is)\s+true"
    r"|think(?:s)?\s+that(?:'s| is)\s+true"
    r"|convinced"
    r"|repeating\s+it"
    r"|do\s+we\s+(?:actually\s+)?know"
    r"|is\s+(?:that|this|it)\s+(?:established|known|only\s+a\s+possibility|just\s+(?:a\s+)?possibility)"
    r"|(?:only|just)\s+a\s+possibility"
    r"|are\s+we\s+(?:only\s+)?guessing"
    r"|can\s+we\s+(?:actually\s+)?tell"
    r")\b",
    re.IGNORECASE,
)
# Demonstrative plus an already-supported semantic noun: "this damage", "this condition".
# The noun list is the recognizer's existing category, not a domain lexicon.
_INTERPRETATION_SEMANTIC_NOUN = r"(?:damage|condition|observation)"
_INTERPRETATION_RE = re.compile(
    r"\b(?:"
    r"what\s+(?:does|might|could)\s+"
    r"(?:"
    r"(?:that|this|it)(?:\s+" + _INTERPRETATION_SEMANTIC_NOUN + r")?"
    r"|the\s+" + _INTERPRETATION_SEMANTIC_NOUN +
    r"|its\s+condition"
    r")\s+"
    r"(?:suggest|mean|tell\s+me)"
    r"|what\s+can\s+i\s+infer"
    r"|does\s+(?:that|this|it|anything(?:\s+about\s+(?:it|them|this|that))?)\s+"
    r"(?:suggest|point\s+to)"
    r"|what\s+might\s+(?:its|the)\s+condition\s+mean"
    r"|what\s+(?:does|might)\s+its\s+condition\s+(?:suggest|mean)"
    r")\b",
    re.IGNORECASE,
)
_TIME_RE = re.compile(
    r"\b(?:when\s+(?:did|was|were|is)|how\s+long\s+(?:ago|has|have|had)|how\s+recently|what\s+time|"
    r"was\s+(?:that|this|it)\s+(?:today|yesterday|tonight)|when\s+did\s+that\s+start)\b",
    re.IGNORECASE,
)
_LOCATION_RE = re.compile(
    r"\b(?:where\s+(?:did|does|is|was|were|can|could)|from\s+here|what\s+place)\b",
    re.IGNORECASE,
)
_WEAR_RE = re.compile(
    r"\b(?:"
    r"wear|worn|scuffs?|fray(?:ed|ing)?|disturbed|handled|weathered|weather\s+had"
    r"|(?:look(?:s|ed|ing)?|seem(?:s|ed)?|appear(?:s|ed)?)\s+(?:(?:\w+)\s+){0,5}(?:used|worn|handled|disturbed)"
    r"|(?:people|someone|anybody|anyone|folks)\s+com(?:e|ing)\s+through"
    r"|signs?\s+of\s+(?:use|wear|handling)"
    r")\b",
    re.IGNORECASE,
)
_PURPOSE_QUESTION_RE = re.compile(
    r"\b(?:"
    r"what(?:'s| is| are)\s+(?:this|that|it)\s+(?:used\s+)?for\b"
    r"|what(?:'s| is| are)\s+(?:this|that|the)\s+(?:\w+\s+){0,4}used\s+for\b"
    r"|what\s+(?:do|does)\s+(?:people|they|folks|one)\s+(?:use|come|go)\b"
    r"|why\s+(?:do|does)\s+(?:people|they|folks)\s+(?:use|come|go)\b"
    r"|what(?:'s| is)\s+(?:this|that|it)\s+used\s+for\b"
    r"|why\s+do\s+people\s+use\b"
    r")",
    re.IGNORECASE,
)
_USE_RE = re.compile(
    r"\b(?:"
    r"signs?\s+of\s+use|\buse\b|handled|foot\s+traffic|(?:people|someone|anybody|anyone|folks)\s+com(?:e|ing)\s+through"
    r"|(?:look(?:s|ed|ing)?|seem(?:s|ed)?|appear(?:s|ed)?|been|was|were)\s+(?:(?:\w+)\s+){0,5}used"
    r")\b|"
    + _PURPOSE_QUESTION_RE.pattern,
    re.IGNORECASE,
)
_PROCEDURE_REQUEST_RE = re.compile(
    r"\b(?:"
    r"next step|concrete next|what should i do|immediate next action"
    r"|what\s+(?:do|must|should|would)\s+i\s+(?:have|need)\s+to\s+do"
    r"|what\s+i\s+(?:have|need)\s+to\s+do"
    r"|what(?:'s| is| are)\s+required"
    r"|what(?:'s| is)\s+necessary"
    r"|what\s+it\s+takes\s+to"
    r"|how\s+(?:do|can|should)\s+i\s+(?:proceed|get through|pass|enter)"
    r"|before\s+they(?:'ll| will)\s+let"
    r")\b",
    re.IGNORECASE,
)
_PROCEDURE_ANSWER_RE = re.compile(
    r"\b(?:"
    r"need(?:s)? to|have to|must|required|clearance|report to|"
    r"before (?:you|the gate|they|passing)|in order to|permission|let you|"
    r"you(?:'ll| will) need|need a|need your"
    r")\b",
    re.IGNORECASE,
)
_IDENTITY_FACT_RE = re.compile(
    r"\b(?:commands?|in charge|is the one)\b",
    re.IGNORECASE,
)
_PURPOSE_ANSWER_RE = re.compile(
    r"\b(?:"
    r"used for|meant for|serves as|purpose|function|in order to|so that|"
    r"to see|to post|to announce|to warn|to read|to learn|to check|"
    r"keep\s+\w+(?:\s+\w+){0,5}\s+informed|for official|"
    r"changes in (?:law|enforcement|safety)|people come|"
    r"where\s+(?:\w+\s+){0,12}find|find\s+(?:\w+\s+){0,4}updates|crucial updates"
    r")\b",
    re.IGNORECASE,
)
# What was said, reported, written, or heard. Not who, when, how sure, or what it is for.
_CONTENT_REQUEST_RE = re.compile(
    r"\b(?:"
    r"what\s+(?:does|do|did|is|are|was|were|have|has|had)\b(?:\s+\w+){0,10}\s+"
    r"(?:say|said|saying|tell|told|telling|report|reported|reporting|repeat|repeating|write|wrote|written)"
    r"|what\s+(?:\w+\s+){0,8}(?:been\s+)?(?:saying|telling|reporting|repeating)"
    r"|what\s+(?:was|were|is|has been|have been)\s+(?:said|written|reported|told|heard)"
    r"|what(?:'s| is)\s+written\s+on\b"
    r"|what\s+is\s+written\b"
    r"|written\s+on\s+(?:it|this|that|the)\b"
    r"|what(?:'s| is)\s+on\s+it\b"
    r"|what\s+(?:does|do)\s+(?:it|this|that|(?:the\s+\w+(?:\s+\w+){0,3}))\s+(?:actually\s+)?say\b"
    r")\b",
    re.IGNORECASE,
)
_NAMED_EVENT_RE = re.compile(
    r"\bwhen\s+did\s+(?:the\s+)?(?P<event>[a-z]+(?:\s+[a-z]+){0,2}?)\s+"
    r"(?:begin|start|happen|end|stop|disappear|vanish|change)\b",
    re.IGNORECASE,
)
_BARE_TEMPORAL_ANAPHOR_RE = re.compile(
    r"\b(?:when\s+did\s+(?:that|this|it)\b|"
    r"how\s+long\s+(?:ago\s+)?(?:has|have|was|were)\s+(?:that|this|it)\b|"
    r"how\s+recently\s+(?:was|did)\s+(?:that|this|it)\b)\b",
    re.IGNORECASE,
)
_CLARIFICATION_TEXT_RE = re.compile(
    r"\b(?:clarif\w*|do you mean|what you mean|are you asking|which\b)\b",
    re.IGNORECASE,
)
_ALTERNATIVE_CLARIFICATION_RE = re.compile(
    r"\b(?:are you asking|or something else|do you mean|what you mean|which\b|or the\b)\b",
    re.IGNORECASE,
)
_REPORTED_PROPOSITION_RE = re.compile(
    r"\b(?:say|says|said|saying|speak(?:ing|s)?|tell|told|telling|report(?:ed|ing|s)?|"
    r"wrote|written|reads|rumou?r(?:ed|s)?|word is|concerns?)\b",
    re.IGNORECASE,
)
_CONTENT_STATE_RE = re.compile(
    r"\b(?:about|concern|flood|washed|missing|census|closed|written|letter|message|"
    r"bridge|road|warn|warning|tax|curfew|vanish|patrol)\b",
    re.IGNORECASE,
)
_USED_FOR_TARGET_RE = re.compile(
    r"\bwhat(?:'s| is| are)\s+(?:that|this|the)\s+(?P<target>.+?)\s+used\s+for\b",
    re.IGNORECASE,
)
_DIMENSION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (DIM_SOUND, re.compile(r"\b(?:sounds?|listen(?:ing|ed)?|hearing)\b|\bhear\b", re.IGNORECASE)),
    (DIM_SMELL, re.compile(r"\b(?:smells?|scent|odor|odour|aroma)\b", re.IGNORECASE)),
    (DIM_APPEARANCE, re.compile(r"\b(?:look(?:s|ed)? like|appearance|colou?rs?|what can i see|can i see)\b", re.IGNORECASE)),
    (DIM_WEAR, _WEAR_RE),
    (DIM_USE, _USE_RE),
    (DIM_CHANGE, re.compile(r"\b(?:what changed|what changes|changed when|when i (?:do|did) that)\b", re.IGNORECASE)),
    (DIM_SOURCE, _SOURCE_RE),
    (DIM_CONFIDENCE, _CONFIDENCE_RE),
    (DIM_TIME, _TIME_RE),
    (DIM_LOCATION, _LOCATION_RE),
    (DIM_NEXT_STEP, _PROCEDURE_REQUEST_RE),
    (DIM_CONTENT, _CONTENT_REQUEST_RE),
    (DIM_INTERPRETATION, _INTERPRETATION_RE),
)

_CONSEQUENTIAL_RE = re.compile(
    r"\b(?:secret|hidden|traitor|conspiracy|murderer|spy|cult|vault|artifact|curse|prophecy|"
    r"true motive|really works for|allegiance)\b",
    re.IGNORECASE,
)
_LEAD_RE = re.compile(
    r"\b(?:follow|take|pursue)\b[^.!?]{0,40}\b(?:that|the|this|the best|best)\s+lead\b|\bthat lead\b|\bthe lead\b",
    re.IGNORECASE,
)
_PRIOR_ACTION_RE = re.compile(
    r"\b(?:when i (?:do|did) that|after i (?:do|did) that|what changed when)\b",
    re.IGNORECASE,
)
_CONFIRM_RE = re.compile(r"\bconfirm\b[^.!?]{0,40}\b(?:next action|next step|what i should)\b", re.IGNORECASE)
_ACTION_REQUEST_RE = re.compile(
    r"\b(?:can|could|would|will)\s+(?:you|they|he|she)\s+"
    r"(?:introduce|take|bring|show|open|close|help|point|lead|give|send|ask|arrange)\b"
    r"|\b(?:introduce me|point me to|take me|lead me|bring me|show me)\b"
    r"|\bi(?:'ll| will)\s+(?:do|take|follow)\b"
    r"|\bi take that step\b"
    r"|\bdo the next\b",
    re.IGNORECASE,
)
# Player commits to one already-established step. Anchored so a change question
# ("when I do that") is not rewritten into a new action.
_REFERENTIAL_ACTION_RE = re.compile(
    r"^(?:(?:ok|okay|then|alright|all right)[, ]+)?"
    r"(?:"
    r"i(?:'ll| will| shall)?\s+(?:do|take|follow)\s+(?:that|this|it)(?:\s+step)?"
    r"|i\s+take\s+that\s+step"
    r"|let(?:'s| us)\s+(?:do|take|follow)\s+(?:it|that|this)"
    r"|i(?:'ll| will)?\s+go\s+there"
    r"|i(?:'ll| will)?\s+follow\s+(?:that|the lead|it)"
    r")\b",
    re.IGNORECASE,
)
_CLAIM_FOLLOWUP_RE = re.compile(
    r"\b(?:that|this|it|they|them|he|she|him|her|the story|the rumou?r|happen(?:ed)?)\b",
    re.IGNORECASE,
)
_PRONOUN_CUE_RE = re.compile(
    r"\b(?:he|she|him|her|they|them|it|that|this|the story|the rumou?r)\b",
    re.IGNORECASE,
)
_GENERIC_SOCIAL_INFO_RE = re.compile(
    r"\b(?:another source|couldn'?t tell you|could not tell you|"
    r"cannot verify|can't verify|have heard talk|heard talk|"
    r"do not know enough|don't know enough)\b",
    re.IGNORECASE,
)
_PHYSICAL_RE = re.compile(
    r"\b(?:open|knock|push|pull|break|force|climb|enter)\b",
    re.IGNORECASE,
)
# A committed physical act. Approach, turn, point, and look stay engagement.
_GENUINE_ACT_RE = re.compile(
    r"\bhand\s+(?:him|her|them|me|you|the|a|an|it)\b|\b(?:push|pull|pay|give)\b|\bfollow\s+the\s+\w+"
    r"|\b(?:attack|strike|stab|slash|smite)\b",
    re.IGNORECASE,
)
_INSPECT_RE = re.compile(
    r"\b(?:inspect(?:ing|s|ed)?|examin(?:e|es|ed|ing)|look at|check(?:ing|s|ed)?|"
    r"stud(?:y|ies|ied|ying)|investigat(?:e|es|ed|ing)|search(?:ing|es|ed)?)\b"
    r"|\b(?:rifle|dig)\s+through\b"
    r"|\blook(?:\s+\w+){0,3}\s+over\b"
    r"|\btake a (?:closer|careful|good|long)\s+look\b"
    r"|\bcloser look\b",
    re.IGNORECASE,
)
# A later plan to investigate is not the operation of this turn.
_SUBORDINATE_INVESTIGATION_RE = re.compile(
    r"\b(?:before|without|after|instead of)\s+(?:\w+\s+){0,4}investigat(?:e|es|ed|ing)\b",
    re.IGNORECASE,
)
_PLAYER_OBSERVE_RE = re.compile(
    r"\b(?:look|looking|watch|watching)\s+(?:into|past|across|around|through|over|at)\b"
    r"|\bi\s+(?:look|watch)\b",
    re.IGNORECASE,
)
_LOOK_OVER_TARGET_RE = re.compile(
    r"\blook\s+(?:the\s+|a\s+|an\s+)?(?P<target>.+?)\s+over\b",
    re.IGNORECASE,
)
_LOOK_OVER_FORWARD_TARGET_RE = re.compile(
    r"\blook\s+over\s+(?:the\s+|a\s+|an\s+)?(?P<target>[^?.!,]{1,60})",
    re.IGNORECASE,
)
_REPEAT_RE = re.compile(
    r"\b(?:"
    r"repeat\b(?:\s+(?:that|the|this|it|what)\b)?"
    r"|say\s+(?:that|it)\s+again\b"
    r"|what\s+was\s+that\b"
    r"|repeat\s+what\s+(?:he|she|they|you)\s+said\b"
    r")",
    re.IGNORECASE,
)
_OR_OBJECT_RE = re.compile(
    r"\bthe\s+[a-z]+(?:\s+[a-z]+)?\s+or\s+(?:the\s+)?[a-z]+(?:\s+[a-z]+)?\b",
    re.IGNORECASE,
)
_CLARIFY_RE = re.compile(r"\b(?:what do you mean|which one|which person|clarify)\b", re.IGNORECASE)
_SCENE_TARGET_RE = re.compile(r"\b(?:where i am|around me|this place|the scene)\b", re.IGNORECASE)
_EXPLICIT_TARGET_RE = re.compile(
    r"\b(?:inspect|examine|look at|listen(?:\s+to|\s+through)?|open|read|check|study|"
    r"investigate|search|(?:rifle|dig)\s+through)\s+"
    r"(?:the\s+|a\s+|an\s+)?(?P<target>[^?.!,]{1,60})",
    re.IGNORECASE,
)
_SMELL_TARGET_RE = re.compile(
    r"\b(?:smell|smelling)\s+(?:the\s+|a\s+|an\s+)(?P<target>[^?.!,]{1,60})",
    re.IGNORECASE,
)
_AT_OBJECT_RE = re.compile(
    r"\b(?:at|on)\s+(?:the\s+|a\s+|an\s+)?(?P<target>[a-z][^?.!,]{1,40}?)(?=\s+and\b|[?.!,]|$)",
    re.IGNORECASE,
)
_WHAT_DOES_RE = re.compile(
    r"\bwhat does\s+(?:the\s+|a\s+|an\s+)?(?P<target>.+?)\s+(?:look|smell|sound|feel)\b",
    re.IGNORECASE,
)
_PRONOUN_TARGET_RE = re.compile(
    r"^(?:it|its|that|this|them|they|him|her|that lead|the lead|that person|that place|that thing)$",
    re.IGNORECASE,
)
_ANAPHOR_RE = re.compile(r"\b(?:it|its|that|this|them|they|that person|that place)\b", re.IGNORECASE)

_RESPONSE_CUES: dict[str, re.Pattern[str]] = {
    DIM_SOUND: re.compile(
        r"\b(?:sounds?|hear|hearing|listen|quiet|noise|noisy|silence|silent|voices?|footsteps?|"
        r"murmurs?|clang|creak|shouts?|whispers?|music|thuds?|rustle|calls?|called|calling)\b",
        re.IGNORECASE,
    ),
    DIM_SMELL: re.compile(r"\b(?:smells?|scent|odor|odour|aroma|stink|reek|fragrant|stench)\b", re.IGNORECASE),
    DIM_APPEARANCE: re.compile(
        r"\b(?:look(?:s|ed|ing)?|appear(?:s|ance)?|colou?r|visible|seen|shaped|painted|dented|scarred)\b",
        re.IGNORECASE,
    ),
    DIM_WEAR: re.compile(
        r"\b(?:wear|worn|used|marks|scuffs?|scratched|faded|dented|disturbed|polished|scarred|"
        r"handled|come through|fresh)\b",
        re.IGNORECASE,
    ),
    DIM_USE: re.compile(
        r"\b(?:used|use|handled|foot traffic|opened often|rarely touched|come through|"
        r"serves as|purpose|function|meant for|used for|used to|clearinghouse|"
        r"to see|to post|to announce|to warn|for official|people come|"
        r"changes in (?:law|enforcement|safety)|informed|"
        r"where\s+(?:\w+\s+){0,12}find|find\s+(?:\w+\s+){0,4}updates|crucial updates)\b",
        re.IGNORECASE,
    ),
    DIM_CHANGE: re.compile(
        r"\b(?:change[ds]?|unchanged|no difference|still the same|nothing (?:new|changes)|remains)\b",
        re.IGNORECASE,
    ),
    DIM_SOURCE: re.compile(
        r"\b(?:told|heard from|heard it|according to|source|someone|nobody|travelers?|"
        r"cannot verify|from (?:him|her|them)|word came)\b",
        re.IGNORECASE,
    ),
    DIM_CONFIDENCE: re.compile(
        r"\b(?:certain|sure|believe|doubt|trust|unsure|confident|certainty|not sure)\b",
        re.IGNORECASE,
    ),
    DIM_LOCATION: re.compile(
        r"\b(?:from here|over there|located|location|took place|happened|nearby|beside|next to|across|near)\b",
        re.IGNORECASE,
    ),
    DIM_TIME: re.compile(
        r"\b(?:yesterday|tonight|earlier|recently|recent|timing|recency|ago|at dusk|last night|this morning)\b",
        re.IGNORECASE,
    ),
    DIM_NEXT_STEP: re.compile(
        r"\b(?:next step|you can|ask the|go to|try to|follow|first|route|another route)\b",
        re.IGNORECASE,
    ),
}
_ACTION_SUCCESS_RE = re.compile(
    r"\b(?:leads?|led|takes you|brings you|shows you|follows|followed|goes with|sets off|"
    r"steps toward|opens?|opened|closes|closed|pulls?|points toward|heads toward)\b",
    re.IGNORECASE,
)
_ACTION_NONRESOLUTION_RE = re.compile(
    r"\b(?:refuses|refused|will not (?:leave|take|lead|go|do|carry|introduce)|"
    r"won't (?:leave|take|lead|go|introduce)|"
    r"cannot (?:leave|take|lead|go|follow|complete|do|introduce)|"
    r"can't (?:leave|take|lead|go|follow|introduce)|"
    r"not until|only if|unless|which (?:place|one|lead)|do you mean|"
    r"cannot be completed|another route|will not carry|blocked|fails to)\b",
    re.IGNORECASE,
)
_ECHO_FRAME = frozenset(
    {
        "you", "your", "ask", "asks", "asked", "asking", "wonder", "wonders", "wondering",
        "whether", "about", "the", "and", "that", "this", "what", "how", "who", "where",
        "when", "why", "does", "did", "are", "was", "were", "have", "has", "with", "from",
        "into", "want", "wants", "trying", "look", "looking", "tell", "told",
    }
)
_LEGITIMATE_RE = re.compile(
    r"\b(?:cannot|can't|could not|couldn't|will not|won't|unable|another (?:source|route)|"
    r"cannot be identified|which (?:one|person)|clarif(?:y|ication)|no reliable|no distinct|"
    r"not able|do not know|don't know|not enough|need another|will not carry)\b",
    re.IGNORECASE,
)
_GENERIC_ACTION_REFUSAL_RE = re.compile(
    r"\b(?:will not carry out that request|won'?t carry out that request|"
    r"you will need another route|another route is needed|"
    r"requested action cannot be completed)\b",
    re.IGNORECASE,
)
_ACK_ONLY_RE = re.compile(
    r"\b(?:there (?:has|have) been talk|there(?:'s| is| was) talk|have heard talk|heard talk|"
    r"there are rumou?rs|people are talking|word is going around)\b",
    re.IGNORECASE,
)
_REPORT_FRAME_RE = re.compile(
    r"\b(?:say|says|said|whisper(?:ed|s)?|rumou?r|word is|heard|repeat(?:ed|ing)?|claim(?:s|ed)?|"
    r"story|gossip|news)\b",
    re.IGNORECASE,
)
_NEGATIVE_RESOLUTION_RE = re.compile(
    r"\b(?:no (?:further|reliable|distinct|change)|cannot|can't|could not|couldn't|"
    r"do not know|don't know|unable|not able|illegible|too (?:far|dark|faint)|"
    r"while it(?:'s| is) sealed|is sealed|never heard|did not hear|didn't hear|"
    r"cannot recall|can't recall|cannot read|can't read|no one(?: here)? can say|cannot say|can't say|"
    r"will not repeat|won't repeat|"
    r"will not say|won't say|"
    r"no one(?: at hand| here)? answers|nobody answers|the question hangs|hangs in the noise)\b",
    re.IGNORECASE,
)
_GENERIC_USE_NONANSWER_RE = re.compile(
    r"visible wear and marks establish no reliable use",
    re.IGNORECASE,
)
_GENERIC_INSPECTION_NONANSWER_RE = re.compile(
    r"\b(?:closer looking yields nothing|inspection yields no further|yields nothing further)\b",
    re.IGNORECASE,
)
_CANONICAL_DENIAL_RE = re.compile(
    r"\b(?:find no such|no such (?:thing|person|one)|nothing here matches|"
    r"not among what is actually present|no such guard|there is no guard here)\b",
    re.IGNORECASE,
)
_LITERAL_STEP_RE = re.compile(
    r"\b(?:foot|feet)\b[^.!?]{0,40}\bstep\b"
    r"|\bplace(?:s|d)?\s+(?:your|a|the)\s+foot\b"
    r"|\bworn step\b",
    re.IGNORECASE,
)
_EXPLICIT_NONANSWER_RE = re.compile(
    r"\b(?:no one(?: at hand| here)? answers|nobody answers|the question hangs|"
    r"hangs in the noise|never tightens into a single clear voice|"
    r"without anyone stepping forward|no answer was (?:given|provided)|"
    r"does not answer|did not answer|no one answers the question)\b",
    re.IGNORECASE,
)
_REPEAT_SPLICE_RE = re.compile(
    r"sharpens when you look again|still competes for notice|holds the eye, while|"
    r"doesn'?t let the moment go slack|reads clearer while|keeps pulling the eye",
    re.IGNORECASE,
)
_DEVOICE_RE = re.compile(
    r"^(?:i can tell(?: you)? that|i(?:'ll| will) tell you that|i can say that)\s+",
    re.IGNORECASE,
)
_PRICE_BLOCK_RE = re.compile(
    r"\b(?:copper|coppers|silver|gold)\b|\b(?:costs?|priced?|sells?\s+for)\b",
    re.IGNORECASE,
)
_REDIRECT_BLOCK_RE = re.compile(
    r"\b(?:speak|talk)\s+to\s+(?:the\s+)?[A-Za-z]|\bask\s+the\s+[A-Za-z]|"
    r"\b(?:go|head)\s+to\s+(?:the\s+)?[A-Za-z]",
    re.IGNORECASE,
)
_ATMOSPHERE_WORDS = frozenset(
    {
        "rain", "crowd", "murmur", "whisper", "eye", "noise", "moment", "weather",
        "watcher", "refugee", "muddy", "ragged", "threadbare", "hushed", "cluster",
        "glance", "voice", "line", "soggy", "nearby", "quiet", "still", "passing",
    }
)
_REFUSAL_FRAME_RE = re.compile(
    r"\b(?:will not|won't|refuse|refuses|refused|not going to)\b",
    re.IGNORECASE,
)
_ABOUT_TARGET_RE = re.compile(
    r"\b(?:about|regarding|concerning)\s+(?:the\s+|a\s+|an\s+)?(?P<target>[a-z0-9_]+(?:\s+[a-z0-9_]+){0,4})",
    re.IGNORECASE,
)
_DOC_ALIASES = frozenset({"sheet", "notice", "posting", "placard"})
_TARGET_STOP = frozenset(
    {
        "the", "a", "an", "of", "on", "to", "and", "or", "it", "its", "this", "that", "over",
        "look", "about", "for", "with", "from", "into", "your", "you",
    }
)
_BOILERPLATE_TERMS = frozenset(
    {
        "inspection", "establishes", "establish", "further", "reliable", "detail", "details",
        "about", "current", "scene", "visible", "already", "apparent", "beyond", "what",
        "this", "that", "there", "here", "from", "with", "have", "been", "does", "did",
        "request", "requested", "information", "another", "source", "route", "carry",
        "talk", "heard", "verify", "cannot", "could", "would", "will", "not", "none",
    }
)
_LONG_VISUAL_RE = re.compile(r"\b(?:stands?|watchers?|crowd|street|gate|square)\b", re.IGNORECASE)
_SCENE_FRAME_RE = re.compile(
    r"\b(?:the new ground shows itself|shows itself|frame the|fresh worry tracks along the posted lines)\b",
    re.IGNORECASE,
)
_EARLIER_CLAIM_RE = re.compile(
    r"\bearlier\s+(?:claim|wording|remark|statement)\b",
    re.IGNORECASE,
)
_INABILITY_DIMENSION_SPAN_RE = re.compile(
    r"\b(?:cannot|can't|could not|couldn't|no one(?: here)? can|no reliable source can)\s+"
    r"(?:say|tell|verify|swear|establish)\b[^.!?]{0,80}",
    re.IGNORECASE,
)
_GENERIC_OBSERVE_STOCK_RE = re.compile(
    r"\bas you watch the scene\b|\bimmediate read on what is there\b",
    re.IGNORECASE,
)
_ATMOSPHERIC_AVOIDANCE_RE = re.compile(
    r"\bno one\b.{0,180}\bsteps forward\b"
    r"|\bnobody\b.{0,120}\bsteps forward\b"
    r"|\bwatches you carefully\b"
    r"|\bthe gate remains tense\b"
    r"|\bno one at hand answers\b",
    re.IGNORECASE,
)
_ATTRIBUTED_SPEECH_RE = re.compile(
    r'"|\b(?:says|said|replies|replied|asks|asked|refuses|refused)\b',
    re.IGNORECASE,
)
_UNRELATED_NARRATED_FACT_RE = re.compile(
    r"\b(?:was|were)\s+(?:last\s+)?seen\b",
    re.IGNORECASE,
)


def _clean(value: Any, *, limit: int = 180) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:limit]


# Display, logs, and prompts may keep a short excerpt. Contract interpretation may not.
PROVENANCE_EXCERPT_LIMIT = 240


def semantic_input_text(value: Any) -> str:
    """Whitespace-normalized player utterance. No character cap.

    Storage and display bounds are applied later, as a provenance excerpt.
    """
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())


def bounded_provenance_excerpt(text: str | None, *, limit: int = PROVENANCE_EXCERPT_LIMIT) -> str:
    """Bounded copy for logs and prompts. Not the semantic input."""
    return semantic_input_text(text)[:limit]


@dataclass(frozen=True)
class TargetRef:
    type: str
    id_or_text: str | None
    source: str


@dataclass(frozen=True)
class DiscoursePointer:
    type: str
    id: str | None
    label: str | None
    source_turn: int | None


@dataclass(frozen=True)
class ResolutionContract:
    contract_id: str
    turn_index: int | None
    request_kind: str
    operation: str
    target_ref: TargetRef | None
    interlocutor_id: str | None
    conversational_subject: str | None
    dimension: str | None
    dimensions: tuple[str, ...]
    expected_resolution: str
    epistemic_mode: str
    discourse_ref: DiscoursePointer | None
    referent_provenance: str
    ambiguous: bool
    raw_input: str
    construction: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["dimensions"] = list(self.dimensions)
        return payload


def contract_mapping_from_resolution(resolution: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(resolution, Mapping):
        return {}
    metadata = resolution.get("metadata")
    contract = metadata.get("resolution_contract") if isinstance(metadata, Mapping) else None
    return dict(contract) if isinstance(contract, Mapping) else {}


def contract_requests_consequential_protection(contract: Mapping[str, Any] | None) -> bool:
    return isinstance(contract, Mapping) and contract.get("epistemic_mode") == EPISTEMIC_CONSEQUENTIAL


def _contract_id(turn_index: int | None, text: str) -> str:
    raw = f"{turn_index if turn_index is not None else ''}|{text.lower()}"
    return "rc_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _dimensions(text: str) -> tuple[str, ...]:
    found: list[tuple[int, str]] = []
    for name, pattern in _DIMENSION_PATTERNS:
        match = pattern.search(text)
        if match:
            found.append((match.start(), name))
    found.sort()
    ordered: list[str] = []
    for _, name in found:
        if name not in ordered:
            ordered.append(name)
    if DIM_SOURCE in ordered and DIM_LOCATION in ordered and _SOURCE_RE.search(text):
        ordered = [name for name in ordered if name != DIM_LOCATION]
    perceptual_sound = re.search(r"\b(?:sounds?|listen(?:ing|ed)?|hearing)\b", text, re.IGNORECASE)
    if DIM_SOUND in ordered and _SOURCE_RE.search(text) and not perceptual_sound:
        ordered = [name for name in ordered if name != DIM_SOUND]
    if DIM_SOUND in ordered and DIM_CONFIDENCE in ordered and _CONFIDENCE_RE.search(text):
        ordered = [name for name in ordered if name != DIM_SOUND]
    if DIM_APPEARANCE in ordered and DIM_LOCATION in ordered and re.search(
        r"\b(?:what can i see|can i see)\b", text, re.IGNORECASE
    ):
        ordered = [name for name in ordered if name != DIM_LOCATION]
    if DIM_APPEARANCE in ordered and set(ordered) & {DIM_WEAR, DIM_USE, DIM_CHANGE, DIM_SMELL, DIM_SOUND}:
        ordered = [name for name in ordered if name != DIM_APPEARANCE] + [DIM_APPEARANCE]
    # Content is what was said. Source, confidence, time, and purpose keep their own questions.
    if DIM_CONTENT in ordered and DIM_SOURCE in ordered and _SOURCE_RE.search(text):
        ordered = [name for name in ordered if name != DIM_CONTENT]
    if DIM_CONTENT in ordered and DIM_CONFIDENCE in ordered and _CONFIDENCE_RE.search(text):
        ordered = [name for name in ordered if name != DIM_CONTENT]
    if DIM_CONTENT in ordered and DIM_TIME in ordered and re.match(
        r"\s*(?:and\s+|but\s+|so\s+|then\s+)?(?:when|how long|how recently)\b",
        text,
        re.IGNORECASE,
    ):
        ordered = [name for name in ordered if name != DIM_CONTENT]
    if DIM_CONTENT in ordered and DIM_USE in ordered and _PURPOSE_QUESTION_RE.search(text):
        ordered = [name for name in ordered if name != DIM_CONTENT]
    if DIM_CONTENT in ordered and _CONTENT_REQUEST_RE.search(text) and not _PURPOSE_QUESTION_RE.search(text):
        ordered = [name for name in ordered if name not in {DIM_USE, DIM_WEAR}]
    if DIM_CONTENT in ordered:
        ordered = [DIM_CONTENT] + [name for name in ordered if name != DIM_CONTENT]
    return tuple(ordered)


_OBLIGATORY_DIMENSIONS = frozenset(
    {DIM_CONFIDENCE, DIM_USE, DIM_TIME, DIM_SOURCE, DIM_LOCATION, DIM_CONTENT, DIM_NEXT_STEP, DIM_INTERPRETATION}
)


def first_obvious_dimension(text: str) -> str | None:
    """A dimension the utterance itself asks for. None when the request is dimensionless."""
    for name in _dimensions(text):
        if name in _OBLIGATORY_DIMENSIONS:
            return name
    return None


def _lock_player_dimension(text: str, dimensions: tuple[str, ...]) -> tuple[str, ...]:
    """Keep the dimension the player's words asked for when binding does not supply one."""
    obvious = first_obvious_dimension(text)
    if obvious not in CLAIM_DIMENSIONS:
        return dimensions
    kept = list(dimensions)
    if obvious == DIM_SOURCE and _SOURCE_RE.search(text) and not _CONTENT_REQUEST_RE.search(text):
        kept = [item for item in kept if item != DIM_CONTENT]
    if obvious not in kept:
        kept.insert(0, obvious)
    else:
        kept = [obvious, *[item for item in kept if item != obvious]]
    return tuple(kept)


def _mentioned_in_text(candidate: str, player_text: str) -> bool:
    words = [word for word in re.split(r"[^a-z0-9]+", candidate.lower()) if len(word) > 2]
    raw = player_text.lower()
    return bool(words) and all(word in raw for word in words)


def _known_content_id(candidate: str, focus: Mapping[str, Any]) -> bool:
    """A parser id may name a focused object, claim, or lead. An interlocutor id may not."""
    interlocutor = focus.get(SLOT_INTERLOCUTOR) if isinstance(focus.get(SLOT_INTERLOCUTOR), Mapping) else {}
    if candidate and candidate == _clean(interlocutor.get("id"), limit=80):
        return False
    for name in (SLOT_INSPECTED, SLOT_CLAIM, SLOT_LEAD):
        slot = focus.get(name) if isinstance(focus.get(name), Mapping) else {}
        if candidate and candidate == _clean(slot.get("id"), limit=80):
            return True
    return False


def _echoes_utterance(candidate: str, player_text: str) -> bool:
    """A parser label that repeats the utterance is not a resolved nominal target."""
    cand = semantic_input_text(candidate).lower().strip(" ?.!")
    raw = semantic_input_text(player_text).lower().strip(" ?.!")
    if not cand or not raw:
        return False
    if cand == raw:
        return True
    return len(cand) >= 24 and (cand in raw or raw in cand)


def _explicit_target_capture(text: str) -> tuple[str, str, bool]:
    """Return the raw span, which pattern produced it, and whether it had a determiner.

    The span is not a canonical identity. Callers must canonicalize or abstain.
    """
    named = (
        ("used_for", _USED_FOR_TARGET_RE),
        ("look_over", _LOOK_OVER_FORWARD_TARGET_RE),
        ("look_over", _LOOK_OVER_TARGET_RE),
        ("what_does", _WHAT_DOES_RE),
        ("verb_object", _EXPLICIT_TARGET_RE),
        ("verb_object", _SMELL_TARGET_RE),
        ("preposition", _AT_OBJECT_RE),
    )
    for kind, pattern in named:
        match = pattern.search(text)
        if not match:
            continue
        target = _clean(match.group("target"), limit=80).strip(" \"'")
        target = re.sub(r"\s+\b(?:like|closely|carefully)\b$", "", target, flags=re.IGNORECASE).strip()
        if not target or _PRONOUN_TARGET_RE.match(target):
            continue
        has_determiner = bool(re.search(r"\b(?:the|a|an)\b", match.group(0), re.IGNORECASE))
        return target, kind, has_determiner
    return "", "none", False


def _explicit_target(text: str) -> str:
    target, _kind, _has_determiner = _explicit_target_capture(text)
    return target


def _named_event(text: str) -> str:
    match = _NAMED_EVENT_RE.search(text or "")
    if not match:
        return ""
    event = _clean(match.group("event"), limit=80)
    if event.lower() in {"that", "this", "it", "them", "they", "him", "her"}:
        return ""
    return event


def _slot_mentions(slot: Mapping[str, Any], event: str) -> bool:
    label = f"{slot.get('label') or ''} {slot.get('id') or ''}".lower()
    words = [word for word in re.findall(r"[a-z]+", event.lower()) if len(word) > 2]
    return bool(words) and all(word in label for word in words)


def _is_clarification_text(text: str) -> bool:
    if not _CLARIFICATION_TEXT_RE.search(text or ""):
        return False
    return "?" in str(text or "") or bool(re.search(r"\b(?:asks?|asking)\b", text or "", re.IGNORECASE))


def _offers_alternatives(text: str) -> bool:
    return bool(_ALTERNATIVE_CLARIFICATION_RE.search(text or ""))


def _reference_unbound(contract: Mapping[str, Any]) -> bool:
    if contract.get("ambiguous") or contract.get("expected_resolution") == EXPECT_CLARIFICATION:
        return True
    if str(contract.get("referent_provenance") or "") in {PROVENANCE_AMBIGUOUS, PROVENANCE_UNRESOLVED}:
        return True
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    bound = bool(discourse.get("id") or discourse.get("label") or target.get("id_or_text"))
    return not bound


def necessary_clarification(text: str | None, contract: Mapping[str, Any] | None) -> bool:
    """Clarification is necessary only when the referent itself is unresolved."""
    if not isinstance(contract, Mapping) or not _is_clarification_text(str(text or "")):
        return False
    if not _reference_unbound(contract):
        return False
    if contract.get("ambiguous") or contract.get("expected_resolution") == EXPECT_CLARIFICATION:
        return True
    raw = str(contract.get("raw_input") or "")
    if _BARE_TEMPORAL_ANAPHOR_RE.search(raw) and _offers_alternatives(str(text or "")):
        return True
    if str(contract.get("referent_provenance") or "") == PROVENANCE_AMBIGUOUS and _offers_alternatives(str(text or "")):
        return True
    return bool(_offers_alternatives(str(text or "")) and _reference_unbound(contract))


def _inspected_id(focus: Mapping[str, Any]) -> str | None:
    slot = focus.get(SLOT_INSPECTED) if isinstance(focus, Mapping) else None
    if not isinstance(slot, Mapping):
        return None
    return _clean(slot.get("id") or slot.get("label"), limit=80) or None


def _pointer_from_slot(slot_name: str, slot: Mapping[str, Any] | None) -> DiscoursePointer | None:
    if not isinstance(slot, Mapping):
        return None
    kind = {
        SLOT_CLAIM: "claim",
        SLOT_LEAD: "lead",
        SLOT_INSPECTED: "object",
        SLOT_ACTION: "action",
        SLOT_INTERLOCUTOR: "interlocutor",
    }[slot_name]
    return DiscoursePointer(
        type=kind,
        id=_clean(slot.get("id"), limit=80) or None,
        label=_clean(slot.get("label"), limit=160) or None,
        source_turn=slot.get("turn_index") if isinstance(slot.get("turn_index"), int) else None,
    )


def _resolve_referent(
    text: str,
    *,
    dimensions: tuple[str, ...],
    focus: Mapping[str, Any],
    explicit_target: str,
) -> tuple[str, TargetRef | None, DiscoursePointer | None, bool, str]:
    """Return provenance, target, discourse pointer, ambiguity, and why."""
    lead_slot = focus.get(SLOT_LEAD) if isinstance(focus.get(SLOT_LEAD), Mapping) else None
    claim_slot = focus.get(SLOT_CLAIM) if isinstance(focus.get(SLOT_CLAIM), Mapping) else None
    inspected = focus.get(SLOT_INSPECTED) if isinstance(focus.get(SLOT_INSPECTED), Mapping) else None
    action = focus.get(SLOT_ACTION) if isinstance(focus.get(SLOT_ACTION), Mapping) else None
    interlocutor = focus.get(SLOT_INTERLOCUTOR) if isinstance(focus.get(SLOT_INTERLOCUTOR), Mapping) else None

    if _LEAD_RE.search(text):
        pointer = _pointer_from_slot(SLOT_LEAD, lead_slot)
        if pointer is None:
            return (
                PROVENANCE_UNRESOLVED,
                TargetRef("lead", "that lead", PROVENANCE_UNRESOLVED),
                None,
                False,
                "lead_unresolved",
            )
        return (
            PROVENANCE_INHERITED,
            TargetRef("lead", pointer.label or pointer.id, PROVENANCE_INHERITED),
            pointer,
            False,
            "unique_actionable_lead",
        )
    from game.interpretation_proposal import elliptical_probe_dimension, referential_action_shape

    if _REFERENTIAL_ACTION_RE.search(text) or referential_action_shape(text):
        go_there = bool(re.search(r"\bgo\s+there\b", text, re.IGNORECASE))
        candidates: list[tuple[str, Mapping[str, Any]]] = []
        if isinstance(lead_slot, Mapping):
            candidates.append((SLOT_LEAD, lead_slot))
        if isinstance(action, Mapping):
            candidates.append((SLOT_ACTION, action))
        if go_there and isinstance(inspected, Mapping):
            candidates.append((SLOT_INSPECTED, inspected))
        if len(candidates) > 1:
            return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_actionable_referents"
        if len(candidates) == 1:
            slot_name, slot = candidates[0]
            pointer = _pointer_from_slot(slot_name, slot)
            kind = {SLOT_LEAD: "lead", SLOT_ACTION: "action", SLOT_INSPECTED: "place"}[slot_name]
            reason = {
                SLOT_LEAD: "unique_actionable_lead",
                SLOT_ACTION: "previous_action",
                SLOT_INSPECTED: "unique_destination",
            }[slot_name]
            return (
                PROVENANCE_INHERITED,
                TargetRef(kind, pointer.label if pointer else None, PROVENANCE_INHERITED),
                pointer,
                False,
                reason,
            )
        return PROVENANCE_AMBIGUOUS, None, None, True, "no_actionable_referent"
    if elliptical_probe_dimension(text) == "conditional" and not explicit_target:
        pointer = _pointer_from_slot(SLOT_ACTION, action)
        if pointer is None:
            return PROVENANCE_UNRESOLVED, None, None, False, "elliptical_unbound"
        return (
            PROVENANCE_INHERITED,
            TargetRef("action", pointer.label or pointer.id, PROVENANCE_INHERITED),
            pointer,
            False,
            "previous_action",
        )
    if _PRIOR_ACTION_RE.search(text) or DIM_CHANGE in dimensions and re.search(r"\bthat\b", text, re.IGNORECASE):
        pointer = _pointer_from_slot(SLOT_ACTION, action)
        if pointer is None:
            return (
                PROVENANCE_UNRESOLVED,
                TargetRef("action", "prior action", PROVENANCE_UNRESOLVED),
                None,
                False,
                "previous_action_missing",
            )
        return (
            PROVENANCE_INHERITED,
            TargetRef("action", pointer.label or pointer.id, PROVENANCE_INHERITED),
            pointer,
            False,
            "previous_action",
        )
    claimish = bool(set(dimensions) & {DIM_SOURCE, DIM_CONFIDENCE}) or bool(
        re.search(r"\b(?:who told|do you believe|how certain|that claim|what they said)\b", text, re.IGNORECASE)
    )
    if elliptical_probe_dimension(text) in {DIM_SOURCE, DIM_CONFIDENCE, DIM_LOCATION, DIM_TIME}:
        claimish = True
    if not claimish and set(dimensions) & {DIM_LOCATION, DIM_TIME} and _CLAIM_FOLLOWUP_RE.search(text):
        claimish = True
    if DIM_TIME in dimensions and not explicit_target:
        named = _named_event(text)
        temporal_slots: list[tuple[str, Mapping[str, Any]]] = []
        if isinstance(claim_slot, Mapping):
            temporal_slots.append((SLOT_CLAIM, claim_slot))
        if isinstance(inspected, Mapping):
            temporal_slots.append((SLOT_INSPECTED, inspected))
        if isinstance(lead_slot, Mapping):
            temporal_slots.append((SLOT_LEAD, lead_slot))
        if named:
            matched = [pair for pair in temporal_slots if _slot_mentions(pair[1], named)]
            if len(matched) > 1:
                return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_plausible_referents"
            if len(matched) == 1:
                slot_name, slot = matched[0]
                pointer = _pointer_from_slot(slot_name, slot)
                return (
                    PROVENANCE_INHERITED,
                    TargetRef(pointer.type if pointer else "event", pointer.label if pointer else named, PROVENANCE_INHERITED),
                    pointer,
                    False,
                    "named_event",
                )
            return (
                PROVENANCE_EXPLICIT,
                TargetRef("event", named, PROVENANCE_EXPLICIT),
                None,
                False,
                "explicit_event",
            )
        if _BARE_TEMPORAL_ANAPHOR_RE.search(text) and len(temporal_slots) > 1:
            return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_plausible_referents"
    if claimish and not explicit_target:
        pointer = _pointer_from_slot(SLOT_CLAIM, claim_slot)
        if pointer is None:
            return PROVENANCE_UNRESOLVED, TargetRef("claim", None, PROVENANCE_UNRESOLVED), None, False, "claim_unresolved"
        from game.interpretation_proposal import claim_target_identity

        return (
            PROVENANCE_INHERITED,
            TargetRef("claim", claim_target_identity(pointer.label, pointer.id), PROVENANCE_INHERITED),
            pointer,
            False,
            "unique_active_claim",
        )
    if _OR_OBJECT_RE.search(text) and re.search(r"\b(?:say|says|written|read)\b", text, re.IGNORECASE):
        return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_object_referents"
    if _REPEAT_RE.search(text) and not explicit_target:
        rumorish = bool(re.search(r"\b(?:rumou?r|said|claim)\b", text, re.IGNORECASE))
        if isinstance(claim_slot, Mapping) and (rumorish or not isinstance(inspected, Mapping)):
            pointer = _pointer_from_slot(SLOT_CLAIM, claim_slot)
            from game.interpretation_proposal import claim_target_identity

            return (
                PROVENANCE_INHERITED,
                TargetRef(
                    "claim",
                    claim_target_identity(pointer.label if pointer else None, pointer.id if pointer else None),
                    PROVENANCE_INHERITED,
                ),
                pointer,
                False,
                "unique_active_claim",
            )
        if isinstance(claim_slot, Mapping) and isinstance(inspected, Mapping):
            return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_restatement_referents"
        return PROVENANCE_UNRESOLVED, TargetRef("claim", None, PROVENANCE_UNRESOLVED), None, False, "repeat_unresolved"
    if explicit_target and re.search(r"\bor\b", explicit_target, re.IGNORECASE):
        return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_object_referents"
    if explicit_target:
        return (
            PROVENANCE_EXPLICIT,
            TargetRef("object", explicit_target, PROVENANCE_EXPLICIT),
            None,
            False,
            "explicit_current_turn_target",
        )
    if _SCENE_TARGET_RE.search(text) and not _ANAPHOR_RE.search(text):
        return PROVENANCE_EXPLICIT, TargetRef("scene", "current scene", PROVENANCE_EXPLICIT), None, False, "explicit_scene"

    wants_inspected = (
        bool(set(dimensions) & PERCEPTION_DIMENSIONS)
        or _player_inspection(text)
        or DIM_CONTENT in dimensions
    )
    wants_person = bool(re.search(r"\b(?:them|that person|they)\b", text, re.IGNORECASE))
    wants_place = bool(re.search(r"\bthat place\b", text, re.IGNORECASE))
    if (
        set(dimensions) & {DIM_WEAR, DIM_USE, DIM_CHANGE}
        and isinstance(inspected, Mapping)
        and not explicit_target
        and not (_PRIOR_ACTION_RE.search(text) or (DIM_CHANGE in dimensions and re.search(r"\bthat\b", text, re.IGNORECASE)))
    ):
        pointer = _pointer_from_slot(SLOT_INSPECTED, inspected)
        return (
            PROVENANCE_INHERITED,
            TargetRef(str(inspected.get("kind") or "object"), pointer.label if pointer else None, PROVENANCE_INHERITED),
            pointer,
            False,
            "unique_inspected_object",
        )
    if wants_person and interlocutor is not None and not wants_inspected:
        pointer = _pointer_from_slot(SLOT_INTERLOCUTOR, interlocutor)
        return (
            PROVENANCE_INHERITED,
            TargetRef("interlocutor", pointer.label if pointer else None, PROVENANCE_INHERITED),
            pointer,
            False,
            "active_interlocutor",
        )
    if wants_place:
        if inspected is not None and lead_slot is not None:
            return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_place_referents"
        if inspected is not None:
            pointer = _pointer_from_slot(SLOT_INSPECTED, inspected)
            return (
                PROVENANCE_INHERITED,
                TargetRef("place", pointer.label if pointer else None, PROVENANCE_INHERITED),
                pointer,
                False,
                "unique_place",
            )
        if lead_slot is not None:
            pointer = _pointer_from_slot(SLOT_LEAD, lead_slot)
            return (
                PROVENANCE_INHERITED,
                TargetRef("place", pointer.label if pointer else None, PROVENANCE_INHERITED),
                pointer,
                False,
                "unique_actionable_lead",
            )
        return PROVENANCE_UNRESOLVED, TargetRef("place", "that place", PROVENANCE_UNRESOLVED), None, False, "place_unresolved"
    if DIM_CONTENT in dimensions and _OR_OBJECT_RE.search(text) and not explicit_target:
        return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_object_referents"
    if wants_inspected and _ANAPHOR_RE.search(text) and not explicit_target and isinstance(inspected, Mapping):
        if _OR_OBJECT_RE.search(text):
            return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_object_referents"
        pointer = _pointer_from_slot(SLOT_INSPECTED, inspected)
        return (
            PROVENANCE_INHERITED,
            TargetRef(str(inspected.get("kind") or "object"), pointer.label if pointer else None, PROVENANCE_INHERITED),
            pointer,
            False,
            "unique_inspected_object",
        )
    if wants_inspected and _ANAPHOR_RE.search(text) and not explicit_target:
        if inspected is None:
            return PROVENANCE_UNRESOLVED, TargetRef("object", None, PROVENANCE_UNRESOLVED), None, False, "inspected_unresolved"
        pointer = _pointer_from_slot(SLOT_INSPECTED, inspected)
        return (
            PROVENANCE_INHERITED,
            TargetRef(str(inspected.get("kind") or "object"), pointer.label if pointer else None, PROVENANCE_INHERITED),
            pointer,
            False,
            "unique_inspected_object",
        )
    if (
        re.search(r"\bask\b", text, re.IGNORECASE)
        and re.search(r"\b(?:him|her|them)\b", text, re.IGNORECASE)
        and re.search(r"\b(?:it|that|this)\b", text, re.IGNORECASE)
    ):
        objects: list[tuple[str, Mapping[str, Any]]] = []
        if isinstance(inspected, Mapping):
            objects.append((SLOT_INSPECTED, inspected))
        if isinstance(claim_slot, Mapping):
            objects.append((SLOT_CLAIM, claim_slot))
        person = isinstance(interlocutor, Mapping)
        if person and len(objects) == 1:
            slot_name, slot = objects[0]
            pointer = _pointer_from_slot(slot_name, slot)
            kind = "claim" if slot_name == SLOT_CLAIM else str(slot.get("kind") or "object")
            return (
                PROVENANCE_INHERITED,
                TargetRef(kind, pointer.label if pointer else None, PROVENANCE_INHERITED),
                pointer,
                False,
                "multi_reference_bound",
            )
        return PROVENANCE_UNRESOLVED, None, None, False, "partial_reference_binding"
    if _ANAPHOR_RE.search(text) and not explicit_target:
        candidates = [slot for slot in (inspected, claim_slot, lead_slot, interlocutor, action) if isinstance(slot, Mapping)]
        if len(candidates) > 1:
            return PROVENANCE_AMBIGUOUS, None, None, True, "multiple_plausible_referents"
        if len(candidates) == 1:
            slot = candidates[0]
            slot_name = next(
                name
                for name in (SLOT_INSPECTED, SLOT_CLAIM, SLOT_LEAD, SLOT_INTERLOCUTOR, SLOT_ACTION)
                if focus.get(name) is slot
            )
            pointer = _pointer_from_slot(slot_name, slot)
            return (
                PROVENANCE_INHERITED,
                TargetRef(pointer.type if pointer else "object", pointer.label if pointer else None, PROVENANCE_INHERITED),
                pointer,
                False,
                "unambiguous_discourse_referent",
            )
        return PROVENANCE_UNRESOLVED, None, None, False, "no_referent"
    return PROVENANCE_EXPLICIT, None, None, False, "no_anaphor"


def _social_or_inquiry_operation(text: str) -> bool:
    """True when the utterance is still an inquiry, request, or quoted speech.

    Deictic "where are we" and a bare "describe" stay ordinary narration.
    """
    if re.search(r"\bwhere\s+(?:am\s+i|are\s+we)\b|\bwhere\s+is\s+this(?:\s+place)?\b", text, re.IGNORECASE):
        if not re.search(r"\b(?:ask|inquire)\b", text, re.IGNORECASE):
            return False
    if re.search(r"\bdescribe\b", text, re.IGNORECASE) and not re.search(
        r"\b(?:ask|inquire|please)\b|[\"“]",
        text,
    ):
        return False
    return bool(
        re.search(
            r"\?|\b(?:what|who|how|whether|please|ask|inquire|does|is there|can i|will you|"
            r"talk|speak|persuade|convince|tell)\b|[\"“]"
            r"|\bwhere\s+(?:is|are|'s)\s+(?:the|a|an|that|this|you|he|she|they)\b",
            text,
            re.IGNORECASE,
        )
    )


def _player_inspection(text: str) -> bool:
    """Inspection language that governs this turn.

    Search and investigate belong to the existing inspect family. A subordinate
    "before investigating" plan does not. An explicit ask still follows the
    question path in ``_operation``.
    """
    if not _INSPECT_RE.search(text):
        return False
    if not _SUBORDINATE_INVESTIGATION_RE.search(text):
        return True
    stripped = _SUBORDINATE_INVESTIGATION_RE.sub(" ", text)
    return bool(_INSPECT_RE.search(stripped))


def _operation(
    text: str,
    dimensions: tuple[str, ...],
    *,
    action_type: str,
) -> tuple[str, str]:
    if _CLARIFY_RE.search(text):
        return REQUEST_CLARIFICATION, OP_ASK
    if _REPEAT_RE.search(text):
        return REQUEST_INQUIRY, OP_REPEAT
    from game.intent_parser import _declared_matches_passive_interruption_wait

    if _declared_matches_passive_interruption_wait(text):
        return REQUEST_ACTION, OP_ACT
    if _LEAD_RE.search(text):
        return REQUEST_ACTION, OP_FOLLOW
    from game.interpretation_proposal import referential_action_shape

    if _REFERENTIAL_ACTION_RE.search(text) or referential_action_shape(text):
        if re.search(r"\bfollow\b", text, re.IGNORECASE):
            return REQUEST_ACTION, OP_FOLLOW
        return REQUEST_ACTION, OP_ACT
    if _CONFIRM_RE.search(text) or DIM_NEXT_STEP in dimensions and re.search(r"\bconfirm\b", text, re.IGNORECASE):
        return REQUEST_ACTION, OP_CONFIRM
    if _ACTION_REQUEST_RE.search(text):
        return REQUEST_SOCIAL_ACTION, OP_ACT
    if _PHYSICAL_RE.search(text) and not dimensions:
        from game.contract_adjudication_bridge import direct_feasibility_question
        from game.interpretation_proposal import ask_governs_embedded_act

        if not ask_governs_embedded_act(text) and not direct_feasibility_question(text):
            return REQUEST_ACTION, OP_ACT
    if dimensions and set(dimensions) <= PERCEPTION_DIMENSIONS | {DIM_NEXT_STEP}:
        if _PURPOSE_QUESTION_RE.search(text) and not _player_inspection(text):
            return REQUEST_INQUIRY, OP_ASK
        if _player_inspection(text) and not (set(dimensions) & {DIM_SOUND, DIM_SMELL, DIM_APPEARANCE, DIM_CHANGE}):
            return REQUEST_INQUIRY, OP_INSPECT
        if set(dimensions) & PERCEPTION_DIMENSIONS:
            from game.player_commitment import perception_is_supporting

            if perception_is_supporting(text):
                return REQUEST_INQUIRY, OP_ASK
            return REQUEST_INQUIRY, OP_PERCEIVE
    if _player_inspection(text) or action_type in {"observe", "investigate"}:
        if set(dimensions) & {DIM_SOUND, DIM_SMELL, DIM_APPEARANCE, DIM_CHANGE}:
            from game.player_commitment import perception_is_supporting

            if perception_is_supporting(text):
                return REQUEST_INQUIRY, OP_ASK
            return REQUEST_INQUIRY, OP_PERCEIVE
        return REQUEST_INQUIRY, OP_INSPECT
    # A look or watch is perception even when the clause contains who/which.
    # An explicit ask still follows the question path below.
    if _PLAYER_OBSERVE_RE.search(text) and not re.search(
        r"\b(?:ask|inquire|speak(?:ing)?\s+to|talk(?:ing)?\s+to)\b",
        text,
        re.IGNORECASE,
    ):
        return REQUEST_INQUIRY, OP_PERCEIVE
    question = bool(re.search(r"\?|\b(?:what|where|who|how|whether|does|is there|can i|will you)\b", text, re.IGNORECASE))
    if (
        _GENUINE_ACT_RE.search(text)
        and not question
        and not re.search(r"\b(?:ask|inquire)\b", text, re.IGNORECASE)
    ):
        return REQUEST_ACTION, OP_ACT
    if (
        re.search(r"\b(?:go|walk|head|travel|leave|return)\b", text, re.IGNORECASE)
        and not question
        and not re.search(r"\b(?:ask|inquire)\b", text, re.IGNORECASE)
    ):
        return REQUEST_ACTION, OP_ACT
    if action_type in {"interact", "custom", "travel", "attack"} and not question:
        if not (set(dimensions) & PERCEPTION_DIMENSIONS):
            return REQUEST_ACTION, OP_ACT
    from game.interaction_context import _looks_like_local_observation_question

    if _looks_like_local_observation_question(text):
        return REQUEST_INQUIRY, OP_PERCEIVE
    # Questions, requests, and quoted speech stay inquiries.
    # Waits, descriptions, scene-orientation, and unmatched statements do not
    # become asks, so they are not answered as NPC dialogue or incomplete acts.
    if _social_or_inquiry_operation(text):
        return REQUEST_INQUIRY, OP_ASK
    return REQUEST_ACTION, "unresolved"


def construct_resolution_contract(
    *,
    player_text: str | None,
    session: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
    normalized_action: Mapping[str, Any] | None = None,
    scene_id: str | None = None,
    canonical_referents: Sequence[Mapping[str, Any]] | None = None,
    model_interpreter: Any = None,
    visible_turns: Sequence[Mapping[str, Any]] | None = None,
    scene: Mapping[str, Any] | None = None,
) -> ResolutionContract:
    """Build a contract from raw player text and current runtime context."""
    text = semantic_input_text(player_text)
    from game.player_commitment import perception_is_supporting

    supporting_perception = perception_is_supporting(text)
    turn_index = None
    if isinstance(session, Mapping) and isinstance(session.get("turn_counter"), int):
        turn_index = int(session["turn_counter"])
    focus = effective_discourse_focus(session, scene_id=scene_id)
    dimensions = _dimensions(text)
    if supporting_perception and DIM_SOUND in dimensions:
        dimensions = tuple(name for name in dimensions if name != DIM_SOUND)
    from game.interpretation_proposal import elliptical_probe_dimension

    probe = elliptical_probe_dimension(text)
    if probe in CLAIM_DIMENSIONS and probe not in dimensions:
        dimensions = (*dimensions, probe)
    explicit, capture_kind, has_determiner = _explicit_target_capture(text)
    if not explicit and isinstance(normalized_action, Mapping):
        for key in ("target_id", "targetEntityId", "label"):
            action_target = _clean(normalized_action.get(key), limit=80)
            if not action_target or _PRONOUN_TARGET_RE.match(action_target):
                continue
            if _echoes_utterance(action_target, text):
                continue
            if not _mentioned_in_text(action_target, text) and not _known_content_id(action_target, focus):
                continue
            explicit = action_target
            break
    provenance, target, discourse, ambiguous, referent_reason = _resolve_referent(
        text,
        dimensions=dimensions,
        focus=focus,
        explicit_target=explicit,
    )
    action_type = ""
    if isinstance(normalized_action, Mapping):
        action_type = str(normalized_action.get("type") or "").strip().lower()
    request_kind, operation = _operation(text, dimensions, action_type=action_type)
    unresolved_anaphor = provenance == PROVENANCE_UNRESOLVED and bool(_ANAPHOR_RE.search(text))
    clear_claim_question = referent_reason == "claim_unresolved" and bool(set(dimensions) & CLAIM_DIMENSIONS)
    if (ambiguous or unresolved_anaphor) and not clear_claim_question:
        request_kind = REQUEST_CLARIFICATION
        expected = EXPECT_CLARIFICATION
    elif _CONSEQUENTIAL_RE.search(text):
        expected = EXPECT_REFUSAL
    elif operation in {OP_ACT, OP_FOLLOW, OP_CONFIRM}:
        expected = EXPECT_ACTION
    else:
        expected = EXPECT_ANSWER
    if ambiguous:
        provenance = PROVENANCE_AMBIGUOUS
    if _CONSEQUENTIAL_RE.search(text):
        epistemic = EPISTEMIC_CONSEQUENTIAL
    elif set(dimensions) & {DIM_SOURCE, DIM_CONFIDENCE}:
        epistemic = EPISTEMIC_NPC_CLAIM
    elif set(dimensions) & PERCEPTION_DIMENSIONS:
        epistemic = EPISTEMIC_INCIDENTAL
    elif set(dimensions) & CLAIM_DIMENSIONS or re.search(r"\b(?:rumou?rs?|heard)\b", text, re.IGNORECASE):
        epistemic = EPISTEMIC_NPC_CLAIM
    elif operation in {OP_ACT, OP_FOLLOW} and not (set(dimensions) & PERCEPTION_DIMENSIONS):
        epistemic = EPISTEMIC_AUTHORITATIVE
    else:
        epistemic = EPISTEMIC_UNKNOWN

    social = resolution.get("social") if isinstance(resolution, Mapping) else None
    interlocutor = _clean(social.get("npc_id"), limit=80) if isinstance(social, Mapping) else ""
    if not interlocutor:
        slot = focus.get(SLOT_INTERLOCUTOR)
        if isinstance(slot, Mapping) and request_kind in {REQUEST_INQUIRY, REQUEST_SOCIAL_ACTION, REQUEST_CLARIFICATION}:
            if re.search(r"\b(?:you|your|them|they|him|her|he|she)\b", text, re.IGNORECASE) or set(dimensions) & CLAIM_DIMENSIONS:
                interlocutor = _clean(slot.get("id"), limit=80)
    from game.incidental_entity import incidental_catalog_rows, resolve_proposed_interlocutor
    from game.interaction_completion import explicit_discourse_binding

    referent_index = list(canonical_referents) if canonical_referents is not None else None
    if referent_index is not None:
        referent_index.extend(incidental_catalog_rows(session, scene_id or ""))
    binding = explicit_discourse_binding(text, referent_index or (), focus)
    if (
        DIM_CONFIDENCE in dimensions
        and isinstance(discourse, DiscoursePointer)
        and discourse.type == "claim"
        and not binding.get("selected_interlocutor_id")
    ):
        binding = {
            **binding,
            "proposed_nominal": None,
            "proposed_span": None,
            "explicit_new_interlocutor": False,
            "suppress_inherited_interlocutor": False,
        }
    binding_terminal = str(binding.get("terminal_operation") or "")
    referent_open = ambiguous or provenance in {PROVENANCE_UNRESOLVED, PROVENANCE_AMBIGUOUS}
    bound_now = bool(binding.get("selected_interlocutor_id") or binding.get("selected_object_id"))
    if binding_terminal == OP_ASK and operation != OP_ASK and (bound_now or not referent_open):
        operation = OP_ASK
        request_kind = REQUEST_INQUIRY
        expected = EXPECT_ANSWER
    if binding_terminal in {OP_INSPECT, OP_PERCEIVE, OP_ACT} and (bound_now or not referent_open):
        operation = binding_terminal
        if operation == OP_ACT:
            request_kind = REQUEST_ACTION
            expected = EXPECT_ACTION
        else:
            request_kind = REQUEST_INQUIRY
            expected = EXPECT_ANSWER
    if binding.get("selected_interlocutor_id"):
        interlocutor = str(binding.get("selected_interlocutor_id") or "")
        label = str(binding.get("selected_interlocutor_label") or interlocutor)
        target = TargetRef("interlocutor", label, PROVENANCE_EXPLICIT)
        discourse = DiscoursePointer(type="interlocutor", id=interlocutor, label=label, source_turn=None)
        provenance = PROVENANCE_EXPLICIT
        ambiguous = False
        explicit = label
        referent_reason = "explicit_current_turn_interlocutor"
    elif binding.get("suppress_inherited_interlocutor"):
        if isinstance(discourse, DiscoursePointer) and discourse.type == "interlocutor":
            discourse = None
        if isinstance(target, TargetRef) and getattr(target, "type", "") == "interlocutor":
            target = None
        interlocutor = ""
        if provenance == PROVENANCE_INHERITED:
            provenance = PROVENANCE_EXPLICIT
        referent_reason = "explicit_interlocutor_rejected"
    if binding.get("selected_object_id") and binding_terminal in {OP_INSPECT, OP_PERCEIVE}:
        operation = binding_terminal
        request_kind = REQUEST_INQUIRY
        expected = EXPECT_ANSWER
        object_label = str(binding.get("selected_object_label") or binding.get("selected_object_id") or "")
        target = TargetRef("object", object_label, PROVENANCE_EXPLICIT)
        discourse = DiscoursePointer(
            type="object",
            id=str(binding.get("selected_object_id") or ""),
            label=object_label,
            source_turn=None,
        )
        provenance = PROVENANCE_EXPLICIT
        explicit = object_label
        ambiguous = False
        if binding.get("suppress_inherited_interlocutor"):
            interlocutor = ""
        referent_reason = "explicit_current_turn_target"
    if binding.get("ambiguous_addressee") and not binding.get("selected_interlocutor_id"):
        ambiguous = True
        referent_reason = "ambiguous_addressee"
    selected_source = ""
    if binding.get("selected_interlocutor_id") and referent_index is not None:
        for row in referent_index:
            if str(row.get("id") or "") == str(binding.get("selected_interlocutor_id") or ""):
                selected_source = str(row.get("source") or "")
                break
    selected_incidental = selected_source == "bounded_incidental" or str(
        binding.get("selected_interlocutor_id") or ""
    ).startswith("inc_")
    entity_binding: dict[str, Any] = {
        "status": "unresolved",
        "entity_class": "ambiguous_unresolved",
        "proposed_interlocutor": binding.get("proposed_nominal") or None,
        "proposed_span": binding.get("proposed_span") or None,
        "bound_interlocutor_id": None,
        "entity_id": None,
        "label": None,
        "explicit_new_interlocutor": bool(binding.get("explicit_new_interlocutor")),
        "authority_reasons": [],
        "claim_binding": (
            "unresolved"
            if referent_reason == "claim_unresolved"
            else "bound"
            if referent_reason == "unique_active_claim"
            else "none"
        ),
    }
    if binding.get("selected_interlocutor_id"):
        entity_binding.update(
            {
                "status": "bound_incidental" if selected_incidental else "bound_canonical",
                "entity_class": "permitted_bounded_incidental" if selected_incidental else "canonical_established",
                "bound_interlocutor_id": binding.get("selected_interlocutor_id"),
                "entity_id": binding.get("selected_interlocutor_id") if selected_incidental else None,
                "label": binding.get("selected_interlocutor_label"),
                "authority_reasons": ["identity:established"],
            }
        )
    elif (
        binding.get("proposed_nominal")
        and not binding.get("ambiguous_addressee")
        and not binding.get("selected_object_id")
    ):
        decision = resolve_proposed_interlocutor(
            str(binding.get("proposed_nominal") or ""),
            str(binding.get("proposed_span") or ""),
            scene=scene,
            session=session,
            scene_id=str(scene_id or ""),
            catalog=referent_index or (),
        )
        entity_binding.update(decision)
        if decision.get("status") == "bound_incidental":
            interlocutor = str(decision.get("entity_id") or "")
            label = str(decision.get("label") or interlocutor)
            target = TargetRef("interlocutor", label, PROVENANCE_EXPLICIT)
            discourse = DiscoursePointer(type="interlocutor", id=interlocutor, label=label, source_turn=None)
            provenance = PROVENANCE_EXPLICIT
            ambiguous = False
            explicit = label
            referent_reason = "bounded_incidental_interlocutor"
            row = decision.get("catalog_row")
            if isinstance(row, Mapping):
                if referent_index is None:
                    referent_index = [dict(row)]
                else:
                    referent_index.append(dict(row))
            if binding_terminal == OP_ASK or re.search(r"\b(?:ask|inquire)\b", text, re.IGNORECASE):
                operation = OP_ASK
                request_kind = REQUEST_INQUIRY
                expected = EXPECT_ANSWER
        else:
            interlocutor = ""
            if isinstance(discourse, DiscoursePointer) and discourse.type == "interlocutor":
                discourse = None
            if isinstance(target, TargetRef) and getattr(target, "type", "") == "interlocutor":
                target = None
            if decision.get("status") == "rejected_consequential":
                epistemic = EPISTEMIC_CONSEQUENTIAL
                expected = EXPECT_REFUSAL
                referent_reason = "rejected_consequential_entity"
            else:
                expected = EXPECT_CLARIFICATION
                referent_reason = "incidental_entity_" + str(decision.get("status") or "unresolved")
            if binding_terminal == OP_ASK or re.search(r"\b(?:ask|inquire|speak|talk)\b", text, re.IGNORECASE):
                operation = OP_ASK
                request_kind = REQUEST_INQUIRY
    elif binding.get("ambiguous_addressee"):
        entity_binding.update(
            {
                "status": "ambiguous",
                "entity_class": "ambiguous_unresolved",
                "explicit_new_interlocutor": True,
                "authority_reasons": ["proposal:ambiguous"],
            }
        )
        interlocutor = ""
    active_slot = focus.get(SLOT_INTERLOCUTOR) if isinstance(focus.get(SLOT_INTERLOCUTOR), Mapping) else {}
    active_id = _clean(active_slot.get("id"), limit=80) if isinstance(active_slot, Mapping) else ""
    continuing_person = bool(re.search(r"\b(?:you|your|he|she|him|her)\b", text, re.IGNORECASE))
    if (
        ambiguous
        and active_id
        and continuing_person
        and not binding.get("suppress_inherited_interlocutor")
        and not binding.get("explicit_new_interlocutor")
        and not binding.get("selected_object_id")
        and str(binding.get("selected_interlocutor_id") or "") in {"", active_id}
    ):
        ambiguous = False
        interlocutor = interlocutor or active_id
        request_kind = REQUEST_INQUIRY
        expected = EXPECT_ANSWER
        if operation == "unresolved":
            operation = OP_ASK
        if not isinstance(discourse, DiscoursePointer):
            discourse = DiscoursePointer(
                type="interlocutor",
                id=active_id,
                label=_clean(active_slot.get("label"), limit=120) or active_id,
                source_turn=None,
            )
            provenance = PROVENANCE_INHERITED
            referent_reason = "active_interlocutor"
    subject = None
    if isinstance(discourse, DiscoursePointer) and discourse.type == "claim" and discourse.label:
        subject = discourse.label
    elif isinstance(target, TargetRef) and target.id_or_text:
        subject = target.id_or_text
    elif dimensions:
        subject = None
    else:
        subject = text or None
    cues = [name for name in dimensions]
    if _REFERENTIAL_ACTION_RE.search(text) or _LEAD_RE.search(text):
        cues.append("referential_action")
    if _PRONOUN_CUE_RE.search(text):
        cues.append("pronoun")
    referent_slot = None
    if provenance == PROVENANCE_EXPLICIT and isinstance(target, TargetRef):
        referent_slot = "explicit_target"
    elif isinstance(discourse, DiscoursePointer):
        referent_slot = {
            "claim": SLOT_CLAIM,
            "lead": SLOT_LEAD,
            "object": SLOT_INSPECTED,
            "action": SLOT_ACTION,
            "interlocutor": SLOT_INTERLOCUTOR,
            "place": SLOT_INSPECTED if referent_reason == "unique_place" else SLOT_LEAD,
        }.get(discourse.type)
    from game.interpretation_proposal import (
        OP_UNRESOLVED,
        REASON_CONFLICTING_OPERATIONS,
        REASON_INCOMPLETE_SEMANTICS,
        REASON_INSUFFICIENT_DISCOURSE,
        REASON_MALFORMED_SPAN,
        REASON_TARGET_NOT_CANONICAL,
        REASON_UNRESOLVED_COMPOUND,
        SOURCE_DISCOURSE,
        SOURCE_FAST_PATH,
        SOURCE_MODEL,
        STATUS_ABSTAINED,
        STATUS_VALIDATED,
        InterpretationProposal,
        export_referent_index,
        fast_path_operation_families,
        operation_conflict,
        proposal_from_mapping,
        claim_target_identity,
        span_is_malformed,
        structural_inspection_subject,
        validate_interpretation_proposal,
    )
    from game.semantic_interpreter import bump_interpretation_telemetry

    families = fast_path_operation_families(text)
    conflict = operation_conflict(families, text)
    if (
        explicit
        and structural_inspection_subject(
            explicit,
            capture_kind=capture_kind,
            operation=operation,
            raw_input=text,
        )
        and referent_reason in {"target_not_canonical", "inspected_unresolved"}
    ):
        target = TargetRef("resolution_subject", explicit, PROVENANCE_EXPLICIT)
        discourse = None
        provenance = PROVENANCE_EXPLICIT
        ambiguous = False
        referent_reason = "explicit_resolution_subject"
        request_kind = REQUEST_INQUIRY
        expected = EXPECT_ANSWER
        subject = explicit
    inherited_id = None
    if isinstance(discourse, DiscoursePointer) and discourse.id:
        inherited_id = discourse.id
    elif isinstance(target, TargetRef) and provenance == PROVENANCE_INHERITED:
        inherited_id = target.id_or_text
    raw_target = explicit or None
    if conflict:
        raw_target = explicit or None
    proposal_source = SOURCE_DISCOURSE if provenance == PROVENANCE_INHERITED and not explicit else SOURCE_FAST_PATH
    proposal = InterpretationProposal(
        raw_input=text,
        source=proposal_source,
        primary_operation=None if conflict else operation,
        supporting_operations=families if conflict else (),
        raw_target_text=raw_target,
        target_capture=capture_kind,
        has_determiner=has_determiner,
        interlocutor_id=interlocutor or None,
        dimension=dimensions[0] if dimensions else None,
        dimensions=dimensions,
        expected_resolution=expected,
        referenced_inspected_id=inherited_id if provenance == PROVENANCE_INHERITED else None,
        ambiguous=bool(ambiguous),
        operation_conflict=conflict,
        clarification_required=bool(ambiguous or (provenance == PROVENANCE_UNRESOLVED and _ANAPHOR_RE.search(text))),
    )
    if explicit and span_is_malformed(explicit) and not conflict:
        proposal = InterpretationProposal(
            raw_input=text,
            source=SOURCE_FAST_PATH,
            primary_operation=operation,
            raw_target_text=explicit,
            target_capture=capture_kind,
            has_determiner=has_determiner,
            dimension=dimensions[0] if dimensions else None,
            dimensions=dimensions,
            referenced_inspected_id=_inspected_id(focus),
            operation_conflict=False,
        )
    validation = validate_interpretation_proposal(
        proposal,
        discourse_focus=focus,
        canonical_referents=referent_index if referent_index is not None else canonical_referents,
    )
    fast_path_status = validation.status
    fast_path_reason = validation.reason
    interpreter_invoked = False
    interpreter_rejected = False
    clarification_after_model = False
    interpretation_api_calls = 0
    interpreter_error = None
    if (
        validation.status == STATUS_ABSTAINED
        and validation.model_interpretation_appropriate
        and model_interpreter is not None
    ):
        candidates = [row.as_dict() for row in export_referent_index(focus, canonical_referents)]
        try:
            interpreted = model_interpreter(
                {
                    "raw_input": text,
                    "abstention_reason": validation.reason,
                    "candidates": candidates,
                    "discourse_focus": focus_summary(focus),
                    "visible_turns": [dict(turn) for turn in (visible_turns or []) if isinstance(turn, Mapping)],
                }
            )
        except Exception as exc:  # noqa: BLE001 - interpreter failures stay non-authoritative
            interpreted = {"status": "failed", "reason": type(exc).__name__, "api_calls": 0}
        if isinstance(interpreted, Mapping) and "status" not in interpreted and (
            "primary_operation" in interpreted or interpreted.get("clarification_required") is True
        ):
            interpreted = {"status": "proposed", "proposal": dict(interpreted), "api_calls": 0}
        if not isinstance(interpreted, Mapping) or interpreted.get("status") == "skipped":
            interpreted = interpreted if isinstance(interpreted, Mapping) else {"status": "failed", "api_calls": 0}
        else:
            interpreter_invoked = True
            interpretation_api_calls = int(interpreted.get("api_calls") or 0)
            proposal_payload = interpreted.get("proposal") if interpreted.get("status") == "proposed" else None
            if not isinstance(proposal_payload, Mapping):
                interpreter_rejected = True
                clarification_after_model = True
                interpreter_error = str(interpreted.get("reason") or "interpretation_failed")
            else:
                model_proposal = proposal_from_mapping({**dict(proposal_payload), "raw_input": text, "source": SOURCE_MODEL})
                model_validation = validate_interpretation_proposal(
                    model_proposal,
                    discourse_focus=focus,
                    canonical_referents=referent_index if referent_index is not None else canonical_referents,
                )
                if model_validation.status == STATUS_VALIDATED and not model_proposal.ambiguous and not model_proposal.clarification_required:
                    proposal = model_proposal
                    validation = model_validation
                    operation = model_validation.authoritative_operation or OP_ASK
                    conflict = False
                    ambiguous = False
                    if operation in {OP_ASK, OP_INSPECT, OP_PERCEIVE, OP_REPEAT}:
                        request_kind = REQUEST_INQUIRY
                        expected = EXPECT_ANSWER
                    elif operation in {OP_ACT, OP_FOLLOW, OP_CONFIRM}:
                        request_kind = REQUEST_ACTION
                        expected = EXPECT_ACTION
                    if proposal.interlocutor_id and entity_binding.get("status") not in {
                        "bound_incidental",
                        "bound_canonical",
                    }:
                        interlocutor = proposal.interlocutor_id
                    known_dimensions = {
                        DIM_APPEARANCE,
                        DIM_SOUND,
                        DIM_SMELL,
                        DIM_WEAR,
                        DIM_USE,
                        DIM_CHANGE,
                        DIM_SOURCE,
                        DIM_CONFIDENCE,
                        DIM_LOCATION,
                        DIM_TIME,
                        DIM_NEXT_STEP,
                        DIM_CONTENT,
                        DIM_INTERPRETATION,
                    }
                    chosen = [item for item in (proposal.dimension, *proposal.dimensions) if item in known_dimensions]
                    if chosen:
                        dimensions = tuple(dict.fromkeys(chosen))
                    if _CONSEQUENTIAL_RE.search(text):
                        epistemic = EPISTEMIC_CONSEQUENTIAL
                    elif set(dimensions) & CLAIM_DIMENSIONS:
                        epistemic = EPISTEMIC_NPC_CLAIM
                    elif operation in {OP_INSPECT, OP_PERCEIVE}:
                        epistemic = EPISTEMIC_INCIDENTAL
                    elif operation in {OP_ACT, OP_FOLLOW}:
                        epistemic = EPISTEMIC_AUTHORITATIVE
                else:
                    interpreter_rejected = True
                    clarification_after_model = True
                    interpreter_error = model_validation.reason or "rejected_proposal"
    if (
        validation.status == STATUS_VALIDATED
        and validation.authoritative_operation
        and validation.authoritative_operation != operation
        and not conflict
    ):
        operation = validation.authoritative_operation
    # Missing discourse for an incidental anaphor keeps the lexical operation.
    # That abstention still blocks discourse commit. A bad target or an
    # operation conflict replaces the contract with an unresolved result.
    left_object = bool(re.search(r"\b(?:leave|leaving|ignore|ignoring|forget)\s+(?:it|that|this|the)\b", text, re.IGNORECASE))
    explicit_ask = bool(binding.get("selected_interlocutor_id")) and operation == OP_ASK
    subject_gap_only = validation.reason == REASON_INCOMPLETE_SEMANTICS and set(validation.failed_fields) <= {
        "conversational_subject",
        "interlocutor",
    }
    genuine_act = bool(_GENUINE_ACT_RE.search(text)) and not re.search(
        r"\b(?:ask|inquire|whether)\b|\?",
        text,
    )
    keep_act = genuine_act and validation.reason in {REASON_TARGET_NOT_CANONICAL, REASON_MALFORMED_SPAN}
    player_asked = bool(re.search(r"\b(?:ask|inquire)\b|\bwho\s+(?:told|said)\b|\?", text, re.IGNORECASE))
    preserve_intent = not conflict and validation.reason not in {
        REASON_CONFLICTING_OPERATIONS,
        REASON_UNRESOLVED_COMPOUND,
    } and (
        entity_binding.get("status") == "bound_incidental"
        or (
            player_asked
            and (
                bool(entity_binding.get("explicit_new_interlocutor"))
                or first_obvious_dimension(text) in CLAIM_DIMENSIONS
            )
        )
    )
    lexical_operation = operation
    if validation.status == STATUS_ABSTAINED and validation.reason != REASON_INSUFFICIENT_DISCOURSE and not (
        left_object and explicit_ask and subject_gap_only
    ) and not keep_act and not preserve_intent:
        target = None
        discourse = None
        ambiguous = True
        provenance = PROVENANCE_AMBIGUOUS if validation.reason == "ambiguous_referent" else PROVENANCE_UNRESOLVED
        request_kind = REQUEST_CLARIFICATION
        expected = EXPECT_CLARIFICATION
        operation = OP_UNRESOLVED
        subject = None
        referent_slot = None
        referent_reason = validation.reason or referent_reason
        # Inspection and perception survive a bad target span. Binding failure
        # must not turn a look or a listen into clarification.
        if lexical_operation in {OP_INSPECT, OP_PERCEIVE} and not conflict:
            operation = lexical_operation
            request_kind = REQUEST_INQUIRY
            expected = EXPECT_ANSWER
    elif validation.canonical_target_label and validation.canonical_basis:
        label = validation.canonical_target_label
        shown = label
        if validation.canonical_target_type == "claim":
            shown = claim_target_identity(label, validation.canonical_target_id) or label
        target = TargetRef(validation.canonical_target_type or "object", shown, provenance)
        if validation.canonical_basis == "discourse" and inherited_id:
            discourse = discourse if isinstance(discourse, DiscoursePointer) else None
        elif validation.canonical_target_id and validation.canonical_basis != "unscoped_player_nominal":
            discourse = DiscoursePointer(
                type=validation.canonical_target_type or "object",
                id=validation.canonical_target_id,
                label=label,
                source_turn=None,
            )
            provenance = PROVENANCE_EXPLICIT
        subject = label
    if proposal.source == SOURCE_MODEL and validation.status == STATUS_VALIDATED:
        if validation.canonical_target_id and validation.canonical_basis != "unscoped_player_nominal":
            label = validation.canonical_target_label or validation.canonical_target_id
            target = TargetRef(validation.canonical_target_type or "object", label, PROVENANCE_EXPLICIT)
            discourse = DiscoursePointer(
                type=validation.canonical_target_type or "object",
                id=validation.canonical_target_id,
                label=label,
                source_turn=None,
            )
            provenance = PROVENANCE_INHERITED if validation.canonical_basis == "discourse" else PROVENANCE_EXPLICIT
            if operation != OP_ASK:
                subject = label
            if validation.canonical_target_type == "claim":
                target = TargetRef(
                    "claim",
                    claim_target_identity(label, validation.canonical_target_id),
                    PROVENANCE_INHERITED if validation.canonical_basis == "discourse" else PROVENANCE_EXPLICIT,
                )
            elif validation.canonical_target_type == "interlocutor" and operation == OP_ASK:
                interlocutor = validation.canonical_target_id
        else:
            target = None
            discourse = None
            provenance = PROVENANCE_EXPLICIT
        if proposal.conversational_subject and (operation == OP_ASK or not subject):
            subject = proposal.conversational_subject
    if isinstance(session, dict):
        bump_interpretation_telemetry(
            session,
            fast_path_success=1 if fast_path_status == STATUS_VALIDATED else 0,
            fast_path_abstention=1 if fast_path_status == STATUS_ABSTAINED else 0,
            model_interpreter_invoked=1 if interpreter_invoked else 0,
            proposal_accepted=1 if interpreter_invoked and validation.status == STATUS_VALIDATED else 0,
            proposal_rejected=1 if interpreter_rejected else 0,
            clarification_after_model=1 if clarification_after_model else 0,
            interpretation_api_calls=interpretation_api_calls,
        )
    dimensions = _lock_player_dimension(text, dimensions)
    if DIM_SOURCE in dimensions and epistemic != EPISTEMIC_CONSEQUENTIAL:
        epistemic = EPISTEMIC_NPC_CLAIM
    if entity_binding.get("status") in {"bound_incidental", "bound_canonical"} and entity_binding.get(
        "explicit_new_interlocutor"
    ):
        interlocutor = str(entity_binding.get("bound_interlocutor_id") or interlocutor or "")
        ambiguous = False
        if entity_binding.get("status") == "bound_incidental" and operation == "unresolved":
            operation = OP_ASK
            request_kind = REQUEST_INQUIRY
            expected = EXPECT_ANSWER
    elif entity_binding.get("explicit_new_interlocutor") and entity_binding.get("status") in {
        "unresolved",
        "ambiguous",
        "rejected_consequential",
    }:
        interlocutor = ""
        if player_asked and operation == "unresolved" and not conflict:
            operation = OP_ASK
            request_kind = REQUEST_INQUIRY
    if referent_reason == "claim_unresolved":
        entity_binding["claim_binding"] = "unresolved"
    elif referent_reason == "unique_active_claim":
        entity_binding["claim_binding"] = "bound"
    active_slot_for_followup = focus.get(SLOT_INTERLOCUTOR) if isinstance(focus.get(SLOT_INTERLOCUTOR), Mapping) else {}
    active_interlocutor_id_for_followup = (
        _clean(active_slot_for_followup.get("id"), limit=80)
        if isinstance(active_slot_for_followup, Mapping)
        else ""
    )
    active_interlocutor_label_for_followup = (
        _clean(active_slot_for_followup.get("label"), limit=120)
        if isinstance(active_slot_for_followup, Mapping)
        else ""
    )
    if (
        not interlocutor
        and operation == OP_ASK
        and isinstance(discourse, DiscoursePointer)
        and discourse.type == "interlocutor"
        and discourse.id
    ):
        interlocutor = discourse.id
        if entity_binding.get("status") == "unresolved":
            entity_binding["status"] = "bound_canonical"
            entity_binding["entity_class"] = "canonical_established"
            entity_binding["bound_interlocutor_id"] = interlocutor
            entity_binding["label"] = discourse.label or active_interlocutor_label_for_followup or interlocutor
            entity_binding["authority_reasons"] = ["identity:discourse"]
    elif (
        not interlocutor
        and active_interlocutor_id_for_followup
        and operation in {"unresolved", OP_ASK}
        and str(validation.status or "") == STATUS_ABSTAINED
        and str(validation.reason or "") == REASON_INCOMPLETE_SEMANTICS
        and re.fullmatch(r"\s*(?:why|how|what about that|and that)\s*\??\s*", text, re.IGNORECASE)
    ):
        interlocutor = active_interlocutor_id_for_followup
        operation = OP_ASK
        request_kind = REQUEST_INQUIRY
        expected = EXPECT_ANSWER
        ambiguous = False
        target = TargetRef("interlocutor", active_interlocutor_label_for_followup or interlocutor, PROVENANCE_INHERITED)
        discourse = DiscoursePointer(
            type="interlocutor",
            id=interlocutor,
            label=active_interlocutor_label_for_followup or interlocutor,
            source_turn=None,
        )
        provenance = PROVENANCE_INHERITED
        referent_reason = "active_interlocutor_followup"
        entity_binding["status"] = "bound_canonical"
        entity_binding["entity_class"] = "canonical_established"
        entity_binding["bound_interlocutor_id"] = interlocutor
        entity_binding["label"] = active_interlocutor_label_for_followup or interlocutor
        entity_binding["authority_reasons"] = ["identity:discourse"]
    if (
        interlocutor
        and not entity_binding.get("explicit_new_interlocutor")
        and entity_binding.get("status") == "unresolved"
    ):
        inherited_incidental = str(interlocutor).startswith("inc_")
        entity_binding["status"] = "bound_incidental" if inherited_incidental else "bound_canonical"
        entity_binding["entity_class"] = (
            "permitted_bounded_incidental" if inherited_incidental else "canonical_established"
        )
        entity_binding["bound_interlocutor_id"] = interlocutor
        if not entity_binding.get("label"):
            entity_binding["label"] = active_interlocutor_label_for_followup or interlocutor
        entity_binding["authority_reasons"] = ["identity:discourse"]
    candidate_rows = [
        {"id": row.id, "type": row.type, "label": row.label}
        for row in export_referent_index(focus, referent_index if referent_index is not None else canonical_referents)
    ]
    construction = {
        "cues": cues,
        "referent_slot": referent_slot,
        "referent_reason": referent_reason,
        "ambiguity_detected": bool(ambiguous or provenance == PROVENANCE_AMBIGUOUS),
        "actionable_inherited": referent_reason in {"unique_actionable_lead", "previous_action", "unique_destination"},
        "active_claim_inherited": referent_reason == "unique_active_claim",
        "fast_path_proposal": True,
        "fast_path_used": fast_path_status == STATUS_VALIDATED,
        "fast_path_abstained": fast_path_status == STATUS_ABSTAINED,
        "fast_path_abstention_reason": fast_path_reason,
        "model_interpreter_invoked": interpreter_invoked,
        "model_proposal_rejected": interpreter_rejected,
        "clarification_after_model": clarification_after_model,
        "interpretation_api_calls": interpretation_api_calls,
        "interpretation_error": interpreter_error,
        "canonical_candidates": candidate_rows,
        "proposal_source": proposal.source,
        "proposed_operation": proposal.primary_operation,
        "proposed_supporting_operations": list(proposal.supporting_operations),
        "proposed_raw_target": proposal.raw_target_text,
        "canonicalization_attempted": True,
        "canonical_target_found": bool(validation.canonical_target_id),
        "operation_conflict": conflict,
        "validation_status": validation.status,
        "validation_result": validation.as_dict(),
        "abstention_reason": validation.reason,
        "failed_fields": list(validation.failed_fields),
        "clarification_required": validation.clarification_required,
        "model_interpretation_appropriate": validation.model_interpretation_appropriate,
        "discourse_commit_allowed": entity_binding.get("status") == "bound_incidental"
        or (validation.discourse_commit_allowed and validation.status == STATUS_VALIDATED),
        "interlocutor_rejected": bool(
            (
                binding.get("suppress_inherited_interlocutor") and not binding.get("selected_interlocutor_id")
            )
            or (
                entity_binding.get("explicit_new_interlocutor")
                and entity_binding.get("status") in {"unresolved", "ambiguous", "rejected_consequential"}
            )
        ),
        "entity_binding": {
            key: value
            for key, value in entity_binding.items()
            if key != "catalog_row"
        },
        "authoritative": validation.status == STATUS_VALIDATED,
        "semantic_completeness": (
            "sufficient"
            if fast_path_status == STATUS_VALIDATED
            else "insufficient"
            if fast_path_reason == REASON_INCOMPLETE_SEMANTICS
            else "not_applied"
        ),
        "compatibility_bridge": validation.compatibility_bridge,
        "interpretation_proposal": proposal.as_dict(),
    }
    from game.interaction_completion import terminal_resolution_operation

    if operation == OP_ACT and terminal_resolution_operation(text) == OP_ASK and interlocutor:
        operation = OP_ASK
        request_kind = REQUEST_INQUIRY
        expected = EXPECT_ANSWER
        if epistemic == EPISTEMIC_AUTHORITATIVE:
            epistemic = EPISTEMIC_UNKNOWN
        construction["operation_canonicalized"] = "ask"
    from game.player_commitment import (
        EXECUTED_NOW,
        commitment_status,
        executable_obligations,
        supporting_operations,
    )

    status = commitment_status(text)
    if status != EXECUTED_NOW and operation in {OP_ACT, OP_FOLLOW}:
        operation = OP_ASK
        request_kind = REQUEST_INQUIRY
        expected = EXPECT_ANSWER
        if epistemic == EPISTEMIC_AUTHORITATIVE:
            epistemic = EPISTEMIC_UNKNOWN
    requested = (
        entity_binding.get("proposed_interlocutor")
        or entity_binding.get("label")
        or binding.get("selected_interlocutor_label")
        or None
    )
    construction["commitment_status"] = status
    construction["primary_operation"] = operation
    from game.contract_adjudication_bridge import resolve_subject_coherence
    from game.incidental_entity import referential_person_nominal

    nominal = str(
        entity_binding.get("proposed_interlocutor")
        or binding.get("proposed_nominal")
        or ""
    )
    explicit_addressee = bool(
        binding.get("selected_interlocutor_id") or entity_binding.get("bound_interlocutor_id")
    )
    if not explicit_addressee and nominal:
        explicit_addressee = bool(referential_person_nominal(nominal))
    resolution_subject, subject_coherence = resolve_subject_coherence(
        text,
        operation=operation,
        proposed_operation=str(proposal.primary_operation or lexical_operation or ""),
        commitment=status,
        dimension=dimensions[0] if dimensions else None,
        explicit_addressee=explicit_addressee,
    )
    construction["resolution_subject"] = resolution_subject
    construction["resolution_subject_coherence"] = subject_coherence
    construction["semantic_input_length"] = len(text)
    construction["provenance_excerpt"] = bounded_provenance_excerpt(text)
    construction["secondary_operations"] = list(supporting_operations(text))
    construction["executable_obligations"] = executable_obligations(text)
    construction["requested_addressee"] = requested
    construction["addressee_binding_status"] = entity_binding.get("status")
    return ResolutionContract(
        contract_id=_contract_id(turn_index, text),
        turn_index=turn_index,
        request_kind=request_kind,
        operation=operation,
        target_ref=target,
        interlocutor_id=interlocutor or None,
        conversational_subject=_clean(subject, limit=160) or None,
        dimension=dimensions[0] if dimensions else None,
        dimensions=dimensions,
        expected_resolution=expected,
        epistemic_mode=epistemic,
        discourse_ref=discourse,
        referent_provenance=provenance,
        ambiguous=ambiguous or provenance == PROVENANCE_AMBIGUOUS,
        raw_input=text,
        construction=construction,
    )


def generation_projection(contract: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Compact model-facing constraint. Internal bookkeeping stays off the prompt."""
    if not isinstance(contract, Mapping) or not contract.get("contract_id"):
        return None
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    dims = [str(item) for item in (contract.get("dimensions") or []) if str(item).strip()]
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), Mapping) else {}
    abstained = construction.get("validation_status") == "abstained" or contract.get("operation") == "unresolved"
    named_target = _clean(target.get("id_or_text"), limit=80)
    subject_text = _clean(contract.get("conversational_subject"), limit=120)
    target_text = named_target or subject_text or "the established target"
    if binding.get("status") == "rejected_consequential":
        constraint = (
            "The player named a person the scene does not establish. "
            "Do not create that person or treat their story as true. "
            "Refuse or say that cannot be established. Do not answer as a different person."
        )
    elif binding.get("explicit_new_interlocutor") and binding.get("status") in {"unresolved", "ambiguous"}:
        proposed = binding.get("proposed_interlocutor") or "someone else"
        constraint = (
            f"The player wants to speak with {proposed}. That person is not available. "
            "Say so, or ask who they mean. Do not invent them. Do not answer as a different person."
        )
    elif abstained or contract.get("ambiguous") or contract.get("expected_resolution") == EXPECT_CLARIFICATION and contract.get(
        "referent_provenance"
    ) in {PROVENANCE_AMBIGUOUS, PROVENANCE_UNRESOLVED}:
        constraint = (
            "The referent is not unambiguous. Ask which one is meant, or say it cannot be identified. Do not guess."
        )
    elif contract.get("epistemic_mode") == EPISTEMIC_CONSEQUENTIAL:
        constraint = (
            "This asks for protected information. Refuse or defer. Do not invent hidden or consequential truth. "
            "Do not answer as a different person."
        )
    else:
        point = ", ".join(dims) if dims else str(contract.get("operation") or "request")
        expected = str(contract.get("expected_resolution") or "answer").replace("_", " ")
        article = "an" if expected[:1].lower() in "aeiou" else "a"
        constraint = (
            f"Resolve {contract.get('operation')} for {target_text} ({point}). "
            f"The reply must be {article} {expected}, a real inability, a refusal, a condition, "
            "or a clarification. Do not replace that request with an unrelated scene description."
        )
        if contract.get("interlocutor_id"):
            speaker = binding.get("label") or contract.get("interlocutor_id")
            constraint += (
                f" That interlocutor is {speaker}. Do not deny that they exist."
                " Have them answer, refuse, admit they do not know, or ask a clarifying question."
                " Do not narrate that nobody steps forward. Do not answer as a different person."
            )
        if named_target:
            constraint += " That target is available. Do not deny that it is present."
    return {
        "request_kind": contract.get("request_kind"),
        "operation": contract.get("operation"),
        "target": named_target or None,
        "interlocutor": contract.get("interlocutor_id"),
        "subject": contract.get("conversational_subject"),
        "dimension": contract.get("dimension"),
        "dimensions": dims,
        "expected_resolution": contract.get("expected_resolution"),
        "authority": contract.get("epistemic_mode"),
        "constraint": constraint,
    }


def _norm_words(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()


def _stem_word(word: str) -> str:
    if len(word) > 4 and word.endswith("s"):
        return word[:-1]
    return word


def _content_words(text: str) -> list[str]:
    return [_stem_word(word) for word in _norm_words(text).split() if len(word) > 2 and word not in _ECHO_FRAME]


def player_text_is_echoed(body: str | None, raw_input: str | None) -> bool:
    """True when the candidate restates the player instead of adding an answer.

    A full paste counts. So does a paraphrase whose content words are only the
    player's content words plus framing ("you ask how sure he is").
    """
    raw = _norm_words(raw_input or "")
    visible = _norm_words(body or "")
    if len(raw) < 8 or not visible:
        return False
    if raw in visible:
        return True
    player_words = _content_words(raw)
    response_words = _content_words(visible)
    if len(player_words) < 1 or not response_words:
        return False
    if len(response_words) + 1 < len(player_words):
        return False
    player_set = set(player_words)
    return all(word in player_set for word in response_words)


def _strip_player_echo(body: str, raw_input: str) -> str:
    visible = _norm_words(body)
    raw = _norm_words(raw_input)
    if raw and raw in visible:
        visible = visible.replace(raw, " ")
    player_words = set(_content_words(raw))
    return " ".join(word for word in visible.split() if _stem_word(word) not in player_words)


def _dimension_cue_body(text: str, dimension: str) -> str:
    """Drop collocations that mention a dimension without answering it."""
    body = str(text or "")
    if dimension == DIM_TIME:
        body = _EARLIER_CLAIM_RE.sub(" ", body)
    if dimension == DIM_SOUND:
        body = re.sub(r"\byou listen(?:s|ed|ing)?\b", " ", body, flags=re.IGNORECASE)
    return _INABILITY_DIMENSION_SPAN_RE.sub(" ", body)


def _raw_dimension_cue(text: str, dimension: str) -> bool:
    """Lexical cue on the original line, ignoring only the earlier-claim collision."""
    body = _EARLIER_CLAIM_RE.sub(" ", str(text or "")) if dimension == DIM_TIME else str(text or "")
    pattern = _RESPONSE_CUES.get(dimension)
    return bool(pattern and pattern.search(body))


def _dimension_covered(text: str, dimension: str) -> bool:
    if dimension == DIM_CONTENT:
        return _substantive_content(text)
    body = _dimension_cue_body(text, dimension)
    if dimension == DIM_NEXT_STEP and _PROCEDURE_ANSWER_RE.search(body):
        return True
    if dimension == DIM_NEXT_STEP and _IDENTITY_FACT_RE.search(body):
        return False
    if dimension == DIM_USE and _PURPOSE_ANSWER_RE.search(body):
        return True
    pattern = _RESPONSE_CUES.get(dimension)
    return bool(pattern and pattern.search(body))


def _foreign_claim_dimension(text: str, requested: set[str]) -> str | None:
    """A different claim dimension answered while the requested one is not.

    Extra information does not erase a requested dimension that is already covered.
    """
    if not requested:
        return None
    if any(_dimension_covered(text, dim) for dim in requested):
        return None
    claim_dims = (DIM_SOURCE, DIM_CONFIDENCE, DIM_LOCATION, DIM_TIME)
    if any(dim in requested and _raw_dimension_cue(text, dim) for dim in claim_dims):
        return None
    for dim in claim_dims:
        if dim in requested:
            continue
        if _raw_dimension_cue(text, dim):
            return dim
    return None


def _generic_atmospheric_avoidance(text: str) -> bool:
    """Crowd or scene prose standing in for an addressed NPC."""
    if _ATTRIBUTED_SPEECH_RE.search(str(text or "")) and _REFUSAL_FRAME_RE.search(str(text or "")):
        return False
    return bool(_ATMOSPHERIC_AVOIDANCE_RE.search(str(text or "")))


def _unrelated_narrated_fact(text: str) -> bool:
    """A third-person scene or clue sentence that does not answer the person addressed."""
    body = str(text or "")
    if _ATTRIBUTED_SPEECH_RE.search(body):
        return False
    if re.search(r"\byou\b", body, re.IGNORECASE) and re.search(
        r"\b(?:need|must|can|cannot|can't|may|don't|do not)\b",
        body,
        re.IGNORECASE,
    ):
        return False
    if _SCENE_FRAME_RE.search(body):
        return True
    return bool(_UNRELATED_NARRATED_FACT_RE.search(body))


def resolution_rank(view: Mapping[str, Any] | None) -> int:
    """Valid answer outranks a partial answer, which outranks a real nonresolution."""
    if not isinstance(view, Mapping):
        return 0
    reasons = {str(item) for item in (view.get("reasons") or [])}
    if reasons & {
        "dimension_substituted",
        "atmospheric_avoidance",
        "social_not_resolved",
        "canonical_premise_contradicted",
        "generic_use_nonanswer",
        "literal_referent_reinterpretation",
        "generic_scene_replaced_dimension",
        "structurally_incomplete",
        "passive_observation_collapse",
        "player_text_leakage",
        "discourse_state_contradiction",
        "interaction_not_completed",
    }:
        return 0
    status = str(view.get("status") or "")
    if status == "satisfied":
        if view.get("dimension_compatible") is False:
            return 1
        return 4
    if status == "partial" and view.get("resolution_kind") == "answer":
        return 3
    if status in {"legitimate_nonresolution", "partial"}:
        if view.get("necessary_clarification"):
            return 3
        return 2
    if status in {"unchecked", "not_applicable"}:
        return 1
    return 0


def _action_outcome(text: str) -> str:
    if _ACTION_SUCCESS_RE.search(text):
        return "success"
    if _ACTION_NONRESOLUTION_RE.search(text):
        return "nonresolution"
    return ""


def _contract_dims(contract: Mapping[str, Any]) -> list[str]:
    dims = [str(item) for item in (contract.get("dimensions") or []) if str(item).strip()]
    if not dims and contract.get("dimension"):
        dims = [str(contract.get("dimension"))]
    return dims


def _contract_target_text(contract: Mapping[str, Any]) -> str:
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    return _clean(target.get("id_or_text") or discourse.get("label") or "", limit=160)


def _term_set(text: str) -> set[str]:
    return {
        _stem_word(word)
        for word in _norm_words(text).split()
        if len(word) > 2 and word not in _TARGET_STOP
    }


def _expand_terms(terms: set[str]) -> set[str]:
    expanded = set(terms)
    if expanded & {_stem_word(word) for word in _DOC_ALIASES}:
        expanded |= {_stem_word(word) for word in _DOC_ALIASES}
    return expanded


def _target_terms(contract: Mapping[str, Any]) -> set[str]:
    return _expand_terms(_term_set(_contract_target_text(contract)))


def _meaningful_terms(text: str, contract: Mapping[str, Any]) -> list[str]:
    skip = _BOILERPLATE_TERMS | _target_terms(contract)
    found: list[str] = []
    for word in _norm_words(text).split():
        stemmed = _stem_word(word)
        if len(stemmed) <= 2 or stemmed in _TARGET_STOP or stemmed in skip:
            continue
        found.append(stemmed)
    return found


def _identity_role_sentence(text: str) -> bool:
    """A role assignment such as who commands is not the substance of a report."""
    if not _IDENTITY_FACT_RE.search(text or ""):
        return False
    return not bool(_CONTENT_STATE_RE.search(text or ""))


def _reported_proposition(text: str) -> bool:
    if not _REPORTED_PROPOSITION_RE.search(text or ""):
        return False
    if _identity_role_sentence(text):
        return False
    payload = [
        word
        for word in _content_words(text)
        if word not in {"say", "said", "tell", "told", "word", "report", "reported", "speak", "speaking"}
    ]
    return len(payload) >= 3


def _substantive_content(text: str) -> bool:
    """The requested speech, report, or writing, not a nearby identity or scene fact."""
    parts = _split_resolution_sentences(text) or [str(text or "")]
    for part in parts:
        if _identity_role_sentence(part):
            continue
        if _NEGATIVE_RESOLUTION_RE.search(part) or explicit_nonanswer_response(part):
            continue
        if _content_observation(part) or _reported_proposition(part):
            return True
    return False


def _content_observation(text: str) -> bool:
    text = _spoken_body(text)
    if _SCENE_FRAME_RE.search(text):
        text = _SCENE_FRAME_RE.sub(" ", text)
    return bool(
        re.search(
            r"\b(?:lists?|reads?|says|said|written|inscribed|blank|illegible|curfew|"
            r"tax(?:es)?|postings?|placard|chalk|words?|text)\b",
            text,
            re.IGNORECASE,
        )
    )


def _spoken_body(text: str) -> str:
    """Drop dialogue tags so \"says\" is not mistaken for the answer itself."""
    return re.sub(
        r"\b(?:says|said|replies|replied|asks|asked|answers|answered)\b,?\s*",
        " ",
        text,
        flags=re.IGNORECASE,
    )


def _positive_observation(text: str) -> bool:
    text = _spoken_body(text)
    listing = re.search(
        r"\b(?:lists?|says|said|written|inscribed|blank|stained|torn|faded|worn|scuffed|"
        r"dented|smells?|sounds?|quiet|silent|curfew|whisper(?:ed|s)?)\b",
        text,
        re.IGNORECASE,
    )
    if _NEGATIVE_RESOLUTION_RE.search(text) and not listing:
        return False
    return bool(listing or _content_observation(text))


def _head_subject(text: str) -> str:
    """The opening noun phrase, stopping before the verb. Pronouns stay intact."""
    norm = _norm_words(text)
    if not norm or re.match(r"^(?:no|not|none|nothing)\b", norm):
        return ""
    verbs = {
        "is", "are", "was", "were", "be", "smell", "smells", "sound", "sounds", "look", "looks",
        "seem", "seems", "stand", "stands", "list", "lists", "read", "reads", "show", "shows",
        "say", "says", "establish", "establishes", "adjust", "adjusts", "watch", "watches",
        "glance", "glances", "sit", "sits", "can", "cannot",
    }
    words: list[str] = []
    for word in norm.split():
        if words and (word in verbs or word in _TARGET_STOP):
            break
        if word in verbs:
            break
        if word in _TARGET_STOP:
            continue
        words.append(word)
        if len(words) >= 3:
            break
    return " ".join(words)


def _target_relation(text: str, contract: Mapping[str, Any]) -> tuple[bool | None, str, bool]:
    """Return target compatibility, the answer's subject, and whether that subject conflicts."""
    wanted = _target_terms(contract)
    if not wanted:
        return None, "", False
    about = ""
    response_terms = _expand_terms(_term_set(text))
    about_match = _ABOUT_TARGET_RE.search(text)
    if about_match:
        about = about_match.group("target")
        about_terms = _expand_terms(_term_set(about))
        if about_terms and about_terms.isdisjoint(wanted) and response_terms.isdisjoint(wanted):
            return False, about, True
    if response_terms & wanted:
        return True, about or _contract_target_text(contract), False
    subject = _head_subject(text)
    if subject in {"it", "its", "this", "that", "they", "them"}:
        return True, subject, False
    subject_terms = _expand_terms(_term_set(subject))
    dimension_terms = {str(item) for item in _contract_dims(contract)}
    if (
        subject_terms
        and subject_terms.isdisjoint(wanted)
        and subject_terms.isdisjoint(_BOILERPLATE_TERMS)
        and subject_terms.isdisjoint(dimension_terms)
    ):
        return False, subject, True
    if re.search(r"\b(?:it|its|this|that)\b", text, re.IGNORECASE):
        return True, "it", False
    # Missing the target is not a rival subject. Callers still reject it.
    return False, about or subject, False


def _tied_to_request(text: str, contract: Mapping[str, Any]) -> bool:
    request_terms = _term_set(str(contract.get("raw_input") or "")) - _BOILERPLATE_TERMS
    if request_terms & _term_set(text):
        return True
    compatible, _label, conflict = _target_relation(text, contract)
    if conflict:
        return False
    return compatible is True


def _specific_inquiry(raw_input: str, operation: str) -> bool:
    if operation != OP_ASK:
        return False
    return bool(
        re.search(r"\b(?:what|who|where|when|which|how|rumou?r|news|story|stories|tell)\b", raw_input, re.IGNORECASE)
    )


def _scene_staging(text: str) -> bool:
    return bool(re.search(r"\b(?:stands?|watches|watching|glances|nods|adjusts|crowd|square)\b", text, re.IGNORECASE))


def _claim_label(contract: Mapping[str, Any]) -> str:
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    return _clean(
        discourse.get("label") or contract.get("conversational_subject") or _contract_target_text(contract),
        limit=180,
    )


def canonical_existence_denied(text: str | None, contract: Mapping[str, Any] | None) -> bool:
    """True when visible text denies a referent the contract already validated."""
    if not isinstance(contract, Mapping) or not contract.get("contract_id"):
        return False
    if contract.get("ambiguous"):
        return False
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    if construction.get("validation_status") == "abstained":
        return False
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    established = bool(contract.get("interlocutor_id")) or bool(discourse.get("id")) or bool(target.get("id_or_text"))
    if not established:
        return False
    return bool(_CANONICAL_DENIAL_RE.search(str(text or "")))


def generic_use_nonanswer(text: str | None) -> bool:
    """The canned wear line, without a request-specific limit such as sealed or illegible."""
    body = str(text or "")
    if not _GENERIC_USE_NONANSWER_RE.search(body):
        return False
    return not bool(re.search(r"\b(?:illegible|sealed|too dark|blank|unposted|missing)\b", body, re.IGNORECASE))


def explicit_nonanswer_response(text: str | None) -> bool:
    """True when the visible text says that no answer was given.

    A later sentence that actually reports the requested content keeps the
    text eligible to be an answer. The dodge by itself is not an answer.
    """
    body = _clean(text, limit=2000)
    if not body or not _EXPLICIT_NONANSWER_RE.search(body):
        return False
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\s+[—–-]\s+|\n+", body) if part.strip()]
    for part in parts:
        if _EXPLICIT_NONANSWER_RE.search(part) and not _positive_observation(part):
            continue
        if _positive_observation(part) or (_REPORT_FRAME_RE.search(part) and len(_content_words(part)) >= 3):
            return False
    return True


def _repeat_contaminated(label: str, text: str) -> bool:
    """A restatement that also carries a competing fact or a momentum splice."""
    if _REPEAT_SPLICE_RE.search(text or ""):
        return True
    claim = set(_content_words(label))
    if not claim:
        return False
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", str(text or "")) if part.strip()]
    for part in parts:
        words = [word for word in _content_words(part) if word not in _ATMOSPHERE_WORDS]
        if len(words) < 4:
            continue
        overlap = [word for word in words if word in claim]
        if len(overlap) >= 2:
            continue
        if claim and len(overlap) / max(len(set(words)), 1) >= 0.34:
            continue
        return True
    return False


def genuine_resolution_blocker(text: str | None) -> bool:
    """Authority problems that may still reject an apparent answer.

    A place name or a topical sentence is not one of these. Consequential
    invention, a price, or a redirect to an unestablished person is.
    """
    body = str(text or "")
    if not body.strip():
        return False
    if _CONSEQUENTIAL_RE.search(body):
        return True
    if _PRICE_BLOCK_RE.search(body) or _REDIRECT_BLOCK_RE.search(body):
        return True
    return False


def _split_resolution_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", str(text or "")) if part.strip()]


def repair_answer_locally(text: str | None, resolution: Mapping[str, Any] | None) -> str:
    """Drop a local defect when the remainder still answers the contract."""
    parts = _split_resolution_sentences(str(text or ""))
    kept: list[str] = []
    for part in parts:
        cleaned = _DEVOICE_RE.sub("", part).strip()
        if not cleaned:
            continue
        if cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]
        if explicit_nonanswer_response(cleaned) and not _positive_observation(cleaned):
            continue
        if genuine_resolution_blocker(cleaned):
            continue
        if _scene_staging(cleaned) and not _REPORT_FRAME_RE.search(cleaned):
            continue
        kept.append(cleaned if re.search(r"[.!?]$", cleaned) else f"{cleaned}.")
    if not kept:
        return ""
    joined = " ".join(kept)
    if semantic_line_view(joined, resolution).get("keeps_answer") and not genuine_resolution_blocker(joined):
        return joined
    contract = contract_mapping_from_resolution(resolution)
    if str(contract.get("operation") or "") == OP_REPEAT:
        label = _claim_label(contract)
        faithful = [part for part in kept if not _repeat_contaminated(label, part)]
        if faithful:
            narrowed = " ".join(faithful)
            if semantic_line_view(narrowed, resolution).get("keeps_answer") and not genuine_resolution_blocker(narrowed):
                return narrowed
    return ""


def _invalidated_candidate_match(debug: Mapping[str, Any], text: str) -> bool:
    """True when this exact candidate was already rejected for a hard reason."""
    inv = debug.get("best_safe_invalidation") if isinstance(debug, Mapping) else None
    if not isinstance(inv, Mapping):
        return False
    rejected = str(inv.get("candidate") or "").strip()
    body = str(text or "").strip()
    if not rejected or not body:
        return False
    needle = rejected[:160].lower()
    return needle in body.lower() or body[:160].lower() in needle


def invalidate_best_safe_candidate(
    gm: dict[str, Any] | None,
    *,
    reason: str,
    candidate: str | None,
) -> None:
    """Drop a tracked best candidate for an explicit hard reason.

    A later candidate may still be stored. The invalidated text itself may not
    return just because another line exists or because it covers the contract.
    """
    if not isinstance(gm, dict):
        return
    metadata = gm.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        return
    debug = metadata.setdefault("emission_debug", {})
    if not isinstance(debug, dict):
        return
    rejected = str(candidate or debug.get("best_safe_candidate") or "").strip()
    debug["best_safe_invalidation"] = {"reason": str(reason or "invalidated"), "candidate": rejected[:180]}
    if rejected and str(debug.get("best_safe_candidate") or "").strip()[:160] in rejected:
        debug.pop("best_safe_candidate", None)
        debug["best_safe_rank"] = 0
    if rejected and str(debug.get("satisfied_candidate") or "").strip()[:160] in rejected:
        debug.pop("satisfied_candidate", None)


def _authority_rejection_reason(text: str | None, resolution: Mapping[str, Any] | None) -> str | None:
    """Explicit authority invalidity. Coverage does not override it."""
    if not isinstance(resolution, Mapping):
        return None
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), Mapping) else {}
    blobs = [str(item) for item in (meta.get("authority_invalid_candidates") or []) if str(item).strip()]
    debug = meta.get("emission_debug") if isinstance(meta.get("emission_debug"), Mapping) else {}
    authority = debug.get("bounded_improvisation_authority") if isinstance(debug.get("bounded_improvisation_authority"), Mapping) else {}
    for row in list(authority.get("rejected") or []):
        if isinstance(row, Mapping):
            blobs.append(str(row.get("text") or row.get("proposal") or ""))
    low = str(text or "").lower()
    for blob in blobs:
        needle = blob.strip().lower()
        if needle and needle in low:
            return "authority_violation"
    contract = contract_mapping_from_resolution(resolution)
    if contract.get("epistemic_mode") == EPISTEMIC_CONSEQUENTIAL and str(text or "").strip():
        if not _LEGITIMATE_RE.search(str(text or "")):
            return "authority_violation"
    return None


def _effective_contract_dims(contract: Mapping[str, Any]) -> list[str]:
    dims = _contract_dims(contract)
    if dims:
        return dims
    obvious = first_obvious_dimension(str(contract.get("raw_input") or ""))
    return [obvious] if obvious else []


def resolution_coverage(text: str | None, resolution: Mapping[str, Any] | None) -> dict[str, Any]:
    """Which requested dimensions this candidate actually resolves.

    A shared name or topic word is not coverage. The contract's dimension is.
    """
    contract = contract_mapping_from_resolution(resolution)
    if not contract and isinstance(resolution, Mapping) and resolution.get("contract_id"):
        contract = dict(resolution)
    required = _effective_contract_dims(contract) if contract else []
    covered = [dim for dim in required if _dimension_covered(str(text or ""), dim)]
    return {
        "contract_id": contract.get("contract_id") if contract else None,
        "operation": contract.get("operation") if contract else None,
        "target": _contract_target_text(contract) if contract else None,
        "interlocutor": contract.get("interlocutor_id") if contract else None,
        "dimension": contract.get("dimension") if contract else None,
        "expected_resolution": contract.get("expected_resolution") if contract else None,
        "required_dimensions": required,
        "covered_dimensions": covered,
        "complete": (not required) or set(required) <= set(covered),
    }


def _dimension_cue_hits(text: str, dimensions: set[str]) -> int:
    total = 0
    for dim in dimensions:
        pattern = _RESPONSE_CUES.get(dim)
        if pattern:
            total += len(pattern.findall(str(text or "")))
        if dim == DIM_NEXT_STEP:
            total += len(_PROCEDURE_ANSWER_RE.findall(str(text or "")))
        if dim == DIM_USE:
            total += len(_PURPOSE_ANSWER_RE.findall(str(text or "")))
    return total


def candidate_may_replace(
    incumbent: str | None,
    challenger: str | None,
    resolution: Mapping[str, Any] | None,
) -> tuple[bool, str]:
    """Rank is necessary. The challenger must also keep the incumbent's resolution."""
    if _authority_rejection_reason(challenger, resolution):
        return False, "authority_violation"
    contract = contract_mapping_from_resolution(resolution)
    from game.interaction_completion import structural_assessment

    incumbent_structure = structural_assessment(incumbent, contract)
    challenger_structure = structural_assessment(challenger, contract)
    if incumbent_structure.get("valid") and not challenger_structure.get("valid"):
        return False, "structurally_incomplete"
    if (
        str((contract or {}).get("operation") or "") in {OP_INSPECT, OP_PERCEIVE}
        and not incumbent_structure.get("stall")
        and challenger_structure.get("stall")
        and incumbent_structure.get("valid")
    ):
        return False, "inspection_detail_loss"
    incumbent_text = str(incumbent or "").strip()
    challenger_text = str(challenger or "").strip()
    if not incumbent_text:
        return True, "no_incumbent"
    if not challenger_text:
        return False, "empty_challenger"
    contract = contract_mapping_from_resolution(resolution)
    if canonical_existence_denied(challenger_text, contract):
        return False, "hard_invalid"
    if genuine_resolution_blocker(challenger_text):
        incumbent_view = semantic_line_view(incumbent_text, resolution)
        challenger_view = semantic_line_view(challenger_text, resolution)
        if incumbent_view.get("keeps_answer") or resolution_rank(challenger_view) <= resolution_rank(incumbent_view):
            return False, "hard_invalid"
    incumbent_view = semantic_line_view(incumbent_text, resolution)
    challenger_view = semantic_line_view(challenger_text, resolution)
    incumbent_rank = resolution_rank(incumbent_view)
    challenger_rank = resolution_rank(challenger_view)
    if challenger_rank < incumbent_rank:
        return False, "lower_satisfaction_rank"
    if challenger_view.get("target_compatible") is False and incumbent_view.get("target_compatible") is not False:
        return False, "target_changed"
    if challenger_view.get("operation_compatible") is False and incumbent_view.get("operation_compatible") is True:
        return False, "operation_changed"
    challenger_reasons = {str(item) for item in (challenger_view.get("reasons") or [])}
    if "dimension_substituted" in challenger_reasons:
        return False, "different_proposition"
    incumbent_covered = set(resolution_coverage(incumbent_text, resolution)["covered_dimensions"])
    challenger_covered = set(resolution_coverage(challenger_text, resolution)["covered_dimensions"])
    if incumbent_view.get("necessary_clarification") and challenger_view.get("resolution_kind") == "inability":
        if challenger_rank <= incumbent_rank:
            return False, "clarification_required"
    if incumbent_covered and not incumbent_covered <= challenger_covered:
        return False, "resolution_content_not_preserved"
    if (
        challenger_rank == incumbent_rank
        and incumbent_covered
        and incumbent_covered == challenger_covered
        and _dimension_cue_hits(challenger_text, incumbent_covered) < _dimension_cue_hits(incumbent_text, incumbent_covered)
    ):
        return False, "less_specific_same_dimension"
    if challenger_rank > incumbent_rank:
        return True, "higher_rank"
    return True, "resolution_content_preserved"


def _proposed_is_weaker(current_view: Mapping[str, Any], proposed_view: Mapping[str, Any]) -> bool:
    if resolution_rank(current_view) > resolution_rank(proposed_view):
        return True
    current_status = str(current_view.get("status") or "")
    proposed_status = str(proposed_view.get("status") or "")
    if current_status == "satisfied" and proposed_status != "satisfied":
        return True
    if current_status == "satisfied" and "repeat_contaminated" in {str(item) for item in (proposed_view.get("reasons") or [])}:
        return True
    if current_status == "partial" and current_view.get("resolution_kind") == "answer":
        if proposed_status in {"legitimate_nonresolution", "unsatisfied"}:
            return True
        if proposed_view.get("resolution_kind") in {"inability", "refusal", "clarification"}:
            return True
    return False


def prefer_stronger_resolution(
    current: str | None,
    proposed: str | None,
    resolution: Mapping[str, Any] | None,
    *,
    invalidated: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Keep a valid answer when a later step would replace it with a weaker close.

    A genuinely blocked answer may still be rejected. Repair is tried before that.
    """
    current_text = str(current or "")
    proposed_text = str(proposed or "")
    info: dict[str, Any] = {
        "downgrade_attempted": False,
        "downgrade_rejected": False,
        "downgrade_reason": None,
        "recovery_used": False,
        "recovery_source": None,
        "destroyed": False,
    }
    if invalidated:
        info["downgrade_attempted"] = True
        contract = contract_mapping_from_resolution(resolution)
        blocked = genuine_resolution_blocker(current_text) or canonical_existence_denied(current_text, contract)
        current_view = semantic_line_view(current_text, resolution)
        if not blocked and current_view.get("keeps_answer"):
            info["downgrade_rejected"] = True
            info["downgrade_reason"] = "valid_answer_not_downgraded"
            info["recovery_source"] = "valid_answer"
            return current_text, info
        info["downgrade_reason"] = "candidate_invalid"
        return proposed_text, info
    if genuine_resolution_blocker(current_text):
        repaired = repair_answer_locally(current_text, resolution)
        if repaired and not genuine_resolution_blocker(repaired):
            info["downgrade_attempted"] = True
            info["downgrade_rejected"] = True
            info["recovery_used"] = True
            info["recovery_source"] = "local_repair"
            info["downgrade_reason"] = "repaired_local_defect"
            return repaired, info
        info["downgrade_attempted"] = True
        info["downgrade_reason"] = "candidate_invalid"
        return proposed_text, info
    current_view = semantic_line_view(current_text, resolution)
    proposed_view = semantic_line_view(proposed_text, resolution)
    allowed, reason = candidate_may_replace(current_text, proposed_text, resolution)
    if current_text.strip() and not allowed:
        info["downgrade_attempted"] = True
        info["downgrade_rejected"] = True
        info["downgrade_reason"] = reason
        info["recovery_source"] = "valid_answer"
        info["replacement_reason"] = reason
        return current_text, info
    repaired_early = repair_answer_locally(current_text, resolution)
    repaired_answers = bool(repaired_early) and bool(semantic_line_view(repaired_early, resolution).get("keeps_answer"))
    if not _proposed_is_weaker(current_view, proposed_view) and not (
        repaired_answers and not proposed_view.get("keeps_answer")
    ):
        return proposed_text, info
    if repaired_answers and not current_view.get("keeps_answer"):
        info["downgrade_attempted"] = True
        info["downgrade_rejected"] = True
        info["recovery_used"] = True
        info["recovery_source"] = "local_repair"
        info["downgrade_reason"] = "repaired_local_defect"
        return repaired_early, info
    info["downgrade_attempted"] = True
    repaired = repair_answer_locally(current_text, resolution)
    if repaired and semantic_line_view(repaired, resolution).get("keeps_answer"):
        info["downgrade_rejected"] = True
        info["recovery_used"] = repaired.strip() != current_text.strip()
        info["recovery_source"] = "local_repair" if info["recovery_used"] else "valid_answer"
        info["downgrade_reason"] = "repaired_local_defect" if info["recovery_used"] else "valid_answer_not_downgraded"
        return repaired, info
    if current_view.get("keeps_answer") or (
        current_view.get("status") == "partial" and current_view.get("resolution_kind") == "answer"
    ):
        info["downgrade_rejected"] = True
        info["downgrade_reason"] = "valid_answer_not_downgraded"
        info["recovery_source"] = "valid_answer"
        return current_text, info
    info["downgrade_reason"] = "no_valid_answer"
    info["destroyed"] = bool(current_view.get("keeps_answer")) and not proposed_view.get("keeps_answer")
    return proposed_text, info


def _candidate_rank(text: str | None, resolution: Mapping[str, Any] | None) -> int:
    body = str(text or "").strip()
    if not body:
        return -1
    contract = contract_mapping_from_resolution(resolution)
    if genuine_resolution_blocker(body) or canonical_existence_denied(body, contract):
        repaired = repair_answer_locally(body, resolution)
        if (
            not repaired
            or genuine_resolution_blocker(repaired)
            or canonical_existence_denied(repaired, contract)
        ):
            return -1
        return resolution_rank(semantic_line_view(repaired, resolution))
    return resolution_rank(semantic_line_view(body, resolution))


def remember_satisfied_candidate(
    gm: dict[str, Any] | None,
    text: str | None,
    resolution: Mapping[str, Any] | None,
) -> None:
    """Keep the best authority-safe candidate so a later rewrite cannot erase it."""
    if not isinstance(gm, dict):
        return
    body = str(text or "").strip()
    if not body:
        return
    view = semantic_line_view(body, resolution)
    stored = body
    from game.interaction_completion import structural_assessment

    if not structural_assessment(body, contract_mapping_from_resolution(resolution)).get("valid"):
        return
    rank = _candidate_rank(body, resolution)
    if rank < 2:
        repaired = repair_answer_locally(body, resolution)
        repaired_rank = _candidate_rank(repaired, resolution)
        if repaired_rank < 2:
            return
        stored = repaired
        rank = repaired_rank
        view = semantic_line_view(stored, resolution)
    elif genuine_resolution_blocker(body):
        return
    metadata = gm.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        return
    debug = metadata.setdefault("emission_debug", {})
    if not isinstance(debug, dict):
        return
    existing = int(debug.get("best_safe_rank") or 0)
    existing_text = str(debug.get("best_safe_candidate") or "")
    contract = contract_mapping_from_resolution(resolution)
    contract_id = str(contract.get("contract_id") or "")
    if contract_id and str(debug.get("best_safe_contract_id") or "") not in {"", contract_id}:
        existing = 0
        existing_text = ""
        debug.pop("best_safe_candidate", None)
        debug.pop("best_safe_rank", None)
        debug.pop("satisfied_candidate", None)
        debug.pop("best_safe_invalidation", None)
        debug.pop("initial_safe_candidate", None)
    if _invalidated_candidate_match(debug, stored):
        debug["replacement_decision"] = "rejected"
        inv = debug.get("best_safe_invalidation") if isinstance(debug.get("best_safe_invalidation"), dict) else {}
        debug["replacement_reason"] = str(inv.get("reason") or "invalidated")
        return
    rejection = _authority_rejection_reason(stored, resolution)
    if rejection:
        debug["best_safe_invalidation"] = {"reason": rejection, "candidate": stored[:180]}
        return
    if existing_text:
        allowed, reason = candidate_may_replace(existing_text, stored, resolution)
    else:
        allowed, reason = True, "no_incumbent"
    if not allowed:
        debug["replacement_decision"] = "rejected"
        debug["replacement_reason"] = reason
        return
    if rank >= existing:
        debug["best_safe_candidate"] = stored[:2000]
        debug["best_safe_rank"] = rank
        debug["best_safe_contract_id"] = contract_id or None
        debug["best_safe_coverage"] = resolution_coverage(stored, resolution)
        debug["replacement_decision"] = "accepted"
        debug["replacement_reason"] = reason
        if not str(debug.get("initial_safe_candidate") or "").strip():
            debug["initial_safe_candidate"] = stored[:2000]
    if view.get("keeps_answer") and rank >= 4 and not str(debug.get("satisfied_candidate") or "").strip():
        debug["satisfied_candidate"] = stored[:2000]


def _text_attributes_speaker(text: str, name: str) -> bool:
    """True when this line already has the canonical speaker saying the words."""
    cleaned = str(name or "").strip()
    if not cleaned:
        return False
    speaker = re.escape(cleaned)
    return bool(
        re.search(
            rf"\b{speaker}\b.{{0,48}}\b(?:says|said|replies|replied|mutters|muttered|answers|answered|asks|asked)\b"
            rf"|\b(?:says|said|replies|replied|mutters|muttered|answers|answered)\b.{{0,24}}\b{speaker}\b",
            str(text or ""),
            re.IGNORECASE,
        )
    )


def _speaker_aligned_text(text: str | None, resolution: Mapping[str, Any] | None) -> str:
    """Keep text that honors the speaker contract, retargeting a wrong opening speaker when possible.

    A satisfying answer attributed to the wrong canonical interlocutor is not authority-safe.
    Returning an empty string marks it ineligible to replace a speaker-correct line.
    """
    body = str(text or "").strip()
    if not body or not isinstance(resolution, dict):
        return body
    from game.speaker_contract_enforcement import (
        _try_local_rebind_opening_speaker,
        get_speaker_selection_contract,
        validate_emitted_speaker_against_contract,
    )

    contract = get_speaker_selection_contract(resolution)
    if not isinstance(contract, dict):
        return body
    debug = contract.get("debug") if isinstance(contract.get("debug"), dict) else {}
    if debug.get("contract_missing"):
        return body
    if not str(contract.get("primary_speaker_id") or "").strip() and not list(contract.get("allowed_speaker_ids") or []):
        return body
    validation = validate_emitted_speaker_against_contract(body, contract, resolution=resolution)
    if validation.get("ok"):
        return body
    signature = (validation.get("details") or {}).get("signature") or {}
    label = str(signature.get("speaker_label") or "").strip()
    # A long span or a second sentence is narration, not an opening speaker name.
    if not label or len(label.split()) > 6 or "." in label:
        return body
    names = [
        str(validation.get("canonical_speaker_name") or "").strip(),
        str(contract.get("primary_speaker_name") or "").strip(),
    ]
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    names.append(str(social.get("npc_name") or "").strip())
    if any(_text_attributes_speaker(body, name) for name in names if name):
        return body
    canonical_name = str(validation.get("canonical_speaker_name") or "").strip()
    if label and canonical_name:
        renamed = _try_local_rebind_opening_speaker(body, wrong_label=label, canonical_name=canonical_name)
        if renamed:
            recheck = validate_emitted_speaker_against_contract(renamed, contract, resolution=resolution)
            if recheck.get("ok"):
                return renamed
    return ""


def select_preserved_answer(
    candidate: str | None,
    final: str | None,
    resolution: Mapping[str, Any] | None,
    *,
    stashed: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """After post-processing, emit the strongest authority-safe answer still in hand."""
    final_text = str(final or "")
    final_view = semantic_line_view(final_text, resolution)
    info: dict[str, Any] = {
        "downgrade_attempted": False,
        "downgrade_rejected": False,
        "downgrade_reason": None,
        "recovery_used": False,
        "recovery_source": None,
        "destroyed": False,
        "scene_momentum_appended": "\n\n" in final_text,
        "final_outcome_kind": final_view.get("resolution_kind"),
        "final_satisfaction": final_view.get("status"),
    }
    aligned_final = _speaker_aligned_text(final_text, resolution)
    if aligned_final and aligned_final != final_text.strip():
        final_text = aligned_final
        final_view = semantic_line_view(final_text, resolution)
        info["recovery_used"] = True
        info["recovery_source"] = "speaker_retarget"
        info["final_outcome_kind"] = final_view.get("resolution_kind")
        info["final_satisfaction"] = final_view.get("status")
    best_text = ""
    best_rank = -1
    best_source = ""
    for source, text in (("candidate", candidate), ("stashed", stashed)):
        aligned = _speaker_aligned_text(text, resolution)
        rank = _candidate_rank(aligned, resolution) if aligned else -1
        if rank > best_rank:
            best_rank = rank
            best_text = aligned
            best_source = source if aligned == str(text or "").strip() else f"{source}_speaker"
    if best_text:
        allowed, reason = candidate_may_replace(best_text, final_text, resolution)
        info["replacement_reason"] = reason
        if allowed and final_text.strip():
            return final_text, info
        info["downgrade_attempted"] = True
        info["downgrade_rejected"] = True
        info["recovery_used"] = True
        info["recovery_source"] = best_source
        info["downgrade_reason"] = reason
        recovered = semantic_line_view(best_text, resolution)
        info["final_outcome_kind"] = recovered.get("resolution_kind")
        info["final_satisfaction"] = recovered.get("status")
        info["destroyed"] = False
        return best_text, info
    for source, text in (("candidate", candidate), ("stashed", stashed)):
        body = _speaker_aligned_text(text, resolution)
        if not body:
            continue
        view = semantic_line_view(body, resolution)
        choice = body if view.get("keeps_answer") and not genuine_resolution_blocker(body) else ""
        if not choice:
            repaired = repair_answer_locally(body, resolution)
            if repaired and semantic_line_view(repaired, resolution).get("keeps_answer"):
                choice = repaired
                source = f"{source}_repaired"
        if not choice:
            continue
        info["downgrade_attempted"] = True
        info["downgrade_rejected"] = True
        info["recovery_used"] = True
        info["recovery_source"] = source
        info["downgrade_reason"] = "post_processing_destroyed_answer"
        recovered = semantic_line_view(choice, resolution)
        info["final_outcome_kind"] = recovered.get("resolution_kind")
        info["final_satisfaction"] = recovered.get("status")
        info["destroyed"] = False
        return choice, info
    had_answer = any(
        semantic_line_view(text, resolution).get("keeps_answer")
        for text in (candidate, stashed)
        if str(text or "").strip()
    )
    if had_answer and not final_view.get("keeps_answer"):
        info["downgrade_attempted"] = True
        info["destroyed"] = True
        info["downgrade_reason"] = "candidate_invalid" if genuine_resolution_blocker(str(candidate or "")) else "no_valid_answer"
    return final_text, info


def continuation_preserves_resolution(
    current: str | None,
    continuation: str | None,
    resolution: Mapping[str, Any] | None,
) -> bool:
    """Scene momentum may follow a satisfied answer only as a separable, compatible line."""
    view = semantic_line_view(current, resolution)
    if not view.get("keeps_answer"):
        return True
    extra = str(continuation or "").strip()
    if not extra:
        return True
    if _REPEAT_SPLICE_RE.search(extra):
        return False
    combined = str(current or "").rstrip() + "\n\n" + extra
    after = semantic_line_view(combined, resolution)
    if not after.get("keeps_answer"):
        return False
    if "repeat_contaminated" in {str(item) for item in (after.get("reasons") or [])}:
        return False
    return True


def _overlap_count(label: str, text: str) -> tuple[int, int]:
    claim = []
    seen: set[str] = set()
    for word in _content_words(label):
        if word not in seen:
            seen.add(word)
            claim.append(word)
    response = set(_content_words(text))
    hits = [word for word in claim if word in response]
    return len(hits), len(claim)


def _satisfaction(
    contract: Mapping[str, Any],
    *,
    status: str,
    reasons: list[str],
    target_compatible: bool | None = None,
    operation_compatible: bool | None = None,
    dimension_compatible: bool | None = None,
    resolution_kind: str | None = None,
    answer_target: str = "",
    necessary_clarification: bool = False,
) -> dict[str, Any]:
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    return {
        "status": status,
        "reasons": reasons,
        "contract_id": contract.get("contract_id"),
        "operation": contract.get("operation"),
        "target": _contract_target_text(contract) or None,
        "dimension": contract.get("dimension"),
        "discourse_referent": _clean(discourse.get("label") or discourse.get("id"), limit=120) or None,
        "candidate_answer_target": _clean(answer_target, limit=120) or None,
        "target_compatible": target_compatible,
        "operation_compatible": operation_compatible,
        "dimension_compatible": dimension_compatible,
        "resolution_kind": resolution_kind,
        "valid_inability": resolution_kind == "inability",
        "valid_refusal": resolution_kind == "refusal",
        "valid_clarification": resolution_kind == "clarification",
        "necessary_clarification": necessary_clarification,
    }


def _assess_repeat(text: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    label = _claim_label(contract)
    if _GENERIC_ACTION_REFUSAL_RE.search(text):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["generic_action_refusal", "repeat_not_restated"],
            target_compatible=False,
            operation_compatible=False,
            dimension_compatible=None,
            resolution_kind="unrelated",
        )
    if contract.get("ambiguous"):
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["clarification_or_inability"],
            operation_compatible=True,
            resolution_kind="clarification",
        )
    if explicit_nonanswer_response(text):
        kind = "refusal" if _REFUSAL_FRAME_RE.search(text) else "inability"
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["explicit_nonanswer"],
            target_compatible=True,
            operation_compatible=True,
            dimension_compatible=None,
            resolution_kind=kind,
            answer_target=label,
        )
    hits, total = _overlap_count(label, text) if label else (0, 0)
    faithful = total > 0 and (hits >= 2 or (hits / total) >= 0.34)
    if faithful and _repeat_contaminated(label, text):
        return _satisfaction(
            contract,
            status="partial",
            reasons=["repeat_restated", "repeat_contaminated"],
            target_compatible=True,
            operation_compatible=True,
            dimension_compatible=False,
            resolution_kind="answer",
            answer_target=label,
        )
    if faithful:
        return _satisfaction(
            contract,
            status="satisfied",
            reasons=["repeat_restated"],
            target_compatible=True,
            operation_compatible=True,
            dimension_compatible=True,
            resolution_kind="answer",
            answer_target=label,
        )
    if _NEGATIVE_RESOLUTION_RE.search(text) and (_tied_to_request(text, contract) or not label):
        kind = "refusal" if _REFUSAL_FRAME_RE.search(text) else "inability"
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["valid_refusal" if kind == "refusal" else "valid_inability"],
            target_compatible=True,
            operation_compatible=True,
            dimension_compatible=None,
            resolution_kind=kind,
            answer_target=label,
        )
    if total > 0 and hits == 0 and _REPORT_FRAME_RE.search(text):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["repeat_new_content"],
            target_compatible=False,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=label,
        )
    return _satisfaction(
        contract,
        status="unsatisfied",
        reasons=["repeat_not_restated"],
        target_compatible=False,
        operation_compatible=False,
        dimension_compatible=False,
        resolution_kind="unrelated",
        answer_target=label,
    )


def _assess_object(text: str, contract: Mapping[str, Any], *, echoed: bool) -> dict[str, Any]:
    dims = _contract_dims(contract)
    compatible, answer_target, conflict = _target_relation(text, contract)
    if echoed:
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["echo_not_answer"],
            target_compatible=compatible,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=answer_target,
        )
    if _GENERIC_SOCIAL_INFO_RE.search(text):
        reasons = ["perception_routed_to_social_fallback"]
        if dims:
            reasons.append("dimension_not_addressed")
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=reasons,
            target_compatible=compatible,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=answer_target,
        )
    if _GENERIC_ACTION_REFUSAL_RE.search(text):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["generic_action_refusal", "inspection_not_resolved"],
            target_compatible=False,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=answer_target,
        )
    if conflict:
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["target_incompatible"],
            target_compatible=False,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=answer_target,
        )
    if generic_use_nonanswer(text) and DIM_USE in dims:
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["generic_use_nonanswer"],
            target_compatible=compatible is not False,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=answer_target,
        )
    strict = [dim for dim in dims if dim in {DIM_SOUND, DIM_SMELL, DIM_WEAR, DIM_USE, DIM_CHANGE}]
    covered = [dim for dim in dims if dim != DIM_CONTENT and _dimension_covered(text, dim)]
    if compatible is False and not covered:
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["target_incompatible"],
            target_compatible=False,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=answer_target,
        )
    if explicit_nonanswer_response(text):
        kind = "refusal" if _REFUSAL_FRAME_RE.search(text) else "inability"
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["explicit_nonanswer"],
            target_compatible=True if compatible is not False else False,
            operation_compatible=True,
            dimension_compatible=None,
            resolution_kind=kind,
            answer_target=answer_target or _contract_target_text(contract),
        )
    observed = _positive_observation(text)
    meaningful = bool(_meaningful_terms(text, contract))
    mentions_target = not _target_terms(contract) or bool(_expand_terms(_term_set(text)) & _target_terms(contract)) or bool(
        re.search(r"\b(?:it|its|this|that)\b", text, re.IGNORECASE)
    )
    dimension_tied = bool(set(dims) & {DIM_SOUND, DIM_SMELL, DIM_WEAR, DIM_USE, DIM_CHANGE, DIM_APPEARANCE, DIM_CONTENT})
    if _NEGATIVE_RESOLUTION_RE.search(text) and not observed and (mentions_target or dimension_tied):
        kind = "refusal" if _REFUSAL_FRAME_RE.search(text) else "inability"
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["valid_refusal" if kind == "refusal" else "valid_inability"],
            target_compatible=True if compatible is not False else False,
            operation_compatible=True,
            dimension_compatible=None,
            resolution_kind=kind,
            answer_target=answer_target or _contract_target_text(contract),
        )
    if (_GENERIC_OBSERVE_STOCK_RE.search(text) or _GENERIC_INSPECTION_NONANSWER_RE.search(text)) and not _content_observation(text):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["inspection_not_resolved"],
            target_compatible=compatible,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=answer_target,
        )
    if _SCENE_FRAME_RE.search(text) and not covered and not _content_observation(text):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["generic_scene_replaced_dimension", "inspection_not_resolved"],
            target_compatible=compatible,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=answer_target,
        )
    if strict and not any(dim in covered for dim in strict):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["dimension_not_addressed"],
            target_compatible=compatible,
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=answer_target,
        )
    if dims and covered and len(covered) < len([dim for dim in dims if dim != DIM_CONTENT]):
        return _satisfaction(
            contract,
            status="partial",
            reasons=[f"covered:{dim}" for dim in covered] + [f"missing:{dim}" for dim in dims if dim not in covered],
            target_compatible=compatible is not False,
            operation_compatible=True,
            dimension_compatible=False,
            resolution_kind="answer",
            answer_target=answer_target,
        )
    content_required = DIM_CONTENT in dims
    content_met = (not content_required) or _substantive_content(text)
    if content_met and (
        covered
        or (observed and content_met)
        or (meaningful and not _NEGATIVE_RESOLUTION_RE.search(text) and not content_required)
        or (content_required and content_met)
    ):
        if covered:
            reason = "covered:" + ",".join(covered)
        elif content_required:
            reason = "content_addressed"
        else:
            reason = "target_observation"
        return _satisfaction(
            contract,
            status="satisfied",
            reasons=[reason],
            target_compatible=True if compatible is not False else False,
            operation_compatible=True,
            dimension_compatible=True if not dims or len(covered) == len([dim for dim in dims if dim != DIM_CONTENT]) else None,
            resolution_kind="answer",
            answer_target=answer_target or _contract_target_text(contract),
        )
    return _satisfaction(
        contract,
        status="unsatisfied",
        reasons=["inspection_not_resolved"],
        target_compatible=compatible,
        operation_compatible=False,
        dimension_compatible=False,
        resolution_kind="unrelated",
        answer_target=answer_target,
    )


def _assess_dimensionless_inquiry(text: str, contract: Mapping[str, Any], *, echoed: bool) -> dict[str, Any]:
    if echoed:
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["echo_not_answer"],
            operation_compatible=False,
            resolution_kind="unrelated",
        )
    if _GENERIC_ACTION_REFUSAL_RE.search(text):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["generic_action_refusal", "operation_not_addressed"],
            operation_compatible=False,
            target_compatible=False,
            resolution_kind="unrelated",
        )
    meaningful = _meaningful_terms(text, contract)
    if _ACK_ONLY_RE.search(text) and len(meaningful) < 2:
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["topic_acknowledgement"],
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="acknowledgement",
        )
    proposition = bool(re.search(r"\bthat\s+(?:\w+\s+){2,}\w+", text, re.IGNORECASE))
    general_inability = bool(
        re.search(r"\b(?:do not know|don't know|not enough|cannot answer|can't answer|unable to answer)\b", text, re.IGNORECASE)
    )
    if (
        _NEGATIVE_RESOLUTION_RE.search(text)
        and (_tied_to_request(text, contract) or general_inability)
        and not proposition
        and not _positive_observation(text)
    ):
        kind = "refusal" if _REFUSAL_FRAME_RE.search(text) else "inability"
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["valid_refusal" if kind == "refusal" else "valid_inability"],
            operation_compatible=True,
            target_compatible=True,
            resolution_kind=kind,
        )
    if explicit_nonanswer_response(text):
        kind = "refusal" if _REFUSAL_FRAME_RE.search(text) else "inability"
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["explicit_nonanswer"],
            operation_compatible=True,
            target_compatible=True,
            resolution_kind=kind,
        )
    if contract.get("interlocutor_id") and _generic_atmospheric_avoidance(text):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["atmospheric_avoidance"],
            operation_compatible=False,
            target_compatible=True,
            dimension_compatible=False,
            resolution_kind="unrelated",
        )
    if contract.get("interlocutor_id") and _unrelated_narrated_fact(text):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["social_not_resolved"],
            operation_compatible=False,
            target_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
        )
    payload = [word for word in meaningful if word not in _term_set(str(contract.get("raw_input") or ""))]
    reported = bool(_REPORT_FRAME_RE.search(text) and payload)
    direct = len(payload) >= 3 and not (_scene_staging(text) and not _REPORT_FRAME_RE.search(text))
    if reported or direct:
        return _satisfaction(
            contract,
            status="satisfied",
            reasons=["inquiry_answered"],
            operation_compatible=True,
            dimension_compatible=True,
            target_compatible=True,
            resolution_kind="answer",
        )
    return _satisfaction(
        contract,
        status="unsatisfied",
        reasons=["unrelated_fact" if _scene_staging(text) or meaningful else "operation_not_addressed"],
        operation_compatible=False,
        dimension_compatible=False,
        target_compatible=False,
        resolution_kind="unrelated",
    )


def assess_contract_satisfaction(text: str | None, contract: Mapping[str, Any] | None) -> dict[str, Any]:
    """Decide whether player-visible text meets the contract. This is not a generator."""
    if not isinstance(contract, Mapping) or not contract.get("contract_id"):
        return {"status": "not_applicable", "reasons": ["no_contract"]}
    body = _clean(text, limit=2000)
    if not body:
        return {"status": "unsatisfied", "reasons": ["empty_text"], "contract_id": contract.get("contract_id")}
    reasons: list[str] = []
    ambiguity_blocker = bool(
        contract.get("ambiguous")
        or (
            contract.get("expected_resolution") == EXPECT_CLARIFICATION
            and contract.get("referent_provenance") in {PROVENANCE_AMBIGUOUS, PROVENANCE_UNRESOLVED}
        )
    )
    if ambiguity_blocker:
        blocker_dims = _contract_dims(contract)
        blocker_covered = [dim for dim in blocker_dims if _dimension_covered(body, dim)]
        answered = bool(blocker_dims) and len(blocker_covered) == len(blocker_dims)
        if not answered:
            if _is_clarification_text(body):
                return _satisfaction(
                    contract,
                    status="legitimate_nonresolution",
                    reasons=["necessary_clarification"],
                    operation_compatible=True,
                    resolution_kind="clarification",
                    necessary_clarification=True,
                )
            social_dump = bool(_GENERIC_SOCIAL_INFO_RE.search(body))
            if _LEGITIMATE_RE.search(body) and not social_dump:
                kind = "refusal" if _REFUSAL_FRAME_RE.search(body) else "inability"
                return _satisfaction(
                    contract,
                    status="legitimate_nonresolution",
                    reasons=["valid_refusal" if kind == "refusal" else "valid_inability"],
                    operation_compatible=True,
                    resolution_kind=kind,
                )
            reasons.append("clarification_missing")
            return _satisfaction(
                contract,
                status="unsatisfied",
                reasons=reasons,
                operation_compatible=False,
                resolution_kind="unrelated",
            )
    if contract.get("epistemic_mode") == EPISTEMIC_CONSEQUENTIAL:
        if _LEGITIMATE_RE.search(body) or re.search(r"\b(?:won't|will not|cannot|can't|no one|not something)\b", body, re.IGNORECASE):
            return {
                "status": "legitimate_nonresolution",
                "reasons": ["consequential_refused"],
                "contract_id": contract.get("contract_id"),
            }
        return {
            "status": "unsatisfied",
            "reasons": ["consequential_not_refused"],
            "contract_id": contract.get("contract_id"),
        }
    raw_input = str(contract.get("raw_input") or "")
    echoed = player_text_is_echoed(body, raw_input)
    if echoed and (_NEGATIVE_RESOLUTION_RE.search(body) or _REFUSAL_FRAME_RE.search(body)):
        echoed = False
    scored = _strip_player_echo(body, raw_input) if echoed else body
    dims = [str(item) for item in (contract.get("dimensions") or []) if str(item).strip()]
    if not dims and contract.get("dimension"):
        dims = [str(contract.get("dimension"))]
    operation = str(contract.get("operation") or "")
    contract_id = contract.get("contract_id")
    if canonical_existence_denied(body, contract):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["canonical_premise_contradicted"],
            operation_compatible=False,
            target_compatible=False,
            resolution_kind="unrelated",
        )
    if operation in {OP_ACT, OP_FOLLOW, OP_CONFIRM}:
        from game.interpretation_proposal import referential_action_shape

        if referential_action_shape(raw_input) and _LITERAL_STEP_RE.search(body):
            return _satisfaction(
                contract,
                status="unsatisfied",
                reasons=["literal_referent_reinterpretation"],
                operation_compatible=False,
                resolution_kind="unrelated",
            )
        outcome = _action_outcome(scored)
        if outcome == "success":
            return {"status": "satisfied", "reasons": ["action_resolved"], "contract_id": contract_id}
        if outcome == "nonresolution":
            return {
                "status": "legitimate_nonresolution",
                "reasons": ["action_nonresolution"],
                "contract_id": contract_id,
            }
        reasons = ["echo_not_answer"] if echoed else ["action_outcome_missing"]
        if _LONG_VISUAL_RE.search(body):
            reasons.append("generic_scene_replaced_action")
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=reasons,
            operation_compatible=False,
            resolution_kind="unrelated",
        )
    if operation == OP_ASK and scored.strip() and not echoed:
        from game.interaction_completion import ask_structural_block, nonverbal_resolution, quoted_payload

        if nonverbal_resolution(scored) and not quoted_payload(scored):
            return _satisfaction(
                contract,
                status="legitimate_nonresolution",
                reasons=["valid_refusal"],
                operation_compatible=True,
                target_compatible=True,
                resolution_kind="refusal",
            )
        block = ask_structural_block(scored, contract)
        if block:
            return _satisfaction(
                contract,
                status="unsatisfied",
                reasons=[block],
                operation_compatible=False,
                target_compatible=False,
                dimension_compatible=False,
                resolution_kind="unrelated",
            )
    objectish = operation in {OP_INSPECT, OP_PERCEIVE}
    if operation == OP_REPEAT:
        return _assess_repeat(scored, contract)
    if objectish:
        return _assess_object(scored, contract, echoed=echoed)
    if not dims and _specific_inquiry(raw_input, operation):
        return _assess_dimensionless_inquiry(scored, contract, echoed=echoed)
    if not dims:
        if echoed:
            return _satisfaction(contract, status="unsatisfied", reasons=["echo_not_answer"], operation_compatible=False)
        return _satisfaction(
            contract,
            status="unchecked",
            reasons=["no_dimension"],
            operation_compatible=None,
            dimension_compatible=None,
        )
    covered = [dim for dim in dims if _dimension_covered(scored, dim)]
    if echoed and not (covered and len(covered) == len(dims)):
        return _satisfaction(contract, status="unsatisfied", reasons=["echo_not_answer"], operation_compatible=False)
    if _GENERIC_ACTION_REFUSAL_RE.search(scored):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["generic_action_refusal", "operation_not_addressed"],
            operation_compatible=False,
            resolution_kind="unrelated",
        )
    if explicit_nonanswer_response(scored):
        kind = "refusal" if _REFUSAL_FRAME_RE.search(scored) else "inability"
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["explicit_nonanswer"],
            operation_compatible=True,
            dimension_compatible=None,
            resolution_kind=kind,
        )
    if DIM_CONTENT in dims and _ACK_ONLY_RE.search(scored) and len(_meaningful_terms(scored, contract)) < 2:
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["topic_acknowledgement"],
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="acknowledgement",
        )
    if DIM_CONTENT in dims and _GENERIC_SOCIAL_INFO_RE.search(scored) and not _substantive_content(scored):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["social_not_resolved"],
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
        )
    if covered and len(covered) == len(dims):
        return _satisfaction(
            contract,
            status="satisfied",
            reasons=[f"covered:{dim}" for dim in covered],
            operation_compatible=True,
            dimension_compatible=True,
            resolution_kind="answer",
        )
    if covered:
        return _satisfaction(
            contract,
            status="partial",
            reasons=[f"covered:{dim}" for dim in covered] + [f"missing:{dim}" for dim in dims if dim not in covered],
            operation_compatible=True,
            dimension_compatible=False,
            resolution_kind="answer",
        )
    if str(contract.get("operation") or "") == OP_ASK and contract.get("interlocutor_id") and _generic_atmospheric_avoidance(scored):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["atmospheric_avoidance"],
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
        )
    if str(contract.get("operation") or "") == OP_ASK and contract.get("interlocutor_id") and _unrelated_narrated_fact(scored):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["social_not_resolved"],
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
        )
    if _is_clarification_text(scored):
        needed = necessary_clarification(scored, contract)
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["necessary_clarification" if needed else "clarification_or_inability"],
            operation_compatible=True,
            dimension_compatible=None,
            resolution_kind="clarification",
            necessary_clarification=needed,
        )
    foreign = _foreign_claim_dimension(scored, set(dims))
    if foreign:
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["dimension_substituted", "dimension_not_addressed"],
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
            answer_target=foreign,
        )
    strict_perception = set(dims) & {DIM_SOUND, DIM_SMELL, DIM_WEAR, DIM_USE, DIM_CHANGE}
    if strict_perception and _GENERIC_SOCIAL_INFO_RE.search(scored):
        return _satisfaction(
            contract,
            status="unsatisfied",
            reasons=["perception_routed_to_social_fallback", "dimension_not_addressed"],
            operation_compatible=False,
            dimension_compatible=False,
            resolution_kind="unrelated",
        )
    if _LEGITIMATE_RE.search(scored):
        kind = "refusal" if _REFUSAL_FRAME_RE.search(scored) else "inability"
        return _satisfaction(
            contract,
            status="legitimate_nonresolution",
            reasons=["valid_refusal" if kind == "refusal" else "valid_inability"],
            operation_compatible=True,
            dimension_compatible=None,
            resolution_kind=kind,
        )
    reasons: list[str] = []
    if set(dims) & {DIM_SOUND, DIM_SMELL, DIM_WEAR, DIM_USE, DIM_CHANGE, DIM_SOURCE, DIM_CONFIDENCE} and _LONG_VISUAL_RE.search(body):
        reasons.append("generic_scene_replaced_dimension")
    reasons.append("dimension_not_addressed")
    return _satisfaction(
        contract,
        status="unsatisfied",
        reasons=reasons,
        operation_compatible=False,
        dimension_compatible=False,
        resolution_kind="unrelated",
    )


def semantic_line_view(text: str | None, resolution: Mapping[str, Any] | None) -> dict[str, Any]:
    """How player-visible text sits against the active Resolution Contract.

    ``keeps_answer`` means the line actually resolves the contract.
    ``compatible`` includes a genuine inability or clarification.
    An unrelated grounded fact is neither.
    """
    contract = contract_mapping_from_resolution(resolution)
    if not contract:
        return {
            "contract_id": None,
            "dimension": None,
            "operation": None,
            "status": "not_applicable",
            "reasons": ["no_contract"],
            "keeps_answer": False,
            "compatible": True,
        }
    assessment = assess_contract_satisfaction(text, contract)
    status = str(assessment.get("status") or "")
    return {
        "contract_id": contract.get("contract_id"),
        "dimension": contract.get("dimension"),
        "dimensions": list(contract.get("dimensions") or []),
        "operation": contract.get("operation"),
        "target": assessment.get("target"),
        "discourse_referent": assessment.get("discourse_referent"),
        "candidate_answer_target": assessment.get("candidate_answer_target"),
        "status": status,
        "reasons": list(assessment.get("reasons") or []),
        "target_compatible": assessment.get("target_compatible"),
        "operation_compatible": assessment.get("operation_compatible"),
        "dimension_compatible": assessment.get("dimension_compatible"),
        "resolution_kind": assessment.get("resolution_kind"),
        "valid_inability": assessment.get("valid_inability"),
        "valid_refusal": assessment.get("valid_refusal"),
        "valid_clarification": assessment.get("valid_clarification"),
        "necessary_clarification": assessment.get("necessary_clarification"),
        "keeps_answer": status == "satisfied",
        "compatible": status in {"satisfied", "legitimate_nonresolution", "partial", "unchecked", "not_applicable"},
    }


def detect_semantic_degradation(
    before: str | None,
    after: str | None,
    resolution: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Whether a later candidate lost resolution an earlier safe candidate had.

    Equal rank does not hide the loss. A rank drop, a missing requested
    dimension, a clarification replaced by generic inability, or a dropped
    target all count. This does not choose the emitted line.
    """
    before_text = str(before or "").strip()
    after_text = str(after or "").strip()
    if not before_text or before_text == after_text:
        return {"degraded": False, "reasons": []}
    before_view = semantic_line_view(before_text, resolution)
    after_view = semantic_line_view(after_text, resolution)
    before_rank = resolution_rank(before_view)
    after_rank = resolution_rank(after_view)
    before_covered = set(resolution_coverage(before_text, resolution).get("covered_dimensions") or [])
    after_covered = set(resolution_coverage(after_text, resolution).get("covered_dimensions") or [])
    reasons: list[str] = []
    if after_rank < before_rank:
        reasons.append("lower_rank")
    if before_covered - after_covered:
        reasons.append("requested_dimension_loss")
    if before_view.get("necessary_clarification") and after_view.get("resolution_kind") == "inability":
        reasons.append("clarification_replaced_by_inability")
    if (
        before_view.get("target_compatible") is not False
        and after_view.get("target_compatible") is False
        and (after_rank < before_rank or before_covered - after_covered)
    ):
        reasons.append("target_loss")
    if before_view.get("keeps_answer") and not after_view.get("keeps_answer") and "lower_rank" not in reasons:
        reasons.append("proposition_loss")
    from game.interaction_completion import degradation_reasons

    contract = contract_mapping_from_resolution(resolution)
    for reason in degradation_reasons(before_text, after_text, contract):
        if reason not in reasons:
            reasons.append(reason)
    return {"degraded": bool(reasons), "reasons": reasons}


def retain_resolved_contract_text(
    previous: str | None,
    candidate: str | None,
    resolution: Mapping[str, Any] | None,
) -> tuple[str, bool]:
    """Keep a resolved answer when a later candidate drops that resolution."""
    prev = str(previous or "")
    nxt = str(candidate or "")
    allowed, _reason = candidate_may_replace(prev, nxt, resolution)
    if prev.strip() and not allowed:
        return prev, True
    return nxt, False


def note_response_stage(
    gm: dict[str, Any] | None,
    *,
    stage: str,
    reason: str | None,
    before: str | None,
    after: str | None,
    resolution: Mapping[str, Any] | None,
) -> None:
    """Record one candidate transition without a second model pass."""
    if not isinstance(gm, dict):
        return
    metadata = gm.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        return
    debug = metadata.setdefault("emission_debug", {})
    if not isinstance(debug, dict):
        return
    before_view = semantic_line_view(before, resolution)
    after_view = semantic_line_view(after, resolution)
    before_coverage = resolution_coverage(before, resolution)
    after_coverage = resolution_coverage(after, resolution)
    allowed, replacement_reason = candidate_may_replace(before, after, resolution)
    contract = contract_mapping_from_resolution(resolution)
    transitions = debug.setdefault("candidate_transitions", [])
    if not isinstance(transitions, list):
        transitions = []
        debug["candidate_transitions"] = transitions
    best_before = str(debug.get("best_safe_candidate") or "")
    transitions.append(
        {
            "stage": stage,
            "reason": reason,
            "contract_id": contract.get("contract_id"),
            "operation": contract.get("operation"),
            "target": _contract_target_text(contract) or None,
            "interlocutor": contract.get("interlocutor_id"),
            "dimension": contract.get("dimension"),
            "expected_resolution": contract.get("expected_resolution"),
            "satisfaction_before": before_view.get("status"),
            "satisfaction_after": after_view.get("status"),
            "rank_before": resolution_rank(before_view),
            "rank_after": resolution_rank(after_view),
            "coverage_before": before_coverage.get("covered_dimensions"),
            "coverage_after": after_coverage.get("covered_dimensions"),
            "replacement_decision": "accepted" if allowed else "rejected",
            "replacement_reason": replacement_reason,
            "best_safe_candidate_before": best_before[:180],
            "selected_preview": str(after or "")[:180],
            "invalidation_reason": (debug.get("best_safe_invalidation") or {}).get("reason")
            if isinstance(debug.get("best_safe_invalidation"), dict)
            else None,
        }
    )


_GROUNDING_LOCK_TAGS = frozenset({
    "perception_non_invention",
    "referenced_surface_realization",
    "destination_arrival_realization",
})


def enforce_emitted_contract_monotonicity(
    gm: dict[str, Any] | None,
    resolution: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Immediately before emission, do not keep a weaker candidate than the best safe one.

    An explicit grounding or surface correction is not a weaker answer. It
    invalidates the candidate it replaced, and that candidate cannot return.
    """
    if not isinstance(gm, dict) or not isinstance(resolution, Mapping):
        return gm
    from game.immutable_valid_response import response_is_immutable, restore_accepted_text, note_mutator_skipped

    if response_is_immutable(gm):
        note_mutator_skipped(gm, "enforce_emitted_contract_monotonicity")
        current_text = str(gm.get("player_facing_text") or "")
        metadata_now = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
        debug_now = metadata_now.get("emission_debug") if isinstance(metadata_now, dict) else {}
        stashed_now = ""
        if isinstance(debug_now, dict):
            stashed_now = str(debug_now.get("best_safe_candidate") or debug_now.get("satisfied_candidate") or "")
        chosen_now, info_now = select_preserved_answer(stashed_now, current_text, resolution, stashed=stashed_now)
        if isinstance(debug_now, dict):
            debug_now["legacy_would_emit"] = str(chosen_now or "")[:500]
            debug_now["legacy_comparison"] = dict(info_now)
            debug_now["legacy_emission_authority"] = False
        restore_accepted_text(gm)
        return gm
    current = str(gm.get("player_facing_text") or "")
    tags = {str(item) for item in (gm.get("tags") or []) if str(item).strip()}
    metadata = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    debug = metadata.get("emission_debug") if isinstance(metadata, dict) else {}
    if tags & _GROUNDING_LOCK_TAGS:
        if isinstance(debug, dict):
            prior = str(debug.get("best_safe_candidate") or debug.get("satisfied_candidate") or "")
            if prior.strip() and prior.strip() != current.strip():
                invalidate_best_safe_candidate(gm, reason="grounding_contradiction", candidate=prior)
        remember_satisfied_candidate(gm, current, resolution)
        note_response_stage(
            gm,
            stage="final_emission",
            reason="grounding_correction_authoritative",
            before=current,
            after=current,
            resolution=resolution,
        )
        if isinstance(debug, dict):
            prior_info = debug.get("outcome_precedence") if isinstance(debug.get("outcome_precedence"), dict) else {}
            debug["outcome_precedence"] = {
                **prior_info,
                "downgrade_attempted": False,
                "downgrade_rejected": False,
                "downgrade_reason": "grounding_correction_authoritative",
                "stage": "final_emission",
            }
            debug["final_selected_candidate"] = current[:2000]
            debug["final_resolution_coverage"] = resolution_coverage(current, resolution)
        return gm
    remember_satisfied_candidate(gm, current, resolution)
    metadata = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    debug = metadata.get("emission_debug") if isinstance(metadata, dict) else {}
    stashed = ""
    if isinstance(debug, dict):
        stashed = str(debug.get("best_safe_candidate") or debug.get("satisfied_candidate") or "")
    chosen, info = select_preserved_answer(stashed, current, resolution, stashed=stashed)
    if chosen.strip() and chosen.strip() != current.strip():
        gm["player_facing_text"] = chosen
        info = dict(info)
        info["stage"] = "final_emission"
    else:
        info = dict(info)
        if stashed.strip() and not _speaker_aligned_text(stashed, resolution) and chosen.strip() == current.strip():
            debug_map = metadata.get("emission_debug") if isinstance(metadata, dict) else None
            if isinstance(debug_map, dict):
                debug_map["best_safe_invalidation"] = {
                    "reason": "speaker_contract",
                    "candidate": stashed[:180],
                }
    from game.interaction_completion import generic_ask_completion, structural_assessment

    visible_contract = contract_mapping_from_resolution(resolution)
    visible = str(gm.get("player_facing_text") or "")
    if str(visible_contract.get("operation") or "") == OP_ASK and not structural_assessment(visible, visible_contract).get("valid"):
        repaired = generic_ask_completion(visible_contract)
        if repaired and repaired.strip() != visible.strip():
            gm["player_facing_text"] = repaired
            info = dict(info)
            info["recovery_used"] = True
            info["recovery_source"] = "structural_completion"
            info["downgrade_reason"] = "structurally_incomplete"
    note_response_stage(
        gm,
        stage="final_emission",
        reason=str(info.get("downgrade_reason") or "compared"),
        before=current,
        after=str(gm.get("player_facing_text") or ""),
        resolution=resolution,
    )
    if isinstance(debug, dict):
        prior = debug.get("outcome_precedence") if isinstance(debug.get("outcome_precedence"), dict) else {}
        debug["outcome_precedence"] = {**prior, **info}
        debug["final_selected_candidate"] = str(gm.get("player_facing_text") or "")[:2000]
        debug["final_resolution_coverage"] = resolution_coverage(str(gm.get("player_facing_text") or ""), resolution)
        earlier = str(debug.get("initial_safe_candidate") or "")
        report = detect_semantic_degradation(earlier, str(gm.get("player_facing_text") or ""), resolution)
        debug["semantic_degradation"] = bool(report.get("degraded"))
        debug["semantic_degradation_reasons"] = list(report.get("reasons") or [])
    return gm


def contract_trace(
    contract: Mapping[str, Any] | None,
    *,
    focus: Mapping[str, Any] | None = None,
    obligation_kind: str | None = None,
    authority_route: str | None = None,
    semantic: Mapping[str, Any] | None = None,
    retry_preserved: bool = False,
) -> dict[str, Any]:
    semantic_map = dict(semantic) if isinstance(semantic, Mapping) else {}
    reason_text = " ".join(str(item) for item in (semantic_map.get("reasons") or []))
    claim = focus.get("active_claim") if isinstance(focus, Mapping) else None
    claim_source = claim.get("source") if isinstance(claim, Mapping) else ""
    return {
        "event": "resolution_contract",
        "raw_input": (contract or {}).get("raw_input") if isinstance(contract, Mapping) else None,
        "resolution_contract": generation_projection(contract),
        "referent_provenance": (contract or {}).get("referent_provenance") if isinstance(contract, Mapping) else None,
        "discourse_ref": (contract or {}).get("discourse_ref") if isinstance(contract, Mapping) else None,
        "discourse_focus": focus_summary(focus),
        "interaction_obligation_kind": obligation_kind,
        "authority_route": authority_route,
        "semantic_result": semantic_map or None,
        "echo_detected": "echo_not_answer" in reason_text,
        "action_outcome": next((item for item in reason_text.split() if item.startswith("action_")), None),
        "claim_promoted": claim_source in {"emitted_npc_claim", "claim_ledger"},
        "retry_preserved": bool(retry_preserved),
        "construction": (contract or {}).get("construction") if isinstance(contract, Mapping) else None,
    }
