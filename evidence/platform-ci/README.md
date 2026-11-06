# Native CI evidence

The six-target workflow is configured; actual runner results will be recorded here after execution. No new Linux/Windows native pass is inferred from local configuration.

Local checks: actionlint v1.7.12 accepted the workflow, all six existing executable headers match target metadata, the reference source/fixture checks pass with explicit UTF-8 workers, and the qualification aggregator rejects empty/partial/duplicate/foreign/failed inventories. A local macOS arm64 preflight exercises the harness against the previous private package; it is not a hosted CI result or a clean-machine test.

See [CI scope and limitations](../../docs/NATIVE-CI.md). Downloaded packages/captures/logs stay ignored; compact actual run provenance and native statuses will be retained in Git. Full clean-machine/minimum-OS/trust-flow checks remain open even if hosted native jobs pass.
