Work in the standalone TestReceipts repository. Read AGENTS.md, HANDOFF.md, Tasks.md, docs/PORTING-CONTRACT.md and docs/G01-VALIDATION.md first.

G01 local Go comparison is complete. Use ./tools/go for the ignored project-local Go 1.27.3 toolchain, or install the pinned version on a fresh checkout. Build bin/testreceipts and run python3 tools/verify.py --go-binary bin/testreceipts before changing behavior.

The reference/ tree is a frozen development comparator: preserve its hashes. Python must never become a production dependency. Unsupported or empty evidence must remain explicit. Implement scoped tranches, retain reviewable inputs/outputs, and update completion evidence. Continue with the task ledger; do not assume live networking, release packaging, native platform compatibility, or MCP are already complete. Do not run model evaluations without explicit authorization or claim a Go size/speed advantage without measuring the complete comparable workload.
