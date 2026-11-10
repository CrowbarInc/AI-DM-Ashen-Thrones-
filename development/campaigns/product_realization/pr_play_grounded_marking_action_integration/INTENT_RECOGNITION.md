# Intent Recognition

`recognize_marking` accepts a bounded sentence: optional "I" or "we", optional "try" or "attempt to", optional manner (`secretly`, `quietly`, `carefully`, `in secret`), then copy, write, jot, scribble, mark, or inscribe, then content onto/on/into a target, with an optional using/with medium. An alternate form is `use MEDIUM to VERB content onto target`. Scratch, engrave, carve, etch, and `into` are recognized and marked destructive.

Purpose tails beginning with so, because, to remember, or to forget are stripped from the extracted phrases. Trailing periods are stripped. The proposal keeps the utterance, verb, preparation, target phrase, content phrase, and medium phrase. Those phrases are not evidence that the named things exist.

The recognizer returns None for questions, delegated writing (`tell/ask/order/have someone write`), remember, recall, mental note, and fighting stance. `I write down what happened` has no onto/on/into target, so it is not a marking action. `I mark the location on my map` is recognized and then fails target resolution when no map is established.

No provider call is used to classify the action.
