# 04 — Response-Path Audit

```mermaid
flowchart TD
 A[Provider candidate or host resolver result] --> B[Authority resolution and existing decision]
 B --> C[Host speech selection or full hard validation]
 C --> D[Accepted response or fixed GM safety fallback]
 D --> E[Pin existing accepted_response and SHA256 identity]
 E --> F[Legacy final emission stages: sealed text protected]
 F --> G[Restore exact pinned text and attribution]
 G --> H[Commit authorized history and NPC speech]
 H --> I[Save session and log]
 I --> J[API payload verifies and removes private seal]
 J --> K[JSON delivery: same exact text]
 L[Legacy retry without adoption] --> C
```

Real ordering differs from the ideal: host adoption occurs before the legacy final emission gate; post-gate reconciliation and preservation historically ran afterward. Both resolved chat and structured action share finalization. Conversational decisions seal their host response separately using the same record. Missing-adoption social retries now enter complete authorization before legacy stages; other legacy finalizations enter the same validator before history. Pipeline-origin state mutation is resolver owned and precedes narration; final delivery adds no mutation authority. See source diffs and inventory.
