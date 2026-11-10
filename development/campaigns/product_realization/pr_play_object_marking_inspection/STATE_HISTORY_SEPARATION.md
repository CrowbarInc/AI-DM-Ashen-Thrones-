# State History Separation

Milestone: `pr_play_object_marking_inspection`. Date: 2026-11-09.

Current state remains solely inventory[index].markings. Successful removal physically removes one entry from that active collection; empty list is valid. The existing character.object_marking_receipts version-1 ledger remains the only durable idempotency/history host. Add receipts remain exactly intact. A removal receipt extends the existing result with operation=remove_marking, its canonical request and removed_marking. The latter is one bounded marking record, not an object snapshot or a second object-state ledger.

This retained marking evidence is required for compatibility with predecessor bidirectional validation: old add receipts contain no content/authorization, so deleting the only semantic evidence would make their digest unverifiable. Retaining one removed record enables the existing digest/provenance/integrity checks without rewriting old receipts or retaining tombstones in the bounded active collection. Validator checks every active/historical add against its unchanged receipt, every removal against its request/target/revisions and removed record, unique IDs/request keys/revision events, and complete receipt coverage. Resurrection, dropped removal receipts, tampered old add receipts and malformed history fail closed. Inspection derives its list exclusively from active state, while history validation may refuse corruption.

S0 restores zero active marks, revision 0, zero receipts; S1 restores two, revision 2, two add receipts; S2 restores one, revision 3, two add plus one removal receipts. No latest external ledger is consulted. Captured timeline semantics and pre-existing multi-file restore limitations remain unchanged.
