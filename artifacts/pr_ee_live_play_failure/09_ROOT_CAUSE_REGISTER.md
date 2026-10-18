# 09 — Root-Cause Register

Task classification letters are used verbatim (A lifecycle; B interpretation; C orchestration; D context; E confirmation; F resolver contract; I fallback; J prompt/schema; K integration/configuration; L architectural deficiency). No G narration or H final-emission defect is established for this interaction.

## EE-01 — Message-purpose/authority contract excludes ordinary GM/session/narrative requests

- Role / categories: primary; C, J, L.
- Evidence: Original turns 1,2,6; orchestration:1616–1674; schema modes; prompt mode line.
- Trigger: Understood readiness/start/GM address with no connected world operation.
- Responsible component: PR-DR prompt / PR-DO schema / record decision / API mode routing.
- Downstream consequence: Understood intention becomes clarification or unsupported executable proposal.
- Severity / confidence: Critical; High.
- Recommended repair boundary: Typed recipient and purpose independent of executable components; non-mutating GM answer path with grounded context.

## EE-02 — Unsupported singleton becomes compound confirmation, including zero executable steps

- Role / categories: primary; C, E, F, I.
- Evidence: Original turns 3,6 and exact HTTP replay; stored supported=false.
- Trigger: Any unsupported component, even when component count is one.
- Responsible component: conversational_orchestration.py:1442–1477,1673;1146–1188.
- Downstream consequence: False multi-action language, approval of known impossible action, misleading promise.
- Severity / confidence: Critical; High.
- Recommended repair boundary: Separate unsupported/single/compound routes; validate each offer before confirmation; preserve operation identity and scope.

## EE-03 — GM rejection/recipient absent from typed continuation; questions bypass pending; bridge clarification not stored

- Role / categories: primary; D, C, E, B.
- Evidence: Original turns 4–6, original post-session; captured reconstructed context includes prior refusal.
- Trigger: Why not? after engine-owned rejection; subsequent explicit GM recipient.
- Responsible component: orchestration:323–449,1352–1360; API early-response/context updater.
- Downstream consequence: Question becomes NPC ASK; missing_target emits Who are you asking; next reply cannot fill unstored question slot.
- Severity / confidence: Critical; High.
- Recommended repair boundary: Persist rejection subject/reason/recipient and actual pending conversational obligation; dispatch GM follow-ups before NPC action routing.

## EE-04 — Lifecycle availability tied to empty transcript; recognized chat opening still filtered before lifecycle dispatch

- Role / categories: primary; A, C, L.
- Evidence: Original turn 2 follows logged clarification; lifecycle_gate_probes; recognized_fresh_start_replay.
- Trigger: Any non-opening chat before start; or fresh matching start cue with live interpretation enabled.
- Responsible component: api.py:4474–4494,4565–4578,6198–6290,6508.
- Downstream consequence: Started=false yet start UI disabled; existing opening implementation unreachable for these requests.
- Severity / confidence: Critical; High for current implementation; historical UI before turn one unknown.
- Recommended repair boundary: Route lifecycle intent before world interpretation; gate start on authoritative lifecycle completion rather than arbitrary transcript content.

## EE-05 — Provider assigns campaign start to INVENTORY_GRANT; Why not to in-world ASK

- Role / categories: contributor; B, J.
- Evidence: Original raw_interpretation turns 3 and 5, not inferred from replies.
- Trigger: Begin; Why not under restricted mode/operation prompt.
- Responsible component: Original interpreter completions / prompt-schema authority categories.
- Downstream consequence: Unsupported/missing-target processing; downstream routing amplifies classifier errors.
- Severity / confidence: High; High occurrence; frequency unmeasured.
- Recommended repair boundary: Correct semantic contract and context projection; retain validation against unintended operations, avoid phrase handlers.

## EE-06 — Mode and operation vocabularies disagree across schema, eligibility and orchestration

- Role / categories: secondary integration defect; C, F, J.
- Evidence: Original turn 6; static schema/routing inspection for RULES_QUESTION.
- Trigger: OTHER+SOCIAL_SIGNAL observed; RULES_QUESTION mismatch latent.
- Responsible component: schema.py:9,35; eligibility.py:23; orchestration.py:91–108,1619.
- Downstream consequence: Describable social signal becomes unsupported; some OOC modes miss answer handling.
- Severity / confidence: High; High current source; RULES_QUESTION not observed here.
- Recommended repair boundary: One shared, explicit mapping from message domain and class to conversation/execution disposition.

## EE-07 — Early-path telemetry calls every completed conversational response successful; tokens/stages missing at summary

- Role / categories: secondary observability; K.
- Evidence: Original turn 4 resolution.success=false but performance.successful=true; nested usage vs null summary.
- Trigger: Non-mutating clarify/decline early return with interpreter usage.
- Responsible component: api.py:785–791,1002–1033.
- Downstream consequence: Responsiveness instrumentation cannot measure playability or summarize interpreter cost reliably.
- Severity / confidence: Medium; High.
- Recommended repair boundary: Separate transport/delivery, decision validity, opening/gameplay success; aggregate interpreter usage.
