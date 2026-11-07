# TestReceipts

**Spend fewer agent tokens figuring out what changed between two CI runs.** TestReceipts turns two public Kubernetes Prow/GCS run URLs into a structured comparison: new and disappeared exact failure diagnostics, source reports, and explicit gaps in coverage. Your agent can investigate the changes without assembling its own report-discovery, download and comparison workflow. TestReceipts itself makes no model calls.

**Measured first-use token savings with the Go workflow:**

| Compared with | Fewer agent tokens (median paired savings) |
|---|---:|
| Agent-written comparison using an existing parser | **41.53%** |
| An existing ready-made comparison query | **27.23%** |

Across **12 run pairs from eight projects and 72 investigations**, all automated required-fact and inventory checks passed. **23/24 Go-assigned attempts ran the Go comparison; one used the permitted Python fallback, whose cost is included.** These are total input + output tokens, including cached input, **not dollar-cost savings**. [Results, per-case metrics and limitations](evidence/go-url-first/README.md).

**When this helps:** an agent starts with two unfamiliar CI run URLs and needs to identify changed failures and inspect the supporting evidence. The measured benefit is first-use discovery and setup. An already integrated, reusable comparison script may leave less to save; larger reports alone did not consistently improve savings.

**Measurement scope:** `gpt-6-astra` investigated captured provider responses in fresh workspaces. Both baselines were rerun with the current Go workflow. The historical Python results were 42.63% and 24.36%; the figures above are the new measurements. Savings varied by case, and one pair used 12.51% more tokens than the ready query. **Repeated use and live-network performance remain unmeasured.** Human narrative review is pending; additional model trials are deferred.

The current tool is an unsigned Go PoC with JSON output, live capture and offline replay. No Python, Node or compiler is needed at runtime. [MIT licensed](LICENSE). [Tested-platform support](docs/SUPPORT.md).

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
| Packaging | 6/6 reproducible builds and native CI targets pass; Linux minimal userlands: 2/2 |
| macOS arm64 package | 2.83 MB archive; 6.83 MB executable (`v0.3.0-dev.1`) |

See [real-capture evidence](docs/G03-VALIDATION.md) and [native CI results](evidence/platform-ci/README.md). Go speed remains unmeasured; first-use agent-token results are scoped above. Unsigned PoC; support is limited to the tested platforms. Older OS/full-machine checks, signing, MCP upgrades and additional evaluations are outside the current scope. Repository visibility is the maintainer’s decision. [MCP setup](docs/MCP.md) · [Remaining tasks](Tasks.md).
