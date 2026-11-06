#!/usr/bin/env python3
"""Build and package a private release candidate reproducibly, offline."""
import argparse,gzip,hashlib,io,json,os,platform,re,shutil,subprocess,sys,tarfile,tempfile,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGETS=[f'{o}/{a}' for o in ('darwin','linux','windows') for a in ('amd64','arm64')]
PIN='go1.27.3'
ASSETS=['INSTALL.md','NOTICE.txt','LICENSE']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def run(cmd,**kwargs):return subprocess.check_output(cmd,text=True,**kwargs).strip()
def archive(files,base,windows):
 out=io.BytesIO()
 if windows:
  with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for name,(raw,mode) in sorted(files.items()):
    info=zipfile.ZipInfo(base+'/'+name,(1980,1,1,0,0,0));info.create_system=3;info.external_attr=(0o100000|mode)<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw,compresslevel=9)
 else:
  with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0,compresslevel=9) as gz:
   with tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT) as tar:
    for name,(raw,mode) in sorted(files.items()):
     info=tarfile.TarInfo(base+'/'+name);info.size=len(raw);info.mode=mode;info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';tar.addfile(info,io.BytesIO(raw))
 return out.getvalue()
def unpack(path):
 # Verify an exact allowlist before extraction; no links or other filesystem objects.
 if path.suffix=='.zip':
  with zipfile.ZipFile(path) as z:
   entries=[(i.filename,z.read(i),i.external_attr>>16) for i in z.infolist()]
 else:
  with tarfile.open(path) as t:
   entries=[]
   for i in t:
    if not i.isfile():raise ValueError('nonregular_archive_member')
    entries.append((i.name,t.extractfile(i).read(),i.mode))
 names=[n for n,_,_ in entries];bases={n.split('/')[0] for n in names}
 if len(bases)!=1 or len(names)!=len(set(names)):raise ValueError('archive_shape')
 files={}
 for name,raw,mode in entries:
  parts=name.split('/')
  if len(parts)!=2 or parts[0] in ('','.','..') or parts[1] in ('','.','..') or '\\' in name or ':' in name:raise ValueError('archive_path')
  if mode&0o170000 not in (0,0o100000):raise ValueError('archive_member_type')
  files[parts[1]]=(raw,mode&0o777)
 exe='testreceipts.exe' if 'testreceipts.exe' in files else 'testreceipts'
 expected=set(ASSETS+['GO-LICENSE.txt','BUILD.json',exe])
 if set(files)!=expected:raise ValueError('archive_allowlist')
 metadata=json.loads(files['BUILD.json'][0]);binary=files[exe][0]
 if sha(binary)!=metadata['binarySha256'] or len(binary)!=metadata['binaryBytes']:raise ValueError('binary_integrity')
 return files,metadata

def build(args):
 go=Path(args.go).resolve() if args.go else ROOT/'.cache/toolchain/go/bin/go'
 if not go.exists():
  found=shutil.which('go')
  if not found:raise SystemExit('Go toolchain unavailable; use --go PATH')
  go=Path(found).resolve()
 env={k:v for k,v in os.environ.items() if not k.startswith('GO') and k not in ('CGO_ENABLED','CC','CXX')}
 env.update(GOTOOLCHAIN='local',GOENV='off',GOFLAGS='',GOEXPERIMENT='',GOPROXY='off',GOSUMDB='off',GOWORK='off',CGO_ENABLED='0',GOAMD64='v1',GOARM64='v8.0',GOCACHE=str(ROOT/'.cache/release-build'),GOPATH=str(ROOT/'.cache/release-gopath'))
 version=run([str(go),'version'],env=env)
 if version.split()[2]!=PIN:raise SystemExit(f'Expected {PIN}, got {version}')
 if not re.fullmatch(r'v\d+\.\d+\.\d+-[a-zA-Z0-9.\-]+',args.version):raise SystemExit('Only explicit pre-release versions are allowed until public distribution is approved')
 out=args.out.resolve()
 if out.exists():raise SystemExit('Output exists; choose a new empty output directory')
 sources=sorted([ROOT/'go.mod',*ROOT.glob('cmd/**/*.go'),*ROOT.glob('internal/**/*.go')]);source_bytes={str(p.relative_to(ROOT)):p.read_bytes() for p in sources}
 revision=run(['git','rev-parse','HEAD'],cwd=ROOT);dirty=bool(run(['git','status','--porcelain'],cwd=ROOT))
 goroot=Path(run([str(go),'env','GOROOT'],env=env));license_bytes=(goroot/'LICENSE').read_bytes()
 assets={n:(ROOT/n if n=='LICENSE' else ROOT/'release'/n).read_bytes() for n in ASSETS};assets['GO-LICENSE.txt']=license_bytes
 modules=run([str(go),'list','-m','all'],cwd=ROOT,env=env).splitlines()
 if modules!=['testreceipts']:raise SystemExit('Dependency inventory changed; update and review package notices before building')
 common={'version':args.version,'sourceRevision':revision,'workingTreeDirty':dirty,'sourceFilesSha256':{n:sha(b) for n,b in source_bytes.items()},'releaseAssetsSha256':{n:sha(b) for n,b in assets.items()},'toolchain':version,'dependencies':modules,'settings':{k:env[k] for k in ('CGO_ENABLED','GOAMD64','GOARM64','GOTOOLCHAIN','GOENV','GOFLAGS','GOEXPERIMENT','GOPROXY','GOSUMDB','GOWORK')},'packagerSourceSha256':sha(Path(__file__).read_bytes()),'goExecutableSha256':sha(go.read_bytes()),'packager':{'python':platform.python_version(),'zlib':zlib.ZLIB_VERSION,'archivePolicy':'sorted members; fixed owners/modes/timestamps; gzip mtime=0; ZIP epoch=1980'},'distribution':'private unsigned development candidate; platform qualification/publication pending'}
 rows=[];out.mkdir(parents=True)
 with tempfile.TemporaryDirectory(prefix='testreceipts-release-') as tmp:
  for target in TARGETS:
   osname,arch=target.split('/');exe='testreceipts'+('.exe' if osname=='windows' else '');base=f'testreceipts-{args.version}-{osname}-{arch}';extension='.zip' if osname=='windows' else '.tar.gz';hashes=[];binary_hashes=[]
   for attempt in range(2 if args.verify_repro else 1):
    work=Path(tmp)/f'build-{attempt}'
    for name,raw in source_bytes.items():p=work/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    destination=work/'output'/exe;destination.parent.mkdir(exist_ok=True)
    target_env=env|{'GOOS':osname,'GOARCH':arch}
    flags=['-trimpath','-buildvcs=false',f'-ldflags=-s -w -buildid= -X=main.version={args.version}']
    subprocess.run([str(go),'build',*flags,'-o',str(destination),'./cmd/testreceipts'],cwd=work,env=target_env,check=True)
    binary=destination.read_bytes();metadata=common|{'target':target,'binarySha256':sha(binary),'binaryBytes':len(binary),'buildFlags':flags,'goBuildInfo':run([str(go),'version','-m',str(destination)],env=env).replace(str(destination),exe)}
    files={n:(raw,0o644) for n,raw in assets.items()};files[exe]=(binary,0o755);files['BUILD.json']=(encoded(metadata),0o644)
    package=archive(files,base,osname=='windows');hashes.append(sha(package));binary_hashes.append(sha(binary))
    if attempt==0:(out/(base+extension)).write_bytes(package)
   if len(set(hashes))!=1 or len(set(binary_hashes))!=1:raise RuntimeError(f'{target}: nonreproducible output')
   path=out/(base+extension);unpack(path)
   rows.append({'target':target,'archive':path.name,'archiveBytes':len(package),'archiveSha256':hashes[0],'binaryBytes':len(binary),'binarySha256':binary_hashes[0],'installedPackageBytes':sum(len(b) for b,_ in files.values()),'archiveMembers':sorted(files),'binaryBuildHashes':binary_hashes,'archiveBuildHashes':hashes,'reproducibility':'pass (two source directories, shared build cache)' if args.verify_repro else 'not checked','nativeRuntime':'unverified'})
   print(f'{target}: {len(binary)} executable bytes; {len(package)} packaged bytes; {rows[-1]["reproducibility"]}',flush=True)
 manifest=common|{'targets':rows};(out/'release-manifest.json').write_bytes(encoded(manifest));checksums={p.name:sha(p.read_bytes()) for p in sorted(out.iterdir())};(out/'SHA256SUMS.json').write_bytes(encoded(checksums));print(out)

def verify(args):
 root=args.directory.resolve();sums=json.loads((root/'SHA256SUMS.json').read_text());actual={p.name for p in root.iterdir()}
 if actual!=set(sums)|{'SHA256SUMS.json'}:raise ValueError('unexpected_or_missing_artifact')
 for name,digest in sums.items():
  if Path(name).name!=name:raise ValueError('checksum_path')
  if sha((root/name).read_bytes())!=digest:raise ValueError('checksum_mismatch')
 manifest=json.loads((root/'release-manifest.json').read_text())
 if sorted(row['target'] for row in manifest['targets'])!=sorted(TARGETS):raise ValueError('target_inventory')
 for row in manifest['targets']:
  if row['archive'] not in sums or Path(row['archive']).name!=row['archive']:raise ValueError('manifest_archive_path')
  files,metadata=unpack(root/row['archive'])
  if metadata['target']!=row['target'] or metadata['binarySha256']!=row['binarySha256'] or sha((root/row['archive']).read_bytes())!=row['archiveSha256']:raise ValueError('manifest_mismatch')
 print('PASS: checksums, six-target inventory, archive allowlists and executable metadata')

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 b=sub.add_parser('build');b.add_argument('--version',required=True);b.add_argument('--out',type=Path,required=True);b.add_argument('--go');b.add_argument('--verify-repro',action='store_true');b.set_defaults(func=build)
 v=sub.add_parser('verify');v.add_argument('directory',type=Path);v.set_defaults(func=verify)
 args=p.parse_args();args.func(args)
if __name__=='__main__':main()
