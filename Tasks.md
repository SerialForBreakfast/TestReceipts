# TestReceipts tasks

## Current PoC scope — maintainer decision, 2026-11-06

The unsigned MIT PoC is complete on the [tested platforms](docs/SUPPORT.md). Existing native CI is sufficient. No additional VMs, paid hosting, old-version campaign, signing or notarization work is required. Full-machine/minimum-OS/download-trust claims remain unverified, not silently passed. Modern MCP/client upgrades remain deferred. One subsequently authorized 72-investigation first-use Go replication is complete; additional model calls, repeated-use trials, token spending and evaluation infrastructure remain deferred. Repository visibility and any public release are controlled by the maintainer.

Earlier acceptance requirements below are narrowed explicitly for this PoC; historical evidence is preserved. Optional/deferred work is not a release blocker.


This is the execution ledger for the new repository. States: Planned → Ready → In progress → Validating → Done. A testable deliverable and linked evidence are required for Done. Owners are roles, not assigned people. Do not confuse the working Python reference with a completed Go product.

## G00 — Portable handoff

**Outcome:** A movable folder with reference code, fixtures, expected outputs, readable findings and Go build scaffolding. **Status:** Done for handoff preparation. **Evidence:** [Validation](VALIDATION.md), [provenance](docs/source-provenance.json). At handoff time no Git repository, remote, production connector or new chat was created. Git is now initialized locally; see [G01 validation](docs/G01-VALIDATION.md).

## G01 — Correct local Go comparison

**Outcome:** A Go executable compares two recorded runs and preserves the reference facts and uncertainty. **Dependencies:** G00. **Status:** Done. **Plan:** [G01](docs/plans/G01-parser-and-comparison.md). **Excluded:** live HTTP, MCP, agent studies and speed claims.

### G01-01 — Lock the contract and add missing vectors

- **Status:** Done. **Owner:** Go engineer / evaluation lead. **Dependencies:** G00.
- **Deliverable:** Review the existing nine expected outputs, reference tests and exact signature rules; add small vectors for Unicode added diagnostics, 512-code-point truncation, suite-level errors, retries and canonical JSON edge cases.
- **Acceptance:** Existing reference tests pass without editing copied reference files. New vectors agree with the runtime and independent checker, or discrepancies are documented as bugs before implementation proceeds. Inputs and expected outputs stay reviewable.
- **Context:** [Porting contract](docs/PORTING-CONTRACT.md), [G01](docs/plans/G01-parser-and-comparison.md). **Evidence:** [Contract 1.1](docs/PORTING-CONTRACT.md#contract-11--g01-implementation-and-hardened-recording-boundary), [15-pair verification](evidence/g01/verify.txt), [new vectors](testdata/README.md).

### G01-02 — Port bounded XML classification and facts

- **Status:** Done. **Owner:** Go engineer. **Dependencies:** G01-01.
- **Deliverable:** Go packages for format classification, testcase/diagnostic facts, identity warnings and exact signatures, using streaming XML where suitable.
- **Acceptance:** Preserve state precedence, original-record counts, entity rejection, unsupported states, warnings and exact text. Reject budgets before unbounded allocations. Go tests cover all named edge cases and compare checked-in expected facts. No Python subprocesses.
- **Context:** [G01](docs/plans/G01-parser-and-comparison.md). **Evidence:** [Go tests](evidence/g01/go-tests.txt), [parser fuzz smoke](evidence/g01/fuzz.txt), [validation scope](docs/G01-VALIDATION.md).

### G01-03 — Port recorded discovery, inventories and comparison

- **Status:** Done. **Owner:** Go engineer. **Dependencies:** G01-02.
- **Deliverable:** `compare-recording RECORDING BEFORE_URL AFTER_URL`; recorded pagination, hashes, inventory accounting and exact diagnostic changes.
- **Acceptance:** `tools/verify.py --go-binary ...` passes every included pair. Cache reuse cannot bypass source validation. Paths stay within the supplied recording. Missing data is explicit; empty evidence is not success. Non-JSON diagnostics go to stderr; failures have nonzero exits.
- **Context:** [G01](docs/plans/G01-parser-and-comparison.md). **Evidence:** [15-pair parity](evidence/g01/verify.txt), [boundary tests](internal/provider/recording_test.go), [CLI tests](cmd/testreceipts/main_test.go).

### G01-04 — Audit Go parity and make the results inspectable

- **Status:** Done. **Owner:** Evaluation lead. **Dependencies:** G01-03.
- **Deliverable:** Side-by-side inputs, Python outputs and Go outputs, with per-case pass/fail, warnings, runtime and memory measurements.
- **Acceptance:** Repeat from a relocated checkout without the original repo or network. Deliberately altered inputs/expected outputs are detected. Record all failures and no agent-token claims. Reference and Go performance are compared on the same complete local operation.
- **Context:** [G01](docs/plans/G01-parser-and-comparison.md), [evaluation](docs/EVALUATION.md). **Evidence:** [Side-by-side outputs and measurements](evidence/g01/README.md), [per-case audit](evidence/g01/audit.json), [relocation/negative controls](evidence/g01/relocation.json).

## G02 — Portable executable deployment

**Outcome:** Users can run the completed local comparison without installing a language runtime. **Dependencies:** G01. **Status:** Done for the unsigned PoC on tested platforms. Full-machine/minimum-OS/publisher-trust coverage is unverified and outside the support promise. **Plan:** [G02](docs/plans/G02-portable-deployment.md).

### G02-01 — Reproducible builds and dependency accounting

- **Status:** Done. **Owner:** Release engineer. **Dependencies:** G01-04.
- **Deliverable:** Pinned supported Go toolchain, six target binaries, checksums and dependency/build metadata using the supplied build helper as a starting point.
- **Acceptance:** Repeated builds under the same declared environment have explained reproducibility results. Record compressed and installed sizes for the completed tool, not only scaffold sizes. No Python, fixtures, caches, secrets or large datasets in release packages.
- **Context:** [G02](docs/plans/G02-portable-deployment.md). **Evidence:** [Build/reproducibility pipeline](docs/RELEASING.md), [six-target clean-source manifest](evidence/g02/release-manifest.json), [qualification evidence](evidence/g02/README.md).

### G02-02 — Native PoC validation (scope revised)

- **Status:** Done for PoC scope: native CI 6/6 and minimal Linux userlands 2/2 pass. Full-machine/minimum-OS/download-trust tests remain unverified and are not required for this PoC. **Owner:** Release/test engineer. **Dependencies:** G02-01.
- **Deliverable:** macOS/Linux/Windows tests, with amd64/arm64 coverage explicitly identified.
- **Acceptance (revised PoC scope):** Execute actual packages on all six tested native OS/CPU pairs, preserving paths/Unicode, permissions, stderr/exits, output files, HTTPS/replay and source provenance. Retain empty-PATH/minimal-userland proof with its limits. Do not claim full-machine or older-OS compatibility. No new VMs or paid hosting.
- **Context:** [G02](docs/plans/G02-portable-deployment.md). **Evidence:** [Current six-target results](evidence/platform-ci/native-results.json), [native CI scope/results](docs/NATIVE-CI.md), [explicit platform matrix and gaps](docs/G02-VALIDATION.md).

### G02-03 — Prepare distribution documentation

- **Status:** Done for PoC documentation: MIT, project/module names, unsigned policy and install/uninstall instructions are settled. Visibility and release publication are maintainer-controlled, outside this task. **Owner:** Maintainer. **Dependencies:** G02-02.
- **Deliverable:** TestReceipts / local module `testreceipts`, MIT license, notices, install/uninstall instructions and explicitly unsigned PoC policy. Hosted-library migration and signing/notarization are outside scope.
- **Acceptance:** A reviewer can follow installation and reproduce a sample comparison. License and attribution files accompany relevant dependencies. Publishing is a separate action; no automatic release.
- **Context:** [G02](docs/plans/G02-portable-deployment.md). **Evidence:** [Release/install/uninstall/checklist](docs/RELEASING.md), [packaged instructions](release/INSTALL.md), [MIT license](LICENSE).

## G03 — Live provider support

**Outcome:** Two supported live CI URLs produce the same bounded evidence contract. **Dependencies:** G01; packaging validation repeated after HTTP is added. **Status:** Done for the supported public Prow/GCS scope; support is limited to the tested environments in docs/SUPPORT.md. **Plan:** [G03](docs/plans/G03-live-provider.md).

### G03-01 — Implement the first live provider

- **Status:** Done. **Owner:** Go engineer. **Dependencies:** G01-04.
- **Deliverable:** Read-only public Prow/GCS adapter with documented URL forms, bounded pagination, generation-pinned fetches, timeouts, retries and explicit unavailable states.
- **Acceptance:** Local HTTP-server tests cover pages, cycles, rate limits, redirects, integrity mismatch, oversized content and missing reports. Arbitrary URL fetching and out-of-scope redirects are rejected. Network failure never becomes “no failures.” Live access is tested separately from replay.
- **Context:** [G03](docs/plans/G03-live-provider.md). **Evidence:** [Live contract](docs/G03-LIVE.md), [HTTP/TLS tests](evidence/g03/go-tests.txt), [partial-listing fixture](testdata/live/partial-listing/expected.json).

### G03-02 — Validate live capture and recovery

- **Status:** Done. **Owner:** Evaluation lead. **Dependencies:** G03-01.
- **Deliverable:** A bounded real-run capture with exact inputs/outputs and a repeatable offline replay; report bytes, requests, time and errors.
- **Acceptance:** Inventories account for every discovered XML object, including generic Ginkgo names. Include partial availability and recovery controls. Full completed-binary size and platform checks are rerun. No token-saving claim from local timing.
- **Context:** [G03](docs/plans/G03-live-provider.md). **Evidence:** [Real capture audit](evidence/g03/real-capture-audit.json), [HTTP-enabled release/native evidence](evidence/g03-release/README.md), [validation and remaining platform gaps](docs/G03-VALIDATION.md).

## G04 — Agent integration and repeated-use value

**Outcome:** Determine whether the tool helps beyond a reusable URL script. **Dependencies:** G03. **Status:** Existing MCP profile and first-use Go-workflow replication complete; upgrades/client integrations and repeated-use evaluation deferred, not PoC blockers. **Plan:** [G04](docs/plans/G04-agent-value.md).

### G04-01 — Optional MCP boundary

- **Status:** Done for the pinned legacy 2025-11-25 stdio profile; modern protocol and third-party hosts remain unverified and explicitly deferred. **Owner:** Integration engineer. **Dependencies:** G03-02 and explicit prioritization.
- **Deliverable:** A thin MCP wrapper around the same Go core, with validated arguments, bounded output and exact evidence references.
- **Acceptance:** Same inputs yield the same facts as the CLI; record protocol overhead separately. No duplicate parser or model-generated summaries. Keep the CLI usable independently.
- **Context:** [G04](docs/plans/G04-agent-value.md). **Evidence:** [MCP usage/profile](docs/MCP.md), [17-case parity/overhead audit](evidence/g04/mcp-audit.json), [boundary tests](internal/mcp/server_test.go), [packaged native/live qualification](evidence/g04-release/README.md).

### G04-02 — Repeated-use agent comparison

- **Status:** First-use replication Done for the separately authorized 72 attempts; repeated-use work Deferred. All 72 automated fact/inventory checks pass; 23/24 assigned attempts execute Go, with one allowed Python fallback retained in costs. No further model campaign is authorized. **Owner:** Evaluation lead. **Dependencies:** Working interface and frozen study plan.
- **Deliverable:** A proposed comparison retaining capable parser and ready-query baselines plus a reusable URL-wrapper baseline, with first-use and repeated-use conditions separated.
- **Acceptance:** Freeze questions, source selection, correctness rubric and total-token accounting before execution. Keep failed runs, cached/uncached inputs, retries, tool overhead, follow-up reads and auditable charts. Record human review. Do not tune on held-out outcomes or assume the historical 24.36% saving transfers.
- **Context:** [G04](docs/plans/G04-agent-value.md), [evaluation](docs/EVALUATION.md). **Evidence:** [12-pair Go parity preflight](evidence/go-token-preflight/README.md), [72-attempt results and audit](evidence/go-url-first/README.md), [study protocol](docs/STUDY-PLAN.md). Median paired workflow savings are 41.53% / 27.23%; one fallback and one ready-query pair regression are explicit. Human narrative review remains pending; no repeated-use result or 24/24 Go-only execution claim is made. See [current PoC policy](docs/SUPPORT.md).
