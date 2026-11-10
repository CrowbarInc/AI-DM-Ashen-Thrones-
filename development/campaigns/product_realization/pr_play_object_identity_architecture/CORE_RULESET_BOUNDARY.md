# Core / ruleset / campaign / AI responsibility matrix

Milestone: `pr_play_object_identity_architecture`. All new adapter/instance APIs here are proposed, not present runtime interfaces.

| Major operation | Core owner | Ruleset adapter | Campaign/world authority | AI role | Persistence owner |
|---|---|---|---|---|---|
| Definition import | Validate namespaced definition reference; separate instances | Parse/version item stats and capability descriptors | Choose enabled content packages | Suggest mapping, never grant items | Immutable content host; no campaign mutation on import |
| Mint identity / reconcile import | Instance owner generates opaque ID, rejects collision | Supply external definition key only | Authorize existing/created object and campaign scope | Resolve ambiguous reference suggestions | Existing character/world host via storage |
| Resolve target / part | Deterministic binder checks unique identity and disclosure | May interpret system-defined component identifiers | Establish presence and supported parts | Parse target, source, surface; clarify ambiguity | No write unless deliberate promotion |
| Existence/access/ownership | Validate placement, access evidence, consent and bounds | Contested action/proficiency restrictions | Locks, distance, custody, rights and contradictions | Propose intended interaction; no inferred possession | Existing state roots |
| Containment/transfer | Acyclic one-placement relationship and conserved identity | Capacity/encumbrance/special transfer rules | Container access and recipient identity/consent | Interpret from/to | Atomic source/destination host saves |
| Equip/unequip | Generic relation to actor (wear/wield/carry), placement invariant | Slot identifiers, hand limits, armor/proficiency effects | Establish actor/item/body context | Interpret wearing versus holding | Object host plus actor extension under coordinated commit |
| Capabilities/material compatibility | Typed evidence and unknown/false/true evaluation | Special material/item exceptions | Actual cloth, mud, wetness, access, suitability | Suggest physical operation only | Provenance on promoted facts/receipts |
| Mundane affordance | Deterministic consequence/risk budget gate | Veto combat/resource/cost effects | Approve campaign policy and established scene basis | Propose bounded detail | Transient evidence or established fact host if persistent |
| Mechanical adjudication | Verify adapter identity/version/result binding | Checks, difficulty, abilities, action economy, proficiency, damage, consumption, crafting, conditions, special abilities | Authored constraints and available resources | Explain request/result, never choose a successful roll | Mechanical owner stages result/costs with object delta |
| Modification proposal | Instance service validates target/revision/operation/preconditions | Allow/check/deny/unsupported with authorized costs | Source inscription knowledge and physical facts | Extract exact requested text/grounded excerpt | No write for proposal |
| Apply/rollback/idempotency | Instance service validates and stages; API coordinates | Never writes core record directly | No new fact from prose | No write authority | Storage runtime scope and existing roots |
| Inspection/recall | Current-state projection and stable-reference lookup | Render permitted mechanical interpretation | Visibility/knowledge policy for markings and objects | Phrase the authorized current result | No truth write; journal/conversation derived |
| Narration/publication | Existing projection, validation, seal and immutable publication | Consume applied consequences only | Hidden data excluded before projection | Narrate only authorized completion/uncertainty | Existing log/publication seams, not object authority |
| Save/reload/ruleset switch | Validate host/binding/revision/schema; preserve opaque extensions | Migrate/disable unsupported mechanics explicitly | Campaign chooses active ruleset | No reinterpreting state from memory | storage/snapshot infrastructure |

Core object fields must contain no AC/BAB/saving throws/spell levels/PF equipment slots. Extension example is `extensions["pf1e@package-version"]`, validated only by its adapter. Core treats unknown extensions as inert opaque data; they cannot become object policy through arbitrary keys.

An adapter decision is bound to operation, involved object revisions, relevant context digest, ruleset/package/version and adjudication result. Values: not_applicable, allowed, pending_check, denied, unsupported. A small no-mechanics adapter explicitly returns not_applicable for an ordinary noncontested marking. “No adapter installed” cannot mean permission for a mechanically consequential action. Checks are performed once by existing engine mechanics; the AI cannot choose DCs, roll results or bypasses.

Current doctrine defines five state domains and no pluggable loader. The roadmap adds one narrow seam for object mechanics, not a global ruleset migration. Raw character schema and other existing gameplay may remain PF-inspired; this design claims portability of the new identity/mutation boundary only.
