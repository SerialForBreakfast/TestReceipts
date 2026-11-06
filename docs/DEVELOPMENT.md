# Development

Go 1.27.3 is pinned. This checkout uses the verified ignored toolchain through `./tools/go`; a normal native Go installation may use `go` instead. On a fresh macOS arm64 checkout, obtain the pinned archive from https://go.dev/dl/ and run `python3 tools/setup_go.py --archive /path/to/go1.27.3.darwin-arm64.tar.gz`. Other hosts can install the pinned version natively.

```sh
./tools/go test ./...
./tools/go build -trimpath -buildvcs=false -o bin/testreceipts ./cmd/testreceipts
python3 tools/verify.py --go-binary bin/testreceipts
./tools/go test -race ./...
./tools/go vet ./...
```

HTTP failure tests need local loopback access; no public network or model calls are used in the test suite. Python reference checks need Python 3.10+, and the setup helper needs 3.12+. The frozen reference wheel is bundled; its isolated runner does not need pip. Preserve reference hashes and the original fixture outputs.

See [release builds](RELEASING.md), [task ledger](../Tasks.md), [porting contract](PORTING-CONTRACT.md) and [handoff](../HANDOFF.md). Source installs and removal are described in [install instructions](../release/INSTALL.md). No runtime language installation is needed for a packaged executable.

For MCP parity and protocol-overhead checks, run `python3 tools/check_mcp.py --binary bin/testreceipts --out evidence/g04 --real-capture .artifacts/g03-release-live`. Omit `--real-capture` on a fresh checkout without the ignored dataset; the 16 small fixture cases still run. The optional `--live` performs a public capture, not a model evaluation.
