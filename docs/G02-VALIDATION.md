# G02 release qualification — 2026-11-06

G02 is partially validated. Six-target reproducible private development packaging is implemented; native checks currently cover macOS arm64 on the existing development host. G02 is not fully Done: clean-machine, other native targets, first-party license, hosted module path and public distribution decisions remain open.

## Build and packaging evidence

The [release pipeline](RELEASING.md) pins Go 1.27.3, CGO=0, baseline amd64/arm64 targets and controlled Go settings. Each candidate is compiled twice in different temporary source directories with a shared build cache, then packaged twice with deterministic archive metadata. Both binary and archive hashes must agree for all six targets. The release manifest records exact source revision/dirty state, compiler/source/asset/packager hashes, Go build info, Python/zlib versions, settings, compressed size, executable size and full package logical bytes.

The development packages contain only the executable and five metadata/license/install files. The Go runtime license is included; no Python, junitparser, reports, fixtures, caches, toolchain, credentials or datasets are packaged. Archive integrity/allowlist checks and negative controls are retained under [evidence/g02](../evidence/g02/README.md). The prior preflight candidate was built from a dirty development tree; the final qualification candidate is identified separately by its recorded source commit.

## Runtime matrix

| Target | Build / repeated byte check | Native execution | Clean machine / oldest OS |
|---|---|---|---|
| macOS arm64 | Available; inspect release evidence | Passed on macOS 27.0 arm64 | Not tested |
| macOS amd64 | Available; inspect release evidence | Not tested; no native Intel runner | Not tested |
| Linux amd64 | Available; inspect release evidence | Not tested; no Linux runner | Not tested |
| Linux arm64 | Available; inspect release evidence | Not tested; Docker engine unavailable | Not tested |
| Windows amd64 | Available; inspect release evidence | Not tested; no Windows runner | Not tested |
| Windows arm64 | Available; inspect release evidence | Not tested; no Windows runner | Not tested |

[Availability probes](../evidence/g02/availability.json) record the unavailable Docker daemon and failed x86 translation probe. Translation would not establish native Intel hardware coverage even if available. No platform is called runtime-passed based on a cross-build or executable header.

## Native macOS arm64 checks

The package was extracted into a temporary installation path containing spaces and Unicode. Its actual executable ran with an empty PATH and matched all 15 checked-in expected comparisons. The driver checked stamped version, stderr/nonzero command errors, missing recording, output-file redirection, missing execute permission, unreadable catalog and unwritable stdout. The package did not install any runtime, service or system-wide file.

The [native result](../evidence/g02/native-macos-arm64/result.json) retains per-case wall time/peak RSS, ten version-command startup measurements, original comparison outputs, system-library inspection and code-signature inspection. Timings include process launch and the optional macOS time wrapper; caches/system load are uncontrolled. They are inspection measurements, not a Go/Python performance advantage claim.

The host already has development tools installed. Empty PATH checks demonstrate that the executable does not look up a language runtime; they do not prove installation on a clean machine without those tools. The source smoke driver needs Python as a test harness; the package does not.

## Requirements and unverified behavior

[Go's upstream minimum requirements](https://go.dev/wiki/MinimumRequirements), checked 2026-11-06, list macOS 13+, Linux kernel 3.2+, Windows 10+/Server 2016+. These are upstream toolchain floors, not tested TestReceipts minimums. Hardware/architecture and OS-specific constraints still apply. The Linux binaries have no ELF interpreter/shared-library imports if confirmed by the retained inspection; macOS uses Apple system libraries. Windows system DLL imports are recorded without asserting they work on an untested OS.

The macOS executable has a Go linker ad hoc signature, no Developer ID identity, and no notarization. Windows has no Authenticode signature; Linux has no publisher signature. Fresh-download quarantine/Gatekeeper/SmartScreen and publisher trust flows are untested. Packages remain private development candidates; no release, tag, upload or remote was created.

The current command is local-only and does not use TLS certificates. G03 must repeat network, certificate, size and packaging qualification. No installed-size/speed advantage is claimed from these builds.

## Remaining work

1. Run the supplied package smoke checks on fresh native runners for all six target pairs, including the oldest intended OS and Windows ACL/output behavior. Retain exact inputs, outputs and host details.
2. Complete clean installation/removal checks without language tools installed and downloaded-package trust behavior.
3. Choose the first-party license and hosted repository/module path. LICENSE-STATUS.txt remains explicit in packages until then.
4. Decide public signing/notarization policy, regenerate post-signing hashes if used, then request explicit publication authorization.
