# G03 validation — 2026-11-06

**Current PoC policy:** tested-platform support and existing native CI are sufficient. Signing, new VMs, old-OS/full-machine qualification, MCP upgrades and evaluations are outside scope or deferred, not release blockers. The measurements and unverified claims below remain historical facts; see [current policy](SUPPORT.md).

**Subsequent CI update:** all six native OS/architecture pairs, live HTTPS/replay and two minimal Linux userlands now pass; see [current platform evidence](../evidence/platform-ci/README.md). The version-specific results below remain historical. Full clean-machine, minimum-OS and publisher-trust checks are still open.

The public Prow/GCS adapter and `compare-live` command are implemented using the Go standard library. A live operation retains bounded original HTTP bodies, listings and generation-pinned XML, then invokes the shared recording comparison. Offline replay performs no HTTP. See [usage and contract 1.2](G03-LIVE.md).

## Real capture and exact replay

Two public `ci-aws-ebs-csi-driver-e2e-functional` runs were acquired read-only:

- [2116467111751585792](https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/ci-aws-ebs-csi-driver-e2e-functional/2116467111751585792)
- [2116739156053856256](https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/ci-aws-ebs-csi-driver-e2e-functional/2116739156053856256)

They are from the same job; no consecutive-run claim is made. The capture observed one XML report per run and downloaded 918,777 and 922,902 report bytes. Both runs contain 105 observed testcase records: 91 passed, 13 skipped, one failure. One exact diagnostic disappeared and another appeared. These are recorded facts, not a common-root-cause explanation.

Discovery of the listed XML completed and both reports passed generation, size, MD5 and CRC32C validation. Both parsers retained `ambiguous_slash_identity`, so parser coverage and `comparisonComplete` remain false. These warnings were not removed to claim success. Every listed XML was accounted for; filename filtering does not require “junit,” as exercised by generic-name/uppercase fixtures.

The [network record](../evidence/g03/network.json) reports four HTTP attempts and 1,849,268 consumed response-body bytes, with request and acquisition times separated. Exact live JSON equals offline replay run with an empty PATH and unusable HTTP/HTTPS/ALL proxy settings. The Go facts also match the frozen Python runtime and independent DOM checker after removing only the new acquisition wrapper fields. Full comparison outputs and original response hashes are retained in [the audit](../evidence/g03/real-capture-audit.json).

A copied real report was deliberately altered: replay retained other evidence and marked the affected inventory unresolved. Restoring the original bytes recovered the exact original result. Original downloaded bodies/reports remain under ignored `.artifacts/g03-release-live/`; they are not committed datasets. The audit records exact paths, sizes and SHA-256. A clone needs that separately retained capture, or a new live acquisition, to replay this specific real observation.

## Local failure and correctness tests

The [Go tests](../evidence/g03/go-tests.txt) cover:

- 429 limits, bounded backoff/retries and transient 503 recovery;
- permanent 403/404, failed/malformed later pages, cycles, duplicates and out-of-scope objects;
- request timeout, context cancellation and request/byte/page/object/listing-size limits;
- generation mismatch, changed bytes, declared oversize, MD5/CRC failure, CRC-only objects and missing checksums;
- unsupported content encoding, untrusted TLS and object redirects that never reach the redirect target;
- replay of partial acquisition, retained usable counts, immutable capture directories and recovery into a fresh capture;
- strict supported URL forms and contradictory coverage rejection.

The new checked-in [partial listing fixture](../testdata/live/partial-listing/expected.json) keeps usable report facts while marking missing pagination explicitly. Existing [G01 parity](../evidence/g03/parity.txt) still verifies the 20 reference tests and all 15 original pairs. Frozen reference hashes and original expected outputs are unchanged. The development corrections are documented in [development notes](../evidence/g03/development-notes.md).

## Packaging, native checks and remaining limits

The HTTP-enabled executable requires system TLS roots and HTTPS egress; the real capture exercised the native macOS arm64 trust store. Untrusted-certificate tests reject a local TLS server, and no insecure verification mode is provided. Linux may require a system CA bundle; Windows/macOS use platform trust facilities. A local-only executable's previous package validation is not claimed as validation of this larger HTTP-enabled binary.

The HTTP-enabled private candidate `v0.2.0-dev.1` was built twice from clean source `646211db653731b2caef68beca65a56c6de24a1a`. All six executable and archive hashes agree across source directories. The extracted macOS arm64 package passed all 15 comparisons and native permissions/output/version checks; that exact packaged executable then performed the real HTTPS capture described above. Its live result again equals offline replay and both independent parser facts. See [release evidence](../evidence/g03-release/README.md), [manifest](../evidence/g03-release/release-manifest.json), and [native result](../evidence/g03-release/native-macos-arm64/result.json).

| Target | Executable bytes | Archive bytes | Repeated binary + archive |
|---|---:|---:|---|
| darwin/amd64 | 7,335,552 | 3,068,291 | Pass |
| darwin/arm64 | 6,793,938 | 2,815,664 | Pass |
| linux/amd64 | 7,168,124 | 3,021,320 | Pass |
| linux/arm64 | 6,619,260 | 2,715,268 | Pass |
| windows/amd64 | 7,369,728 | 3,092,092 | Pass |
| windows/arm64 | 6,681,088 | 2,754,115 | Pass |

Logical installed package bytes, source/build/packager hashes and full request/startup/memory measurements are retained in the manifests and native result. The Linux binaries have no ELF interpreter or direct shared-library imports; a system CA bundle is still needed for HTTPS. macOS imports libSystem/libresolv and CoreFoundation/Security through the standard-library TLS implementation; these system dependencies were inspected and exercised on this host. Windows direct imports were inspected without claiming native runtime success. Native Windows/Linux and macOS amd64 execution, clean-machine installs, oldest-OS testing and downloaded-package/publisher-signing flows remain unvalidated. Cross-builds will be reported separately from native execution. No public release or model/agent evaluation is part of G03.

Live listing is an observation of a potentially changing provider, not an atomic snapshot or proof a job has finished uploading. Scope excludes other buckets/providers, private runs, archives, extensionless reports and arbitrary logs. Unsupported XML dialects and identity warnings remain explicit. There is no production cache or resume-in-place; capture again into a new directory to recover. No Go size/speed or token-saving advantage is claimed.
