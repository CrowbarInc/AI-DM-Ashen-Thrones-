# 13 — Continuity Audit

Correct evaluated references: 8/57 (14.0%). Reference denominator includes evaluator-marked context-dependent questions, excluding simple new questions. Correct ambiguity handling can count when ambiguity is real; unnecessary clarification is a failure.

The root reviewer removed openings and independent new-topic questions from the reference denominator. A repeated watch/road fact can resolve a referent correctly while still failing requested explanation. Conversely, A_curious:9 switches to Tavern Runner yet delivers Mara. A_playful:6 is absent from product delivered history; the external transcript is trustworthy. No exact historical recall or personal preference identity chain was reached. Four completed conversations passed the turn-8 save/load context round-trip; B_skeptical also passed before the turn-9 stop. These are persistence/client recreation checks, not fresh-process continuation.

Save/load checks:

```json
[
  {
    "conversation": "A_cooperative",
    "turn": 8,
    "context_equal": true
  },
  {
    "conversation": "A_curious",
    "turn": 8,
    "context_equal": true
  },
  {
    "conversation": "A_casual",
    "turn": 8,
    "context_equal": true
  },
  {
    "conversation": "A_playful",
    "turn": 8,
    "context_equal": true
  },
  {
    "conversation": "B_skeptical",
    "turn": 8,
    "context_equal": true
  }
]
```

These checks round-trip persisted conversational context and recreate the HTTP client at turn 8; they do not establish process-restart equivalence.

| Conversation | Turn | Correct | Reason |
| --- | --- | --- | --- |
| A_cooperative | 2 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_cooperative | 3 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_cooperative | 4 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_cooperative | 5 | True | The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution. |
| A_cooperative | 6 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_cooperative | 8 | True | The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution. |
| A_cooperative | 10 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_cooperative | 11 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_cooperative | 12 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_cooperative | 13 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_cooperative | 14 | True | The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution. |
| A_curious | 2 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_curious | 3 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_curious | 4 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_curious | 5 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_curious | 6 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_curious | 7 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_curious | 8 | True | The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution. |
| A_curious | 9 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_curious | 10 | True | The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution. |
| A_curious | 12 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_curious | 14 | True | The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution. |
| A_casual | 2 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 3 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 4 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 5 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 6 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 7 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 8 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 9 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 10 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 11 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 12 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 13 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 14 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_casual | 15 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 2 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 3 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 4 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 5 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 6 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 7 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 8 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 9 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 10 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 11 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 12 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| A_playful | 13 | True | The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution. |
| A_playful | 14 | True | The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution. |
| B_skeptical | 2 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| B_skeptical | 3 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| B_skeptical | 4 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| B_skeptical | 5 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| B_skeptical | 6 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| B_skeptical | 7 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| B_skeptical | 8 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
| B_skeptical | 9 | False | The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange. |
