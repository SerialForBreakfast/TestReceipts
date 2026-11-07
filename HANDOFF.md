# TestReceipts PoC handoff

Updated 2026-11-06. TestReceipts is a standalone MIT-licensed, unsigned Go proof of concept, separate from Spotlightning. The [PoC scope and tested platforms](docs/SUPPORT.md) are authoritative.

## Complete for this PoC

- Local comparison, bounded XML parsing, exact diagnostic changes and honest incomplete/unsupported states.
- Public Kubernetes Prow/GCS capture, generation/size/checksum validation and exact offline replay.
- Reproducible packages for macOS/Linux/Windows × amd64/arm64, notices, checksums and install/uninstall documentation.
- All six native targets passed CI run `42300372775` on source `54614e1`, including live HTTPS/replay, reference parity, permissions and MCP parity. Both Linux architectures also passed minimal-userland checks without language tools. [Evidence](evidence/platform-ci/README.md).
- Optional MCP stdio profile pinned to legacy 2025-11-25. It uses the same Go core; newer protocol and third-party host interoperability are not claimed.

The frozen Python comparator and original hashes remain unchanged. Twenty reference tests and 15 Go/Python/DOM fixture comparisons pass; MCP parity covers 17 cases including partial and real captures. The Go runtime does not invoke Python or models. The project-local Go 1.27.3 toolchain and caches are ignored; use `./tools/go` or a native pinned Go installation.

## Maintainer decisions

No paid hosting, new VMs, old-OS support campaign, publisher signing or notarization work. Full clean-machine/minimum-OS/download-trust behavior remains unverified and is outside the PoC support promise, not a blocker. Use the exact tested environments in [SUPPORT.md](docs/SUPPORT.md); do not infer broader compatibility.

Modern MCP/client upgrades remain deferred. The maintainer subsequently authorized one 72-investigation Go first-use replication, now complete: **41.53% fewer tokens versus parser assembly; 27.23% fewer versus a ready query**. All 72 automated fact/inventory checks passed. Go comparisons ran in 23/24 assigned attempts; one permitted Python fallback is included in costs. [Evidence and limits](evidence/go-url-first/README.md). Human narrative review and repeated-use evaluation remain pending. No further model calls, token spending or evaluation infrastructure are authorized; the [broader study draft](docs/STUDY-PLAN.md) is not permission for another campaign.

The maintainer alone decides when to make the repository public and whether to publish release assets. Do not change visibility, create release tags or publish packages without a new explicit instruction. The repository is SerialForBreakfast/TestReceipts; the CLI keeps local module `testreceipts`. No public-library module migration is required for this PoC.

## Continue only within scope

Use [README](README.md), [installation](release/INSTALL.md), [development](docs/DEVELOPMENT.md), [live limits](docs/G03-LIVE.md) and [MCP profile](docs/MCP.md). G00–G03 and the existing G04-01 profile are complete for the agreed PoC scope; [Tasks.md](Tasks.md) distinguishes done work from deferred/out-of-scope work.

Preserve original evidence, exact diagnostics and uncertainty. Empty evidence is never a passing test suite. Keep downloaded captures, traces, toolchains and binaries ignored. No Go size/speed advantage is claimed. The README highlights the measured first-use Go-assigned workflow savings, including its fallback, with both baselines and limitations. Historical Python measurements remain separately preserved in [historical evidence](evidence/README.md). Historical validation reports retain their original, version-specific limitations; the current support policy supersedes their old release-blocking requirements.
