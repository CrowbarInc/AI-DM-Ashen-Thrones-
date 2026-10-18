# 24 — Failure Attribution

Earliest codes, owner from the pre-registered rules:

- A: F01 provider 44, F08 host 26, F03 provider 23, F02 provider 22, F11 provider 11. Two turns had no failure code.
- B: F03 provider 47, F01 provider 30, F09 provider 12, F06 provider 7. Thirty-four turns had no failure code.
- C: F03 provider 37, F01 provider 25, F05 provider 5, F06 provider 3. Fifty-eight turns had no failure code.

A's host slice is mostly production bind and source rejection. B and C host rejections are witness and anchor failures inside the experimental compilers. The dominant remaining error for B and C is still the provider choosing the wrong role or the wrong move, not a random transport failure. Malformed JSON was 0/132 for each architecture.
