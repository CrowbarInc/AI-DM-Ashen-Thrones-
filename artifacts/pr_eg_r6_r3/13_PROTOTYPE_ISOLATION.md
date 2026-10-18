# 13 — Prototype Isolation

B and C are `experiments/pr_eg_r6_r3/architecture_b.py` and `architecture_c.py`. A calls production `_invoke_provider` and `authorize_information_turn` on an in-memory fixture. No production module was edited. Canonical world files, disclosure policy, final-response sealing, and session persistence were not changed. Restricted topics stay on the NPC with `disclosure: secret` and are omitted from provider context by the same `_topic_rows` filter A already uses.
