# Original scaffold handoff validation — 2026-11-06

Historical evidence only. For the implemented TestReceipts local comparison, see [G01 validation](docs/G01-VALIDATION.md).

The starter was copied to a temporary directory outside Spotlightning and tested there. The reference does not require the original checkout, an external drive, network access or credentials.

| Check | Result |
|---|---|
| Copied reference source hashes | Pass |
| Existing discovery tests | 13/13 pass |
| Existing URL integration tests | 7/7 pass |
| Small recorded-pair contracts | 9/9 agree with runtime and independent DOM checker |
| Go scaffold tests | Pass |
| Go cross-builds | macOS/Linux/Windows × amd64/arm64 pass |
| Native executable | macOS arm64 help and unimplemented-command error checked without Go/Python on PATH |
| Go parser/comparison parity | Not run: Go comparison is not implemented |
| Other platforms' runtime behavior | Not tested; cross-builds only |
| Live CI networking / MCP | Not implemented or tested |
| Model calls | None |

The build check used Go 1.27.3, downloaded from the official Go site and verified against its published SHA-256. The toolchain was kept in a temporary directory, not installed system-wide and not shipped in this folder. The module declares a provisional Go 1.23 language floor; that older toolchain was not tested.

Scaffold binary sizes are recorded in [validation.json](docs/validation.json) only to prove builds exist. They are **not** size estimates for the finished parser, HTTP provider or MCP tool. Only the native macOS arm64 binary was executed. No speed or token advantage is claimed for Go.

The bundled wheel and small upstream XML files retain their notices. Bulky historical archives are referenced by hash but excluded. Relative documentation links were checked to stay within the starter folder. The source code has no required original-machine absolute paths.
