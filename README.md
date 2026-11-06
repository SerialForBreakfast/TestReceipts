# TestReceipts

Compare two CI runs: what failed, which exact diagnostics appeared or disappeared, and which original reports support the result. A portable Go executable with JSON output, live public Kubernetes Prow/GCS capture, and offline replay. No Python, Node or compiler is needed at runtime. [MIT licensed](LICENSE).

**[Install and uninstall](release/INSTALL.md)** · [Build from source](docs/DEVELOPMENT.md) · [Live usage and limits](docs/G03-LIVE.md)

## Example

A CI job fails again after a change. Capture the two runs, compare their diagnostics, then replay the saved evidence without downloading it again:

```sh
testreceipts compare-live ./.artifacts/example-capture "$BEFORE_URL" "$AFTER_URL" > comparison.json
testreceipts compare-recording ./.artifacts/example-capture "$BEFORE_URL" "$AFTER_URL" > replay.json
```

Set the URLs to supported Prow runs; `./.artifacts/example-capture` must be new. Our [real-run example](evidence/g03/comparison.json) found one new and one disappeared exact diagnostic across 105 testcase records per run. Both reports had ambiguous identities, so `comparisonComplete` stayed **false**. Missing or unsupported evidence never means a passing CI suite.

## Measured status

| Check | Observed result |
|---|---|
| Correctness | 20 reference tests; 15/15 Go/Python/DOM fixture comparisons pass |
| Real capture | 2 runs, 4 requests, 1.85 MB response bodies; exact offline replay |
| Packaging | 6/6 targets reproduce byte for byte; native runtime checked on macOS arm64 only |
| macOS arm64 package | 2.82 MB archive; 6.79 MB executable (`v0.2.0-dev.1`) |

Metrics are [measured development evidence](docs/G03-VALIDATION.md), not speed or token-saving claims. Packages are private candidates; other native platforms, clean machines and publisher signing remain unvalidated. [MCP setup](docs/MCP.md) · [Remaining tasks](Tasks.md).
