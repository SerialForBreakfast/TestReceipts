#!/usr/bin/env python3
"""Retain exact G01 parity results and measure complete local CLI operations."""
import argparse,json,platform,re,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--go-binary',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'evidence/g01');a=p.parse_args();binary=a.go_binary.resolve();a.output.mkdir(parents=True,exist_ok=True)
rows=[]
def execute(cmd):
 with tempfile.TemporaryDirectory() as tmp:
  measurements=Path(tmp)/'time.txt';wrapped=cmd
  if platform.system()=='Darwin':wrapped=['/usr/bin/time','-l','-o',str(measurements),*cmd]
  start=time.perf_counter();r=subprocess.run(wrapped,capture_output=True,text=True);elapsed=time.perf_counter()-start
  if r.returncode:raise RuntimeError(f'command failed ({r.returncode}): {r.stderr[:512]}')
  peak=None
  if measurements.exists():
   m=re.search(r'(\d+)\s+maximum resident set size',measurements.read_text());peak=int(m.group(1)) if m else None
  return r.stdout,elapsed,peak
for case in sorted((ROOT/'testdata/cases').iterdir()):
 urls=json.loads((case/'request.json').read_text())['urls'];gold=json.loads((case/'expected.json').read_text());target=a.output/case.name;target.mkdir(exist_ok=True);metrics={}
 for name,cmd in [('python',[sys.executable,str(ROOT/'tools/reference_cli.py'),str(case),*urls]),('go',[str(binary),'compare-recording',str(case),*urls])]:
  raw,elapsed,peak=execute(cmd);actual=json.loads(raw);(target/f'{name}.json').write_text(json.dumps(actual,ensure_ascii=False,indent=2)+'\n');passed=actual==gold
  metrics[name]={'pass':passed,'wallSeconds':round(elapsed,6),'maximumResidentSetBytes':peak}
  if not passed:raise AssertionError(f'{case.name}: {name}')
 rows.append({'case':case.name,'inputs':f'testdata/cases/{case.name}','results':metrics})
result={'scope':'Complete recorded comparison CLI operations, one invocation per case; not a performance advantage claim. Python includes temporary reference setup and subprocess execution. OS caches uncontrolled; no agent/model calls. Memory is maximum RSS reported by macOS time for the timed command, not summed concurrent child-process memory.','platform':platform.platform(),'python':platform.python_version(),'cases':rows}
(a.output/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(f'PASS: saved {len(rows)} Python/Go comparison pairs and operation measurements.')
