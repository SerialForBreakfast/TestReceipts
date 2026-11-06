package provider

import (
	"crypto/md5"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"testing"
	"testreceipts/internal/evidence"
)

var urls = []string{"https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100", "https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200"}

func TestGoldenPairs(t *testing.T) {
	paths, err := filepath.Glob("../../testdata/cases/*")
	if err != nil {
		t.Fatal(err)
	}
	for _, p := range paths {
		t.Run(filepath.Base(p), func(t *testing.T) {
			got, err := Compare(p, urls)
			if err != nil {
				t.Fatal(err)
			}
			raw, _ := os.ReadFile(filepath.Join(p, "expected.json"))
			var want, normalized any
			json.Unmarshal(raw, &want)
			encoded, _ := json.Marshal(got)
			json.Unmarshal(encoded, &normalized)
			if !reflect.DeepEqual(want, normalized) {
				t.Fatalf("mismatch\n%s", encoded)
			}
		})
	}
}
func copyCase(t *testing.T) string {
	t.Helper()
	dst := t.TempDir()
	err := filepath.WalkDir("../../testdata/cases/changes", func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel("../../testdata/cases/changes", path)
		target := filepath.Join(dst, rel)
		if d.IsDir() {
			return os.MkdirAll(target, 0755)
		}
		raw, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		return os.WriteFile(target, raw, 0644)
	})
	if err != nil {
		t.Fatal(err)
	}
	return dst
}
func load(t *testing.T, path string) Object {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	v, err := strictJSON(raw)
	if err != nil {
		t.Fatal(err)
	}
	m, err := obj(v)
	if err != nil {
		t.Fatal(err)
	}
	return m
}
func save(t *testing.T, path string, v any) {
	t.Helper()
	raw, err := json.Marshal(v)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(path, raw, 0644); err != nil {
		t.Fatal(err)
	}
}
func TestStrictJSON(t *testing.T) {
	for _, s := range []string{`{"x":1,"x":2}`, `{} {}`, `{"x":1.2}`, `[`, strings.Repeat("[", 130) + strings.Repeat("]", 130)} {
		if _, err := strictJSON([]byte(s)); err == nil {
			t.Error("accepted", s)
		}
	}
}
func TestPathEscapes(t *testing.T) {
	for _, kind := range []string{"absolute", "parent", "symlink", "backslash"} {
		t.Run(kind, func(t *testing.T) {
			root := copyCase(t)
			catalog := load(t, filepath.Join(root, "catalog.json"))
			runs := catalog["runs"].(Object)
			switch kind {
			case "absolute":
				runs[urls[0]] = "/etc/passwd"
			case "parent":
				runs[urls[0]] = "../catalog.json"
			case "backslash":
				runs[urls[0]] = `..\catalog.json`
			case "symlink":
				if err := os.Symlink(os.TempDir(), filepath.Join(root, "escape")); err != nil {
					t.Skip(err)
				}
				runs[urls[0]] = "escape/outside"
			}
			save(t, filepath.Join(root, "catalog.json"), catalog)
			if _, err := Compare(root, urls); err == nil {
				t.Fatal("accepted escaped path")
			}
		})
	}
}
func TestListingFailures(t *testing.T) {
	for _, kind := range []string{"duplicate", "cycle", "missing-page", "scope", "negative-size", "bad-md5", "unreachable"} {
		t.Run(kind, func(t *testing.T) {
			root := copyCase(t)
			p := filepath.Join(root, "pages-0.json")
			raw, _ := os.ReadFile(p)
			v, _ := strictJSON(raw)
			pages := v.([]any)
			page := pages[0].(Object)
			item := page["items"].([]any)[0].(Object)
			switch kind {
			case "duplicate":
				page["items"] = []any{item, item}
			case "cycle":
				page["nextPageToken"] = "x"
				pages = append(pages, page)
			case "missing-page":
				page["nextPageToken"] = "x"
			case "scope":
				item["name"] = "logs/test/999/else.xml"
			case "negative-size":
				item["size"] = "-1"
			case "bad-md5":
				item["md5Hash"] = "invalid"
			case "unreachable":
				pages = append(pages, page)
			}
			save(t, p, pages)
			if _, err := Compare(root, urls); err == nil {
				t.Fatal("accepted bad listing")
			}
		})
	}
}
func TestAcquisitionAndFreshValidation(t *testing.T) {
	root := copyCase(t)
	if _, err := Compare(root, urls); err != nil {
		t.Fatal(err)
	}
	files, _ := filepath.Glob(filepath.Join(root, "objects", "*"))
	for _, p := range files {
		os.WriteFile(p, []byte("tampered"), 0644)
	}
	got, err := Compare(root, urls)
	if err != nil {
		t.Fatal(err)
	}
	for _, run := range got["runs"].([]Object) {
		if run["artifactComplete"] != false || run["includedReports"] != 0 || len(run["unresolvedObjects"].([]Object)) != 1 {
			t.Fatalf("tampering hidden %+v", run)
		}
	}
}
func TestBudgets(t *testing.T) {
	root := copyCase(t)
	p := filepath.Join(root, "pages-0.json")
	raw, _ := os.ReadFile(p)
	v, _ := strictJSON(raw)
	pages := v.([]any)
	item := pages[0].(Object)["items"].([]any)[0].(Object)
	item["size"] = "16777217"
	save(t, p, pages)
	got, err := Compare(root, urls)
	if err != nil {
		t.Fatal(err)
	}
	run := got["runs"].([]Object)[0]
	if run["unresolvedObjects"].([]Object)[0]["reason"] != "xml_budget_exceeded" {
		t.Fatal("budget not preserved")
	}
}

func TestRetainedSHA(t *testing.T) {
	root := copyCase(t)
	path := filepath.Join(root, "catalog.json")
	catalog := load(t, path)
	for _, entry := range catalog["objects"].(Object) {
		entry.(Object)["sha256"] = strings.Repeat("0", 64)
	}
	save(t, path, catalog)
	if _, err := Compare(root, urls); err == nil || err.Error() != "source_hash_mismatch" {
		t.Fatal("retained hash was ignored", err)
	}
}
func TestExistingSymlinkEscapes(t *testing.T) {
	for _, target := range []string{"listing", "object"} {
		t.Run(target, func(t *testing.T) {
			root := copyCase(t)
			outside := filepath.Join(t.TempDir(), "outside")
			os.WriteFile(outside, []byte(`[]`), 0644)
			catalog := load(t, filepath.Join(root, "catalog.json"))
			if err := os.Symlink(outside, filepath.Join(root, "escape")); err != nil {
				t.Skip(err)
			}
			if target == "listing" {
				catalog["runs"].(Object)[urls[0]] = "escape"
			} else {
				for _, entry := range catalog["objects"].(Object) {
					entry.(Object)["path"] = "escape"
				}
			}
			save(t, filepath.Join(root, "catalog.json"), catalog)
			if _, err := Compare(root, urls); err == nil || err.Error() != "out_of_scope_path" {
				t.Fatal("symlink escaped", err)
			}
		})
	}
}
func TestListingBounds(t *testing.T) {
	for _, kind := range []string{"pages", "objects", "json"} {
		t.Run(kind, func(t *testing.T) {
			root := copyCase(t)
			path := filepath.Join(root, "pages-0.json")
			switch kind {
			case "pages":
				pages := make([]any, MaxPages+1)
				for i := range pages {
					pages[i] = Object{}
				}
				save(t, path, pages)
			case "objects":
				items := make([]any, MaxObjects+1)
				for i := range items {
					items[i] = Object{}
				}
				save(t, path, []any{Object{"items": items}})
			case "json":
				os.WriteFile(path, []byte(strings.Repeat(" ", MaxJSON+1)), 0644)
			}
			if _, err := Compare(root, urls); err == nil {
				t.Fatal("budget accepted")
			}
		})
	}
}

func repeatedRecording(t *testing.T, n int, raw []byte) string {
	t.Helper()
	root := t.TempDir()
	os.WriteFile(filepath.Join(root, "shared.xml"), raw, 0644)
	md := md5.Sum(raw)
	items := []any{}
	objects := Object{}
	for i := 0; i < n; i++ {
		name := fmt.Sprintf("logs/test/100/artifacts/%05d.xml", i)
		items = append(items, Object{"name": name, "generation": "1", "size": strconv.Itoa(len(raw)), "md5Hash": base64.StdEncoding.EncodeToString(md[:])})
		objects[evidence.Hash([]string{name, "1"})] = Object{"path": "shared.xml"}
	}
	save(t, filepath.Join(root, "pages-0.json"), []any{Object{"items": items}})
	save(t, filepath.Join(root, "pages-1.json"), []any{Object{"items": []any{}}})
	save(t, filepath.Join(root, "catalog.json"), Object{"runs": Object{urls[0]: "pages-0.json", urls[1]: "pages-1.json"}, "objects": objects})
	return root
}
func TestReportCountBudget(t *testing.T) {
	root := repeatedRecording(t, 2049, []byte("<testsuite><testcase/></testsuite>"))
	if _, err := Compare(root, urls); err == nil || err.Error() != "report_count_budget_exceeded" {
		t.Fatal("report budget ignored", err)
	}
}
func TestCollectionBudget(t *testing.T) {
	raw := []byte("<config>" + strings.Repeat(" ", 12*1024*1024) + "</config>")
	root := repeatedRecording(t, 3, raw)
	got, err := Compare(root, urls)
	if err != nil {
		t.Fatal(err)
	}
	run := got["runs"].([]Object)[0]
	rows := run["unresolvedObjects"].([]Object)
	if len(rows) != 1 || rows[0]["reason"] != "xml_collection_budget_exceeded" || run["artifactComplete"] != false {
		t.Fatal("collection budget hidden", run)
	}
}

func TestJSONUnicodeAndNumbers(t *testing.T) {
	for _, s := range []string{`{"x":"\ud800"}`, `{"x":"\udc00"}`, `{"x":"\ud800\u0041"}`, string([]byte{'"', 255, '"'})} {
		if _, err := strictJSON([]byte(s)); err == nil {
			t.Fatal("accepted invalid Unicode", s)
		}
	}
	v, err := strictJSON([]byte(`{"x":"\ud83d\ude42","n":-0}`))
	if err != nil || string(evidence.Canonical(v)) != `{"n":0,"x":"🙂"}` {
		t.Fatal("canonical JSON changed", v, err)
	}
}
