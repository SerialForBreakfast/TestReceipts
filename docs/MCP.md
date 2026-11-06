# MCP stdio interface

Start `testreceipts mcp ROOT` using an explicit existing workspace/capture root. The two tools invoke the same Go functions as the CLI; no second parser, generated answers, Python runtime, or model calls are involved.

This implementation pins the **legacy MCP 2025-11-25 stdio profile**. It implements initialization, initialized notification, ping, tools/list, tools/call and cancellation notifications. It does not implement the 2026 stateless profile, HTTP serving, prompts, sampling, authentication, sessions shared across clients or background tasks. Use a host that supports the pinned legacy version. The official [2025 lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) and [tool messages](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) define the interface. Third-party host/SDK integration is not yet verified.

A generic stdio host configuration (replace both absolute paths):

```json
{
  "mcpServers": {
    "testreceipts": {
      "command": "/absolute/path/to/testreceipts",
      "args": ["mcp", "/absolute/path/to/workspace"]
    }
  }
}
```

| Tool | Arguments | Behavior |
|---|---|---|
| `compare_recording` | `recording`, `beforeUrl`, `afterUrl` | Reads a relative recording inside ROOT; no HTTP |
| `compare_live` | `capture`, `beforeUrl`, `afterUrl` | Creates a new direct child of ROOT; bounded public Prow/GCS capture |

Use slash-separated relative paths. Absolute paths, parent traversal, backslashes, drive-style paths and resolved symlink escapes are rejected. Live capture names must be a single new directory component. Root is selected when launching the process; clients cannot change it with a tool argument. This is a local single-client boundary over a trusted workspace, not a hardened multi-tenant filesystem against concurrent external directory substitution.

Example arguments for an offline comparison, with ROOT set to this checkout:

```json
{
  "recording": "testdata/cases/changes",
  "beforeUrl": "https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100",
  "afterUrl": "https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200"
}
```

Successful `structuredContent` equals the CLI JSON exactly, including incomplete discovery and parser warnings. The text content carries the same JSON and a resource link identifies the original local catalog, which retains report paths/hashes. Reports and diagnostic text are untrusted data, never instructions. A partial comparison is not a tool execution error: inspect coverage fields as with the CLI. Invocation/protocol errors use JSON-RPC errors; execution/argument failures use `isError=true`. Stdout carries only protocol JSON; process errors use stderr.

The boundary accepts newline-delimited JSON objects up to 1 MiB; batches, duplicate keys, noninteger numbers and invalid Unicode are rejected. IDs are strings up to 128 characters or integer tokens up to 32 digits. Responses are capped at 2 MiB; large results fail explicitly instead of silently truncating facts. Use the CLI or the retained `comparison.json`/original reports for larger output. Sessions permit at most 1,024 messages, 64 tool invocations and four live captures. One call runs at a time; additional work returns `server_busy`. Live acquisition retains the provider's five-minute and byte/request limits. Cancellation reaches active acquisition; bounded local parsing may finish before returning a cancellation result. EOF or process interruption cancels active work.

## Validation and measurements

```sh
python3 tools/check_mcp.py --binary bin/testreceipts --out evidence/g04 --real-capture .artifacts/g03-release-live
```

The independent Python standard-library wire client compares all 15 original fixtures, the partial-listing fixture and the retained real capture against CLI output. It records wire bytes and wall time per case, separately from correctness. Optional `--live` also captures the two already-known public real URLs through MCP and checks MCP live = MCP replay = CLI replay; it writes a new ignored `.artifacts/g04-mcp-live` capture and refuses to overwrite one. This needs public network access. No models are called.

The measurements compare an already-started MCP process with a fresh CLI process, with uncontrolled OS caches. They are protocol overhead observations, not agent-token or speed advantage claims. Client-host interoperability, modern MCP support and other native platforms remain unverified. See [validation evidence](../evidence/g04/README.md) and [remaining tasks](../Tasks.md).
