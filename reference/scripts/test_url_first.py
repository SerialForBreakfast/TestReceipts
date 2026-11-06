"""URL-entry invariants with small isolated provider recordings."""
import base64,hashlib,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'scripts/url_first';sys.path.insert(0,str(ROOT/'scripts/test_scale'));sys.path.insert(0,str(P));from reference import expected
from parser_profile import install
canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
class URLFirst(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.work=self.root/'work';self.work.mkdir();install(self.work);
  for name in ['provider_api.py','manifest_api.py','ready_query.py','inspect_urls.py']:shutil.copy2(P/name,self.work/name)
  shutil.copy2(ROOT/'scripts/cross_run/discovery.py',self.work/'discovery.py');self.recording=self.root/'recording';self.recording.mkdir();self.urls=['https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100','https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200'];self.cat=dict(runs={},objects={})
 def tearDown(self):self.tmp.cleanup()
 def configure(self,contents,missing=False,paginate=False):
  for i,url in enumerate(self.urls):
   items=[]
   for n,raw in enumerate(contents[i]):
    name=f'logs/test/{100*(i+1)}/artifacts/generic-{n}.xml';item=dict(name=name,generation='1',size=str(len(raw)),md5Hash=base64.b64encode(hashlib.md5(raw).digest()).decode());items.append(item);key=hashlib.sha256(canon([name,'1'])).hexdigest();(self.recording/key).write_bytes(raw);self.cat['objects'][key]=dict(error='captured unavailable') if missing else dict(path=key)
   pages=[dict(items=items)]
   if paginate:pages=[dict(items=items[:1],nextPageToken='next'),dict(items=items[1:])]
   name=f'pages-{i}.json';(self.recording/name).write_text(json.dumps(pages));self.cat['runs'][url]=name
  (self.recording/'catalog.json').write_text(json.dumps(self.cat));(self.work/'provider-config.json').write_text(json.dumps(dict(recording=str(self.recording))))
 def run_query(self):
  p=subprocess.run([sys.executable,'-B','inspect_urls.py',*self.urls],cwd=self.work,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);out=json.loads(p.stdout);self.assertEqual(out,expected(self.recording,self.urls));return out
 def test_generic_names_and_pagination(self):
  self.configure([[b'<testsuite><testcase name="a"/></testsuite>']*2,[b'<testsuite><testcase name="a"><failure>bad</failure></testcase></testsuite>']*2],paginate=True);x=self.run_query();self.assertEqual([r['includedReports'] for r in x['runs']],[2,2]);self.assertEqual(x['change']['newOccurrences'],2);events=[json.loads(l) for l in (self.work/'.state/provider-events.jsonl').read_text().splitlines()];self.assertEqual(sum(e['operation']=='list' for e in events),4)
 def test_no_xml_is_not_passed_tests(self):
  self.configure([[],[]]);x=self.run_query();self.assertTrue(x['runs'][0]['artifactComplete']);self.assertFalse(x['runs'][0]['parserCoverage']['complete']);self.assertEqual(x['runs'][0]['counts']['attempts'],0)
 def test_non_junit_accounted(self):
  self.configure([[b'<config/>'],[b'<config/>']]);x=self.run_query();self.assertEqual(x['runs'][0]['excludedObjects'][0]['reason'],'non_junit_xml_root')
 def test_malformed_xml_not_silently_dropped(self):
  self.configure([[b'<testsuite'],[b'<testsuite']]);x=self.run_query();self.assertFalse(x['runs'][0]['artifactComplete']);self.assertEqual(x['runs'][0]['unresolvedObjects'][0]['reason'],'malformed_xml')
 def test_unavailable_object_blocks_completeness(self):
  self.configure([[b'<testsuite/>'],[b'<testsuite/>']],missing=True);x=self.run_query();self.assertFalse(x['runs'][1]['artifactComplete'])
 def test_download_and_parser_cache_reuse(self):
  self.configure([[b'<testsuite><testcase/></testsuite>'],[b'<testsuite><testcase/></testsuite>']]);self.run_query();self.run_query();ev=[json.loads(l) for l in (self.work/'.state/provider-events.jsonl').read_text().splitlines()];self.assertEqual(sum(e.get('cacheHit',False) for e in ev),4)
 def test_provider_tamper_rejected(self):
  self.configure([[b'<testsuite/>'],[b'<testsuite/>']]);entry=next(iter(self.cat['objects'].values()));(self.recording/entry['path']).write_bytes(b'bad');p=subprocess.run([sys.executable,'-B','inspect_urls.py',*self.urls],cwd=self.work,capture_output=True,text=True);x=json.loads(p.stdout);self.assertFalse(x['runs'][0]['artifactComplete']);self.assertEqual(x['runs'][0]['unresolvedObjects'][0]['reason'],'acquisition_error')
if __name__=='__main__':unittest.main()
