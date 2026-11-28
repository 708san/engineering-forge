# Local text trim — development entry and specification
This is a public synthetic calibration example (CAL-03), not an approved real product.
## Purpose and protected requirements
Remove trailing horizontal whitespace from local text without changing the original or sending data over a network. Use a separate, previously nonexistent output path; never overwrite input or existing output.
## Design decision
Small, trusted local UTF-8 files only. Remove ASCII spaces and tabs immediately before CRLF, CR, LF or end of file; preserve other characters (including fullwidth spaces), mixed newline encodings and BOM if present. Reject invalid UTF-8 before creating output. Standard Python library only. One developer, no custom agent, server, database or formal record ledger. These semantics are provisional design decisions for this example, not user-approved general requirements.
## How to use and verify
Python 3.11+: `python -B trim.py input.txt output.txt`. Test from this directory: `python -B -m unittest -v test_trim`. Verify input preservation, byte-exact expected output and refusal to overwrite. No network or Engineering Forge installation required.
## Change and next work
Keep the source/output separation and local-only constraints. Propose changes to them separately; no publication or extra authority implied. Verify and preserve human edits. Limitations: reads entire file in memory; long internal whitespace may cause slow regex matching; write failure may leave partial new output. Trusted stationary local files only, not hostile filesystem or concurrent modification. Next improvement if actual use warrants it: linear-time scanning and crash-safe output creation, with additional performance/failure tests. No need for additional roles now. This example does not establish independent review or production readiness.
