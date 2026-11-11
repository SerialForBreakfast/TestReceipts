// testreceipts compares structured reports from two recorded CI runs.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/signal"
	"testreceipts/internal/mcp"
	"testreceipts/internal/provider"
	"time"
)

var version = "dev"

func run(args []string, out, errOut io.Writer) int {
	if len(args) == 0 || (len(args) == 1 && (args[0] == "help" || args[0] == "--help")) {
		fmt.Fprintln(out, "TestReceipts: exact CI report comparison\nUsage: testreceipts version | help\n       testreceipts compare-recording RECORDING BEFORE_URL AFTER_URL\n       testreceipts compare-live NEW_CAPTURE BEFORE_URL AFTER_URL\n       testreceipts log-context [--partial] FILE LITERAL\n       testreceipts mcp ROOT")
		return 0
	}
	if len(args) > 0 && args[0] == "log-context" {
		return logCommand(args[1:], out, errOut)
	}
	if len(args) == 1 && args[0] == "version" {
		fmt.Fprintln(out, version)
		return 0
	}
	if len(args) == 2 && args[0] == "mcp" {
		server, e := mcp.New(args[1], version)
		if e == nil {
			base, stop := signal.NotifyContext(context.Background(), os.Interrupt)
			defer stop()
			e = server.Serve(base, os.Stdin, out)
		}
		if e != nil {
			fmt.Fprintln(errOut, "MCP server failed:", e)
			return 2
		}
		return 0
	}
	if len(args) != 4 || (args[0] != "compare-recording" && args[0] != "compare-live") {
		fmt.Fprintln(errOut, "Invalid command. Use testreceipts help.")
		return 2
	}
	var result provider.Object
	var err error
	if args[0] == "compare-live" {
		base, stop := signal.NotifyContext(context.Background(), os.Interrupt)
		defer stop()
		ctx, cancel := context.WithTimeout(base, 5*time.Minute)
		defer cancel()
		result, err = provider.Capture(ctx, provider.NewHTTPSource(), args[1], args[2:])
	} else {
		result, err = provider.Compare(args[1], args[2:])
	}
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
