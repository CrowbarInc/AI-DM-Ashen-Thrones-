# PR-PLAY-46 preimplementation finding

Both exact PR-PLAY-45 residual sentences were replayed through
`validate_generated_response` and `run_preserve_if_valid`, without providers.
Both returned `hard_valid=true`, extracted zero claims, and reached the player
unchanged. Empty inventory and zero currency remained unchanged. Raw inputs,
outcomes, state snapshots, decisions and final response objects are in
`baseline_originals.json`. This finding was recorded before implementation.

The architectural defect is open-world prose paired with a closed list of
recognized assertion frames. No extracted claim is treated as no violation,
although it does not prove that no claim exists. A structured provider response
or provider-declared claim list cannot repair this: both remain untrusted prose.
The existing resolver-derived `authorized_mechanical_outcome` already implements
most of option B. It constrains permission, but does not classify arbitrary text.

Bounded decision: retain that envelope, explicitly communicate its delta-only
meaning and descriptive role, and audit two general possession-state structures
against existing outcome permissions. Amount increments can match deltas;
absolute balances and pre-existing possessions cannot be verified from deltas
and must not be inferred. Do not add synonyms across the whole taxonomy.
Preserve free description outside those bounded structures and measure residual
false acceptances explicitly. Option B plus conceptual separation of engine
outcomes and descriptive realization is the preferred migration direction;
visible labels or provider self-attestation cannot enforce semantic separation.
This compatibility improvement is not a production-grade semantic guarantee.
