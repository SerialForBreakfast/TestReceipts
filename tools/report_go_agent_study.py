#!/usr/bin/env python3
"""Export small, independently reconstructed study metrics; never call models."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import statistics


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def go_comparison_seen(commands):
    """Include Python subprocess calls; help alone is not a comparison."""
    return any(re.search(r'''testreceipts['"]?\s*(?:,\s*['"])?\s*compare-recording''', command)
               for command in commands)


def export(root, out):
    out.mkdir(parents=True, exist_ok=True)
    report = json.loads((root / 'summary.json').read_text())
    freeze = json.loads((root / 'freeze.json').read_text())
    assert report['complete'] and report['attempts'] == 72
    assert json.loads((root / 'audit.json').read_text())['status'] == 'pass'
    rows = [json.loads(p.read_text()) for p in sorted((root / 'runs').glob('U*.json'))]
    # Reconstruct per-pair savings without using the experiment's summarizer.
    comparisons = {}
    for baseline in ['api', 'ready']:
        savings = []
        for pair in sorted({r['id'] for r in rows}):
            a = [r['usage']['input_tokens'] + r['usage']['output_tokens']
                 for r in rows if r['id'] == pair and r['arm'] == 'adapter']
            b = [r['usage']['input_tokens'] + r['usage']['output_tokens']
                 for r in rows if r['id'] == pair and r['arm'] == baseline]
            assert len(a) == len(b) == 2
            savings.append(100 * (1 - statistics.median(a) / statistics.median(b)))
        median = statistics.median(savings)
        assert median == report['comparisons'][baseline]['medianPairedSavingsPercent']
        rng = random.Random(20261106)
        boot = sorted(statistics.median(rng.choices(savings, k=len(savings))) for _ in range(10000))
        comparisons[baseline] = dict(report['comparisons'][baseline],
            exploratoryBootstrap95PercentInterval=[boot[249], boot[9749]],
            bootstrap='10,000 paired-case resamples, fixed seed 20261106; exploratory, small n=12',
            original30PercentGatePassed=median >= 30)
    attempts = []
    for r in rows:
        stem = '{id}-{rep}-{arm}'.format(**r)
        events = [json.loads(line) for line in (root / 'runs' / (stem + '.jsonl')).read_text().splitlines()
                  if line.startswith('{')]
        commands = [e['item'].get('command', '') for e in events
                    if e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'command_execution']
        attempts.append({**{k: r[k] for k in ['id', 'arm', 'rep', 'thread', 'usage', 'calls',
                                             'correct', 'checks', 'inventoryCorrect',
                                             'unsupportedCompletenessClaims', 'sourceUnchanged',
                                             'elapsed', 'exitCode', 'timeout']},
                         'goCommandObserved': go_comparison_seen(commands)
                         if r['arm'] == 'adapter' else None,
                         'recordSha256': digest(root / 'runs' / (stem + '.json')),
                         'traceSha256': digest(root / 'runs' / (stem + '.jsonl'))})
    report['comparisons'] = comparisons
    report['independentMetricReconstruction'] = 'pass'
    report['goArmAttemptsWithGoCommandObserved'] = sum(r['goCommandObserved'] is True for r in attempts)
    report['goArmComparisonNotObserved'] = [{k: r[k] for k in ['id', 'rep', 'traceSha256']}
                                           for r in attempts if r['goCommandObserved'] is False]
    report['goArmInterpretation'] = (
        'Intention-to-treat assigned workflow, retaining fallback costs. U08 repetition 1 ran '
        'testreceipts --help, then used the allowed Python helpers without running the Go comparison. '
        'The help command exited successfully; no Go comparison failure was observed in that attempt. '
        '23/24 assigned attempts executed the Go comparison. Required-fact checks passed in all 24. '
        'These percentages are not a 24/24 Go-only execution result.')
    report['limits'].append(report['goArmInterpretation'])
    rollouts = root / 'rollout-usage.json'
    report['independentRolloutUsage'] = 'unverified'
    if rollouts.exists():
        counters = json.loads(rollouts.read_text())
        assert len(counters) == 72
        for row in rows:
            counter = next(c for c in counters if c['thread'] == row['thread'])
            assert all(counter['usage'][k] == row['usage'][k] for k in
                       ['input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens'])
        report['independentRolloutUsage'] = 'pass'
    diagnostics = []
    for path in sorted((root / 'runs').glob('*.stderr')):
        for line in path.read_text().splitlines():
            if 'retry' in line.lower() or 'mcp server startup failed' in line.lower():
                diagnostics.append({'attempt': path.stem, 'line': line})
    def write(name, value):
        (out / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n')
    write('summary.json', report)
    write('attempts.json', attempts)
    write('runner-diagnostics.json', diagnostics)
    write('audit.json', json.loads((root / 'audit.json').read_text()))
    if rollouts.exists():
        write('rollout-usage.json', json.loads(rollouts.read_text()))
    write('run-config.json', {k: freeze[k] for k in ['version', 'model', 'reasoning', 'cliHash',
          'cliVersion', 'createdAt', 'timeout', 'toolLimit', 'maximumAttempts', 'scope', 'authorization']})
    write('provenance.json', json.loads((root / 'provenance.json').read_text()))
    if (root / 'execution-context.json').exists():
        write('execution-context.json', json.loads((root / 'execution-context.json').read_text()))
    write('inputs-expected.json', json.loads((root / 'protocol/questions.json').read_text()))
    write('narratives.json', [dict(id=r['id'], arm=r['arm'], rep=r['rep'],
          explanation=r['answer'].get('explanation') if isinstance(r['answer'], dict) else None)
          for r in rows])
    files = {p.relative_to(root).as_posix(): {'sha256': digest(p), 'bytes': p.stat().st_size}
             for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
             and 'work' not in p.relative_to(root).parts}
    write('raw-catalog.json', {'availability': 'Local ignored .artifacts/go-url-first-v1; not uploaded',
          'files': files, 'note': 'Workspaces excluded from this catalog; their original source inventories '
          'are in each attempt record. The study runner audit checks them against retained workspaces.'})
    # Small chart of complete per-case measurements; no guessed values.
    cases = report['cases']
    maximum = max(a['medianTokens'] for c in cases for a in c['arms'].values())
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1040 910" role="img" '
           'aria-label="Go study median whole-investigation tokens by run pair">',
           '<rect width="1040" height="910" fill="white"/>',
           '<g font-family="sans-serif" font-size="14" fill="#172033">',
           '<text x="20" y="28" font-size="21">Go first-use replication: agent tokens</text>',
           '<text x="20" y="52">Blue: parser assembly · Green: ready query · Orange: Go tool</text>',
           '<text x="20" y="74">Per-pair medians of two attempts; includes cached input. Historical replay inputs.</text>']
    colors = ['#2563eb', '#059669', '#c2410c']
    for i, case in enumerate(cases):
        y = 102 + i * 64
        svg.append(f'<text x="20" y="{y+16}">{case["id"]}</text>')
        for j, arm in enumerate(['api', 'ready', 'adapter']):
            value = case['arms'][arm]['medianTokens']
            width = value / maximum * 800
            svg.append(f'<rect x="75" y="{y+j*17}" width="{width:.2f}" height="14" fill="{colors[j]}"/>')
            svg.append(f'<text x="{width+83:.2f}" y="{y+j*17+12}">{value:,.0f}</text>')
    svg.append('</g></svg>')
    (out / 'overview.svg').write_text('\n'.join(svg) + '\n')
    print(json.dumps(comparisons, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    export(args.root.resolve(), args.out.resolve())
