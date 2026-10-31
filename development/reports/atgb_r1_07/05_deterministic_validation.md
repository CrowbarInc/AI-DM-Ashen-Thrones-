# 05 — Deterministic Validation

29 new checks inspect actual production messages/schema and exercise stubbed wire -> adapter -> host decision, including four direct chat deliveries. Contract C1-C7 cover conversational/mechanical distinction, player versus GM clarification, continuation, corrected-question public evidence, necessary ambiguity, restricted facts and actual pending authority. Tests use production construction, not a duplicate contract fixture. Behavioral coverage includes subject/referent/description, insufficient/private evidence, unresolved correction and no-fact withdrawal acknowledgment. Existing R1-02/R1-04 tests cover genuine pending revision, absent pending and executed-action prohibition.

Offline replay script executes six arms over R1-05 L1/L2 and R1-03 L3: preserved output and explicit substituted answer interpretation. Both use current production request assembly. Original outputs still clarify; substitution accepts OTHER/INTERPRETED GM/CORRECTION, projects visible:1/2/3 and emits a receipt plus their text with no context update/execution. Full requests, schema, records and decisions are in offline_replay.json. Input snapshots are unchanged. This is a host counterfactual, not a model selection result or new live result. Direct chat tests separately verify final API delivery; replay itself stops at decision text.

Evidence packet: artifacts/validation_evidence/atgb_r1_07/, six synthetic offline arms, structural/runtime claims only; human review UNREVIEWED. No semantic scoring, independent held-out result or benchmark performance claim. Exact commands, failures and output capture paths: test_commands.json; logs and JUnit included.

| Run | Passed | Failed | Skipped | Exit | Completion |
|---|---:|---:|---:|---:|---|
| baseline | 72 observed | 0 observed | 0 observed | 1 | interrupted; totals unknown |
| baseline_direct | 209 | 0 | 0 | 0 | complete |
| focused | 25 | 0 | 0 | 0 | complete |
| after | 238 | 0 | 0 | 0 | complete |
| broader | 0 observed | 0 observed | 0 observed | 1 | interrupted; totals unknown |
| broader_direct | 23 | 1 | 0 | 1 | complete |
| broader_baseline | 23 | 1 | 0 | 1 | complete |

Replay command: `.venv/Scripts/python.exe artifacts/atgb/atgb_r1_07/replay.py`; exit 0, six arms validated, no pytest pass count. Baseline comparison wrapper command: `.venv/Scripts/python.exe artifacts/atgb/atgb_r1_07/compare_broader_baseline.py`; exit 0; inner pytest exit 1 preserved.
