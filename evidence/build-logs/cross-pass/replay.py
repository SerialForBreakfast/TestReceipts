"""Run from any directory. --fetch restores missing public archives."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
cache = ROOT/'.artifacts/log-cross'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fetch', action='store_true')
args = parser.parse_args()
cache.mkdir(parents=True, exist_ok=True)
freeze = json.loads((HERE/'freeze.json').read_text())
for name, digest in freeze['hashes'].items():
    if not name.startswith('.artifacts/'):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'frozen source changed: {name}')
binary = cache/'testreceipts'
subprocess.run([ROOT/'tools/go','build','-o',binary,'./cmd/testreceipts'],cwd=ROOT,check=True)
cases = json.loads((HERE/'cases.json').read_text())
if [{k:c[k] for k in ('id','job','url')} for c in cases] != freeze['sources']:
    raise ValueError('selection changed')
urls = {c['url'] for c in freeze['excluded']}
hashes = {c['sha256'] for c in freeze['excluded']}
rows = []
for c in cases:
    path = cache/c['id']
    if args.fetch and not path.exists():
        subprocess.run(['curl','-fsSL','--max-time','90','--max-filesize','100000000',c['url'],'-o',path],check=True)
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != c['sha256'] or digest in hashes or c['url'] in urls:
        raise ValueError('source changed or reused')
    hashes.add(digest)
    urls.add(c['url'])
    lines = data.split(b'\n')
    row = {'id':c['id']}
    for tool, cmd in [('go',[binary,'log-context']),('python',[sys.executable,ROOT/'tools/search_log.py'])]:
        raw = json.loads(subprocess.check_output([*cmd,path,c['literal']]))
        shown = set()
        for block in raw['excerpts'] + raw.get('related',[]):
            for n,text in enumerate(block['lines'],block['startLine']):
                if not 1<=n<=len(lines) or lines[n-1].removesuffix(b'\r') != text.encode():
                    raise ValueError('invalid source citation')
                shown.add(n)
        missed = [label for label,g in zip(c['labels'],c['evidenceGroups']) if shown.isdisjoint(g)]
        row[tool] = dict(status=raw['status'],coverage=raw['coverage'],matches=raw['matchedLines'],
                         missed=missed,shown=sorted(shown),extra=sorted(shown.difference(*c['evidenceGroups'])))
    rows.append(row)
print(json.dumps(rows,indent=2))
