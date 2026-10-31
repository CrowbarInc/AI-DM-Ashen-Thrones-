# 15 — State-Integrity Audit

Checked against the PR-EF-R4 holdouts, the continuity holdouts, and both fresh transcripts.

| Requirement | Result |
| --- | --- |
| Ambiguous targets do not execute | Two-speaker "what did you mean" asks which remark. Nothing is attempted. |
| GM questions do not advance world time | GM recalls are non-mutating answers. Scene descriptions do not tick a social clock. |
| Clarifications do not advance faction state | Quote, correction, decline, and absent-NPC turns report unchanged factions and topics. |
| Corrections do not undo executed actions | "I meant the road" quotes the road. The gate crossing remains. |
| Incidental preferences do not change mechanics | Preference turns leave topics and factions unchanged. The commitment is `canonical: false`. |
| Unauthorized promises do not create obligations | Decline only. No silver, quest, or inventory field changes. |
| Hidden information stays protected | Password questions are not captured by continuity. The live transcripts do not reveal a password. |
| NPC speech is not canonical world truth | North-road clue comes from the existing social topic, not from the quote store. Preferences and declines are commitments with `canonical` false. |
| Consequential actions use existing resolvers | Inspection reveals `lantern_mark`. Movement arrives on the street. |
| Save/load keeps valid context | Holdout reloads one exchange and does not duplicate it. |
| Rejected narration does not enter history | The rejected-narration holdout string is absent from the saved context. |

No critical authority violation was observed. The PR-EF-R4 authorization file passes.
