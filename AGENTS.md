# Project working agreement

- This is the standalone CI tool, not Spotlightning. No Swift or Apple-only dependency belongs in its core.
- Read HANDOFF.md and Tasks.md; implement scoped tranches and update completion evidence.
- Python under reference/ is a frozen development comparator, not a production dependency. Preserve its hashes. Document/version any deliberate correction.
- Never infer complete CI coverage from an empty or partial report inventory. Preserve unsupported and unresolved states.
- Keep small development fixtures and expected outputs in Git; ignore downloaded datasets, traces, caches, toolchains and release binaries.
- No model calls are needed for parser correctness or deployment tests. Agent evaluation is a later explicit task.
- Do not claim a Go size/speed advantage until the complete comparable workload is measured.
- State platform build and native runtime checks separately. Keep docs readable and exact inputs/outputs inspectable.
