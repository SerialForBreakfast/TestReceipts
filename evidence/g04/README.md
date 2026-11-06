# G04 MCP boundary validation

The stdio server wraps the same Go comparison/capture functions as the CLI. [MCP usage and limits](../../docs/MCP.md) pins the supported legacy 2025-11-25 profile. The newer 2026 stateless protocol and third-party host/SDK integration are unverified.

`mcp-audit.json` records an independent Python standard-library wire client's semantic parity with the CLI across 15 original development pairs, the partial-listing vector and the retained real capture. Structured JSON and text JSON agree, and original catalogs are linked. Each case retains CLI/MCP wall time and response bytes separately. The MCP process is already initialized while CLI time includes startup, so these single observations are not a speed or agent-token advantage claim.

`go-tests.txt` and `parity.txt` retain final boundary/race and reference checks. `package-tests.txt` records archive boundary checks. [Refreshed packages/native evidence](../g04-release/README.md) identify the exact optional-MCP binary. The same packaged executable also validated live MCP capture = MCP replay = CLI replay on the two known public runs, with incomplete parser coverage preserved.

No model calls or fresh agent studies were executed. The [study protocol](../../docs/STUDY-PLAN.md) is a draft; source selection, sample count, model/version, budget and human review need a separate explicit evaluation task before it can be frozen or run. Downloaded captures remain ignored.
