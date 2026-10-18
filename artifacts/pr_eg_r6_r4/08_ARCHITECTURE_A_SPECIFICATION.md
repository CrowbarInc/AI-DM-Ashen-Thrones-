# 08 — Architecture A Specification

Unchanged production `_invoke_provider` prompt/schema and `semantic_correspondence.coverage`. The primary adapter supplies gold question propositions and uses provider source interpretations. It calls coverage separately for each gold subquestion. Shared aggregation retains bindings across authorized sources and marks conflict PARTIAL. This differs from production selection, which clarifies on multiple direct sources. Thus it measures correspondence, not end-to-end production behavior.

No tuning of the production baseline occurred. Strict clean_proposition normalization adds binary compatibility slots; it does not change predicate/roles. A receives the same eligible prose as C, at most two sources in core cases. A is not compared against the earlier whole-conversation acceptance percentages; those measure a different responsibility.
