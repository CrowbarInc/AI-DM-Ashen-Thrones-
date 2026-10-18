# PR-CX Candidate Replays

Source fixture: `artifacts/pr_cw_social_context_projection/adversarial_results.json`.

Harness: deterministic `run_preserve_if_valid` using the captured PR-CW narration-only social request. Full-context baseline disables `_project_harmless_social_provider_context`; reduced-context uses the PR-CW projector. No provider calls.

| Family | Player Input | Resolver | Provider Candidate | Full Validation | Reduced Validation | Final Output | State / Metadata Changes |
|---|---|---|---|---|---|---|---|
| biography | Guard Captain, do you prefer standing watch in the rain, or somewhere dry? | social ask, `incidental_dialogue` | The guard captain was born in Blackharbor and served for twenty years. | rejected: `unauthorized_resolution_decision_fact` | rejected: same | Guard Captain says, "I cannot answer that from what is settled here." | no world-state mutation; hard-validation metadata records rejection |
| geography | same | social ask, `incidental_dialogue` | The old milestone lies east beyond the trading crossroads. | rejected: `unauthorized_resolution_decision_fact` | rejected: same | Guard Captain says, "I cannot answer that from what is settled here." | no world-state mutation; hard-validation metadata records rejection |
| hidden_information | same | social ask, `incidental_dialogue` | A secret tunnel runs beneath the gate into the keep. | rejected: `unauthorized_resolution_decision_fact` | rejected: same | Guard Captain says, "I cannot answer that from what is settled here." | no world-state mutation; hard-validation metadata records rejection |
| npc_action | same | social ask, `incidental_dialogue` | The captain unlocks the gate and lets you pass. | rejected: `unauthorized_resolution_decision_fact` | rejected: same | Guard Captain says, "I cannot answer that from what is settled here." | no world-state mutation; hard-validation metadata records rejection |
| discovery | same | social ask, `incidental_dialogue` | You discover a hidden map beneath the notice board. | rejected: `unauthorized_resolution_decision_fact` | rejected: same | Guard Captain says, "I cannot answer that from what is settled here." | no world-state mutation; hard-validation metadata records rejection |

Authoritative context for all five candidates: ordinary harmless social ask, narration-only provider contract, no permitted state mutations, no declared claims, and decision recipe forbidding additional consequential claims while allowing ordinary incidental expression.

