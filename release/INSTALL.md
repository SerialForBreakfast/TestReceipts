# TestReceipts unsigned PoC

Repository visibility and any release publication are controlled by the maintainer.
Generate a local PoC package using source docs/RELEASING.md; existing local
packages are under ignored dist/. This install guide does not authorize publishing.
Go/Python are needed only on the build/test host, never to run a copied executable.

Choose the archive matching a tested operating system and CPU architecture. Verify
its SHA-256 against SHA256SUMS.json from the same build. Packages are intentionally
unsigned by a publisher; signing/notarization is not planned for this PoC. OS
security prompts may appear; no prompt-free download/install claim is made.
See LICENSE and BUILD.json before distribution. On macOS use `shasum -a 256`,
on Linux `sha256sum`, or PowerShell `Get-FileHash -Algorithm SHA256` and compare
the archive hash with its SHA256SUMS.json entry.

Extract the archive to a folder you control. On macOS/Linux run
`./testreceipts version` and `./testreceipts help`; on Windows run
`.\testreceipts.exe version` and `.\testreceipts.exe help` in PowerShell.
You may place the executable in a user-owned directory on PATH. No administrator
installation, Go, Python, Node, compiler, or separately installed language runtime
is required. Uninstall by deleting the extracted folder and any executable copy
you placed on PATH. The tool writes JSON to stdout and does not install services.

To compare a local recording:

    testreceipts compare-recording RECORDING BEFORE_URL AFTER_URL > comparison.json

A recording contains catalog.json, saved listing pages and original XML bytes.
The source checkout supplies development examples under testdata/cases/changes;
fixtures are deliberately excluded from the executable package. Run from that
checkout, replacing the executable path with your installed path:

    testreceipts compare-recording testdata/cases/changes https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100 https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200

Successful interpretation returns 0. Invalid command/recording or output failure
returns 2 with an error on stderr. Partial report evidence can return 0 with
artifactComplete=false or parserCoverage.complete=false: inspect both fields.
The compare-recording command never downloads reports and does not use TLS.
To capture two public supported Prow runs, use:

    testreceipts compare-live NEW_CAPTURE BEFORE_URL AFTER_URL > comparison.json

NEW_CAPTURE must not exist. Supported URLs use https://prow.k8s.io/view/gs/
kubernetes-ci-logs/logs/JOB/BUILD or pr-logs/pull/REPOSITORY/PR/JOB/BUILD.
The live command needs HTTPS access to storage.googleapis.com and a working OS
TLS trust store (Linux may need a system CA bundle). It uses public read-only
access with no CI credentials. Unavailable pages/reports remain explicit.
Replay the retained recording with compare-recording, without network access.
Live network acquisition is bounded to five minutes; Ctrl-C cancels acquisition and
preserves an incomplete recording when the process can finish writing.

PoC support is limited to the native CI environments: macOS 15 on Intel/Apple
Silicon, Ubuntu 24.04 hosted Linux on amd64/arm64, Windows Server 2025 amd64 and
Windows 11 arm64, at the actual versions recorded in source docs/SUPPORT.md.
Older OS versions, other distributions/editions and full clean-machine VM installs
are unverified and outside the support promise. No VM/hosting budget is required.

Optional MCP stdio mode:

    testreceipts mcp ROOT

ROOT is an explicit existing workspace/capture directory. A compatible legacy
MCP 2025-11-25 host can call compare_recording and compare_live; the same facts,
coverage warnings and provider limits apply. Use relative paths within ROOT;
new live captures must be direct child directory names. See source docs/MCP.md
for configuration, wire/output limits and compatibility. No model calls are made
by the server. MCP upgrades and all model evaluations are deferred, not PoC release blockers.
MCP 2026 stateless compatibility and third-party clients remain unverified.
