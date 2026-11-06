//go:build ignore

// Compatibility entry point for the single release pipeline. Packaging is a
// development operation; Python is never included in runtime packages.
package main

import (
	"os"
	"os/exec"
)

func main() {
	args := append([]string{"tools/release.py"}, os.Args[1:]...)
	cmd := exec.Command("python3", args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
