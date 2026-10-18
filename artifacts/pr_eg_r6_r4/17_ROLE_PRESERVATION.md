# 17 — Role Preservation

Core Cala/Brin communication cases retain speaker, recipient, topic and message_content; reversed direction is a related nonanswer. Supplemental tests separate lender/borrower, owner/borrower, guard/protected party, buyer/seller, debtor/creditor, appointer/appointee, predecessor/successor and voucher/beneficiary. Direct and reverse queries are distinct.

Bindings are scored by exact role and value, not a bag of entity names. Missing bindings count as extraction failure. Empty negative-case bindings are not evidence of positive role preservation. Read role subsets in `per_case_results.jsonl` and supplemental results rather than treating all UNKNOWNs as correct role handling.
