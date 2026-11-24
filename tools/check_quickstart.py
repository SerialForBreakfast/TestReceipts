#!/usr/bin/env python3
"""Check documented offline outcomes and log citations without model calls."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binary', type=Path, required=True)
args = parser.parse_args()
binary = args.binary.resolve()


def run(*arguments):
    result = subprocess.run([str(binary), *arguments], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=30)
    assert not result.stderr, result.stderr
    return json.loads(result.stdout)


log_path = 'testdata/build-logs/failed.txt'
result = run('log-context', log_path, 'failed to restore temporary ACL')
assert (result['status'], result['coverage'], result['matchedLines']) == (
    'ambiguous', 'supplied_file', 2)
assert [entry['matchLine'] for entry in result['excerpts']] == [11, 13]
lines = (ROOT / log_path).read_text().splitlines()
for block in result['excerpts']:
    start = block['startLine'] - 1
    assert block['lines'] == lines[start:start + len(block['lines'])]

base = 'https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/'
result = run('compare-recording', 'testdata/cases/changes', base + '100', base + '200')
assert result['change']['newDistinct'] == 1
assert result['change']['disappearedDistinct'] == 1
assert result['change']['sharedDistinct'] == 1
assert result['newEvidence'][0]['text'] == 'new diagnostic'
print('PASS: both offline quickstart examples and exact log citations; no model calls.')
