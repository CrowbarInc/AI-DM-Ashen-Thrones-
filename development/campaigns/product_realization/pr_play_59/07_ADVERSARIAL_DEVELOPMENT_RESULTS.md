# ADVERSARIAL DEVELOPMENT RESULTS

{
  "total": 46,
  "groups": {
    "ambiguous": {
      "total": 3,
      "exact_expected": 3,
      "blocked": 3,
      "pass": 0
    },
    "attempted": {
      "total": 2,
      "exact_expected": 2,
      "blocked": 0,
      "pass": 2
    },
    "authorized": {
      "total": 6,
      "exact_expected": 6,
      "blocked": 0,
      "pass": 6
    },
    "existing": {
      "total": 1,
      "exact_expected": 1,
      "blocked": 0,
      "pass": 1
    },
    "harmless": {
      "total": 10,
      "exact_expected": 10,
      "blocked": 0,
      "pass": 10
    },
    "hypothetical": {
      "total": 2,
      "exact_expected": 2,
      "blocked": 0,
      "pass": 2
    },
    "negated": {
      "total": 2,
      "exact_expected": 2,
      "blocked": 0,
      "pass": 2
    },
    "unauthorized": {
      "total": 20,
      "exact_expected": 20,
      "blocked": 20,
      "pass": 0
    }
  },
  "critical_false_acceptance_ids": [],
  "false_rejection_ids": [],
  "review_required": 3,
  "validation_errors": 0,
  "confusion": {
    "FAIL->FAIL": 20,
    "PASS->PASS": 23,
    "REVIEW_REQUIRED->REVIEW_REQUIRED": 3
  },
  "latency": {
    "persistent_ms": {
      "average_ms": 0.060471740257723824,
      "maximum_ms": 0.693799986038357
    },
    "semantic_ms": {
      "average_ms": 0.3737108642741552,
      "maximum_ms": 8.543799980543554
    }
  }
}

Rows, exact authority and claims: development_results.json. Additional active unfamiliar-entity controls pass in the pytest lane. Early development false positives and prior reason-code regressions were corrected before freeze; pre_freeze logs are retained. Corpus covers the requested state-change categories and wrong-entity/additional-consequence adversaries.
