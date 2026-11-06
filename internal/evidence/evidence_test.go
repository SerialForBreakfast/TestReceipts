package evidence

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
	"unicode/utf8"
)

func TestCanonicalVectors(t *testing.T) {
	raw, err := os.ReadFile("../../testdata/canonical-vectors.json")
	if err != nil {
		t.Fatal(err)
	}
	var rows []struct {
		Value   any
		UTF8Hex string
		SHA256  string
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.UseNumber()
	if err = d.Decode(&rows); err != nil {
		t.Fatal(err)
	}
	for _, r := range rows {
		b := Canonical(r.Value)
		if hex.EncodeToString(b) != r.UTF8Hex || Digest(b) != r.SHA256 {
			t.Fatalf("canonical mismatch %s", b)
		}
	}
}
func TestExcerpt(t *testing.T) {
	s := ""
	for i := 0; i < 513; i++ {
		s += "🙂"
	}
	got := Excerpt(s, 512)
	if utf8.RuneCountInString(got) != 512 || !utf8.ValidString(got) {
		t.Fatal("excerpt split Unicode")
	}
}

func TestAddedRanking(t *testing.T) {
	after := map[string]Object{}
	for _, s := range []string{"a", "b", "c", "d"} {
		after[s] = Object{"id": s, "kind": "error", "exceptionType": "", "message": "", "text": "🙂", "occurrences": 1}
	}
	after["d"]["occurrences"] = 4
	out := Compare([]Object{}, []map[string]Object{{}, after})
	rows := out["newEvidence"].([]Object)
	if len(rows) != 3 || rows[0]["id"] != "d" || rows[1]["id"] != "a" || rows[2]["id"] != "b" || out["change"].(Object)["newOccurrences"] != 7 {
		t.Fatal(out)
	}
}
