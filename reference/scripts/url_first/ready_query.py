"""Ready-made two-manifest query; same computation called by the URL adapter."""
import json,sys
from manifest_api import load_manifest
from provider_api import canonical

def groups(reports):
 out={}
 for report in reports:
  for g in report['diagnostics']:
   if g['kind'] not in ['failure','error']:continue
   if g['id'] not in out:out[g['id']]={k:g[k] for k in ['id','kind','exceptionType','message','text']};out[g['id']]['occurrences']=0
   out[g['id']]['occurrences']+=g['occurrences']
 return out

def query(paths):
 data=[load_manifest(p) for p in paths]
 if len(data)!=2:raise ValueError('two_manifests_required')
 snapshots=[];gg=[]
 for d in data:
  g=groups(d['reports']);gg.append(g);snapshots.append(dict(**d['inventory'],inputBytes=d['metadata']['inputBytes'],counts={k:sum(r['counts'][k] for r in d['reports']) for k in ['attempts','passed','failure','error','skipped']},parserCoverage=d['metadata']['coverage'],distinctFailures=len(g)))
 before,after=gg;added=sorted(after.keys()-before.keys(),key=lambda k:(-after[k]['occurrences'],k));evidence=[]
 for key in added[:3]:
  g=after[key];body=g['text'];evidence.append(dict(**{k:g[k] for k in ['id','kind','exceptionType','message','occurrences']},text=body[:512],totalCharacters=len(body)))
 return dict(runs=snapshots,change=dict(newDistinct=len(added),disappearedDistinct=len(before.keys()-after.keys()),sharedDistinct=len(before.keys()&after.keys()),newOccurrences=sum(after[k]['occurrences'] for k in added)),newEvidence=evidence)
if __name__=='__main__':
 try:print(canonical(query(sys.argv[1:])).decode())
 except Exception as e:print(json.dumps(dict(error=str(e),complete=False)));sys.exit(2)
