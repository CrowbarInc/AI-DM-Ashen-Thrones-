PR-DV Authoritative Fact Contract

Minimum public facts preserved when already present in resolver output:

- Inspection/observation: visible authored surface text or public discovered clue text.
- NPC conversation: addressed NPC name plus resolver-selected topic text when available.
- Scene transition: confirmed destination and arrival scene summary/location.
- Surface reading: public clue or notice text exposed by the interactable.
- Failure: failed inspections and transitions must not be narrated as success.

Hidden facts remain excluded:
- The repair does not read or emit `hidden_facts`.
- Hidden fact metadata is not used as player text.
- If a failure has no public fact, the fallback is a non-inventive failure line.
