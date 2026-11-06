"""Audit-only independent DOM classification and facts from recorded originals."""
import base64,hashlib,json
from pathlib import Path
from xml.dom import minidom
from oracle import collect

def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def classify(raw):
 try:text=raw.decode('utf-8-sig')
 except UnicodeDecodeError:return 'blocked','unsupported_encoding'
 if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():return 'blocked','entity_declaration'
 try:doc=minidom.parseString(raw)
 except Exception:return 'blocked','malformed_xml'
 root=doc.documentElement;nodes=[root]+list(root.getElementsByTagName('*'));known=['testcase','testsuite','testsuites']
 if root.tagName in ['testsuite','testsuites'] and not root.namespaceURI:
  result=('blocked','namespaced_junit_content') if any(n.namespaceURI for n in nodes) else ('junit','supported_junit_root')
 elif any((n.localName or n.tagName) in known for n in nodes):result=('blocked','unsupported_junit_like_root')
 else:result=('non-junit','non_junit_xml_root')
 doc.unlink();return result

def expected(recording,urls):
 recording=Path(recording);catalog=json.loads((recording/'catalog.json').read_text());snapshots=[];groups=[]
 for url in urls:
  pages=json.loads((recording/catalog['runs'][url]).read_text());items=sorted([item for page in pages for item in page.get('items',[]) if item['name'].lower().endswith('.xml')],key=lambda x:x['name']);assert len({i['name'] for i in items})==len(items);rows=[];accepted=[];excluded=[];blocked=[]
  for item in items:
   key=sha(canonical([item['name'],item['generation']]));entry=catalog['objects'][key];digest=None
   if 'error' in entry:kind,reason='blocked','acquisition_error'
   else:
    raw=(recording/entry['path']).read_bytes();assert len(raw)==int(item['size']);assert base64.b64encode(hashlib.md5(raw).digest()).decode()==item['md5Hash'];digest=sha(raw);kind,reason=classify(raw)
   rows.append(dict(name=item['name'],generation=item['generation'],sha256=digest,disposition=kind,reason=reason))
   if kind=='junit':accepted.append(dict(path=entry['path'],sha256=digest))
   elif kind=='non-junit':excluded.append(dict(name=item['name'],reason=reason))
   else:blocked.append(dict(name=item['name'],reason=reason))
  counts,g,n,coverage=collect(recording,accepted);g={k:v for k,v in g.items() if v['kind'] in ['failure','error']};groups.append(g)
  if not accepted:coverage=dict(complete=False,unresolved=['no_junit_reports'],limitations=[])
  snapshots.append(dict(url=url,xmlCandidates=len(items),includedReports=len(accepted),excludedObjects=excluded,unresolvedObjects=blocked,artifactComplete=not blocked,inventorySha256=sha(canonical(rows)),listingSha256=sha(canonical(pages)),inputBytes=n,counts=counts,parserCoverage=coverage,distinctFailures=len(g)))
 before,after=groups;added=sorted(after.keys()-before.keys(),key=lambda k:(-after[k]['occurrences'],k));evidence=[dict(**{k:after[key][k] for k in ['id','kind','exceptionType','message','occurrences']},text=after[key]['text'][:512],totalCharacters=len(after[key]['text'])) for key in added[:3]]
 return dict(runs=snapshots,change=dict(newDistinct=len(added),disappearedDistinct=len(before.keys()-after.keys()),sharedDistinct=len(before.keys()&after.keys()),newOccurrences=sum(after[k]['occurrences'] for k in added)),newEvidence=evidence)
