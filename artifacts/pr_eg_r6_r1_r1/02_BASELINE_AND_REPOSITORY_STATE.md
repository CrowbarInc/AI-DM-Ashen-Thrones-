# 02 BASELINE AND REPOSITORY STATE

Preserved R6-R1 evidence remains in `artifacts/pr_eg_r6_r1`. Before this cycle edited production code, the same selection was rerun from the current tree into `reproduction_junit.xml`. All 44 preserved new identities failed again. 24 preserved inherited identities did not fail in a clean process. Their preserved messages are expression-audit `None` or missing `expression_generation`, which is what `expression_generation_disabled()` returns when provider calls are disabled. This cycle did not treat those as fixed disclosure defects.

Two inherited failures still reproduce with the same messages: `answer_sufficiency` is absent on a source-denied authority record built without an NPC, and the preseal test still expects `initial_generation` where the host now seals `authorized_host_speech`.
