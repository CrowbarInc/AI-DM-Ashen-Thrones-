# 18 — Disclosure Authorization

Secret topics are omitted from the provider payload. A source id that is not in that payload is dropped. Across the candidate-mode pilot, the 150 fresh turns, and the 60 planner turns, player-facing text never contained `gray-lantern`. Historical delivered speech is not re-sent to the candidate model. Controlled tests cover a direct secret, a paraphrased secret id, and a secret planted only in delivered speech.
