# Try TestReceipts offline

Install the executable using [the install guide](../release/INSTALL.md) and obtain this source checkout for its small example fixtures. Run the following commands from the checkout with `testreceipts` on PATH. A source build can use `./bin/testreceipts` instead. These examples use local files and make no network or model calls.

## Find context for a build error

```sh
testreceipts log-context testdata/build-logs/failed.txt 'failed to restore temporary ACL'
```

This archived Windows build log contains two matches, including the assertion source and the final exception. Expect `status` to be `ambiguous`, `coverage` to be `supplied_file`, and `matchedLines` to be `2`. The excerpts include physical line numbers so you can inspect both occurrences. Multiple matches need interpretation.

## Compare two recorded runs

```sh
testreceipts compare-recording testdata/cases/changes https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100 https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200
```

The URLs identify saved inputs. Expect `change.newDistinct` and `change.disappearedDistinct` to each equal `1`, and `change.sharedDistinct` to equal `1`. The new diagnostic is `new diagnostic`. Inspect coverage and identity warnings along with those counts.

## Let an agent choose the command

The installable skill is [skills/testreceipts/SKILL.md](../skills/testreceipts/SKILL.md). Copy the entire `testreceipts` directory into your agent host's skill directory. For Codex, from this checkout on macOS or Linux, install without replacing an existing skill using

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
test ! -e "${CODEX_HOME:-$HOME/.codex}/skills/testreceipts" && cp -R skills/testreceipts "${CODEX_HOME:-$HOME/.codex}/skills/"
```

If the target already exists, review it before updating. Other hosts use their own skill installation paths. The executable must also be available to the agent. Remove the copied skill directory to uninstall the skill.

Try this request with the checkout available to your agent

> Use TestReceipts to find context for “failed to restore temporary ACL” in testdata/build-logs/failed.txt. Cite the matching lines and explain any ambiguity.

The skill includes command selection, capture reuse, and interpretation of missing evidence. The optional [MCP interface](MCP.md) exposes the same operations within a configured workspace root. Automatic skill activation and third-party host behavior remain unmeasured.
