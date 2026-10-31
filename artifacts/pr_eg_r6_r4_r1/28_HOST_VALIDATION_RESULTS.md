# 28 — Host Validation Results

```json
{
  "B": {
    "extraction_calls": 30,
    "sources": 31,
    "proposed_facts": 47,
    "levels": {
      "STRUCTURALLY_VALID": 47
    },
    "reasons": {},
    "reference_diagnostics": {
      "gold_role_values": 80,
      "role_value_coverage": 64,
      "exact_role_name_agreement": 30,
      "gold_qualifier_phrases": 28,
      "qualifier_phrase_coverage": 20,
      "semantic_precision": null,
      "semantic_recall": null,
      "reason": "Sparse pre-authored claims, open relation names and unreviewed extra facts prevent defensible entailment precision/recall."
    }
  },
  "C": {
    "extraction_calls": 30,
    "sources": 31,
    "proposed_facts": 48,
    "levels": {
      "SOURCE_ANCHORED": 39,
      "REJECTED": 9
    },
    "reasons": {
      "argument_anchor_mismatch": 7,
      "scope_anchor_mismatch": 1,
      "evidence_span_mismatch": 1
    },
    "reference_diagnostics": {
      "gold_role_values": 80,
      "role_value_coverage": 64,
      "exact_role_name_agreement": 30,
      "gold_qualifier_phrases": 28,
      "qualifier_phrase_coverage": 20,
      "semantic_precision": null,
      "semantic_recall": null,
      "reason": "Sparse pre-authored claims, open relation names and unreviewed extra facts prevent defensible entailment precision/recall."
    }
  }
}
```

Structural validity, anchoring and semantic support are different axes. C accepted anchor level never exceeds SOURCE_ANCHORED. A role swap passes anchors; reported-speech extraction can lose its content link. Every semantic claim still needs trusted support, even when source identity and spans are mechanically valid. Per-fact reasons reside in extractions/. Candidate gate counts are in summary.json, and do not authorize delivery.
