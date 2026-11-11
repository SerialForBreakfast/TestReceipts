# Failure evidence from four public build logs

One archived Prow build-log.txt per project, selected from previously captured run pairs with JUnit failures. Both unmodified tools received the same full file and one literal taken from its failure output. Before running the searches, we inspected the logs and recorded a question and the minimum evidence lines needed to answer it. A group lists interchangeable copies of a line. “Extra” counts distinct displayed lines outside those labels, including headings and blanks that may still help navigation. These exploratory annotations have not had independent human review.

| Project and question | Go evidence groups found | Python evidence groups found | Extra lines, Go / Python | Observed limitation |
|---|---:|---:|---:|---|
| Kubernetes: which volume operation timed out and what unexpected results followed? | 0/3 | 2/3 | 0 / 3 | Go stopped after line 37 and correctly reported partial coverage. Line 38 is 66,645 bytes, above its scanner limit. Python reached the failure at 599 and showed the unexpected results at 597–598, but missed the timeout at 592. |
| Kueue: which package failed setup and why? | 1/2 | 1/2 | 4 / 4 | Both found the package at 418. Their windows ended at 420, before the import-cycle explanation at 423. |
| Prow: which package and running test timed out, and after how long? | 3/3 | 3/3 | 2 / 2 | The five-line window contained the package, ten-minute timeout and test name. The two extra lines were headings. |
| controller-runtime: which two failed specs and source locations appear in the summaries? | 0/4 | 0/4 | 10 / 10 | Both flagged the two TestSource matches as ambiguous. The spec names and locations at 1140–1141 and 2799–2800 preceded both windows. Returned lines included the start of unrelated tests. |

Both tools supplied the complete annotated answer on **one of four questions**. Go returned 4/12 evidence groups and Python 6/12. Identical literal hits can still yield insufficient diagnostic context. This small, deliberately inspected Prow sample establishes concrete failure modes. No model calls, token estimates or latency measurements were used.

[Run URLs, SHA-256 hashes, literals, questions and annotations](cases.json) · [Per-tool output line numbers, missed groups and extra lines](results.json).

## Repeat

From the repository root, restore the four archived files into ignored storage:

```sh
mkdir -p .artifacts/log-projects
python3 - <<'PY'
import json, subprocess
for c in json.load(open('evidence/build-logs/projects/cases.json')):
    subprocess.run(['curl','-fsSL','--max-filesize','25000000',c['url'],'-o','.artifacts/log-projects/'+c['id']],check=True)
PY
./tools/go build -o .artifacts/log-projects/testreceipts ./cmd/testreceipts
python3 tools/replay_project_logs.py .artifacts/log-projects/testreceipts .artifacts/log-projects
```

The replay verifies each downloaded hash before invoking either tool, checks the excerpt text against the cited lines, and scores the union of each tool's windows. Raw logs remain in ignored storage. A missing or changed archive prevents replay of the pinned comparison.

## Follow-up on the same inputs

The updated Go tool skips lines at or above 64 KiB, records their physical line numbers and continues with partial coverage. Within 12 lines of a literal hit it can follow Go test diagnostics, Ginkgo failure summaries and the Errors section following a setup failure. These rules were developed using the earlier misses. This rerun measures improvement on known cases.

| Project | Evidence groups (old Go / Python / updated Go) | Extra lines (old Go / Python / updated Go) | Gain |
|---|---|---|---|
| Kubernetes | 0 / 2 / 3 | 0 / 3 / 7 | Skips line 38 and recovers the timeout and both unexpected results. Coverage stays partial. |
| Kueue | 1 / 1 / 2 | 4 / 4 / 6 | Reaches the import-cycle diagnostic on line 423. |
| Prow | 3 / 3 / 3 | 2 / 2 / 2 | The ordinary timeout window already answers the question. |
| controller-runtime | 0 / 0 / 4 | 10 / 10 / 14 | Both ambiguous suite matches now include their spec and source location. |

Updated Go returns 41 distinct lines across the four files, including 29 outside the minimum evidence labels. Previous Go returned 20 (16 extra), and Python returned 25 (19 extra). Thus the update gains eight groups for 13 additional extra lines versus previous Go, or six groups for ten additional extra lines versus Python. All four annotated answers are now covered. [Updated replay](summary-follow.json).
