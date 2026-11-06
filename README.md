# TestReceipts

TestReceipts compares structured test reports from two recorded CI runs. It reports observed testcase counts, exact diagnostic changes, and the original report inventory, while preserving incomplete and unsupported evidence states.

The local Go comparison works without Python, Node, network access, or a compiler at runtime. Live CI downloading and MCP are later milestones. This standalone project has no Spotlightning, Swift, or Apple framework dependency in its core.

## Build and run

The project pins Go 1.27.3. On this development checkout, the verified toolchain is installed under ignored `.cache/toolchain/`; use:

```sh
./tools/go test ./...
./tools/go build -trimpath -buildvcs=false -o bin/testreceipts ./cmd/testreceipts
bin/testreceipts help
bin/testreceipts compare-recording testdata/cases/changes \
  https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100 \
  https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200
```

The command writes one JSON result to stdout. Invalid commands or recordings write bounded errors to stderr and return a nonzero exit. Report acquisition or classification failures remain explicit in the JSON inventory; they do not erase other usable evidence. Recorded URLs are identifiers and are never fetched.

A normal native Go installation can use `go` in place of `./tools/go`. On Windows, build with `-o bin/testreceipts.exe`. The provisional module path is `testreceipts`; choose a hosted module path before external library publication.

For a fresh macOS arm64 checkout, obtain `go1.27.3.darwin-arm64.tar.gz` from [Go's download archive](https://go.dev/dl/) and run:

```sh
python3 tools/setup_go.py --archive /path/to/go1.27.3.darwin-arm64.tar.gz
./tools/go version
```

The setup helper checks the pinned SHA-256 before extraction and refuses to overwrite an installation. The toolchain is a development dependency and is never committed or bundled into the product. Other hosts can install the same Go version natively.

## Verify

Python 3.12+ is needed only for the development setup helper; the reference verification tools need Python 3.10+. The frozen reference wheel is bundled, and its runner excludes system site packages. No pip installation, network, credentials, or model calls are needed.

```sh
python3 tools/verify.py --go-binary bin/testreceipts
./tools/go test -race ./...
./tools/go vet ./...
python3 tools/check_relocation.py --go-binary bin/testreceipts
python3 tools/audit_g01.py --go-binary bin/testreceipts
```

There are 20 frozen reference tests and 15 recorded comparison pairs, each checked against the Go executable, Python runtime, and independent DOM checker. Go tests additionally exercise boundaries and failure behavior. The audit retains per-case outputs, wall time and macOS peak-RSS measurements; macOS resource measurement may need broader local execution permissions. These development fixtures are not held-out performance or agent-value evidence.

## Status and next milestones

G01 is complete: bounded XML classification, observed-record facts, exact signatures, recorded pagination/discovery, integrity checks, inventories, and two-run comparison. See [G01 validation](docs/G01-VALIDATION.md), [task ledger](Tasks.md), [behavior contract](docs/PORTING-CONTRACT.md), and [handoff](HANDOFF.md).

G02-01 is complete and supplies reproducible six-target private candidate builds and packaging. See [release instructions](docs/RELEASING.md) and [G02 qualification/gaps](docs/G02-VALIDATION.md); clean-machine and other-platform native validation remain pending. Only macOS arm64 has current native runtime evidence; no Windows/Linux runtime compatibility is claimed. G03 adds live Prow/GCS support. MCP and agent studies remain deferred. First-party code uses the [MIT license](LICENSE); the hosted module path remains open before public distribution.

Historical agent findings are in [evidence/README.md](evidence/README.md). They do not measure this Go implementation, repeated use, or live networking. No Go size, speed, or token-saving advantage is claimed.

## Build a private development package

```sh
python3 tools/release.py build --version v0.1.0-dev.2 --out dist/my-candidate --verify-repro
python3 tools/release.py verify dist/my-candidate
```

This builds six packages twice and requires matching binary/archive bytes. Python is only a packaging/test tool. Packages contain the Go executable, install instructions, metadata and notices. They are private candidates while public module naming, signing and platform qualification remain open. No publication is automatic.
