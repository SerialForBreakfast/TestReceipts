package junit

import (
	"bytes"
	"encoding/xml"
	"io"
	"strings"
)

// encoding/xml permits undeclared prefixes. Validate namespace bindings through
// its streaming RawToken API before building facts, so malformed prefixed
// attributes cannot silently become an anonymous passing testcase.
func namespaceCheck(raw []byte) string {
	const xmlURI = "http://www.w3.org/XML/1998/namespace"
	const xmlnsURI = "http://www.w3.org/2000/xmlns/"
	decoder := xml.NewDecoder(bytes.NewReader(raw))
	scopes := []map[string]string{{"xml": xmlURI}}
	nodes := 0
	for {
		token, err := decoder.RawToken()
		if err == io.EOF {
			return ""
		}
		if err != nil {
			return "malformed_xml"
		}
		switch token := token.(type) {
		case xml.StartElement:
			nodes++
			if nodes > MaxNodes || len(scopes) > MaxDepth {
				return "xml_structure_budget_exceeded"
			}
			scope := scopes[len(scopes)-1]
			copied := false
			declared := map[string]bool{}
			for _, a := range token.Attr {
				prefix := ""
				isDeclaration := false
				if a.Name.Space == "xmlns" {
					prefix = a.Name.Local
					isDeclaration = true
				} else if a.Name.Space == "" && a.Name.Local == "xmlns" {
					isDeclaration = true
				}
				if !isDeclaration {
					continue
				}
				if declared[prefix] || prefix == "xmlns" || strings.Contains(prefix, ":") || a.Value == xmlnsURI || (prefix == "xml" && a.Value != xmlURI) || (prefix != "xml" && a.Value == xmlURI) || (prefix != "" && a.Value == "") {
					return "malformed_xml"
				}
				declared[prefix] = true
				if !copied {
					next := map[string]string{}
					for k, v := range scope {
						next[k] = v
					}
					scope = next
					copied = true
				}
				scope[prefix] = a.Value
			}
			if strings.Contains(token.Name.Local, ":") || token.Name.Space == "xmlns" {
				return "malformed_xml"
			}
			if token.Name.Space != "" && scope[token.Name.Space] == "" {
				return "malformed_xml"
			}
			attributes := map[xml.Name]bool{}
			for _, a := range token.Attr {
				if a.Name.Space == "xmlns" || (a.Name.Space == "" && a.Name.Local == "xmlns") {
					continue
				}
				if strings.Contains(a.Name.Local, ":") {
					return "malformed_xml"
				}
				if a.Name.Space != "" {
					uri := scope[a.Name.Space]
					if uri == "" {
						return "malformed_xml"
					}
					a.Name.Space = uri
				}
				if attributes[a.Name] {
					return "malformed_xml"
				}
				attributes[a.Name] = true
			}
			scopes = append(scopes, scope)
		case xml.EndElement:
			if len(scopes) <= 1 {
				return "malformed_xml"
			}
			scopes = scopes[:len(scopes)-1]
		}
	}
}
