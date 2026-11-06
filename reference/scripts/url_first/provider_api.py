"""Generic recorded-provider SDK. No classifications, manifests or answers."""
import base64,hashlib,json,time
from pathlib import Path

def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def digest(b):return hashlib.sha256(b).hexdigest()
def record(event):
 state=Path('.state');state.mkdir(exist_ok=True)
 with (state/'provider-events.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
class Provider:
 def __init__(self):
  self.root=Path(json.loads(Path(__file__).with_name('provider-config.json').read_text())['recording']);self.catalog=json.loads((self.root/'catalog.json').read_text())
 def list_page(self,url,token=None):
  t=time.monotonic()
  if url not in self.catalog['runs']:raise ValueError('unrecorded_run_url')
  pages=json.loads((self.root/self.catalog['runs'][url]).read_text());index=0 if token is None else next(i+1 for i,p in enumerate(pages[:-1]) if p.get('nextPageToken')==token)
  page=pages[index];record(dict(operation='list',url=url,token=token,bytes=len(canonical(page)),seconds=time.monotonic()-t));return page
 def list_all(self,url):
  pages=[];token=None;seen=set()
  while True:
   page=self.list_page(url,token);pages.append(page);token=page.get('nextPageToken')
   if not token:return pages
   if token in seen:raise ValueError('pagination_cycle')
   seen.add(token)
 def download(self,item):
  t=time.monotonic();key=digest(canonical([item['name'],item['generation']]));entry=self.catalog['objects'].get(key)
  if entry is None:raise ValueError('unrecorded_object')
  if 'error' in entry:record(dict(operation='download',name=item['name'],error=entry['error'],seconds=time.monotonic()-t));raise ValueError(entry['error'])
  state=Path('.state/downloads');state.mkdir(parents=True,exist_ok=True);path=state/key;hit=path.exists();raw=path.read_bytes() if hit else (self.root/entry['path']).read_bytes()
  if len(raw)!=int(item['size']) or base64.b64encode(hashlib.md5(raw).digest()).decode()!=item['md5Hash']:raise ValueError('provider_integrity')
  if not hit:path.write_bytes(raw)
  record(dict(operation='download',name=item['name'],generation=item['generation'],cacheHit=hit,bytes=len(raw),seconds=time.monotonic()-t));return raw
