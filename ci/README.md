# Native platform qualification

`platforms.json` is the six-target runner matrix. The workflow builds one verified package set, then runs each target's package on matching hosted hardware/OS. Native jobs assert the actual Python/Go host architecture before testing; cross-building never counts as execution.

Every job retains a report, command logs, package hashes, reference/fixture parity, MCP parity, live HTTPS/replay results and install smoke outputs. Linux jobs also run the binary and all 16 small recordings in a pinned minimal Debian container without Go/Python/Node/compilers or network access. This is a container check sharing the native Linux kernel, not a full clean-machine VM claim.

macOS/Windows hosted images include development tools. Empty-PATH package checks are explicit evidence; a full install on an OS without those tools, minimum OS support, downloaded-package trust, signing and third-party MCP host support remain separate. Windows smoke includes deny-read ACL and output-write checks. Skipped Go tests are listed, not passed.

The public Prow live probe is enabled by default and can be disabled on manual dispatch. Disabled, unavailable or failed checks remain marked as such. Live parser warnings do not fail a TLS acquisition probe: reports must be acquired with complete artifact discovery, while `comparisonComplete` can remain false honestly. No models are called.

The runner labels were checked against [GitHub's runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) on 2026-11-06. Repository plan, quotas and runner availability can still prevent execution. Workflows use read-only repository permissions, immutable official action commits and seven-day artifacts. There is no release/tag/deployment step.
