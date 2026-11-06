"""Research-only JUnit full/overview/fetch interface using pinned junitparser.

One parser and one fact model serve both evaluated workflows. No generated
summaries or diagnostic inference. References require the request SHA-256.
"""
import argparse,hashlib,json,sys
from collections import defaultdict
from pathlib import Path
from junitparser import JUnitXml
INPUT_LIMIT=2*1024*1024
OUTPUT_LIMIT=128*1024

def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def analyze(raw):
 if len(raw)>INPUT_LIMIT:raise ValueError('input_budget_exceeded')
 request=json.loads(raw)
 if request.get('format','junit')!='junit':raise ValueError('unsupported_format')
 xml=request.get('xml')
 if not isinstance(xml,str):raise ValueError('missing_xml')
 if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():raise ValueError('entity_declarations_forbidden')
 document=JUnitXml.fromstring(xml.encode());notes=[];unknown=[];groups={};attempts=defaultdict(list)
 counts=dict(attempts=0,passed=0,failure=0,error=0,skipped=0);nonpassing=[];attachments=[]
 def visit(node,path,location=None):
  if node.tag=='testsuite':path=path+[node.get('name','unnamed')]
  if node.tag in ('testsuite','testsuites'):
   location=dict(phase='suite',identity='/'.join(path))
   if node.get('tests') is not None:
    try:
     if int(node.get('tests'))!=sum(1 for _ in node.iter('testcase')):notes.append('declared_count_mismatch')
    except ValueError:notes.append('invalid_declared_count')
  if node.tag=='testcase':
   identity='/'.join(path+[node.get('classname',''),node.get('name','')]);location=dict(phase='testcase',identity=identity)
   if any('/' in v for v in path+[node.get('classname',''),node.get('name','')]):unknown.append('ambiguous_slash_identity')
   state=next((s for s in ('error','failure','skipped') if any(c.tag==s for c in node)),'passed')
   counts['attempts']+=1;counts[state]+=1
   attempts[(tuple(path),node.get('classname',''),node.get('name',''))].append((node.get('attempt'),state,identity))
   if state!='passed':nonpassing.append(dict(identity=identity,state=state))
  if node.tag in ('failure','error','skipped'):
   detail=dict(kind=node.tag,exceptionType=node.get('type',''),message=node.get('message',''),text=node.text or '')
   ref=digest(canonical(detail));g=groups.setdefault(ref,dict(id=ref,**detail,locations=[]));g['locations'].append(location)
   if len(node):unknown.append('nested_diagnostic_markup')
   return
  if node.tag=='attachment':attachments.append(node.get('path',''));return
  allowed={'testsuite','testsuites','testcase','failure','error','skipped','attachment','properties','system-out','system-err'}
  for child in node:
   if child.tag in ('properties','system-out','system-err'):continue
   if child.tag not in allowed:unknown.append('unrecognized_element:'+str(child.tag));continue
   visit(child,path,location)
 visit(document._elem,[])
 flaky=[]
 for rows in attempts.values():
  if len(rows)<2:continue
  ids=[r[0] for r in rows]
  if any(x is None or not x.isascii() or not x.isdigit() for x in ids) or len(set(map(int,ids)))!=len(ids):notes.append('ambiguous_retry');continue
  rows.sort(key=lambda x:int(x[0]))
  if rows[-1][1]=='passed' and any(r[1] in ('error','failure') for r in rows[:-1]):flaky.append(rows[-1][2])
 if not counts['attempts'] or request.get('interrupted'):notes.append('interrupted_or_no_tests')
 diagnostics=[]
 for g in groups.values():
  g['occurrences']=len(g['locations']);g['locations']=sorted(g['locations'],key=lambda x:(x['phase'],x['identity']));diagnostics.append(g)
 diagnostics.sort(key=lambda g:g['id'])
 return dict(sourceSha256=digest(raw),status='incomplete' if notes else 'ok',counts=counts,
  nonpassing=sorted(nonpassing,key=lambda x:(x['identity'],x['state'])),flaky=sorted(set(flaky)),
  attachments=sorted(set(attachments)),diagnostics=diagnostics,
  coverage=dict(structureComplete=not unknown,sourceFullyRead=True,truncated=False,unresolved=sorted(set(unknown))),limitations=sorted(set(notes)))

def respond(raw,action,ref=None,source_sha=None):
 data=analyze(raw)
 if action=='fetch':
  if source_sha!=data['sourceSha256']:raise ValueError('source_hash_mismatch')
  match=next((g for g in data['diagnostics'] if g['id']==ref),None)
  if match is None:raise ValueError('unknown_diagnostic_id')
  return dict(sourceSha256=data['sourceSha256'],diagnostic=match,coverage=data['coverage'])
 if action=='overview':
  for g in data['diagnostics']:
   message=g.pop('message');text=g.pop('text');g.update(messagePreview=message[:160],messageCharacters=len(message),textCharacters=len(text),detailsOmitted=True)
 data['coverage']['diagnosticBodiesIncluded']=action=='full'
 return data

def main():
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('action',choices=['full','overview','fetch']);p.add_argument('--id');p.add_argument('--sha');a=p.parse_args()
 try:
  with Path(a.source).open('rb') as stream:raw=stream.read(INPUT_LIMIT+1)
  result=respond(raw,a.action,a.id,a.sha);out=canonical(result)
  if len(out)>OUTPUT_LIMIT:raise ValueError('output_budget_exceeded; inspect source or use a narrower diagnostic fetch')
 except Exception as e:
  print(json.dumps(dict(error=str(e),coverage=dict(structureComplete=False,truncated=False,sourceFullyRead=False))));return 2
 print(out.decode());return 0
if __name__=='__main__':sys.exit(main())
