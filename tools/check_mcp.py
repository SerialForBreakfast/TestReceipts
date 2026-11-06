#!/usr/bin/env python3
"""Deterministic stdio MCP/CLI parity and wire overhead audit; no model calls."""
import argparse,json,queue,subprocess,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--real-capture',type=Path);p.add_argument('--live',action='store_true');a=p.parse_args();binary=a.binary.resolve();a.out.mkdir(parents=True,exist_ok=True)
class Client:
 def __init__(self,root):
  self.process=subprocess.Popen([str(binary),'mcp',str(root)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1);self.q=queue.Queue();self.id=0
  def reader():
   for line in self.process.stdout:self.q.put(line)
  self.thread=threading.Thread(target=reader,daemon=True);self.thread.start()
  reply,_,_=self.call('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'independent-python-wire-client','version':'1'}});assert reply['result']['protocolVersion']=='2025-11-25'
  self.process.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');self.process.stdin.flush()
 def call(self,method,params=None):
  self.id+=1;raw=json.dumps({'jsonrpc':'2.0','id':self.id,'method':method,'params':params or {}});start=time.perf_counter();self.process.stdin.write(raw+'\n');self.process.stdin.flush();line=self.q.get(timeout=360);value=json.loads(line);assert value['id']==self.id,(self.id,value);return value,round(time.perf_counter()-start,6),len(line.encode())
 def close(self):
  self.process.stdin.close()
  try:self.process.wait(timeout=30)
  except subprocess.TimeoutExpired:self.process.kill();raise
  assert self.process.returncode==0;assert not self.process.stderr.read();self.thread.join(timeout=2);assert self.q.empty(),'unsolicited stdout'
client=Client(ROOT);rows=[]
try:
 result,_,_=client.call('tools/list');assert len(result['result']['tools'])==2
 cases=sorted((ROOT/'testdata/cases').iterdir())+[ROOT/'testdata/live/partial-listing']
 if a.real_capture:cases.append(a.real_capture.resolve())
 for case in cases:
  if (case/'request.json').exists():urls=json.loads((case/'request.json').read_text())['urls']
  else:urls=[r['url'] for r in json.loads((case/'comparison.json').read_text())['runs']]
  start=time.perf_counter();cli=subprocess.run([str(binary),'compare-recording',str(case),*urls],capture_output=True,text=True,check=True,timeout=30);cli_seconds=round(time.perf_counter()-start,6);assert not cli.stderr
  response,elapsed,wire=client.call('tools/call',{'name':'compare_recording','arguments':{'recording':case.relative_to(ROOT).as_posix(),'beforeUrl':urls[0],'afterUrl':urls[1]}});value=response['result'];assert value['isError'] is False;assert value['structuredContent']==json.loads(cli.stdout)==json.loads(value['content'][0]['text']);assert value['content'][1]['type']=='resource_link'
  rows.append({'case':case.relative_to(ROOT).as_posix(),'factsEqual':True,'cliOutputBytes':len(cli.stdout.encode()),'mcpWireResponseBytes':wire,'mcpEnvelopeExtraBytes':wire-len(cli.stdout.encode()),'cliWallSeconds':cli_seconds,'mcpWallSeconds':elapsed})
 value,_,_=client.call('tools/call',{'name':'unknown','arguments':{}});assert value['error']['code']==-32602
 value,_,_=client.call('tools/call',{'name':'compare_recording','arguments':{'recording':'../escape','beforeUrl':urls[0],'afterUrl':urls[1]}});assert value['result']['isError'] is True
finally:client.close()
live=None
if a.live:
 if not a.real_capture:raise SystemExit('--live requires --real-capture to select already-known public URLs')
 root=ROOT/'.artifacts';capture='g04-mcp-live';client=Client(root)
 try:
  reply,elapsed,wire=client.call('tools/call',{'name':'compare_live','arguments':{'capture':capture,'beforeUrl':urls[0],'afterUrl':urls[1]}});value=reply['result'];assert value['isError'] is False,value
  replay,_,_=client.call('tools/call',{'name':'compare_recording','arguments':{'recording':capture,'beforeUrl':urls[0],'afterUrl':urls[1]}});assert replay['result']['structuredContent']==value['structuredContent'];cli=subprocess.run([str(binary),'compare-recording',str(root/capture),*urls],capture_output=True,text=True,check=True);assert json.loads(cli.stdout)==value['structuredContent']
  live={'capture':'.artifacts/'+capture,'liveAndMCPReplayAndCLIEqual':True,'comparisonComplete':value['structuredContent']['comparisonComplete'],'wallSeconds':elapsed,'mcpWireResponseBytes':wire}
 finally:client.close()
report={'protocol':'2025-11-25 legacy stdio; modern 2026 stateless profile not implemented','client':'independent Python standard-library JSON-RPC harness; not a third-party-host integration test','modelCalls':0,'comparisons':rows,'live':live,'validationErrors':'unknown tool and traversal rejected','measurementLimits':'Single observations; MCP process already initialized, CLI includes process launch; caches uncontrolled. Bytes are protocol overhead, not agent token savings.'}
(a.out/'mcp-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(f'PASS: {len(rows)} MCP/CLI comparisons; live tool checked={live is not None}; no model calls.')
