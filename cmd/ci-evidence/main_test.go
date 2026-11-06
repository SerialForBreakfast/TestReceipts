package main

import (
	"bytes"
	"strings"
	"testing"
)

func TestUnimplementedComparisonDoesNotClaimSuccess(t *testing.T) {
	var out, errOut bytes.Buffer
	if code := run([]string{"compare-recording", "missing", "before", "after"}, &out, &errOut); code == 0 {
		t.Fatal("unimplemented comparison must fail")
	}
	if out.Len() != 0 || !strings.Contains(errOut.String(), "not implemented") {
		t.Fatal("must explain that no comparison occurred")
	}
}
