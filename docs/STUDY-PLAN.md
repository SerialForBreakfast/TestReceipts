# G04-02 evaluation — first-use replication complete

**Current decision (2026-11-06):** the maintainer authorized “that same test” with Go: one replication of the original 72 investigations using `gpt-6-astra`, low reasoning, the same 12 pairs, three approaches and two repetitions. All approaches are rerun. This supersedes the earlier zero-model-spend deferral for this bounded replication. No additional campaign or paid infrastructure is authorized.

The frozen run is `.artifacts/go-url-first-v1`; `freeze.json` pins the model, installed CLI hash/version, protocol, recordings, runner and attempt limit before execution. The installed CLI is newer than the historical CLI; the change is recorded, never treated as an identical environment. Historical inputs are replication data, never new held-out evidence. No dollar-cost claim is made; accounting uses actual input/output tokens including cached input.

## Completed first-use replication

1. Check full Go/Python output parity on the historical 12 pairs using `tools/check_historical_go.py`. Keep per-case outputs in ignored storage and a compact summary in Git. **Preflight complete: 12/12 equal**, [evidence](../evidence/go-token-preflight/README.md). This cannot establish token savings.
2. Frozen: 72 maximum attempts, 900-second timeout per attempt, 16-tool-call correctness gate, fresh workspaces and historical balanced schedule. No automatic replacement of failed attempts. Raw traces and exact model usage are retained; execution/usage/source-integrity failure stops the run. This is an attempt-limited authorization, not an agreed dollar ceiling.
3. Complete: all 72 attempts executed on the frozen balanced schedule. Required facts and inventories passed in all 72; 23/24 assigned attempts executed the Go comparison. One allowed Python fallback and its full cost remain included. Median paired savings: **41.53% versus parser assembly; 27.23% versus ready query**. [Results, exception, uncertainty and audit](../evidence/go-url-first/README.md). The four-arm repeated-use expansion below is a separate future study.
4. Retain all attempts and costs, score exact facts and completeness, and report paired savings separately for each baseline and usage condition. Do not transfer the old percentages to Go in advance. Human narrative review remains necessary before fully validated public claims.

The first-use replication above is frozen; the broader repeated-use protocol below remains a draft. No VM, paid hosting, MCP upgrade or publication is part of this task. A local model can test that model's workflow, but cannot directly validate the original model's percentages.

## Broader repeated-use draft — not part of the current run

Does the packaged interface reduce total investigation work compared with equally capable reusable alternatives, without losing facts or overstating incomplete evidence?

Retain four arms: (1) capable parser-based custom assembly, with reusable code retained; (2) ready-made query over the same manifests; (3) a prepared URL wrapper accepting both run URLs; (4) TestReceipts through MCP. The same core facts must be accessible in every arm. Do not force raw XML reading, redundant calls, extra downloads or setup repetition onto a baseline.

Separate first use in a fresh environment from repeated investigations with scripts, caches and tool connections already prepared. Apply the same source availability, cached-byte policy, permissions, request budgets and recovery controls to all arms. Measure transport/tool definitions and setup overhead rather than assuming they are free.

## Source and question freeze

Before trials, record exact public URLs, generation-pinned bytes/checksums, availability controls and question text in an immutable evaluation manifest. Select held-out data by a prespecified sampling rule, not observed favorable outcomes. Exclude the 15 development pairs, partial-listing fixture, the two G03 real runs and any historical data already inspected during development from held-out claims.

Stratify by observed failure changes, shared diagnostics, no supported reports and partial availability. Keep within the tool's supported Prow/GCS/JUnit scope. Freeze the proposed sample count and job selection before looking at answers. A human reviewer must adjudicate truth from originals using independent checks; unresolved disagreements stay in the record. No held-out source manifest or sample count is selected by this draft.

Ask every arm the same question: observed testcase counts before/after, exact new/disappeared/shared diagnostic groups and occurrences, inventory/parser uncertainty, and original evidence references. Do not ask for inferred common root causes.

## Scoring and accounting

Primary gates are required-fact correctness and honest completeness. Score each run separately; keep malformed/incomplete cases, failed attempts and recovery costs. Do not discard an arm's failures to improve cost figures. An empty or missing inventory cannot earn a passing-suite conclusion.

For each complete investigation record model input/output, cached and uncached input, tool definitions, every retry, follow-up fetch/read, source bytes, requests and wall time. Preserve raw transcripts in ignored storage and a compact checksum catalog in Git. Record fixed setup costs and repeated-use costs separately. Use paired comparisons within source/question blocks, report distributions and uncertainty alongside raw per-case results, and do not extrapolate the historical 24.36% saving to this product.

## Stop and review gates

1. Reviewer approves source/question manifest, model/version, sample count and explicit budget.
2. Freeze protocol and independent expected facts before model execution.
3. Retain unsuccessful runs and protocol deviations; stop on budget exhaustion or broken source equivalence.
4. Human review checks narratives against original reports and uncertainty before any public claims.

Status: authorized first-use replication complete; 72 records audited and all usage totals cross-checked against separate session counters. Models have stopped. Human narrative review and repeated-use evaluation remain pending. No further trials are authorized.
