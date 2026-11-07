# Go historical-input preflight — 2026-11-06

**12/12 full Go outputs equal the frozen Python reference wrapper outputs.** This includes inventory, counts, exact diagnostics and incomplete/unsupported states. No model calls were made. [Per-case summary](summary.json).

This is a historical replication on previously inspected inputs, not held-out correctness or an agent-token benchmark. The 42.63% / 24.36% historical savings remain unvalidated for Go and repeated use. A prepared reusable URL-script baseline is required for the latter.

Reproduce from this checkout with the optional original study available locally:

```sh
./tools/go build -o .artifacts/go-token-preflight/testreceipts ./cmd/testreceipts
python3 tools/check_historical_go.py \
  --study ../Spotlightning/docs/evaluation/results/2026-11-06-url-first-v1 \
  --binary .artifacts/go-token-preflight/testreceipts \
  --out .artifacts/go-token-preflight/results
```

Both implementations' per-case outputs are retained in the ignored output directory. Source and binary fingerprints are in the summary. The original inputs remain external; see the [archive catalog](../external-archive-catalog.json). They are not a TestReceipts runtime dependency. Single timing observations are not comparative speed results.

Next: freeze model, budget and execution schedule in the [study plan](../../docs/STUDY-PLAN.md), then measure complete agent investigations under fresh and prepared repeated-use conditions. Human narrative review is still pending.
