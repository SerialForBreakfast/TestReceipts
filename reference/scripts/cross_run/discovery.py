"""Content-based discovery for XML objects in captured CI listings.

The claim is bounded to enumerated .xml objects, not archives or extensionless
files. Ambiguous XML is unresolved, never silently classified as irrelevant.
"""
import base64,hashlib,json,urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
MAX_XML=16*1024*1024
MAX_CAPTURE=32*1024*1024
BASE='https://storage.googleapis.com/kubernetes-ci-logs/'

def xml_candidates(pages):
    items={}
    for page in pages:
        for item in page.get('items',[]):
            if not item['name'].lower().endswith('.xml'):
                continue
            if item['name'] in items:
                raise ValueError('duplicate_listing_object')
            items[item['name']]=item
    return [items[name] for name in sorted(items)]

def classify(raw):
    if len(raw)>MAX_XML:
        return dict(disposition='blocked',reason='xml_budget_exceeded')
    try:
        text=raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return dict(disposition='blocked',reason='unsupported_encoding')
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        return dict(disposition='blocked',reason='entity_declaration')
    try:
        root=ET.fromstring(raw)
    except ET.ParseError:
        return dict(disposition='blocked',reason='malformed_xml')
    tags=[node.tag for node in root.iter()]
    local=lambda tag:tag.rsplit('}',1)[-1] if isinstance(tag,str) else ''
    if root.tag in ('testsuite','testsuites'):
        if any(isinstance(tag,str) and tag.startswith('{') for tag in tags):
            return dict(disposition='blocked',reason='namespaced_junit_content',rootTag=root.tag)
        return dict(disposition='junit',reason='supported_junit_root',rootTag=root.tag,
                    testcaseRecords=tags.count('testcase'),failureElements=tags.count('failure')+tags.count('error'))
    if any(local(tag) in ('testcase','testsuite','testsuites') for tag in tags):
        return dict(disposition='blocked',reason='unsupported_junit_like_root',rootTag=root.tag)
    return dict(disposition='non-junit',reason='non_junit_xml_root',rootTag=root.tag)

def harvest(pages,read,destination,build,known_paths=None):
    """Capture every candidate and its decision; return accepted source records."""
    destination=Path(destination);known_paths=known_paths or {};ledger=[];sources=[];captured_bytes=0
    for i,item in enumerate(xml_candidates(pages)):
        url=BASE+urllib.parse.quote(item['name'],safe='/')+'?generation='+item['generation']
        row=dict(object=item,url=url)
        if int(item['size'])>MAX_XML:
            row.update(disposition='blocked',reason='xml_budget_exceeded');ledger.append(row);continue
        if captured_bytes+int(item['size'])>MAX_CAPTURE:
            row.update(disposition='blocked',reason='xml_collection_budget_exceeded');ledger.append(row);continue
        try:
            raw=read(item,url)
            if len(raw)!=int(item['size']):raise ValueError('provider_size_mismatch')
            if base64.b64encode(hashlib.md5(raw).digest()).decode()!=item['md5Hash']:raise ValueError('provider_md5_mismatch')
            captured_bytes+=len(raw)
            digest=hashlib.sha256(raw).hexdigest()
            name=known_paths.get(item['name'],f'reports/{build}-discovered-{i:03}.xml')
            path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists() and path.read_bytes()!=raw:raise ValueError('capture_path_collision')
            path.write_bytes(raw);row.update(path=name,sha256=digest,bytes=len(raw),**classify(raw))
            if row['disposition']=='junit':sources.append(dict(path=name,url=url,object=item,sha256=digest,bytes=len(raw),build=build))
        except Exception as error:
            row.update(disposition='blocked',reason='acquisition_error',error=str(error))
        ledger.append(row)
    return dict(sources=sources,discovery=ledger,discoveryComplete=not any(x['disposition']=='blocked' for x in ledger),
                bytes=sum(x['bytes'] for x in sources),failureElements=sum(x.get('failureElements',0) for x in ledger if x['disposition']=='junit'))
