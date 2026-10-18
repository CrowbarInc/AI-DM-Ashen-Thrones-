# PR-BT Selective Epistemic Protocol Diff

MODE: SELECTIVE RESTORATION
MODEL/API CALLS: ZERO
This is a replacement of one abstract sentence. It is not a rollback of the PR-BT deduplication.

The restored text is the 651-character paragraph from `PR-BT_epistemic_guidance_delta.json`, placed in `SYSTEM_PROMPT`. Sentence costs below partition that paragraph. They are not additive.

## BEFORE PR-BT DEDUP

Relevant verbose epistemic guidance from the PR-BS P1 provider request. These paragraphs are still absent from the reconstructed P1/P2/P3 requests.

System question rule, 305 characters:

> If the player asks a direct question, you must answer it concretely. If full certainty is unavailable, provide the best grounded partial answer and state uncertainty in-character through rumor, witness limits, distance, darkness, missing access, or incomplete observation. Do not repeat prior information.

Narrative-authority instruction, 554 characters:

> NARRATIVE AUTHORITY (POLICY): Obey response_policy.narrative_authority for assertion boundaries; deterministic enforcement is authoritative. Do not assert unresolved outcomes as settled fact. Do not assert hidden causes or hidden truths as confirmed without basis in published visible/engine state. Do not assert NPC motives or intentions as fact without explicit basis. When certainty is unavailable, defer via a roll/check request, bounded uncertainty, or conditional/branch framing. Observable visible cues are allowed; omniscient conclusions are not.

Fallback known-edge instruction, 459 characters:

> FALLBACK BEHAVIOR (MANDATORY): When `fallback_behavior.uncertainty_active` is true, do not invent certainty and do not fabricate authority. Either give a bounded partial answer or, only when `fallback_behavior.allowed_behaviors.ask_clarifying_question` is true and a partial would mislead, ask one brief clarifying question. Keep uncertainty diegetic, state the strongest grounded known edge plus the unknown edge, and offer a natural next lead when possible.

Narrator-anchor line, 163 characters:

> If there is no active NPC speaker, keep uncertainty in diegetic narrator voice but anchor it to visible scene circumstances rather than generic omniscient wording.

World-facing limit line, 165 characters:

> Frame uncertainty as world-facing limits only: who knows, what can be seen, what distance, darkness, rumor, missing witnesses, or incomplete clues prevent right now.

Those five passages alone are 1,646 characters. They sat inside a larger deletion: narrative-plan field essays, the long answer-completeness essay, and the rest of the policy-tail restatements. None of those essays were restored.

## FAILED PR-BT OPTIMIZED

The sentence that replaced the uncertainty rule, 99 characters, removed by this slice:

> If certainty is incomplete, give the strongest grounded partial answer and keep the limit diegetic.

Surviving abstract neighbors, left in place because they are field pointers rather than a second epistemic essay:

- `UNCERTAINTY POLICY` points at `response_policy.uncertainty` and says to frame uncertainty as world-facing limits only.
- `POLICY BRIDGE` says to keep uncertainty qualified and preserve hypotheses, and says policy prose and the answer recipe do not create facts.
- `Player hypotheses remain hypothetical unless the supplied decision/claims authorize more.` This authorization exception is not in the new paragraph, so it stays. It was already present. It is not new prose.

`response_policy`, `gm_resolution_decision`, and `decision_facing_answer_recipe` were already the authority objects. They were not the deleted text.

## SELECTIVE RESTORATION

Final compact protocol, 651 characters, once in the constructed system prompt:

> EPISTEMIC REALIZATION: On an interpretation, or when the player offers a hypothesis, state the authorized observations first. If the decision permits inference, add one possibility tied to those observations and say explicitly that cause, actor, time, and history stay unresolved. Do not add a mechanism, setting, maintenance history, or causal chain the observations do not contain. Do not use certainty wording for inferred or hypothetical material, and do not attach that wording to the observations in the same sentence. A player hypothesis stays hypothetical: the visible facts may be compatible with it, and observation alone does not settle it.

Net provider cost versus the failed live optimized requests: **552 characters** on every probe (651 added, 99 removed). Instructions, response policy, turn packet, and answer recipe character counts did not move with this edit.

| Semantic element | Behavior it teaches | Why it was restored | Canonical authority owner | Character cost | P1 | P3 | P2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Scope plus observation | On an interpretation or a player hypothesis, start from the authorized observations. Do not invent evidence to enrich the reading. | PR-BT's "strongest grounded partial" pushed P1 into ringing, exposure, wear, and a causal chain. | `gm_resolution_decision` establishes which observations are world truth. This sentence only says to state them. | 126 | yes | yes | Scoped. Ordinary NPC dialogue is outside "on an interpretation, or when the player offers a hypothesis." |
| Useful qualified inference and unresolved status | If the decision permits inference, add one possibility tied to those observations, and say that cause, actor, time, and history stay unresolved. | P1 needs a useful possibility rather than observation-only refusal, and an explicit unsettled cause/history. The recipe already says could/may/might for P1; this sentence tells the narration to keep the limit explicit. | The infer act and narration constraint live on the decision. The P1 recipe still owns "one qualified possibility" and "could, may, or might." | 155 | yes | The "if the decision permits" clause does not fire when inference is forbidden. | No, unless the decision permits inference. P2 does not. |
| No unsupported history | Do not add a mechanism, setting, maintenance history, or causal chain the observations do not contain. | This is the scope ceiling the P1 initial narration crossed (frequent ringing, exposure, leading-to wear). | The P1 decision constraint already says no cause, actor, or history is established. | 103 | yes | Low. P3 has no infer act. | No. |
| Certainty ceiling | Do not use certainty wording for inferred or hypothetical material, and do not attach that wording to the observations in the same sentence. | P3 failed on "clearly," including "clearly visible" in the observation clause. The protocol forbids that class of wording. It does not hard-code a validator token. | `response_policy.narrative_authority` still forbids settling unresolved outcomes. The narration validator still owns the token check. This sentence does not change the validator. | 141 | yes | yes | Low. It does not rewrite ordinary dialogue. |
| Hypothesis fit without promotion | A player hypothesis stays hypothetical. The visible facts may be compatible with it. Observation alone does not settle it. | P3's successful shape discusses fit and leaves the deliberate cause unsettled. The P3 recipe does not teach that shape. | The P3 decision has no infer act and does not authorize the hypothesis. The recipe still says no player hypothesis is authorized on that turn. | 126 | The same non-promotion rule applies if a hypothesis is in play. | yes | No, unless the player is offering a hypothesis. P2 is a loaf question. |

Modality is taught inside the inference and hypothesis sentences ("one possibility," "may be compatible"). Those words are examples of qualified speech. They are not a closed list of legal forms. The P1 recipe's "could, may, or might" line was not edited.

Usefulness is the "add one possibility" obligation plus the lines that were already in the prompt: "Answer direct questions first" and "Prefer partial truth over refusal." Uncertainty is not an instruction to refuse.

## What this diff is not

The narrative-plan essays, the 1,684-character anti-railroading essay, the context-separation essay, the purity essay, the tone essay, and the perception example were not copied back. Deterministic checks assert these PR-BS sentences are absent from the constructed system prompt and instruction list:

- "provide the best grounded partial answer and state uncertainty in-character"
- "state the strongest grounded known edge plus the unknown edge"
- "anchor it to visible scene circumstances rather than generic omniscient wording"
- "Do not assert hidden causes or hidden truths as confirmed without basis in published visible/engine state"
- "omniscient conclusions are not"
- "give the strongest grounded partial answer and keep the limit diegetic"
