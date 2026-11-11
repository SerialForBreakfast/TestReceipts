"""Build both Go versions, replay all three tools and independently score their raw excerpts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/build-logs'
V = EVIDENCE / 'verification'
SETS = [('projects','log-projects','summary-follow','full-summary'),
        ('holdout','log-holdout','results','full-summary'),
        ('verification','log-verification','previous','results')]


def read(path):
    return json.loads(path.read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_hash(path, expected):
    require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, f'hash mismatch: {path}')


def run(fetch, tmp):
    for name, digest in read(V/'freeze.json')['hashes'].items():
        check_hash(ROOT/name, digest)
    source = ROOT/'cmd/testreceipts/logs.go'
    previous = tmp/'previous.go'
    subprocess.run(['patch','-s','-o',previous,source,V/'previous.patch'],check=True)
    check_hash(previous, read(EVIDENCE/'holdout/freeze.json')['tools']['cmd/testreceipts/logs.go'])
    overlay = tmp/'overlay.json'
    overlay.write_text(json.dumps({'Replace':{str(source):str(previous)}}))
    commands = {'python':[sys.executable, ROOT/'tools/search_log.py']}
    for version, flags in [('previous',['-overlay',overlay]), ('current',[])]:
        binary = tmp/version
        subprocess.run([ROOT/'tools/go','build',*flags,'-o',binary,'./cmd/testreceipts'],cwd=ROOT,check=True)
        commands[version] = [binary,'log-context']
    seen = set()
    totals = {}
    for name, cache, old, new in SETS:
        cases = read(EVIDENCE/name/'cases.json')
        totals[name] = {}
        for version, command in commands.items():
            receipts = read(EVIDENCE/name/((old if version=='previous' else new)+'.json'))
            require([r['id'] for r in receipts]==[c['id'] for c in cases], 'case order or identity')
            found = extra = complete = 0
            for c, saved in zip(cases, receipts):
                path = ROOT/'.artifacts'/cache/c['id']
                if fetch and not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(['curl','-fsSL','--max-time','120','--max-filesize','30000000',c['url'],'-o',path],check=True)
                check_hash(path, c['sha256'])
                if version=='previous':
                    require(c['sha256'] not in seen, 'duplicate log content')
                    seen.add(c['sha256'])
                lines = path.read_bytes().split(b'\n')
                raw = json.loads(subprocess.check_output([*command,path,c['literal']]))
                cited = set()
                for e in raw['excerpts']:
                    for n,text in enumerate(e['lines'], e['startLine']):
                        require(1<=n<=len(lines) and lines[n-1].removesuffix(b'\r')==text.encode(), 'incorrect source citation')
                        cited.add(n)
                groups = c['evidenceGroups']
                require(all(g and all(1<=n<=len(lines) for n in g) for g in groups),'invalid label')
                missed = [g for g in groups if not any(n in cited for n in g)]
                outside = sorted(n for n in cited if not any(n in g for g in groups))
                receipt = saved['results']['python' if version=='python' else 'go']
                actual = [sorted(cited), missed, outside, raw['matchedLines'],raw['status'],raw['coverage']]
                require(actual==[receipt[k] for k in ('shownLines','missedGroups','extraLines','matches','status','coverage')], f'{name}/{c["id"]}/{version}: receipt mismatch')
                found += len(groups)-len(missed)
                extra += len(outside)
                complete += not missed
            totals[name][version] = dict(found=found, extra=extra, complete=complete)
    return totals


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch',action='store_true',help='fetch missing public logs into ignored storage')
    with tempfile.TemporaryDirectory() as directory:
        print(json.dumps(run(parser.parse_args().fetch, Path(directory)),indent=2))
