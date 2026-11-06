//go:build ignore

// Run with: go run ./tools/build.go
// Builds target executables; only native tests establish execution compatibility.
package main

import (
	"crypto/sha256"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func main() {
	targets := []string{"darwin/amd64", "darwin/arm64", "linux/amd64", "linux/arm64", "windows/amd64", "windows/arm64"}
	if err := os.MkdirAll("dist", 0755); err != nil {
		panic(err)
	}
	checksums := ""
	for _, target := range targets {
		parts := strings.Split(target, "/")
		name := "testreceipts-" + parts[0] + "-" + parts[1]
		if parts[0] == "windows" {
			name += ".exe"
		}
		path := filepath.Join("dist", name)
		cmd := exec.Command("go", "build", "-trimpath", "-buildvcs=false", "-ldflags=-s -w", "-o", path, "./cmd/testreceipts")
		env := []string{}
		for _, v := range os.Environ() {
			if !strings.HasPrefix(v, "GOOS=") && !strings.HasPrefix(v, "GOARCH=") && !strings.HasPrefix(v, "CGO_ENABLED=") {
				env = append(env, v)
			}
		}
		cmd.Env = append(env, "GOOS="+parts[0], "GOARCH="+parts[1], "CGO_ENABLED=0")
		cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
		if err := cmd.Run(); err != nil {
			panic(err)
		}
		raw, err := os.ReadFile(path)
		if err != nil {
			panic(err)
		}
		checksums += fmt.Sprintf("%x  %s\n", sha256.Sum256(raw), name)
		fmt.Printf("%s: %d bytes (recorded comparison; native runtime validation is separate)\n", name, len(raw))
	}
	if err := os.WriteFile(filepath.Join("dist", "SHA256SUMS"), []byte(checksums), 0644); err != nil {
		panic(err)
	}
}
