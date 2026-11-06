//go:build ignore

// Inspect cross-built executables without executing them.
package main

import (
	"debug/elf"
	"debug/macho"
	"debug/pe"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

func main() {
	rows := []map[string]any{}
	for _, path := range os.Args[1:] {
		row := map[string]any{"binary": filepath.Base(path)}
		if f, e := elf.Open(path); e == nil {
			row["format"] = "ELF"
			row["machine"] = f.Machine.String()
			interpreters := []string{}
			for _, p := range f.Progs {
				if p.Type == elf.PT_INTERP {
					raw, e := os.ReadFile(path)
					if e != nil {
						panic(e)
					}
					interpreters = append(interpreters, string(raw[p.Off:p.Off+p.Filesz]))
				}
			}
			row["interpreters"] = interpreters
			libs, _ := f.ImportedLibraries()
			if libs == nil {
				libs = []string{}
			}
			row["importedLibraries"] = libs
			f.Close()
		} else if f, e := macho.Open(path); e == nil {
			row["format"] = "Mach-O"
			row["machine"] = f.Cpu.String()
			libs, e := f.ImportedLibraries()
			if e != nil {
				panic(e)
			}
			row["importedLibraries"] = libs
			for _, l := range f.Loads {
				raw := l.Raw()
				if len(raw) >= 16 && f.ByteOrder.Uint32(raw[:4]) == 0x32 {
					v := f.ByteOrder.Uint32(raw[12:16])
					row["linkedMinimumOS"] = fmt.Sprintf("%d.%d.%d", v>>16, (v>>8)&255, v&255)
				}
			}
			f.Close()
		} else if f, e := pe.Open(path); e == nil {
			row["format"] = "PE"
			row["machine"] = fmt.Sprintf("0x%x", f.Machine)
			symbols, e := f.ImportedSymbols()
			if e != nil {
				panic(e)
			}
			set := map[string]bool{}
			for _, symbol := range symbols {
				if i := strings.LastIndex(symbol, ":"); i >= 0 {
					set[symbol[i+1:]] = true
				}
			}
			libs := []string{}
			for lib := range set {
				libs = append(libs, lib)
			}
			sort.Strings(libs)
			row["importedLibraries"] = libs
			row["importScope"] = "PE direct import table only; dynamic OS loads not enumerated"
			f.Close()
		} else {
			panic("unknown executable format")
		}
		rows = append(rows, row)
	}
	if err := json.NewEncoder(os.Stdout).Encode(rows); err != nil {
		panic(err)
	}
}
