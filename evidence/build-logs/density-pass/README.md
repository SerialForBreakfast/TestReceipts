# Frozen replay on six additional failure logs

We selected all six archived builds in the earlier Kubernetes failure-density corpus, in manifest order, before downloading or inspecting these build logs. All six URLs and content hashes differ from the ten log-context development inputs and from each other. The selection covers Kubernetes integration and unit jobs, not six separate projects. The frozen executable, Go search source, Python baseline and existing scorer were hashed before retrieval. No extraction rules changed.

Each query uses the first Go test failure marker (or failed-package summary marker), through its test/package name. Questions and line labels were chosen by inspecting raw files before either search ran. Each group accepts repeated copies of the annotated text. These task-specific labels have not received independent human adjudication.

| Build | Go found / extra | Python found / extra | Misses |
|---|---:|---:|---|
| Integration 1, heavy | 0/1 · 5 | 0/1 · 5 | Both missed the test server's context deadline at line 200, three lines before the hit. |
| Integration 1, sparse | 2/2 · 5 | 1/2 · 4 | Go included both sides of the topology-label diff. Python returned the actual labels but missed the expected nil map at 147. |
| Integration 2, heavy | 2/2 · 21 | 0/2 · 5 | Go included the missing govet warning at 245 and the unexpected typecheck import error at 251. Python missed both. |
| Integration 2, sparse | 0/2 · 5 | 0/2 · 5 | Both missed the successful linearizability check at 114 and the expected expired-watch behavior at 120. |
| Unit, volume | 1/2 · 7 | 1/2 · 7 | Both cited the failed package and flagged ambiguous literal matches. Neither reached the first undefined-type diagnostic at 3841. |
| Unit, sparse | 0/2 · 5 | 0/2 · 5 | Both missed the expected resource-version error at 1274–1275 and the failed list at revision 3 on 1276. Go also marked partial coverage for an oversized line. |

Go recovered 5/11 groups with 48 extra lines and answered 2/6 questions completely. Python recovered 2/11 with 31 extra lines and answered 0/6 completely. The linter case accounts for 16 of the 17 additional extra lines. Extra lines are distinct returned lines outside that question's minimum labels. The scorer checks each displayed line against the archived bytes. No model calls or token measurements.

[Selection, exclusions and tool hashes](freeze.json) · [Pinned source URLs, queries and acceptable lines](cases.json) · [Per-tool line receipts and coverage warnings](results.json).

From the repository root with the project Go toolchain installed, rebuild and reproduce:

```sh
mkdir -p .artifacts/log-density
python3 - <<'PY'
import hashlib, json, pathlib, subprocess
base = pathlib.Path('evidence/build-logs/density-pass')
for name, digest in json.loads((base/'freeze.json').read_text())['hashes'].items():
    if not name.startswith('.artifacts/'):
        assert hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest() == digest
for case in json.loads((base/'cases.json').read_text()):
    out = pathlib.Path('.artifacts/log-density')/case['id']
    if not out.exists():
        subprocess.run(['curl','-fsSL','--max-time','90','--max-filesize','100000000',case['url'],'-o',out],check=True)
PY
./tools/go build -o .artifacts/log-density/testreceipts ./cmd/testreceipts
python3 tools/replay_project_logs.py .artifacts/log-density/testreceipts .artifacts/log-density --cases evidence/build-logs/density-pass/cases.json > .artifacts/log-density/replay.json
cmp .artifacts/log-density/replay.json evidence/build-logs/density-pass/results.json
```
