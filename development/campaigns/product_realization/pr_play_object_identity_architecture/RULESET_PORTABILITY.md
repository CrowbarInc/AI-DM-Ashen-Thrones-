# Ruleset portability assessment

Milestone: `pr_play_object_identity_architecture`. **Conceptual compatibility only; no additional rulesets imported or executed.** Existing registry RCR-01 says current engine is PF1e-inspired, without a pluggable ruleset loader.

Same recognizable operation across all three: `modify_object(target_instance, add_marking(text, medium, part), context)`. Stable identity, source disclosure, host/revision validation, applied delta, save/reload and later inspection are identical. Adapter may require/check/deny mechanics but never mints object truth or writes core fields directly.

| Aspect | PF1e adapter | Rules-light adapter | Modern/science-fiction adapter | Core invariant |
|---|---|---|---|---|
| Ordinary marking | Usually explicit not_applicable for uncontested mundane task; do not invent DC | Usually automatic or system-specific move trigger | Ordinary physical label may be automatic | Positive surface/material/source evidence required regardless of roll |
| Equipment slots | PF slot restrictions in extension mapping | Optional tags/fictional positioning | Body mounts, hands, ports or rig slots in system extension | Generic wearing/wielding relation has no PF enum |
| Item statistics | Weight/value/armor/weapon stats by package | Minimal tags/fictional traits | Mass, power, ammunition, tech stats | Definition ref and identity independent of stats |
| Skill checks | Existing engine skill-check resolver behind seam, only configured supported checks | Narrative move or no check | Electronics/repair/forgery skill according to installed adapter | Core accepts bound adjudication receipt, not skill names/DC formula |
| Action costs | Adapter defines action economy | Fiction/time/limited move if system tracks it | Action points, time, charge or power cost | Costs staged atomically with object change; no core round assumptions |
| Resource consumption | Tracked ink/special material per supported rules | Ignore mundane supply only when system explicitly permits and world establishes it | Ink cartridge/battery/ammunition as required | Conservation/existence core; quantity/cost policy adapter. No free ammo |
| Conditions | System conditions/durations | Narrative status/aspect | Damage, contamination, electronic lockouts | Namespaced effects with explicit lifecycle; not universal AC/fort fields |
| Special abilities | Magical item/proficiency exceptions | Special fictional permission | Encrypted/authorized firmware, restricted hardware | Adapter cannot bypass campaign access/security or hidden-information policy |

An electronic text file is not automatically a physical marking: use a later typed content mutation with authorization, storage capacity and adapter security checks. Current add_marking cannot rewrite firmware or forge credentials. This boundary demonstrates extensibility without pretending every modern action is already supported.

Definition import supplies immutable package/version/local key and optional capability facts. Campaign instantiation supplies actual existence, placement and core UUID. Reimport or ruleset switch preserves UUID, current markings and provenance; unresolved extension mechanics become inert/unsupported. No automatic conversion of armor slots, skill bonuses or item powers. A ruleset switch cannot refill ammunition, erase markings or recreate possessions. Mechanic-changing extension migration must be an explicit, separately tested adapter operation.

Prohibited universal fields: Armor Class, BAB, spell level, saving throws, PF slots, fixed d20/DC algorithms, prescribed action economy. Core may carry generic refs to mechanical effects without interpreting them. AI parsing/narration uses stable semantic operations and applied results, not system-specific success inference.

Conclusion: **the proposed core object architecture can support imported rulesets without PF1e assumptions**. This does not claim the entire current engine supports alternate systems. A full loader, package validation and combat/character migrations remain outside scope. Adapter identity/capability/result binding is specified; implementation and mechanical coverage remain future work.
