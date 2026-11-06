// Package junit classifies XML and counts observed records without inferring executions.
package junit

import (
	"bytes"
	"encoding/xml"
	"io"
	"math/big"
	"strings"
	"testreceipts/internal/evidence"
	"unicode"
	"unicode/utf8"
)

type Node struct {
	Name     xml.Name
	Attr     map[string]string
	Text     strings.Builder
	Children []*Node
}
type Report struct {
	Disposition, Reason  string
	Counts               evidence.Object
	Groups               map[string]evidence.Object
	Unknown, Limitations map[string]bool
}

const MaxXML = 16 * 1024 * 1024

// Bound tree growth independently of the byte budget and reject excessive nesting.
const MaxNodes = 250000
const MaxDepth = 256

func Parse(raw []byte) Report {
	r := Report{Disposition: "blocked", Counts: evidence.Object{"attempts": 0, "passed": 0, "failure": 0, "error": 0, "skipped": 0}, Groups: map[string]evidence.Object{}, Unknown: map[string]bool{}, Limitations: map[string]bool{}}
	if len(raw) > MaxXML {
		r.Reason = "xml_budget_exceeded"
		return r
	}
	if !utf8.Valid(raw) {
		r.Reason = "unsupported_encoding"
		return r
	}
	upper := bytes.ToUpper(raw)
	if bytes.Contains(upper, []byte("<!DOCTYPE")) || bytes.Contains(upper, []byte("<!ENTITY")) {
		r.Reason = "entity_declaration"
		return r
	}
	normalized := normalizeAttributes(bytes.TrimPrefix(raw, []byte{0xef, 0xbb, 0xbf}))
	if reason := namespaceCheck(normalized); reason != "" {
		r.Reason = reason
		return r
	}
	dec := xml.NewDecoder(bytes.NewReader(normalized))
	var root *Node
	stack := []*Node{}
	nodes := 0
	namespaced, like := false, false
	for {
		t, err := dec.Token()
		if err == io.EOF {
			break
		}
		if err != nil {
			r.Reason = "malformed_xml"
			return r
		}
		switch t := t.(type) {
		case xml.StartElement:
			nodes++
			if nodes > MaxNodes || len(stack) >= MaxDepth {
				r.Reason = "xml_structure_budget_exceeded"
				return r
			}
			n := &Node{Name: t.Name, Attr: map[string]string{}}
			seenAttributes := map[xml.Name]bool{}
			for _, a := range t.Attr {
				if seenAttributes[a.Name] {
					r.Reason = "malformed_xml"
					return r
				}
				seenAttributes[a.Name] = true
				if a.Name.Space == "" {
					n.Attr[a.Name.Local] = a.Value
				}
			}
			if t.Name.Space != "" {
				namespaced = true
			}
			if t.Name.Local == "testsuite" || t.Name.Local == "testsuites" || t.Name.Local == "testcase" {
				like = true
			}
			if len(stack) == 0 {
				if root != nil {
					r.Reason = "malformed_xml"
					return r
				}
				root = n
			} else {
				p := stack[len(stack)-1]
				p.Children = append(p.Children, n)
			}
			stack = append(stack, n)
		case xml.Directive:
			r.Reason = "malformed_xml"
			return r
		case xml.EndElement:
			if len(stack) == 0 {
				r.Reason = "malformed_xml"
				return r
			}
			stack = stack[:len(stack)-1]
		case xml.CharData:
			if len(stack) > 0 {
				n := stack[len(stack)-1]
				if len(n.Children) == 0 {
					n.Text.Write(t)
				}
			} else if strings.TrimSpace(string(t)) != "" {
				r.Reason = "malformed_xml"
				return r
			}
		}
	}
	if root == nil || len(stack) != 0 {
		r.Reason = "malformed_xml"
		return r
	}
	if root.Name.Space != "" || (root.Name.Local != "testsuite" && root.Name.Local != "testsuites") {
		if like {
			r.Reason = "unsupported_junit_like_root"
		} else {
			r.Disposition = "non-junit"
			r.Reason = "non_junit_xml_root"
		}
		return r
	}
	if namespaced {
		r.Reason = "namespaced_junit_content"
		return r
	}
	r.Disposition = "junit"
	r.Reason = "supported_junit_root"
	type attempt struct {
		id      string
		present bool
		state   string
	}
	attempts := map[string][]attempt{}
	var cases func(*Node) int
	cases = func(n *Node) int {
		v := 0
		if n.Name.Local == "testcase" {
			v++
		}
		for _, c := range n.Children {
			v += cases(c)
		}
		return v
	}
	var visit func(*Node, []string)
	visit = func(n *Node, path []string) {
		tag := n.Name.Local
		if tag == "testsuite" {
			name, ok := n.Attr["name"]
			if !ok {
				name = "unnamed"
			}
			path = append(append([]string{}, path...), name)
		}
		if tag == "testsuite" || tag == "testsuites" {
			if s, ok := n.Attr["tests"]; ok {
				v, valid := declaredInteger(s)
				if !valid {
					r.Limitations["invalid_declared_count"] = true
				} else if v.Cmp(big.NewInt(int64(cases(n)))) != 0 {
					r.Limitations["declared_count_mismatch"] = true
				}
			}
		}
		if tag == "testcase" {
			identity := append(append([]string{}, path...), n.Attr["classname"], n.Attr["name"])
			for _, s := range identity {
				if strings.Contains(s, "/") {
					r.Unknown["ambiguous_slash_identity"] = true
				}
			}
			state := "passed"
			for _, s := range []string{"error", "failure", "skipped"} {
				found := false
				for _, c := range n.Children {
					if c.Name.Local == s {
						found = true
					}
				}
				if found {
					state = s
					break
				}
			}
			r.Counts["attempts"] = r.Counts["attempts"].(int) + 1
			r.Counts[state] = r.Counts[state].(int) + 1
			id, present := n.Attr["attempt"]
			key := evidence.Hash(identity)
			attempts[key] = append(attempts[key], attempt{id, present, state})
		}
		if tag == "failure" || tag == "error" || tag == "skipped" {
			g := evidence.Object{"kind": tag, "exceptionType": n.Attr["type"], "message": n.Attr["message"], "text": n.Text.String()}
			id := evidence.Hash(g)
			if old, ok := r.Groups[id]; ok {
				old["occurrences"] = old["occurrences"].(int) + 1
			} else {
				g["id"] = id
				g["occurrences"] = 1
				r.Groups[id] = g
			}
			if len(n.Children) > 0 {
				r.Unknown["nested_diagnostic_markup"] = true
			}
			return
		}
		if tag == "attachment" {
			return
		}
		for _, c := range n.Children {
			switch c.Name.Local {
			case "properties", "system-out", "system-err":
				continue
			case "testsuite", "testsuites", "testcase", "failure", "error", "skipped", "attachment":
				visit(c, path)
			default:
				r.Unknown["unrecognized_element:"+c.Name.Local] = true
			}
		}
	}
	visit(root, []string{})
	for _, rows := range attempts {
		if len(rows) < 2 {
			continue
		}
		seen := map[string]bool{}
		for _, a := range rows {
			valid := a.present && a.id != ""
			for _, c := range a.id {
				if c < '0' || c > '9' {
					valid = false
				}
			}
			normalized := strings.TrimLeft(a.id, "0")
			if seen[normalized] {
				valid = false
			}
			seen[normalized] = true
			if !valid {
				r.Limitations["ambiguous_retry"] = true
			}
		}
	}
	if r.Counts["attempts"].(int) == 0 {
		r.Limitations["interrupted_or_no_tests"] = true
	}
	return r
}

// normalizeAttributes supplies XML 1.0 literal attribute-whitespace normalization
// missing from encoding/xml. Character references remain untouched. Go's XML
// decoder still validates and parses the entire result; this is not a parser.
func normalizeAttributes(raw []byte) []byte {
	raw = bytes.ReplaceAll(raw, []byte("\r\n"), []byte("\n"))
	raw = bytes.ReplaceAll(raw, []byte("\r"), []byte("\n"))
	out := bytes.Clone(raw)
	for i := 0; i < len(out); i++ {
		if out[i] != '<' {
			continue
		}
		skipped := false
		for _, delim := range [][2]string{{"<!--", "-->"}, {"<![CDATA[", "]]>"}, {"<?", "?>"}} {
			if bytes.HasPrefix(out[i:], []byte(delim[0])) {
				end := bytes.Index(out[i+len(delim[0]):], []byte(delim[1]))
				if end < 0 {
					return out
				}
				i += len(delim[0]) + end + len(delim[1]) - 1
				skipped = true
				break
			}
		}
		if skipped {
			continue
		}
		var quote byte
		for i++; i < len(out); i++ {
			b := out[i]
			if quote != 0 {
				if b == quote {
					quote = 0
				} else if b == '\n' || b == '\t' {
					out[i] = ' '
				}
			} else if b == '\'' || b == '"' {
				quote = b
			} else if b == '>' {
				break
			}
		}
	}
	return out
}

// Python int accepts decimal Unicode digits and underscores between digits.
func declaredInteger(s string) (*big.Int, bool) {
	s = strings.TrimSpace(s)
	var b strings.Builder
	previousDigit := false
	digits := 0
	for i, r := range s {
		if i == 0 && (r == '+' || r == '-') {
			b.WriteRune(r)
			continue
		}
		if r == '_' {
			if !previousDigit {
				return nil, false
			}
			previousDigit = false
			continue
		}
		digit := -1
		for _, row := range unicode.Nd.R16 {
			if r >= rune(row.Lo) && r <= rune(row.Hi) && (r-rune(row.Lo))%rune(row.Stride) == 0 {
				digit = int((r-rune(row.Lo))/rune(row.Stride)) % 10
				break
			}
		}
		if digit < 0 {
			for _, row := range unicode.Nd.R32 {
				if r >= rune(row.Lo) && r <= rune(row.Hi) && (r-rune(row.Lo))%rune(row.Stride) == 0 {
					digit = int((r-rune(row.Lo))/rune(row.Stride)) % 10
					break
				}
			}
		}
		if digit < 0 {
			return nil, false
		}
		digits++
		if digits > 4300 {
			return nil, false
		}
		b.WriteByte(byte('0' + digit))
		previousDigit = true
	}
	if !previousDigit {
		return nil, false
	}
	v, ok := new(big.Int).SetString(b.String(), 10)
	return v, ok
}
