# Ranked Root Causes

1. Execution eligibility is used as the gate for conversational understanding.
Severity: critical. Confidence: high. Type: architectural limitation / contract mismatch. Evidence: `game/live_chat_interpretation.py:309`, `game/live_chat_interpretation.py:324`, `game/player_interpretation_bridge.py:14-25`. Remedy: conversational orchestration envelope before execution bridge.

2. Single-component bridge rejects coherent multi-intent utterances.
Severity: high. Confidence: high. Type: orchestration defect. Evidence: current `data/session_log.jsonl` movement turn; `game/live_chat_interpretation.py:324`. Remedy: primary-intent plus incidental/dependent components and slot-specific clarification.

3. Context exists but is not uniformly available at the rejection boundary.
Severity: high. Confidence: high. Type: contract mismatch. Evidence: `data/session.json` active target; `game/prompt_context.py:2549-2577`; bridge rejection still possible. Remedy: orchestrator uses active interlocutor/topic before bridge failure.

4. Campaign lifecycle is split between UI button, exact chat cues, and session freshness.
Severity: medium-high. Confidence: medium-high. Type: local/orchestration defect. Evidence: `static/app.js:649`, `game/api.py:4157`, `game/api.py:5592`. Remedy: formal start/resume router and automatic/fresh-start opening behavior.

5. Narration continuity is downstream of resolver success.
Severity: medium. Confidence: medium. Type: orchestration defect. Evidence: memory and response-delta contracts are prompt-side; rejected turns bypass them. Remedy: allow answer/acknowledge responses without requiring resolver mutation.

6. Authority protections are correct but over-applied to harmless conversation.
Severity: medium. Confidence: high. Type: architectural limitation. Evidence: bridge visible-target and operation checks; final-emission authority contracts. Remedy: keep authority gates for mutation; introduce non-mutating conversational outcomes.
