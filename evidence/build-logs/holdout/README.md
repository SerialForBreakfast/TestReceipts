# Fixed-rule replay on four additional failures

Go recovered 7/19 labeled evidence groups with 28 extra lines. Python recovered 1/19 with 24 extra lines. Go covered one complete question and Python covered none. Both tools found their search literals on every log. A literal hit alone was insufficient on three Go cases and all four Python cases.

| Archived project | Go found / extra lines | Python found / extra lines | Evidence missed |
|---|---:|---:|---|
| kOps | 1/10 · 4 | 1/10 · 4 | Both found the summary header and first spec. Neither returned the remaining nine volume-metrics spec names on even-numbered lines 9130–9146. |
| Kubernetes node swap | 0/1 · 10 | 0/1 · 10 | Both flagged two ambiguous suite-failure markers. The rejected NodeSwap feature gate appeared three lines before each marker, at 210 and 241. Both windows missed it. |
| Azure cloud provider | 4/4 · 7 | 0/4 · 5 | Go followed the summary and recovered both failed specs and both locations at 8914–8917. Python missed all four, including the service annotation and load-balancer failure locations. |
| controller-runtime | 2/4 · 7 | 0/4 · 5 | Go recovered the failed cache spec and its location. Both missed the empty service list and expected length of one at 682–683. Python also missed the spec and location. |

## Scope and scoring

Before fetching build logs, we pinned both search implementations and selected the first eligible failed run per project in the historical JUnit index after excluding the four tuning-log URLs. All four eligible projects were retained. These build logs were held out from log-context tuning. Their runs were already represented in earlier JUnit work. The queries and minimum line labels were constructed by inspecting the full logs before running the search tools. They have no independent human adjudication. The totals weight each evidence group equally, so the ten-name kOps question accounts for ten of the nineteen groups.

An evidence group is found if the excerpt contains any of its labeled line numbers. Extra lines are distinct returned lines outside the labels for that question. This can include helpful headings or locations. Repeated excerpts are deduplicated. The replay verifies excerpt text against the original bytes split on LF and checks each source hash. No model evaluation was run.

[Selection and tool hashes](freeze.json) · [Pinned log URLs, input hashes, queries and labels](cases.json) · [Every returned, missed and extra line number](results.json).

## Reproduce from the repository root

```sh
mkdir -p .artifacts/log-holdout
python3 - <<'PY'
import json, subprocess
for case in json.load(open('evidence/build-logs/holdout/cases.json')):
    subprocess.run(['curl','-fsSL','--max-filesize','30000000',case['url'],'-o','.artifacts/log-holdout/'+case['id']],check=True)
PY
./tools/go build -o .artifacts/log-holdout/testreceipts ./cmd/testreceipts
python3 tools/replay_project_logs.py .artifacts/log-holdout/testreceipts .artifacts/log-holdout --cases evidence/build-logs/holdout/cases.json
```
