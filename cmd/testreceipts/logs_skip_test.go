package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestLogSkipPreservesCitations(t *testing.T) {
	path := filepath.Join(t.TempDir(), "step.log")
	large := strings.Repeat("x", 64<<10)
	if err := os.WriteFile(path, []byte("hit before\r\n"+large+"\r\nhit after\n"+large), 0600); err != nil {
		t.Fatal(err)
	}
	r := searchLog(path, "hit", true)
	if r.Status != "ambiguous" || r.Coverage != "partial" || !r.DeclaredPartial || r.Scanned != 4 || r.Count != 2 || len(r.Skipped) != 2 || r.Skipped[0] != 2 || r.Skipped[1] != 4 {
		t.Fatalf("unexpected result %+v", r)
	}
	for i, e := range r.Excerpts {
		if e.Match != 2*i+1 || e.Start != e.Match || len(e.Lines) != 1 {
			t.Fatalf("excerpt crossed skipped line: %+v", e)
		}
	}
}

func TestLongSummaryBoundary(t *testing.T) {
	path := filepath.Join(t.TempDir(), "step.log")
	body := "Summarizing 30 Failures:\n" + strings.Repeat("  [FAIL] example\n  spec.go:10\n", 30) + "\nRan 30 Specs\n--- FAIL: TestExample\n"
	if err := os.WriteFile(path, []byte(body), 0600); err != nil {
		t.Fatal(err)
	}
	direct := searchLog(path, "Summarizing", false).Excerpts[0]
	if direct.Start != 1 || len(direct.Lines) != 61 {
		t.Fatalf("summary start %d, length %d", direct.Start, len(direct.Lines))
	}
	trailing := searchLog(path, "--- FAIL:", false).Excerpts[0]
	if trailing.Start != 1 || trailing.Match != 64 {
		t.Fatalf("trailing match %d, start %d", trailing.Match, trailing.Start)
	}
}

func TestSummaryDiagnosticRequiresSameSite(t *testing.T) {
	for _, site := range []string{"resize.go:42", "resize.go:420"} {
		lines := []string{"[FAILED] operation timed out", "In [It] at: resize.go:42 @ yesterday", "---", "", "", "Summarizing 1 Failure:", "  [FAIL] spec", "  " + site}
		got := summaryContext(excerpt{Match: 6, Start: 1, Lines: lines})
		want := 4
		if site == "resize.go:42" {
			want = 1
		}
		if got.Start != want {
			t.Errorf("site %s: start %d, want %d", site, got.Start, want)
		}
	}
}

func TestRelatedEvidenceBoundaries(t *testing.T) {
	if namedAssertion([]string{"Test: OtherTest", "Messages: expected expiry"}, "--- FAIL: SomeTest (1s)", 3) != nil {
		t.Fatal("used another test's assertion")
	}
	path := filepath.Join(t.TempDir(), "build.log")
	data := "=== FAIL: pkg/example (0s)\nFAIL\tpkg/example [build failed]\nDONE 1 test\n=== Errors\nfile.go:3:4: undefined: x\n"
	if err := os.WriteFile(path, []byte(data), 0600); err != nil {
		t.Fatal(err)
	}
	if r := searchLog(path, "=== FAIL: pkg/example", false); len(r.Related) != 0 {
		t.Fatal("attached diagnostic from a different batch")
	}
}
