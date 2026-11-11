package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"regexp"
	"strings"
	"unicode/utf8"
)

type excerpt struct {
	Match int      `json:"matchLine"`
	Start int      `json:"startLine"`
	Lines []string `json:"lines"`
}
type relatedBlock struct {
	Kind  string   `json:"kind"`
	Start int      `json:"startLine"`
	Lines []string `json:"lines"`
}

type logResult struct {
	Related         []relatedBlock `json:"related,omitempty"`
	Source          string         `json:"source"`
	Query           string         `json:"query"`
	Status          string         `json:"status"`
	Coverage        string         `json:"coverage"`
	Reason          string         `json:"reason,omitempty"`
	SHA256          string         `json:"sha256,omitempty"`
	Scanned         int            `json:"linesScanned"`
	Count           int            `json:"matchedLines"`
	Excerpts        []excerpt      `json:"excerpts"`
	Skipped         []int          `json:"skippedLines,omitempty"`
	DeclaredPartial bool           `json:"declaredPartial,omitempty"`
	Omitted         int            `json:"omittedMatches"`
}

func searchLog(path, query string, partial bool) logResult {
	r := logResult{Source: path, Query: query, Status: "unavailable", Coverage: "unavailable", Excerpts: []excerpt{}}
	info, err := os.Stat(path)
	if err != nil || !info.Mode().IsRegular() {
		r.Reason = "not_readable_regular_file"
		if os.IsNotExist(err) {
			r.Reason = "file_missing"
		}
		return r
	}
	f, err := os.Open(path)
	if err != nil {
		r.Reason = "open_failed"
		return r
	}
	defer f.Close()
	const limit = 16 << 20
	if info.Size() > limit {
		r.Reason = "file_size_limit"
		return r
	}
	data, err := io.ReadAll(io.LimitReader(f, limit+1))
	if err != nil || len(data) > limit {
		r.Reason = "read_error_or_file_limit"
		return r
	}
	r.SHA256 = fmt.Sprintf("%x", sha256.Sum256(data))
	r.DeclaredPartial = partial
	r.Coverage = "supplied_file"
	var history []string
	var candidates []excerpt
	segmentStart := 1
	var recent []string
	pendingPackage := ""
	awaitErrors, inErrors := false, false
	summaryStart, summaryEnd := 0, 0
	for len(data) > 0 {
		raw, rest, _ := bytes.Cut(data, []byte{'\n'})
		data = rest
		raw = bytes.TrimSuffix(raw, []byte{'\r'})
		r.Scanned++
		if len(raw) >= 64<<10 {
			r.Skipped = append(r.Skipped, r.Scanned)
			r.Reason = "oversized_lines"
			history = nil
			recent = nil
			pendingPackage = ""
			awaitErrors, inErrors = false, false
			summaryStart, summaryEnd = 0, 0
			segmentStart = r.Scanned + 1
			continue
		}
		if !utf8.Valid(raw) || bytes.IndexByte(raw, 0) >= 0 {
			r.Reason = "unsupported_text"
			break
		}
		line := string(raw)
		// A gotestsum Errors section can follow many package failures. Cite its
		// first compiler diagnostic as section evidence, not a package-specific cause.
		if pendingPackage != "" {
			if line == "FAIL\t"+pendingPackage+" [build failed]" {
				awaitErrors = true
			}
			pendingPackage = ""
		}
		if strings.HasPrefix(line, "DONE ") || strings.HasPrefix(line, "=== RUN") || strings.HasPrefix(line, "+++ ") {
			awaitErrors, inErrors = false, false
		}
		if inErrors && strings.TrimSpace(line) != "" {
			if compilerDiagnostic.MatchString(line) {
				r.Related = append(r.Related, relatedBlock{"errors_section", r.Scanned, []string{line}})
			}
			inErrors = false
		}
		if awaitErrors && line == "=== Errors" {
			awaitErrors, inErrors = false, true
		}
		if suiteSummary.MatchString(line) {
			summaryStart, summaryEnd = r.Scanned, r.Scanned
		} else if summaryStart > 0 && summaryEnd == r.Scanned-1 && summaryEntry(line) {
			summaryEnd = r.Scanned
		}
		for i := range candidates {
			e := &candidates[i]
			insideMatchedSummary := e.Match == summaryStart && r.Scanned == summaryEnd
			if e.Match >= segmentStart && (r.Scanned-e.Match <= summaryRadius || insideMatchedSummary) {
				e.Lines = append(e.Lines, line)
			}
		}
		if strings.Contains(line, query) {
			r.Count++
			if len(candidates) < 8 {
				if fields := strings.Fields(line); len(fields) >= 3 && fields[0] == "===" && fields[1] == "FAIL:" {
					pendingPackage = fields[2]
				}
				if block := namedAssertion(recent, line, r.Scanned); block != nil {
					r.Related = append(r.Related, *block)
				}
				lines := append([]string(nil), history...)
				candidates = append(candidates, excerpt{r.Scanned, r.Scanned - len(history), append(lines, line)})
			}
		}
		recent = append(recent, line)
		if len(recent) > 48 {
			recent = recent[1:]
		}
		history = append(history, line)
		keep := summaryRadius
		if summaryStart > 0 && r.Scanned-summaryEnd <= summaryRadius {
			keep = max(keep, r.Scanned-summaryStart+1+assertionLookback)
		}
		if len(history) > keep {
			history = history[len(history)-keep:]
		}
	}
	for _, e := range candidates {
		r.Excerpts = append(r.Excerpts, summaryContext(e))
	}
	if partial && r.Reason == "" {
		r.Reason = "declared_partial"
	}
	if r.Reason != "" {
		r.Coverage = "partial"
	}
	r.Omitted = r.Count - len(r.Excerpts)
	switch {
	case r.Count > 1:
		r.Status = "ambiguous"
	case r.Coverage == "partial":
		r.Status = "incomplete"
	case r.Count == 1:
		r.Status = "matched"
	default:
		r.Status = "no_match"
	}
	return r
}

const summaryRadius = 20
const assertionLookback = 12

var testDiagnostic = regexp.MustCompile(`_test\.go:[0-9]+:`)
var suiteSummary = regexp.MustCompile(`Summarizing [0-9]+ Failures?:`)

var compilerDiagnostic = regexp.MustCompile(`^.+\.go:[0-9]+:[0-9]+: .+`)
var sourceError = regexp.MustCompile(`\.go:[0-9]+: (context deadline exceeded|Expected |Unexpected error)`)

// Testify reports can be separated from the FAIL marker by shutdown logs.
// Require the exact Test: name and its Messages: field before attaching one.
func namedAssertion(lines []string, marker string, n int) *relatedBlock {
	if !strings.HasPrefix(marker, "--- FAIL: ") {
		return nil
	}
	name, _, _ := strings.Cut(strings.TrimPrefix(marker, "--- FAIL: "), " ")
	for i := len(lines) - 2; i >= 0; i-- {
		t := strings.TrimSpace(lines[i])
		if strings.HasPrefix(t, "=== RUN") || strings.HasPrefix(t, "--- FAIL:") {
			break
		}
		if !strings.HasPrefix(t, "Test:") || strings.TrimSpace(strings.TrimPrefix(t, "Test:")) != name || !strings.HasPrefix(strings.TrimSpace(lines[i+1]), "Messages:") {
			continue
		}
		start := i
		for j := i - 1; j >= max(0, i-8); j-- {
			if strings.Contains(lines[j], ".go:") && strings.Contains(lines[j], ": ERROR:") {
				start = j
				if j > 0 && testDiagnostic.MatchString(lines[j-1]) {
					start--
				}
				break
			}
		}
		return &relatedBlock{"named_assertion", n - len(lines) + start, append([]string(nil), lines[start:i+2]...)}
	}
	return nil
}

var ansiColor = regexp.MustCompile("\x1b" + `\[[0-9;]*m`)

func summaryEntry(line string) bool {
	plain := ansiColor.ReplaceAllString(line, "")
	return strings.TrimSpace(plain) != "" && (strings.HasPrefix(plain, " ") || strings.HasPrefix(plain, "\t"))
}

// Link a single-spec Ginkgo summary to the preceding failure only when the
// summary and the diagnostic cite the same source location.
func diagnosticStart(lines []string, header, fallback int) int {
	clean := func(s string) string { return strings.TrimSpace(ansiColor.ReplaceAllString(s, "")) }
	if clean(lines[header]) != "Summarizing 1 Failure:" || header+2 >= len(lines) || !strings.HasPrefix(clean(lines[header+1]), "[FAIL] ") {
		return fallback
	}
	location := clean(lines[header+2])
	if location == "" {
		return fallback
	}
	for i := header - 1; i >= max(1, header-assertionLookback); i-- {
		text := clean(lines[i])
		if suiteSummary.MatchString(text) || strings.HasPrefix(text, "--- FAIL:") {
			break
		}
		if !strings.HasPrefix(text, "In [It] at: ") {
			continue
		}
		site, _, _ := strings.Cut(strings.TrimPrefix(text, "In [It] at: "), " @ ")
		if site == location && strings.HasPrefix(clean(lines[i-1]), "[FAILED] ") {
			return min(fallback, i-1)
		}
		break
	}
	return fallback
}

// Expand only around recognizable test failure sections. Preserve raw text and physical lines.
func summaryContext(e excerpt) excerpt {
	at := e.Match - e.Start
	lo, hi := max(0, at-2), min(len(e.Lines), at+3)
	if suiteSummary.MatchString(e.Lines[at]) {
		lo = diagnosticStart(e.Lines, at, lo)
		for j := at + 1; j < len(e.Lines) && summaryEntry(e.Lines[j]); j++ {
			hi = max(hi, j+1)
		}
	}
	if strings.TrimSpace(e.Lines[at]) == "Test Suite Failed" {
		for i := at - 1; i >= max(0, at-6); i-- {
			line := strings.TrimSpace(ansiColor.ReplaceAllString(e.Lines[i], ""))
			if strings.HasPrefix(line, "ERROR:") {
				lo = min(lo, i)
				break
			}
			if line == "Test Suite Failed" {
				break
			}
		}
	}
	if strings.HasPrefix(e.Lines[at], "--- FAIL:") {
		for i := at - 1; i >= 0; i-- {
			line := e.Lines[i]
			if strings.HasPrefix(line, "=== RUN") || strings.HasPrefix(line, "--- FAIL:") {
				break
			}
			if suiteSummary.MatchString(line) {
				lo = diagnosticStart(e.Lines, i, min(lo, i))
				// Include a nearby assertion block preceding the summary.
				for j := i - 1; j >= max(0, i-assertionLookback); j-- {
					text := strings.TrimSpace(ansiColor.ReplaceAllString(e.Lines[j], ""))
					if suiteSummary.MatchString(text) || strings.HasPrefix(text, "--- FAIL:") {
						break
					}
					if strings.HasPrefix(text, "[FAILED] Expected") {
						lo = j
						break
					}
				}
				break
			}
			if testDiagnostic.MatchString(line) || sourceError.MatchString(line) {
				lo = min(lo, i)
			}
		}
	}
	if strings.Contains(e.Lines[at], "[setup failed]") {
		for i := at + 1; i < len(e.Lines); i++ {
			if strings.TrimSpace(e.Lines[i]) == "" {
				continue
			}
			if strings.TrimSpace(e.Lines[i]) == "=== Errors" {
				for j := i + 1; j < len(e.Lines); j++ {
					line := e.Lines[j]
					if strings.HasPrefix(line, "===") || strings.HasPrefix(line, "DONE ") {
						break
					}
					if line != "" {
						hi = max(hi, j+1)
					} else if j > i+1 && e.Lines[j-1] == "" {
						break
					}
				}
			}
			break
		}
	}
	e.Start += lo
	e.Lines = e.Lines[lo:hi]
	return e
}

func logCommand(args []string, out, errOut io.Writer) int {
	flags := flag.NewFlagSet("log-context", flag.ContinueOnError)
	flags.SetOutput(errOut)
	partial := flags.Bool("partial", false, "supplied log is known to be incomplete")
	if flags.Parse(args) != nil || flags.NArg() != 2 || strings.TrimSpace(flags.Arg(1)) == "" || strings.ContainsAny(flags.Arg(1), "\r\n") {
		fmt.Fprintln(errOut, "Usage: testreceipts log-context [--partial] FILE LITERAL")
		return 2
	}
	r := searchLog(flags.Arg(0), flags.Arg(1), *partial)
	if err := json.NewEncoder(out).Encode(r); err != nil {
		fmt.Fprintln(errOut, err)
		return 2
	}
	if r.Coverage == "unavailable" {
		return 2
	}
	return 0
}
