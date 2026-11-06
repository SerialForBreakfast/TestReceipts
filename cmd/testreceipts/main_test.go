package main

import (
	"bytes"
	"encoding/json"
	"testing"
)

func TestCLI(t *testing.T) {
	for _, args := range [][]string{{"help"}, {"version"}, {"compare-recording", "../../testdata/cases/changes", "https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100", "https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200"}} {
		var out, errOut bytes.Buffer
		if code := run(args, &out, &errOut); code != 0 || errOut.Len() != 0 {
			t.Fatalf("%v: code %d %s", args, code, errOut.String())
		}
		if args[0] == "compare-recording" && !json.Valid(out.Bytes()) {
			t.Fatal("invalid JSON")
		}
	}
}
func TestErrors(t *testing.T) {
	for _, args := range [][]string{{"unknown"}, {"compare-recording"}, {"compare-recording", "missing", "before", "after"}, {"help", "extra"}} {
		var out, errOut bytes.Buffer
		if code := run(args, &out, &errOut); code == 0 || out.Len() != 0 || errOut.Len() == 0 {
			t.Fatalf("bad error behavior %v", args)
		}
	}
}
