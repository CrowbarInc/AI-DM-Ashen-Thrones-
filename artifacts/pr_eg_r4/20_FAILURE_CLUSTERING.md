# 20 — Failure Clustering

```json
[
  {
    "id": "adoption",
    "mechanism": "Post-validation fact preservation",
    "severity": "CRITICAL",
    "evidence": [
      "B_skeptical:9"
    ],
    "frequency": "1/69 delivered target-corpus turns",
    "impact": "Rejected speaker/target speech reaches delivery and delivered history via a new wrapper.",
    "source": "game/api_turn_support.py:330,858; game/api.py:5873",
    "scope": "Focused post-gate authority/adoption repair; no new semantic architecture justified yet."
  },
  {
    "id": "interpretation",
    "mechanism": "Lexical addressee and conversational/compound-action interpretation",
    "severity": "BLOCKING",
    "evidence": [
      "A_cooperative:4",
      "A_casual:1,3,10,14",
      "A_playful:1–10"
    ],
    "frequency": "Multi-label symptom counts in failure_counts.json; overlapping mechanisms are not summed as unique turns.",
    "impact": "Natural greetings, sequencing and direct names repeatedly become clarification or action execution instructions.",
    "source": "game/interaction_completion.py:627; game/ordinary_semantic_ownership.py:643; game/conversational_orchestration.py:752",
    "scope": "Focused recognition/grounding investigation after the integrity repair."
  },
  {
    "id": "selection",
    "mechanism": "Subject token overlap and answer sufficiency",
    "severity": "BLOCKING",
    "evidence": [
      "A_cooperative:7–14",
      "A_curious:13–15",
      "B_skeptical:1–9"
    ],
    "frequency": "Persistent within three completed conversations and the interrupted harbor conversation; see F02/F09/F10/F17.",
    "impact": "Safe facts are selected as answers to different questions, so repetition and rephrasing do not recover.",
    "source": "game/social.py:1564,1587,1611; game/dialogue_authority.py:220",
    "scope": "Study general/clarification sufficiency and referent-vs-request separation; do not add vocabulary exceptions."
  },
  {
    "id": "history",
    "mechanism": "Early unparsed return omits delivered-history entry",
    "severity": "MAJOR",
    "evidence": [
      "A_playful:6"
    ],
    "frequency": "1/69 observed missing product-history entries",
    "impact": "The player sees a response that the product's conversational store does not remember; external transcript remains intact.",
    "scope": "Localized return-path history audit after the integrity blocker."
  },
  {
    "id": "expression",
    "mechanism": "Rigid fallback / narrow characterization",
    "severity": "MAJOR",
    "evidence": [
      "A_cooperative:5,6,14,15",
      "A_curious:8,10",
      "A_playful:12–14"
    ],
    "frequency": "Provider failure taxonomy retained; unknown factual details are not automatically treated as false ignorance.",
    "impact": "Some genuine unknowns are handled safely, but blanket phrases do not support flexible small talk or establish distinct people.",
    "scope": "Insufficient personal-scene coverage for a broad architecture conclusion; do not expand R4."
  },
  {
    "id": "cost",
    "mechanism": "Broad narration and retry path",
    "severity": "MAJOR",
    "evidence": [
      "A_playful:11"
    ],
    "frequency": "1 outlier turn with 3 engine calls and 2 retries",
    "impact": "81,078 input tokens on a wrong-speaker response; no evidence of a systemic unbounded retry loop.",
    "scope": "Measure route eligibility after correctness work, not broad performance optimization."
  }
]
```

Clusters are hypotheses supported by symptoms and source inspection, not experimentally proven repairs. Several symptoms can share the same mechanism.
