# CI Evidence — Go port starter

A standalone starting point for a small tool that compares structured test reports from two CI runs. **CI Evidence is a working name.** It has no dependency on Spotlight, Swift, Apple frameworks or the original repository.

The Python reference works with recorded provider responses. The Go code currently provides only help/version and an explicit error for unimplemented operations. **The Go parser, live downloading and MCP interface are not built yet.** This folder is ready to copy into a new repository and use as a new chat's workspace.

## Start here

1. Read [HANDOFF.md](HANDOFF.md) for the current state and scope.
2. Use [NEW_CHAT_PROMPT.md](NEW_CHAT_PROMPT.md) to start the implementation chat.
3. Follow [Tasks.md](Tasks.md), beginning with the parser and recorded-run comparison.

## Run now

From this folder, with Python 3.10 or newer:

```sh
python3 tools/verify.py
```

On Windows, use `py -3` in place of `python3`. The reference dependency is bundled; no pip installation, network, external drive, credentials or model access is needed. Python is for development checks, not the intended deployed tool.

With Go installed ([official instructions](https://go.dev/doc/install)):

```sh
go test ./...
go build -trimpath -buildvcs=false -o bin/ci-evidence ./cmd/ci-evidence
go run ./cmd/ci-evidence help
go run ./tools/build.go
```

For a directly runnable Windows native binary, use `-o bin/ci-evidence.exe`. The build helper emits six OS/architecture binaries and checksums under ignored `dist/`. Cross-compilation is not proof they run correctly on each OS. The module's provisional language floor is Go 1.23; use a currently supported Go release and pin the verified version for releases. Change the local module name `ci-evidence` to the new repository's module path before external library publication.

After the Go comparison is implemented, this must pass:

```sh
python3 tools/verify.py --go-binary bin/ci-evidence
```

It deliberately fails with today's scaffold. There is no fake comparison or silent Python fallback.

## What is included

- Tested Python discovery, parser, inventory and comparison helpers, with 20 tests.
- Nine small recorded development pairs, exact expected outputs and a separate DOM-based checker.
- Four small original Jenkins fixture reports with source provenance and license.
- Go CLI scaffold and a dependency-free cross-build helper.
- Porting contract, implementation plans, release checklist and a new-chat handoff.
- Compact historical evaluation metrics and a chart. Large CI recordings and agent traces are excluded.

## Evidence and limits

The latest historical study found 42.63% fewer median paired agent tokens than parser-based custom assembly and 24.36% fewer than a ready-made query, across 12 pairs and 72 investigations. All required-fact and inventory checks passed. This measured first-use setup on captured Prow/GCS data—not a Go implementation, live networking, repeated use of a prepared URL script, or Spotlight.

See [the evidence summary](evidence/README.md). The new development fixtures are for correctness, not fresh evidence of token savings. The first release goal is a correct portable executable; do not rerun paid agent benchmarks to validate a language port.
