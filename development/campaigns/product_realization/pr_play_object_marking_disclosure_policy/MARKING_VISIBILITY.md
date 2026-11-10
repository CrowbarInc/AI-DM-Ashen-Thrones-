# Marking Visibility

Milestone: `pr_play_object_marking_disclosure_policy`. Date: 2026-11-09.

Small optional object-row metadata (not inside exact legacy marking records):

```json
{"marking_visibility":{"version":1,"markings":{"<existing-mark-UUID>":{"classification":"visible"}}}}
```

Classifications: visible; concealed; restricted with exactly one additional scope string. Ordinary established visual authority includes visible only. Explicit concealed=true permits concealed classifications. Restricted marks require a matching restricted_scopes tuple; wildcard is explicit trusted all-scopes authority. Complete observation requires both concealed authority and wildcard restricted authority. Publicly visible does not mean public access: observer/target/scope/access authorization is still mandatory.

Missing/unknown/ambiguous metadata never defaults to visible or concealed. Existing source_disclosed/write authorization does not prove later visibility. Legacy records stay byte-identical and undisclosed until upstream supplies evidence. Classification is object state consumed by the projection, not inferred from inventory, names, mechanics or text. Unmatched stale metadata for removed marks is ignored; only active UUIDs are looked up. No receipt or latest-timeline lookup. IDs, revisions, content, receipts, unknown fields and extensions are untouched. Metadata survives ordinary storage/snapshots as existing opaque row data. No marking-application API, schema migration, new writer or arbitrary ACL evaluator is introduced. Fixture authoring uses existing trusted storage solely to establish controlled state; shipping classification-authoring lifecycle is deferred.
