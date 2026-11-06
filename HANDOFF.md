# Handoff: build the standalone Go CI tool

Prepared 2026-11-06. The user explicitly wants to separate this CI work from Spotlightning and start a portable Go deployment. Do not bring Spotlight features into this project.

## Product intent

Given two CI runs, report what failed before and after, which exact diagnostic messages appeared or disappeared, and which original reports support the comparison. Preserve warnings when the evidence is incomplete. This is structured-report comparison, not arbitrary-log diagnosis or proof of a common root cause.

The desired deployment is an executable users can run without Python, Node or a compiler. A CLI comes first. A reusable Go core and optional MCP interface can follow. Git hooks, GitHub Actions integration and multiple providers are not prerequisites for the first port.

## What already works

The Python reference reads saved Prow/GCS listings, follows listing pages, verifies report bytes, classifies XML by content, parses JUnit records, builds inventories, groups exact diagnostics and compares two runs. It retains distinctions between complete artifact discovery and incomplete parser coverage. Empty evidence is never a passing test suite.

The reference helpers and tests are copied with their original relative layout under `reference/`. They include the tested parser-profile adjustments. `tools/reference_cli.py` creates a temporary isolated workspace to run them. No paths point to the original machine. A copied-file hash manifest records origin; some source was uncommitted in Spotlightning, so hashes—not the historical Git commit alone—identify this version.

## What does not exist yet

The Go executable is scaffolding only. It does not parse, compare or download. The provider reference replays captured responses; it is not a live connector. No production MCP server, installer, Windows runtime validation or measured Go performance advantage exists. The ordinary Python source dependency is junitparser 5.0.3; it must not ship in the final Go binary.

## First implementation session

1. Run `python3 tools/verify.py`; confirm the 20 tests and nine fixture comparisons.
2. Read [porting contract](docs/PORTING-CONTRACT.md) and [G01 plan](docs/plans/G01-parser-and-comparison.md).
3. Implement the bounded Go parser and exact diagnostic grouping with the standard library where practical. Preserve observed-record semantics and warnings.
4. Implement `compare-recording RECORDING BEFORE_URL AFTER_URL` against the included recording format. Return JSON compatible with each fixture's expected.json.
5. Run the same fixture comparison through the Go executable. Any disagreement is investigated, not hidden by rewriting the golden data.
6. Add focused tests for gaps, then proceed to portable packaging. Live HTTP is a distinct milestone.

Keep the Python reference frozen as a comparator. If it contains a bug, retain a regression, document the deliberate behavior change and version the contract. Do not preserve unsafe behavior just for parity.

## Evidence to carry forward

The useful observed benefit is packaging discovery and setup. Earlier apparent gains shrank when a strong ready-made query was the baseline. Increasing corpus size and failure density did not consistently improve savings. The latest URL-first result still misses the 30% target against the ready-made query.

Maintain both capable baselines in future agent studies. Add a reusable URL-script baseline and repeated-use trials before claiming long-term savings. Count complete investigations, tool overhead, retries and follow-up reads; show cached and uncached tokens separately. Human narrative review of historical results remains pending.

## Moving this folder

Copy the entire `ci-evidence` folder, including dotfiles, into the desired new repository directory. It intentionally contains no `.git` directory, credentials, external-drive links required at runtime, or bundled toolchain. Initialize Git in that copied folder when ready. No repository, remote or new chat has been created automatically.

Open the copy as the new chat workspace and paste [NEW_CHAT_PROMPT.md](NEW_CHAT_PROMPT.md). All local document links and reference checks should work after relocation. See [VALIDATION.md](VALIDATION.md) for what was actually verified at handoff time.

## Decisions still open

Choose the final repository/module name and first-party license before public distribution. Target macOS, Linux and Windows on amd64/arm64; each needs native smoke tests. The Go choice is authorized as the implementation direction, but binary size and speed claims remain unmeasured for the complete tool. Standard-library-only is preferred, not a reason to hand-roll XML or TLS. Make any added dependencies explicit.
