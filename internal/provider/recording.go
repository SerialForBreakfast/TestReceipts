// Package provider reads bounded local recordings. Recorded URLs never trigger HTTP.
package provider

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/big"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"testreceipts/internal/evidence"
	"testreceipts/internal/junit"
	"unicode/utf8"
)

type Object = evidence.Object

const MaxJSON = 8 * 1024 * 1024
const MaxPages = 1024
const MaxObjects = 16384
const MaxCapture = 32 * 1024 * 1024

// strictJSON rejects duplicate keys, trailing data and non-integer JSON numbers.
func strictJSON(raw []byte) (any, error) {
	if !utf8.Valid(raw) || !json.Valid(raw) {
		return nil, errors.New("invalid_json")
	}
	// Reject lone surrogate escapes instead of silently replacing diagnostic identity.
	for i := 0; i < len(raw); i++ {
		if raw[i] != '\\' {
			continue
		}
		if raw[i+1] != 'u' {
			i++
			continue
		}
		v, _ := strconv.ParseUint(string(raw[i+2:i+6]), 16, 16)
		if v >= 0xd800 && v <= 0xdbff {
			if i+12 > len(raw) || string(raw[i+6:i+8]) != `\u` {
				return nil, errors.New("invalid_unicode_escape")
			}
			low, _ := strconv.ParseUint(string(raw[i+8:i+12]), 16, 16)
			if low < 0xdc00 || low > 0xdfff {
				return nil, errors.New("invalid_unicode_escape")
			}
			i += 11
		} else if v >= 0xdc00 && v <= 0xdfff {
			return nil, errors.New("invalid_unicode_escape")
		} else {
			i += 5
		}
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.UseNumber()
	var read func(int) (any, error)
	read = func(depth int) (any, error) {
		if depth > 128 {
			return nil, errors.New("json_depth_budget")
		}
		t, err := d.Token()
		if err != nil {
			return nil, err
		}
		switch x := t.(type) {
		case json.Delim:
			switch x {
			case '{':
				m := Object{}
				for d.More() {
					k, e := d.Token()
					if e != nil {
						return nil, e
					}
					s, ok := k.(string)
					if !ok {
						return nil, errors.New("invalid_json_key")
					}
					if _, ok = m[s]; ok {
						return nil, errors.New("duplicate_json_key")
					}
					v, e := read(depth + 1)
					if e != nil {
						return nil, e
					}
					m[s] = v
				}
				_, err = d.Token()
				return m, err
			case '[':
				a := []any{}
				for d.More() {
					v, e := read(depth + 1)
					if e != nil {
						return nil, e
					}
					a = append(a, v)
				}
				_, err = d.Token()
				return a, err
			}
		case json.Number:
			if strings.ContainsAny(string(x), ".eE") {
				return nil, errors.New("noninteger_json_number")
			}
			if len(x) > 4096 {
				return nil, errors.New("json_integer_budget")
			}
			normalized, ok := new(big.Int).SetString(string(x), 10)
			if !ok {
				return nil, errors.New("invalid_json_number")
			}
			return json.Number(normalized.String()), nil
		default:
			return t, nil
		}
		return nil, errors.New("invalid_json")
	}
	v, err := read(0)
	if err != nil {
		return nil, err
	}
	if _, err = d.Token(); err != io.EOF {
		return nil, errors.New("trailing_json")
	}
	return v, nil
}
func readBound(path string, limit int) ([]byte, error) {
	st, err := os.Stat(path)
	if err != nil || !st.Mode().IsRegular() {
		return nil, errors.New("not_regular_file")
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, errors.New("unavailable_file")
	}
	defer f.Close()
	st, err = f.Stat()
	if err != nil || !st.Mode().IsRegular() {
		return nil, errors.New("not_regular_file")
	}
	if st.Size() > int64(limit) {
		return nil, errors.New("file_budget_exceeded")
	}
	raw, err := io.ReadAll(io.LimitReader(f, int64(limit)+1))
	if err != nil || len(raw) > limit {
		return nil, errors.New("file_budget_exceeded")
	}
	return raw, nil
}
func safePath(root, relative string) (string, error) {
	if relative == "" || filepath.IsAbs(relative) || strings.Contains(relative, "\\") || strings.Contains(relative, ":") {
		return "", errors.New("out_of_scope_path")
	}
	for _, p := range strings.Split(relative, "/") {
		if p == ".." {
			return "", errors.New("out_of_scope_path")
		}
	}
	p, err := filepath.EvalSymlinks(filepath.Join(root, filepath.FromSlash(relative)))
	if err != nil {
		return "", errors.New("unavailable_file")
	}
	r, err := filepath.Rel(root, p)
	if err != nil || r == ".." || strings.HasPrefix(r, ".."+string(filepath.Separator)) {
		return "", errors.New("out_of_scope_path")
	}
	return p, nil
}
func readJSON(root, path string) (any, error) {
	p, err := safePath(root, path)
	if err != nil {
		return nil, err
	}
	raw, err := readBound(p, MaxJSON)
	if err != nil {
		return nil, err
	}
	return strictJSON(raw)
}
func obj(v any) (Object, error) {
	m, ok := v.(map[string]any)
	if !ok {
		return nil, errors.New("expected_object")
	}
	return m, nil
}
func str(m Object, k string) (string, error) {
	v, ok := m[k].(string)
	if !ok || v == "" {
		return "", fmt.Errorf("invalid_%s", k)
	}
	return v, nil
}

// Compare performs both runs from fresh bytes. There is no cache to bypass validation.
func Compare(root string, urls []string) (Object, error) {
	if len(urls) != 2 {
		return nil, errors.New("two_run_urls_required")
	}
	root, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	root, err = filepath.EvalSymlinks(root)
	if err != nil {
		return nil, errors.New("unavailable_recording")
	}
	v, err := readJSON(root, "catalog.json")
	if err != nil {
		return nil, err
	}
	catalog, err := obj(v)
	if err != nil {
		return nil, err
	}
	runs, err := obj(catalog["runs"])
	if err != nil {
		return nil, err
	}
	objects, err := obj(catalog["objects"])
	if err != nil {
		return nil, err
	}
	acquisition := Object{}
	if v, ok := catalog["acquisition"]; ok {
		acquisition, err = obj(v)
		if err != nil {
			return nil, err
		}
	}
	snapshots := []Object{}
	groups := []map[string]Object{}
	for _, u := range urls {
		snapshot, g, err := run(root, u, runs, objects, acquisition)
		if err != nil {
			return nil, err
		}
		snapshots = append(snapshots, snapshot)
		groups = append(groups, g)
	}
	result := evidence.Compare(snapshots, groups)
	if len(acquisition) > 0 {
		complete := true
		for _, s := range snapshots {
			if s["artifactComplete"] != true || s["parserCoverage"].(Object)["complete"] != true || len(s["parserCoverage"].(Object)["limitations"].([]string)) > 0 {
				complete = false
			}
		}
		result["comparisonComplete"] = complete
	}
	return result, nil
}
func run(root, u string, runs, objects, acquisition Object) (Object, map[string]Object, error) {
	listingComplete := true
	var discovery Object
	if len(acquisition) > 0 {
		v, ok := acquisition[u]
		if !ok {
			return nil, nil, errors.New("missing_acquisition_coverage")
		}
		var e error
		discovery, e = obj(v)
		if e != nil {
			return nil, nil, e
		}
		var valid bool
		listingComplete, valid = discovery["complete"].(bool)
		if !valid {
			return nil, nil, errors.New("invalid_acquisition_coverage")
		}
		rows, ok := discovery["unresolved"].([]any)
		if !ok {
			return nil, nil, errors.New("invalid_acquisition_issues")
		}
		for _, v := range rows {
			if _, ok := v.(string); !ok {
				return nil, nil, errors.New("invalid_acquisition_issue")
			}
		}
		if listingComplete && len(rows) > 0 || !listingComplete && len(rows) == 0 {
			return nil, nil, errors.New("contradictory_acquisition_coverage")
		}
	}
	path, err := str(runs, u)
	if err != nil {
		return nil, nil, errors.New("unrecorded_run_url")
	}
	v, err := readJSON(root, path)
	if err != nil {
		return nil, nil, err
	}
	all, ok := v.([]any)
	if !ok || len(all) == 0 || len(all) > MaxPages {
		return nil, nil, errors.New("listing_page_budget_or_shape")
	}
	parsed, err := url.Parse(u)
	if err != nil || parsed.Scheme != "https" || parsed.Host != "prow.k8s.io" || parsed.RawQuery != "" || parsed.Fragment != "" || parsed.User != nil {
		return nil, nil, errors.New("unsupported_recorded_url")
	}
	const prefix = "/view/gs/kubernetes-ci-logs/"
	if !strings.HasPrefix(parsed.Path, prefix) {
		return nil, nil, errors.New("unsupported_recorded_url")
	}
	scope := strings.TrimSuffix(strings.TrimPrefix(parsed.Path, prefix), "/") + "/"
	for _, p := range strings.Split(scope, "/") {
		if p == ".." || p == "." {
			return nil, nil, errors.New("out_of_scope_run")
		}
	}
	pages := []any{}
	items := map[string]Object{}
	tokens := map[string]bool{}
	totalObjects := 0
	for i, p := range all {
		page, err := obj(p)
		if err != nil {
			return nil, nil, err
		}
		pages = append(pages, page)
		if values, exists := page["items"]; exists {
			a, ok := values.([]any)
			if !ok {
				return nil, nil, errors.New("invalid_listing_items")
			}
			totalObjects += len(a)
			if totalObjects > MaxObjects {
				return nil, nil, errors.New("listing_object_budget")
			}
			for _, v := range a {
				item, err := obj(v)
				if err != nil {
					return nil, nil, err
				}
				name, err := str(item, "name")
				if err != nil {
					return nil, nil, err
				}
				if !strings.HasPrefix(name, scope) {
					return nil, nil, errors.New("out_of_scope_object")
				}
				for _, p := range strings.Split(name, "/") {
					if p == ".." || p == "." || strings.Contains(p, "\\") {
						return nil, nil, errors.New("out_of_scope_object")
					}
				}
				if !strings.HasSuffix(strings.ToLower(name), ".xml") {
					continue
				}
				if _, ok := items[name]; ok {
					return nil, nil, errors.New("duplicate_listing_object")
				}
				items[name] = item
			}
		}
		token := ""
		if t, exists := page["nextPageToken"]; exists {
			var ok bool
			token, ok = t.(string)
			if !ok {
				return nil, nil, errors.New("invalid_page_token")
			}
		}
		if token == "" {
			if i != len(all)-1 {
				return nil, nil, errors.New("unreachable_listing_pages")
			}
			break
		}
		if tokens[token] && !(!listingComplete && i == len(all)-1) {
			return nil, nil, errors.New("pagination_cycle")
		}
		tokens[token] = true
		if i == len(all)-1 && listingComplete {
			return nil, nil, errors.New("missing_listing_page")
		}
	}
	names := make([]string, 0, len(items))
	for n := range items {
		names = append(names, n)
	}
	sort.Strings(names)
	rows := []Object{}
	excluded := []Object{}
	unresolved := []Object{}
	unknown := map[string]bool{}
	limits := map[string]bool{}
	counts := Object{"attempts": 0, "passed": 0, "failure": 0, "error": 0, "skipped": 0}
	groups := map[string]Object{}
	captured, input, included := 0, 0, 0
	for _, name := range names {
		item := items[name]
		generation, err := str(item, "generation")
		if err != nil {
			return nil, nil, err
		}
		sizeString, err := str(item, "size")
		if err != nil {
			return nil, nil, err
		}
		size, e := strconv.ParseInt(sizeString, 10, 64)
		if e != nil || size < 0 {
			return nil, nil, errors.New("invalid_object_size")
		}
		if v, ok := item["md5Hash"]; ok {
			s, ok := v.(string)
			if !ok {
				return nil, nil, errors.New("invalid_object_md5")
			}
			b, e := base64.StdEncoding.DecodeString(s)
			if e != nil || len(b) != 16 {
				return nil, nil, errors.New("invalid_object_md5")
			}
		}
		disposition, reason := "blocked", ""
		var sha any
		var raw []byte
		if size > junit.MaxXML {
			reason = "xml_budget_exceeded"
		} else if int64(captured)+size > MaxCapture {
			reason = "xml_collection_budget_exceeded"
		} else {
			key := evidence.Hash([]string{name, generation})
			entry, exists := objects[key]
			if !exists {
				reason = "acquisition_error"
			} else {
				m, err := obj(entry)
				if err != nil {
					return nil, nil, err
				}
				if _, ok := m["error"]; ok {
					reason = "acquisition_error"
				} else {
					p, err := str(m, "path")
					if err != nil {
						return nil, nil, err
					}
					p, err = safePath(root, p)
					if err != nil {
						if err.Error() == "out_of_scope_path" {
							return nil, nil, err
						}
						reason = "acquisition_error"
					} else {
						raw, err = readBound(p, junit.MaxXML)
						if err != nil {
							reason = "acquisition_error"
						} else {
							if verifyObject(raw, item) != nil {
								reason = "acquisition_error"
							}
						}
					}
				}
			}
			if reason == "" {
				captured += len(raw)
				sha = evidence.Digest(raw)
				if m, ok := entry.(map[string]any); ok {
					if expected, exists := m["sha256"]; exists && expected != sha {
						return nil, nil, errors.New("source_hash_mismatch")
					}
				}
				report := junit.Parse(raw)
				disposition, reason = report.Disposition, report.Reason
				if disposition == "junit" {
					included++
					if included > 2048 {
						return nil, nil, errors.New("report_count_budget_exceeded")
					}
					input += len(raw)
					for k, v := range report.Counts {
						counts[k] = counts[k].(int) + v.(int)
					}
					for k := range report.Unknown {
						unknown[k] = true
					}
					for k := range report.Limitations {
						limits[k] = true
					}
					for k, g := range report.Groups {
						if g["kind"] != "failure" && g["kind"] != "error" {
							continue
						}
						if old, ok := groups[k]; ok {
							old["occurrences"] = old["occurrences"].(int) + g["occurrences"].(int)
						} else {
							groups[k] = g
						}
					}
				}
			}
		}
		rows = append(rows, Object{"name": name, "generation": generation, "sha256": sha, "disposition": disposition, "reason": reason})
		if disposition == "blocked" {
			unresolved = append(unresolved, Object{"name": name, "reason": reason})
		}
		if disposition == "non-junit" {
			excluded = append(excluded, Object{"name": name, "reason": reason})
		}
	}
	if included == 0 {
		unknown["no_junit_reports"] = true
	}
	snapshot := Object{"url": u, "xmlCandidates": len(rows), "includedReports": included, "excludedObjects": excluded, "unresolvedObjects": unresolved, "artifactComplete": len(unresolved) == 0 && listingComplete, "inventorySha256": evidence.Hash(rows), "listingSha256": evidence.Hash(pages), "inputBytes": input, "counts": counts, "parserCoverage": Object{"complete": len(unknown) == 0, "unresolved": evidence.Sorted(unknown), "limitations": evidence.Sorted(limits)}, "distinctFailures": len(groups)}
	if discovery != nil {
		snapshot["discoveryCoverage"] = discovery
	}
	return snapshot, groups, nil
}
