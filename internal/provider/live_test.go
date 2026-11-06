package provider

import (
	"context"
	"crypto/md5"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"hash/crc32"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"sync/atomic"
	"testing"
	"testreceipts/internal/evidence"
	"time"
)

func liveItem(run int, raw []byte) Object {
	m := md5.Sum(raw)
	b := make([]byte, 4)
	binary.BigEndian.PutUint32(b, crc32.Checksum(raw, crc32.MakeTable(crc32.Castagnoli)))
	return Object{"name": "logs/test/" + strconv.Itoa(run) + "/artifacts/generic.XML", "generation": "12", "size": strconv.Itoa(len(raw)), "md5Hash": base64.StdEncoding.EncodeToString(m[:]), "crc32c": base64.StdEncoding.EncodeToString(b)}
}
func serverSource(t *testing.T, handler http.HandlerFunc) *HTTPSource {
	t.Helper()
	server := httptest.NewServer(handler)
	t.Cleanup(server.Close)
	s := newHTTPSource(server.URL, server.Client().Transport)
	s.delay = 0
	return s
}
func TestLiveURLs(t *testing.T) {
	for _, u := range []string{"http://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/a/1", "https://evil.test/view/gs/kubernetes-ci-logs/logs/a/1", "https://prow.k8s.io/view/gs/other/logs/a/1", urls[0] + "?x=1", urls[0] + "#x", "https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/../1", "https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/%74est/100", "file:///tmp/a", "https://user@prow.k8s.io/view/gs/kubernetes-ci-logs/logs/a/1"} {
		if _, err := RunScope(u); err == nil {
			t.Fatal("accepted", u)
		}
	}
	for _, u := range []string{urls[0], "https://prow.k8s.io/view/gs/kubernetes-ci-logs/pr-logs/pull/kubernetes_kubernetes/123/job/456"} {
		if _, err := RunScope(u); err != nil {
			t.Fatal(err)
		}
	}
}
func TestLiveCaptureReplay(t *testing.T) {
	raw := []byte(`<testsuite><testcase><failure>exact</failure></testcase></testsuite>`)
	s := serverSource(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("alt") == "media" {
			if r.URL.Query().Get("generation") != "12" {
				t.Error("generation missing")
			}
			w.Header().Set("X-Goog-Generation", "12")
			w.Write(raw)
			return
		}
		run := 100
		if strings.Contains(r.URL.Query().Get("prefix"), "200") {
			run = 200
		}
		json.NewEncoder(w).Encode(Object{"items": []any{liveItem(run, raw)}})
	})
	dir := filepath.Join(t.TempDir(), "capture 界")
	got, err := Capture(context.Background(), s, dir, urls)
	if err != nil {
		t.Fatal(err)
	}
	want, err := Compare(dir, urls)
	if err != nil || !reflect.DeepEqual(got, want) {
		t.Fatal("replay mismatch", err)
	}
	if got["comparisonComplete"] != true || s.Requests != 4 {
		t.Fatal(got)
	}
	if _, err = Capture(context.Background(), s, dir, urls); err == nil {
		t.Fatal("overwrote capture")
	}
	if _, err = os.Stat(filepath.Join(dir, "responses", "001.body")); err != nil {
		t.Fatal(err)
	}
}
func TestHTTPFailures(t *testing.T) {
	for _, kind := range []string{"rate-limit", "server-recovery", "not-found", "redirect", "generation", "body", "timeout", "encoding"} {
		t.Run(kind, func(t *testing.T) {
			var calls atomic.Int32
			s := serverSource(t, func(w http.ResponseWriter, r *http.Request) {
				calls.Add(1)
				switch kind {
				case "rate-limit":
					w.Header().Set("Retry-After", "0")
					w.WriteHeader(429)
				case "server-recovery":
					if calls.Load() < 3 {
						w.WriteHeader(503)
					} else {
						w.Write([]byte("ok"))
					}
				case "not-found":
					w.WriteHeader(404)
				case "redirect":
					http.Redirect(w, r, "https://example.com/escape", 302)
				case "generation":
					w.Header().Set("X-Goog-Generation", "13")
					w.Write([]byte("ok"))
				case "body":
					w.Write([]byte(strings.Repeat("x", 1025)))
				case "timeout":
					time.Sleep(30 * time.Millisecond)
					w.Write([]byte("ok"))
				case "encoding":
					w.Header().Set("Content-Encoding", "gzip")
					w.Write([]byte("ok"))
				}
			})
			if kind == "timeout" {
				s.client.Timeout = 5 * time.Millisecond
			}
			var err error
			if kind == "generation" || kind == "encoding" {
				_, err = s.Fetch(context.Background(), liveItem(100, []byte("ok")))
			} else {
				_, _, err = s.get(context.Background(), "/test", nil, 1024)
			}
			if kind == "server-recovery" {
				if err != nil || calls.Load() != 3 {
					t.Fatal(calls.Load(), err)
				}
			} else if err == nil {
				t.Fatal("failure became success")
			}
			if s.Requests > 3 {
				t.Fatal("unbounded retries")
			}
			if kind == "not-found" && calls.Load() != 1 {
				t.Fatal("retried permanent failure")
			}
		})
	}
}
func TestPartialDiscovery(t *testing.T) {
	for _, kind := range []string{"missing-page", "cycle", "scope", "malformed", "empty-unavailable", "duplicate", "checksum-metadata"} {
		t.Run(kind, func(t *testing.T) {
			raw := []byte(`<testsuite><testcase/></testsuite>`)
			s := serverSource(t, func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Query().Get("alt") == "media" {
					w.Write(raw)
					return
				}
				run := 100
				if strings.Contains(r.URL.Query().Get("prefix"), "200") {
					run = 200
				}
				item := liveItem(run, raw)
				if kind == "empty-unavailable" {
					w.WriteHeader(403)
					return
				}
				if r.URL.Query().Get("pageToken") == "next" {
					switch kind {
					case "missing-page":
						w.WriteHeader(404)
					case "cycle":
						json.NewEncoder(w).Encode(Object{"nextPageToken": "next"})
					case "scope":
						item["name"] = "logs/other/100/outside.xml"
						json.NewEncoder(w).Encode(Object{"items": []any{item}})
					case "malformed":
						w.Write([]byte("{bad"))
					case "duplicate":
						json.NewEncoder(w).Encode(Object{"items": []any{item}})
					case "checksum-metadata":
						item["md5Hash"] = "invalid"
						json.NewEncoder(w).Encode(Object{"items": []any{item}})
					}
					return
				}
				json.NewEncoder(w).Encode(Object{"items": []any{item}, "nextPageToken": "next"})
			})
			dir := filepath.Join(t.TempDir(), "capture")
			got, err := Capture(context.Background(), s, dir, urls)
			if err != nil {
				t.Fatal(err)
			}
			if got["comparisonComplete"] != false {
				t.Fatal("partial considered complete")
			}
			for _, run := range got["runs"].([]Object) {
				if run["artifactComplete"] != false || run["discoveryCoverage"].(Object)["complete"] != false {
					t.Fatal(run)
				}
				if kind != "empty-unavailable" && run["includedReports"] != 1 {
					t.Fatal("usable report lost", run)
				}
			}
			replay, e := Compare(dir, urls)
			if e != nil || !reflect.DeepEqual(got, replay) {
				t.Fatal("partial replay disagrees", e)
			}
		})
	}
}
func TestAcquisitionFailuresAndRecovery(t *testing.T) {
	for _, kind := range []string{"missing", "generation", "integrity", "oversize", "no-checksum", "crc-only", "crc-bad"} {
		t.Run(kind, func(t *testing.T) {
			raw := []byte(`<testsuite><testcase/></testsuite>`)
			recovered := false
			s := serverSource(t, func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Query().Get("alt") == "media" {
					if !recovered {
						switch kind {
						case "missing":
							w.WriteHeader(404)
							return
						case "generation":
							w.Header().Set("X-Goog-Generation", "13")
						case "integrity":
							w.Write([]byte("altered"))
							return
						}
					}
					w.Write(raw)
					return
				}
				run := 100
				if strings.Contains(r.URL.Query().Get("prefix"), "200") {
					run = 200
				}
				item := liveItem(run, raw)
				if !recovered {
					switch kind {
					case "oversize":
						item["size"] = "16777217"
					case "no-checksum":
						delete(item, "md5Hash")
						delete(item, "crc32c")
					case "crc-only":
						delete(item, "md5Hash")
					case "crc-bad":
						item["crc32c"] = "AAAAAA=="
					}
				}
				json.NewEncoder(w).Encode(Object{"items": []any{item}})
			})
			got, e := Capture(context.Background(), s, filepath.Join(t.TempDir(), "failed"), urls)
			if e != nil {
				t.Fatal(e)
			}
			if got["comparisonComplete"] != (kind == "crc-only") {
				t.Fatal("incorrect completeness", got)
			}
			recovered = true
			got, e = Capture(context.Background(), s, filepath.Join(t.TempDir(), "recovered"), urls)
			if e != nil || got["comparisonComplete"] != true {
				t.Fatal("recovery failed", e, got)
			}
		})
	}
}
func TestHTTPBudgetsAndCancellation(t *testing.T) {
	s := serverSource(t, func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("ok")) })
	s.Requests = liveRequests
	if _, _, e := s.get(context.Background(), "/", nil, 10); e == nil {
		t.Fatal("request cap")
	}
	s.Requests = 0
	s.Bytes = liveBytes
	if _, _, e := s.get(context.Background(), "/", nil, 10); e == nil {
		t.Fatal("byte cap")
	}
	s.Bytes = 0
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, _, e := s.get(ctx, "/", nil, 10); e == nil {
		t.Fatal("cancellation")
	}
}
func TestTLSFailure(t *testing.T) {
	server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("ok")) }))
	defer server.Close()
	source := newHTTPSource(server.URL, http.DefaultTransport.(*http.Transport).Clone())
	source.delay = 0
	if _, _, e := source.get(context.Background(), "/", nil, 10); e == nil {
		t.Fatal("untrusted TLS accepted")
	}
}
func TestAcquisitionCoverageCannotLie(t *testing.T) {
	root := copyCase(t)
	path := filepath.Join(root, "catalog.json")
	c := load(t, path)
	c["acquisition"] = Object{urls[0]: Object{"complete": true, "unresolved": []any{"lost_page"}}}
	save(t, path, c)
	if _, e := Compare(root, urls); e == nil {
		t.Fatal("contradictory coverage accepted")
	}
}
func TestChecksumVectors(t *testing.T) {
	raw := []byte("123456789")
	item := liveItem(100, raw)
	if e := verifyObject(raw, item); e != nil {
		t.Fatal(e)
	}
	if evidence.Digest(raw) == "" {
		t.Fatal("sha missing")
	}
}

type fakeSource struct {
	list func(context.Context, string, string) (Object, error)
}

func (s fakeSource) List(c context.Context, scope, token string) (Object, error) {
	return s.list(c, scope, token)
}
func (s fakeSource) Fetch(context.Context, Object) ([]byte, error) { panic("unexpected download") }
func TestLiveListingBudgets(t *testing.T) {
	for _, kind := range []string{"pages", "objects", "bytes"} {
		t.Run(kind, func(t *testing.T) {
			calls := 0
			source := fakeSource{list: func(ctx context.Context, scope, token string) (Object, error) {
				calls++
				switch kind {
				case "pages":
					return Object{"nextPageToken": strconv.Itoa(calls)}, nil
				case "objects":
					return Object{"items": make([]any, MaxObjects+1)}, nil
				default:
					return Object{"oversized": strings.Repeat("x", MaxJSON)}, nil
				}
			}}
			dir := filepath.Join(t.TempDir(), "capture")
			r, e := Capture(context.Background(), source, dir, urls)
			if e != nil {
				t.Fatal(e)
			}
			if r["comparisonComplete"] != false {
				t.Fatal("budget hidden")
			}
			if calls > 2*livePages {
				t.Fatal("unbounded pages")
			}
		})
	}
}
func TestObjectRedirectCannotEscape(t *testing.T) {
	escaped := false
	destination := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { escaped = true }))
	defer destination.Close()
	source := serverSource(t, func(w http.ResponseWriter, r *http.Request) { http.Redirect(w, r, destination.URL+"/object", 307) })
	if _, e := source.Fetch(context.Background(), liveItem(100, []byte("x"))); e == nil || escaped {
		t.Fatal("redirect followed", e)
	}
}

func TestPartialListingGolden(t *testing.T) {
	root := "../../testdata/live/partial-listing"
	got, e := Compare(root, urls)
	if e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(filepath.Join(root, "expected.json"))
	if e != nil {
		t.Fatal(e)
	}
	var expected, normalized any
	json.Unmarshal(raw, &expected)
	encoded, _ := json.Marshal(got)
	json.Unmarshal(encoded, &normalized)
	if !reflect.DeepEqual(expected, normalized) {
		t.Fatal("partial contract changed")
	}
	if got["runs"].([]Object)[0]["counts"].(Object)["attempts"] != 2 {
		t.Fatal("usable records lost")
	}
}

func TestCaptureRequestOrder(t *testing.T) {
	raw := []byte(`<testsuite><testcase/></testsuite>`)
	source := serverSource(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("alt") == "media" {
			w.Write(raw)
			return
		}
		run := 100
		if strings.Contains(r.URL.Query().Get("prefix"), "200") {
			run = 200
		}
		json.NewEncoder(w).Encode(Object{"items": []any{liveItem(run, raw)}})
	})
	for _, pair := range [][]string{{urls[1], urls[0]}, {urls[0], urls[0]}} {
		dir := filepath.Join(t.TempDir(), "capture")
		got, e := Capture(context.Background(), source, dir, pair)
		if e != nil {
			t.Fatal(e)
		}
		request := load(t, filepath.Join(dir, "request.json"))
		if request["urls"].([]any)[0] != pair[0] || got["runs"].([]Object)[0]["url"] != pair[0] {
			t.Fatal("request order changed")
		}
	}
}
