# 07 — Host-Owned Adoption Integration

Adopted and rejected lines share the R2C record. `speech_adoption` remains `AUTHORIZED_HOST_SPEECH`. On adoption, `expression_adoption` is `ADOPTED_GENERATED_EXPRESSION` and the sealed text is the candidate. On rejection, `expression_adoption` is `HOST_FALLBACK` and the sealed text is the host sentence. The candidate, reasons, contract, and provider usage stay on the turn’s `expression_generation` audit. They do not become a second delivered history.

`record_delivered_exchange` receives the sealed text. The repaired qualification check compared that retained sentence with the player-facing sentence on every turn. Rejected candidates do not appear in delivered history, and they are not written back into authorized propositions. A later turn’s contract is built from resolver output and retained host speech, not from a discarded candidate.

Narration drafts that still differ from the sealed line remain `UNAUTHORIZED_GENERATED_CANDIDATE` in the adoption record. Expression does not grant those drafts a delivery path.
