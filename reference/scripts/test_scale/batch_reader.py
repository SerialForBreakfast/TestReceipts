"""Generic bounded per-report API over junitparser; no cross-report query methods."""
import hashlib,json
from pathlib import Path
from single_report import analyze
class Batch:
 def __init__(self,manifest):
  p=Path(manifest).resolve();self.root=p.parent
  with p.open('rb') as f:raw=f.read(1024*1024+1)
  if len(raw)>1024*1024:raise ValueError('manifest_budget_exceeded')
  self.sha=hashlib.sha256(raw).hexdigest();m=json.loads(raw)
  if m.get('version')!=1:raise ValueError('unsupported_manifest_version')
  self.entries=m['reports']
  if len(self.entries)>2048:raise ValueError('report_count_budget_exceeded')
  if len({e['path'] for e in self.entries})!=len(self.entries):raise ValueError('duplicate_report_entry')
  self.bytes=0;self.read=0;self.unknown=set();self.limits=set();self.started=False;self.done=False
 def reports(self):
  if self.started:raise ValueError('iterator_already_consumed')
  self.started=True
  for entry in self.entries:
   path=Path(entry['path'])
   if path.is_absolute() or '..' in path.parts:raise ValueError('out_of_scope_path')
   path=(self.root/path).resolve()
   if not path.is_relative_to(self.root):raise ValueError('out_of_scope_path')
   with path.open('rb') as f:raw=f.read(1024*1024+1)
   if len(raw)>1024*1024:raise ValueError('per_report_budget_exceeded')
   self.bytes+=len(raw)
   if self.bytes>32*1024*1024:raise ValueError('collection_budget_exceeded')
   if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('source_hash_mismatch')
   data=analyze(json.dumps({'xml':raw.decode(),'format':'junit'},ensure_ascii=False).encode());self.read+=1;self.unknown.update(data['coverage']['unresolved']);self.limits.update(data['limitations']);yield data
  self.done=True
 def metadata(self):
  if not self.done:raise ValueError('reports_not_fully_consumed')
  return dict(manifestSha256=self.sha,inputBytes=self.bytes,reportsRead=self.read,coverage=dict(complete=not self.unknown,unresolved=sorted(self.unknown),limitations=sorted(self.limits)))
