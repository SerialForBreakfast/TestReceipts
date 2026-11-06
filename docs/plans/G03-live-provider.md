# G03 — Live Prow/GCS acquisition

Task ledger: [G03](../../Tasks.md#g03--live-provider-support).

Separate a provider interface for listing pages and fetching versioned bytes from discovery/classification. Start with the public Prow/GCS platform actually represented by the historical experiment; GitHub Actions support is not assumed. Define supported URL forms before implementation. Recorded URLs in testdata are fixture identifiers, not real source runs to fetch.

Use Go HTTP with explicit request/body/time/page/object limits. Verify redirects remain within the supported provider scope, and resolve object names under the selected run. Preserve object generation, size and available checksums. Treat partial pagination and unavailable objects as incomplete acquisition. Do not recursively crawl arbitrary links or follow local/file URLs.

Build local-server fixtures for throttling, transient errors, missing objects, changed generations, pagination loops and integrity mismatches. Cache entries must be tied to source identity/version and validated before reuse. Store original inputs for replay, not just derived summaries. Keep authentication out of the first public-provider milestone unless separately scoped; never retain credentials in evidence.

A live run produces a bounded inventory and capture, then invokes the same G01 comparison. Report network requests/bytes/time separately from local processing. Compare the live capture and replay facts, then repeat release tests because HTTP dependencies and certificate requirements affect the final executable.
