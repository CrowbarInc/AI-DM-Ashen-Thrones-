# T06 Integration Map

Milestone: `pr_play_object_visibility_authoring`. Date: 2026-11-09.

Existing call graph: `/api/chat` -> api_chat -> chat/_chat_turn -> conversational decision -> `_unbound_physical_decline` -> parser probes -> unsupported_physical_manipulation -> sealed decline; resolver and prerequisites not reached. Standalone internal path: set_marking_visibility -> shared API mutation coordinator -> prepare_visibility -> existing character atomic save. Observation is a separate read-only call, never mutation authority.

| Stage | Status | Actual source and finding |
|---|---|---|
| Player-message interpretation | Implemented and usable | `game/api.py:7265 (api_chat)` — Existing HTTP/FIFO/commit envelope; original T06 enters conversational orchestration. |
| Action extraction | Implemented but not integrated | `game/intent_parser.py:914 (recover_actionable_explicit_world_action)` — Recovery captures physical verb try and an unbound clause. No canonical copy/source/garment/medium action. |
| Object-target resolution | Implemented but not integrated | `game/object_marking.py:167 (_target)` — Durable inventory ID lookup works internally; no natural-language sleeve-to-existing-garment/part binding. |
| Inventory/equipment resolution | Missing | `game/object_instances.py:75 (inspect_object_identity)` — Existing singleton identity is usable. Generic equipment/garment-part relation is absent; T06 has a Spellbook only. |
| Environmental-material resolution | Missing | `game/physical_adjudication.py:99 (_objects)` — Scene enumeration is not an accessible usable-mud supply resolver. Experimental owner remains disabled. |
| Physical prerequisite validation | Blocked by missing authority | `game/object_marking.py:39 (_request_error)` — Internal positive evidence schema exists; no upstream basis for this sleeve, wet accessible mud or compatibility. |
| Ruleset adjudication | Blocked by missing authority | `game/skill_checks.py:41 (resolve_skill_check)` — Existing checks exist. No integrated marking decision adapter; explicit not_applicable is a trusted assertion, not default success. |
| Object mutation authorization | Implemented but not integrated | `game/api.py:5772 (_mutate_inventory_object_marking)` — Existing world-state guard, lane and durable receipts. No player action issuer; do not call standalone lane recursively inside api_chat. |
| Marking application | Implemented but not integrated | `game/object_marking.py:77 (prepare_marking)` — Exact known text can stage one addition after all evidence is established; T06 never calls it. |
| Visibility classification | Implemented but not integrated | `game/object_marking.py:407 (prepare_visibility)` — This cycle stages typed-authorized metadata and shared receipt; no natural-language authority. |
| Observation/disclosure | Implemented but not integrated | `game/object_observation.py:118 (observe_object)` — Existing typed grants filter current active metadata. No player inspection path calls it. |
| State persistence | Implemented and usable | `game/storage.py:316 (save_character)` — Atomic character file carries active state and receipts; real save/reload/snapshots verified. Whole-turn integration still needed. |
| Narrative publication | Implemented but not integrated | `game/immutable_valid_response.py:32 (seal_delivery_contract)` — Existing seal/publication is usable, but no applied-marking DTO/assertion adapter reaches it. |
| Current decisive decline | Implemented and usable | `game/conversational_orchestration.py:2856 (_unbound_physical_decline)` — Unsupported before resolver/preconditions; T06 prior publication pointer retained. |

Required authority decisions: bind the exact previously disclosed patrol wording; identify an actually established garment and sleeve part; establish usable wet mud, access, rights and surface compatibility; supply explicit noncontested no-mechanics adjudication or delegate real mechanics. The original fixture establishes a muddy gate line but no equipped garment or accessible compatible smear. Spellbook possession and the phrase my sleeve prove neither.

Minimum viable sequence: recognize one bounded semantic copy proposal before the unconditional decline; bind disclosed source and an existing authored target/part; resolve only positively established material facts; return precise missing/ambiguous prerequisites without creating facts. For a valid controlled fixture, stage prepare_marking then prepare_visibility against its resulting revision within the already-entered whole-turn lane; commit both receipts and final character together through the existing API authority/save seam. Do not call standalone ordered_turn helpers recursively. Establish fresh observation authority, project permitted committed text, adapt that result into ExplorationEngineResult/noncombat resolution and authorized narration, validate then seal/publish. On failure discard/roll back staged state and never publish completion. Verify immediate/later inspection, reload/retry and twelve-turn preservation.

Risks: invented mud is an unauthorized material grant; invented clothing is an unauthorized inventory/equipment grant; prose before commit can claim a marking that never exists; raw receipts leak private evidence. Keep PF1e checks, DCs, spell effects and technology eligibility upstream; core metadata and IDs remain ruleset neutral. Smallest defensible next implementation is one grounded copy path with explicitly authored positive fixtures plus negative original-state cases, not transfer, crafting, a registry or a general equipment system.

Exactly one recommended next milestone: `pr_play_grounded_marking_action_integration` — a bounded end-to-end player copy action over an explicitly established existing target, disclosed source and usable medium, with truthful missing-prerequisite handling for original T06. No general object-framework expansion.
