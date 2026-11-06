#!/usr/bin/env python3
"""Run native qualification and fail closed on missing platform evidence."""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import struct
import sys
import time
from pathlib import Path
from release import ROOT, TARGETS, PIN, unpack

REQUIRED_CHECKS = ['nativeArchitecture', 'archiveVerification', 'goTests', 'goVet', 'referenceParity', 'packageSmoke', 'packagingBoundaries', 'mcpParity']


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def inventory():
    matrix = read(ROOT / 'ci/platforms.json')
    if sorted(row['target'] for row in matrix['include']) != sorted(TARGETS):
        raise RuntimeError('six-target inventory mismatch')
    return matrix


def host_target():
    osname = {'Darwin': 'darwin', 'Linux': 'linux', 'Windows': 'windows'}.get(platform.system())
    arch = {'x86_64': 'amd64', 'amd64': 'amd64', 'aarch64': 'arm64', 'arm64': 'arm64'}.get(platform.machine().lower())
    return f'{osname}/{arch}'



def binary_target(raw):
    if raw[:4] == b'\x7fELF' and len(raw) >= 20 and raw[4:6] == b'\x02\x01':
        machine = struct.unpack_from('<H', raw, 18)[0]
        arch = {62:'amd64', 183:'arm64'}.get(machine)
        if arch:
            return 'linux/' + arch
    if raw[:4] == b'\xcf\xfa\xed\xfe' and len(raw) >= 8:
        machine = struct.unpack_from('<I', raw, 4)[0]
        arch = {0x1000007:'amd64', 0x100000c:'arm64'}.get(machine)
        if arch:
            return 'darwin/' + arch
    if raw[:2] == b'MZ' and len(raw) >= 64:
        offset = struct.unpack_from('<I', raw, 60)[0]
        if offset + 6 <= len(raw) and raw[offset:offset+4] == b'PE\0\0':
            machine = struct.unpack_from('<H', raw, offset+4)[0]
            arch = {0x8664:'amd64', 0xaa64:'arm64'}.get(machine)
            if arch:
                return 'windows/' + arch
    raise RuntimeError('unknown executable OS/architecture')


def qualify(args):
    target = args.target
    if target not in [r['target'] for r in inventory()['include']]:
        raise RuntimeError('unknown target')
    output = args.out.resolve() / target.replace('/', '-')
    output.mkdir(parents=True, exist_ok=True)
    report = {'target': target, 'status': 'running', 'sourceRevision': os.getenv('GITHUB_SHA'),
              'runner': {'name': os.getenv('RUNNER_NAME'), 'os': platform.platform(),
                         'machine': platform.machine(), 'runnerArch': os.getenv('RUNNER_ARCH')},
              'checks': {}, 'unverified': ['oldest-supported OS', 'full clean-machine VM installs; Linux minimal container is narrower proof',
                                          'downloaded-package trust and publisher signing', 'third-party MCP hosts and modern protocol']}
    report_file = output / 'report.json'
    write(report_file, report)

    def command(name, cmd, timeout=600):
        report['checks'][name] = {'status': 'running', 'command': [str(x) for x in cmd]}
        write(report_file, report)
        start = time.perf_counter()
        with (output / (name + '.log')).open('w', encoding='utf-8') as log:
            process = subprocess.run([str(x) for x in cmd], stdout=log, stderr=subprocess.STDOUT,
                                     text=True, timeout=timeout, env=os.environ | {'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'})
        record = report['checks'][name]
        record.update(status='passed' if process.returncode == 0 else 'failed',
                      exit=process.returncode, seconds=round(time.perf_counter() - start, 6))
        write(report_file, report)
        if process.returncode:
            raise RuntimeError(name + ' failed; inspect ' + name + '.log')

    try:
        if host_target() != target:
            raise RuntimeError('native host architecture mismatch: ' + host_target())
        go = shutil.which('go')
        if not go:
            raise RuntimeError('Go is required on the qualification harness host')
        go_version = subprocess.check_output([go, 'version'], text=True).strip()
        if go_version.split()[2] != PIN:
            raise RuntimeError('toolchain mismatch: ' + go_version)
        go_host = subprocess.check_output([go, 'env', 'GOHOSTOS', 'GOHOSTARCH'], text=True).split()
        if '/'.join(go_host) != target:
            raise RuntimeError('Go toolchain is emulated or foreign')
        report['checks']['nativeArchitecture'] = {'status': 'passed', 'python': host_target(), 'go': '/'.join(go_host), 'goVersion': go_version}
        command('archiveVerification', [sys.executable, ROOT / 'tools/release.py', 'verify', args.packages])
        manifest = read(args.packages / 'release-manifest.json')
        row = next(r for r in manifest['targets'] if r['target'] == target)
        expected_revision = os.getenv('GITHUB_SHA')
        if expected_revision and manifest['sourceRevision'] != expected_revision:
            raise RuntimeError('package/source revision mismatch')
        if manifest['workingTreeDirty']:
            raise RuntimeError('packages did not originate from a clean source tree')
        files, metadata = unpack(args.packages / row['archive'])
        executable_name = 'testreceipts.exe' if target.startswith('windows') else 'testreceipts'
        if binary_target(files[executable_name][0]) != target:
            raise RuntimeError('packaged executable is foreign; emulation is not qualification')
        report['checks']['nativeArchitecture']['binary'] = target
        report.update(sourceRevision=manifest['sourceRevision'], package=row['archive'],
                      packageSha256=row['archiveSha256'], binarySha256=row['binarySha256'])
        installed = output / 'installed'
        installed.mkdir(exist_ok=True)
        for name, (raw, mode) in files.items():
            destination = installed / name
            destination.write_bytes(raw)
            destination.chmod(mode)
        binary = installed / ('testreceipts.exe' if target.startswith('windows') else 'testreceipts')
        command('goTests', [go, 'test', '-json', './...'])
        skipped = []
        for line in (output / 'goTests.log').read_text(encoding='utf-8').splitlines():
            try:
                event = json.loads(line)
                if event.get('Action') == 'skip':
                    skipped.append({'package': event.get('Package'), 'test': event.get('Test')})
            except json.JSONDecodeError:
                pass
        report['skippedGoTests'] = skipped
        command('goVet', [go, 'vet', './...'])
        command('referenceParity', [sys.executable, ROOT / 'tools/verify.py', '--go-binary', binary])
        command('packageSmoke', [sys.executable, ROOT / 'tools/smoke_release.py', '--package', args.packages / row['archive'], '--out', output / 'smoke'])
        command('packagingBoundaries', [sys.executable, ROOT / 'tools/test_release.py'])
        live = os.getenv('LIVE_VALIDATION', 'true').lower() == 'true'
        capture = output / 'capture'
        if live:
            job = 'https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/ci-aws-ebs-csi-driver-e2e-functional/'
            urls = [job + '2116467111751585792', job + '2116739156053856256']
            command('liveHTTPS', [binary, 'compare-live', capture, *urls])
            result = read(capture / 'comparison.json')
            if not all(run['artifactComplete'] for run in result['runs']):
                report['checks']['liveHTTPS']['status'] = 'failed'
                raise RuntimeError('public reports unavailable or incomplete; live TLS acquisition not qualified')
            report['checks']['liveHTTPS']['comparisonComplete'] = result['comparisonComplete']
            report['checks']['liveHTTPS']['scope'] = 'artifact acquisition passed; parser uncertainty retained'
            command('liveReplay', [sys.executable, ROOT / 'tools/validate_live_capture.py', '--capture', capture, '--binary', binary, '--out', output / 'live-audit'])
        else:
            report['checks']['liveHTTPS'] = {'status': 'not_run', 'reason': 'disabled for this dispatch'}
            report['unverified'].append('live HTTPS / OS certificate trust on this run')
        mcp = [sys.executable, ROOT / 'tools/check_mcp.py', '--binary', binary, '--out', output / 'mcp']
        if live:
            mcp += ['--real-capture', capture]
        command('mcpParity', mcp)
        if os.getenv('MINIMAL_LINUX', 'false').lower() == 'true':
            command('minimalLinux', [sys.executable, ROOT / 'tools/minimal_linux.py', '--target', target, '--binary', binary, '--out', output / 'minimal'])
        else:
            report['checks']['minimalLinux'] = {'status': 'not_applicable', 'reason': 'not requested; full clean-machine coverage remains separate'}
        report['status'] = 'passed'
    except Exception as error:
        report.update(status='failed', error=str(error))
        for check in report['checks'].values():
            if check.get('status') == 'running':
                check['status'] = 'failed'
                check['reason'] = str(error)
    finally:
        write(report_file, report)
    print(json.dumps({'target': target, 'status': report['status'], 'report': str(report_file)}))
    return report['status'] == 'passed'


def aggregate(reports, manifest, revision):
    targets = [r['target'] for r in inventory()['include']]
    grouped = {target: [] for target in targets}
    for report in reports:
        if report.get('target') in grouped:
            grouped[report['target']].append(report)
    output = []
    for target in targets:
        found = grouped[target]
        state, reason = 'unverified', 'no native report; skipped/unavailable is not passing'
        if len(found) > 1:
            state, reason = 'failed', 'duplicate target reports'
        elif len(found) == 1:
            report = found[0]
            row = next((r for r in (manifest or {}).get('targets', []) if r['target'] == target), None)
            if not row or manifest.get('sourceRevision') != revision or manifest.get('workingTreeDirty'):
                state, reason = 'unverified', 'package provenance missing'
            elif report.get('sourceRevision') != revision or report.get('binarySha256') != row['binarySha256'] or report.get('packageSha256') != row['archiveSha256']:
                state, reason = 'failed', 'source/artifact provenance mismatch'
            elif report.get('status') != 'passed':
                state, reason = 'failed', report.get('error', 'native checks failed')
            elif any(report.get('checks', {}).get(key, {}).get('status') != 'passed' for key in REQUIRED_CHECKS):
                state, reason = 'failed', 'required check evidence missing or failed'
            elif report.get('checks', {}).get('liveHTTPS', {}).get('status') not in ['passed', 'not_run']:
                state, reason = 'failed', 'live HTTPS check missing or failed'
            elif target.startswith('linux/') and report.get('checks', {}).get('minimalLinux', {}).get('status') != 'passed':
                state, reason = 'failed', 'minimal Linux evidence missing or failed'
            else:
                state = 'passed'
                reason = 'native package checks passed; ' + ('live HTTPS not run' if report['checks']['liveHTTPS']['status'] == 'not_run' else 'live HTTPS passed; parser warnings remain separate')
        output.append({'target': target, 'status': state, 'reason': reason})
    return output


def summarize(args):
    manifest = None
    if (args.packages / 'release-manifest.json').exists():
        manifest = read(args.packages / 'release-manifest.json')
    reports = [read(p) for p in args.reports.rglob('report.json')]
    revision = os.getenv('GITHUB_SHA') or (manifest or {}).get('sourceRevision')
    rows = aggregate(reports, manifest, revision)
    jobs = {key: os.getenv(key, 'not_recorded') for key in ['PACKAGE_RESULT', 'NATIVE_RESULT', 'RACE_RESULT']}
    passed = all(row['status'] == 'passed' for row in rows) and all(value == 'success' for value in jobs.values())
    result = {'sourceRevision': revision, 'status': 'passed' if passed else 'incomplete_or_failed',
              'native': rows, 'workflowJobs': jobs,
              'reportedUnverified': {r['target']: r.get('unverified', []) for r in reports if r.get('target') in TARGETS},
              'skippedGoTests': {r['target']: r.get('skippedGoTests', []) for r in reports if r.get('target') in TARGETS},
              'remaining': ['full clean-machine VM installs; Linux minimal containers are narrower proof', 'minimum OS versions',
                            'publisher signing and downloaded-package trust', 'modern MCP and third-party host integration']}
    write(args.out / 'summary.json', result)
    lines = ['# Native qualification', '', '| Target | Result | Evidence |', '|---|---|---|']
    lines += [f'| {r["target"]} | {r["status"]} | {r["reason"]} |' for r in rows]
    lines += ['', 'Hosted images contain development tools. Linux minimal-container evidence is separate from full-machine qualification.',
              'Missing, cancelled or skipped jobs are never counted as passing. See summary.json and retained reports for limits.']
    text = '\n'.join(lines) + '\n'
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'summary.md').write_text(text, encoding='utf-8')
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a', encoding='utf-8') as stream:
            stream.write(text)
    print(text)
    return passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('matrix')
    run = subs.add_parser('run')
    run.add_argument('--target', required=True)
    run.add_argument('--packages', type=Path, required=True)
    run.add_argument('--out', type=Path, required=True)
    summary = subs.add_parser('summarize')
    summary.add_argument('--reports', type=Path, required=True)
    summary.add_argument('--packages', type=Path, required=True)
    summary.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'matrix':
        print('matrix=' + json.dumps(inventory(), separators=(',', ':')))
        return
    success = qualify(args) if args.command == 'run' else summarize(args)
    if not success:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
