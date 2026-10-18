# 04 — Production Integration Design

`game/host_constrained_candidates.py` generates candidates and compiles one selection into the existing plan schema. `propose_semantic_plan` uses that path only when the candidate gate is on. `authorize_information_turn` then performs referent bind, source coverage, disclosure, and the locked host line. A clarification shell uses conversational act `other` plus `clarification_needed`, and only while the candidate gate is on, so the semantic planner's rejection behavior is unchanged.
