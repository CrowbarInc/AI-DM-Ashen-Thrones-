# C27 implementation summary

## Subject derivation

`game/contract_adjudication_bridge.py`

- Player-voiced quoted questions, including an unclosed quote, are an addressed social frame.
- Quotes attributed to another speaker are not that frame.
- `resolve_subject_coherence` canonicalizes a direct-world topical subject to `social` when the frame is an addressed ask.
- Direct where-is, where-does-it-lead, and what-does-the-object-say questions are structural. They are not noun lists.
- `select_resolver_family` is unchanged. It still does not read the utterance.

## Semantic input

`game/resolution_contract.py`

- `semantic_input_text` is the full whitespace-normalized utterance.
- Contract construction and `raw_input` use it.
- `construction.provenance_excerpt` keeps a 240-character copy for logs.
- `conversational_subject` is unchanged by the resolution subject.

## Tests

`tests/test_pr_br_continuation27_structural_subject.py` covers the C26 turn replays, D1–D8, H1–H6, L1–L8, M1–M5, U1–U20, the 12-case long-context matrix, 27 length variants, post-contract closure, structured output, and T1–T10.
