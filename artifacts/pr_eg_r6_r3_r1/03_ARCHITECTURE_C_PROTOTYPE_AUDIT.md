# 03 — Architecture C Prototype Audit

`experiments/pr_eg_r6_r3/architecture_c.py` builds candidates from referent roles, asks the provider to pick one id, and rejects unknown ids. It does not call production bind, disclosure, or final adoption. Reused without importing the experiment harness: host-owned ids, no nearest-candidate repair, witness checks, and an explicit none/clarify choice. Not reused: the experiment's in-memory case shape, its grader, or its direct answer-class assignment.
