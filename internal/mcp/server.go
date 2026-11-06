// Package mcp exposes the existing comparison core over a scoped stdio boundary.
// It implements the explicitly pinned legacy MCP 2025-11-25 profile.
package mcp

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testreceipts/internal/evidence"
	"testreceipts/internal/provider"
	"time"
)

const Protocol = "2025-11-25"
const MaxInput = 1024 * 1024
const MaxOutput = 2 * 1024 * 1024
const MaxCalls = 64
const MaxLiveCalls = 4

type object = map[string]any

// Server is a single-client stdio server, scoped to an explicitly selected root.
type Server struct {
	Root, Version      string
	out                io.Writer
	writeMu            sync.Mutex
	writeErr           error
	mu                 sync.Mutex
	active             string
	cancel             context.CancelFunc
	calls, lives       int
	wg                 sync.WaitGroup
	initialized, ready bool
}

func New(root, version string) (*Server, error) {
	if root == "" {
		return nil, errors.New("explicit_root_required")
	}
	root, e := filepath.Abs(root)
	if e != nil {
		return nil, errors.New("invalid_root")
	}
	root, e = filepath.EvalSymlinks(root)
	if e != nil {
		return nil, errors.New("root_unavailable")
	}
	st, e := os.Stat(root)
	if e != nil || !st.IsDir() {
		return nil, errors.New("root_not_directory")
	}
	return &Server{Root: root, Version: version}, nil
}
func (s *Server) send(message object) {
	s.writeMu.Lock()
	defer s.writeMu.Unlock()
	if s.writeErr != nil {
		return
	}
	raw, e := json.Marshal(message)
	if e != nil {
		s.writeErr = e
		return
	}
	if len(raw) > MaxOutput {
		message = object{"jsonrpc": "2.0", "id": message["id"], "result": toolError("output_budget_exceeded; use the CLI and original recording for full output")}
		raw, _ = json.Marshal(message)
	}
	_, s.writeErr = s.out.Write(append(raw, '\n'))
}
func (s *Server) rpcError(id any, code int, message string) {
	s.send(object{"jsonrpc": "2.0", "id": id, "error": object{"code": code, "message": message}})
}
func (s *Server) result(id any, result any) {
	s.send(object{"jsonrpc": "2.0", "id": id, "result": result})
}
func toolError(message string) object {
	return object{"isError": true, "content": []any{object{"type": "text", "text": message}}}
}

// Serve keeps stdout exclusively JSON-RPC. EOF cancels active acquisition.
func (s *Server) Serve(ctx context.Context, in io.Reader, out io.Writer) error {
	s.out = out
	finished := make(chan struct{})
	defer close(finished)
	if closer, ok := in.(io.Closer); ok {
		go func() {
			select {
			case <-ctx.Done():
				closer.Close()
			case <-finished:
			}
		}()
	}
	scanner := bufio.NewScanner(in)
	scanner.Buffer(make([]byte, 64*1024), MaxInput)
	count := 0
	for scanner.Scan() {
		count++
		if count > 1024 {
			s.rpcError(nil, -32000, "session_message_budget")
			break
		}
		s.handle(ctx, scanner.Bytes())
	}
	s.mu.Lock()
	if s.cancel != nil {
		s.cancel()
	}
	s.mu.Unlock()
	s.wg.Wait()
	if e := scanner.Err(); e != nil && ctx.Err() == nil {
		return errors.New("input_frame_budget_or_read_error")
	}
	s.writeMu.Lock()
	defer s.writeMu.Unlock()
	return s.writeErr
}
func (s *Server) handle(ctx context.Context, raw []byte) {
	v, e := evidence.DecodeJSON(raw)
	if e != nil {
		code := -32600
		if !json.Valid(raw) {
			code = -32700
		}
		s.rpcError(nil, code, "invalid_request_json")
		return
	}
	request, ok := v.(object)
	if !ok {
		s.rpcError(nil, -32600, "request_must_be_object")
		return
	}
	id, hasID := request["id"]
	if hasID {
		switch id.(type) {
		case string:
			if len(id.(string)) > 128 {
				s.rpcError(nil, -32600, "request_id_budget")
				return
			}
		case json.Number:
			if len(id.(json.Number)) > 32 {
				s.rpcError(nil, -32600, "request_id_budget")
				return
			}
		default:
			s.rpcError(nil, -32600, "invalid_request_id")
			return
		}
	}
	method, ok := request["method"].(string)
	if !ok || request["jsonrpc"] != "2.0" {
		s.rpcError(nil, -32600, "invalid_request")
		return
	}
	params := object{}
	if v, exists := request["params"]; exists {
		var valid bool
		params, valid = v.(object)
		if !valid {
			if hasID {
				s.rpcError(id, -32602, "params_must_be_object")
			}
			return
		}
	}
	if !hasID {
		switch method {
		case "notifications/initialized":
			if s.initialized {
				s.ready = true
			}
		case "notifications/cancelled":
			key := string(evidence.Canonical(params["requestId"]))
			s.mu.Lock()
			if key == s.active && s.cancel != nil {
				s.cancel()
			}
			s.mu.Unlock()
		}
		return
	}
	if method == "ping" {
		s.result(id, object{})
		return
	}
	if method == "server/discover" {
		s.rpcError(id, -32601, "method_not_found; legacy MCP 2025-11-25 only")
		return
	}
	if method == "initialize" {
		if s.initialized {
			s.rpcError(id, -32600, "already_initialized")
			return
		}
		version, ok := params["protocolVersion"].(string)
		_, caps := params["capabilities"].(object)
		info, okInfo := params["clientInfo"].(object)
		name, n := info["name"].(string)
		clientVersion, cv := info["version"].(string)
		if !ok || version == "" || !caps || !okInfo || !n || name == "" || !cv || clientVersion == "" {
			s.rpcError(id, -32602, "invalid_initialize_params")
			return
		}
		s.initialized = true
		s.result(id, object{"protocolVersion": Protocol, "capabilities": object{"tools": object{"listChanged": false}}, "serverInfo": object{"name": "testreceipts", "version": s.Version}, "instructions": "Compare facts retain incomplete evidence. Only paths within the configured root are accepted. No model calls are made."})
		return
	}
	if !s.ready {
		s.rpcError(id, -32002, "initialize_and_notify_first")
		return
	}
	switch method {
	case "tools/list":
		if cursor, ok := params["cursor"]; ok && cursor != "" {
			s.rpcError(id, -32602, "invalid_cursor")
			return
		}
		s.result(id, object{"tools": tools()})
	case "tools/call":
		s.call(ctx, id, params)
	default:
		s.rpcError(id, -32601, "method_not_found")
	}
}
func tools() []any {
	out := []any{}
	for _, name := range []string{"compare_recording", "compare_live"} {
		pathKey := "recording"
		description := "Compare two recorded public Prow runs offline; preserves exact diagnostics and coverage."
		readonly := true
		if name == "compare_live" {
			pathKey = "capture"
			description = "Capture two supported public Prow/GCS runs into a NEW direct child directory, then compare. Bounded HTTPS; partial evidence stays explicit."
			readonly = false
		}
		out = append(out, object{"name": name, "description": description, "inputSchema": object{"type": "object", "properties": object{pathKey: object{"type": "string"}, "beforeUrl": object{"type": "string"}, "afterUrl": object{"type": "string"}}, "required": []string{pathKey, "beforeUrl", "afterUrl"}, "additionalProperties": false}, "annotations": object{"readOnlyHint": readonly, "destructiveHint": false, "idempotentHint": readonly, "openWorldHint": !readonly}})
	}
	return out
}
func (s *Server) path(value string, live bool) (string, error) {
	if value == "" || len(value) > 4096 || filepath.IsAbs(value) || strings.ContainsAny(value, "\\:") {
		return "", errors.New("invalid_scoped_path")
	}
	for _, part := range strings.Split(value, "/") {
		if part == ".." || part == "." || part == "" {
			return "", errors.New("invalid_scoped_path")
		}
	}
	if live && strings.Contains(value, "/") {
		return "", errors.New("capture_must_be_direct_child")
	}
	p := filepath.Join(s.Root, filepath.FromSlash(value))
	if live {
		if _, e := os.Lstat(p); !os.IsNotExist(e) {
			return "", errors.New("capture_must_be_new")
		}
		return p, nil
	}
	p, e := filepath.EvalSymlinks(p)
	if e != nil {
		return "", errors.New("recording_unavailable")
	}
	relative, e := filepath.Rel(s.Root, p)
	if e != nil || relative == ".." || strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		return "", errors.New("path_out_of_scope")
	}
	return p, nil
}
func (s *Server) call(ctx context.Context, id any, params object) {
	name, ok := params["name"].(string)
	if !ok || (name != "compare_recording" && name != "compare_live") {
		s.rpcError(id, -32602, "unknown_tool")
		return
	}
	args, ok := params["arguments"].(object)
	if !ok {
		s.rpcError(id, -32602, "arguments_must_be_object")
		return
	}
	live := name == "compare_live"
	key := "recording"
	if live {
		key = "capture"
	}
	if len(args) != 3 {
		s.result(id, toolError("expected exactly path, beforeUrl and afterUrl arguments"))
		return
	}
	values := map[string]string{}
	for _, k := range []string{key, "beforeUrl", "afterUrl"} {
		v, ok := args[k].(string)
		if !ok || v == "" || len(v) > 4096 {
			s.result(id, toolError("invalid argument: "+k))
			return
		}
		values[k] = v
	}
	path, e := s.path(values[key], live)
	if e != nil {
		s.result(id, toolError(e.Error()))
		return
	}
	urls := []string{values["beforeUrl"], values["afterUrl"]}
	for _, u := range urls {
		if _, e := provider.RunScope(u); e != nil {
			s.result(id, toolError(e.Error()))
			return
		}
	}
	s.mu.Lock()
	if s.cancel != nil {
		s.mu.Unlock()
		s.result(id, toolError("server_busy; wait for the active call"))
		return
	}
	if s.calls >= MaxCalls || (live && s.lives >= MaxLiveCalls) {
		s.mu.Unlock()
		s.result(id, toolError("session_tool_budget"))
		return
	}
	s.calls++
	if live {
		s.lives++
	}
	callCtx, cancel := context.WithTimeout(ctx, 5*time.Minute)
	s.active = string(evidence.Canonical(id))
	s.cancel = cancel
	s.wg.Add(1)
	s.mu.Unlock()
	go func() {
		defer s.wg.Done()
		defer cancel()
		var result provider.Object
		var err error
		if live {
			result, err = provider.Capture(callCtx, provider.NewHTTPSource(), path, urls)
		} else {
			result, err = provider.Compare(path, urls)
		}
		response := object{}
		switch {
		case callCtx.Err() != nil:
			response = toolError("request_cancelled_or_timed_out; retained captures may contain partial evidence")
		case err != nil:
			response = toolError(err.Error())
		default:
			raw, _ := json.Marshal(result)
			if len(raw) > MaxOutput/4 {
				s.mu.Lock()
				s.active = ""
				s.cancel = nil
				s.mu.Unlock()
				s.result(id, toolError("output_budget_exceeded; use CLI and retained original recording"))
				return
			}
			source := filepath.ToSlash(filepath.Join(path, "catalog.json"))
			if !strings.HasPrefix(source, "/") {
				source = "/" + source
			}
			response = object{"isError": false, "structuredContent": result, "content": []any{object{"type": "text", "text": string(raw)}, object{"type": "resource_link", "uri": (&url.URL{Scheme: "file", Path: source}).String(), "name": "catalog.json", "mimeType": "application/json"}}}
		}
		s.mu.Lock()
		s.active = ""
		s.cancel = nil
		s.mu.Unlock()
		s.result(id, response)
	}()
}
