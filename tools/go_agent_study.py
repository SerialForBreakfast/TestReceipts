#!/usr/bin/env python3
"""Frozen historical first-use replication; explicit model execution only via run.

Raw inputs, workspaces and transcripts stay in ignored storage. Original evidence
is copied, never edited. No prepared URL-wrapper/repeated-use claim is tested.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import time

CLI = Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex')
INV = ['url', 'xmlCandidates', 'includedReports', 'excludedObjects',
       'unresolvedObjects', 'artifactComplete', 'inventorySha256', 'listingSha256']
ARMS = ['api', 'ready', 'adapter']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and '.state' not in p.parts}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n')


def prepare(root, original, binary):
    root.mkdir(parents=True, exist_ok=False)
    for directory in ['runs', 'work']:
        (root / directory).mkdir()
    shutil.copytree(original / 'recordings', root / 'recordings')
    shutil.copytree(original / 'protocol', root / 'protocol',
                    ignore=shutil.ignore_patterns('__pycache__'))
    p = root / 'protocol'
    original_freeze = json.loads((original / 'freeze.json').read_text())
    # Verify copied originals before changing only documented harness paths/prompts.
    assert inventory(root / 'recordings') == original_freeze['recordings']
    assert inventory(p) == original_freeze['protocol']
    for dataset in (p / 'datasets').iterdir():
        write(dataset / 'provider-config.json', {'recording': str(root / 'recordings' / dataset.name)})
        (dataset / 'inspect_urls.py').unlink()
    common = (p / 'common.txt').read_text()
    common = common.replace('Use python3 -B.',
                            'Use python3 -B for Python; the supplied Go executable may also be run.')
    (p / 'common.txt').write_text(common)
    (p / 'adapter.txt').write_text(
        'The integrated URL entry point is ./testreceipts compare-recording RECORDING BEFORE_URL AFTER_URL. '
        'RECORDING is the recording path in provider-config.json. The Go executable handles the same '
        'discovery and comparison as the supplied generic helpers. You may use any supplied lower-level '
        'APIs or scripts. Only the executable/SDK may read recording storage.\n')
    shutil.copy2(binary, p / 'testreceipts')
    shutil.copy2(Path(__file__), root / 'runner.py')
    provenance = {
        'originalFreezeSha256': sha(original / 'freeze.json'),
        'originalSummarySha256': sha(original / 'summary.json'),
        'originalModel': original_freeze['model'],
        'originalCliVersion': original_freeze['cliVersion'],
        'originalProtocol': original_freeze['protocol'],
        'changes': ['Go executable replaces Python integrated URL entry point',
                    'recording absolute paths relocated; inputs unchanged',
                    'common prompt permits Go execution in every arm',
                    'Python integrated URL helper removed from every dataset',
                    'installed Codex CLI version recorded; all baselines rerun',
                    'Go SDK request telemetry unavailable; never represented as zero requests'],
    }
    write(root / 'provenance.json', provenance)
    write(root / 'freeze.json', {
        'version': 'go-url-first-v1', 'model': 'gpt-6-astra', 'reasoning': 'low',
        'CLI': str(CLI), 'cliHash': sha(CLI),
        'cliVersion': subprocess.check_output([str(CLI), '--version'], text=True).strip(),
        'createdAt': time.time(), 'protocol': inventory(p),
        'recordings': inventory(root / 'recordings'), 'runnerSha256': sha(root / 'runner.py'),
        'provenanceSha256': sha(root / 'provenance.json'),
        'timeout': 900, 'toolLimit': 16, 'maximumAttempts': 72,
        'scope': 'Same historical 12 pairs, three arms, two repetitions; fresh workspaces. '
                 'Not held-out data, not repeated use, not MCP or live networking.',
        'authorization': 'Maintainer: ok you can do that same test on the go model. '
                         'One 72-attempt replication; no automatic replacement trials.',
    })
    print('Frozen: 72 investigations; gpt-6-astra, low reasoning; no model calls yet.', flush=True)


def check_freeze(root):
    f = json.loads((root / 'freeze.json').read_text())
    assert inventory(root / 'protocol') == f['protocol'], 'protocol drift'
    assert inventory(root / 'recordings') == f['recordings'], 'recording drift'
    assert sha(root / 'runner.py') == f['runnerSha256'], 'runner drift'
    assert sha(root / 'provenance.json') == f['provenanceSha256'], 'provenance drift'
    assert sha(Path(f['CLI'])) == f['cliHash'], 'CLI changed'
    return f


def score(answer, gold):
    checks = {k: isinstance(answer, dict) and answer.get(k) == v for k, v in gold.items()}
    observed = answer.get('runs', []) if isinstance(answer, dict) else []
    inv_ok = len(observed) == 2 and all(
        all(a.get(k) == b[k] for k in INV) for a, b in zip(observed, gold['runs']))
    unsupported = sum(a.get('artifactComplete') is True and any(a.get(k) != b[k] for k in INV)
                      for a, b in zip(observed, gold['runs']))
    return checks, inv_ok, unsupported


def run(root):
    f = check_freeze(root)
    p = root / 'protocol'
    questions = {q['id']: q for q in json.loads((p / 'questions.json').read_text())}
    schedule = json.loads((p / 'schedule.json').read_text())
    assert len(schedule) == f['maximumAttempts'] == 72
    for row in schedule:
        stem = '{id}-{rep}-{arm}'.format(**row)
        dest = root / 'runs' / stem
        if dest.with_suffix('.json').exists():
            continue
        assert not dest.with_suffix('.jsonl').exists(), 'partial attempt retained; stop, never overwrite'
        check_freeze(root)
        work = root / 'work' / stem
        shutil.copytree(p / 'datasets' / row['id'], work)
        if row['arm'] == 'api':
            (work / 'ready_query.py').unlink()
        if row['arm'] == 'adapter':
            shutil.copy2(p / 'testreceipts', work / 'testreceipts')
        before = inventory(work)
        q = questions[row['id']]
        prompt = (p / 'common.txt').read_text() + (p / (row['arm'] + '.txt')).read_text() + q['task']
        command = [f['CLI'], 'exec', '--ignore-user-config', '--ignore-rules',
                   '--skip-git-repo-check', '--sandbox', 'workspace-write', '-C', str(work),
                   '--json', '--model', f['model'], '--output-schema', str(p / 'schema.json'),
                   '-c', 'web_search="disabled"', '-c', 'model_reasoning_effort="low"', '-']
        started = time.time()
        timedout = False
        with dest.with_suffix('.jsonl').open('x') as out, dest.with_suffix('.stderr').open('x') as err:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                       start_new_session=True)
            try:
                process.communicate(prompt.encode(), timeout=f['timeout'])
            except subprocess.TimeoutExpired:
                timedout = True
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        ended = time.time()
        events = [json.loads(line) for line in dest.with_suffix('.jsonl').read_text().splitlines()
                  if line.startswith('{')]
        messages = [e['item']['text'] for e in events if e.get('type') == 'item.completed'
                    and e.get('item', {}).get('type') == 'agent_message']
        try:
            answer = json.loads(messages[-1])
        except (IndexError, ValueError):
            answer = None
        calls = [e['item'] for e in events if e.get('type') == 'item.completed'
                 and e.get('item', {}).get('type') in ['command_execution', 'mcp_tool_call', 'web_search']]
        raw_usage = [e['usage'] for e in events if e.get('type') == 'turn.completed']
        usage = None
        if len(raw_usage) == 1:
            u = raw_usage[0]
            usage = {k: u[k] for k in ['input_tokens', 'cached_input_tokens', 'output_tokens']}
            usage.update(total_tokens=u['input_tokens'] + u['output_tokens'],
                         uncached_input_tokens=u['input_tokens'] - u['cached_input_tokens'])
        checks, inv_ok, unsupported = score(answer, q['gold'])
        unchanged = inventory(work) == before
        threads = [e['thread_id'] for e in events if e.get('type') == 'thread.started']
        r = dict(row, prompt=prompt, command=command, thread=threads[0] if len(threads) == 1 else None,
                 answer=answer, rawUsage=raw_usage, usage=usage, checks=checks,
                 inventoryCorrect=inv_ok, unsupportedCompletenessClaims=unsupported,
                 sourceUnchanged=unchanged, sourceInventory=before, calls=len(calls),
                 outputBytes=sum(len(str(c.get('aggregated_output', '')).encode()) for c in calls),
                 startedAt=started, endedAt=ended, elapsed=ended-started,
                 exitCode=process.returncode, timeout=timedout,
                 correct=all(checks.values()) and unchanged and len(calls) <= f['toolLimit']
                         and process.returncode == 0 and not timedout)
        write(dest.with_suffix('.json'), r)
        summarize(root)
        print(stem, 'correct=', r['correct'], 'tokens=', usage['total_tokens'] if usage else 'UNKNOWN',
              'elapsed=', round(r['elapsed'], 1), flush=True)
        if usage is None or not unchanged or process.returncode != 0 or timedout:
            raise RuntimeError('Execution/telemetry/source failure retained; stop without replacement')


def summarize(root):
    rows = [json.loads(p.read_text()) for p in sorted((root / 'runs').glob('U*.json'))]
    questions = json.loads((root / 'protocol/questions.json').read_text())
    complete = len(rows) == 72 and all(r['usage'] is not None for r in rows)
    cases = []
    for q in questions:
        arms = {}
        for arm in ARMS:
            rs = [r for r in rows if r['id'] == q['id'] and r['arm'] == arm]
            if rs:
                arms[arm] = {'attempts': len(rs), 'correct': sum(r['correct'] for r in rs),
                             'inventoryCorrect': sum(r['inventoryCorrect'] for r in rs),
                             'medianTokens': statistics.median(r['usage']['total_tokens'] for r in rs)
                             if all(r['usage'] is not None for r in rs) else None}
        savings = {}
        for arm in ['api', 'ready']:
            if all(a in arms and arms[a]['attempts'] == 2 and arms[a]['medianTokens']
                   for a in [arm, 'adapter']):
                savings[arm] = 100 * (1 - arms['adapter']['medianTokens'] / arms[arm]['medianTokens'])
        cases.append(dict(id=q['id'], project=q['project'], arms=arms, savingsPercent=savings))
    comparisons = {}
    if complete:
        for arm in ['api', 'ready']:
            savings = [c['savingsPercent'][arm] for c in cases]
            comparisons[arm] = {
                'medianPairedSavingsPercent': statistics.median(savings),
                'perPairRangePercent': [min(savings), max(savings)],
                'aggregateSavingsPercent': 100 * (1 -
                    sum(r['usage']['total_tokens'] for r in rows if r['arm'] == 'adapter') /
                    sum(r['usage']['total_tokens'] for r in rows if r['arm'] == arm)),
                'pairsWithOver10PercentRegression': sum(s < -10 for s in savings),
            }
    totals = {}
    for arm in ARMS:
        rs = [r for r in rows if r['arm'] == arm]
        totals[arm] = dict(attempts=len(rs), correct=sum(r['correct'] for r in rs),
            usage={k: sum(r['usage'][k] for r in rs if r['usage']) for k in
                   ['input_tokens', 'cached_input_tokens', 'uncached_input_tokens', 'output_tokens', 'total_tokens']},
            missingUsage=sum(r['usage'] is None for r in rs))
    report = dict(complete=complete, planned=72, attempts=len(rows),
                  correct=sum(r['correct'] for r in rows),
                  inventoryCorrect=sum(r['inventoryCorrect'] for r in rows),
                  unsupportedCompletenessClaims=sum(r['unsupportedCompletenessClaims'] for r in rows),
                  comparisons=comparisons, cases=cases, totals=totals,
                  failures=[{k: r[k] for k in ['id', 'arm', 'rep', 'checks', 'exitCode', 'timeout']}
                            for r in rows if not r['correct']],
                  humanNarrativeReview='pending', promotion=False,
                  limits=['Historical inputs, not held out; one model, fresh setup only',
                          'CLI version differs from original; all baselines rerun',
                          'Includes cached input tokens; not dollar savings',
                          'Recorded responses; not live networking, MCP or repeated use',
                          'Go SDK acquisition telemetry unavailable; output inventory correctness checked',
                          'Prompt-scoped access is not proven OS isolation'])
    write(root / 'summary.json', report)
    return report


def audit(root):
    f = check_freeze(root)
    rows = [json.loads(p.read_text()) for p in sorted((root / 'runs').glob('U*.json'))]
    schedule = json.loads((root / 'protocol/schedule.json').read_text())
    questions = {q['id']: q for q in json.loads((root / 'protocol/questions.json').read_text())}
    assert len(rows) == 72 and {(r['id'], r['arm'], r['rep']) for r in rows} == {
        (r['id'], r['arm'], r['rep']) for r in schedule}
    threads = []
    for r in rows:
        stem = '{id}-{rep}-{arm}'.format(**r)
        events = [json.loads(line) for line in (root / 'runs' / (stem + '.jsonl')).read_text().splitlines()
                  if line.startswith('{')]
        usage = [e['usage'] for e in events if e.get('type') == 'turn.completed']
        assert usage == r['rawUsage'] and len(usage) == 1
        u = usage[0]
        assert r['usage'] == dict(input_tokens=u['input_tokens'], cached_input_tokens=u['cached_input_tokens'],
                                  output_tokens=u['output_tokens'], total_tokens=u['input_tokens']+u['output_tokens'],
                                  uncached_input_tokens=u['input_tokens']-u['cached_input_tokens'])
        messages = [e['item']['text'] for e in events if e.get('type') == 'item.completed'
                    and e.get('item', {}).get('type') == 'agent_message']
        try:
            answer = json.loads(messages[-1])
        except (IndexError, ValueError):
            answer = None
        assert answer == r['answer']
        checks, inv_ok, unsupported = score(answer, questions[r['id']]['gold'])
        assert (checks, inv_ok, unsupported) == (r['checks'], r['inventoryCorrect'], r['unsupportedCompletenessClaims'])
        assert inventory(root / 'work' / stem) == r['sourceInventory'] and r['sourceUnchanged']
        calls = [e['item'] for e in events if e.get('type') == 'item.completed'
                 and e.get('item', {}).get('type') in ['command_execution', 'mcp_tool_call', 'web_search']]
        assert len(calls) == r['calls']
        assert r['correct'] == (all(checks.values()) and len(calls) <= f['toolLimit']
                                and r['exitCode'] == 0 and not r['timeout'])
        assert r['prompt'] == ((root / 'protocol/common.txt').read_text() +
                               (root / 'protocol' / (r['arm'] + '.txt')).read_text() + questions[r['id']]['task'])
        ids = [e['thread_id'] for e in events if e.get('type') == 'thread.started']
        assert ids == [r['thread']]
        threads += ids
    assert len(set(threads)) == 72
    ordered = [next(r for r in rows if all(r[k] == s[k] for k in ['id', 'arm', 'rep'])) for s in schedule]
    assert all(a['endedAt'] <= b['startedAt'] for a, b in zip(ordered, ordered[1:]))
    saved = json.loads((root / 'summary.json').read_text())
    assert summarize(root) == saved, 'metric reconstruction drift'
    write(root / 'audit.json', {'status': 'pass', 'attempts': 72,
          'checks': ['frozen protocol/recordings/runner/CLI', 'raw answers and usage',
                     'exact gold facts and inventories', 'source immutability',
                     '72 unique sessions in frozen sequential schedule', 'summary reconstruction'],
          'limits': saved['limits'], 'humanNarrativeReview': 'pending'})
    print('Audit passed: 72 raw attempts reconstructed; narrative review pending.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare', 'run', 'summary', 'audit'])
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--original', type=Path)
    p.add_argument('--binary', type=Path)
    a = p.parse_args()
    root = a.root.resolve()
    if a.action == 'prepare':
        assert a.original and a.binary
        prepare(root, a.original.resolve(), a.binary.resolve())
    elif a.action == 'run':
        run(root)
    elif a.action == 'summary':
        print(json.dumps(summarize(root), indent=2))
    else:
        audit(root)


if __name__ == '__main__':
    main()
