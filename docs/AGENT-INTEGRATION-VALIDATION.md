# Agent integration validation

Local validation on 2026-11-23 covers the installable skill, shared log extractor, MCP log search and offline examples. Changes are Unreleased. Native results for older versions remain historical evidence.

| Check | Result |
|---|---|
| Skill structure | Bundled skill-creator validator passes. PyYAML was installed into ignored `.artifacts/skill-validator` solely for this check. |
| Offline quickstart | Both documented examples pass, including exact log citations at lines 11 and 13. |
| MCP wire parity | 16 comparison fixtures and four log searches match CLI output. Log source paths use the resolved absolute path. |
| MCP boundaries | Invalid arguments, missing files, traversal, symlink escape, oversized-line handling, partial input and session budget covered by Go tests. |
| Reference contracts | Frozen hashes, 20 Python reference tests and 15 Go comparison contracts pass. |
| Go race suite and vet | Pass. The HTTP tests required local loopback permission outside the sandbox. |
| 20-log replay | Exact equality with saved teardown receipts. Go 54/54 groups with 171 extra lines. Python 14/54 with 104. |

Reproduce from this checkout with the pinned Go toolchain

```sh
./tools/go build -trimpath -buildvcs=false -o bin/testreceipts ./cmd/testreceipts
./tools/go test -race ./...
./tools/go vet ./...
python3 tools/verify.py --go-binary bin/testreceipts
python3 tools/check_quickstart.py --binary bin/testreceipts
python3 tools/check_mcp.py --binary bin/testreceipts --out .artifacts/agent-integration-mcp
python3 tools/replay_source_errors.py bin/testreceipts --all > .artifacts/agent-integration-replay.json
```

The last command requires the existing hash-pinned archived datasets in ignored storage. Compare its JSON with `evidence/build-logs/teardown/results.json`. The extractor moved from the CLI package into `internal/logcontext` so MCP and CLI share its implementation. The same queries, labels and Python comparator were retained. All twenty archived logs remain development evidence.

The native CI harness now runs the offline examples and expanded MCP parity suite. Updated native macOS, Linux and Windows runs remain pending. Third-party host integration, automatic skill discovery, repeated-use gains and new token savings remain unmeasured. No model calls were made.

## Prepared discovery cases

These are intended outcomes for a future authorized agent evaluation. They have not been run against a model.

| Request | Expected behavior |
|---|---|
| Compare these two supported public Prow run URLs | Select live comparison, or reuse a supplied capture containing both runs. |
| Compare these runs using this saved TestReceipts capture | Select offline comparison. |
| Find context for “failed to restore temporary ACL” in this local log | Select literal log search and report both matches. |
| This truncated log has no matches | Preserve partial coverage and avoid claiming the build passed. |
| Why did this build fail? (no artifact or diagnostic supplied) | Obtain the missing evidence before selecting a command. |
| Compare two GitHub Actions URLs | Explain the current live provider scope and work with available local logs or supported artifacts. |
| Refactor this application function | Leave TestReceipts unused. |

A future evaluation should record activation, selected operation, argument validity, evidence accuracy, calls and total tokens. Successful executable examples alone do not establish agent routing quality.
