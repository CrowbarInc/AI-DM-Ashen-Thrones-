# 21 — Referent Persistence

Referents commit only inside the existing delivery path, after the sealed exchange is recorded. Controlled tests show no commit before adoption, no focus change after a forged id, and a save/load round trip that keeps the corrected topic and the parent id. Every fresh turn's `reload` check passed, including the turns marked for a session reload.
