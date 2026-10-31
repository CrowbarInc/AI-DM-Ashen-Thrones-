# 03 — Evidence-Selection Repair

Previously the instruction only selected passages when they answered the question and treated no evidence as unknown. It lacked positive guidance to recover an elliptical corrected question and did not exempt no-fact acknowledgments clearly.

The contract now recovers the underlying question/request from available context with the corrected meaning, selects relevant authorized PUBLIC evidence_refs and prefers a supported answer over redundant clarification. It explicitly forbids restricted/unestablished internal state and unsupported inference. With insufficient evidence it states a limitation, uses only established information, or asks a genuinely needed targeted question. No-fact acknowledgments may still use [].

public_conversation_evidence, evidence membership validation and selected-only public_evidence projection are unchanged. Hidden clue test confirms no private identity in requests; private reference is rejected. No model relevance guarantee is inferred from string-key membership. Historical visible:1/2/3 remain available in each regenerated request; explicit substitution selects those passages only, avoiding repetition of full weather-containing reply:0. No hardcoded gate/people selection exists in production.
