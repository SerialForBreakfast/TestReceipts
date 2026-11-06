package junit

import (
	"strings"
	"testing"
)

func TestClassification(t *testing.T) {
	for _, c := range []struct{ xml, disposition, reason string }{
		{"<config/>", "non-junit", "non_junit_xml_root"}, {"<testsuite", "blocked", "malformed_xml"}, {"<testsuite/><testsuite/>", "blocked", "malformed_xml"}, {"<!DOCTYPE testsuite><testsuite/>", "blocked", "entity_declaration"}, {"<testsuite xmlns='u'/>", "blocked", "unsupported_junit_like_root"}, {"<testsuite><x xmlns='u'/></testsuite>", "blocked", "namespaced_junit_content"}, {"<wrapper><testcase/></wrapper>", "blocked", "unsupported_junit_like_root"}, {"<testsuite/>", "junit", "supported_junit_root"}, {string([]byte{255}), "blocked", "unsupported_encoding"}, {strings.Repeat(" ", MaxXML+1), "blocked", "xml_budget_exceeded"}, {strings.Repeat("<x>", MaxDepth+1) + strings.Repeat("</x>", MaxDepth+1), "blocked", "xml_structure_budget_exceeded"},
	} {
		r := Parse([]byte(c.xml))
		if r.Disposition != c.disposition || r.Reason != c.reason {
			t.Errorf("%q: %s %s", c.xml[:min(len(c.xml), 80)], r.Disposition, r.Reason)
		}
	}
}
func TestFacts(t *testing.T) {
	r := Parse([]byte(`<testsuite name="a/b" tests="9"><error>suite</error><testcase name="x"><skipped/><failure>f</failure><error>e</error></testcase><testcase name="x"/><testcase name="nested"><failure>first<b>hidden</b>tail</failure></testcase><weird/></testsuite>`))
	if r.Counts["attempts"] != 3 || r.Counts["error"] != 1 || r.Counts["failure"] != 1 || r.Counts["passed"] != 1 || len(r.Groups) != 5 {
		t.Fatalf("bad facts %+v", r)
	}
	for _, key := range []string{"ambiguous_slash_identity", "nested_diagnostic_markup", "unrecognized_element:weird"} {
		if !r.Unknown[key] {
			t.Error("missing", key)
		}
	}
	for _, key := range []string{"ambiguous_retry", "declared_count_mismatch"} {
		if !r.Limitations[key] {
			t.Error("missing", key)
		}
	}
	for _, g := range r.Groups {
		if g["text"] == "firsttail" {
			t.Fatal("nested tail changes original signature")
		}
	}
}
func TestRetries(t *testing.T) {
	for _, ids := range [][2]string{{"1", "2"}, {"00", "0"}, {"١", "2"}, {"", "2"}} {
		r := Parse([]byte(`<testsuite><testcase name="x" attempt="` + ids[0] + `"/><testcase name="x" attempt="` + ids[1] + `"/></testsuite>`))
		want := ids[0] != "1"
		if r.Limitations["ambiguous_retry"] != want {
			t.Fatalf("%v %+v", ids, r.Limitations)
		}
	}
}
func FuzzParse(f *testing.F) {
	for _, s := range []string{"<testsuite/>", "<testsuite><testcase><failure>🙂</failure></testcase></testsuite>", "<!ENTITY a 'x'>"} {
		f.Add([]byte(s))
	}
	f.Fuzz(func(t *testing.T, raw []byte) {
		if len(raw) > MaxXML+1 {
			return
		}
		r := Parse(raw)
		if r.Disposition == "" || r.Reason == "" {
			t.Fatal("missing disposition")
		}
	})
}

func TestAttributeNormalization(t *testing.T) {
	r := Parse([]byte("<testsuite><testcase><failure message=\"a\tb\nc\r\nd&#10;e&#9;\">pre<![CDATA[<raw>]]><!--ignored-->tail&#13;</failure></testcase></testsuite>"))
	for _, g := range r.Groups {
		if g["message"] != "a b c d\ne\t" || g["text"] != "pre<raw>tail\r" {
			t.Fatalf("normalization changed facts %+v", g)
		}
	}
}
func TestDeclaredIntegers(t *testing.T) {
	for _, s := range []string{"99999999999999999999999999999999999999", "１_２", "١٢"} {
		r := Parse([]byte(`<testsuite tests="` + s + `"/>`))
		if !r.Limitations["declared_count_mismatch"] || r.Limitations["invalid_declared_count"] {
			t.Error(s, r.Limitations)
		}
	}
	r := Parse([]byte(`<testsuite tests="1__2"/>`))
	if !r.Limitations["invalid_declared_count"] {
		t.Fatal("invalid integer accepted")
	}
}
func TestNodeBudget(t *testing.T) {
	r := Parse([]byte("<testsuite>" + strings.Repeat("<testcase/>", MaxNodes) + "</testsuite>"))
	if r.Reason != "xml_structure_budget_exceeded" {
		t.Fatal(r.Reason)
	}
}

func TestNamespaceValidity(t *testing.T) {
	for _, xml := range []string{`<testsuite><testcase p:name="x"/></testsuite>`, `<testsuite p:name="x"/>`, `<testsuite xmlns:p=""><testcase/></testsuite>`, `<testsuite xmlns:xml="wrong"/>`, `<testsuite xmlns:p="u" xmlns:q="u" p:a="1" q:a="2"/>`, `<testsuite a="1" a="2"/>`} {
		r := Parse([]byte(xml))
		if r.Reason != "malformed_xml" {
			t.Fatalf("malformed namespaces accepted: %s %+v", xml, r)
		}
	}
	r := Parse([]byte(`<testsuite xmlns:p="u"><testcase p:name="ignored" xml:lang="en"/></testsuite>`))
	if r.Disposition != "junit" || r.Counts["passed"] != 1 {
		t.Fatal("valid namespaced attributes rejected", r)
	}
}

func TestDeclaredIntegerBudget(t *testing.T) {
	r := Parse([]byte(`<testsuite tests="` + strings.Repeat("9", 4301) + `"/>`))
	if !r.Limitations["invalid_declared_count"] {
		t.Fatal("integer digit budget ignored")
	}
}
