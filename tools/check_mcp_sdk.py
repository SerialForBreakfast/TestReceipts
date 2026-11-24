#!/usr/bin/env python3
"""Validate legacy stdio interoperability with the official MCP Python SDK.

Development-only dependency: mcp==1.30.0. No model calls.
"""
import argparse
import asyncio
import hashlib
import json
import subprocess
from datetime import timedelta
from importlib.metadata import version
from pathlib import Path

from jsonschema import Draft202012Validator
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


def cli(binary, *arguments):
    result = subprocess.run([str(binary), *arguments], capture_output=True,
                            text=True, timeout=30, check=True)
    assert not result.stderr, result.stderr
    return json.loads(result.stdout)


async def check(binary):
    rows = []
    parameters = StdioServerParameters(command=str(binary), args=['mcp', str(ROOT)])
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=30)) as session:
            initialized = await session.initialize()
            assert initialized.protocolVersion == '2025-11-25'
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            assert names == {'compare_live', 'compare_recording', 'log_context'}
            for tool in listed.tools:
                Draft202012Validator.check_schema(tool.inputSchema)
            await session.send_ping()
            cases = sorted((ROOT / 'testdata/cases').iterdir())
            cases.append(ROOT / 'testdata/live/partial-listing')
            for case in cases:
                urls = json.loads((case / 'request.json').read_text())['urls']
                result = await session.call_tool('compare_recording', {
                    'recording': case.relative_to(ROOT).as_posix(),
                    'beforeUrl': urls[0], 'afterUrl': urls[1],
                })
                assert not result.isError, result
                expected = cli(binary, 'compare-recording', str(case), *urls)
                assert result.structuredContent == expected
                assert json.loads(result.content[0].text) == expected
                assert result.content[1].type == 'resource_link'
                rows.append({'case': case.relative_to(ROOT).as_posix(), 'parity': True})
            path = (ROOT / 'testdata/build-logs/failed.txt').resolve()
            for query, partial in [('failed to restore temporary ACL', False),
                                   ('Traceback', False), ('absent diagnostic', False),
                                   ('failed to restore temporary ACL', True)]:
                result = await session.call_tool('log_context', {
                    'file': path.relative_to(ROOT).as_posix(), 'query': query, 'partial': partial,
                })
                expected = cli(binary, 'log-context', *(['--partial'] if partial else []), str(path), query)
                assert not result.isError
                assert result.structuredContent == expected
                assert json.loads(result.content[0].text) == expected
                rows.append({'query': query, 'partial': partial, 'parity': True})
            for arguments in [{'file': '../escape', 'query': 'error'},
                              {'file': 'missing.log', 'query': 'error'},
                              {'file': 'testdata/build-logs/failed.txt', 'query': ''}]:
                result = await session.call_tool('log_context', arguments)
                assert result.isError, result
    return {
        'sdk': 'official MCP Python SDK', 'sdkVersion': version('mcp'),
        'protocol': initialized.protocolVersion, 'tools': sorted(names),
        'binarySha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'checks': rows, 'invalidInputsRejected': 3, 'modelCalls': 0,
        'limits': 'Local SDK stdio interoperability only; agent-host UI and model tool selection unmeasured.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = asyncio.run(check(args.binary.resolve()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(f"PASS: official MCP SDK {report['sdkVersion']}, {len(report['checks'])} parity cases and 3 invalid inputs.")


if __name__ == '__main__':
    main()
