// Package evidence defines canonical identities and exact diagnostic comparisons.
package evidence

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"sort"
	"strconv"
	"unicode/utf8"
)

type Object = map[string]any

// Canonical matches Python's ensure_ascii=False, sort_keys=True compact JSON.
// This intentionally does not use encoding/json's HTML or U+2028 escaping.
func Canonical(v any) []byte {
	var b bytes.Buffer
	var write func(any)
	quote := func(s string) {
		b.WriteByte('"')
		for _, r := range s {
			switch r {
			case '"', '\\':
				b.WriteByte('\\')
				b.WriteRune(r)
			case '\b':
				b.WriteString(`\b`)
			case '\f':
				b.WriteString(`\f`)
			case '\n':
				b.WriteString(`\n`)
			case '\r':
				b.WriteString(`\r`)
			case '\t':
				b.WriteString(`\t`)
			default:
				if r < 32 {
					fmt.Fprintf(&b, `\u%04x`, r)
				} else {
					b.WriteRune(r)
				}
			}
		}
		b.WriteByte('"')
	}
	write = func(v any) {
		switch x := v.(type) {
		case nil:
			b.WriteString("null")
		case string:
			quote(x)
		case bool:
			if x {
				b.WriteString("true")
			} else {
				b.WriteString("false")
			}
		case int:
			b.WriteString(strconv.Itoa(x))
		case int64:
			b.WriteString(strconv.FormatInt(x, 10))
		case json.Number:
			b.WriteString(string(x))
		case []any:
			b.WriteByte('[')
			for i, y := range x {
				if i > 0 {
					b.WriteByte(',')
				}
				write(y)
			}
			b.WriteByte(']')
		case []Object:
			b.WriteByte('[')
			for i, y := range x {
				if i > 0 {
					b.WriteByte(',')
				}
				write(y)
			}
			b.WriteByte(']')
		case []string:
			b.WriteByte('[')
			for i, y := range x {
				if i > 0 {
					b.WriteByte(',')
				}
				quote(y)
			}
			b.WriteByte(']')
		case Object:
			keys := make([]string, 0, len(x))
			for k := range x {
				keys = append(keys, k)
			}
			sort.Strings(keys)
			b.WriteByte('{')
			for i, k := range keys {
				if i > 0 {
					b.WriteByte(',')
				}
				quote(k)
				b.WriteByte(':')
				write(x[k])
			}
			b.WriteByte('}')
		default:
			panic(fmt.Sprintf("unsupported canonical type %T", v))
		}
	}
	write(v)
	return b.Bytes()
}
func Digest(raw []byte) string { return fmt.Sprintf("%x", sha256.Sum256(raw)) }
func Hash(v any) string        { return Digest(Canonical(v)) }
func Sorted(set map[string]bool) []string {
	out := make([]string, 0, len(set))
	for s := range set {
		out = append(out, s)
	}
	sort.Strings(out)
	return out
}
func Excerpt(s string, n int) string {
	if utf8.RuneCountInString(s) <= n {
		return s
	}
	return string([]rune(s)[:n])
}
func Compare(runs []Object, groups []map[string]Object) Object {
	before, after := groups[0], groups[1]
	added := []string{}
	gone, shared := 0, 0
	for k := range after {
		if _, ok := before[k]; ok {
			shared++
		} else {
			added = append(added, k)
		}
	}
	for k := range before {
		if _, ok := after[k]; !ok {
			gone++
		}
	}
	sort.Slice(added, func(i, j int) bool {
		a, b := after[added[i]]["occurrences"].(int), after[added[j]]["occurrences"].(int)
		if a == b {
			return added[i] < added[j]
		}
		return a > b
	})
	total := 0
	rows := []Object{}
	for i, k := range added {
		g := after[k]
		total += g["occurrences"].(int)
		if i < 3 {
			s := g["text"].(string)
			row := Object{}
			for _, key := range []string{"id", "kind", "exceptionType", "message", "occurrences"} {
				row[key] = g[key]
			}
			row["text"] = Excerpt(s, 512)
			row["totalCharacters"] = utf8.RuneCountInString(s)
			rows = append(rows, row)
		}
	}
	return Object{"runs": runs, "change": Object{"newDistinct": len(added), "disappearedDistinct": gone, "sharedDistinct": shared, "newOccurrences": total}, "newEvidence": rows}
}
