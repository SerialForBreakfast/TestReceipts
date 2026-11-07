# TestReceipts

**Help AI assistants investigate failed software tests with fewer tokens.**

When automated tests fail, an AI assistant often has to find the reports, download them, and write code to compare the results. TestReceipts does that work and returns the evidence: **which failure messages appeared, which disappeared, and where they came from**. The assistant can focus on investigating the changes.

**Measured first-use token savings with the Go workflow:**

| Compared with | Median token savings |
|---|---:|
| An assistant building a comparison with an existing parser | **41.53% fewer** |
| An assistant using an existing ready-made comparison query | **27.23% fewer** |

The study covered **72 investigations across 12 run pairs from eight projects**. All automated fact and report-inventory checks passed. **23/24 Go-assigned attempts ran the Go comparison; one chose the permitted Python fallback. Its full cost is included.** These are workflow results, not 24/24 Go-only executions. [Results and limitations](evidence/go-url-first/README.md).

**[Install and uninstall](release/INSTALL.md)** · [Build from source](docs/DEVELOPMENT.md) · [Tested platforms](docs/SUPPORT.md)

## How it works

1. Give TestReceipts two supported CI run URLs, one before and one after a change.
2. It finds and compares the test reports, returning exact changed failure messages, report references, and any missing or uncertain evidence as JSON.
3. Your assistant uses that comparison to investigate what changed. You can save the captured evidence and repeat the comparison offline.

**Use it when:** an assistant starts with unfamiliar run URLs and would otherwise assemble the comparison itself. Current live support covers public Kubernetes Prow/GCS runs with supported JUnit XML reports. TestReceipts makes no model calls and needs no Python, Node or compiler at runtime. It is an unsigned, [MIT-licensed](LICENSE) Go proof of concept.

**Savings vary:** one tested pair used 12.51% more tokens than the ready-made query. **Savings from repeated use or an already-prepared comparison script remain unmeasured.**

<details>
<summary>What the measurements cover</summary>

The same `gpt-6-astra` model setting investigated captured provider responses in fresh workspaces; both baselines were rerun. Tools were already installed. The figures are median paired savings in total input plus output tokens, including cached input—not dollar-cost savings. They do not measure live-network performance, other models or modern MCP integrations. Human narrative review is pending. [Full method, per-case results and audit](evidence/go-url-first/README.md) · [Historical Python results](evidence/README.md).

</details>

## Example: what changed between two failed test runs?

Yesterday's run failed. Today's run also failed. Before asking your assistant to explain why, use TestReceipts to identify the changed failure messages:

```sh
JOB=https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/ci-aws-ebs-csi-driver-e2e-functional
BEFORE_URL=$JOB/2116467111751585792
AFTER_URL=$JOB/2116739156053856256
testreceipts compare-live ./.artifacts/example-capture "$BEFORE_URL" "$AFTER_URL" > comparison.json
```

Our [real-run example](evidence/g03/comparison.json) found **one new and one disappeared exact diagnostic**, across 105 testcase records per run. Both reports had ambiguous test identities, so `comparisonComplete` remained **false**. A disappeared message does not prove a fix; missing reports never mean passing tests.

Use your Prow URLs and a new capture directory. To repeat the comparison without downloading again:

```sh
testreceipts compare-recording ./.artifacts/example-capture "$BEFORE_URL" "$AFTER_URL" > replay.json
```

[Live usage and limits](docs/G03-LIVE.md).

## Measured status

| Check | Observed result |
|---|---|
| Correctness | 20 reference tests; 15/15 fixture comparisons and 17/17 MCP/CLI comparisons pass |
| Real capture | 2 runs, 4 requests, 1.85 MB response bodies; exact offline replay |
| Packaging | 6/6 reproducible builds and native CI targets pass; Linux minimal userlands: 2/2 |
| macOS arm64 package | 2.83 MB archive; 6.83 MB executable (`v0.3.0-dev.1`) |

See [real-capture evidence](docs/G03-VALIDATION.md) and [native CI results](evidence/platform-ci/README.md). Go speed remains unmeasured; first-use agent-token results are scoped above. Unsigned PoC; support is limited to the tested platforms. Older OS/full-machine checks, signing, MCP upgrades and additional evaluations are outside the current scope. Repository visibility is the maintainer’s decision. [MCP setup](docs/MCP.md) · [Remaining tasks](Tasks.md).
