# PR-EG-R6-R3 evaluation contract

This file is hashed before the official provider run. Labels live in `corpus.py` and are not taken from model output.

## Success

- Correction success requires the intended correction, the labeled referent, the labeled resulting roles and qualifiers, host acceptance, and no false clarification.
- Follow-up success requires the labeled follow-up relationship, referent, preserved roles, host acceptance, and no false clarification.
- Referent success uses the labeled target. New questions are outside that denominator.
- Speaker, recipient, courier, debtor, creditor, and the other protected role names must match by name. Other filled slots match by value, so calling the casks an item or an object is the same binding.
- An extra time or place mention counts when the label did not require one, as long as the words are in the utterance. A required qualifier must match.
- The name of the missing slot is reported separately and is not required for correction, follow-up, or answer success.
- A parsed description that fails a witness check is a host rejection, not a malformed structured output. Malformed means the provider output did not parse.
- Genuine ambiguity succeeds when the response class is clarification. A safe clarification on a clear referent is a false clarification.
- Security failure is a restricted source string outside the player utterance, a restricted string in authorized answer text, or acceptance of a forbidden target id.
- Architecture C selection accuracy includes only cases whose exact labeled candidate was generated. Missing candidates are reported separately and are not counted as selection successes.

## Decision rule

Recommend an architecture only if the frozen holdout shows a paired net gain of at least 8 cases on correction success, follow-up success, or referent binding versus the current planner; the validation partition moves the same way by at least 5; no core holdout metric loses more than 3; restricted leaks are zero; and the result does not depend on a keyword classifier. Otherwise recommend further discovery.

## Architectures

A asks the production planner for a full operation and proposition. B asks for a delta description and the host copies unchanged roles. C asks the model to select a candidate built only from referent structure. B does not read the free-text meaning field. C does not repair an unknown candidate id.
