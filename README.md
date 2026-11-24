# TestReceipts

**Help your coding agent investigate failed builds with fewer tokens.**

TestReceipts does the report comparison and log searching locally, then gives your agent exact failure messages, relevant log lines, and source references. It runs as a standalone Go executable and makes no model calls.

- **Use fewer tokens to compare failed runs.** Measured median savings of **27.23% versus a ready-made comparison query** and **41.53% versus assembling a comparison with an existing parser**.
- **Find evidence beyond the test result.** In one archived build, all **91 tests passed**, then teardown timed out. Log search returned both the passing count and the timeout.
- **Give your agent a reusable workflow.** The current source includes an installable skill, CLI commands, and MCP tools for comparison and log search.
- **Check and reuse the evidence.** Results retain source references and uncertainty. Saved captures can be compared again offline.

**[Try it offline](docs/QUICKSTART.md)** · **[Install the agent skill](docs/QUICKSTART.md#let-an-agent-choose-the-command)** · **[Install the executable](release/INSTALL.md)**

## Measured token savings

| Compared with | Median token savings |
|---|---:|
| An assistant building a comparison with an existing parser | **41.53% fewer** |
| An assistant using an existing ready-made comparison query | **27.23% fewer** |

The study covered **72 investigations across 12 run pairs from eight projects**. All automated fact and report-inventory checks passed. **23/24 Go-assigned attempts ran the Go comparison; one chose the permitted Python fallback. Its full cost is included.** The reported savings cover the complete assigned workflows, including that fallback. [Results and limitations](evidence/go-url-first/README.md).

## When to use it

Use **report comparison** when an agent has two CI run URLs and needs to find which failure messages appeared or disappeared. Live support covers public Kubernetes Prow/GCS runs with supported JUnit XML reports. Captures retain the downloaded evidence for offline replay.

Use **log search** when you have a local build log and a known failure message. It finds literal matches and related failure evidence, returning line numbers, source hashes, and explicit gaps. Local logs can come from other projects and CI systems.

TestReceipts needs no Python, Node or compiler at runtime. It is an unsigned, [MIT-licensed](LICENSE) Go proof of concept. [Build from source](docs/DEVELOPMENT.md) · [Tested platforms](docs/SUPPORT.md).

**Savings vary:** one tested pair used 12.51% more tokens than the ready-made query. **Savings from repeated use or an already-prepared comparison script remain unmeasured.**

<details>
<summary>What the measurements cover</summary>

The same `gpt-6-astra` model setting investigated captured provider responses in fresh workspaces; both baselines were rerun. Tools were already installed. The figures are median paired savings in total input plus output tokens, including cached input. Dollar-cost savings were not measured. They do not measure live-network performance, other models or modern MCP integrations. Human narrative review is pending. [Full method, per-case results and audit](evidence/go-url-first/README.md) · [Historical Python results](evidence/README.md).

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

## Find evidence in a failed build log

One archived build reported **91 passing tests and zero failures**, then failed when its teardown command hit a two-hour timeout. The passing count and timeout were 152 lines apart. Given the interrupted-command error, `log-context` returned both pieces of evidence. [Archived case and evidence labels](evidence/build-logs/cross-pass/cases.json).

In **0.4.0**, give `log-context` a local build log and a literal failure message. It returns JSON with the matching line numbers, nearby failure summaries, and supporting evidence such as assertion values, compiler errors, or a timeout for the same operation. Multiple matches, missing files and skipped oversized lines are explicit. For a known partial log, add `--partial` before the filename.

```sh
testreceipts log-context testdata/build-logs/failed.txt 'failed to restore temporary ACL'
```

On **20 archived logs used during development**, we checked whether each tool returned the lines needed to answer one question per log. Extra lines are distinct returned lines outside that question’s evidence labels.

| Tool | Evidence groups found | Extra lines returned |
|---|---:|---:|
| TestReceipts | **54/54** | 171 |
| Reusable Python search script | 14/54 | 104 |

The Go tool found **40 more evidence groups** and returned **67 more extra lines**. All 20 logs informed tuning. The latest agent-integration update reproduced these existing results exactly. Token savings for log search and the new skill remain unmeasured. [Per-log results](evidence/build-logs/teardown/results.json) · [Replay method](evidence/build-logs/README.md) · [Release notes](CHANGELOG.md)

## Use it with your agent

The current source adds an [installable skill](skills/testreceipts/SKILL.md) that tells agents when to compare runs, reuse a capture, or search a local log. The optional MCP interface exposes `compare_live`, `compare_recording`, and `log_context` with described arguments and scoped file access.

Follow the [offline quickstart](docs/QUICKSTART.md) for installation and examples with expected outputs. These integration changes are **Unreleased** and pass native checks on macOS, Linux and Windows, each on amd64 and arm64. The official MCP Python SDK 1.30.0 also passes local interoperability checks. Automatic skill selection and agent-app behavior remain unmeasured. [MCP setup](docs/MCP.md) · [Integration validation](docs/AGENT-INTEGRATION-VALIDATION.md).

## Validation and availability

| Check | Observed result |
|---|---|
| Current source | Go race tests and vet pass; 20 reference tests and 15 fixture comparisons pass |
| Current MCP integration | CLI parity passes on all six native targets; official Python SDK 1.30.0 passes 20 local parity cases and three invalid-input checks |
| Offline quickstart | Both documented examples and exact log citations pass on all six native targets |
| Archived log replay | Existing 20-log evidence receipts reproduced exactly |
| Real capture | Previously validated 2 runs, 4 requests and 1.85 MB of response bodies with exact offline replay |
| Platform qualification | Six native OS/CPU targets, reproducible packages and Linux race checks pass on source `e118af3` |

See [current integration checks](docs/AGENT-INTEGRATION-VALIDATION.md), [real-capture evidence](docs/G03-VALIDATION.md), and [current native CI results](https://github.com/SerialForBreakfast/TestReceipts/actions/runs/45306925614). Support is limited to the tested platforms. Go speed, repeated-use token savings and log-search token savings remain unmeasured. [Release notes](CHANGELOG.md) · [Remaining tasks](Tasks.md).
