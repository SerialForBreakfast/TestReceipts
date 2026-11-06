# Behavior to preserve during the Go port

The executable's first complete command is proposed as:

```text
ci-evidence compare-recording RECORDING BEFORE_URL AFTER_URL
```

It reads only the supplied local recording, emits one JSON result to stdout, and sends execution errors to stderr with a nonzero exit. No live network calls occur in this mode. Unknown commands fail. The CLI name and JSON contract are local development choices until versioned for release.

## Input format and discovery

See each `testdata/cases/*/catalog.json`, `pages-*.json` and `request.json`. A catalog maps run URLs to saved listing pages and object keys to relative byte-file paths or recorded acquisition errors. Treat all relative paths as untrusted: no absolute paths, parent traversal or symlink escapes. Recorded URLs are identifiers, not permission to fetch them.

Enumerate all pages, detect cycles, and account for every case-insensitive `.xml` object under the run scope. Do not rely on a filename containing junit: that previously omitted Ginkgo reports. Duplicate listed object names are errors. Preserve distinct objects with identical bytes rather than inventing unique-test counts.

Verify declared object size and provider MD5, plus retained SHA-256. Provider MD5 is an integrity check, not a security identity. Account for malformed, unavailable, unsupported, oversized and non-JUnit XML separately. Non-JUnit objects may be excluded with a reason; ambiguous or unavailable evidence makes discovery incomplete.

Reference bounds: 16 MiB per XML, 32 MiB per run, at most 2,048 accepted reports in a parsed inventory. Add explicit bounded listing pages/object counts, timeouts and archive limits before live network support. The prototype's internal JSON parser-input cap is 128 MiB; this does not override the outer XML/run limits.

Reject DTD/entity declarations. Namespaced JUnit and wrapped/unknown JUnit-like roots currently produce explicit unresolved states. Do not silently drop them or treat them as passing. Use Go's XML parser, not regex, and preserve these stricter format policies around it.

## Counts and identity

Count observed testcase records. A case's state precedence is error, then failure, then skipped, otherwise passed. Counts are not distinct logical tests and not guaranteed executions when producer semantics are unclear. Preserve coverage warnings for ambiguous identities, retry ambiguity, count mismatches, nested diagnostic markup and unsupported constructs. Read `single_report.py` and `oracle.py` for precise existing behavior; fixtures alone are not the entire specification.

An exact diagnostic signature hashes canonical JSON of kind, exceptionType, message and original text. Do not normalize paths, stack frames, whitespace, timestamps or case. Equality means equal recorded diagnostics, not the same root cause. Group occurrence counts separately from testcase counts.

Canonical JSON uses UTF-8, sorted keys, no separator spaces and Python-compatible escaping. Go's default HTML escaping, Unicode escaping and terminal newline can change hashes. Write explicit cross-language vectors, including Unicode, quotes, backslashes, control characters and U+2028/U+2029. Do not assume `encoding/json` defaults are byte-identical.

## Comparison output

Use the included `expected.json` files as exact development contracts. Each run includes original URL, inventory counts/hashes, excluded/unresolved objects, parsed-record counts, parser coverage and distinct failure signatures. Changes include new, disappeared and shared signatures and new occurrence totals.

New evidence contains at most three added diagnostics sorted by descending occurrence count and then signature. Diagnostic excerpts are the first 512 Unicode code points, not 512 UTF-8 bytes or Go string bytes. Preserve totalCharacters so truncation is visible. Keep complete originals available for later exact fetch.

An empty listing can have complete artifact discovery while parser coverage is false with `no_junit_reports`. These fields answer different questions. Coverage is scoped to listed XML, not all CI logs, archives or external reports.

## Comparing implementations

`tools/verify.py` checks nine recorded pairs against both the Python runtime and a separate DOM-based checker. It optionally executes the Go binary on exactly those inputs. Current fixtures cover added/shared/disappeared diagnostics, skipped/passed records, generic filenames, pagination, empty evidence, malformed/namespace/entity XML, Unicode and original upstream reports. Existing tests add cache reuse, tampering, download errors and budgets.

The upstream fixture pair is deliberately unrelated: it tests parser compatibility, not a real consecutive-run investigation. All included data is development data; do not label it held out after use. Add Go tests for the full reference semantics, including retries, suite-level failures, source changes, error-message stability and boundary conditions.
