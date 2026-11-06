Work in this new CI Evidence repository. Read HANDOFF.md, AGENTS.md, Tasks.md and docs/PORTING-CONTRACT.md first.

This project was spun out of Spotlightning. It is independent of Spotlight/macOS. Build the portable Go CLI, starting with G01: match the included Python reference on local recorded CI fixtures, then prepare standalone builds for macOS, Linux and Windows. Keep production dependencies minimal; no Python runtime in the deployed tool.

Run tools/verify.py before changing the reference. Implement the real parser and compare-recording command; the current Go CLI is only a scaffold. Preserve source hashes, exact diagnostic text, original-record counts, explicit incomplete/unsupported states and bounded input sizes. Use the supplied expected outputs and independent checker, and add tests for gaps. Do not silently replace the capable baselines with weaker ones.

Keep inputs, outputs and charts easy to inspect. Keep bulky artifacts out of Git. Do not run model/agent evaluations, upload data, publish releases or add an MCP service as part of the initial port. Record actual build size and platform test results without claiming cross-compilation proves runtime compatibility. Update task status and report exactly what passed and what remains unimplemented.
