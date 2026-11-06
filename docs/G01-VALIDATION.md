# G01 validation — 2026-11-06

TestReceipts now performs the complete local recorded-run comparison in Go. The executable does not launch Python, use a network provider, or read expected outputs. G01 is the local correctness milestone; portable release qualification remains G02.

## Environment and setup

- Go 1.27.3, macOS arm64; the project-local archive SHA-256 matches the original handoff's pinned `dd3908cf20959d798c1e06ebe5b72213f0505ce01373b40ce3110975a6cd99c2`.
- Python 3.14.3 for development verification. Reference workers use `-E -S` and the bundled junitparser wheel, excluding optional site packages.
- Native host: macOS 27.0, build 26A428, arm64.
- Git initialized on `main`; initial commit `4f9e15e` preserves the original handoff. No remote or public release was created.
- Module/command renamed to `testreceipts`; toolchain and caches remain ignored, selected with `./tools/go`.

## Checks

| Check | Evidence / scope |
|---|---|
| Frozen source hashes and 20 reference tests | [Verification log](../evidence/g01/verify.txt); copied reference files unchanged |
| 15 recorded-pair contracts | Python runtime, independent DOM checker, and Go executable agree; original nine goldens preserved |
| Focused Go tests with race detector | [Go test log](../evidence/g01/go-tests.txt); parser, signatures, comparison, recording boundaries, CLI behavior |
| Static checks | `./tools/go vet ./...` passed |
| Parser fuzz smoke | [Fuzz log](../evidence/g01/fuzz.txt); bounded exploratory check, not exhaustive coverage |
| Complete-operation outputs and measurements | [Audit](../evidence/g01/audit.json), with per-case Python and Go JSON |
| Relocated source verification and binary | [Relocation results](../evidence/g01/relocation.json); copied into a path with spaces and Unicode |
| No Go/Python on executable PATH | Actual recorded comparison passed with an empty PATH, macOS arm64 only |
| Negative controls | Altered golden and copied frozen source fail verification; altered original XML becomes explicit unresolved evidence |
| Other native platforms | Not tested in G01; prior handoff cross-builds apply only to the scaffold |
| Live networking / MCP / model calls | None |

The [build record](../evidence/g01/build.json) identifies the native binary, its production-source hashes, toolchain, build command and dependency inventory.

## Named behavior and boundary coverage

Go tests cover canonical UTF-8 JSON bytes and hashes, Unicode/control escaping and U+2028/U+2029, 512-code-point excerpts, top-three ordering and full added-occurrence totals, testcase state precedence, suite diagnostics, retries, slash identities, declared counts, nested diagnostic markup, comments/CDATA, literal attribute whitespace versus character references, malformed roots, namespace bindings/attributes, DTD/entity rejection, unsupported encoding, and unsupported report structure.

Recording tests cover paths and existing symlink escapes, duplicate/trailing/malformed JSON, invalid UTF-8 and surrogate escapes, missing/unreachable listing pages, cycles, duplicate objects, run scope, invalid sizes/MD5 metadata, current-byte tampering after a successful run, retained SHA mismatch, per-XML budgets, collection budgets, listing page/object/JSON bounds, and the 2,048-report cap. CLI tests check usable JSON and stderr/nonzero failures. Empty reports preserve `no_junit_reports`; partial evidence never becomes a complete passing suite.

The parser uses Go's XML decoder with independent byte, node and depth limits. Namespace validity is checked through its streaming RawToken API because the decoder otherwise tolerates undeclared prefixes. The production core uses only the Go standard library and has no cache to bypass source validation.

## Contract notes and limits

[Contract 1.1](PORTING-CONTRACT.md#contract-11--g01-implementation-and-hardened-recording-boundary) documents explicit recording hardening, structure bounds and the isolated-reference harness correction discovered by the XML comment regression. Frozen reference files were not rewritten. The legacy DOM checker differs from the runtime on nested element tail text; a focused Go regression preserves runtime semantics and the coverage warning.

The per-case measurements time full local CLI invocations, not parser-only microbenchmarks. Python includes isolated-workspace preparation and subprocess execution; OS caches/system load are uncontrolled. macOS `time` reports maximum resident set size for the timed command, not aggregate concurrent child-process memory. One observation per implementation/case is retained for inspectability. These measurements do not establish a complete-production Go size/speed advantage, token savings, live-network performance, or repeated-use value.

No clean-machine installation, Windows/Linux native runtime, signing/notarization, final first-party license, or hosted module path is claimed. Fixture parity and a short fuzz run do not establish support for every JUnit producer. Unsupported and unresolved states remain part of the product contract.
