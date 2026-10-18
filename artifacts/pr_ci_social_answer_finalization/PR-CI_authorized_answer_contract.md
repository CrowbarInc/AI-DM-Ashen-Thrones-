# PR-CI Authorized Answer Contract

When all of the following are true:

- the social resolver succeeds
- the addressed NPC is authorized to speak
- `social.topic_revealed` contains a selected authored topic
- the selected topic is relevant to the player question
- the answer is authorized for disclosure

Then the immutable candidate must preserve that selected authored answer or an equivalent faithful realization.

The provider may not suppress the selected answer by producing:

- ignorance
- evasion
- unrelated authored facts
- wrong-topic answers
- generic nonresolution

Speaker attribution must remain the selected NPC.

The repair preserves this by using `format_authored_knowledge_realization_line` for the resolver-selected topic before immutable sealing.

