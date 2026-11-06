# Evaluation rules for the new project

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
