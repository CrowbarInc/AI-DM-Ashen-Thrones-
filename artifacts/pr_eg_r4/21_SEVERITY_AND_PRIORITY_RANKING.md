# 21 — Severity and Priority Ranking

```json
[
  {
    "rank": 1,
    "cluster": "adoption",
    "severity": "CRITICAL",
    "frequency": "1/69 delivered target-corpus turns",
    "player_impact": "Rejected speaker/target speech reaches delivery and delivered history via a new wrapper.",
    "recoverability": "Stop required; downstream restoration defeats the gate",
    "architectural_significance": "Authority finality",
    "estimated_scope": "Focused post-gate authority/adoption repair; no new semantic architecture justified yet."
  },
  {
    "rank": 2,
    "cluster": "interpretation",
    "severity": "BLOCKING",
    "frequency": "Multi-label symptom counts in failure_counts.json; overlapping mechanisms are not summed as unique turns.",
    "player_impact": "Natural greetings, sequencing and direct names repeatedly become clarification or action execution instructions.",
    "recoverability": "Mostly poor; audited episodes show repeated failure despite clarification",
    "architectural_significance": "Lexical addressee and conversational/compound-action interpretation",
    "estimated_scope": "Focused recognition/grounding investigation after the integrity repair."
  },
  {
    "rank": 3,
    "cluster": "selection",
    "severity": "BLOCKING",
    "frequency": "Persistent within three completed conversations and the interrupted harbor conversation; see F02/F09/F10/F17.",
    "player_impact": "Safe facts are selected as answers to different questions, so repetition and rephrasing do not recover.",
    "recoverability": "Mostly poor; audited episodes show repeated failure despite clarification",
    "architectural_significance": "Subject token overlap and answer sufficiency",
    "estimated_scope": "Study general/clarification sufficiency and referent-vs-request separation; do not add vocabulary exceptions."
  },
  {
    "rank": 4,
    "cluster": "history",
    "severity": "MAJOR",
    "frequency": "1/69 observed missing product-history entries",
    "player_impact": "The player sees a response that the product's conversational store does not remember; external transcript remains intact.",
    "recoverability": "Mostly poor; audited episodes show repeated failure despite clarification",
    "architectural_significance": "Early unparsed return omits delivered-history entry",
    "estimated_scope": "Localized return-path history audit after the integrity blocker."
  },
  {
    "rank": 5,
    "cluster": "expression",
    "severity": "MAJOR",
    "frequency": "Provider failure taxonomy retained; unknown factual details are not automatically treated as false ignorance.",
    "player_impact": "Some genuine unknowns are handled safely, but blanket phrases do not support flexible small talk or establish distinct people.",
    "recoverability": "Mostly poor; audited episodes show repeated failure despite clarification",
    "architectural_significance": "Rigid fallback / narrow characterization",
    "estimated_scope": "Insufficient personal-scene coverage for a broad architecture conclusion; do not expand R4."
  },
  {
    "rank": 6,
    "cluster": "cost",
    "severity": "MAJOR",
    "frequency": "1 outlier turn with 3 engine calls and 2 retries",
    "player_impact": "81,078 input tokens on a wrong-speaker response; no evidence of a systemic unbounded retry loop.",
    "recoverability": "Mostly poor; audited episodes show repeated failure despite clarification",
    "architectural_significance": "Broad narration and retry path",
    "estimated_scope": "Measure route eligibility after correctness work, not broad performance optimization."
  }
]
```

Rank accounts for frequency, severity, player impact, recoverability, architectural significance and estimated repair scope. No implementation was started.
