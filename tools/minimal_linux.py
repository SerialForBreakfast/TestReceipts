#!/usr/bin/env python3
"""Run packaged offline comparisons in a native minimal Linux container."""
import argparse
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'debian@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc'


def validate(binary, target, output):
    host = {'x86_64': 'amd64', 'aarch64': 'arm64'}.get(platform.machine().lower())
    if platform.system() != 'Linux' or target != f'linux/{host}':
        raise RuntimeError('native Linux host/target mismatch; emulation is not qualification')
    output.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(args, timeout=180):
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        commands.append({'command': args, 'exit': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        if result.returncode:
            raise RuntimeError(f'container command failed: {result.stderr[:300]}')
        return result.stdout

    try:
        run(['docker', 'pull', '--platform', target, IMAGE])
        inspect = json.loads(run(['docker', 'image', 'inspect', IMAGE]))[0]
        if inspect['Architecture'] != host or inspect['Os'] != 'linux':
            raise RuntimeError('container image architecture mismatch')
        prefix = ['docker', 'run', '--rm', '--pull=never', '--platform', target,
                  '--network=none', '--read-only', '--user', '65534:65534',
                  '--cap-drop=ALL', '--security-opt=no-new-privileges',
                  '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m',
                  '--mount', f'type=bind,src={binary.resolve().parent},dst=/app,readonly',
                  '--mount', f'type=bind,src={ROOT / "testdata"},dst=/inputs,readonly']
        probe = ('for tool in go python python3 node gcc cc clang; do '
                 'if command -v "$tool" >/dev/null 2>&1; then exit 1; fi; done; uname -m')
        observed = run(prefix + [IMAGE, '/bin/sh', '-c', probe]).strip()
        if observed not in ({'amd64': {'x86_64'}, 'arm64': {'aarch64', 'arm64'}}[host]):
            raise RuntimeError('container kernel architecture mismatch')
        version = run(prefix + [IMAGE, '/app/' + binary.name, 'version']).strip()
        cases = sorted((ROOT / 'testdata/cases').iterdir()) + [ROOT / 'testdata/live/partial-listing']
        rows = []
        for case in cases:
            urls = json.loads((case / 'request.json').read_text(encoding='utf-8'))['urls']
            relative = case.relative_to(ROOT / 'testdata').as_posix()
            raw = run(prefix + [IMAGE, '/app/' + binary.name, 'compare-recording', '/inputs/' + relative, *urls])
            if json.loads(raw) != json.loads((case / 'expected.json').read_text(encoding='utf-8')):
                raise RuntimeError('minimal-container facts mismatch: ' + relative)
            rows.append({'case': relative, 'pass': True})
        result = {'status': 'passed', 'target': target, 'image': IMAGE,
                  'imageID': inspect['Id'], 'architecture': inspect['Architecture'],
                  'version': version, 'languageToolsAbsent': ['go', 'python', 'python3', 'node', 'gcc', 'cc', 'clang'],
                  'network': 'disabled', 'comparisons': rows,
                  'scope': 'minimal userland container on matching native Linux kernel; not a clean full-machine installation'}
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        return result
    finally:
        (output / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    validate(args.binary, args.target, args.out)
