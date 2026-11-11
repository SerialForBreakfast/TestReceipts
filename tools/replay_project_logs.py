"""Score local, hash-pinned logs against annotated evidence lines."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
parser.add_argument('log_dir', type=Path)
parser.add_argument('--cases', type=Path, default=ROOT/'evidence/build-logs/projects/cases.json')
args = parser.parse_args()
cases = json.loads(args.cases.read_text())
results = []
for case in cases:
    path = args.log_dir / case['id']
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != case['sha256']:
        raise ValueError(f'Archive changed: {path}')
    lines = data.decode().split('\n')
    groups = case['evidenceGroups']
    observed = {}
    for tool, cmd in [('go', [args.binary.resolve(), 'log-context']),
                      ('python', [sys.executable, ROOT/'tools/search_log.py'])]:
        result = json.loads(subprocess.check_output([*cmd, path, case['literal']]))
        shown = set()
        for excerpt in result['excerpts']:
            for n, line in enumerate(excerpt['lines'], start=excerpt['startLine']):
                assert lines[n-1].removesuffix('\r') == line
                shown.add(n)
        observed[tool] = dict(status=result['status'], coverage=result['coverage'],
                              matches=result['matchedLines'], shownLines=sorted(shown),
                              missedGroups=[g for g in groups if shown.isdisjoint(g)],
                              extraLines=sorted(shown.difference(*groups)))
        if result.get('skippedLines'):
            observed[tool]['skippedLines'] = result['skippedLines']
        if result.get('reason'):
            observed[tool]['reason'] = result['reason']
            observed[tool]['linesScanned'] = result['linesScanned']
    results.append(dict(id=case['id'], results=observed))
print(json.dumps(results, indent=2))
