#!/usr/bin/env python3
"""Recreate small development fixtures; never call them held-out evaluation data."""
import base64,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference/scripts/url_first'))
sys.path.insert(0,str(ROOT/'reference/scripts/test_scale'))
from reference import expected
from reference_cli import compare
canonical=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
urls=['https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100','https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200']
cases={
 'changes':[[b'<testsuite name="s"><testcase name="old"><failure type="X" message="old">old diagnostic</failure></testcase><testcase name="shared"><error>shared</error></testcase></testsuite>'],[b'<testsuite name="s"><testcase name="new"><failure type="X" message="new">new diagnostic</failure></testcase><testcase name="shared"><error>shared</error></testcase><testcase name="pass"/><testcase name="skip"><skipped/></testcase></testsuite>']],
 'empty':[[],[]],
 'malformed':[[b'<testsuite'],[b'<testsuite']],
 'non-junit':[[b'<config/>'],[b'<config/>']],
 'namespace':[[b'<testsuite xmlns="urn:test"/>'],[b'<testsuite xmlns="urn:test"/>']],
 'entities':[[b'<!DOCTYPE testsuite><testsuite/>'],[b'<!DOCTYPE testsuite><testsuite/>']],
 'unicode':[[('<testsuite><testcase name="caf\u00e9"><failure type="X" message="&lt;&amp;&gt;">'+('🙂\n'*300)+'</failure></testcase></testsuite>').encode()],[]],
 'pagination':[[b'<testsuite><testcase name="same"><failure>repeat</failure></testcase></testsuite>']*2,[b'<testsuite><testcase name="same"><failure>repeat</failure></testcase></testsuite>']*2],
 'upstream-parser-only':[[ (ROOT/'testdata/upstream/junit-report-errror-details.xml').read_bytes() ],[(ROOT/'testdata/upstream/paintroid-junit-report.xml').read_bytes()]],
}
for name,contents in cases.items():
 target=ROOT/'testdata/cases'/name
 if target.exists():raise SystemExit('Fixture directory exists; use a new destination or explicitly review regeneration.')
 target.mkdir(parents=True);cat=dict(runs={},objects={})
 for i,docs in enumerate(contents):
  items=[]
  for n,raw in enumerate(docs):
   obj=f'logs/test/{100*(i+1)}/artifacts/generic-{n}.xml';item=dict(name=obj,generation='1',size=str(len(raw)),md5Hash=base64.b64encode(hashlib.md5(raw).digest()).decode());items.append(item)
   key=hashlib.sha256(canonical([obj,'1'])).hexdigest();path=f'objects/{key}.xml';(target/'objects').mkdir(exist_ok=True);(target/path).write_bytes(raw);cat['objects'][key]=dict(path=path)
  pages=[dict(items=items)] if name!='pagination' else [dict(items=items[:1],nextPageToken='next'),dict(items=items[1:])]
  path=f'pages-{i}.json';(target/path).write_text(json.dumps(pages,indent=2)+'\n');cat['runs'][urls[i]]=path
 (target/'catalog.json').write_text(json.dumps(cat,indent=2)+'\n')
 (target/'request.json').write_text(json.dumps(dict(urls=urls,kind='development fixture; not real consecutive runs'),indent=2)+'\n')
 result=compare(target,urls);assert result==expected(target,urls),name
 (target/'expected.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print('Created and independently checked',len(cases),'development pairs.')
