"""Generic manifest, inventory and per-report APIs shared by every arm."""
import hashlib,json,time
from pathlib import Path
from batch_reader import Batch
from provider_api import canonical,digest,record

def write_manifest(url,pages,result,path):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 value=dict(version=1,previous=[],url=url,reports=[dict(path=x['path'],sha256=x['sha256']) for x in result['sources']],discovery=result['discovery'],listingSha256=digest(canonical(pages)))
 path.write_bytes(canonical(value));return str(path)
def inventory(manifest):
 m=json.loads(Path(manifest).read_text());rows=m['discovery'];entries=sorted([dict(name=x['object']['name'],generation=x['object']['generation'],sha256=x.get('sha256'),disposition=x['disposition'],reason=x['reason']) for x in rows],key=lambda x:x['name'])
 return dict(url=m['url'],xmlCandidates=len(rows),includedReports=sum(x['disposition']=='junit' for x in rows),excludedObjects=sorted([dict(name=x['object']['name'],reason=x['reason']) for x in rows if x['disposition']=='non-junit'],key=lambda x:x['name']),unresolvedObjects=sorted([dict(name=x['object']['name'],reason=x['reason']) for x in rows if x['disposition']=='blocked'],key=lambda x:x['name']),artifactComplete=not any(x['disposition']=='blocked' for x in rows),inventorySha256=digest(canonical(entries)),listingSha256=m['listingSha256'])
def load_manifest(path):
 path=Path(path).resolve();m=json.loads(path.read_text());total=0
 for entry in m['reports']:
  relative=Path(entry['path']);q=(path.parent/relative).resolve()
  if relative.is_absolute() or '..' in relative.parts or not q.is_relative_to(path.parent):raise ValueError('out_of_scope')
  with q.open('rb') as f:raw=f.read(16*1024*1024+1)
  total+=len(raw)
  if len(raw)>16*1024*1024 or total>32*1024*1024:raise ValueError('input_budget')
  if digest(raw)!=entry['sha256']:raise ValueError('source_hash_mismatch')
 key=digest(canonical([m,[(n,digest(Path(__file__).with_name(n).read_bytes())) for n in ['manifest_api.py','single_report.py','batch_reader.py']]]));state=Path('.state/parsed');state.mkdir(parents=True,exist_ok=True);cached=state/key;hit=False
 if cached.exists():
  old=json.loads(cached.read_bytes())
  if digest(canonical(old['data']))==old['sha256']:data=old['data'];hit=True
 if not hit:
  b=Batch(path);reports=list(b.reports());metadata=b.metadata()
  if not reports:metadata['coverage']=dict(complete=False,unresolved=['no_junit_reports'],limitations=[])
  data=dict(inventory=inventory(path),reports=reports,metadata=metadata);cached.write_bytes(canonical(dict(data=data,sha256=digest(canonical(data)))))
 record(dict(operation='parse',cacheHit=hit,reportsParsed=0 if hit else len(data['reports']),validatedSourceBytes=total));return data
