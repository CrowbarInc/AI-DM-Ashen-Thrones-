# 22 — Fresh-Provider Conversations

Path: production `POST /api/chat?ui_mode=player` via `TestClient`. Gate on. Expression and live interpretation enabled. Isolated data directory per conversation.

Turns: 119. Conversations: 8 (adaptive_A, adaptive_B, adaptive_C, adaptive_wardens, labeled_adversarial, labeled_harbor_direct, labeled_harbor_gap, labeled_quill).
Sources: adaptive 60, labeled 59, frozen-holdout 0.

Status: `STOP`.

A first live attempt stopped at 32 turns because a repeated non-question scene blurb did not append a second delivered-history row. A second attempt stopped when a refusal echoed the player's words "ash cowl" without stating the secret value. The completed file is `live_turns.jsonl`. The stopped transcripts are kept as `live_turns_stopped.jsonl` and `live_turns_echo_stop.jsonl`. The adaptive player instruction was narrowed to one addressee after the first sample. Labeled strings and frozen holdouts were not edited.

Representative labeled lines:

- `labeled_harbor_gap` turn 1: player `Keeper Nara, who manages the ferry schedules?`
  delivered: Keeper Nara says, "I do not know who manages the ferry schedules."
  plan: act=information_question addressee=keeper_nara relationship=manages(ferry_schedules) sufficiency=unknown reason=no_relevant_source
- `labeled_harbor_gap` turn 2: player `Keeper Nara, what is the harbor bell called?`
  delivered: Keeper Nara mutters, "Word is, the bell beside the ferry is called the harbor bell."
  plan: act=information_question addressee=keeper_nara relationship=called(harbor_bell) sufficiency=direct reason=authorized_direct
- `labeled_harbor_gap` turn 3: player `No, I meant who manages the ferry schedules.`
  delivered: Keeper Nara says, "I do not know who manages the ferry schedules."
  plan: act=correction addressee=keeper_nara relationship=manages(ferry_schedules) sufficiency=unknown reason=no_relevant_source
- `labeled_harbor_gap` turn 4: player `Why?`
  delivered: Keeper Nara says, "I simply couldn't tell you."
  plan: act=follow_up addressee=keeper_nara relationship=cause_of(ferry_schedule) sufficiency=unknown reason=no_relevant_source
