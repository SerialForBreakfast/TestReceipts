"""Research URL integration: discover, capture, manifest, then ready query."""
import json,sys
from pathlib import Path
from provider_api import Provider,canonical,digest
from discovery import harvest
from manifest_api import write_manifest
from ready_query import query

def inspect(urls):
 if len(urls)!=2:raise ValueError('two_run_urls_required')
 provider=Provider();paths=[]
 for url in urls:
  dest=Path('.state/captured')/digest(url.encode());dest.mkdir(parents=True,exist_ok=True);pages=provider.list_all(url);build=url.rstrip('/').split('/')[-1]
  result=harvest(pages,lambda item,download_url:provider.download(item),dest,build)
  paths.append(write_manifest(url,pages,result,dest/'manifest.json'))
 return query(paths)
if __name__=='__main__':
 try:print(canonical(inspect(sys.argv[1:])).decode())
 except Exception as e:print(json.dumps(dict(error=str(e),complete=False)));sys.exit(2)
