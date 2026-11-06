"""Recreate the already-tested real-CI parser profile from tracked sources.

Only the historical input-budget adjustments differ from test_scale sources.
No large evidence bundle or network installation is needed for unit tests.
"""
from pathlib import Path
import zipfile
REPO=Path(__file__).resolve().parents[2]
def install(destination):
 destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
 for name in ['single_report.py','batch_reader.py','oracle.py']:
  text=(REPO/'scripts/test_scale'/name).read_text()
  if name=='single_report.py':
   assert 'INPUT_LIMIT=2*1024*1024' in text; text=text.replace('INPUT_LIMIT=2*1024*1024','INPUT_LIMIT=128*1024*1024')
  elif name=='batch_reader.py':
   assert 'f.read(1024*1024+1)' in text;text=text.replace('f.read(1024*1024+1)','f.read(16*1024*1024+1)').replace("if len(raw)>1024*1024:raise ValueError('per_report_budget_exceeded')","if len(raw)>16*1024*1024:raise ValueError('per_report_budget_exceeded')")
  (destination/name).write_text(text)
 with zipfile.ZipFile(REPO/'evals/heldout-tests/vendor/junitparser-5.0.3-py3-none-any.whl') as z:
  for name in z.namelist():
   path=Path(name)
   if path.is_absolute() or '..' in path.parts:raise ValueError('unsafe pinned wheel path')
   target=destination/path
   if name.endswith('/'):target.mkdir(parents=True,exist_ok=True)
   else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
