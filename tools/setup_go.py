#!/usr/bin/env python3
"""Install the pinned macOS arm64 development toolchain from a verified archive."""
import argparse,hashlib,platform,tarfile
from pathlib import Path
VERSION='1.27.3'
SHA256='dd3908cf20959d798c1e06ebe5b72213f0505ce01373b40ce3110975a6cd99c2'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);a=p.parse_args()
if (platform.system(),platform.machine())!=('Darwin','arm64'):raise SystemExit('This pinned archive is macOS arm64 only; use a native Go installation on other hosts.')
if hashlib.sha256(a.archive.read_bytes()).hexdigest()!=SHA256:raise SystemExit('Toolchain SHA-256 mismatch')
dest=Path(__file__).resolve().parents[1]/'.cache/toolchain'
if (dest/'go').exists():raise SystemExit('Toolchain already exists; refusing to overwrite it')
dest.mkdir(parents=True,exist_ok=True)
with tarfile.open(a.archive) as archive:archive.extractall(dest,filter='data')
print(f'Installed verified Go {VERSION}. Run ./tools/go version.')
