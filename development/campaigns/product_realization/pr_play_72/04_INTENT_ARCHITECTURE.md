# PR-PLAY-72 — 04 INTENT ARCHITECTURE

```text
PLAYER TEXT (static/app.js → POST /api/chat)
  → game.api._chat_turn / communication mode
  → conversational_orchestration.deterministic_conversational_decision
  → player_initiative.decide (explicit gate + identity binding; read-only)
  → existing ConversationalDecision / operation record
  → player_interpretation_bridge.normalized_action_from_interpretation
  → contextual target / scene / prerequisite validation
  → existing exploration / social resolver, authored_consequences.resolve
  → existing world updates + runtime_commit_scope / storage persistence
  → mandatory disclosure / deterministic fallback
  → optional existing validated AI presentation
  → player_http_projection allowlist → frontend
```
Information, clarification and refusals use the existing nonmutating conversation response. Their transcript is appended; PR72 deliberately avoids updating session conversation context or calling expression generation. All four gameplay documents remain equal before/after those requests. Publication selection in the existing lifecycle happens after authority saves and before log append; the endpoint commit scope rolls back failures. No second store, resolver, knowledge database, provider dependency or persistent clarification schema was added.

