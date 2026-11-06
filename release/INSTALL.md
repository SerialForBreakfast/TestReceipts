# TestReceipts private development candidate

Choose the archive matching your operating system and CPU architecture. Verify
its SHA-256 against SHA256SUMS.json from the same build. These unsigned development
packages have not been published, notarized, or qualified on every target platform.
See LICENSE-STATUS.txt and BUILD.json before distribution.

Extract the archive to a folder you control. On macOS/Linux run
`./testreceipts version` and `./testreceipts help`; on Windows run
`.\testreceipts.exe version` and `.\testreceipts.exe help` in PowerShell.
You may place the executable in a user-owned directory on PATH. No administrator
installation, Go, Python, Node, compiler, or separately installed language runtime
is required. Uninstall by deleting the extracted folder and any executable copy
you placed on PATH. The tool writes JSON to stdout and does not install services.

To compare a local recording:

    testreceipts compare-recording RECORDING BEFORE_URL AFTER_URL > comparison.json

A recording contains catalog.json, saved listing pages and original XML bytes.
The source checkout supplies development examples under testdata/cases/changes;
fixtures are deliberately excluded from the executable package. Run from that
checkout, replacing the executable path with your installed path:

    testreceipts compare-recording testdata/cases/changes https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100 https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200

Successful interpretation returns 0. Invalid command/recording or output failure
returns 2 with an error on stderr. Partial report evidence can return 0 with
artifactComplete=false or parserCoverage.complete=false: inspect both fields.
This version never downloads CI reports and does not need TLS certificates for
recorded comparisons. Network/certificate requirements must be retested with G03.

Toolchain upstream floors (not tested minimums): macOS 13+, Linux kernel 3.2+,
Windows 10+/Server 2016+. amd64 uses baseline v1; arm64 uses v8.0.
Current native results are recorded separately in the source's G02 validation.
