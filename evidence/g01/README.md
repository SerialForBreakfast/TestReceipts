# G01 local comparison evidence

The original recorded inputs and expected results are under [`testdata/cases`](../../testdata/cases/). Each named directory here contains the complete Python and Go comparison JSON for that case. Warnings and unresolved states are retained in those outputs. [`audit.json`](audit.json) records per-case pass/fail, complete-operation wall times and macOS peak RSS. This is development correctness evidence, not an agent evaluation or performance advantage claim.

- [`build.json`](build.json): native binary hash, production-source hashes, toolchain, command and dependency inventory.
- [`verify.txt`](verify.txt): frozen source hashes, 20 reference tests, and 15 runtime/DOM/Go fixture contracts.
- [`go-tests.txt`](go-tests.txt): focused Go tests, race detection and statement coverage.
- [`fuzz.txt`](fuzz.txt): bounded parser fuzz smoke.
- [`relocation.json`](relocation.json): relocated verification, spaces/Unicode path, empty executable PATH, and negative controls.
- [`G01 validation`](../../docs/G01-VALIDATION.md): exact scope, environment and limitations.

Recreate after building `bin/testreceipts`:

```sh
python3 tools/verify.py --go-binary bin/testreceipts
python3 tools/check_relocation.py --go-binary bin/testreceipts
python3 tools/audit_g01.py --go-binary bin/testreceipts
```

The audit's macOS resource measurement may require broader local execution permissions. Timing is one invocation per case; caches and system load are uncontrolled. Python includes temporary reference setup. RSS is the timed command's reported maximum, not summed child-process memory. No model calls are involved.
