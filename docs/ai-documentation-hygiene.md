# AI Documentation Hygiene

AI coding tools can generate excellent structure and useful content, but they also leave recognizable stylistic fingerprints. This project treats those fingerprints as a hygiene problem that can be improved deterministically before documentation lands in a repo.

Current examples include:
- overuse of em dashes and en dashes as prose separators
- space-flanked `--` that reads like a typewriter-era fallback
- stock discourse markers
- polished but repetitive phrasing

## Why this matters

Documentation style drift is usually too small to justify another model pass and too repetitive to justify manual cleanup on every commit. That makes it a good fit for narrow, deterministic tooling.

## Why deterministic cleanup fits

This layer should be:
- cheap to run
- easy to audit
- local to the repository
- predictable enough for hooks and automation

`prose-hygiene` is a proof of concept for handling that layer locally and predictably.
