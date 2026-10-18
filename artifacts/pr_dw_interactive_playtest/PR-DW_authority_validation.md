PR-DW authority validation

Authority findings:
- The forbidden author-mode chat request was blocked with HTTP 403.
- The exact OOC correction shortcut produced metadata `authoritative_mutation: false` and `resolver_invoked: false`.
- The generic OOC probe incorrectly entered ordinary contract/resolution handling and advanced runtime counters.

Duplicate execution:
- No duplicate committed action observed in this PR-DW run.

Hidden information:
- No hidden-information disclosure observed in the captured UI transcript.

Authority concern:
- An OOC instruction not to change state still changed session turn/time counters. This is an authority failure for OOC classification, but no duplicate action was observed.

