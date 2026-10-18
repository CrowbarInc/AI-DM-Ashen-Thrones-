# PR-CS Token Targets

Simple NPC dialogue target 3,000-6,000 input tokens: feasible after deduplicating policy, sending only active speaker/knowledge/scene anchor, and keeping validator-only metadata app-side.

Ordinary exploration target 5,000-10,000 input tokens: feasible for local observe/investigate/interact turns if scene projection becomes target-specific and inactive social/combat policy is omitted.

Complex consequential actions target 10,000-20,000 input tokens: feasible but not guaranteed. Combat, multi-actor social pressure, transitions, or high-risk inference may legitimately require the upper range or exceed it until projection tests mature.

Authority information that must remain: CTIR/resolution contract, response type contract, visibility/authority ceilings, active scene facts, relevant NPC knowledge boundaries, allowed state mutations, and hard validation inputs. The key optimization is not deletion from authoritative state; it is not sending every deterministic artifact verbatim to the provider.
