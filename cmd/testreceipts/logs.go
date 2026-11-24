package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"strings"
	"testreceipts/internal/logcontext"
)

func logCommand(args []string, out, errOut io.Writer) int {
	flags := flag.NewFlagSet("log-context", flag.ContinueOnError)
	flags.SetOutput(errOut)
	partial := flags.Bool("partial", false, "supplied log is known to be incomplete")
	if flags.Parse(args) != nil || flags.NArg() != 2 || strings.TrimSpace(flags.Arg(1)) == "" || strings.ContainsAny(flags.Arg(1), "\r\n") {
		fmt.Fprintln(errOut, "Usage: testreceipts log-context [--partial] FILE LITERAL")
		return 2
	}
	r := logcontext.Search(flags.Arg(0), flags.Arg(1), *partial)
	if err := json.NewEncoder(out).Encode(r); err != nil {
		fmt.Fprintln(errOut, err)
		return 2
	}
	if r.Coverage == "unavailable" {
		return 2
	}
	return 0
}
