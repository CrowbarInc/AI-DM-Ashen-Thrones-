# Root causes and changed assertions

1. PR61 recall: exploration._repeat_publication emitted only a no-new-information sentence. It never retrieved already explicit source knowledge. Repaired in the existing resolver, using current source binding, known clue identity/text, explicit disclosure, scene provenance and validity checks. No global memory or provider rediscovery was added.
2. PR66 no_new/continuity/fast_path: API finalization copied engine_publication then returned before legacy publication verification. Request-local direct-engine verification now fills the PR66 invariant record without generation. Actual completed publications are recorded separately at PlayerHTTPRoute, after serialization/projection.
3. PR47 matrix[5]: narration_skip stamped the caller's repeat-resolution metadata. The read-only repeat selector now returns its sentence without modifying resolution. The original row == original assertion is unchanged and passes.
4. Browser approach: bounded_improvisation expressed an adjudication, then left its contract eligible for another bounded expression. It now stamps the settled final contract after its one expression opportunity, including rejection/fallback. Two targeted tests protect this.

Changed assertions (none deleted):

- PR61: [True,True,True,True] AI-published flags becomes [True,True,False,True]. Replacement checks engine owner, PASS invariant and recalled ROUTE in actual text. The repeat provider candidate was accepted but was not the published expression, so counting it as visible AI would be incorrect. Resume wording now names the notice board and additionally requires ROUTE.
- PR62: exact no-fact repeat sentence becomes target prefix + known ROUTE + nothing-new status. The exclusion assertion still prohibits ROUTE in unrelated barrel/gate responses; only the legitimate source repeat may contain it.
- PR69 structured/chat: exact no-recall sentence becomes target prefix + no-new status + every originally disclosed clue. Existing unchanged journal equality, no-canary checks, four resolver calls and generation bounds remain. Both new-oracle identities pass in reclassified_and_ordering.xml and the final historical lane.

PR62 and PR69 were passing at entry, reproducing the three later 79C repairs. The new recall contract invalidated their literal no-recall assertions. These are explicit contract/oracle changes, not tests weakened to hide hidden-fact or state failures.
