# Optional MCP candidate qualification

Private candidate `v0.3.0-dev.1`, built twice from clean source `3665338fd5abd37866d5e39b91c2a9e1723eab0c`. All six binary/archive hashes agree; manifest/checksums identify ignored `dist/g04-release/` packages. The packaged macOS arm64 executable passed all 15 local comparisons and native permissions/output checks. It also passed the [17-case independent stdio parity audit](../g04/mcp-audit.json), a public live capture through MCP, and equality of MCP live, MCP replay and CLI replay. No model calls were made.

- `release-manifest.json`, `SHA256SUMS.json`: exact build/source/asset provenance, sizes and repeated hashes.
- `native-macos-arm64/result.json`: actual installed-package checks and measured resource/startup observations.
- `checks.json`: scope and explicit unvalidated platforms/protocol/client integrations.

The supported MCP profile is legacy 2025-11-25. This is not a claim of current stateless-protocol or third-party-host interoperability. Other native/clean-machine/signing checks remain open, and the evaluation plan is unexecuted. The [real CI use case](../g03/comparison.json) retains ambiguous-identity warnings.
