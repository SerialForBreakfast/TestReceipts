# G02 — Deploy without a language environment

Task ledger: [G02](../../Tasks.md#g02--portable-executable-deployment).

Use the Go core and CLI from G01. The provided `tools/build.go` uses `CGO_ENABLED=0`, `-trimpath`, `-buildvcs=false`, and stripped symbols to create macOS/Linux/Windows amd64/arm64 binaries with SHA-256 checksums. These choices are starting settings, not a proven final release policy. Keep `go version`, module list, source revision and build settings with each artifact.

Test on native clean runners. A cross-compiled Windows executable is not a tested Windows release. Test the actual report command, not just help. Include paths with spaces and non-ASCII characters, missing files, output redirection and nonzero error exits. Document OS floors and any remaining runtime dependencies. Live HTTP adds certificate and networking behavior that must be retested after G03.

Measure compressed download size, installed size, startup, peak memory and full-operation time. Exclude build caches and development fixtures from release packages. Treat signing/notarization, package-manager recipes and public releases as later distribution work after functionality is proven. Decide the repository name and first-party license before public publication.

The starter builds have no external Go modules. If later MCP or provider code adds modules, retain sums, notices and dependency inventory. Prefer a small maintained library over an unsafe custom XML/TLS implementation solely to claim zero dependencies.
