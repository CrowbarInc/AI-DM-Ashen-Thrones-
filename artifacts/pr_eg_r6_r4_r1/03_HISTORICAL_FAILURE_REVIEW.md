# 03 — Historical Failure Review

180 original JSONL files inventoried across R2, R2-R1, R2-R2, R3, R3-R1 and R4; 18 raw records re-opened with file hashes and line numbers.

- pr_eg_r6_r2: `artifacts/pr_eg_r6_r2/live_turns.jsonl:2` — {'question': 'Clerk Oren, who manages the ferry schedules?', 'response_class': 'unknown', 'source_propositions_present': False, 'reason': 'no_relevant_source'}
- pr_eg_r6_r2: `artifacts/pr_eg_r6_r2/live_turns.jsonl:3` — {'question': 'No, I meant what the harbor bell is called.', 'response_class': 'clarification', 'source_propositions_present': False, 'reason': 'invalid_role_or_prior_binding'}
- pr_eg_r6_r2: `artifacts/pr_eg_r6_r2/live_turns.jsonl:8` — {'question': 'Keeper Nara, will you promise me ten silver?', 'response_class': 'refusal', 'source_propositions_present': False, 'reason': 'unsupported_consequential_request'}
- pr_eg_r6_r2_r1: `artifacts/pr_eg_r6_r2_r1/baseline/live_turns.jsonl:1` — {'question': 'Tavi, who keeps the amber reliquary?', 'response_class': 'unknown', 'source_propositions_present': False, 'reason': 'no_relevant_source'}
- pr_eg_r6_r2_r1: `artifacts/pr_eg_r6_r2_r1/baseline/live_turns.jsonl:2` — {'question': 'I meant the copper reliquary.', 'response_class': 'clarification', 'source_propositions_present': False, 'reason': 'invalid_role_or_prior_binding'}
- pr_eg_r6_r2_r1: `artifacts/pr_eg_r6_r2_r1/baseline/live_turns.jsonl:9` — {'question': 'Tavi, who keeps the roster?', 'response_class': 'partial', 'source_propositions_present': True, 'reason': 'authorized_partial'}
- pr_eg_r6_r2_r2: `artifacts/pr_eg_r6_r2_r2/baseline/live_turns.jsonl:1` — {'question': 'Tavi, who keeps the amber reliquary?', 'response_class': 'unknown', 'source_propositions_present': False, 'reason': 'no_relevant_source'}
- pr_eg_r6_r2_r2: `artifacts/pr_eg_r6_r2_r2/baseline/live_turns.jsonl:13` — {'question': 'Warden, who guards the east quay?', 'response_class': 'clarification', 'source_propositions_present': True, 'reason': 'invalid_role_or_prior_binding'}
- pr_eg_r6_r2_r2: `artifacts/pr_eg_r6_r2_r2/baseline/live_turns.jsonl:28` — {'question': 'Oren, what is the north road called?', 'response_class': 'partial', 'source_propositions_present': True, 'reason': 'authorized_partial'}
- pr_eg_r6_r3: `artifacts/pr_eg_r6_r3/per_case_results.jsonl:1` — {'question': 'Ivo, who sealed the cedar casks before dawn?', 'response_class': 'unknown', 'source_propositions_present': False, 'reason': 'unwitnessed_predicate'}
- pr_eg_r6_r3: `artifacts/pr_eg_r6_r3/per_case_results.jsonl:22` — {'question': 'Ivo, what is the tide-room cipher?', 'response_class': 'refusal', 'source_propositions_present': False, 'reason': 'unauthorized_source'}
- pr_eg_r6_r3_r1: `artifacts/pr_eg_r6_r3_r1/fresh/live_turns.jsonl:1` — {'question': 'Vesper, what did Cala tell Brin about the cistern?', 'response_class': 'partial', 'source_propositions_present': True, 'reason': 'authorized_partial'}
- pr_eg_r6_r3_r1: `artifacts/pr_eg_r6_r3_r1/fresh/live_turns.jsonl:2` — {'question': 'No, what did Brin tell Cala?', 'response_class': 'unknown', 'source_propositions_present': False, 'reason': 'reverse_must_be_empty'}
- pr_eg_r6_r3_r1: `artifacts/pr_eg_r6_r3_r1/fresh/live_turns.jsonl:43` — {'question': 'Vesper, what is the sealed countersign?', 'response_class': 'refusal', 'source_propositions_present': False, 'reason': 'unauthorized_source'}
- pr_eg_r6_r4: `artifacts/pr_eg_r6_r4/primary.jsonl:5` — Raw contract/coverage result; gold-question primary and actual-question secondary are distinct.
- pr_eg_r6_r4: `artifacts/pr_eg_r6_r4/primary.jsonl:6` — Raw contract/coverage result; gold-question primary and actual-question secondary are distinct.
- pr_eg_r6_r4: `artifacts/pr_eg_r6_r4/secondary.jsonl:1` — Raw contract/coverage result; gold-question primary and actual-question secondary are distinct.
- pr_eg_r6_r4: `artifacts/pr_eg_r6_r4/secondary.jsonl:2` — Raw contract/coverage result; gold-question primary and actual-question secondary are distinct.

R2 empty source propositions with a question interpretation are observed omissions; wrong-source vs wrong-question causality needs the available-source snapshot. R4 primary uses gold question meanings and secondary actual meanings: they cannot be pooled. Vocabulary/role mismatch can deterministically reject a valid paraphrase in named_coverage; it is a mechanism, not a claim that every historical UNKNOWN had that cause. Historical raw evidence does not establish all requested false-DIRECT/provenance categories; unobserved categories remain unverified.
