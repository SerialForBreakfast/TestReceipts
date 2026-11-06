# ADR-001 — Standalone Go CLI for CI evidence

**Status:** Go implementation direction authorized by the user, 2026-11-06. Detailed behavior and deployment remain to be validated. This supersedes the tentative language preference recorded as Spotlightning ADR-014 for this spin-off only.

## Decision

Build an independent Go CLI with a reusable comparison core. Start with local captured reports and preserve the tested Python behavior before adding live CI providers. Ship platform-specific executables without requiring Python, Node or Go on the user's machine. Keep MCP optional and later.

## Why

The measured benefit came from packaging report discovery and comparison, not Spotlight or Apple frameworks. The user wants a lightweight portable tool and wants Spotlightning to remain focused on Spotlight. Go is selected for implementation and deployment simplicity, not a measured performance advantage.

## Alternatives considered

- Rust: good control over size and memory; could be smaller or faster, but requires more implementation work for this task. It remains an option if measured constraints warrant reconsideration.
- Swift: supports macOS, Linux and Windows, and matches existing expertise; deployment/runtime dependencies need platform-specific work. Spotlight itself remains Apple-only.
- C: potentially small, with more manual memory and library integration work.
- TypeScript/Node: convenient npm distribution, but users need Node or a bundled runtime.
- Python: proven reference implementation; environment setup or runtime bundling conflicts with the desired deployment.
- Java: excluded by user preference.

## Consequences

A rewrite must preserve parsing semantics and evidence boundaries. Go's built-in XML and HTTP tools reduce dependency needs but do not implement JUnit semantics or a CI provider for us. Six target builds are a goal, not proof of compatibility. Benchmark the complete tool, including HTTPS and parsing, rather than a help-only binary.

## Sources

- [Go installation](https://go.dev/doc/install)
- [Go XML support](https://pkg.go.dev/encoding/xml)
- [Go target/build documentation](https://go.dev/doc/install/source)
- [Swift platform support](https://www.swift.org/about/)
- [Rust target support](https://doc.rust-lang.org/rustc/platform-support.html)

The source project has not been deleted or rewritten by creating this folder. Historical reports remain there; compact evidence is carried here.
