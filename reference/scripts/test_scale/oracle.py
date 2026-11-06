"""Independent DOM reference for cross-report facts and snapshot diffs."""
import hashlib,json
from pathlib import Path
from xml.dom import minidom

def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def sha(x):return hashlib.sha256(x).hexdigest()
def collect(root,entries):
 counts=dict(attempts=0,passed=0,failure=0,error=0,skipped=0);groups={};input_bytes=0;unresolved=set();limitations=set()
 for entry in entries:
  raw=(root/entry['path']).read_bytes();assert sha(raw)==entry['sha256'];input_bytes+=len(raw);doc=minidom.parseString(raw)
  identities={}
  cases=doc.getElementsByTagName('testcase')
  if not cases:limitations.add('interrupted_or_no_tests')
  for tag in ['testsuite','testsuites']:
   for suite in doc.getElementsByTagName(tag):
    if suite.hasAttribute('tests'):
     try:
      if int(suite.getAttribute('tests'))!=len(suite.getElementsByTagName('testcase')):limitations.add('declared_count_mismatch')
     except ValueError:limitations.add('invalid_declared_count')
  for case in cases:
   parents=[];node=case.parentNode
   while node:
    if getattr(node,'tagName',None)=='testsuite':parents.insert(0,node.getAttribute('name') if node.hasAttribute('name') else 'unnamed')
    node=node.parentNode
   components=tuple(parents+[case.getAttribute('classname'),case.getAttribute('name')])
   if any('/' in x for x in components):unresolved.add('ambiguous_slash_identity')
   identities.setdefault(components,[]).append(case.getAttribute('attempt'))
   tags={c.tagName for c in case.childNodes if c.nodeType==c.ELEMENT_NODE};state=next((x for x in ['error','failure','skipped'] if x in tags),'passed');counts['attempts']+=1;counts[state]+=1
  for ids in identities.values():
   if len(ids)>1 and (any(not x or not x.isascii() or not x.isdigit() for x in ids) or len(set(map(int,ids)))!=len(ids)):limitations.add('ambiguous_retry')
  def visit(n):
   if n.nodeType!=n.ELEMENT_NODE:return
   if n.tagName in ['properties','system-out','system-err']:return
   if n.tagName in ['failure','error','skipped']:
    if any(c.nodeType==c.ELEMENT_NODE for c in n.childNodes):unresolved.add('nested_diagnostic_markup')
    d=dict(kind=n.tagName,exceptionType=n.getAttribute('type'),message=n.getAttribute('message'),text=''.join(x.data for x in n.childNodes if x.nodeType in [x.TEXT_NODE,x.CDATA_SECTION_NODE]));ref=sha(canonical(d));groups.setdefault(ref,dict(id=ref,**d,occurrences=0))['occurrences']+=1;return
   if n.tagName not in ['testsuite','testsuites','testcase','attachment']:unresolved.add('unrecognized_element:'+n.tagName)
   if n.tagName in ['testsuite','testsuites','testcase']:
    for child in n.childNodes:visit(child)
  visit(doc.documentElement);doc.unlink()
 return counts,groups,input_bytes,dict(complete=not unresolved,unresolved=sorted(unresolved),limitations=sorted(limitations))

def expected(path,action,ref=None):
 path=Path(path);spec=json.loads(path.read_text());counts,after,total,coverage=collect(path.parent,spec['reports'])
 def top(groups):return [{k:g[k] for k in ['id','occurrences','kind','exceptionType']} for g in sorted(groups.values(),key=lambda g:(-g['occurrences'],g['id']))[:5]]
 if action=='summary':facts=dict(counts=counts,distinctDiagnostics=len(after),duplicateOccurrences=sum(g['occurrences']-1 for g in after.values()),topGroups=top(after))
 elif action=='changes':
  _,before,prev,old_coverage=collect(path.parent,spec['previous']);total+=prev;coverage=dict(complete=coverage['complete'] and old_coverage['complete'],unresolved=sorted(set(coverage['unresolved']+old_coverage['unresolved'])),limitations=sorted(set(coverage['limitations']+old_coverage['limitations'])));new={k:g for k,g in after.items() if k not in before};facts=dict(newDistinct=len(new),resolvedDistinct=len(set(before)-set(after)),sharedDistinct=len(set(after)&set(before)),newOccurrences=sum(g['occurrences'] for g in new.values()),topNewGroups=top(new))
 else:
  g=after[ref];facts=dict(id=ref,kind=g['kind'],exceptionType=g['exceptionType'],message=g['message'],text=g['text'][:512],offset=0,nextOffset=512 if len(g['text'])>512 else None,totalCharacters=len(g['text']))
 return dict(manifestSha256=sha(path.read_bytes()),inputBytes=total,reportsRead=len(spec['reports'])+(len(spec['previous']) if action=='changes' else 0),coverage=coverage,facts=facts)
