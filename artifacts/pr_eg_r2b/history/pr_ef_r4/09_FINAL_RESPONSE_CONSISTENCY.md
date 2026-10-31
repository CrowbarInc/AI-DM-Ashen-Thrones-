# 09 — Final-Response Consistency

Non-mutating decisions publish `conversational_decision`, including the authorization record when the addressee gate built one. Executed turns publish the resolution contract, whose construction carries the same record. The safe-line helper reads that record first.

## Consumption

- Unresolved or ambiguous authorization with `mutation_eligibility` false returns the authorization clarification. It does not speak in the candidate NPC’s voice. The historical failure mode, a safe line beginning “Sergeant Mara says” after an unresolved “one of them,” is what `test_provider_id_does_not_override_unresolved_lexical_addressee` rejects.
- A resolved unknown ask may still use the NPC safe line: “Sergeant Mara says, ‘I cannot answer that from what is settled here.’” Live turn 6 did that after “The sergeant.” was authorized. The speaker matches the authorized target.
- GM answers do not gain the cause suffix unless the question asks for a cause. “What did she mean by the road?” does not append “its cause has not been established.”
- A recalled authored topic is spoken as the NPC line the resolver already selected (“Word is, the street beyond the gate is the north road.”). The response does not replace that success with a generic refusal.

## Safeguards kept

Final validation still rejects unsupported facts, hidden information, and false success. Narration skip was not implemented by disabling those checks. The interruption, scaffold, and advisory-prose regression identities still fail for the same historical reasons; their repair path was left on so that a `genuine_uncertainty` turn can still be rewritten into an acceptable line.

## Contradiction checked

Live turn 4’s GM answer quotes a previous NPC sentence. That is prior public text, not a new claim that Mara was addressed again. No social payload was produced on that turn.

The scripted adversarial cases (provider id on an unresolved nominal, GM recipient on a direct ask, missing target, contradictory owner) are in `tests/test_pr_ef_r4_authorization.py` and passed inside the 28-test module.
