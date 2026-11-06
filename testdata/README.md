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

`tools/make_testdata.py` generated these fixtures and compared the runtime with the independent reference. It refuses to overwrite existing fixture directories. Preserve the originals and review any regeneration as a contract change. G01 added the further vectors described below; the original unicode case tests disappearance.

The additional four source files under `upstream/` retain their license and origin. They are already-known parser examples, not held-out evaluation data.

G01 adds `unicode-added`, `suite-errors`, `retries`, `identity-and-counts`, `unsupported-constructs`, and `xml-text`. These exercise long added Unicode excerpts, exact escaping, suite diagnostics, retry ambiguity, state precedence, slash identities, invalid/mismatched declared counts, wrapped reports, unknown elements, comments/CDATA, and XML attribute whitespace. `canonical-vectors.json` records exact UTF-8 bytes and SHA-256 for cross-language JSON edge cases, including XML-inexpressible control characters and U+2028/U+2029.

`tools/add_g01_vectors.py` creates the new vectors and refuses to overwrite a case. Use `--case NAME` to create one missing case. The original nine expected outputs remain unchanged. The `xml-text` case exposed the optional-system-parser dependency described in contract 1.1; it now agrees under the isolated standard-library reference runner.

The `xml-text` original intentionally contains literal tab, LF and CRLF in an attribute. Its scoped `.gitattributes` rule preserves exact bytes and disables whitespace style errors for that fixture.
