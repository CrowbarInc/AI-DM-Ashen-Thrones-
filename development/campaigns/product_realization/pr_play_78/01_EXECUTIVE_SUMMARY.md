# PR-PLAY-78 — Executive summary

**Verdict: B — PARTIAL / INTEGRATION IMPROVED.**

A player can explore, inspect, travel, greet, and ask ordinary questions in natural language, and the host can publish live narration and live NPC speech without letting the provider commit state. The same session can cross those domains, save, reload, and resume. That is a real step past PR-PLAY-77.

It is not yet a coherent adventure. Ordinary speech that paraphrases a visible authored choice is treated as travel and refused. After the milestone, an adaptive player who had used the grounded ideas on screen repeated the same look-around until the session ended. The report branch can be finished by pressing the suggested-action button. It was not finished by saying the button's sentence.

Live provider content is real and was published:

- Post-fix gate session: 3 accepted NPC lines and 4 accepted narration restyles, all published. One narration proposal was rejected. "Who are you?" clarified in 35.6 ms and did not call the provider.
- Extended session, before scene scoping: 4 more accepted NPC lines were published, including one uncommitted remark that the mud track "gets tricky." That guard was addressed at the milestone. Scene scoping now refuses that address. Those four lines still count as published provider speech. They do not count as a correct knowledge boundary.

Provider total: 14 completed requests, 3,000 tokens, 0 retries, model `gpt-4.1-mini-2025-04-14`. The provider did not commit state. Browser play used a host with provider calls disabled, so browser dialogue is deterministic.

Protected repository files: 150/150 unchanged. Isolated lifecycle: 39/39. Focused regression: 1065 passed / 20 failed, 0 new versus PR-PLAY-77. Boundary: 101/6, 0 new. Broader: 0/9, 0 new. The failure identities match the previous cycle. Hidden-fact phrases (noble house, Ash Cowl, coordinated signal, spotter, silver list, sentinel) were absent from the browser session and were not published as discoveries. The northwest mud-track sentence is the authored notice-board clue, not a hidden leak.

No commit and no push.
