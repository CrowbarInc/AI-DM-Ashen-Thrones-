# PR-EG-R6-R4-R1 frozen experiment contract

Only experiment modules and artifacts may change. No production imports this
prototype. No world writes, final emission, provider-selected clue discovery or
automatic canonical promotion. All outputs are offline proposals, including A.
The immutable final delivery boundary remains untouched.

Primary: raw questions, no gold relationships, roles, expected values or labels in
provider inputs. The 34 independently authored families contain 170 pre-labeled
questions. Author labels are independent of provider output, not independently
human adjudicated. Family modulo 3 assigns development/validation/holdout.
All labels, partitions, adapter and scorer code freeze before provider execution.
No tuning is planned. Gold diagnostic runs separately on the first question per
family after primary completion; it must not be pooled with primary results.

A uses the literal current production planner prompt/schema and unchanged
clean_proposition/coverage kernel. It retains the production single-request
representation limit. This is a production-style kernel experiment, not a full
chat/API or final-response test. All arms share source access, model, temperature,
output cap and visible history. A sees prose on each question; B/C see immutable
cached proposals and never re-extract per question. This difference is the tested
architecture, not an oracle. Long context is four inert exchanges for q1/q3;
short context is empty for q0/q2/q4. Report these strata separately.

B/C share extraction prompt/schema and alignment prompt/schema. Separate real
extractions are run for each arm, so sampling variation is a limitation. B checks
schema and host-owned source availability. C additionally enforces exact source
spans, literal role-value anchors, scope anchors, source epistemic/provenance and
fact identity. This is a validator difference, not cosmetic prompt wording.
Neither validator proves semantic entailment. Named role swaps and lost
qualifiers can pass anchoring. C cannot claim SEMANTICALLY_SUPPORTED or
HUMAN_REVIEWED. Both remain delivery_authorized=false. A/B/C acceptance errors
refer only to *candidate predictions*, never delivered gameplay claims.

Scoring is frozen exact normalized answer-value set equality (case, whitespace,
leading articles and terminal period only), exact class, and inclusion of each
required literal qualifier. Provider role names are not gold hints. Relatedness
or safety alone never earns success. False acceptance counts a positive
prediction with unsupported class, extra values or missing required qualifiers;
false rejection counts a negative prediction for answerable evidence. Missing
values in a positive answer are failures too. Source-anchoring is measured
mechanically; extraction semantic precision/recall and named-role equivalence
need adjudication. Exact agreement with annotated claims is only a conservative
diagnostic and must not be relabeled semantic truth.

All calls preserve requests, provider response objects, parsed outputs, usage,
latency and failures. SDK retries disabled. No mocked responses qualify. Only
host-eligible sources reach provider contexts; unavailable sources expose neither
their text nor their IDs. Historical dialogue does not become world evidence.
UNKNOWN is correct for denied evidence in this source-access experiment: no
runtime gold-based restricted-topic classifier is provided to any arm.

Performance includes extraction overhead, runtime alignment, both context strata,
mean/p95 token and latency values, calls, stable extraction hashes and amortized
tokens per question. Dollar prices are not assumed. Human labor is unavailable;
no human minutes or independent adjudication will be fabricated. Frozen labels
may be disputed in a separate review ledger, never edited after exposure.

Stop actual delivery/state operations if any unauthorized content, fabricated
identity/span or unsupported fact could be accepted. Adversarial test proposals
and provider prediction errors are retained for diagnosis; quarantine is not
factual acceptance. If semantic correctness requires an unimplemented trusted
checker, recommend against integration. A/B verdict requires all user criteria;
otherwise C or UNVERIFIED with explicit evidence gaps. Stop this cycle, await
external review, do not begin PR-EH.
