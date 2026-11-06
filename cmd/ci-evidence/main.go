// ci-evidence is the portable deployment scaffold. Parsing is not implemented yet.
package main

import (
	"fmt"
	"io"
	"os"
)

var version = "dev"

func run(args []string, out, errOut io.Writer) int {
	if len(args) == 0 || args[0] == "help" || args[0] == "--help" {
		fmt.Fprintln(out, "ci-evidence: CI report comparison (Go port scaffold)")
		fmt.Fprintln(out, "Usage: ci-evidence version | help")
		fmt.Fprintln(out, "Planned: compare-recording RECORDING BEFORE_URL AFTER_URL")
		fmt.Fprintln(out, "Parsing, live providers and MCP are not implemented.")
		return 0
	}
	if len(args) == 1 && args[0] == "version" {
		fmt.Fprintln(out, version)
		return 0
	}
	fmt.Fprintln(errOut, "This operation is not implemented. See Tasks.md; no comparison was performed.")
	return 2
}

func main() { os.Exit(run(os.Args[1:], os.Stdout, os.Stderr)) }
