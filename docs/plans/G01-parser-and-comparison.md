# G01 — Port the verified local behavior

Read [the contract](../PORTING-CONTRACT.md). The first deliverable is a correct local comparison, not a live connector. Task status belongs in [Tasks.md](../../Tasks.md#g01--correct-local-go-comparison).

## Component boundaries

Use `internal/junit` for XML classification/facts, `internal/evidence` for stable identities and exact diagnostic comparison, `internal/provider` for the recorded listing/object source, and `internal/cli` if command handling grows. Keep data structures independent of the CLI and MCP. Prefer Go's standard library; document any dependency and why it is necessary.

The path is request → validated recording → all listing pages → bounded original bytes → classification → facts and coverage → two-run comparison → JSON. Retain source hashes and original diagnostic text throughout. Distinguish provider completeness from parser coverage and record identity uncertainty.

## Porting sequence

G01-01 freezes additional edge vectors; G01-02 implements XML and canonical signatures; G01-03 connects discovery and comparison; G01-04 checks parity and records outputs. Implement the small signature function early: Go JSON escaping and rune/byte differences can silently change IDs or excerpts.

The current `reference/scripts/url_first/ready_query.py` is both the ready-query baseline and the adapter's comparison. Preserve that equality. `provider_api.py` is a replay implementation. `manifest_api.py` shows inventory semantics and cache validation. `reference.py` and `oracle.py` are audit-only alternate parsers; do not import their expected answers into the product.

## Failure behavior

Reject invalid manifests, path escapes, malformed JSON, invalid recorded object lengths/hashes, duplicate listings and pagination cycles. A report acquisition/classification failure is visible in the run's unresolved inventory. Preserve any usable evidence without claiming completeness. Failures that prevent trustworthy interpretation return nonzero status and bounded errors; no source dumping into terminal errors.

The prototype has rough edges, including recording paths and caches designed for controlled experiments. Harden those boundaries in the port rather than reproduce them blindly. Deliberate deviations need a regression case and contract note.

## Verification

Test locally without network or models. Run existing checks before porting. Compare parsed JSON, not pretty-print whitespace, but preserve canonical bytes wherever hashes depend on them. Record Python and Go versions, raw expected/actual outputs, counts and timings. Keep real upstream fixtures labeled parser examples, not consecutive CI runs. Full historical archives are optional and unnecessary for this milestone.
