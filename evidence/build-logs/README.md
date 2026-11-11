# Archived build-log replay

From a source build, run:

```sh
./tools/go build -o ./bin/testreceipts ./cmd/testreceipts
./bin/testreceipts log-context testdata/build-logs/failed.txt 'AssertionError: failed to restore temporary ACL'
python3 tools/search_log.py testdata/build-logs/failed.txt 'AssertionError: failed to restore temporary ACL'
python3 tools/replay_build_logs.py ./bin/testreceipts
```

The command searches one local step log for a case-sensitive literal. Each JSON excerpt gives the 1-based matched line, starting line and normally up to two original lines on either side. SHA-256 identifies the supplied bytes when read successfully. The search counts all matching lines and displays the first eight windows. Overlapping windows are allowed. Files over 16 MiB are refused. Lines of 64 KiB or more (excluding CRLF) are skipped and numbered in `skippedLines`. Search continues with partial coverage. Excerpts never bridge a skipped line. Invalid UTF-8 or NUL bytes in supported-size lines stop the scan with partial coverage. Read failures return unavailable. Recognized Ginkgo summary headers include the contiguous indented entries until a blank or unindented line. A trailing Go failure can recover the nearby summary and an assertion block beginning with `[FAILED] Expected` up to 12 lines before its header. A `Test Suite Failed` marker can also include an `ERROR:` within the preceding six lines. Original text and line numbers are preserved.

Use `--partial` before the filename when the upstream log is known to be truncated. With zero or one hit in a partial file, status is `incomplete`. Multiple observed hits are always `ambiguous`; consult `coverage` and `reason` for partial input. A missing file returns `unavailable` and exit 2. A clean local read establishes coverage of the supplied file only. Silent upstream truncation cannot be detected. No match establishes only that the literal was absent from the scanned lines.

## Replay

Two small fixtures preserve the exact Windows amd64 packageSmoke.log artifact bytes from the [failed native CI run](https://github.com/SerialForBreakfast/TestReceipts/actions/runs/42299118931) and its [successful rerun](https://github.com/SerialForBreakfast/TestReceipts/actions/runs/42300372775). The original local artifact paths were `.artifacts/ci-run1/native-windows-amd64/packageSmoke.log` and `.artifacts/ci-final/native-windows-amd64/packageSmoke.log`. The replay pins both hashes and checks expected line numbers and exact surrounding text against a reusable Python search script.

| Input | Query | Expected result from both tools |
|---|---|---|
| Failed step | Exact final assertion | Line 13, with context from lines 11–13 |
| Failed step | Traceback | Ambiguous, lines 1 and 9 |
| Successful rerun | AssertionError | No match |
| Successful rerun | PASS: | Line 1 |
| First five lines of failed step, explicitly partial | Traceback | Incomplete, observed line 1 |
| Same partial copy | restore temporary ACL | Incomplete, zero observed matches |
| Missing file | Traceback | Unavailable |

All seven cases passed. Four use unmodified archived inputs. The last three are derived or missing-file controls. This is one failure and its rerun from one project. The terminal assertion identifies a cleanup failure; an earlier assertion is visible at line 5. Neither a unique string match nor a missing string determines root cause or job status. The replay tests literal search accuracy and excerpt fidelity. Agent tokens, time savings and generalization to other failure families remain unmeasured. [Per-case outputs and hashes](replay.json).

[Four-project follow-up](projects/README.md) measures missed evidence and extra context on full archived Prow logs.

[Held-out replay](holdout/README.md) compares the frozen rules and reusable script on four additional archived failures.

## Full-summary replay on both known sets

The same hash-pinned logs, literals, evidence groups and Python script were rerun. Both sets now inform development. Extra lines are distinct returned lines outside each question's minimum labels, including headings or source locations that may still help a reader.

| Set | Previous Go (groups / extra) | Updated Go | Python | Change versus previous Go |
|---|---:|---:|---:|---|
| Original four | 12/12 · 29 | 12/12 · 35 | 6/12 · 19 | Six extra lines, all in controller-runtime, for no additional labeled evidence |
| Later four | 7/19 · 28 | 19/19 · 41 | 1/19 · 24 | Twelve additional evidence groups and thirteen additional extra lines |

On the later set, kOps gained nine failed spec names for nine extra lines (mostly source locations). Node swap gained the rejected feature gate for zero additional extra lines; the two occurrences supply equivalent evidence and both are shown. Controller-runtime gained actual and expected collection lengths for four additional extra lines. Azure was unchanged. Ambiguous matches and the skipped oversized Kubernetes line on the original set remain explicit. No model calls or token measurements.

[Original four current line receipts](projects/full-summary.json) · [Later four current line receipts](holdout/full-summary.json). The earlier result files remain available for comparison. Reproduce with the same replay commands in each set's README using the current binary.

[Independent replay](verification/README.md) rebuilds both Go versions and scores all saved comparisons, including two additional runs.

[Six-build frozen replay](density-pass/README.md) measures the resize-diagnostic version on archived logs outside all ten development cases.

## Go test and compiler diagnostics on all sixteen logs

For Go failure markers the search includes nearby source-positioned deadlines and expected/unexpected error messages. A matching Testify test name can attach its assertion block from the preceding 48 lines. For a matched failed-package header followed by its build-failed record, the first compiler diagnostic in the subsequent Errors section is reported as batch-level evidence. Disjoint blocks are returned in the optional JSON `related` array with their own starting line and kind. They do not increment the literal match count.

Across the 16 development cases, current Go recovered 46/46 labeled groups with 145 extra lines. Prior Go recovered 40/46 with 138 extra lines. Python recovered 11/46 with 87 extra lines. Only four Go outputs changed: test-server timeout (+1 group, +0 extra), watch expiry and linearizability result (+2, +5), compiler diagnostic (+1, +0), and compacted-revision assertion (+2, +2). Fifteen additional distinct lines were shown: eight labeled lines (including equivalent evidence) and seven outside the labels. Input ambiguity and skipped-line coverage remain explicit. No model calls.

With all four archived sets restored, run `./tools/go build -o .artifacts/build-logs/testreceipts ./cmd/testreceipts` and `python3 tools/replay_source_errors.py .artifacts/build-logs/testreceipts`. The scorer verifies source hashes and excerpt bytes, checks Python against the pinned baseline receipts, and records added and removed line numbers relative to the preceding run. [All 16 per-case receipts](source-errors/results.json).

[Four additional fixed-rule log comparisons](cross-pass/README.md) cover the GCP aggregator, AWS EBS volume modification, GCE teardown, and GCP pod connectivity failures.
