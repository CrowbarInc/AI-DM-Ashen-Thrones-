# Combined validation

The existing pipeline and precedence are preserved: semantic decision; legacy hard-valid requirement; coverage requirement. Coverage PASS cannot override semantic FAIL, REVIEW_REQUIRED or VALIDATION_ERROR; injected-layer tests exercise all three. Legacy gold-gain rejection remains mandatory. Missing/ambiguous/contradicted coverage cannot PASS. Shape errors and exceptions preserve fallback and quarantine.

These invariants do not imply comprehensive assertion extraction. H41 passes every layer because the persistent opening predicate is not recognized. It is a confirmed corpus-level false acceptance, not a bypass of a layer rejection. Hidden disclosure, inventory and mechanical contradictions retain existing controls. No discovery, grant or mutation is returned by validation.
