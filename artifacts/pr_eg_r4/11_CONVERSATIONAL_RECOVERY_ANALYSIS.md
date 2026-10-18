# 11 — Conversational Recovery Analysis

Root-agent audited recovery episodes are in `agent_audit.json`. Each begins after a poor response and requires a reasonable attempt to resolve the same intent. A topic change or acceptance of an unrelated answer is not recovery. A successful repair must occur on the first recovery request or within the next two player turns; overlapping attempts in the same unresolved episode are not counted as independent successes. One episode at conversation end is right-censored and excluded from the gate denominator.

Success: 1/11 (9.1%).

```json
[
  {
    "conversation": "A_cooperative",
    "initial_failure_turn": 1,
    "first_recovery_attempt_turn": 2,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "Sequencing both NPCs, then selecting Mara, still leads to addressee questions through turn 4. Turn 5 finally reaches Mara after the two-additional-turn window."
  },
  {
    "conversation": "A_cooperative",
    "initial_failure_turn": 5,
    "first_recovery_attempt_turn": 6,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "A request for any available information receives the same nonanswer, then an unrelated watch fact, then repetition rather than elaboration."
  },
  {
    "conversation": "A_cooperative",
    "initial_failure_turn": 8,
    "first_recovery_attempt_turn": 9,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "Reformulating night-watch reasons as incidents/dangers leads to repeated subject clarification through turns 10–12."
  },
  {
    "conversation": "A_curious",
    "initial_failure_turn": 1,
    "first_recovery_attempt_turn": 2,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "Repeated explicit sequencing and single-name clarification do not resolve the addressee within two additional turns; only turn 8 reaches Mara."
  },
  {
    "conversation": "A_curious",
    "initial_failure_turn": 9,
    "first_recovery_attempt_turn": 10,
    "success_within_two": true,
    "additional_turns_after_first_attempt": 0,
    "eligible": true,
    "assessment": "Repeating the same genuine unknown question directly to Tavern Runner changes the delivered speaker correctly and returns appropriate uncertainty."
  },
  {
    "conversation": "A_curious",
    "initial_failure_turn": 13,
    "first_recovery_attempt_turn": 14,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": false,
    "assessment": "The road's name does not answer destinations/dangers; the retry repeats the name, and turn 15 switches to a watch fact. No recovery observed, but the full two-additional-turn window is unavailable."
  },
  {
    "conversation": "A_casual",
    "initial_failure_turn": 1,
    "first_recovery_attempt_turn": 2,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "Accepting the first proposed question still yields addressee clarification and an unsupported-action refusal through turn 4."
  },
  {
    "conversation": "A_casual",
    "initial_failure_turn": 5,
    "first_recovery_attempt_turn": 6,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "Explicitly addressing Tavern Runner repeats a stale get-attention compound-action refusal at turn 7 and another addressee question at turn 8."
  },
  {
    "conversation": "A_casual",
    "initial_failure_turn": 8,
    "first_recovery_attempt_turn": 9,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "Direct Mara clarification then meta-address and roster clarification produce a spurious movement route refusal and repeated addressee questions. No repair through turn 15."
  },
  {
    "conversation": "A_playful",
    "initial_failure_turn": 1,
    "first_recovery_attempt_turn": 2,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "Repeated clarified lantern/rumor inquiries remain in a proposed/conditional-action loop. Even a single-NPC lantern question later gets Which subject do you mean."
  },
  {
    "conversation": "A_playful",
    "initial_failure_turn": 11,
    "first_recovery_attempt_turn": 12,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "The player directly addresses Tavern Runner about the preceding anecdote invitation; blanket nonanswers at turns 12–14 never correct the misattribution or supply a harmless story."
  },
  {
    "conversation": "B_skeptical",
    "initial_failure_turn": 1,
    "first_recovery_attempt_turn": 2,
    "success_within_two": false,
    "additional_turns_after_first_attempt": null,
    "eligible": true,
    "assessment": "Clear corrections of the ferry scheduling question repeatedly receive the bell name, including after switching clerks. The last repair request triggers post-rejection delivery at turn 9."
  }
]
```
