# Negative Controls

Milestone: `pr_play_object_marking_disclosure_policy`. Date: 2026-11-09.

Authored controls cover missing/malformed/serialized grants, wrong observer/campaign/character/instance/scope/category, stale revision and content/classification changes without revision, blank evidence references, conflicting complete permissions and unsupported/all/history requests. Durable duplicate/malformed/partial/cross-campaign identities fail without migration. Mixed visible/concealed/restricted/legacy records require exact permission; hidden and restricted records cannot be inferred from an empty visual subset. Identical object A/B and reorder controls use durable IDs. Invalid active IDs/revisions/types/versions/content/size/capacity refuse. Malformed or missing classification never guesses. Repeated requests do not widen authority.

information_leakage.json verifies both explicit allowlisted field shape and serialized sentinel values, including actual private request IDs, request digests and mutation UUIDs. noninterference.json verifies equal ordinary output for different concealed/restricted/legacy counts/content and unrelated private history/extensions. Removed metadata/history is ignored even when supplied. Snapshot/read-only/extension controls cover future-state exclusion and purity. These are authored variations, not an independently held-out generalization claim.
