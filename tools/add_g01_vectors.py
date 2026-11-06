#!/usr/bin/env python3
"""Create only new G01 development vectors; never overwrite golden outputs."""
import argparse,base64,hashlib,json,sys
from pathlib import Path
from xml.sax.saxutils import escape,quoteattr
from reference_cli import compare
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'reference/scripts/url_first'),str(ROOT/'reference/scripts/test_scale')]
from reference import expected
canonical=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
urls=json.loads((ROOT/'testdata/cases/changes/request.json').read_text())['urls']
body='🙂é<&>"\\\n\t\u2028\u2029'+'界'*510
cases={
 'xml-text':[[],[b'<testsuite><testcase><failure message="a\tb\nc\r\nd">pre<![CDATA[<raw>]]><!--comment-->tail&#13;end&amp;</failure></testcase></testsuite>']],
 'unicode-added':[[],[f'<testsuite><testcase name="unicode"><failure type="例" message={quoteattr(body[:14])}>{escape(body)}</failure></testcase></testsuite>'.encode()]],
 'suite-errors':[[b'<testsuite tests="0"><error type="Setup">suite setup failed</error></testsuite>'],[b'<testsuite tests="1"><error>teardown</error><testcase name="ok"/></testsuite>']],
 'retries':[[b'<testsuite><testcase name="a" attempt="1"><failure>retry</failure></testcase><testcase name="a" attempt="2"/></testsuite>'],[b'<testsuite tests="3"><testcase name="a"><failure>retry</failure></testcase><testcase name="a"/><testcase name="precedence"><skipped/><failure/><error/></testcase></testsuite>']],
 'identity-and-counts':[[b'<testsuite name="a/b" tests="9"><testcase classname="c/d" name="x"/></testsuite>'],[b'<testsuite tests="bad"><testcase name="x"/><testcase name="x" attempt="00"/><testcase name="x" attempt="0"/></testsuite>']],
 'unsupported-constructs':[[b'<wrapper><testsuite><testcase/></testsuite></wrapper>'],[b'<testsuite><testcase/><unknown/><attachment path="a"/></testsuite>']],
}
p=argparse.ArgumentParser();p.add_argument('--case',choices=cases);args=p.parse_args()
for name,runs in cases.items():
 if args.case and name!=args.case:continue
 target=ROOT/'testdata/cases'/name
 if target.exists():raise SystemExit(f'Refusing to overwrite {name}')
 target.mkdir();(target/'objects').mkdir();catalog={'runs':{},'objects':{}}
 for i,docs in enumerate(runs):
  items=[]
  for n,raw in enumerate(docs):
   name=f'logs/test/{100*(i+1)}/artifacts/generic-{n}.xml';key=hashlib.sha256(canonical([name,'1'])).hexdigest();path=f'objects/{key}.xml';(target/path).write_bytes(raw)
   items.append(dict(name=name,generation='1',size=str(len(raw)),md5Hash=base64.b64encode(hashlib.md5(raw).digest()).decode()));catalog['objects'][key]={'path':path}
  path=f'pages-{i}.json';(target/path).write_text(json.dumps([{'items':items}],indent=2)+'\n');catalog['runs'][urls[i]]=path
 (target/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n');(target/'request.json').write_text(json.dumps({'urls':urls,'kind':'G01 development vector'},indent=2)+'\n')
 result=compare(target,urls);other=expected(target,urls)
 assert result==other, target
 (target/'expected.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
# Canonical vectors include control characters that XML itself cannot represent.
values=[{'kind':'failure','exceptionType':'例','message':'"\\\b\f\n\r\t\x00\x1f<&>','text':'🙂\u2028\u2029é'},{'z':None,'a':[True,False,0,-3,'/'] }]
(ROOT/'testdata/canonical-vectors.json').write_text(json.dumps([{'value':v,'utf8Hex':canonical(v).hex(),'sha256':hashlib.sha256(canonical(v)).hexdigest()} for v in values],ensure_ascii=False,indent=2)+'\n')
print('Created independently checked development pairs and 2 canonical vectors.')
