# G02 packaging and native qualification evidence

Final candidate: `v0.1.0-dev.1`, clean source `404dc82`, generated locally in ignored `dist/g02-release/`.

See [G02 validation](../../docs/G02-VALIDATION.md) for the platform matrix and [release instructions](../../docs/RELEASING.md) for repeatable commands.

- `release-manifest.json`: final candidate's six targets, exact build inputs/provenance, byte hashes, two-build reproducibility and logical/compressed sizes.
- `SHA256SUMS.json`: final package/manifest hashes; archives remain ignored under `dist/`.
- `executable-inspection.json`: executable format, CPU and imported system libraries, inspected without foreign execution.
- `checks.txt` and `negative-controls.json`: Go/reference checks, packaging boundary tests and altered package/extra-file detection.
- [availability.json](availability.json): local runner limitations.
- [native-macos-arm64/result.json](native-macos-arm64/result.json): actual extracted-package checks and measurements. The sibling JSON files retain all 15 exact comparison outputs.

Build-only targets remain native-unverified. Native checks on this development host do not count as clean-machine qualification. No model calls, external release uploads, or agent value studies are involved.
