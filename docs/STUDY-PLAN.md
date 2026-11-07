# G04-02 archived evaluation draft — deferred

**Current decision:** model evaluation is deferred and is not a PoC release blocker. Do not run hosted or local models, spend tokens, select new evaluation sources or provision infrastructure. The maintainer may choose to revisit this on a local-model machine in a separate explicit task. The draft below is retained for history, not as a current approval request or action plan. See [PoC scope](SUPPORT.md).


This is a reviewable draft, not a frozen or executed study. Parser correctness and deployment testing continue without models. A separate explicit evaluation instruction, exact source manifest, model/version, sample size, token/spend budget and human reviewer are required before model trials.

## Question and arms

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

Status: protocol draft prepared; source selection, budget, human review assignment and model execution are deferred, not active pending tasks. No model calls or fresh agent-token measurements have been run.
