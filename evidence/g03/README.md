# G03 live acquisition evidence

[Validation](../../docs/G03-VALIDATION.md) and [usage/contract](../../docs/G03-LIVE.md) define the scope.

- `real-capture-audit.json`: exact original input/response file hashes, source URLs, replay and independent-check results, tamper/recovery controls.
- `comparison.json`, `python-comparison.json`, `dom-comparison.json`: inspectable facts. New Go acquisition fields remain explicit; the original parser facts agree.
- `partial-control.json`: deliberately altered report remains unresolved, without discarding other evidence.
- `network.json`: public requests, response bytes/hashes, attempts, statuses and timing; no credentials.
- `go-tests.txt`, `provider-tests.txt`, `parity.txt`: final HTTP/TLS tests and unchanged reference/fixture checks.
- `development-notes.md`: corrections and failed restricted acquisition probe, not counted as successful live validation.

Raw real responses and reports are downloaded data and remain ignored under `.artifacts/g03-real-final/`. They must be retained separately for future replay; a source-only clone omits them. The compact audit identifies all inputs exactly. The real result intentionally remains incomplete because parser identities contain slashes.
