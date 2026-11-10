# PR-PLAY-72 — 21 LATENCY

```json
{
  "http_ms": {
    "mean": 1623.9246027705829,
    "median": 1338.2852000067942,
    "maximum": 4556.402100017294
  },
  "natural_chat_ms": {
    "mean": 1722.3823899927083,
    "median": 1321.3822499965318,
    "maximum": 3841.715899994597
  },
  "structured_choice_ms": {
    "mean": 1743.7603499856777,
    "median": 1743.7603499856777,
    "maximum": 2284.6143000060692
  },
  "instrumented_function_ms": {
    "interpretation_ms": {
      "mean": 15.049,
      "median": 0.6285000000000001,
      "maximum": 81.308
    },
    "resolver_ms": {
      "mean": 163.27992857142857,
      "median": 100.34,
      "maximum": 508.78
    },
    "atomic_write_ms": {
      "mean": 162.68833333333333,
      "median": 117.89750000000001,
      "maximum": 897.678
    },
    "publication_ms": {
      "mean": 0.45056250000000003,
      "median": 0.053,
      "maximum": 2.563
    }
  }
}
```

Individual request timings are retained in http_traces.json. Lifecycle aggregates compare different actions and are not equivalent-action speed claims. Same-action comparison is separately labelled if available. Diagnostic middleware and evidence capture add overhead. Function timing sums are observations, not exact disjoint A–F intervals. Submission-to-interpretation offsets, exact persistence-to-publication gap, browser rendering and total browser-visible latency were not instrumented. No browser-visible number is inferred from HTTP time.
