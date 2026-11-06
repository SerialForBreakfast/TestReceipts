# Small development inputs and exact expected outputs

Each directory under `cases/` contains the complete recorded input and one expected comparison. Inspect `request.json`, `pages-0.json`, `pages-1.json`, object XML files and `expected.json` together. The recorded URLs are synthetic identifiers; do not fetch them from the internet.

| Case | What it exercises |
|---|---|
| changes | New, disappeared and shared diagnostics; pass/skip counts |
| empty | Complete empty listing but no parser evidence |
| malformed | Invalid XML reported as unresolved |
| non-junit | Valid XML that is not a test report |
| namespace | Unsupported namespaced JUnit stays explicit |
| entities | DTD/entity declaration rejection |
| unicode | Exact Unicode failure text and signature handling |
| pagination | Multiple listing pages and repeated diagnostic occurrences |
| upstream-parser-only | Two small original Jenkins reports; not a real consecutive-run pair |

`tools/make_testdata.py` generated these fixtures and compared the runtime with the independent reference. It refuses to overwrite existing fixture directories. Preserve the originals and review any regeneration as a contract change. The first implementation task adds further missing vectors, including an added long Unicode diagnostic to exercise output truncation (the current unicode case tests disappearance).

The additional four source files under `upstream/` retain their license and origin. They are already-known parser examples, not held-out evaluation data.
