# TestReceipts release notes

## Unreleased

- Add an installable TestReceipts agent skill with command selection, capture reuse and explicit evidence limits.
- Expose `log_context` through the existing MCP stdio profile, using the shared CLI extraction implementation and scoped file access. Improve argument descriptions for comparison tools.
- Add an offline quickstart with expected outputs and refresh agent handoff instructions.
- All six native targets pass updated package, MCP and offline quickstart checks. Qualification now requires quickstart evidence. Package tests exercise log search with empty PATH, Unicode filenames and partial/missing input.
- Official MCP Python SDK 1.30.0 passes 20 local parity cases and three invalid-input checks. Agent-app behavior and skill activation remain unmeasured. No additional token savings have been measured.

## 0.4.0 — 2026-11-12

Unsigned proof of concept. The CLI and local packager now use the plain version `0.4.0`, following the `v0.4.0-dev.1` source build. This minor version adds a CLI command alongside the existing CI report comparison commands.

- Search an archived step log with `testreceipts log-context [--partial] FILE LITERAL`. JSON output cites physical lines, includes related diagnostics, and marks ambiguity, missing input and incomplete coverage.
- Follow Go and Ginkgo failure summaries, assertion values, compiler errors, command stderr, suite counts and interrupted-operation timeouts. Each excerpt can be checked against the supplied log.
- On 20 development logs, Go recovered 54/54 labeled evidence groups with 171 extra lines. The unchanged Python script recovered 14/54 with 104 extra lines. The last update recovered three facts on two logs for five additional extra lines over the preceding Go version. The final rules were tuned on all 20 logs. Agent tokens were not measured for log search. [Results and replay](evidence/build-logs/README.md)
- The separate report-comparison study measured first-use token savings of 41.53% against parser assembly and 27.23% against a ready-made query. Those figures include one Python fallback. [Study](evidence/go-url-first/README.md)

## v0.3.0-dev.1

Earlier unsigned development candidate with local report comparison, public Prow/GCS capture, offline replay and an optional MCP interface. [Candidate evidence](evidence/g04-release/README.md)
