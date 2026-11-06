# CI Evidence tasks

This is the execution ledger for the new repository. States: Planned → Ready → In progress → Validating → Done. A testable deliverable and linked evidence are required for Done. Owners are roles, not assigned people. Do not confuse the working Python reference with a completed Go product.

## G00 — Portable handoff

**Outcome:** A movable folder with reference code, fixtures, expected outputs, readable findings and Go build scaffolding. **Status:** Done for handoff preparation. **Evidence:** [Validation](VALIDATION.md), [provenance](docs/source-provenance.json). No Git repository, remote, production connector or new chat was created.

## G01 — Correct local Go comparison

**Outcome:** A Go executable compares two recorded runs and preserves the reference facts and uncertainty. **Dependencies:** G00. **Status:** Ready to start. **Plan:** [G01](docs/plans/G01-parser-and-comparison.md). **Excluded:** live HTTP, MCP, agent studies and speed claims.

### G01-01 — Lock the contract and add missing vectors

- **Status:** Ready. **Owner:** Go engineer / evaluation lead. **Dependencies:** G00.
- **Deliverable:** Review the existing nine expected outputs, reference tests and exact signature rules; add small vectors for Unicode added diagnostics, 512-code-point truncation, suite-level errors, retries and canonical JSON edge cases.
- **Acceptance:** Existing reference tests pass without editing copied reference files. New vectors agree with the runtime and independent checker, or discrepancies are documented as bugs before implementation proceeds. Inputs and expected outputs stay reviewable.
- **Context:** [Porting contract](docs/PORTING-CONTRACT.md), [G01](docs/plans/G01-parser-and-comparison.md). **Evidence:** Pending.

### G01-02 — Port bounded XML classification and facts

- **Status:** Planned. **Owner:** Go engineer. **Dependencies:** G01-01.
- **Deliverable:** Go packages for format classification, testcase/diagnostic facts, identity warnings and exact signatures, using streaming XML where suitable.
- **Acceptance:** Preserve state precedence, original-record counts, entity rejection, unsupported states, warnings and exact text. Reject budgets before unbounded allocations. Go tests cover all named edge cases and compare checked-in expected facts. No Python subprocesses.
- **Context:** [G01](docs/plans/G01-parser-and-comparison.md). **Evidence:** Pending.

### G01-03 — Port recorded discovery, inventories and comparison

- **Status:** Planned. **Owner:** Go engineer. **Dependencies:** G01-02.
- **Deliverable:** `compare-recording RECORDING BEFORE_URL AFTER_URL`; recorded pagination, hashes, inventory accounting and exact diagnostic changes.
- **Acceptance:** `tools/verify.py --go-binary ...` passes every included pair. Cache reuse cannot bypass source validation. Paths stay within the supplied recording. Missing data is explicit; empty evidence is not success. Non-JSON diagnostics go to stderr; failures have nonzero exits.
- **Context:** [G01](docs/plans/G01-parser-and-comparison.md). **Evidence:** Pending.

### G01-04 — Audit Go parity and make the results inspectable

- **Status:** Planned. **Owner:** Evaluation lead. **Dependencies:** G01-03.
- **Deliverable:** Side-by-side inputs, Python outputs and Go outputs, with per-case pass/fail, warnings, runtime and memory measurements.
- **Acceptance:** Repeat from a relocated checkout without the original repo or network. Deliberately altered inputs/expected outputs are detected. Record all failures and no agent-token claims. Reference and Go performance are compared on the same complete local operation.
- **Context:** [G01](docs/plans/G01-parser-and-comparison.md), [evaluation](docs/EVALUATION.md). **Evidence:** Pending.

## G02 — Portable executable deployment

**Outcome:** Users can run the completed local comparison without installing a language runtime. **Dependencies:** G01. **Status:** Planned. **Plan:** [G02](docs/plans/G02-portable-deployment.md).

### G02-01 — Reproducible builds and dependency accounting

- **Status:** Planned. **Owner:** Release engineer. **Dependencies:** G01-04.
- **Deliverable:** Pinned supported Go toolchain, six target binaries, checksums and dependency/build metadata using the supplied build helper as a starting point.
- **Acceptance:** Repeated builds under the same declared environment have explained reproducibility results. Record compressed and installed sizes for the completed tool, not only scaffold sizes. No Python, fixtures, caches, secrets or large datasets in release packages.
- **Context:** [G02](docs/plans/G02-portable-deployment.md). **Evidence:** Pending.

### G02-02 — Native clean-machine smoke tests

- **Status:** Planned. **Owner:** Release/test engineer. **Dependencies:** G02-01.
- **Deliverable:** macOS/Linux/Windows tests, with amd64/arm64 coverage explicitly identified.
- **Acceptance:** Install and run actual comparisons without Go or Python installed; paths with spaces/Unicode, permissions, stderr, exits and output files behave correctly. Record OS minimums, runtime libraries and certificates. Build-only targets remain unverified, not passed.
- **Context:** [G02](docs/plans/G02-portable-deployment.md). **Evidence:** Pending.

### G02-03 — Prepare distribution documentation

- **Status:** Planned. **Owner:** Maintainer. **Dependencies:** G02-02.
- **Deliverable:** Final module/repository name, chosen first-party license, notices, install/uninstall instructions, release checklist and signing/notarization decision per platform.
- **Acceptance:** A reviewer can follow installation and reproduce a sample comparison. License and attribution files accompany relevant dependencies. Publishing is a separate action; no automatic release.
- **Context:** [G02](docs/plans/G02-portable-deployment.md). **Evidence:** Pending.

## G03 — Live provider support

**Outcome:** Two supported live CI URLs produce the same bounded evidence contract. **Dependencies:** G01; packaging validation repeated after HTTP is added. **Status:** Planned. **Plan:** [G03](docs/plans/G03-live-provider.md).

### G03-01 — Implement the first live provider

- **Status:** Planned. **Owner:** Go engineer. **Dependencies:** G01-04.
- **Deliverable:** Read-only public Prow/GCS adapter with documented URL forms, bounded pagination, generation-pinned fetches, timeouts, retries and explicit unavailable states.
- **Acceptance:** Local HTTP-server tests cover pages, cycles, rate limits, redirects, integrity mismatch, oversized content and missing reports. Arbitrary URL fetching and out-of-scope redirects are rejected. Network failure never becomes “no failures.” Live access is tested separately from replay.
- **Context:** [G03](docs/plans/G03-live-provider.md). **Evidence:** Pending.

### G03-02 — Validate live capture and recovery

- **Status:** Planned. **Owner:** Evaluation lead. **Dependencies:** G03-01.
- **Deliverable:** A bounded real-run capture with exact inputs/outputs and a repeatable offline replay; report bytes, requests, time and errors.
- **Acceptance:** Inventories account for every discovered XML object, including generic Ginkgo names. Include partial availability and recovery controls. Full completed-binary size and platform checks are rerun. No token-saving claim from local timing.
- **Context:** [G03](docs/plans/G03-live-provider.md). **Evidence:** Pending.

## G04 — Agent integration and repeated-use value

**Outcome:** Determine whether the tool helps beyond a reusable URL script. **Dependencies:** G03. **Status:** Deferred. **Plan:** [G04](docs/plans/G04-agent-value.md).

### G04-01 — Optional MCP boundary

- **Status:** Deferred. **Owner:** Integration engineer. **Dependencies:** G03-02 and explicit prioritization.
- **Deliverable:** A thin MCP wrapper around the same Go core, with validated arguments, bounded output and exact evidence references.
- **Acceptance:** Same inputs yield the same facts as the CLI; record protocol overhead separately. No duplicate parser or model-generated summaries. Keep the CLI usable independently.
- **Context:** [G04](docs/plans/G04-agent-value.md). **Evidence:** Pending.

### G04-02 — Repeated-use agent comparison

- **Status:** Deferred; no model execution authorized by this handoff. **Owner:** Evaluation lead. **Dependencies:** Working interface and frozen study plan.
- **Deliverable:** A proposed comparison retaining capable parser and ready-query baselines plus a reusable URL-wrapper baseline, with first-use and repeated-use conditions separated.
- **Acceptance:** Freeze questions, source selection, correctness rubric and total-token accounting before execution. Keep failed runs, cached/uncached inputs, retries, tool overhead, follow-up reads and auditable charts. Record human review. Do not tune on held-out outcomes or assume the historical 24.36% saving transfers.
- **Context:** [G04](docs/plans/G04-agent-value.md), [evaluation](docs/EVALUATION.md). **Evidence:** Pending.
