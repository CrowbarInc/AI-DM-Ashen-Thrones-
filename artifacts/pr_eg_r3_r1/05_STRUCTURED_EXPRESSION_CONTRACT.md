# 05 — Structured Expression Contract

The R3 contract is extended. The public fields now include speaker identity, source identity, proposition id, epistemic posture, answer sufficiency, permitted meaning, prohibited additions, and entity identities. The revision hash covers the permitted meaning, the entities, and the proposition id.

Permitted meaning for a preference explanation is a structured premise, built from an established preference sentence before any candidate exists:

- operation `explain_own_preference`
- preference anchor, such as `evening`
- subject `speaker_experience`
- theme `speaker_preference_ease`
- licensed by `established_preference`
- `external_world` false
- `consequential_commitment` false

The prompt tells the speaker the authorized meaning and allows ordinary grammar. It does not list the candidate, and it does not list "everything" as an authorized fact. Fallback remains the host sentence. Source freshness remains the contract revision. No second knowledge store was added.

A sentence with no preference anchor, such as "The watch wears on me," does not build a characterization contract and does not call the provider.
