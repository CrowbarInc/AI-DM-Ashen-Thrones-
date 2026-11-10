# Publication trace ownership

PlayerHTTPRoute is the authoritative completion boundary. It projects and constructs the actual JSON response, then records one completed publication. The same boundary handles direct engine responses, accepted expression, grounded fallback, request validation and sanitized errors. Ordered-turn duplicate replays explicitly skip a new publication event.

Each record contains a unique turn identifier, owner/category/source handler, provider involvement and attempt references, hashes for actually published accepted expressions, hash of the final text, exact final player-facing response, status and validation outcome. Rejected/unpublished candidate text and hidden resolver payloads are excluded. No credentials are recorded. Contract-aware categories distinguish clarification, unsupported action and failure when the resolver supplies the contract.

The PR66 legacy publication object remains a server-body invariant observation, with client_received unknown; it is not a second completed-publication event. Direct-engine verification consumes its request-local binding once. It does not revive the optional narrator.

Eight browser submissions produced eight records. The earliest place-answer record missed alternate-owner provider provenance; original evidence is preserved. That defect was repaired using actual completed provider deltas plus a matching publication context. The final-source post-reload record correctly references its live provider attempt and published dialogue. No retrospective trace rewrite was made.

Final-source development verifies actual 422 error recording, duplicate HTTP replay, provider provenance, accepted-but-unpublished exclusion and category contracts. Trace-write OSError is logged without undoing an already committed gameplay turn.
