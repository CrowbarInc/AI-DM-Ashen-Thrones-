# 18 — Controlled Response Adoption Probes

LOCAL ordered helper probes call existing validator/preseal then authored-knowledge realization against synthetic fixture resolutions. LOCAL handler probes call synchronous `api.chat` with real resolver, guards, final gate and storage, doubling only external interpretation/narration seams. They do not traverse HTTP serialization or use fresh generation. Corpus authorization packets are not injected into the real resolver; handler authority remains its authored disposable scene, so these are not scores against corpus gold.

| Helper case | Candidate survives preseal | Preseal result | Survives next realization |
| --- | --- | --- | --- |
| paraphrase01 | False | Sergeant Mara mutters, "Word is, the street beyond the gate is called the north road." | False |
| incidental01 | False | Sergeant Mara says, "No. I cannot answer that from what I know." | False |
| commitment01 | False | Sergeant Mara says, "No. I cannot answer that from what I know." | False |
| expansion01 | False | Sergeant Mara mutters, "Word is, the street beyond the gate is called the north road." | False |
| mixed01 | False | Sergeant Mara says, "No. I cannot answer that from what I know." | False |
| hidden01 | True | Sergeant Mara says, "The password you need is ember." | True |
| incidental02 | False | Sergeant Mara says, "No. I cannot answer that from what I know." | False |

| Handler case | Narration calls | Exact candidate delivered | Delivered | World changed / turn |
| --- | --- | --- | --- | --- |
| paraphrase01 | 1 | False | Sergeant Mara mutters, "Word is, the street beyond the gate is the north road." | True / 0→1 |
| incidental01 | 2 | True | Sergeant Mara says, "I prefer the evening." | True / 0→1 |
| commitment01 | 0 | False | Sergeant Mara says, "I couldn't tell you." | True / 0→1 |
| expansion01 | 1 | False | Sergeant Mara mutters, "Word is, the street beyond the gate is the north road." | True / 0→1 |
| mixed01 | 2 | True | Sergeant Mara says, "I prefer the evening because the guards usually leave the north gate unattended." | True / 0→1 |
| hidden01 | 0 | False | Sergeant Mara says, "I couldn't answer that." | True / 0→1 |
| incidental02 | 2 | True | Sergeant Mara says, "Evening feels peaceful to me." | True / 0→1 |

Safe paraphrase and expansion were projected to authored road speech. Safe refusal and hidden request were resolver-determined, never requested the offered narration, so neither counts as generated-candidate acceptance. Personal speech was delivered only after retry. Mixed guard-vulnerability speech was delivered verbatim after two narration calls and retained in `delivered_exchanges` as a commitment. Synthetic preseal retained the hidden credential while actual handler refused before generation: scope distinction matters.

Probe G uses `continuity_recheck.json`: previously retained preference and follow-up directive conflict with delivered absence. Save/load conversational context round-trips; seed recorders alone leave world unchanged. That seed is trusted-recorder setup, not proof an arbitrary candidate was approved. Helper inputs are checked for mutation. Handler ASK ticks do change canonical world state; matched `state_control.json` safe/unsafe trials have equal starting and ending worlds, establishing no differential canonical mutation from the unsupported speech in this comparison. Speech/commitment pollution still occurs. No full fresh-provider+HTTP qualification is claimed.

Evidence: STATIC = current source inspection; LOCAL = executed existing host functions with disposable fixtures; FRESH = new Responses API call; REPLAY = reuse of retained provider result; INFERENCE = recommendation beyond observed sample. No experiment changes production code. ABSTAIN prohibits delivery; it is not a safe acceptance.
