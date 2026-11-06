// testreceipts compares structured reports from two recorded CI runs.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"testreceipts/internal/provider"
)

var version = "dev"

func run(args []string, out, errOut io.Writer) int {
	if len(args) == 0 || (len(args) == 1 && (args[0] == "help" || args[0] == "--help")) {
		fmt.Fprintln(out, "TestReceipts: exact CI report comparison\nUsage: testreceipts version | help\n       testreceipts compare-recording RECORDING BEFORE_URL AFTER_URL")
		return 0
	}
	if len(args) == 1 && args[0] == "version" {
		fmt.Fprintln(out, version)
		return 0
	}
	if len(args) != 4 || args[0] != "compare-recording" {
		fmt.Fprintln(errOut, "Invalid command. Use testreceipts help.")
		return 2
	}
	result, err := provider.Compare(args[1], args[2:])
	if err != nil {
		fmt.Fprintln(errOut, "Comparison failed:", err)
		return 2
	}
	if err = json.NewEncoder(out).Encode(result); err != nil {
		fmt.Fprintln(errOut, "Output failed.")
		return 2
	}
	return 0
}
func main() { os.Exit(run(os.Args[1:], os.Stdout, os.Stderr)) }
