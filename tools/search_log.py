"""Reusable literal-search baseline for small archived UTF-8 step logs."""
import argparse
import json
from pathlib import Path


def search(path, literal, partial):
    with path.open('rb') as stream:
        data = stream.read(16 * 1024 * 1024 + 1)
    if len(data) > 16 * 1024 * 1024 or b'\0' in data:
        raise ValueError('unsupported log')
    lines = data.decode('utf-8').split('\n')
    if lines[-1] == '':
        lines.pop()
    lines = [line.removesuffix('\r') for line in lines]
    hits = [i for i, line in enumerate(lines) if literal in line]
    status = ('ambiguous' if len(hits) > 1 else 'incomplete' if partial
              else 'matched' if hits else 'no_match')
    return dict(status=status, matchedLines=len(hits), coverage='partial' if partial else 'supplied_file',
                excerpts=[dict(matchLine=i+1, startLine=max(0, i-2)+1,
                               lines=lines[max(0, i-2):i+3]) for i in hits[:8]])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partial', action='store_true')
    parser.add_argument('file', type=Path)
    parser.add_argument('literal')
    args = parser.parse_args()
    if not args.literal.strip() or any(c in args.literal for c in '\r\n'):
        parser.error('supply a nonempty single-line literal')
    try:
        result = search(args.file, args.literal, args.partial)
    except (OSError, ValueError) as error:
        print(json.dumps(dict(status='unavailable', coverage='unavailable', error=str(error),
                              matchedLines=0, excerpts=[])))
        raise SystemExit(2)
    print(json.dumps(result))
