"""Replay pinned archived step logs and two explicitly derived controls."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
args = parser.parse_args()
binary = args.binary.resolve()
fixtures = ROOT / 'testdata/build-logs'
hashes = {'failed.txt': '80006e4398c8ca8f53358bcf80bc018956ed806312fa7966f9e14fc076d193ef',
          'passed.txt': '7b3224dc6907835134bb0561b949f8b6c308c2aaa9ce43e040698e8abf70f40f'}
for name, expected in hashes.items():
    assert hashlib.sha256((fixtures / name).read_bytes()).hexdigest() == expected

rows = []
with tempfile.TemporaryDirectory() as directory:
    cut = Path(directory) / 'cut.txt'
    cut.write_bytes(b''.join((fixtures / 'failed.txt').read_bytes().splitlines(True)[:5]))
    for path, literal, partial, status, hits in [
        (fixtures/'failed.txt', 'AssertionError: failed to restore temporary ACL', False, 'matched', [13]),
        (fixtures/'failed.txt', 'Traceback', False, 'ambiguous', [1, 9]),
        (fixtures/'passed.txt', 'AssertionError', False, 'no_match', []),
        (fixtures/'passed.txt', 'PASS:', False, 'matched', [1]),
        (cut, 'Traceback', True, 'incomplete', [1]),
        (cut, 'restore temporary ACL', True, 'incomplete', []),
        (Path(directory)/'missing.txt', 'Traceback', False, 'unavailable', []),
    ]:
        flags = ['--partial'] if partial else []
        results = []
        for cmd in [[str(binary), 'log-context'], [sys.executable, str(ROOT/'tools/search_log.py')]]:
            proc = subprocess.run([*cmd, *flags, str(path), literal], capture_output=True, text=True)
            assert proc.returncode == (2 if status == 'unavailable' else 0), proc.stderr
            result = json.loads(proc.stdout)
            assert result['status'] == status and result['matchedLines'] == len(hits)
            assert [e['matchLine'] for e in result['excerpts']] == hits
            results.append(result)
        for key in ['coverage', 'excerpts']:
            assert results[0][key] == results[1][key]
        for excerpt in results[0]['excerpts']:
            start = max(1, excerpt['matchLine']-2)
            assert excerpt['startLine'] == start
            assert excerpt['lines'] == path.read_text().splitlines()[start-1:excerpt['matchLine']+2]
        rows.append(dict(file=path.name, literal=literal, status=status, matchLines=hits,
                         coverage=results[0]['coverage'], excerpts=results[0]['excerpts']))
print(json.dumps(dict(sourceHashes=hashes, cases=rows), indent=2))
