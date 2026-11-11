"""Compare current Go and the frozen Python search on all 16 labeled logs."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT/'evidence/build-logs'
def read(path):
    return json.loads(path.read_bytes())

def check(ok, message):
    if not ok:
        raise ValueError(message)

baseline = ROOT/'tools/search_log.py'
check(hashlib.sha256(baseline.read_bytes()).hexdigest() ==
      read(E/'density-pass/freeze.json')['hashes']['tools/search_log.py'], 'baseline drift')
rows = []
for suite, cache, old in [('projects','log-projects','linked-diagnostic'), ('holdout','log-holdout','linked-diagnostic'),
                         ('verification','log-verification','linked-diagnostic'), ('density-pass','log-density','results')]:
    prior = {r['id']:r['results'] for r in read(E/suite/(old+'.json'))}
    for c in read(E/suite/'cases.json'):
        path = ROOT/'.artifacts'/cache/c['id']
        data = path.read_bytes()
        check(hashlib.sha256(data).hexdigest()==c['sha256'], 'archive drift')
        lines = data.split(b'\n')
        row = dict(suite=suite,id=c['id'],groups=len(c['evidenceGroups']))
        for tool, command in [('go',[Path(sys.argv[1]).resolve(),'log-context']), ('python',[sys.executable,baseline])]:
            raw = json.loads(subprocess.check_output([*command,path,c['literal']]))
            shown = set()
            for block in raw['excerpts'] + raw.get('related',[]):
                for n,text in enumerate(block['lines'],block['startLine']):
                    check(1<=n<=len(lines) and lines[n-1].removesuffix(b'\r')==text.encode(),'citation drift')
                    shown.add(n)
            groups = c['evidenceGroups']
            missed = [g for g in groups if shown.isdisjoint(g)]
            extra = shown.difference(*groups)
            previous = prior[c['id']][tool]
            if tool=='python':
                check(sorted(shown)==previous['shownLines'] and missed==previous['missedGroups'] and
                      sorted(extra)==previous['extraLines'], 'baseline result drift')
            row[tool] = dict(found=len(groups)-len(missed),extra=len(extra),missed=missed,
                             shown=sorted(shown),added=sorted(shown-set(previous['shownLines'])),
                             removed=sorted(set(previous['shownLines'])-shown),status=raw['status'],
                             coverage=raw['coverage'],skipped=raw.get('skippedLines',[]))
            if tool=='go':
                row['previousGo']=dict(found=len(groups)-len(previous['missedGroups']),extra=len(previous['extraLines']))
        rows.append(row)
print(json.dumps(rows,indent=2))
