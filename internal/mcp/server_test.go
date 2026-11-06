package mcp

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"testreceipts/internal/provider"
	"time"
)

var pair = []string{"https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/100", "https://prow.k8s.io/view/gs/kubernetes-ci-logs/logs/test/200"}

type client struct {
	in      *io.PipeWriter
	decoder *json.Decoder
	out     *io.PipeReader
	done    chan error
	server  *Server
}

func start(t *testing.T, root string) *client {
	t.Helper()
	s, e := New(root, "test")
	if e != nil {
		t.Fatal(e)
	}
	r, w := io.Pipe()
	or, ow := io.Pipe()
	c := &client{w, json.NewDecoder(or), or, make(chan error, 1), s}
	go func() { e := s.Serve(context.Background(), r, ow); ow.Close(); c.done <- e }()
	t.Cleanup(func() {
		w.Close()
		or.Close()
		select {
		case <-c.done:
		case <-time.After(10 * time.Second):
			t.Error("server did not stop")
		}
	})
	return c
}
func (c *client) send(t *testing.T, v any) {
	t.Helper()
	raw, _ := json.Marshal(v)
	if _, e := c.in.Write(append(raw, '\n')); e != nil {
		t.Fatal(e)
	}
}
func (c *client) read(t *testing.T) object {
	t.Helper()
	ch := make(chan object, 1)
	go func() {
		var v object
		if e := c.decoder.Decode(&v); e != nil {
			ch <- object{"decodeError": e.Error()}
			return
		}
		ch <- v
	}()
	select {
	case v := <-ch:
		if v["decodeError"] != nil {
			t.Fatal(v)
		}
		return v
	case <-time.After(10 * time.Second):
		t.Fatal("response timeout")
		return nil
	}
}
func (c *client) init(t *testing.T) {
	c.send(t, object{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": object{"protocolVersion": Protocol, "clientInfo": object{"name": "test", "version": "1"}, "capabilities": object{}}})
	if c.read(t)["result"].(object)["protocolVersion"] != Protocol {
		t.Fatal("bad protocol")
	}
	c.send(t, object{"jsonrpc": "2.0", "method": "notifications/initialized"})
}
func TestRecordingParity(t *testing.T) {
	root, e := filepath.Abs("../..")
	if e != nil {
		t.Fatal(e)
	}
	c := start(t, root)
	c.init(t)
	c.send(t, object{"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
	tools := c.read(t)["result"].(object)["tools"].([]any)
	if len(tools) != 2 {
		t.Fatal(tools)
	}
	paths, _ := filepath.Glob("../../testdata/cases/*")
	paths = append(paths, "../../testdata/live/partial-listing")
	for i, p := range paths {
		abs, _ := filepath.Abs(p)
		rel, _ := filepath.Rel(root, abs)
		c.send(t, object{"jsonrpc": "2.0", "id": i + 3, "method": "tools/call", "params": object{"name": "compare_recording", "arguments": object{"recording": filepath.ToSlash(rel), "beforeUrl": pair[0], "afterUrl": pair[1]}}})
		result := c.read(t)["result"].(object)
		if result["isError"] != false {
			t.Fatal(result)
		}
		want, e := provider.Compare(abs, pair)
		if e != nil {
			t.Fatal(e)
		}
		encoded, _ := json.Marshal(want)
		var normalized any
		json.Unmarshal(encoded, &normalized)
		a, _ := json.Marshal(result["structuredContent"])
		b, _ := json.Marshal(normalized)
		if !bytes.Equal(a, b) {
			t.Fatal("facts differ", p)
		}
		text := result["content"].([]any)[0].(object)["text"].(string)
		var value any
		json.Unmarshal([]byte(text), &value)
		same, _ := json.Marshal(value)
		if !bytes.Equal(a, same) {
			t.Fatal("text differs")
		}
	}
}
func TestProtocolBoundaries(t *testing.T) {
	c := start(t, t.TempDir())
	c.send(t, object{"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
	if c.read(t)["error"] == nil {
		t.Fatal("missing initialize accepted")
	}
	c.init(t)
	for _, v := range []any{[]any{}, object{"jsonrpc": "2.0", "id": nil, "method": "ping"}, object{"jsonrpc": "2.0", "id": strings.Repeat("x", 129), "method": "ping"}, object{"jsonrpc": "2.0", "id": 2, "method": "missing"}, object{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": object{"name": "bad", "arguments": object{}}}} {
		c.send(t, v)
		if c.read(t)["error"] == nil {
			t.Fatal("invalid request accepted", v)
		}
	}
}
func TestPathBoundary(t *testing.T) {
	root := t.TempDir()
	os.Mkdir(filepath.Join(root, "existing"), 0755)
	s, _ := New(root, "test")
	for _, path := range []string{"../escape", "/absolute", `..\escape`, "C:/escape", "x/../escape", "./existing"} {
		if _, e := s.path(path, false); e == nil {
			t.Fatal("accepted", path)
		}
	}
	t.Run("symlink", func(t *testing.T) {
		if e := os.Symlink(t.TempDir(), filepath.Join(root, "escape")); e != nil {
			t.Skipf("symlink creation unavailable: %v", e)
		}
		if _, e := s.path("escape", false); e == nil {
			t.Fatal("symlink escape")
		}
	})
	for _, path := range []string{"existing", "nested/new"} {
		if _, e := s.path(path, true); e == nil {
			t.Fatal("invalid capture", path)
		}
	}
	if _, e := s.path("new", true); e != nil {
		t.Fatal(e)
	}
}
func TestInvalidNotificationsHaveNoSideEffects(t *testing.T) {
	root := t.TempDir()
	c := start(t, root)
	c.init(t)
	c.send(t, object{"jsonrpc": "2.0", "method": "tools/call", "params": object{"name": "compare_live", "arguments": object{"capture": "must-not-exist", "beforeUrl": pair[0], "afterUrl": pair[1]}}})
	c.send(t, object{"jsonrpc": "2.0", "id": 9, "method": "ping"})
	if c.read(t)["id"] != float64(9) {
		t.Fatal("notification produced response")
	}
	if _, e := os.Stat(filepath.Join(root, "must-not-exist")); !os.IsNotExist(e) {
		t.Fatal("notification executed tool")
	}
}
func TestToolValidationAndBudgets(t *testing.T) {
	c := start(t, t.TempDir())
	c.init(t)
	for i, args := range []object{{"recording": "missing", "beforeUrl": pair[0], "afterUrl": pair[1]}, {"capture": "new", "beforeUrl": "https://evil.test/", "afterUrl": pair[1]}, {"recording": "missing", "beforeUrl": pair[0], "afterUrl": pair[1], "extra": true}} {
		name := "compare_recording"
		if args["capture"] != nil {
			name = "compare_live"
		}
		c.send(t, object{"jsonrpc": "2.0", "id": i + 2, "method": "tools/call", "params": object{"name": name, "arguments": args}})
		if c.read(t)["result"].(object)["isError"] != true {
			t.Fatal("validation ignored")
		}
	}
}
func TestOutputAndFrameBounds(t *testing.T) {
	s, _ := New(t.TempDir(), "test")
	var out bytes.Buffer
	s.out = &out
	s.result(1, object{"content": strings.Repeat("x", MaxOutput+1)})
	if out.Len() > MaxOutput {
		t.Fatal("unbounded wire")
	}
	var result object
	json.Unmarshal(out.Bytes(), &result)
	if result["result"].(object)["isError"] != true {
		t.Fatal("truncated silently")
	}
	s, _ = New(t.TempDir(), "test")
	if e := s.Serve(context.Background(), strings.NewReader(strings.Repeat("x", MaxInput+1)), io.Discard); e == nil {
		t.Fatal("input budget ignored")
	}
}
func TestCancellation(t *testing.T) {
	s, _ := New(t.TempDir(), "test")
	ctx, cancel := context.WithCancel(context.Background())
	s.active = `"active"`
	s.cancel = cancel
	var out bytes.Buffer
	s.out = &out
	s.handle(context.Background(), []byte(`{"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":"active"}}`))
	if ctx.Err() == nil || out.Len() != 0 {
		t.Fatal("cancel not delivered")
	}
}

func TestSessionToolBudgets(t *testing.T) {
	root := t.TempDir()
	os.Mkdir(filepath.Join(root, "recording"), 0755)
	s, _ := New(root, "test")
	var out bytes.Buffer
	s.out = &out
	args := object{"name": "compare_recording", "arguments": object{"recording": "recording", "beforeUrl": pair[0], "afterUrl": pair[1]}}
	s.calls = MaxCalls
	s.call(context.Background(), 1, args)
	if !strings.Contains(out.String(), "session_tool_budget") {
		t.Fatal("call cap ignored")
	}
	out.Reset()
	s.calls = 0
	s.lives = MaxLiveCalls
	s.call(context.Background(), 2, object{"name": "compare_live", "arguments": object{"capture": "new", "beforeUrl": pair[0], "afterUrl": pair[1]}})
	if !strings.Contains(out.String(), "session_tool_budget") {
		t.Fatal("live cap ignored")
	}
	if _, e := os.Stat(filepath.Join(root, "new")); !os.IsNotExist(e) {
		t.Fatal("budgeted live call wrote files")
	}
	out.Reset()
	s.cancel = func() {}
	s.call(context.Background(), 3, args)
	if !strings.Contains(out.String(), "server_busy") {
		t.Fatal("parallel work accepted")
	}
}
func TestContextStopsReader(t *testing.T) {
	s, _ := New(t.TempDir(), "test")
	r, w := io.Pipe()
	defer w.Close()
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- s.Serve(ctx, r, io.Discard) }()
	cancel()
	select {
	case e := <-done:
		if e != nil {
			t.Fatal(e)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("cancel did not stop reader")
	}
}

func TestExplicitRoot(t *testing.T) {
	if _, e := New("", "test"); e == nil {
		t.Fatal("implicit root accepted")
	}
	p := filepath.Join(t.TempDir(), "file")
	os.WriteFile(p, []byte("x"), 0644)
	if _, e := New(p, "test"); e == nil {
		t.Fatal("file root accepted")
	}
}
