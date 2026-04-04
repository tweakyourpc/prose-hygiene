# Comparison With Existing Linters

Tools like Vale, markdownlint, and proselint are valuable, but they primarily flag issues. `prose-hygiene` occupies a slightly different space:

- deterministic transformation, not just detection
- workflow-integrated auto-fix for specific artifacts
- designed around AI-generated documentation drift
- structured reporting for hooks and tool integration

## How to think about the boundary

Use traditional linters when you want broad editorial coverage and style-policy enforcement.

Use `prose-hygiene` when you want a narrow cleanup layer for a few high-signal artifacts that are common in AI-assisted documentation workflows.

It complements traditional linters rather than replacing them.
