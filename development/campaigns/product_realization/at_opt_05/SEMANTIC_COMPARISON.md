# Semantic comparison

Compared user instruction lists on the attached F3 rebuild: selected full list versus `manual_play_compact` on the same state. System-prompt dedupe had already removed lines that the system prompt repeats, including the long rule-priority sentence and the no-validator sentence, from both lists. The full line list is in `artifacts/at_opt_05/eligibility_analysis.json`.

Shared lines include the `action_outcome` mode deltas, the narration-mode length line, and the two public disclosure lines. Compact therefore still says the authoritative result comes first, and it still says undiscovered facts are unavailable. That disclosure sentence is not the visibility contract.

`narration_visibility`, `scene_state_anchor_contract`, `speaker_selection`, `response_policy`, `lead_context`, and `narrative_plan` remain on the compact public payload. `first_mention_contract` does not. It is not a key of `response_policy`.

## Full-only material

| Lines | Class | Still available if compact is selected? |
| --- | --- | --- |
| Six visibility sentences, including “You MUST NOT reveal hidden or undiscovered facts” and the visible-entity limits | A. Authority-critical | The visibility object remains. `forbid_secret_leak` remains. The shared disclosure sentence remains. The MUST NOT sentences do not. Not equivalent |
| Six first-mention sentences, and the `first_mention_contract` object | A. Authority-critical | Absent from instructions and from the payload. Not in `response_policy` |
| Three speaker-selection hard rules, including empty `allowed_speaker_ids` and the generic-speaker ban | A. Authority-critical | `speaker_selection` remains. The hard-rule sentences do not |
| Scene-state anchor sentences | A. Authority-critical | The contract object remains. The mandatory wording does not |
| “Follow authoritative engine state…” and the narration-obligation authority limit | A. Authority-critical | Obligations remain as data. These sentences do not |
| Policy-bridge sentence, including “do not treat policy prose or the answer recipe as authority to create facts” | A. Authority-critical | Compact’s policy tail names the policy objects and does not carry the “do not create facts” clause |
| World-simulation faction pressure and agenda sentence | B. Continuity-critical | Public projection nulls nested `world_pressure` and removes `world_progression_summary`. This sentence is the remaining carrier on the full list |
| Lead-registry usage sentences | B. Continuity-critical | `lead_context` remains. The “do not invent leads” sentences do not. F3 pressures were empty, so the loss is latent on this turn |
| “Use campaign and world state to keep political and strategic continuity.” | B. Continuity-critical | Not restated |
| Scene-momentum hard rule and tag requirement | C. Narrative-quality | `scene_momentum_due` can still sit on obligations. The tag rule does not |
| Specificity, forbidden generic phrases, perception tells, NPC-answer shape | C. Narrative-quality | Compact authenticity and answer-first lines cover only part of this |
| Extra anti-echo sentences beyond the one compact paraphrase ban | D. Redundant with the compact sentence, for the ban itself | The compact sentence does not name the obligation flags. The flags remain on the object. Equivalence is limited to the ban |
| Answer, uncertainty, anti-railroading, context, purity, and scene-anchoring pointer lines | E. Conditionally relevant as indexes | The policy objects remain, and the compact tail names them. The pointer wording is shorter. Not treated as proven redundant |
| `new_scene_draft`, `world_updates`, and `suggested_action` permission lines | E. Conditionally relevant | These are the lines a real move would use. Compact removes them even if a transition node is still on the payload |
| Social privacy and non-interjection lines | E. Conditionally relevant | No active interlocutor on this examine-turn plan |
| Full narrative-plan sentence versus the compact plan sentence | F. Uncertain | Both exist. The shared mode line still says CTIR and `response_policy` win conflicts. The compact plan sentence does not repeat “never override CTIR” |
| N3 actor-anchor emphasis bump sentence | C. Narrative-quality | Plan data can still carry the bump. Compact mentions emphasis bands and does not name this bump |

## What compaction would change on this turn

The structured transition object would still be present under forced compact, still saying a same-scene location change is required. Compaction does not fix the flag. It removes the instruction text that tells the model how to treat visibility, first mention, speakers, and a real scene draft.

Policy objects for anti-railroading, context separation, purity, narrative authority, and fallback behavior remain. Pointing at them is not the same as the missing MUST NOT lines. Semantic equivalence was not granted for overlapping names.

Narrative mode lines are kept. A genuine transition’s mode deltas would also be kept if compact were forced while mode was `transition`. The eligibility gate, not the compact template, is what withholds compact from required nodes. The template itself does not contain a transition-motion section beyond whatever mode lines the plan already has.
