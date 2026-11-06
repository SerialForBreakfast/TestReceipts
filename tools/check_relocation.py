#!/usr/bin/env python3
"""Validate relocation, a runtime-free native command, and negative controls."""
import argparse,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--go-binary',type=Path,required=True);a=p.parse_args();binary=a.go_binary.resolve()
with tempfile.TemporaryDirectory(prefix='testreceipts-relocation-') as tmp:
 dest=Path(tmp)/'Test Receipts 界';shutil.copytree(ROOT,dest,ignore=shutil.ignore_patterns('.git','.cache','.state','.artifacts','bin','dist','__pycache__','.DS_Store'))
 (dest/'bin').mkdir();exe=dest/'bin'/binary.name;shutil.copy2(binary,exe)
 def verify():return subprocess.run([sys.executable,'-B','tools/verify.py','--go-binary',str(exe)],cwd=dest,text=True,capture_output=True)
 r=verify();assert r.returncode==0,r.stdout+r.stderr
 checks={'relocatedReferenceAndGoParity':'pass','pathWithSpacesAndUnicode':'pass'}
 case=dest/'testdata/cases/changes';urls=json.loads((case/'request.json').read_text())['urls'];expected=json.loads((case/'expected.json').read_text())
 empty=Path(tmp)/'empty-path';empty.mkdir();env=os.environ.copy();env['PATH']=str(empty)
 native=subprocess.run([str(exe),'compare-recording',str(case),*urls],cwd=tmp,env=env,text=True,capture_output=True);assert native.returncode==0 and json.loads(native.stdout)==expected,native.stderr;checks['nativeWithoutGoOrPythonOnPATH']='pass (macOS arm64 only)'
 golden=case/'expected.json';original=golden.read_bytes();modified=json.loads(original);modified['change']['newDistinct']+=1;golden.write_text(json.dumps(modified));r=verify();assert r.returncode!=0;golden.write_bytes(original);checks['alteredGoldenDetected']='pass'
 source=dest/json.loads((dest/'docs/source-provenance.json').read_text())['files'][0]['destination'];original=source.read_bytes();source.write_bytes(original+b'\n');r=verify();assert r.returncode!=0;source.write_bytes(original);checks['alteredFrozenSourceDetected']='pass'
 obj=next((case/'objects').iterdir());obj.write_bytes(b'tampered');r=subprocess.run([str(exe),'compare-recording',str(case),*urls],cwd=tmp,text=True,capture_output=True);assert r.returncode==0;data=json.loads(r.stdout);assert any(not run['artifactComplete'] and run['unresolvedObjects'] for run in data['runs']);checks['alteredOriginalReportDetected']='pass; explicit unresolved acquisition error'
 (ROOT/'evidence/g01/relocation.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
