# Summary

Milestone: `pr_play_authored_topic_retrieval`. Verdict: **A/PASS**.

The existing social/dialogue owners now retain authored quantitative and comparative answers through relevance/sufficiency selection and ordinary HTTP publication. Production changes: `game/social.py` and `game/dialogue_authority.py` (21 additions, 3 removals). No new information system or publication bypass.

- Original price, headcount and route comparison: 0/3 relevant before -> 3/3 after. Original forbidden-topic control remains safe.
- Representative paraphrases: 3/3. Alternate NPC, clear subject among multiple sources, recall, ambiguity and mixed/forbidden policy controls pass.
- Dedicated authored HTTP: 27 requests, 25 cases, 275 assertions, zero failures. Additional inventory HTTP: 4 requests/44 assertions, zero failures.
- Matched replay: 101 requests per phase, identical publications and time deltas. Forty probes unchanged: SUCCESS 11/40, minimum quality 20/40, mean actionability 1.575/3, misinterpreted 4, irrelevant scenery 0.
- Combined regression before/after: 405 passed /20 inherited failures, identical identities. Focused preservation: 611 passed. Inventory/admission: 32 passed. Topic suite: 269 passed/37 failed with captured initial owners -> 280 passed/26 inherited failures; zero new failure identities. All 22 new tests pass.
- Provider calls: zero in controlled HTTP/evaluation/timing. Pytest live-model constructor guard prevents live calls; mocked provider tests retain their contracts.
- No extra movement, inventory/combat edits, physical scene mutation or ticks. Successful dialogue records authorized knowledge and the existing authored-exit lead, plus existing social runtime/transcript changes. Same request retry returns the same response without state change. Fresh-process marking reload passes.

Root cause: price quantity support rejected number + currency unit + coins; count/comparison were misclassified as surveillance because Guard appeared in the NPC vocative. Dialogue now reuses the existing social quantity/comparison axes ahead of broad surveillance. A comparison must have comparative support, so a route listing is insufficient.

Performance uses five samples per family and descriptive medians/maxima under background load. No new state reads, full-world retrieval scans, provider calls or retry tiers. Lexical coverage remains finite and live naturalness is untested. Review retained inherited failures and harness correction records. Stop after verified archive handoff; no next milestone started.
