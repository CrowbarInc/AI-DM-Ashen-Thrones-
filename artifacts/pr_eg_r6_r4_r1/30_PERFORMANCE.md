# 30 — Performance

```json
{
  "A": {
    "extract": {
      "calls": 0,
      "successful": 0,
      "input_tokens": {
        "n": 0,
        "total": 0,
        "mean": null,
        "p95": null
      },
      "output_tokens": {
        "n": 0,
        "total": 0,
        "mean": null,
        "p95": null
      },
      "latency_ms": {
        "n": 0,
        "total": 0,
        "mean": null,
        "p95": null
      }
    },
    "results": {
      "calls": 170,
      "successful": 170,
      "input_tokens": {
        "n": 170,
        "total": 410872,
        "mean": 2416.894117647059,
        "p95": 3750
      },
      "output_tokens": {
        "n": 170,
        "total": 39238,
        "mean": 230.81176470588235,
        "p95": 294
      },
      "latency_ms": {
        "n": 170,
        "total": 372477.769,
        "mean": 2191.0457,
        "p95": 3265.077
      }
    },
    "all": {
      "calls": 170,
      "successful": 170,
      "input_tokens": {
        "n": 170,
        "total": 410872,
        "mean": 2416.894117647059,
        "p95": 3750
      },
      "output_tokens": {
        "n": 170,
        "total": 39238,
        "mean": 230.81176470588235,
        "p95": 294
      },
      "latency_ms": {
        "n": 170,
        "total": 372477.769,
        "mean": 2191.0457,
        "p95": 3265.077
      }
    },
    "amortized_tokens_per_question": {
      "input_tokens": 2416.894117647059,
      "output_tokens": 230.81176470588235
    },
    "context": {
      "short": {
        "calls": 102,
        "input_tokens": {
          "n": 102,
          "total": 156490,
          "mean": 1534.2156862745098,
          "p95": 1545
        },
        "output_tokens": {
          "n": 102,
          "total": 23201,
          "mean": 227.4607843137255,
          "p95": 287
        },
        "latency_ms": {
          "n": 102,
          "total": 216106.438,
          "mean": 2118.690568627451,
          "p95": 2775.427
        }
      },
      "long": {
        "calls": 68,
        "input_tokens": {
          "n": 68,
          "total": 254382,
          "mean": 3740.9117647058824,
          "p95": 3752
        },
        "output_tokens": {
          "n": 68,
          "total": 16037,
          "mean": 235.83823529411765,
          "p95": 294
        },
        "latency_ms": {
          "n": 68,
          "total": 156371.331,
          "mean": 2299.5783970588236,
          "p95": 3394.973
        }
      }
    }
  },
  "B": {
    "extract": {
      "calls": 30,
      "successful": 30,
      "input_tokens": {
        "n": 30,
        "total": 11775,
        "mean": 392.5,
        "p95": 397
      },
      "output_tokens": {
        "n": 30,
        "total": 5870,
        "mean": 195.66666666666666,
        "p95": 281
      },
      "latency_ms": {
        "n": 30,
        "total": 66442.077,
        "mean": 2214.7359,
        "p95": 3692.982
      }
    },
    "results": {
      "calls": 170,
      "successful": 170,
      "input_tokens": {
        "n": 170,
        "total": 248792,
        "mean": 1463.4823529411765,
        "p95": 2902
      },
      "output_tokens": {
        "n": 170,
        "total": 15241,
        "mean": 89.65294117647059,
        "p95": 118
      },
      "latency_ms": {
        "n": 170,
        "total": 222247.138,
        "mean": 1307.336105882353,
        "p95": 1616.908
      }
    },
    "all": {
      "calls": 200,
      "successful": 200,
      "input_tokens": {
        "n": 200,
        "total": 260567,
        "mean": 1302.835,
        "p95": 2883
      },
      "output_tokens": {
        "n": 200,
        "total": 21111,
        "mean": 105.555,
        "p95": 235
      },
      "latency_ms": {
        "n": 200,
        "total": 288689.215,
        "mean": 1443.446075,
        "p95": 2392.842
      }
    },
    "amortized_tokens_per_question": {
      "input_tokens": 1532.7470588235294,
      "output_tokens": 124.18235294117648
    },
    "context": {
      "short": {
        "calls": 102,
        "input_tokens": {
          "n": 102,
          "total": 59242,
          "mean": 580.8039215686274,
          "p95": 714
        },
        "output_tokens": {
          "n": 102,
          "total": 8939,
          "mean": 87.63725490196079,
          "p95": 108
        },
        "latency_ms": {
          "n": 102,
          "total": 129689.2,
          "mean": 1271.4627450980392,
          "p95": 1511.359
        }
      },
      "long": {
        "calls": 68,
        "input_tokens": {
          "n": 68,
          "total": 189550,
          "mean": 2787.5,
          "p95": 2921
        },
        "output_tokens": {
          "n": 68,
          "total": 6302,
          "mean": 92.67647058823529,
          "p95": 120
        },
        "latency_ms": {
          "n": 68,
          "total": 92557.938,
          "mean": 1361.1461470588235,
          "p95": 1809.98
        }
      }
    }
  },
  "C": {
    "extract": {
      "calls": 30,
      "successful": 30,
      "input_tokens": {
        "n": 30,
        "total": 11775,
        "mean": 392.5,
        "p95": 397
      },
      "output_tokens": {
        "n": 30,
        "total": 5930,
        "mean": 197.66666666666666,
        "p95": 283
      },
      "latency_ms": {
        "n": 30,
        "total": 78003.097,
        "mean": 2600.1032333333333,
        "p95": 4114.151
      }
    },
    "results": {
      "calls": 170,
      "successful": 170,
      "input_tokens": {
        "n": 170,
        "total": 242307,
        "mean": 1425.335294117647,
        "p95": 2856
      },
      "output_tokens": {
        "n": 170,
        "total": 15205,
        "mean": 89.44117647058823,
        "p95": 119
      },
      "latency_ms": {
        "n": 170,
        "total": 222478.865,
        "mean": 1308.699205882353,
        "p95": 1741.073
      }
    },
    "all": {
      "calls": 200,
      "successful": 200,
      "input_tokens": {
        "n": 200,
        "total": 254082,
        "mean": 1270.41,
        "p95": 2842
      },
      "output_tokens": {
        "n": 200,
        "total": 21135,
        "mean": 105.675,
        "p95": 227
      },
      "latency_ms": {
        "n": 200,
        "total": 300481.962,
        "mean": 1502.40981,
        "p95": 2315.352
      }
    },
    "amortized_tokens_per_question": {
      "input_tokens": 1494.6,
      "output_tokens": 124.32352941176471
    },
    "context": {
      "short": {
        "calls": 102,
        "input_tokens": {
          "n": 102,
          "total": 55351,
          "mean": 542.656862745098,
          "p95": 682
        },
        "output_tokens": {
          "n": 102,
          "total": 8899,
          "mean": 87.24509803921569,
          "p95": 109
        },
        "latency_ms": {
          "n": 102,
          "total": 130876.506,
          "mean": 1283.103,
          "p95": 1710.378
        }
      },
      "long": {
        "calls": 68,
        "input_tokens": {
          "n": 68,
          "total": 186956,
          "mean": 2749.3529411764707,
          "p95": 2892
        },
        "output_tokens": {
          "n": 68,
          "total": 6306,
          "mean": 92.73529411764706,
          "p95": 130
        },
        "latency_ms": {
          "n": 68,
          "total": 91602.359,
          "mean": 1347.0935147058824,
          "p95": 1741.073
        }
      }
    }
  }
}
```

All phases include observed usage and request wall latency; parallel latency sums are not end-user elapsed latency. Mean/p95 use nearest-rank p95 and are separated by short/long contexts. Mean amortized tokens include extraction overhead across all 170 questions; eligible-only denominator is 150 and can be recomputed from raw records. Each B/C family extraction call may contain two conflict sources. Caching reduces re-extraction calls but still requires one alignment call/question. Dollar cost is not claimed because no current or account-specific unit price was verified. For any verified rates Pin/Pout per million, cost=(input_tokens*Pin+output_tokens*Pout)/1e6. No unsupported dollar savings claim or production affordability conclusion.
