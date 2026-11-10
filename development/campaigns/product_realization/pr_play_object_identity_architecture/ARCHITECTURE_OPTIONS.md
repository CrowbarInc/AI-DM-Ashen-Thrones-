# Architecture options

Milestone: `pr_play_object_identity_architecture`. All alternatives address the observed character/scene split; ratings are qualitative architectural estimates, not benchmark results.

| Criterion | A: extend inventory records only | B: lightweight common instance layer, selected | C: common mutation/event envelope only |
|---|---|---|---|
| Ruleset independence | Good if fields generic; risk importing PF sheet assumptions | Strong opaque identity/optional definition/extensions | Good event shape, inconsistent target identity remains |
| Existing compatibility | High for carried singleton, poor fixtures/NPCs | Preserve hosts/legacy fields through bindings | High per-owner adoption |
| Migration complexity | Low initially, high once walls/doors become pseudo-inventory | Moderate bounded promotion; no wholesale content migration | Low initially, indefinite reconciliation burden |
| State authority | Carried changes clear; fixtures need another owner | One semantic instance owner, specialist adjudication | Several owners enforce similar invariants separately |
| Persistence | Character JSON works locally; cannot transfer to scene coherently alone | Reuse existing roots/snapshots and coordinated host movement | Each host persists; common event may not resolve competing copies |
| Performance | Cheap local scan | Lazy IDs, derived lookup, bounded state; no full simulation | Cheap events, potentially expensive cross-owner reconstruction |
| Token efficiency | Compact inventory delta | Compact stable refs and current-state slice | Compact events only if never reconstruct history in prompt |
| Extensibility | Poor noncarried objects/parts | Strong portable instance/part identity | Good operation additions but identity adapter drift |
| Testing complexity | Simple first case, divergent fixtures later | Identity/host invariants plus contract consumers | Need cross-product of owner-specific identity/transfer behaviors |
| Duplicate ownership risk | Shadow inventory for doors or scene ledger for sleeves | Low if single-host invariant and delegation enforced | Highest: common log does not resolve authoritative host |
| Mundane improvisation | Awkward environmental material-as-item pressure | Affordance evidence separate from instance promotion | Good prerequisite event, unclear promotion identity |
| Future ruleset imports | Item stats can leak into universal rows | Immutable definitions distinct from core instances | Imports can retain incompatible equipment identity models |

## Decision and rejection rationale

Choose B with a common validated envelope as part of B. A alone is a viable bounded carried-item repair but cannot provide the requested generic architecture without treating fixtures as inventory or duplicating authority. C alone preserves owner autonomy but does not resolve duplicate IDs, identical copies or transfer continuity; events cannot substitute for current object truth. A universal event-sourced entity database is a fourth deferred alternative: excessive migration, crash/replay complexity and reconstruction for a single marking. No evidence requires replacing the file-backed engine with it now.

The new shared layer is deliberately a narrow semantic service, not a second physical orchestrator or central copy of every object. Existing inventory and future world-hosted records remain canonical. The design consolidates identity validation and instance deltas while retaining distinct travel/social/knowledge/combat responsibilities. Experimental scene writes are delegated only for bindings deliberately migrated; no wholesale activation.

## Complexity and efficiency estimate

With N materialized objects, R relevant objects, M markings on a target and A historical applied actions: initial host scanning/index rebuild O(N), in-memory stable-reference lookup expected O(1), validation O(R + M + bounded input bytes). Without an index, a small inventory read is O(N); acceptable initially. Object state O(N + active marking bytes), audit/dedupe O(A). Existing JSON saves rewrite a touched host O(host bytes); snapshots remain O(total saved state), not O(changed delta). Locks serialize turns and can increase contention; no throughput claim is made.

Bounded receipt/context includes only target identity/current visible markings and the adapter result. Do not serialize the entire inventory or audit ledger every turn. Limit exact inscription retrieval to requested objects/parts and keep unrequested provenance private. Use lazy capabilities and material facts, no per-object model calls, no full-world physics and no mandatory model retries. Adapter called only when mechanics classification requires it; explicit no-mechanics result is deterministic. Principal performance risk is file rewrite size and whole-turn serialization, not provider token growth. No measured runtime overhead is introduced during this design-only cycle.
