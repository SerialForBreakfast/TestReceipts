# G03 HTTP-enabled release qualification

Private candidate `v0.2.0-dev.1`, clean source `646211db653731b2caef68beca65a56c6de24a1a`. Packages remain ignored under `dist/g03-release/`; no public release occurred.

- `release-manifest.json` and `SHA256SUMS.json`: six repeated build/archive hashes, exact production-source/toolchain/asset provenance and logical/compressed sizes.
- `executable-inspection.json`: actual target headers and system-library imports; foreign binaries were inspected, not executed.
- `native-macos-arm64/result.json`: installed package, all 15 comparisons, empty-PATH, version, permissions, output and resource checks.
- `checks.json` and `negative-controls.json`: package verification, wrong-byte/extra-file detection and final qualification summary.

The exact extracted macOS package also performed the [real HTTPS capture and offline replay](../g03/real-capture-audit.json). Real report identity warnings remain explicit. All other native targets, clean machines, minimum OS versions, certificate-store behavior on other platforms and public signing/distribution remain unvalidated; see [G03 validation](../../docs/G03-VALIDATION.md).
