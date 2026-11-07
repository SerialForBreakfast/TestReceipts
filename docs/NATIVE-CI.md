# Native platform CI

The [workflow](../.github/workflows/native-platforms.yml) runs on pushes, pull requests and manual dispatch in [SerialForBreakfast/TestReceipts](https://github.com/SerialForBreakfast/TestReceipts). It does not publish a release, create tags, deploy, or call models. Repository permissions are read-only; official actions are pinned to [verified commits](../ci/actions-lock.json).

## Verified run

[Run 42300372775](https://github.com/SerialForBreakfast/TestReceipts/actions/runs/42300372775) passed all six native jobs, both minimal Linux userlands, package reproduction and the Linux amd64 race gate on source `54614e1`. See [actual OS versions and remaining gaps](../evidence/platform-ci/README.md). The first failed Windows ACL probe is retained separately. Full clean-machine/minimum-OS/trust-flow scope remains unverified.

## What is checked

A Linux build job creates the six-target package set twice, checks binary/archive equality, and retains checksums and build provenance. Each [native matrix job](../ci/platforms.json) downloads that same package set and verifies:

- Python host, Go host and actual executable header match the target OS/CPU; emulation is not accepted as native qualification.
- All native Go tests and vet, frozen source hashes, 20 reference tests, 15 golden pairs and partial-listing regressions.
- Actual installed package comparisons, spaces/Unicode paths, version, stderr/exits, output files and empty PATH. Windows adds deny-read ACL (temporarily disabling backup/restore bypass privileges and restoring them afterward) and read-only output-handle tests; POSIX checks include execute/read permissions.
- Exact MCP/CLI parity for the fixtures and, when enabled, the live capture. Skipped Go tests are listed explicitly.
- Real public Prow HTTPS capture using the OS trust store, then exact offline replay and independent Python/DOM facts. Artifact discovery must be complete for this probe; parser identity warnings remain explicit and do not become passing CI claims.
- On Linux only: all 16 small recording comparisons in a pinned minimal Debian container with Go/Python/Node/compilers absent, no network, read-only mounts and an unprivileged user. This verifies minimal userland execution on the native kernel, not a full clean-machine VM.

The common race suite runs on supported Linux amd64 with CGO enabled. Race support on every target, especially Windows arm64, is not inferred from that job.

The summary gate requires all six source/artifact-matched native reports and successful package/native/race jobs. Missing, queued, cancelled, skipped or failed jobs cannot count as passed. Failed jobs retain logs and partial reports. Disabled live probes are marked `not_run`, not silently verified.

## Run and inspect

Pushes/PRs enable the public live probe. A manual dispatch can explicitly disable it for an offline-only check:

```sh
gh workflow run native-platforms.yml --repo SerialForBreakfast/TestReceipts -f live_validation=true
gh run list --repo SerialForBreakfast/TestReceipts --workflow native-platforms.yml
gh run view RUN_ID --repo SerialForBreakfast/TestReceipts
gh run download RUN_ID --repo SerialForBreakfast/TestReceipts --name qualification-summary --dir .artifacts/ci-summary
```

Artifacts expire after seven days; they are not a backup. Package artifacts contain only release files. Native evidence contains compact outputs/logs and the bounded downloaded real capture for replay, outside Git. Public source retention or provider/network outages can make a live probe fail; it must not be relabeled as a passing empty inventory. Re-run when available, or explicitly perform an offline-only run and retain its gap.

Git checkout attributes preserve frozen reference/report bytes. Python workers explicitly use UTF-8 even when isolated from environment variables, so Windows code pages and CRLF conversion cannot change the comparator or signature inputs.

## Unverified scope, outside the PoC support promise

The [maintainer-selected PoC scope](SUPPORT.md) accepts existing native CI and requires no additional VMs, paid hosting or publisher signing. Hosted VMs include development tools. Empty PATH checks and Linux minimal containers do not establish full-machine installation with no language tools present. Oldest supported OS versions, fresh browser-download quarantine/Gatekeeper/SmartScreen, publisher signing/notarization, modern MCP and third-party host integration remain unverified and are not PoC release blockers. MCP upgrades and evaluations are deferred. Native coverage applies only to the actual OS versions reported by jobs. The [runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) documents label availability; private-repository plan/quotas may still prevent a job from starting.

See [qualification evidence](../evidence/platform-ci/README.md) for actual executed results. Configuration and local preflight alone are not remote native passes.

Windows ACL tests follow the [AdjustTokenPrivileges restore-state contract](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-adjusttokenprivileges). They deny only file data, leaving ACL read/write control available so a test can undo its own temporary denial. Privilege state is recorded; no privilege is added or permanently changed.
