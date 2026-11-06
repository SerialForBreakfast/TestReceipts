#!/usr/bin/env python3
"""Focused release boundary tests; no compiler or network needed."""
import io,json,tempfile,tarfile,unittest
from pathlib import Path
import release
class ReleaseTests(unittest.TestCase):
 def files(self):
  binary=b'example';meta={'binarySha256':release.sha(binary),'binaryBytes':len(binary)}
  return {**{name:(b'notice',0o644) for name in release.ASSETS+['GO-LICENSE.txt']},'BUILD.json':(release.encoded(meta),0o644),'testreceipts':(binary,0o755)}
 def test_archives_are_stable_and_modes_survive(self):
  for windows in [False,True]:
   files=self.files()
   if windows:files['testreceipts.exe']=files.pop('testreceipts')
   raw=release.archive(files,'testreceipts-v1.0.0-dev.1-test',windows)
   self.assertEqual(raw,release.archive(dict(reversed(list(files.items()))),'testreceipts-v1.0.0-dev.1-test',windows))
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/('test.zip' if windows else 'test.tar.gz');p.write_bytes(raw);actual,_=release.unpack(p);self.assertEqual(files,actual)
 def test_unexpected_member_rejected(self):
  files=self.files();files['secret.txt']=(b'not allowed',0o644)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'bad.tar.gz';p.write_bytes(release.archive(files,'package',False))
   with self.assertRaisesRegex(ValueError,'archive_allowlist'):release.unpack(p)
 def test_binary_tamper_rejected(self):
  files=self.files();files['testreceipts']=(b'altered',0o755)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'bad.zip';p.write_bytes(release.archive(files,'package',True))
   with self.assertRaisesRegex(ValueError,'binary_integrity'):release.unpack(p)
 def test_traversal_and_links_rejected(self):
  for name,link in [('../escape',False),('package/link',True)]:
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'bad.tar.gz'
    with tarfile.open(p,'w:gz') as t:
     info=tarfile.TarInfo(name)
     if link:info.type=tarfile.SYMTYPE;info.linkname='/tmp/escape'
     t.addfile(info,io.BytesIO())
    with self.assertRaises(ValueError):release.unpack(p)
if __name__=='__main__':unittest.main()
