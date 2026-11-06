# TestReceipts implementation handoff

Updated 2026-11-06 during G02. This is the standalone Go CI comparison tool, separate from Spotlightning.

## Current state

Git is initialized on `main`; the original handoff is preserved in initial commit `4f9e15e`. The product, executable, and local Go module are named TestReceipts / `testreceipts`. A SHA-256-verified Go 1.27.3 toolchain is installed in ignored `.cache/toolchain`; `./tools/go` selects it and keeps caches local.

G01 implements `testreceipts compare-recording RECORDING BEFORE_URL AFTER_URL` with no Python subprocess or live HTTP. The standard-library Go core classifies bounded XML, counts observed records, groups exact diagnostics, validates recorded discovery and original bytes, preserves uncertainty, and compares two snapshots. Original reports remain in the recording for full inspection.

The frozen Python comparator remains under `reference/`, with original hashes unchanged. The development runner now uses Python `-S` to exclude optional system XML libraries; see contract version 1.1 for the discovered environment dependency. Fifteen small fixture pairs agree with Python and an independent DOM checker. The original nine expected outputs were preserved.

Read [G01 validation](docs/G01-VALIDATION.md) for current checks and [the original scaffold validation](VALIDATION.md) for historical build-only evidence. Per-case Python and Go outputs and operation measurements live in [evidence/g01](evidence/g01/README.md).

G02 adds reproducible six-target private candidate packaging, checksums, build provenance and a native package smoke driver. See [G02 validation](docs/G02-VALIDATION.md) for the exact completed checks and remaining native/clean-machine gaps, and [release instructions](docs/RELEASING.md) to recreate packages. G02 remains partially validated; no public release has occurred.

## Continue here

1. Run `./tools/go test ./...`, build using the README, then `python3 tools/verify.py --go-binary bin/testreceipts`.
2. Follow [Tasks.md](Tasks.md), continuing G02 native/clean-machine qualification, or prioritize G03 explicitly if live CI access is the next product need. Retest packaging after networking is added.
3. Preserve unsupported/unresolved states, observed-record semantics, and exact diagnostic text. Matching diagnostics do not prove a common root cause.
4. Update task completion evidence. Keep fixtures small and retain reference hashes. Never regenerate golden outputs to conceal disagreements.

## Not yet delivered

There is no live provider, MCP server, installer, public release, signing/notarization, or native Windows/Linux validation. Git has no configured remote. The first-party license and hosted module path remain open before publication. The target matrix remains macOS/Linux/Windows × amd64/arm64; cross-builds and native execution must be reported separately.

The complete comparable production workload has not been benchmarked, and no Go size/speed advantage is claimed. No model calls are needed or authorized for these development checks. Agent evaluation is a later explicit task; preserve the historical baseline caveats in [evaluation](docs/EVALUATION.md).

## Relocation

Copy the source checkout, including tracked dotfiles and fixtures. Exclude caches, toolchains, binaries and downloaded data. Install Go on the development host; deployed binaries do not require it. The local command was verified in a directory containing spaces and Unicode, outside the checkout and with an empty executable PATH. No original repository or network is required for recorded comparison.
