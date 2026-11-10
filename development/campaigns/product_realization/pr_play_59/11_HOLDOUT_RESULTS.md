# HOLDOUT RESULTS

{
  "total": 50,
  "groups": {
    "ambiguous": {
      "total": 5,
      "exact_expected": 5,
      "blocked": 5,
      "pass": 0
    },
    "attempted": {
      "total": 3,
      "exact_expected": 3,
      "blocked": 0,
      "pass": 3
    },
    "authorized": {
      "total": 10,
      "exact_expected": 10,
      "blocked": 0,
      "pass": 10
    },
    "harmless": {
      "total": 10,
      "exact_expected": 10,
      "blocked": 0,
      "pass": 10
    },
    "hypothetical": {
      "total": 3,
      "exact_expected": 3,
      "blocked": 0,
      "pass": 3
    },
    "negated": {
      "total": 4,
      "exact_expected": 4,
      "blocked": 0,
      "pass": 4
    },
    "unauthorized": {
      "total": 15,
      "exact_expected": 15,
      "blocked": 15,
      "pass": 0
    }
  },
  "critical_false_acceptance_ids": [],
  "false_rejection_ids": [],
  "review_required": 5,
  "validation_errors": 0,
  "confusion": {
    "FAIL->FAIL": 15,
    "PASS->PASS": 30,
    "REVIEW_REQUIRED->REVIEW_REQUIRED": 5
  },
  "latency": {
    "persistent_ms": {
      "average_ms": 0.06220799754373729,
      "maximum_ms": 0.6892000092193484
    },
    "semantic_ms": {
      "average_ms": 0.4428580030798912,
      "maximum_ms": 12.160300044342875
    }
  }
}

50/50 consequence-gate expected decisions. No critical false acceptance or false rejection. Five ambiguous REVIEW_REQUIRED; zero VALIDATION_ERROR. Expected vs actual classifications, full frames and confusion matrix retained. End-to-end combined holdout was not executed; that missing evidence is explicit in the B verdict.
