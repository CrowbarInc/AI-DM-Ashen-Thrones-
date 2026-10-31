# 04 — Strict Social Prompt Attribution


LOCAL: `o200k_base`, tiktoken 0.14.0. Production `build_messages` executed against disposable seeded data with scripted interpretation and narration. Actual serialized system/user message content was retained, then tokenized locally. These are measured content-token counts; provider framing, hidden API overhead and historical exact prompts are excluded. No estimate is presented as measured usage.

| Structural category | Street-name capture | Preference capture |
| --- | --- | --- |
| A system/developer | 893 | 893 |
| B dialogue instructions | 3809 | 3551 |
| C simulation/world | 3875 | 3202 |
| D identity/character | 635 | 637 |
| E top-level knowledge | 114 | 114 |
| F history/continuity | 1381 | 1695 |
| G resolver/contracts | 6138 | 6337 |
| H validation/policy | 7245 | 7172 |
| K other (question) | 19 | 15 |

I tools/schema: 0 separately passed tools, 0 API JSON schema; output format lives in system/instructions. J duplicates is a cross-cutting inventory, not a mutually exclusive extra category. Group JSON wrapper/boundary residuals are -5 and -5 tokens; do not naively sum isolated serialized group costs. Total system+user content: **24,104 / 23,611**. Exact characters and individual top-level fields are in `local_prompt_attribution.json`.

These buckets describe physical prompt sections, not a semantic separation of every fact. NPC topics/knowledge are also nested inside world, mechanical_resolution, decision and turn_packet. The 114-token E bucket counts only top-level selected clue representations, not all NPC knowledge. Full nested facts must be traced before removing anything. System/instructions similarly mix dialogue and global policy.

The largest payload categories are H (7,245/7,172) and G (6,138/6,337), then B (3,809/3,551). Simulation C is 3,875/3,202. The existing size is primarily layered instruction, policy, validation and resolver projections. Dropping the entire world would leave most of the cost and could drop relevant knowledge provenance.

Exact duplicate examples (street capture): answer_completeness.trace occurs three times (248 content tokens each), response_delta twice (432 each), tone_escalation / nested tone_escalation_contract twice (407 each). The inventory records subtree hashes and paths. Parent/child duplicate spans overlap; no additive savings claim is made. Semantically redundant but non-identical contracts remain outside this exact-duplicate inventory.

STATIC: `gm.py:4250` and `:4213` already deduplicate exact provider contracts/policy; `:4403` harmless social projection has a long conjunction of eligibility conditions. The captured payloads retain simulation, opening and policy surfaces because they do not satisfy that narrow projection. This is not evidence that deleting every retained field is safe.

Ordinary dialogue needs target/voice, actual question and conversational task, relevant delivered content, selected authorized facts with epistemic/disclosure status, stable commitments and resolver boundaries. Unrelated combat/character statistics, global faction progression, opening-scene instructions and repeated validation debug traces are unnecessary for these examples. Relevant presence, disclosure rules, mechanical outcomes and prior delivered commitments cannot be reconstructed by the model. Host validation can retain full state without placing it all in the provider prompt.

HISTORICAL: PR-EG-R1 records roughly 24–26k provider input tokens per initial social narration. Fresh full-prompt requests were not sent after automatic review rejected the export. The measured local capture reproduces the size order; it is not an exact attribution of the unretained historical prompt.


Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
