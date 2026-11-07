# Live Prow/GCS capture and replay

TestReceipts supports public read-only Kubernetes Prow runs backed by `kubernetes-ci-logs`. It does not support arbitrary URLs, private/authenticated runs, other buckets, extensionless reports, archives or GitHub Actions in this milestone.

## Commands and supported URLs

```sh
bin/testreceipts compare-live .artifacts/my-new-capture BEFORE_URL AFTER_URL > comparison.json
bin/testreceipts compare-recording .artifacts/my-new-capture BEFORE_URL AFTER_URL > replay.json
```

The capture directory must not exist. Accepted URLs are exactly HTTPS on `prow.k8s.io` with either `/view/gs/kubernetes-ci-logs/logs/JOB/BUILD` or `/view/gs/kubernetes-ci-logs/pr-logs/pull/REPOSITORY/PR/JOB/BUILD`. Builds/PR numbers are decimal; job/repository segments use ASCII letters, digits, dash, underscore or dot. A trailing slash is accepted. Userinfo, ports, query strings, fragments, encoded paths, traversal and other hosts/schemes are rejected before acquisition.

Only the fixed `https://storage.googleapis.com/storage/v1/b/kubernetes-ci-logs/o` API is contacted. The command constructs its own prefix-scoped requests; it does not follow links from Prow HTML or provider metadata. Every redirect is rejected, including same-host redirects. Generation-pinned media requests use the exact listed object name, and a returned generation header must match when present. No credentials or provider authentication are accepted. The system HTTP proxy configuration may be used; proxy credentials/headers are not recorded.

The [GCS list API](https://docs.cloud.google.com/storage/docs/json_api/v1/objects/list) supplies continuation tokens, and [object metadata](https://docs.cloud.google.com/storage/docs/json_api/v1/objects) supplies generation, size and available checksums. The adapter enumerates every listed case-insensitive `.xml` object, including generic names. It validates byte length and every available MD5/CRC32C checksum, retains SHA-256, and treats missing checksums as unavailable evidence. It rejects encoded/compressed objects rather than silently comparing decoded bytes against stored-byte checksums.

## Bounds, failure and cancellation

Live network acquisition has a five-minute deadline, with 20 seconds per HTTP attempt, 10-second dial/TLS handshake limits, and a 15-second response-header timeout. The subsequent bounded local comparison may finish after acquisition ends. Ctrl-C cancels through the same context and allows an incomplete capture to be written if filesystem access remains available. A forced process termination or disk failure can leave a non-replayable directory; it is not reported as a successful comparison.

There are at most three attempts per request. Only transient network/read failures, timeouts, HTTP 429 and HTTP 5xx are retried. Delays use bounded exponential backoff; integer Retry-After is capped at two seconds. Redirects, TLS verification errors and permanent HTTP failures are not retried. Response bodies are bounded before parsing and are retained, including bounded error bodies, for audit. No XML entity expansion is allowed by the shared parser.

Live-specific limits are 64 listing pages per run, 512 HTTP attempts and 96 MiB consumed response bodies per two-run operation. The shared limits remain 8 MiB saved listing JSON, 16,384 listed objects per run, 16 MiB per XML and 32 MiB validated XML per run, with at most 2,048 XML fetches per run. Bodies may read one extra sentinel byte to detect overflow. Error bodies are capped at 64 KiB. Listing pages are validated before acceptance; duplicates, cycles, malformed JSON, out-of-prefix names or limits stop discovery with an explicit issue while preserving previously accepted pages/reports. Data after the unresolved point is unknown.

Missing objects, generation changes, checksum/length mismatches, request limits and unsupported encodings become unavailable object entries. Captures are immutable directories; retrying into a new directory is the recovery path. No persistent download/parse cache exists, so reuse cannot bypass current-byte validation. Invalid invocation/recording structure or output failures return nonzero stderr errors; a successfully interpreted partial capture returns JSON with incomplete fields, not an invented passing suite.

## Recording and uncertainty contract 1.2

`request.json` preserves the exact requested URL order, including repeated URLs. `catalog.json`, `pages-N.json` and `objects/*.xml` retain the G01 recording shape. An optional `acquisition` map adds per-run listing `complete`, `unresolved` issue strings, `noSuccessfulListingPages`, and object acquisition error details. If the first page is unavailable, the replay envelope contains a synthetic empty page and explicitly sets `noSuccessfulListingPages=true` plus incomplete discovery. This is not a claim that the provider returned an empty listing. Later unavailable pages leave the last continuation token intact; replay accepts that terminal token only with explicit incomplete acquisition metadata.

Live snapshots include `discoveryCoverage`. Its `complete` flag covers listing acquisition, not report parsing or object availability. `artifactComplete` also requires complete listing acquisition and no blocked XML. `parserCoverage` retains unsupported constructs and identity/count/retry limitations from G01. Live comparison `comparisonComplete` is true only when both inventories and parser structures are complete and parser limitations are empty. All these claims are scoped to the observed listed XML, never all CI logs/tests or a stable point-in-time snapshot of an actively uploading run. The command does not establish that a run has finished uploading.

Counts remain observed records; diagnostics remain exact text signatures, not root-cause inference. Partial comparisons retain usable counts and changes, with the uncertainty fields visible. The original 15 fixture outputs are unchanged; old recordings without `acquisition` retain their original JSON shape. CRC32C-only GCS objects are now supported alongside MD5; no-checksum objects remain unresolved. A new small [partial-listing fixture](../testdata/live/partial-listing/expected.json) locks the extension. The Python reference is still frozen; its old worker cannot replay incomplete pagination, so partial acquisition has dedicated Go tests while real complete-listing facts are checked independently.

`responses/*.body` contains exact bounded HTTP bodies; `network.json` records public request URLs, statuses, attempts, body-byte counts, timings and response hashes. It stores no authentication headers. `requestSeconds` sums HTTP/response-read durations; `acquisitionSeconds` includes acquisition validation, retry delay and capture I/O, excluding subsequent core comparison. CLI wall time additionally includes parsing/comparison. Body-byte measurements exclude TLS/HTTP framing overhead. `comparison.json` retains the live result; offline replay performs no HTTP.

Downloaded real datasets/responses remain under ignored `.artifacts/`; compact comparison facts, inventories/hashes and request evidence are tracked. Keep the original capture externally or locally if long-term replay is needed; a source-only clone intentionally omits it. Re-fetching later is a new observation and may fail if provider retention removes an original generation.

## Validation

See [G03 validation](G03-VALIDATION.md), [HTTP/TLS tests](../internal/provider/live_test.go), and [real capture audit](../evidence/g03/real-capture-audit.json). The HTTP-enabled build requires HTTPS egress and a working OS trust store; Linux often needs a CA bundle. Real TLS was exercised on this macOS arm64 host. Subsequent native CI verifies HTTPS/replay on all six tested targets; no older-OS or full-machine promise is made. See [unsigned PoC scope](SUPPORT.md). No model calls or performance advantage claims are involved.
