# PR-DK False-Positive Controls

Controls included quoted dialogue, hypothetical actions, negated actions, ordinary compound sentences, single-focus pronouns, combat declarations, movement, harmless social questions, authored factual questions, and conversational follow-ups.

Observed B-policy false-positive pressure:

- Quoted "Walk closer and pry it off" can look like a compound action unless quote spans are removed first.
- Hypothetical "If someone pried..." can look like unsupported object manipulation unless modal/hypothetical framing is honored.
- Negated "I do not pry..." can look like object manipulation unless negation is handled.
- Single-focus "Ask him..." should stay ordinary when discourse has a unique active interlocutor.

The harness removes quoted spans and requires movement plus a second concrete action family for compound detection, but negation and hypothetical framing remain residual risks for production.
