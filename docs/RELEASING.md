# Reproducible TestReceipts development packages

G02 prepares private candidates; it does not publish a release. The current version label is `v0.2.0-dev.1`. First-party code is MIT licensed, selected by the maintainer on 2026-11-06. A hosted module/repository path, broader native qualification and publisher signing remain open. The root LICENSE is included in every package.

## Build and verify

Use Go 1.27.3 and Python 3.10+ on the build host. Python and Go are development tools only and are excluded from executable packages. The project-local Go copy is selected automatically; pass `--go /absolute/path/to/go` elsewhere. A dirty source tree is recorded, not hidden; a distribution candidate should be built from a clean source commit.

```sh
python3 tools/release.py build --version v0.2.0-dev.1 --out dist/my-candidate --verify-repro
python3 tools/release.py verify dist/my-candidate
python3 tools/test_release.py
```

The output directory must not already exist. The compatibility entry point `./tools/go run ./tools/build.go` takes the same arguments. Builds refuse a toolchain version mismatch, unexpected external module inventory, non-prerelease version labels, existing output directories, and divergent repeated binaries/archives. The pipeline works offline with the standard library; automatic toolchain/module downloads are disabled.

The six targets are macOS, Linux and Windows × amd64/arm64. macOS/Linux archives use tar.gz; Windows uses zip. Every package contains exactly the executable, BUILD.json, INSTALL.md, NOTICE.txt, LICENSE and GO-LICENSE.txt. No Python, fixtures, expected outputs, caches, toolchain, credentials or datasets are included. The Go runtime/standard library license is retained. Root SHA256SUMS.json covers the six archives and release-manifest.json; this detects corruption against the manifest, not authenticity against an attacker able to rewrite both. No publisher signature is provided.

## Declared reproducibility envelope

Each target is built twice from identical source bytes staged in different temporary source directories, using the same pinned compiler, host, packaging environment and shared Go build cache. `-trimpath`, `-buildvcs=false`, stripped symbols, empty linker build ID, CGO=0, amd64 v1, arm64 v8.0, a fixed version stamp and controlled Go environment prevent host build options from leaking into output. There is no variable build date.

Archives use sorted entries, fixed modes and owners, epoch timestamps (gzip/tar 0, ZIP 1980), no gzip filename, fixed compression and no links. BUILD.json records revision/dirty state, source/asset/packager/compiler hashes, Go build information, target, settings, Python/zlib versions and executable bytes/hash. The outer manifest records both repeated hashes and compressed, executable and full installed package sizes.

This checks byte reproducibility under the declared environment. It does not prove independently bootstrapped compilers, separate cold caches, different host operating systems, different Python/zlib releases or future Go versions produce identical bytes. A code, asset, version, provenance or packaging-environment change may legitimately change package hashes. Preserve the final manifest and identify the exact source commit.

## Native package qualification

The [native CI workflow](NATIVE-CI.md) now validates all six target pairs, live capture/replay, and minimal Linux userlands on both architectures. The [actual results](../evidence/platform-ci/README.md) retain scope and gaps; a green run does not imply full clean-machine or oldest-OS qualification.


Run the smoke driver on a matching native OS/architecture. It extracts the package, preserves executable modes, copies the development recordings to a temporary location with spaces/Unicode, and launches the executable with an empty PATH. The driver itself uses Python, but the installed executable cannot look up Go/Python/Node through PATH.

```sh
python3 tools/smoke_release.py --package dist/my-candidate/testreceipts-v0.2.0-dev.1-darwin-arm64.tar.gz --out evidence/g02/native-macos-arm64 --measure
```

For other hosts replace the archive and output path. Windows packages end in `.zip`. Omit `--measure` outside macOS; its `/usr/bin/time -l` probe may need process/resource access. The driver refuses to execute a foreign target. All 15 real comparisons must match goldens. It checks version, stderr and exit codes, output files, POSIX execute/read permissions and output-write errors where applicable. Windows ACL/read-only directory tests remain manual work.

An empty PATH on a development host is not a clean-machine installation. Repeat on fresh native runners with no language tools installed, covering the oldest intended OS, unpacking, sample comparison, installation/removal and OS permission behavior. Keep fixtures outside release packages and retain each native result. Neither cross-building nor emulation satisfies native hardware coverage.

## Platform requirements and signing

The [Go minimum-requirements page](https://go.dev/wiki/MinimumRequirements), checked 2026-11-06, states Go 1.27 needs macOS 13+, Linux kernel 3.2+, or Windows 10+/Server 2016+. These are upstream floors, not tested TestReceipts minima. Both CPU targets use baseline microarchitectures. The compare-recording command does not use certificates or HTTP. The compare-live command requires HTTPS egress and OS trust roots; consult the G03 live validation. Every new platform must qualify its certificate/network behavior separately.

macOS binaries use the Go linker's ad hoc signature and Apple system libraries; they have no Developer ID identity or notarization. Download quarantine/Gatekeeper behavior is unverified. Windows packages have no Authenticode signing; SmartScreen and fresh-machine behavior are unverified. Linux packages have no detached publisher signature or package-manager installation. Do not bypass host security prompts automatically. Signing or notarization would change artifact bytes and needs a separate post-signing checksum/reproducibility policy.

## Public-release checklist

- MIT first-party license selected; preserve LICENSE and all distinct third-party notices.
- Private source repository is SerialForBreakfast/TestReceipts. The CLI uses local module `testreceipts`; choose/migrate a hosted module path before publishing a reusable Go library.
- Pass repeated builds and archive verification from the intended clean source revision.
- Retain all six target manifests, executable inspections, sizes and native results.
- Native six-target CI passes; complete full clean-machine/oldest-OS/trust-flow checks and keep missing coverage explicitly unverified.
- Decide publisher signing/notarization per platform and verify resulting packages.
- Follow package INSTALL.md to install, compare a sample and uninstall.
- Review version, source provenance, package allowlist and notices, then obtain explicit publication authorization. No upload, tag, release or remote change is automatic.
