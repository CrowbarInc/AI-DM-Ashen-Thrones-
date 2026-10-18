# 11 — Experimental Conditions

Configured model `gpt-4.1-mini`; provider returned model IDs are retained per call. Temperature 0, max output 1800, production timeout from config, one logical call per A/C case; B uses zero. Both provider clients retain their SDK retry defaults; there is no harness repair/retry loop. All official primary calls returned without transport exceptions.

Inputs/labels are byte-frozen before provider exposure. Same gold questions, world prose, NPC ownership and permissions. Differences: B/C authored facts, A production prompt versus C bounded prompt/schema, deterministic ambiguity bit consumed only by B/C, shared aggregation versus native production selection. The eight ambiguity cases are excluded from ranking after discovering this mismatch; no strong architectural verdict is made. Corpus has 22 templates with eight lexical variants, rather than 176 independent natural conversations.
