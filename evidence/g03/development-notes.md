# G03 development corrections

An initial race-detector run found an unsynchronized counter in the timeout HTTP test server: retries can overlap handlers whose responses have timed out. The test counter now uses atomic operations. This was a test-harness race; final race results are retained separately.

The initial restricted network probe returned no bytes. Its result explicitly retained listing failures, `artifactComplete=false`, `no_junit_reports`, and `comparisonComplete=false`. Loopback tests and real public acquisition were then run with the necessary network access; the unavailable probe was not counted as live validation. The failed probe remains locally under ignored `.artifacts/g03-real/`.

The real reports retain `ambiguous_slash_identity` warnings. Those warnings were not removed to obtain a complete result. Raw downloaded responses and reports remain under ignored capture directories; compact hashes, request measurements and comparison facts are tracked.
