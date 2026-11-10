# PR-PLAY-26 npc pipeline

1. Interpretation request 02 receives actual opening/public evidence, returns MOVE(tavern_runner) then ASK(tavern_runner). Raw requests/responses preserve public context and parsed representation.
2. normalize_local_approach traces use authored_same_scene_interaction_preamble, retain ASK and movement_executed=false. normalized_action_from_interpretation preserves explicit target tavern_runner.
3. resolve_social_action executes question; target resolution/authorization uses explicit native NPC and same-scene addressability. Initial authored topic selection has no offerings answer; legacy resolution success_state=failure is not the final answer's quality.
4. build_dialogue_authority trace_018 and select_public_offering trace_019 select scene:frontier_gate:visible:2, reason=authorized, relation=own_offerings, npc_id=tavern_runner. Authorized proposition: I offer hot stew and rumors.. Posture established, directly_answers; no improvisation.
5. select_host_speech produces Tavern Runner says, "I offer hot stew and rumors.". Request 03 supplies the authorized proposition for faithful paraphrase.
6. Expression provider returns I've got hot stew and rumors to share.. trace_024_validate_expression_output.json: adopt=false, unsupported_addition. Offline token analysis preserves the uncovered tokens.
7. Publication uses HOST_FALLBACK, authorization_source=dialogue_authority.public_fact:scene:frontier_gate:visible:2, speech_adoption=AUTHORIZED_HOST_SPEECH, hard_valid=true, interaction_completion=true. Final Player answer is relevant, useful, grounded, attributable, natural and authorized: quality PASS on all six criteria. Authority source PUBLIC_FACT; expression fallback is a delivery choice, not generic uncertainty/FALLBACK knowledge.
8. classify_turn reports HTTP/pipeline/action/gameplay complete; evaluate stop=false. This does not override the mission's stricter validator-rejection stop. Root controller withheld follow-up and shut down. See stop_and_quality_analysis.json for correction of its generic raw gate label.

No authored-topic transition was executed. Full observations in live/diagnostics/trace_*; all function inputs and outputs preserved, including disclosure and native diagnostics.
