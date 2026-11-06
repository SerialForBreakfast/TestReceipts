# What moved into this starter

This is a copy for a new project, not a destructive migration. The original research and all Spotlight code remain in Spotlightning. The starter has no runtime imports from that repository.

| Original work | What is carried here | New destination |
|---|---|---|
| EXP09 structured test-result tools | Bounded parser, batch reader, independent oracle and exact comparison | G01 parser/recorded comparison |
| EXP09-12 artifact-discovery correction | Content-based XML discovery and 13 regression tests, including generic Ginkgo filenames | G01/G03 discovery |
| EXP09-15 URL-entry comparison | Recorded provider, inventory/query helpers, seven integration tests, compact metrics and chart | G01 parity; G03 live provider |
| ADR-014 portability discussion | Go decision, alternatives, size/runtime cautions and platform targets | ADR-001; G02 deployment |
| Repeated and recurring investigation lessons | Strong baselines, caching fairness and setup-versus-reuse distinction | G04 evaluation plan |
| Human-readable evidence requirement | Exact fixture inputs/outputs, expected results, chart/report rules | EVALUATION.md and all milestones |

Not copied: Spotlight/MCP Swift implementation, Foundation Models experiments, large real CI recordings, raw agent traces, native binaries, toolchains, model-run credentials or automatic paid-evaluation launchers. The original acquisition and agent experiment scripts are deliberately not shipped as a production connector. Their historical bundles can be obtained separately using the optional archive identifiers.

The first G01 task extends the small fixture suite before porting. It does not restart the historical search for a token-saving workload. The current opportunity is a convenient, correct portable CI comparison tool; its lasting advantage over a reusable script remains an open question.
