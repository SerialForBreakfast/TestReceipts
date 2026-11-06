#!/usr/bin/env python3
"""Extract and exercise the matching native package with an empty executable PATH."""
import argparse,json,os,platform,re,shutil,subprocess,tempfile,time
from pathlib import Path
from release import ROOT,unpack,sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--measure',action='store_true');a=p.parse_args()
files,metadata=unpack(a.package);host={'Darwin':'darwin','Linux':'linux','Windows':'windows'}[platform.system()]+'/'+{'arm64':'arm64','aarch64':'arm64','x86_64':'amd64','amd64':'amd64'}[platform.machine().lower()]
if metadata['target']!=host:raise SystemExit(f'Package {metadata["target"]} is not native on {host}')
a.out.mkdir(parents=True,exist_ok=True);rows=[]
with tempfile.TemporaryDirectory(prefix='testreceipts-installed-') as tmp:
 work=Path(tmp)/'Installed TestReceipts 界';work.mkdir();empty=work/'empty-path';empty.mkdir();installed=work/'package';installed.mkdir()
 for name,(raw,mode) in files.items():dest=installed/name;dest.write_bytes(raw);dest.chmod(mode)
 exe=installed/('testreceipts.exe' if platform.system()=='Windows' else 'testreceipts')
 env={k:v for k,v in os.environ.items() if not k.startswith(('GO','PYTHON','DYLD_'))};env['PATH']=str(empty)
 def execute(args,output=None):
  cmd=[str(exe),*args];measure=work/'measurement.txt'
  if a.measure and platform.system()=='Darwin':cmd=['/usr/bin/time','-l','-o',str(measure),*cmd]
  start=time.perf_counter();r=subprocess.run(cmd,cwd=work,env=env,stdout=output or subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30);elapsed=time.perf_counter()-start;rss=None
  if a.measure and measure.exists():
   m=re.search(r'(\d+)\s+maximum resident set size',measure.read_text());rss=int(m.group(1)) if m else None
  return r,elapsed,rss
 r,_,_=execute(['version']);assert r.returncode==0 and r.stdout.strip()==metadata['version'];version_times=[]
 for _ in range(10):
  r,elapsed,_=execute(['version']);assert r.returncode==0;version_times.append(round(elapsed,6))
 for case in sorted((ROOT/'testdata/cases').iterdir()):
  copied=work/('Recorded input '+case.name+' 界');shutil.copytree(case,copied);urls=json.loads((copied/'request.json').read_text())['urls'];args=['compare-recording',str(copied),*urls]
  r,elapsed,rss=execute(args);actual=json.loads(r.stdout);assert r.returncode==0 and r.stderr=='' and actual==json.loads((copied/'expected.json').read_text()),case.name
  (a.out/(case.name+'.json')).write_text(json.dumps(actual,ensure_ascii=False,indent=2)+'\n');rows.append({'case':case.name,'pass':True,'wallSeconds':round(elapsed,6),'maximumResidentSetBytes':rss})
 sample=work/'Recorded input changes 界';urls=json.loads((sample/'request.json').read_text())['urls'];args=['compare-recording',str(sample),*urls]
 output=work/'comparison output 界.json'
 with output.open('w') as stream:r,_,_=execute(args,stream)
 assert r.returncode==0 and json.loads(output.read_text())==json.loads((sample/'expected.json').read_text())
 checks={'extractedArchiveAndExecutablePermissions':'pass','fifteenExactComparisons':'pass','spacesAndUnicodePaths':'pass','outputFileRedirection':'pass','versionStamp':'pass','emptyExecutablePATH':'pass; host still has development runtimes installed'}
 for label,args in [('unknownCommand',['unknown']),('missingRecording',['compare-recording',str(work/'missing'),*urls]),('badArguments',['compare-recording'])]:
  r,_,_=execute(args);assert r.returncode==2 and r.stdout=='' and r.stderr;checks[label]='pass; exit 2, stderr only'
 # Invoke directly for OS permission errors, rather than through the timing wrapper.
 if platform.system()!='Windows':
  exe.chmod(0o644)
  try:subprocess.run([str(exe),'version'],env=env,cwd=work,capture_output=True,timeout=10)
  except PermissionError:checks['missingExecutePermission']='pass; OS rejected execution'
  else:raise AssertionError('execution allowed without execute bit')
  finally:exe.chmod(0o755)
  blocked=sample/'catalog.json';blocked.chmod(0)
  try:
   r,_,_=execute(['compare-recording',str(sample),*urls]);assert r.returncode==2 and r.stdout=='' and r.stderr;checks['unreadableCatalog']='pass; exit 2'
  finally:blocked.chmod(0o644)
  with output.open('r') as readonly:
   # EBADF on stdout is an actual CLI output error, not a shell redirection error.
   r=subprocess.run([str(exe),'compare-recording',str(sample),*urls],env=env,cwd=work,stdout=readonly,stderr=subprocess.PIPE,text=True,timeout=30)
  assert r.returncode==2 and 'Output failed' in r.stderr;checks['unwritableStdout']='pass; exit 2'
 else:checks['POSIXPermissions']='not applicable; Windows ACL checks still required'
 inspections={}
 if platform.system()=='Darwin':
  for label,cmd in [('runtimeLibraries',['/usr/bin/otool','-L',str(exe)]),('codeSignature',['/usr/bin/codesign','-dv','--verbose=4',str(exe)])]:
   r=subprocess.run(cmd,capture_output=True,text=True);text=(r.stdout+r.stderr).replace(str(exe.resolve()),'testreceipts').replace(str(exe),'testreceipts');inspections[label]={'exit':r.returncode,'output':text}
 result={'target':host,'host':platform.platform(),'package':a.package.name,'packageSha256':sha(a.package.read_bytes()),'binarySha256':metadata['binarySha256'],'version':metadata['version'],'checks':checks,'comparisons':rows,'startupVersionWallSeconds':version_times,'inspection':inspections,'limitations':['Existing development host, not a clean machine without runtimes installed','Empty PATH proves no executable runtime lookup; it does not simulate all OS installations','No oldest-supported-OS, downloaded-quarantine/Gatekeeper, notarization, or public install test','This offline package smoke does not validate networking/certificates; inspect separate live evidence','One full-operation observation per case; startup timings include process launch and optional time wrapper; caches uncontrolled']}
 (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(f'PASS: installed {host} package, 15 exact comparisons, CLI/permissions/output checks')
