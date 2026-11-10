# Inspection Contract

Milestone: `pr_play_object_marking_inspection`. Date: 2026-11-09.

Internal Python APIs: game.object_marking.inspect_markings(character, request), and game.api.inspect_inventory_object_markings(request) for current authoritative disk state. No HTTP route. Exact v1 request fields: version=1, operation=inspect_markings, campaign_run_id, character_id, instance_id (canonical UUID4), context={caller_id: bounded nonblank string, purpose: authoritative_state}. The API validates current session campaign; service validates character ID and identity provenance, singleton shape and all declared identities/receipt consistency. Context explicitly separates internal reads from player observation; it is not an authentication boundary.

Success: status=inspected, version, campaign_run_id, character_id, instance_id, current revision, detached markings list. Each active record supplies modification_id, exact content, source, authorization/evidence, request lineage and applied revision. Empty active collection returns []. Repeated reads are equivalent and detached. Historical removed records never populate this collection.

Refusals use status=rejected/error. Invalid or missing identity/request/context, absent/ambiguous target, malformed marking/receipt data, duplicate IDs, cross-scope state and unsupported legacy records fail closed. No repair or migration. Missing runtime files return missing_runtime_state without bootstrap. Invalid character JSON returns invalid_runtime_state. No allocation, revision, receipt, metadata/order change, persistence, provider call, equipment inference or conversational reconstruction. Existing lane read lock and persistence guard supply a coherent in-process read. Full internal provenance must not be returned directly to players.
