#!/usr/bin/env python3
"""Verify the handoff offline; optionally check a Go implementation's parity."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from reference_cli import compare
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference/scripts/url_first'))
sys.path.insert(0,str(ROOT/'reference/scripts/test_scale'))
from reference import expected
p=argparse.ArgumentParser();p.add_argument('--go-binary',type=Path);args=p.parse_args()
for source in json.loads((ROOT/'docs/source-provenance.json').read_text())['files']:
 assert hashlib.sha256((ROOT/source['destination']).read_bytes()).hexdigest()==source['sha256'],source['destination']
for name in ['test_cross_run_discovery.py','test_url_first.py']:
 subprocess.run([sys.executable,'-B',str(ROOT/'reference/scripts'/name)],cwd=ROOT,check=True)
count=0
for case in sorted((ROOT/'testdata/cases').iterdir()):
 urls=json.loads((case/'request.json').read_text())['urls'];gold=json.loads((case/'expected.json').read_text())
 assert compare(case,urls)==gold,case.name
 assert expected(case,urls)==gold,case.name
 if args.go_binary:
  result=subprocess.run([str(args.go_binary.resolve()),'compare-recording',str(case),*urls],capture_output=True,text=True,check=True)
  assert json.loads(result.stdout)==gold,case.name
 count+=1
print(f'PASS: copied source hashes, 20 reference tests and {count} recorded-pair contracts.')
print('Go parity: '+('PASS' if args.go_binary else 'NOT RUN; Go scaffold does not implement comparison yet.'))
