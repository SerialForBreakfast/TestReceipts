# TestReceipts implementation handoff

Updated 2026-11-06 after G03 live implementation. This is the standalone Go CI comparison tool, separate from Spotlightning.

## Current state

Git is initialized on `main`; the original handoff is preserved in initial commit `4f9e15e`. The product, executable, and local Go module are named TestReceipts / `testreceipts`. A SHA-256-verified Go 1.27.3 toolchain is installed in ignored `.cache/toolchain`; `./tools/go` selects it and keeps caches local.

G01 implements `testreceipts compare-recording RECORDING BEFORE_URL AFTER_URL` with no Python subprocess or live HTTP. The standard-library Go core classifies bounded XML, counts observed records, groups exact diagnostics, validates recorded discovery and original bytes, preserves uncertainty, and compares two snapshots. Original reports remain in the recording for full inspection.

The frozen Python comparator remains under `reference/`, with original hashes unchanged. The development runner now uses Python `-S` to exclude optional system XML libraries; see contract version 1.1 for the discovered environment dependency. Fifteen small fixture pairs agree with Python and an independent DOM checker. The original nine expected outputs were preserved.

Read [G01 validation](docs/G01-VALIDATION.md) for current checks and [the original scaffold validation](VALIDATION.md) for historical build-only evidence. Per-case Python and Go outputs and operation measurements live in [evidence/g01](evidence/g01/README.md).

G02-01 is complete: G02 adds reproducible six-target private candidate packaging, checksums, build provenance and a native package smoke driver. See [G02 validation](docs/G02-VALIDATION.md) for the exact completed checks and remaining native/clean-machine gaps, and [release instructions](docs/RELEASING.md) to recreate packages. The latest MIT-licensed candidate `v0.1.0-dev.2` was built from clean source `c3d37e0`; see [updated package evidence](evidence/g02-mit/README.md). The earlier `dev.1` evidence remains historical. G02-02/03 remain partially validated/pending; no public release has occurred.

G03 adds `compare-live NEW_CAPTURE BEFORE_URL AFTER_URL`, with bounded public Prow/GCS requests, immutable captures, generation/size/checksum verification and explicit incomplete discovery. It invokes the same recording comparison; offline replay still performs no HTTP. The real capture and two independent parser comparisons retain identity warnings. See [G03 validation](docs/G03-VALIDATION.md) and [usage/limits](docs/G03-LIVE.md). G03 is complete for the supported public scope. HTTP-enabled `v0.2.0-dev.1` packages were built reproducibly from clean source `646211d`; the native macOS package performed the real capture and replay audit. See [current release evidence](evidence/g03-release/README.md). Prior G02 package results describe earlier local-only binaries; other native OS/certificate/clean-machine checks remain open.

The README is deliberately terse; build/test details are in [development](docs/DEVELOPMENT.md), installation in [install instructions](release/INSTALL.md), and MCP setup in [MCP profile](docs/MCP.md). G04-01 is complete for the pinned legacy 2025-11-25 profile. It adds a scoped stdio adapter over the same core with exact CLI parity and measured protocol overhead. The `v0.3.0-dev.1` candidate was built reproducibly from clean source `3665338`; see [package/native/live evidence](evidence/g04-release/README.md). The [evaluation protocol](docs/STUDY-PLAN.md) is only a draft; no model trials are authorized or run.

Native CI is configured for all six targets; see [workflow scope/results](docs/NATIVE-CI.md). Configured jobs are not native passes until their source/artifact-matched reports are retained.

## Continue here

1. Run `./tools/go test ./...`, build using the README, then `python3 tools/verify.py --go-binary bin/testreceipts`.
2. Follow [Tasks.md](Tasks.md), continuing G02 native/clean-machine qualification, and qualify the optional MCP profile on intended hosts. G03 is complete; repeat packaging/network qualification after provider changes. Model study execution remains a separate explicit task.
3. Preserve unsupported/unresolved states, observed-record semantics, and exact diagnostic text. Matching diagnostics do not prove a common root cause.
4. Update task completion evidence. Keep fixtures small and retain reference hashes. Never regenerate golden outputs to conceal disagreements.

## Not yet delivered

There is no system installer, public release, publisher signing/notarization, or native Windows/Linux validation. The optional MCP stdio boundary now exists; modern-protocol and third-party-host interoperability remain unverified. Git origin is now https://github.com/SerialForBreakfast/TestReceipts.git (private). The first-party license is [MIT](LICENSE); the hosted module path remains open before publication. The target matrix remains macOS/Linux/Windows × amd64/arm64; cross-builds and native execution must be reported separately.

The complete comparable production workload has not been benchmarked, and no Go size/speed advantage is claimed. No model calls are needed or authorized for these development checks. Agent evaluation is a later explicit task; preserve the historical baseline caveats in [evaluation](docs/EVALUATION.md).

## Relocation

Copy the source checkout, including tracked dotfiles and fixtures. Exclude caches, toolchains, binaries and downloaded data. Install Go on the development host; deployed binaries do not require it. The local command was verified in a directory containing spaces and Unicode, outside the checkout and with an empty executable PATH. No original repository or network is required for recorded comparison.
