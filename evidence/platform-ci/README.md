# Native platform CI results — 2026-11-06

[Successful run 42300372775](https://github.com/SerialForBreakfast/TestReceipts/actions/runs/42300372775) validates source `54614e18d531f188d29c02a2d8fbec66a4b27e13`.

| Target | Actual runner OS | Native | Local fixture / MCP cases | Live HTTPS + replay | Minimal userland |
|---|---|---|---|---|---|
| darwin/amd64 | macOS-15.7.9-x86_64-i386-64bit-Mach-O | Pass | 15 / 17 | Pass; parser ambiguity retained | Not tested |
| darwin/arm64 | macOS-15.8.2-arm64-arm-64bit-Mach-O | Pass | 15 / 17 | Pass; parser ambiguity retained | Not tested |
| linux/amd64 | Linux-7.0.0-1017-azure-x86_64-with-glibc2.39 | Pass | 15 / 17 | Pass; parser ambiguity retained | Pass, 16 cases; no language tools |
| linux/arm64 | Linux-7.0.0-1017-azure-aarch64-with-glibc2.39 | Pass | 15 / 17 | Pass; parser ambiguity retained | Pass, 16 cases; no language tools |
| windows/amd64 | Windows-2025Server-10.0.26100-SP0 | Pass | 15 / 17 | Pass; parser ambiguity retained | Not tested |
| windows/arm64 | Windows-11-10.0.26200-SP0 | Pass | 15 / 17 | Pass; parser ambiguity retained | Not tested |

All six packages passed repeated-build checks, native architecture/header verification, native Go tests/vet, 20 reference tests, 15 golden comparisons, MCP parity, permission/output checks and public Prow capture/replay. The separate Linux amd64 race job passed. No Go tests were skipped in this run. Both Linux targets also passed pinned minimal-container checks with no Go/Python/Node/compilers and no network. Containers share the native kernel and do not prove full clean-machine VM installation.

Windows hosted runners had backup and restore privileges enabled. The negative ACL test temporarily disabled/restored those privileges, denied only READ_DATA, verified denied reads return exit 2, and recovered reads after cleanup. The [first failed attempt](first-attempt.json) remains documented; it is not counted as passing.

Real reports still contain `ambiguous_slash_identity` on every target. Native/TLS checks pass while `comparisonComplete` remains false; this is not a passing-CI-suite claim.

Compact evidence: [native results](native-results.json), [fail-closed summary](summary.json), [source/build manifest](release-manifest.json), [package checksums](SHA256SUMS.json). Raw captures/logs/packages are retained locally under ignored `.artifacts/ci-final/` and as seven-day workflow artifacts. They are not a permanent remote backup.

Still unverified: full clean-machine VMs without development tools installed, oldest supported OS versions, fresh browser-download Gatekeeper/SmartScreen flows, publisher signing/notarization, modern MCP and third-party host integration. Hosted test harnesses contain Python/Go; the installed executable runs with empty PATH, and Linux has the separate minimal-userland proof.

Documentation/evidence-only follow-up commits may use `[skip ci]`; this report identifies the exact tested runtime/workflow source and does not imply a new code revision was executed. See [workflow scope](../../docs/NATIVE-CI.md).
