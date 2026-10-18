# 05 — Answer Relevance

## Question representation

`requested_information` matches the player text in a fixed order: hidden, promise, mystery, relationship, rumor, maker, ownership, surveillance, personal state, opinion, otherwise general. There is no phrase table of answers. The subject phrase is a few content words, used for commitment lookup, not spoken back. Speaking the subject (“about the north road”) failed the captured-failure test that forbids “north road” in a rejected stub.

## Answer selection

`authored_answer_sufficient_for_question` returns false when the topic text is empty or when `topic_supports_requested_information` is false. General and clarification questions remain sufficient when a topic exists. A specific kind requires the topic to match that kind’s support pattern (watch/patrol for surveillance, forged/smith for a maker, and so on).

The same gate is applied in `_match_present_npc_topic_authored_knowledge` and in the nested authored-knowledge candidate filter. Without those, the resolver could refuse the topic and a later realization path could still select it from subject overlap. That was the live “Word is, the street…” leak on a watched-road question.

## Partial knowledge

A topic that supports the request and contains a hedge (`sometimes`, `I have not seen`, `haven't seen`, `as far as`, `not sure`) is posture `partial` and `answer_relation` `partial`. The topic text is the answer. Narration is not determined while a topic is present, so the authored line can still be realized.

## Unknown information

No supporting topic, and the kind is surveillance, maker, ownership, hidden, promise, mystery, relationship, or rumor: narration is determined. The line is “I couldn’t tell you.” or, for withheld, “I couldn’t answer that.” A general question that simply lacks a topic is not determined. It stays on the provider path so existing speaker-repair tests still receive a narration call.

## Relevance evaluation

`dialogue_rejection_reasons` adds `answer_not_relevant` when improvisation is not permitted, the request is specific, the response class is `answer`, and the support pattern is missing. Uncertainty and refusal lines are not marked irrelevant. A related fact is not accepted merely because it is available.

## Live gap

Relevance holds when the turn is a resolved NPC ask with a classified request. The live follow-up “Has anyone been keeping an eye on it after dark?” never became that ask. The player heard an internal sentence. Classification cannot repair a turn that does not enter the social resolver.
