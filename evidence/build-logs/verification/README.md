# Reproduce the build-log evidence gains

With the pinned Go toolchain installed for `./tools/go` (see [development setup](../../../docs/DEVELOPMENT.md)), Python 3.10+, curl and patch, run from the repository root:

```sh
python3 tools/verify_log_gains.py --fetch
```

The fetch flag downloads missing archives from the public URLs in the three case manifests. Cached inputs permit offline replay. The verifier checks source and input hashes, rebuilds current Go, applies the supplied reverse patch to a temporary source copy, checks its hash against the previous freeze, and builds previous Go with an overlay. It runs both binaries and the same Python script on all ten logs. An independently implemented scorer checks excerpt text against original line bytes and reconstructs the cited lines, missed groups and extra lines before comparing to the saved receipts. A mismatch stops the run. Expected output is in [totals.json](totals.json).

| Set | Previous Go found / extra | Current Go found / extra | Python found / extra |
|---|---:|---:|---:|
| Eight development logs, 31 labeled groups | 19 / 57 | 31 / 76 | 7 / 43 |
| Two additional logs, four labeled groups | 2 / 13 | 3 / 13 | 2 / 13 |

An extra line is a distinct returned line outside that question's evidence labels. On the development logs the independently rebuilt versions reproduce the earlier gain of 12 groups for 19 additional extra lines.

For the new replay we froze the rules and selected every remaining run in the historical index with observed JUnit failures after excluding both previous sets. Two URLs qualified. Hashes also establish that all ten logs have distinct contents. The projects and failure formats overlap earlier work. Questions and annotations were set from the source logs before running the tools.

* **Kubernetes node swap.** Current Go recovered the rejected NodeSwap feature gate at lines 208 and 239. Previous Go and Python missed it. All three returned ten extra lines and correctly reported two ambiguous literal matches. This repeats an already-observed failure pattern on a different run.
* **kOps volume expansion.** All three returned the failed spec and its source location with three extra lines. All missed the terminal diagnostic at line 2887, five lines before the summary header. The diagnostic reports a deadline exceeded while fetching the PV during resize. Current Go answered one of the two questions completely; the other tools answered neither.

These checks verify replay and arithmetic. Relevance labels have not received independent human review. No model calls or token measurements were made. [Frozen selection](freeze.json) · [Input hashes, queries and evidence lines](cases.json) · [Current receipts](results.json) · [Previous receipts](previous.json).
