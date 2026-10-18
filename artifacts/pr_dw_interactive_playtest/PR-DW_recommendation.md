PR-DW recommendation

Decision:
- D - LIVE INTERPRETATION BLOCKED.

Recommended next step:
- Implement a general communication-mode gate before ordinary gameplay parsing.
- Any explicit `OOC:` message should route to a non-mutating OOC handler unless it contains a deliberate explicit in-character override.
- Ambiguous state-changing input should ask for clarification rather than falling through to parser execution.
- Add HTTP/browser regression coverage proving OOC messages do not advance turn/time and do not call providers.

