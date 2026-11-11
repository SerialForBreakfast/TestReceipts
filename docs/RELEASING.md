# Unsigned PoC packages

TestReceipts is an MIT-licensed, unsigned PoC supported on the [tested native environments](SUPPORT.md). Native CI passes all six target pairs. Additional VMs/hosting, old-OS qualification, publisher signing, notarization, MCP upgrades and model evaluations are not release requirements. No signing credentials or developer accounts are needed.

The maintainer controls repository visibility and any release publication. Building or committing source does not authorize changing visibility, creating public release tags or publishing assets. This workflow has no automatic publication step.

Record user-visible changes, the source version, measurements and their scope in the [release notes](../CHANGELOG.md) for each new version.

## Build and verify

Use Go 1.27.3 and Python 3.10+ on the build host. These are development tools only; packages do not contain or require them at runtime. The project-local compiler is selected automatically; pass `--go /absolute/path/to/go` elsewhere.

```sh
python3 tools/release.py build --version v0.4.0-dev.1 --out dist/my-poc --verify-repro
python3 tools/release.py verify dist/my-poc
python3 tools/test_release.py
```

Use a new output directory. The compatibility entry point `./tools/go run ./tools/build.go` accepts the same arguments. The builder currently accepts explicit prerelease version labels. It rejects a compiler mismatch, unexpected Go modules, existing output directories and divergent repeated output. No stable/public release is created.

The six targets are macOS/Linux/Windows × amd64/arm64. macOS/Linux use tar.gz; Windows uses zip. Each archive contains only the executable, BUILD.json, INSTALL.md, NOTICE.txt, MIT LICENSE and GO-LICENSE.txt. Fixtures, Python, caches, credentials and toolchains are excluded. SHA256SUMS.json covers packages and release-manifest.json; checksums identify bytes, not publisher authenticity.

## Reproducibility and evidence

Each target is compiled twice from identical bytes staged in separate source directories using the same pinned compiler, host, packaging environment and shared build cache. The pipeline uses `-trimpath`, `-buildvcs=false`, stripped symbols, an empty linker build ID, CGO=0, baseline CPU settings and a fixed version stamp. Archive members, modes, owners, ordering and timestamps are deterministic.

BUILD.json and the outer manifest retain source revision/dirty state, source/asset/compiler/packager hashes, settings, Go build information, Python/zlib versions, sizes and repeated hashes. Reproducibility is verified within that declared environment, not across independently bootstrapped compilers or arbitrary hosts/tool versions.

[Native CI](NATIVE-CI.md) verifies package execution, reference/MCP parity, permissions, HTTPS/replay and checksums on all six target pairs. Both Linux architectures also pass minimal-userland tests without language tools. [Retained results](../evidence/platform-ci/README.md) identify the exact versions and source. Full clean-machine VMs, oldest OS versions and fresh-download trust flows remain unverified and outside the PoC support promise; do not provision machines or spend hosting budget to expand it.

## Unsigned policy and install instructions

Follow [INSTALL.md](../release/INSTALL.md) to extract, run and remove a package. macOS has only the Go linker's ad hoc signature, without Developer ID/notarization. Windows has no Authenticode signature; Linux has no publisher signature. OS security prompts may appear. Do not promise prompt-free installation or automatically bypass OS protections. No publisher-signing work is planned for this PoC.

The live command requires HTTPS access and a working OS trust store. Offline replay requires neither network nor certificates. Unsupported or missing evidence remains explicit. The optional existing legacy MCP profile does not invoke models; upgrades and evaluations are deferred.

## Maintainer-controlled release checklist

- Keep the tested-platform support statement, unsigned label, MIT license and notices with packages.
- Use an identified source revision and retain reproducibility/checksum/native-CI evidence.
- Keep unsupported/unverified environments and incomplete report evidence explicit.
- The CLI keeps local module `testreceipts`; a hosted-library migration is outside scope.
- The maintainer decides if/when the repository becomes public and whether to publish release assets. Agents must not perform those actions without a new explicit instruction.

Historical candidate manifests and bundled instructions remain immutable records of their original builds. This documentation cleanup does not rebuild or relabel old artifacts.
