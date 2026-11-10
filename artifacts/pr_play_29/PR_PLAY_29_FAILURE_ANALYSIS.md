# PR-PLAY-29 failure analysis

No blocking failure observed. Both live ordinary actions execute and complete semantically; authority transition, disclosure, clue provenance, state integrity and confidentiality pass. Experiment stops at two_ordinary_turns_complete.

Quality limitation: Turn 2's first-person dialogue frame embeds the authored third-person source, "Word is, the runner heard...". Evidence localizes the awkward wording to existing authored-topic speech formatting in game.social (NPC speech wrapper), not to a rejected live expression: no optional Turn 2 expression request occurred. This is an existing content/realization limitation, visible in prior offline attributed rumor output. Naturalness/self-reference are PARTIAL, but the specific actionable rumor remains understandable; no repair made.

Harness caveats: inherited FiveTurnGameplay subject_terms generate possibly_irrelevant_response heuristics for both relevant answers. Those are quality hints, not decisive engine failures. Actual transport ledger overrides local subtrace counters claiming zero interpretation calls. Initial offline security test setting prevented synthetic dispatch; corrected test-process environment passed 29/29 without code changes. Owned server is intentionally terminated on cleanup (Windows exit_code=1); process stopped and port released, with no in-request worker crash.

Recommended next investigation, only after external review and separate authorization: inspect eligibility/realization of this authored rumor source to determine why optional expression was not invoked and how first-person NPC speech could preserve its authorized rumor meaning. Do not begin a repair or another live run during PR-PLAY-29.
