package provider

import (
	"context"
	"crypto/md5"
	"crypto/tls"
	"encoding/base64"
	"encoding/binary"
	"errors"
	"fmt"
	"hash/crc32"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"testreceipts/internal/evidence"
	"testreceipts/internal/junit"
	"time"
)

const livePages = 64
const liveRequests = 512
const liveBytes = 96 * 1024 * 1024

var redirectRejected = errors.New("redirect_rejected")
var generationPattern = regexp.MustCompile(`^[0-9]+$`)
var runPath = regexp.MustCompile(`^/view/gs/kubernetes-ci-logs/(logs/[A-Za-z0-9_.-]+/[0-9]+|pr-logs/pull/[A-Za-z0-9_.-]+/[0-9]+/[A-Za-z0-9_.-]+/[0-9]+)/?$`)

func RunScope(s string) (string, error) {
	u, e := url.Parse(s)
	if e != nil || u.Scheme != "https" || u.Host != "prow.k8s.io" || u.User != nil || u.RawQuery != "" || u.ForceQuery || u.Fragment != "" || u.RawPath != "" || !runPath.MatchString(u.Path) {
		return "", errors.New("unsupported_prow_url")
	}
	scope := strings.TrimSuffix(strings.TrimPrefix(u.Path, "/view/gs/kubernetes-ci-logs/"), "/") + "/"
	for _, p := range strings.Split(scope, "/") {
		if p == "." || p == ".." {
			return "", errors.New("invalid_run_scope")
		}
	}
	return scope, nil
}

// Source separates acquisition from bounded recording and the shared parser.
type Source interface {
	List(context.Context, string, string) (Object, error)
	Fetch(context.Context, Object) ([]byte, error)
}
type HTTPSource struct {
	client      *http.Client
	base        string
	Requests    int
	Bytes       int
	Events      []Object
	delay       time.Duration
	captureDir  string
	requestTime time.Duration
}

func NewHTTPSource() *HTTPSource {
	return newHTTPSource("https://storage.googleapis.com", &http.Transport{Proxy: http.ProxyFromEnvironment, DialContext: (&net.Dialer{Timeout: 10 * time.Second, KeepAlive: 30 * time.Second}).DialContext, TLSHandshakeTimeout: 10 * time.Second, ResponseHeaderTimeout: 15 * time.Second, IdleConnTimeout: 30 * time.Second, MaxIdleConns: 4, MaxIdleConnsPerHost: 2, DisableCompression: true})
}
func newHTTPSource(base string, transport http.RoundTripper) *HTTPSource {
	return &HTTPSource{base: base, delay: 200 * time.Millisecond, client: &http.Client{Transport: transport, Timeout: 20 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return redirectRejected }}}
}
func (s *HTTPSource) get(ctx context.Context, path string, query url.Values, limit int) ([]byte, http.Header, error) {
	target := s.base + path + "?" + query.Encode()
	for attempt := 0; attempt < 3; attempt++ {
		if s.Requests >= liveRequests || s.Bytes >= liveBytes {
			return nil, nil, errors.New("network_budget_exceeded")
		}
		req, err := http.NewRequestWithContext(ctx, "GET", target, nil)
		if err != nil {
			return nil, nil, errors.New("invalid_request")
		}
		req.Header.Set("Accept-Encoding", "identity")
		req.Header.Set("User-Agent", "TestReceipts/1 public-recording-capture")
		start := time.Now()
		s.Requests++
		resp, err := s.client.Do(req)
		event := Object{"url": target, "attempt": attempt + 1, "seconds": 0, "bytes": 0}
		var raw []byte
		var header http.Header
		status := 0
		reason := ""
		retry := false
		if err != nil {
			reason = "network_error"
			retry = true
			if resp != nil {
				status = resp.StatusCode
			}
			var certError *tls.CertificateVerificationError
			var netError net.Error
			switch {
			case ctx.Err() != nil:
				reason = "operation_cancelled"
				retry = false
			case errors.Is(err, redirectRejected):
				reason = "redirect_rejected"
				retry = false
			case errors.As(err, &certError):
				reason = "tls_verification_failed"
				retry = false
			case errors.As(err, &netError) && netError.Timeout():
				reason = "request_timeout"
			}
		} else {
			header = resp.Header
			status = resp.StatusCode
			remaining := liveBytes - s.Bytes
			cap := min(limit, remaining)
			if status != 200 {
				cap = min(cap, 64*1024)
			}
			raw, err = io.ReadAll(io.LimitReader(resp.Body, int64(cap)+1))
			resp.Body.Close()
			s.Bytes += len(raw)
			event["bytes"] = len(raw)
			switch {
			case err != nil:
				reason = "body_read_error"
				retry = true
			case len(raw) > cap:
				reason = "response_budget_exceeded"
			case status == 429 || status >= 500:
				reason = fmt.Sprintf("http_%d", status)
				retry = true
			case status != 200:
				reason = fmt.Sprintf("http_%d", status)
			default:
			}
		}
		elapsed := time.Since(start)
		s.requestTime += elapsed
		if s.captureDir != "" && raw != nil {
			name := fmt.Sprintf("responses/%03d.body", s.Requests)
			if e := os.WriteFile(filepath.Join(s.captureDir, name), raw, 0644); e != nil {
				return nil, nil, errors.New("capture_write_error")
			}
			event["responseFile"] = name
			event["responseSha256"] = evidence.Digest(raw)
		}
		event["status"] = status
		event["seconds"] = strconv.FormatFloat(elapsed.Seconds(), 'f', 6, 64)
		if reason != "" {
			event["error"] = reason
		}
		s.Events = append(s.Events, event)
		if reason == "" {
			return raw, header, nil
		}
		if !retry || attempt == 2 {
			return nil, nil, errors.New(reason)
		}
		delay := s.delay * time.Duration(1<<attempt)
		if header != nil {
			if n, e := strconv.Atoi(header.Get("Retry-After")); e == nil && n >= 0 {
				delay = time.Duration(min(n, 2)) * time.Second
			}
		}
		timer := time.NewTimer(delay)
		select {
		case <-ctx.Done():
			timer.Stop()
			return nil, nil, errors.New("operation_cancelled")
		case <-timer.C:
		}
	}
	return nil, nil, errors.New("request_failed")
}
func (s *HTTPSource) List(ctx context.Context, scope, token string) (Object, error) {
	q := url.Values{"prefix": {scope}, "maxResults": {"1000"}, "fields": {"items(name,generation,size,md5Hash,crc32c,contentEncoding),nextPageToken"}}
	if token != "" {
		q.Set("pageToken", token)
	}
	raw, _, e := s.get(ctx, "/storage/v1/b/kubernetes-ci-logs/o", q, MaxJSON)
	if e != nil {
		return nil, e
	}
	v, e := strictJSON(raw)
	if e != nil {
		return nil, e
	}
	return obj(v)
}
func (s *HTTPSource) Fetch(ctx context.Context, item Object) ([]byte, error) {
	name, e := str(item, "name")
	if e != nil {
		return nil, e
	}
	generation, e := str(item, "generation")
	if e != nil {
		return nil, e
	}
	raw, h, e := s.get(ctx, "/storage/v1/b/kubernetes-ci-logs/o/"+url.PathEscape(name), url.Values{"alt": {"media"}, "generation": {generation}}, junit.MaxXML)
	if e != nil {
		return nil, e
	}
	if g := h.Get("X-Goog-Generation"); g != "" && g != generation {
		return nil, errors.New("generation_mismatch")
	}
	if h.Get("Content-Encoding") != "" && h.Get("Content-Encoding") != "identity" {
		return nil, errors.New("unsupported_content_encoding")
	}
	return raw, nil
}
func verifyObject(raw []byte, item Object) error {
	size, e := str(item, "size")
	if e != nil {
		return e
	}
	n, e := strconv.ParseInt(size, 10, 64)
	if e != nil || n < 0 || n != int64(len(raw)) {
		return errors.New("provider_size_mismatch")
	}
	verified := false
	if value, ok := item["md5Hash"]; ok {
		s, ok := value.(string)
		b, e := base64.StdEncoding.DecodeString(s)
		if !ok || e != nil || len(b) != 16 {
			return errors.New("invalid_object_md5")
		}
		hash := md5.Sum(raw)
		if base64.StdEncoding.EncodeToString(hash[:]) != s {
			return errors.New("provider_md5_mismatch")
		}
		verified = true
	}
	if value, ok := item["crc32c"]; ok {
		s, ok := value.(string)
		b, e := base64.StdEncoding.DecodeString(s)
		if !ok || e != nil || len(b) != 4 {
			return errors.New("invalid_object_crc32c")
		}
		if crc32.Checksum(raw, crc32.MakeTable(crc32.Castagnoli)) != binary.BigEndian.Uint32(b) {
			return errors.New("provider_crc32c_mismatch")
		}
		verified = true
	}
	if !verified {
		return errors.New("checksum_unavailable")
	}
	return nil
}

// Capture writes an immutable new recording, then compares through the replay core.
// Unavailable pages are acquisition coverage, never an invented empty full listing.
func Capture(ctx context.Context, source Source, dir string, urls []string) (Object, error) {
	if len(urls) != 2 {
		return nil, errors.New("two_run_urls_required")
	}
	scopes := []string{}
	for _, u := range urls {
		scope, e := RunScope(u)
		if e != nil {
			return nil, e
		}
		scopes = append(scopes, scope)
	}
	if e := os.MkdirAll(filepath.Dir(dir), 0755); e != nil {
		return nil, errors.New("capture_parent_unavailable")
	}
	if e := os.Mkdir(dir, 0755); e != nil {
		return nil, errors.New("capture_directory_must_be_new")
	}
	if e := os.Mkdir(filepath.Join(dir, "objects"), 0755); e != nil {
		return nil, e
	}
	if s, ok := source.(*HTTPSource); ok {
		s.captureDir = dir
		s.Requests = 0
		s.Bytes = 0
		s.Events = nil
		s.requestTime = 0
		if e := os.Mkdir(filepath.Join(dir, "responses"), 0755); e != nil {
			return nil, e
		}
	}
	catalog := Object{"runs": Object{}, "objects": Object{}, "acquisition": Object{}}
	start := time.Now()
	write := func(name string, v any) error {
		return os.WriteFile(filepath.Join(dir, name), append(evidence.Canonical(v), '\n'), 0644)
	}
	if e := write("request.json", Object{"urls": urls, "mode": "public_prow_gcs_live"}); e != nil {
		return nil, e
	}
	for index, u := range urls {
		if _, exists := catalog["runs"].(Object)[u]; exists {
			continue
		}
		pages := []any{}
		items := map[string]Object{}
		seenTokens := map[string]bool{}
		token := ""
		issues := []string{}
		listed := 0
		for pageNumber := 0; ; pageNumber++ {
			if pageNumber >= livePages {
				issues = append(issues, "listing_page_budget")
				break
			}
			page, e := source.List(ctx, scopes[index], token)
			if e != nil {
				issues = append(issues, "listing_unavailable:"+e.Error())
				break
			}
			// Validate a page completely before accepting any of its objects.
			if _, ok := page["error"]; ok {
				issues = append(issues, "provider_error_document")
				break
			}
			pageItems := []any{}
			if v, ok := page["items"]; ok {
				var valid bool
				pageItems, valid = v.([]any)
				if !valid {
					issues = append(issues, "invalid_listing_items")
					break
				}
			}
			next := ""
			if v, ok := page["nextPageToken"]; ok {
				var valid bool
				next, valid = v.(string)
				if !valid || len(next) > 8192 {
					issues = append(issues, "invalid_page_token")
					break
				}
			}
			if listed+len(pageItems) > MaxObjects {
				issues = append(issues, "listing_object_budget")
				break
			}
			pending := map[string]Object{}
			bad := ""
			for _, v := range pageItems {
				item, e := obj(v)
				if e != nil {
					bad = "invalid_listing_object"
					break
				}
				name, e := str(item, "name")
				if e != nil || !strings.HasPrefix(name, scopes[index]) {
					bad = "out_of_scope_object"
					break
				}
				for _, p := range strings.Split(name, "/") {
					if p == ".." || p == "." || strings.Contains(p, "\\") {
						bad = "out_of_scope_object"
					}
				}
				if bad != "" {
					break
				}
				if _, ok := items[name]; ok {
					bad = "duplicate_listing_object"
					break
				}
				if _, ok := pending[name]; ok {
					bad = "duplicate_listing_object"
					break
				}
				if strings.HasSuffix(strings.ToLower(name), ".xml") {
					gen, e := str(item, "generation")
					if e != nil || !generationPattern.MatchString(gen) {
						bad = "invalid_generation"
						break
					}
					size, e := str(item, "size")
					n, err := strconv.ParseInt(size, 10, 64)
					if e != nil || err != nil || n < 0 {
						bad = "invalid_object_size"
						break
					}
					for key, want := range map[string]int{"md5Hash": 16, "crc32c": 4} {
						if value, ok := item[key]; ok {
							text, valid := value.(string)
							decoded, e := base64.StdEncoding.DecodeString(text)
							if !valid || e != nil || len(decoded) != want {
								bad = "invalid_checksum_metadata"
							}
						}
					}
					if bad != "" {
						break
					}
				}
				pending[name] = item
			}
			if bad != "" {
				issues = append(issues, bad)
				break
			}
			if len(evidence.Canonical(append(pages, page))) > MaxJSON {
				issues = append(issues, "listing_byte_budget")
				break
			}
			pages = append(pages, page)
			listed += len(pageItems)
			for n, item := range pending {
				items[n] = item
			}
			if next == "" {
				break
			}
			if seenTokens[next] {
				issues = append(issues, "pagination_cycle")
				break
			}
			seenTokens[next] = true
			token = next
		}
		synthetic := len(pages) == 0
		if synthetic {
			pages = append(pages, Object{"items": []any{}})
		}
		names := []string{}
		for name := range items {
			if strings.HasSuffix(strings.ToLower(name), ".xml") {
				names = append(names, name)
			}
		}
		sort.Strings(names)
		captured, fetched := 0, 0
		objectErrors := []Object{}
		for _, name := range names {
			item := items[name]
			generation := item["generation"].(string)
			key := evidence.Hash([]string{name, generation})
			size, _ := strconv.ParseInt(item["size"].(string), 10, 64)
			entry := Object{}
			reason := ""
			switch {
			case size > junit.MaxXML:
				reason = "xml_budget_exceeded"
			case int64(captured)+size > MaxCapture:
				reason = "xml_collection_budget_exceeded"
			case fetched >= 2048:
				reason = "report_fetch_budget"
			case item["contentEncoding"] != nil && item["contentEncoding"] != "":
				reason = "unsupported_content_encoding"
			default:
				fetched++
				raw, e := source.Fetch(ctx, item)
				if e != nil {
					reason = e.Error()
				} else if e = verifyObject(raw, item); e != nil {
					reason = e.Error()
				} else {
					captured += len(raw)
					path := "objects/" + key + ".xml"
					if e = os.WriteFile(filepath.Join(dir, path), raw, 0644); e != nil {
						return nil, e
					}
					entry["path"] = path
					entry["sha256"] = evidence.Digest(raw)
				}
			}
			if reason != "" {
				entry["error"] = reason
				objectErrors = append(objectErrors, Object{"name": name, "reason": reason})
			}
			catalog["objects"].(Object)[key] = entry
		}
		path := fmt.Sprintf("pages-%d.json", index)
		if e := write(path, pages); e != nil {
			return nil, e
		}
		catalog["runs"].(Object)[u] = path
		catalog["acquisition"].(Object)[u] = Object{"complete": len(issues) == 0, "unresolved": issues, "noSuccessfulListingPages": synthetic, "objectErrors": objectErrors}
	}
	if e := write("catalog.json", catalog); e != nil {
		return nil, e
	}
	metrics := Object{"acquisitionSeconds": strconv.FormatFloat(time.Since(start).Seconds(), 'f', 6, 64), "scope": "public Prow/GCS; no authentication; generation-pinned objects"}
	if s, ok := source.(*HTTPSource); ok {
		metrics["requestSeconds"] = strconv.FormatFloat(s.requestTime.Seconds(), 'f', 6, 64)
		metrics["requests"] = s.Requests
		metrics["responseBytes"] = s.Bytes
		metrics["events"] = s.Events
	}
	if e := write("network.json", metrics); e != nil {
		return nil, e
	}
	result, e := Compare(dir, urls)
	if e != nil {
		return nil, e
	}
	if e = write("comparison.json", result); e != nil {
		return nil, e
	}
	return result, nil
}
