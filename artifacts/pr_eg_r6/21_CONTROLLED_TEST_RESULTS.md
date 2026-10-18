# 21 — Controlled Test Results

`tests/test_pr_eg_r6_unified_semantic_planning.py` covers T01–T28 with a deterministic proposer, plus the bare-predicate repair and the harbor-word predicate overlap case. The last focused run of that file passed.

The tests do not call the network. They are necessary and not sufficient for the verdict. The fresh-provider section is the production evidence.

Old tests were not edited to raise the pass count. The preseal provenance failure `test_immutable_preseal_preserves_selected_authored_answer_over_ignorance` already failed in the PR-EG-R4-R1 repaired JUnit.
