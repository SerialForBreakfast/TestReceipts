#!/usr/bin/env python3
"""Compare Go with the frozen Python wrapper on historical inputs; no models.

The original study directory is optional external evidence, never a runtime dependency.
This verifies full output parity, not agent-token savings or held-out correctness.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from reference_cli import compare

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--study', type=Path, required=True)
p.add_argument('--binary', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
study, binary = a.study.resolve(), a.binary.resolve()
a.out.mkdir(parents=True, exist_ok=True)
questions = json.loads((study / 'protocol/questions.json').read_text())
rows = []
for question in questions:
    recording = study / 'recordings' / question['id']
    urls = question['urls']
    row = {'id': question['id'], 'urls': urls}
    try:
        start = time.perf_counter()
        result = subprocess.run([str(binary), 'compare-recording', str(recording), *urls],
                                capture_output=True, text=True, check=True, timeout=120)
        row['goWallSeconds'] = time.perf_counter() - start
        actual = json.loads(result.stdout)
        expected = compare(recording, urls)
        row.update(fullOutputEqual=actual == expected,
                   comparisonComplete=actual.get('comparisonComplete'),
                   goOutputBytes=len(result.stdout.encode()))
        for label, value in [('go', actual), ('reference', expected)]:
            (a.out / (question['id'] + '-' + label + '.json')).write_text(
                json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    except Exception as exc:
        row.update(fullOutputEqual=False, error=str(exc))
    rows.append(row)
    print(question['id'], row['fullOutputEqual'], flush=True)
report = {
    'modelCalls': 0,
    'binarySha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
    'historicalFreezeSha256': hashlib.sha256((study / 'freeze.json').read_bytes()).hexdigest(),
    'cases': rows,
    'passed': sum(r['fullOutputEqual'] for r in rows),
    'total': len(rows),
    'limits': 'Historical development data; not held out. Full Go/Python output parity only. '
              'Single uncontrolled timing observations are not speed benchmarks. '
              'No agent-token savings, repeated-use benefit or live network reliability measured.'
}
(a.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
raise SystemExit(0 if report['passed'] == report['total'] else 1)
