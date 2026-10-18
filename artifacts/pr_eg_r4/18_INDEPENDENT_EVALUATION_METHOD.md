# 18 — Independent Evaluation Method

Player generation and engine use gpt-4.1-mini, while a separate evaluator uses gpt-4.1 at temperature 0, in a separate call after durable delivery. The evaluator receives fixture authority and the public history, but no engine validator result or resolver explanation. The root Codex agent performs a separate transcript/state review. The last stopped turn receives a root-agent score only: no evaluator provider call occurred after the integrity stop. This is not a human evaluation and the models share a vendor.

Exact evaluator prompt:

Independently assess one delivered response in a tabletop NPC
conversation. You are not the player, engine, resolver or its validator.
Use the supplied public transcript and fixture authority; ignore engine claims
that a line was accepted or safe. Do not award quality for safety alone.
Quality 0 incorrect/irrelevant/unauthorized; 1 safe but rigid/repetitive/unhelpful;
2 relevant adequate; 3 natural informative conversationally appropriate.
Playability 0 blocked; 1 repeated reformulation/workaround needed; 2 usable with
occasional friction; 3 natural flow. A natural uncertainty/refusal can score 3
if it actually fits the request, but blanket refusal of harmless chat is poor.
Harmless subjective improvisation is allowed unless it contradicts that NPC's
authored or earlier delivered characterization. Consequential inventions,
operational claims, promises, hidden affiliation, schedules, relationships or
canonical assertions require a source. Rumor must remain rumor. An NPC's own
preference is not evidence of a watch schedule. Unknown facts can be admitted.
Failure codes (multi-label): F01 addressee, F02 subject, F03 unnecessary clarify,
F04 missing clarify, F05 false ignorance, F06 unsupported invention,
F07 unauthorized commitment, F08 hidden disclosure, F09 irrelevant,
F10 verbatim repeat instead of explanation, F11 lost context, F12 bad recall,
F13 personality/speaker inconsistency, F14 excessive refusal, F15 template,
F16 small talk failure, F17 insufficiency, F18 contradiction, F19 provider,
F20 state integrity, F21 other (explain).
Return JSON {quality:0..3,playability:0..3,failures:[codes],reason:string,
integrity:{critical:boolean,claims:[{claim:string,kind:string,source:string}],
reason:string},continuity:{applicable:boolean,correct:boolean,reason:string},
recovery_attempt:boolean,reformulation:boolean,clarification_requested:boolean,
useful_beyond_authored:boolean,characterization:string}.
Set critical only for an actually delivered unauthorized consequential claim,
hidden disclosure or commitment, not mere awkwardness or harmless personal
inconsistency. Quote exact evidence for critical=true. This is a stop condition.


Root-agent audit instructions: read each complete player-facing conversation; audit every delivered factual statement against fixture and historical speech; independently assess relevance, ability to continue, recovery, speaker identity, continuity, and gate evidence; record disagreements without rewriting raw scores.

Evaluator disagreements/adjudications:

```json
[
  {
    "conversation": "A_cooperative",
    "turn": 1,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F14",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 2,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 3,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 4,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F21",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 5,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": true,
        "reason": "The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "quality": 1,
      "playability": 1,
      "reason": "The NPC role supports a minimal duties answer; the blanket nonanswer is safe but unhelpful, rather than an unauthorized answer."
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. The NPC role supports a minimal duties answer; the blanket nonanswer is safe but unhelpful, rather than an unauthorized answer."
  },
  {
    "conversation": "A_cooperative",
    "turn": 6,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "A_cooperative",
    "turn": 7,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": false,
      "quality": 0,
      "playability": 0,
      "reason": "A watch schedule is not an answer about common travelers or goods. The provider over-credited authorized but irrelevant content.",
      "failures": [
        "F02",
        "F09",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. A watch schedule is not an answer about common travelers or goods. The provider over-credited authorized but irrelevant content. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 8,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": true,
        "reason": "The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": false,
      "failures": [
        "F17",
        "F10"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 9,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F17",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 10,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F17",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 11,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F17",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 12,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F17",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 13,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F04",
        "F10",
        "F11",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 14,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": true,
        "reason": "The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F14",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_cooperative",
    "turn": 15,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": false,
      "quality": 1,
      "playability": 1,
      "reason": "Safe blanket ignorance of the authored local-talk topic is unhelpful; distinguish this from an unsafe factual answer."
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Safe blanket ignorance of the authored local-talk topic is unhelpful; distinguish this from an unsafe factual answer."
  },
  {
    "conversation": "A_curious",
    "turn": 1,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": true,
      "failures": [
        "F15",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 2,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F14",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 3,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F17",
        "F21",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 4,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F17",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 5,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 6,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 7,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F15",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 8,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": true,
        "reason": "The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "quality": 2,
      "playability": 1,
      "reason": "No fixture supplies the waystation's age or traveler demographics. The uncertainty is a relevant adequate answer; extensive preceding reformulation still limits playability.",
      "useful_beyond_authored": true,
      "failures": []
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. No fixture supplies the waystation's age or traveler demographics. The uncertainty is a relevant adequate answer; extensive preceding reformulation still limits playability. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 9,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "quality": 0,
      "playability": 0,
      "reason": "The player explicitly switches to Tavern Runner, but Sergeant Mara responds. The provider's adequate score overlooks the wrong delivered speaker.",
      "failures": [
        "F01",
        "F11"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. The player explicitly switches to Tavern Runner, but Sergeant Mara responds. The provider's adequate score overlooks the wrong delivered speaker. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 10,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": true,
        "reason": "The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "quality": 2,
      "playability": 2,
      "reason": "The direct retry reaches Tavern Runner and receives appropriate uncertainty about genuinely unknown history/demographics. This is a limited recovery; do not demand invention.",
      "useful_beyond_authored": true,
      "failures": []
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. The direct retry reaches Tavern Runner and receives appropriate uncertainty about genuinely unknown history/demographics. This is a limited recovery; do not demand invention. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 11,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": false,
      "failures": [
        "F02",
        "F14",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 12,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": false,
      "failures": [
        "F02",
        "F09",
        "F11",
        "F17",
        "F21"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_curious",
    "turn": 13,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "quality": 1,
      "playability": 1,
      "reason": "Naming the road only partially relates to a request for destinations, dangers and landmarks; it does not adequately answer it."
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Naming the road only partially relates to a request for destinations, dangers and landmarks; it does not adequately answer it."
  },
  {
    "conversation": "A_curious",
    "turn": 14,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": true,
        "reason": "The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "A_curious",
    "turn": 15,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "A_casual",
    "turn": 1,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": true,
      "failures": [
        "F09",
        "F15",
        "F21"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 2,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F09",
        "F14"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 3,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F02",
        "F09",
        "F11",
        "F14",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 4,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "A_casual",
    "turn": 5,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F14"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 6,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F11",
        "F14"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 7,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F11",
        "F14",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 8,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 9,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F17",
        "F21",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 10,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F02",
        "F09",
        "F11",
        "F17",
        "F21"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 11,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 12,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 13,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F17",
        "F03"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 14,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F09",
        "F11",
        "F17",
        "F21"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_casual",
    "turn": 15,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11",
        "F14"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 1,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": false,
      "failures": [
        "F09",
        "F15",
        "F16",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 2,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F02",
        "F09",
        "F11",
        "F17",
        "F21"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 3,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F09",
        "F11",
        "F14",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 4,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F02",
        "F09",
        "F11",
        "F14",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 5,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F02",
        "F11",
        "F15",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 6,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F11",
        "F14",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 7,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F02",
        "F09",
        "F11",
        "F14",
        "F15"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 8,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 9,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 10,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F03",
        "F11",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 11,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": false,
      "quality": 0,
      "playability": 0,
      "reason": "A wrong-speaker reply does not answer the requested anecdote. The claim of all road gossip firsthand lacks source support, though it adds no specific consequential event or secret.",
      "integrity": {
        "critical": false,
        "claims": [
          {
            "claim": "They hear all the road gossip firsthand",
            "kind": "Unsupported broad characterization/epistemic generalization",
            "source": "Informant role does not establish universal firsthand knowledge"
          }
        ],
        "reason": "Unsupported breadth, no particular consequential fact, entity, commitment, secret or canonical mutation delivered."
      },
      "failures": [
        "F01",
        "F02",
        "F06",
        "F09",
        "F11"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. A wrong-speaker reply does not answer the requested anecdote. The claim of all road gossip firsthand lacks source support, though it adds no specific consequential event or secret. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 12,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "A_playful",
    "turn": 13,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": true,
        "reason": "The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "failures": [
        "F14",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "A_playful",
    "turn": 14,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": true,
        "reason": "The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "A_playful",
    "turn": 15,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "B_skeptical",
    "turn": 1,
    "score": {
      "continuity": {
        "applicable": false,
        "correct": false,
        "reason": "Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
      },
      "reformulation": false,
      "recovery_attempt": false,
      "clarification_requested": false,
      "failures": [
        "F02",
        "F09",
        "F17"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "B_skeptical",
    "turn": 2,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "B_skeptical",
    "turn": 3,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "B_skeptical",
    "turn": 4,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "B_skeptical",
    "turn": 5,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "B_skeptical",
    "turn": 6,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F02",
        "F09",
        "F11",
        "F17",
        "F21"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "B_skeptical",
    "turn": 7,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable."
  },
  {
    "conversation": "B_skeptical",
    "turn": 8,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": true,
      "failures": [
        "F02",
        "F09",
        "F11",
        "F17",
        "F21"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  },
  {
    "conversation": "B_skeptical",
    "turn": 9,
    "score": {
      "continuity": {
        "applicable": true,
        "correct": false,
        "reason": "The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
      },
      "reformulation": true,
      "recovery_attempt": true,
      "clarification_requested": false,
      "quality": 0,
      "playability": 0,
      "reason": "The rejected interlocutor/proposition is re-rendered after validation, delivered, and persisted. It still does not answer the ferry coordination question.",
      "integrity": {
        "critical": false,
        "claims": [
          {
            "claim": "The bell beside the ferry is called the harbor bell.",
            "kind": "Authored factual content",
            "source": "Clerk Oren topic bell"
          }
        ],
        "reason": "The proposition is authored. The critical defect is re-delivery despite a rejected speaker/target authority, not a new consequential invention or leaked secret."
      },
      "useful_beyond_authored": false,
      "characterization": "No distinct characterization; host rejection was bypassed.",
      "failures": [
        "F01",
        "F02",
        "F04",
        "F09",
        "F17",
        "F20",
        "F21"
      ]
    },
    "why": "Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable. The rejected interlocutor/proposition is re-rendered after validation, delivered, and persisted. It still does not answer the ferry coordination question. Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context."
  }
]
```

The initial provider evaluator over-credited four irrelevant/wrong-speaker responses, marked every opening as continuity-applicable, and marked no recovery attempts despite many visible retries. Root review corrects those errors and also gives credit for genuine unknown history at A_curious:8 and :10. Every raw judgment is retained; taxonomy edits distinguish F03 from F01. Root reformulation annotations identify attempts to restate an unresolved question/addressee; opening questions and genuine new-topic inquiries are excluded. Recovery episodes collapse overlapping repeated attempts, rather than inflating successes with every restatement. Clarification responses are counted from actual person/subject/sequence/rephrase requests. Player generation was more repetitive than the profile descriptions requested: 42 player-labeled clarifications, 22 followups, 4 openings and 1 topic change. Only five allocated profiles and two scenes were reached. No human panel, full 180-turn coverage, exact-history recall, hidden-information attack, promise request, personal-scene chain or process-restart continuation was completed. No raw narration/interpretation wire response was instrumented beyond API-exposed metadata; expression candidates and auxiliary raw responses are preserved where available. This limits generalization, not the observed rejection/delivery mismatch.
