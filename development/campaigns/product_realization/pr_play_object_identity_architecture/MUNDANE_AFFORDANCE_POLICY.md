# Proposed mundane-affordance policy

Milestone: `pr_play_object_identity_architecture`. Not implemented in this cycle; existing improvisation gates are not silently widened.

## Authority categories

| Category | Evidence | Engine decision |
|---|---|---|
| Established | Explicit campaign/character/scene state, valid version and current access | Use within stated scope; material suitability is a separate check |
| Reasonable affordance | Direct low-consequence consequence of established physical facts | Deterministic policy may approve bounded use with basis, amount/use and no-resource-grant receipt |
| Uncertain | Plausible but lacks sufficient basis/access/suitability | Clarify only the missing fact or offer an already established alternative; no silent success |
| Contradictory/prohibited | Contradicts explicit absence, locks, visibility, inventory or consequential-resource limits | Reject the assumption; do not name hidden reasons in public output |
| Ruleset-dependent | Combat, mechanical bonus, constrained cost/ability, special material/item | Await adapter adjudication; mundane policy cannot replace it |

Evaluate context and intended consequence, not a whitelist of nouns. A free splinter used as table texture differs from the same splinter used to bypass a lock. Low market value alone is insufficient. The policy forbids granting hidden information, valuable resources, weapons, special tools, ammunition/charges, ruleset consumables, quest items, mechanical bonuses, NPC consent or new routes. Any requested persistent change still needs a validated mutation; an affordance receipt only proves one prerequisite.

## Bounded decision procedure

Establish factual source and actor access; reject contradictions; classify intended consequences, scarcity and system relevance. Allow a trace amount of mundane material if directly supported, safe, unowned/uncontested for that use, nonvaluable and not mechanically scarce. Record `{basis_ref, basis_version, medium, permitted_use, bounded_amount, expiry: turn, no_inventory_grant: true}`. Revalidate at commit. No arbitrary amount or stockpile: repeated attempts to extract, sell or exploit cumulative supply leave the policy and require resource authority.

If an incidental new detail rather than an entailment is proposed, the campaign must explicitly enable that detail class and its consequence budget. The core validates it deterministically against established context and records provenance through the existing controlled-fact owner if retained. The AI only proposes. Disabled policy or uncertain evidence produces clarification. Do not automatically activate experimental world improvisation to realize this design.

## Required cases

| Case | Decision and constraints |
|---|---|
| A: explicitly wet muddy road | A small finger-smear can be used without creating an inventory item if the wet patch is accessible and no ownership/hazard contradiction exists. “Wet mud exists somewhere” does not prove reachability. Compatibility with the target remains separate |
| B: dry stone corridor, mud requested | Mud is not established. Ask for an established supply or suggest a known medium. Do not create mud, a leak or an outside route; explicit dryness is contrary evidence |
| C: tavern table splinter | Already loose, accessible, ordinary waste can be a low-consequence affordance. A table alone does not imply a loose splinter. A campaign may permit incidental damaged-wood detail with bounded provenance; otherwise unknown. Breaking owned furniture is persistent damage and requires permission/adjudication. A lockpick, weapon, saleable supply or combat advantage is excluded |
| D: guarded armory unattended weapon | Consequential resource and custody/security issue. No mundane improvisation grant, regardless of plausibility. Requires authored object, access, ownership and acquisition/contested mechanics |
| E: sleeve/clothing | Explicit character description establishing a long-sleeved garment may justify deliberate lazy promotion into a clothing instance and supported sleeve part. This creates no armor/tool bonus. A PF ancestry/class, typical social expectation, bare request “my sleeve,” or Spellbook possession is insufficient. Contradictory bare arms/short sleeves veto. Original T06 still needs this evidence |
| F: mud/charcoal/ink writing | Mud: established wet trace + access + surface compatibility. Charcoal: established usable residue/piece, no invented fire. Ink: actual equipment/resource proof, and adapter-defined consumption if tracked. Dirt does not automatically equal writable mud. None implies legibility, duration or exact source knowledge |

For original T06, “muddy gate line” is evidence to evaluate, not an automatic full prerequisite grant. Establish wet usable accessible medium, clothing identity and writable part explicitly before completion. Do not retcon predecessor refusal into a successful action.

## State granularity decisions

| Interaction | Result category | Why |
|---|---|---|
| Touch accessible door | Transient action receipt, no durable object mutation | Contact alone has no later physical consequence; T04 contract |
| Open a door | Persistent instance state / world access update if applicable | Later openness and passage must be truthful. Specialized travel/access owner coordinates any route effect; transient narration cannot unlock a route |
| Write on sleeve | Persistent marking on clothing part | Text must be inspectable later; no automatic knowledge discovery or skill benefit |
| Scratch symbol into wall | Persistent world-hosted object change; possible mechanical damage | Durability/ownership/tool requirements differ from harmless smear. Unsupported until corresponding operation ships |
| Pick up stone | Persistent placement/custody change and lazy promotion | Scarce individual must follow actor; acquisition authority required even if inexpensive |
| Break bottle | Persistent destroyed/condition state plus contents/world effects; adapter if contested | More than narration; lifecycle and spill consequences deferred |
| Clean mud from clothing | Remove specific compatible markings and increment revision | Current inscription must disappear; harmless pose description alone cannot erase it |
| Move chair | Transient receipt for an inconsequential tiny adjustment; persistent placement when later accessibility/location changes | Intent and consequence determine detail level. Persistent claim requires object and placement validation |
| Read notice | Transient reading receipt plus existing persistent knowledge/discovery if new | Information owner persists disclosure; notice itself is unchanged |

No persistent state for idle background description; transient receipt for completed inconsequential acts; instance delta for later observable object changes; world delta for broader access/scene facts; adapter effect for mechanical consequences. Categories can coexist only as an explicitly coordinated outcome. The engine must not silently downgrade an intended persistent or consequential action into a harmless touch.
