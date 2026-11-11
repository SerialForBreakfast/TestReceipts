# Frozen replay on four additional builds

Go supplied 5/8 labeled facts and 21 extra lines. Python supplied 3/8 and 17 extra lines. Go completely answered two questions, Python zero. Both tools returned a unique literal match and supplied-file coverage in each case.

| Build | Go found / extra | Python found / extra | Missed evidence |
|---|---:|---:|---|
| GCP aggregator, 2116943251540807680 | 2/2 · 6 | 1/2 · 4 | Python included the spec but missed the dynamic client's server-unavailable error at 2419. |
| AWS EBS, 2117917430956167168 | 2/2 · 6 | 1/2 · 4 | Python included the spec but missed the three-minute PV modification timeout at 1152. |
| Kubernetes alpha features, 2118169343949803520 | 0/2 · 5 | 0/2 · 5 | Both excerpts showed resource listing failed, but omitted the two-hour timeout at 822 and the suite counts (91 passed, zero failed) at 670. |
| GCP pod connectivity, 2116218469547511808 | 1/2 · 4 | 1/2 · 4 | Both included the spec but omitted the server's missing-pod error for pause-pod-1 at 2896. |

All distinct failure-bearing builds from the historical cross-run v4 selection qualified after excluding the sixteen development logs by URL. Input hashes were checked against all sixteen hashes and each other. No candidate was dropped. These are new logs for log-context, from three Kubernetes ecosystem jobs. Two successful recoveries use the same single-failure summary format. They do not measure token savings or performance across CI providers.

Source and binary hashes and the selection were recorded before the logs were fetched. One question per build and acceptable evidence lines were assigned by inspecting the raw logs before either tool ran. For the three Ginkgo spec failures the literal was the single-failure summary heading; for the teardown failure it was the resource-listing failure marker. Groups accept repeated copies of the same annotated text. Extra lines are distinct displayed lines outside the question's minimal labels, including potentially helpful context. The scorer checks exact source text in both ordinary excerpts and related diagnostic blocks. The labels have not received independent human review. No model calls ran.

[Selection, excluded inputs and tool hashes](freeze.json) · [Archives, questions and labels](cases.json) · [Line receipts](results.json).

From a checkout with the project Go toolchain installed, reproduce with:

```sh
python3 evidence/build-logs/cross-pass/replay.py --fetch > .artifacts/cross-pass-replay.json
cmp .artifacts/cross-pass-replay.json evidence/build-logs/cross-pass/results.json
```

Create .artifacts before redirecting on a fresh checkout. Omitting --fetch uses existing local archives. A changed search source or changed archive fails the replay.
