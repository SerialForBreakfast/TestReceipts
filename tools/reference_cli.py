#!/usr/bin/env python3
"""Portable offline reference. Python is for development parity, not the Go release."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference/scripts/url_first'))
from parser_profile import install

def compare(recording,urls):
 with tempfile.TemporaryDirectory(prefix='testreceipts-reference-') as tmp:
  work=Path(tmp);install(work)
  for name in ['inspect_urls.py','manifest_api.py','provider_api.py','ready_query.py']:
   shutil.copyfile(ROOT/'reference/scripts/url_first'/name,work/name)
  shutil.copyfile(ROOT/'reference/scripts/cross_run/discovery.py',work/'discovery.py')
  (work/'provider-config.json').write_text(json.dumps(dict(recording=str(Path(recording).resolve()))))
  p=subprocess.run([sys.executable,'-E','-S','-X','utf8','-B','inspect_urls.py',*urls],cwd=work,text=True,capture_output=True)
  if p.returncode:raise RuntimeError(p.stderr or p.stdout)
  return json.loads(p.stdout)
if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('Usage: python tools/reference_cli.py RECORDING BEFORE_URL AFTER_URL')
 print(json.dumps(compare(sys.argv[1],sys.argv[2:]),indent=2,ensure_ascii=False))
