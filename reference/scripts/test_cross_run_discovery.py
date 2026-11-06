import base64,hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'cross_run'))
from unittest.mock import patch
from discovery import classify,harvest,xml_candidates,MAX_XML
class Discovery(unittest.TestCase):
 def item(self,name,raw):return dict(name=name,size=str(len(raw)),generation='1',md5Hash=base64.b64encode(hashlib.md5(raw).digest()).decode())
 def test_generic_ginkgo_and_uppercase_names(self):
  raw=b'<testsuites><testsuite><testcase name="x"/></testsuite></testsuites>'
  with tempfile.TemporaryDirectory() as d:
   items=[self.item(n,raw) for n in ['artifacts/ginkgo/report.xml','TEST-results.XML','junit.xml']];r=harvest([dict(items=items)],lambda i,u:raw,d,'build')
   self.assertTrue(r['discoveryComplete']);self.assertEqual(len(r['sources']),3);self.assertEqual([x['testcaseRecords'] for x in r['discovery']],[1,1,1])
 def test_filename_does_not_override_content(self):
  raw=b'<coverage/>'
  with tempfile.TemporaryDirectory() as d:
   r=harvest([dict(items=[self.item('junit.xml',raw)])],lambda i,u:raw,d,'build');self.assertEqual(r['sources'],[]);self.assertEqual(r['discovery'][0]['disposition'],'non-junit');self.assertTrue(r['discoveryComplete']);self.assertEqual(len(list(Path(d).rglob('*.xml'))),1)
 def test_empty_junit_kept(self):self.assertEqual(classify(b'<testsuite/>')['disposition'],'junit')
 def test_malformed_unresolved(self):self.assertEqual(classify(b'<testsuite>')['disposition'],'blocked')
 def test_namespaced_unresolved(self):self.assertEqual(classify(b'<testsuite xmlns="urn:x"/>')['disposition'],'blocked')
 def test_wrapped_junit_unresolved(self):self.assertEqual(classify(b'<report><testcase/></report>')['disposition'],'blocked')
 def test_entity_rejected(self):self.assertEqual(classify(b'<!DOCTYPE testsuite><testsuite/>')['reason'],'entity_declaration')
 def test_non_utf8_unresolved(self):self.assertEqual(classify(b'\xff')['reason'],'unsupported_encoding')
 def test_provider_mismatch_unresolved(self):
  raw=b'<testsuite/>'
  with tempfile.TemporaryDirectory() as d:
   r=harvest([dict(items=[self.item('x.xml',raw)])],lambda i,u:b'<testsuites/>',d,'build');self.assertFalse(r['discoveryComplete']);self.assertEqual(r['sources'],[])
 def test_no_silent_oversize(self):
  item=self.item('x.xml',b'');item['size']=str(MAX_XML+1)
  with tempfile.TemporaryDirectory() as d:
   r=harvest([dict(items=[item])],lambda i,u:self.fail('must not fetch'),d,'build');self.assertFalse(r['discoveryComplete'])
 def test_collection_budget_is_unresolved(self):
  raw=b'<testsuite/>'
  with tempfile.TemporaryDirectory() as d,patch('discovery.MAX_CAPTURE',len(raw)):
   r=harvest([dict(items=[self.item('a.xml',raw),self.item('b.xml',raw)])],lambda i,u:raw,d,'build');self.assertFalse(r['discoveryComplete']);self.assertEqual(r['discovery'][1]['reason'],'xml_collection_budget_exceeded')
 def test_page_duplicates_rejected(self):
  item=self.item('x.xml',b'')
  with self.assertRaisesRegex(ValueError,'duplicate_listing'):xml_candidates([dict(items=[item]),dict(items=[item])])
 def test_preserve_distinct_objects_with_identical_records(self):
  raw=b'<testsuite><testcase name="same"/></testsuite>'
  with tempfile.TemporaryDirectory() as d:
   r=harvest([dict(items=[self.item('one.xml',raw),self.item('two.xml',raw)])],lambda i,u:raw,d,'build');self.assertEqual(len(r['sources']),2)
if __name__=='__main__':unittest.main()
