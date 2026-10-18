# 07 — Requested Relationship Handling

`parse_relationship` splits `predicate(argument)` into stemmed tokens. The vocabulary is open. `of` is dropped from the predicate. Unknown predicates remain tokens.

Host coverage compares those tokens with the source text. Predicate tokens that merely repeat the argument do not count as extra predicate evidence, so a label such as `harbor_bell_called(harbor_bell)` does not make every harbor sentence a direct answer.

Name-tautology sentences ("is called") are unrelated unless the question is about a name. Cause, source, and "other" predicates require an explicit causal or attribution marker in the source. Ordinary preference and schedule facts do not become explanations.
