package evidence

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"math/big"
	"strconv"
	"strings"
	"unicode/utf8"
)

// DecodeJSON rejects duplicate keys, trailing data and non-integer JSON numbers.
func DecodeJSON(raw []byte) (any, error) {
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
