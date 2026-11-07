# Unsigned PoC scope

Maintainer decision, 2026-11-06: TestReceipts is an MIT-licensed, unsigned proof of concept. Existing native CI is sufficient for this PoC. There is no additional VM, hosting, signing or evaluation budget. Repository visibility and any public release are the maintainer's actions.

## Tested platform support

Support is limited to the environments actually exercised by [native CI run 42300372775](https://github.com/SerialForBreakfast/TestReceipts/actions/runs/42300372775), source `54614e1`:

| Target | Tested environment |
|---|---|
| macOS amd64 | macOS 15.7.9, Intel |
| macOS arm64 | macOS 15.8.2, Apple Silicon |
| Linux amd64 | Ubuntu 24.04 hosted image, kernel 7.0.0-1017-azure, glibc 2.39 |
| Linux arm64 | Ubuntu 24.04 ARM hosted image, kernel 7.0.0-1017-azure, glibc 2.39 |
| Windows amd64 | Windows Server 2025, build 26100 |
| Windows arm64 | Windows 11, build 26200 |

Both Linux targets also passed offline comparisons in pinned minimal Debian userlands without language tools installed. Those containers share the tested native kernel. CI images can change; future claims must identify the versions actually recorded by successful jobs.

Older versions, other distributions/editions, full clean-machine VM installs and minimum-OS compatibility are **unverified and outside this PoC's support promise**. They are not release blockers. No additional machines or paid hosting are to be provisioned. Empty-PATH and minimal-container checks retain their precise scope; they do not become full-machine claims. The exact reports remain in [platform evidence](../evidence/platform-ci/README.md).

## Unsigned distribution

Packages include the MIT license, Go runtime notice, build provenance and checksums. There is no publisher signing, notarization, Authenticode or detached publisher signature planned for this PoC. macOS binaries may contain the Go linker's ad hoc signature; that is not a verified publisher identity. OS download/security prompts may appear. Download-trust flows are unverified, and documentation must not promise prompt-free installation or automatically bypass OS protections.

Signing credentials, certificates and developer accounts are not required for the PoC. Checksums identify bytes; they do not establish publisher authenticity.

## Deferred work

- Modern MCP upgrades and third-party client integration: deferred. The existing optional legacy 2025-11-25 stdio profile remains available with its documented limits.
- Model evaluations and token-saving studies: deferred. Do not run local or hosted model trials, spend tokens, select a new evaluation dataset or provision evaluation infrastructure without a new explicit instruction. A local-model machine is a possible later option, not an active task.
- Public-library module-path migration, system installers and package-manager integrations: outside this CLI PoC's scope. The local module remains `testreceipts`.

The maintainer controls making the repository public and authorizing any release publication. Agents must not change repository visibility, publish releases/tags or upload public packages as part of this cleanup. Documentation maintenance and normal source commits do not constitute public release authorization.
