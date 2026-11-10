# T04 / T06 integration and architecture controls

Milestone: `pr_play_object_identity_architecture`.

| Stage | T04 local approach/contact | T06 persistent inscription |
|---|---|---|
| Intent | Approach board, touch frame | Copy disclosed warning to clothing part with medium |
| Bind | Existing scene-local notice_board address sufficient | Known clue plus stable garment instance/part and material evidence |
| Access | Existing T04 authored interactable visibility/inspectability intersection and vetoes | Positive custody/access, clothing/surface/material suitability and capability |
| Mechanics | Existing unresolved-check veto | Explicit adapter not_applicable or completed mechanical decision |
| Semantics | Transient movement/contact | add_marking with exact disclosed wording |
| Validation | Current local owner validates its bounded class | Instance owner validates proposal and expected revisions/evidence |
| Application | No persistent change; do not mint board merely for touch | Character-held garment updated under turn scope; revision/idempotency saved |
| Receipt | Existing transient_local_action completed record | Existing exploration envelope with additive object_action/applied modifications |
| Publication | Existing host-speech seal/equality check and pointer | Applied receipt projected before seal; preserve T05 disclosure and pre-seal hidden gates |
| Later recall | Contact receipt need not persist as physical state | Inspect active marking on same instance/part; no conversational reconstruction |

Shared stages are intent, unique reference, access/prerequisite validation, optional mechanics, authorized result and immutable publication. Only persistent effects require canonical instance promotion/application and enduring inspection. T04 does not need a dummy durable delta. Two unrelated physical systems are not required.

Original T06 blockers remain: parser currently recovers `try` with unbound copy target; no sleeve instance/equipment binding; wet usable accessible mud and writable cloth not proven; no mutation/inspection owner wired; existing optional client_request_id/in-memory cache lacks durable mutation dedupe. New architecture specifies the missing contracts but does not satisfy these prerequisites retroactively. Controlled success on an established object must precede original-scenario integration. An incomplete T06 returns truthful missing/unknown/unsupported detail without inventing success, clothing or a resource.

## Publication compatibility

Preserve the direction intent -> adjudication -> validated proposal -> application -> narration -> immutable publication. `immutable_valid_response` and `referenced_surface` pre-seal authority remain closed surfaces. `response_policy_enforcement` T05 authorized-clue composition must still avoid stock additions. Known warning copying does not reveal a second clue. Existing travel precedence, inventory delta projection, immutable accepted text and hidden protections remain authoritative. Later player inspection must explicitly extend narrow DTO/authority projections, not expose arbitrary `markings`, provenance or extension subtrees.

## Conceptual negative controls (not execution results)

| Scenario | Proposed support / exact obligation | Remaining implementation dependency |
|---|---|---|
| Touch accessible object | Yes: current T04 transient completion, empty durable delta | Shared read adapter only; preserve current behavior |
| Mark owned object | Yes: owner validates then applies active marking | Identity, atomic save, marking owner, inspection phases |
| Mark inaccessible object | Block before commit; stale access rechecked | Evidence evaluator/commit critical section |
| Copy hidden information | Reject hidden source, no hidden reason in public response | Knowledge projection + source fingerprint validation |
| Use nonexistent equipment | Unknown/false gate, no minted implement | Reference/precondition evaluator |
| Ordinary environmental medium | Bounded evidence receipt only, no inventory grant | Explicit mundane-affordance policy implementation |
| Take another character's item | No transfer absent custody/rights/contested adjudication | Deferred transfer owner; unsupported until shipped |
| Modify system equipment | Mechanical relevance consults bound adapter | Narrow adapter seam; special operations remain unsupported |
| Transfer modified object | Same ID/state once in new host, source removed atomically | Later transfer phase; not part of initial marking success claim |
| Save/reload modified object | Same revision, text/provenance and dedupe keys | Snapshot integration/fault and successful round-trip tests |
| Remove marking | Target stable marking ID, compatible method; current inspection empty | Removal operation phase |
| Duplicate request | Same key/digest returns historical receipt, no double charge/write | Durable operation ledger and ingress key |
| Application failure | No completed marking/pointer; rollback or operational uncertainty | Atomic character save, exception/fault controls |
| Switch rulesets | Preserve core ID/state; unsupported extensions inert | Adapter selection/migration; conceptual portability only |

All fourteen controls are addressed by the proposed design; several are intentionally unsupported at runtime until their phases ship. No conceptual row is implementation verification. Fresh preservation controls cover existing T04/T05/pre-seal/physical/persistence behavior only, as recorded in validation_summary.json. T06 success, transfer, removal, duplicate application, failure after marking and alternate-system execution have not occurred.
