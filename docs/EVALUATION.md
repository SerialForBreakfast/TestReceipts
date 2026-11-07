# Evaluation rules for the new project

The separately authorized 72-investigation first-use Go replication is complete. [Results and audit](../evidence/go-url-first/README.md): 41.53% / 27.23% median paired workflow savings, 72/72 automated fact/inventory passes, 23/24 assigned attempts executing Go and one permitted Python fallback retained in costs. Human narrative review remains pending. Additional model runs, repeated-use evaluation, token spending and infrastructure remain deferred without a new explicit instruction. Existing correctness/CI checks remain valid; later-study guidance below is retained for a future task.

## Port correctness first

The included fixtures are development inputs. Their expected outputs were checked against the runtime and independent DOM reference. Reusing them is appropriate for regression tests, not a claim of unseen-data validation. Keep all source versions, commands, outputs, warnings and expected-result changes reviewable.

Go release checks require the same facts and coverage as the reference. Size and time measurements compare the complete same workload. Record failures, OS/architecture, compiler, dependencies and whether a result was built or actually executed. Do not compare a minimal scaffold binary with a full parser or downloader.

## Human-readable reporting

Every substantial comparison should include:

- A short plain-language finding and its limitation.
- Exact input files/URLs with source hashes, and expected/actual outputs beside each other.
- Per-case correctness/completeness outcomes, not just one average.
- Charts for useful measured quantities: output bytes, processing time, memory, executable size; agent tokens only when actually measured.
- Version history and failed attempts. Missing measurements stay unknown, not zero.

Keep large original reports and traces in ignored storage. Track a small catalog with checksums and restore instructions; a local archive is not a remote backup. Small fixtures and compact review reports belong in Git.

## Later agent evaluation

The historical studies retain two capable baselines: agent-written comparisons using a reusable parser, and an existing ready-made query. Add a reusable URL-wrapper baseline for repeated-use claims. Preserve comparable tool access, caching and script reuse across approaches. Include model tool overhead, retries and follow-up reads; report cached/uncached tokens separately. More bytes, more failures or a smaller response alone do not demonstrate agent savings. Model execution requires its own frozen scope and authorization.
