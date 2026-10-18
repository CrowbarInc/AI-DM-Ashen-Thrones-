# 22 — R2C Closure Assessment

```json
{
  "1_grounded_eligibility": true,
  "2_genuine_ambiguity": true,
  "3_addressee_authority": true,
  "4_subject_authority": true,
  "5_authorized_disclosure": true,
  "6_knowledge_distinction": true,
  "7_continuity": true,
  "8_information_integrity": true,
  "9_regression": true,
  "10_fresh_provider": true,
  "11_performance": true
}
```

Exact retained failure identities and evidence classes:

```json
[
  {
    "id": "historical.before_reproduction",
    "evidence": "recorded-provider wire injection + real HTTP",
    "failure": "unresolved north gate annotation bypasses social resolver",
    "artifact": "before_reproduction.json"
  },
  {
    "id": "controlled.clarification_probe.turn_3",
    "evidence": "controlled wire + real HTTP",
    "failure": "bare repeat after clarification repeats previous NPC fact",
    "artifact": "clarification_probe.json"
  },
  {
    "id": "qualification_before_status_fix.primary.turn_12",
    "evidence": "fresh provider /api/chat",
    "failure": "explicit named addressee rejected via npc_to_ask annotation and missing target",
    "artifact": "qualification_before_status_fix/live_qualification.json"
  },
  {
    "id": "qualification_before_status_fix.primary.turn_13",
    "evidence": "fresh provider /api/chat",
    "failure": "stale CLARIFICATION_REQUIRED blocks unknown factual answer",
    "artifact": "qualification_before_status_fix/live_qualification.json"
  },
  {
    "id": "qualification_before_status_fix.primary.turn_14",
    "evidence": "fresh provider /api/chat + later source audit",
    "failure": "clarifier mentions north road but fails resolver-owned factual disclosure; early substring check missed this",
    "artifact": "qualification_before_status_fix/live_qualification.json"
  },
  {
    "id": "original_holdout.F07",
    "evidence": "deterministic frozen expectation",
    "failure": "old conservative retention expectation superseded by authoritative raw-question eligibility",
    "artifact": "original_holdout_final_attempt.json"
  },
  {
    "id": "literal_role.L01",
    "evidence": "controlled reconciliation",
    "failure": "literal interlocutor subject incorrectly cleared as addressee metadata",
    "artifact": "literal_role_before.json"
  },
  {
    "id": "literal_role.L02",
    "evidence": "controlled reconciliation",
    "failure": "literal addressee subject incorrectly cleared as addressee metadata",
    "artifact": "literal_role_before.json"
  },
  {
    "id": "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[confirm_single_candidate]",
    "evidence": "intermediate regression",
    "failure": "transient Windows os.replace PermissionError; passed subsequent full runs",
    "artifact": "qualification_before_clarification_fix/final.xml"
  }
]
```



All eleven gates pass within the tested grounding/authority boundary. The historical fact reaches its resolver; real ambiguity, explicit resolution, clarification repetition, unknown/withheld posture, correct topic/speaker source, immutable adoption, delivered history and canonical state are evidenced. Predecessor topic/recall behavior and its frozen holdouts remain intact.



Intermediate live failures and the controlled continuity failure are retained. The later audit additionally flags status-attempt primary turn 14: its clarification merely mentioned north road, fooling the early substring checker; final audits require actual resolver-owned topic provenance. F07's old retention expectation failed the final authority contract; independently frozen N01–N05 qualified the final repair afterward. Closure is recommended with documented limitations and external review, not as proof of universal language understanding or all repository tests passing.
