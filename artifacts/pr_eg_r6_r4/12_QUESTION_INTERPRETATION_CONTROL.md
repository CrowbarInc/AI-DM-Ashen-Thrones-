# 12 — Question Interpretation Control

Primary: gold predicates, role names, missing arguments and qualifiers isolate correspondence. Primary provider payloads also expose those gold interpretations; source normalization can benefit from them. Do not extrapolate this performance to unhinted production.

Secondary: 22 fresh unhinted production planner calls on variant -07, one per family, with the gold field removed. Actual request propositions feed all three kernels. A native `authorize_information_turn` result is preserved alongside kernel results. C makes a fresh correspondence call using the actual request. B/C therefore inherit the actual role vocabulary and may fail to align it with authored facts.

| Architecture | Supported answer success | Relevance | Sufficiency | Acceptance errors | Rejections of answerable cases |
|---|---:|---:|---:|---:|---:|
| A | 15/22 (68.2%) | 18/22 (81.8%) | 18/22 (81.8%) | 3 | 2 |
| B | 9/22 (40.9%) | 11/22 (50.0%) | 12/22 (54.5%) | 0 | 10 |
| C | 5/22 (22.7%) | 6/22 (27.3%) | 12/22 (54.5%) | 0 | 10 |


Secondary scores use the original independent labels. A actual query has only one requested role; multipart coverage may be lost. Native and replay outputs are different measures; neither is a 150-turn production qualification.
