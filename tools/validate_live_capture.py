#!/usr/bin/env python3
"""Audit a retained real capture offline; never fetch source URLs."""
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from reference_cli import compare
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'reference/scripts/url_first'),str(ROOT/'reference/scripts/test_scale')]
from reference import expected
p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();capture=a.capture.resolve();binary=a.binary.resolve();a.out.mkdir(parents=True,exist_ok=True)
load=lambda p:json.loads(p.read_text());catalog=load(capture/'catalog.json');live=load(capture/'comparison.json');urls=[run['url'] for run in live['runs']]
env=os.environ.copy();env['PATH']='';env['HTTPS_PROXY']='http://127.0.0.1:1';env['HTTP_PROXY']='http://127.0.0.1:1';env['ALL_PROXY']='http://127.0.0.1:1'
def replay(root):
 start=time.perf_counter();r=subprocess.run([str(binary),'compare-recording',str(root),*urls],env=env,capture_output=True,text=True,check=True,timeout=30);assert not r.stderr;return json.loads(r.stdout),round(time.perf_counter()-start,6)
actual,seconds=replay(capture);assert actual==live
# New acquisition fields extend the unchanged G01 facts contract.
legacy=json.loads(json.dumps(actual));legacy.pop('comparisonComplete')
for run in legacy['runs']:run.pop('discoveryCoverage')
python=compare(capture,urls);dom=expected(capture,urls);assert legacy==python==dom,'independent facts disagree'
for name,value in [('comparison.json',actual),('python-comparison.json',python),('dom-comparison.json',dom),('network.json',load(capture/'network.json'))]:(a.out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
with tempfile.TemporaryDirectory(prefix='testreceipts-real-control-') as tmp:
 control=Path(tmp)/'capture';shutil.copytree(capture,control);modified=load(control/'catalog.json');key=next(iter(modified['objects']));entry=modified['objects'][key];original=(control/entry['path']).read_bytes();(control/entry['path']).write_bytes(original+b'changed')
 partial,_=replay(control);assert any(not r['artifactComplete'] and r['unresolvedObjects'] for r in partial['runs']);assert partial['comparisonComplete'] is False
 (control/entry['path']).write_bytes(original);recovered,_=replay(control);assert recovered==live
 (a.out/'partial-control.json').write_text(json.dumps(partial,indent=2,ensure_ascii=False)+'\n')
network=load(capture/'network.json')
for event in network['events']:
 if 'responseFile' in event:assert hashlib.sha256((capture/event['responseFile']).read_bytes()).hexdigest()==event['responseSha256']
manifest={'capturePath':str(capture.relative_to(ROOT)),'urls':urls,'replayEqual':True,'replayWallSeconds':seconds,'offlineExecution':'empty PATH and unusable HTTP/HTTPS/ALL proxy; replay code performs no HTTP','pythonAndIndependentDOMFactsEqual':True,'partialControl':'altered report detected as unresolved; unaffected evidence retained','recoveryControl':'restored report bytes recover exact original result','networkResponseHashesValid':True,'captureFiles':{str(p.relative_to(capture)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(capture.rglob('*')) if p.is_file() and p.name!='.DS_Store'},'limitations':'Runs from the same public job; not asserted consecutive. Artifact discovery is scoped to enumerated XML; parser uncertainty remains in outputs. Downloaded original capture remains ignored, outside Git.'}
(a.out/'real-capture-audit.json').write_text(json.dumps(manifest,indent=2)+'\n');print('PASS: real capture equals offline replay and both Python checkers; tamper/recovery and response hashes pass.')
