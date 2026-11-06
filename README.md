# TestReceipts

Compare two CI runs: changed failures, exact diagnostics, and the reports behind them. Portable Go CLI with JSON output, public Kubernetes Prow/GCS capture, and offline replay. No Python, Node or compiler at runtime. [MIT licensed](LICENSE).

**[Install and uninstall](release/INSTALL.md)** · [Build from source](docs/DEVELOPMENT.md) · [Live usage and limits](docs/G03-LIVE.md)

## Example

Investigate a CI regression: capture the runs, compare diagnostics, and replay the evidence offline:

```sh
JOB=https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/ci-aws-ebs-csi-driver-e2e-functional
BEFORE_URL=$JOB/2116467111751585792
AFTER_URL=$JOB/2116739156053856256
testreceipts compare-live ./.artifacts/example-capture "$BEFORE_URL" "$AFTER_URL" > comparison.json
testreceipts compare-recording ./.artifacts/example-capture "$BEFORE_URL" "$AFTER_URL" > replay.json
```

Use your Prow URLs; the capture directory must be new. Our [real-run example](evidence/g03/comparison.json) found one new and one disappeared exact diagnostic across 105 testcase records per run. Both reports had ambiguous identities, so `comparisonComplete` stayed **false**. Missing or unsupported evidence never means a passing CI suite.

## Measured status

| Check | Observed result |
|---|---|
| Correctness | 20 reference tests; 15/15 fixture comparisons and 17/17 MCP/CLI comparisons pass |
| Real capture | 2 runs, 4 requests, 1.85 MB response bodies; exact offline replay |
| Packaging | 6/6 targets reproduce byte for byte; native runtime checked on macOS arm64 only |
| macOS arm64 package | 2.83 MB archive; 6.83 MB executable (`v0.3.0-dev.1`) |

See [real-capture evidence](docs/G03-VALIDATION.md) and [current package/MCP checks](evidence/g04-release/README.md). No speed or token-saving advantage is claimed. Private candidates; other native platforms, clean installs and signing remain unvalidated. [MCP setup](docs/MCP.md) · [Remaining tasks](Tasks.md).
