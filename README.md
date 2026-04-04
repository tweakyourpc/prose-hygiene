# prose-hygiene

Deterministic prose cleanup for AI-assisted documentation workflows.

`prose-hygiene` started as an em dash scrubber and evolved into a broader proof of concept for **AI documentation hygiene**: a local, explainable cleanup layer that normalizes common stylistic artifacts before generated docs land in a repository.

## Why this exists
AI coding tools often write polished but stylistically repetitive documentation. Em dashes are a common example, but they are really just one symptom of a larger problem: generated prose drifting away from repository norms.

This project closes that loop with:
- a deterministic rewrite engine
- structured CLI output
- Git hook integration
- advisory phrase warnings
- optional web UI for local/demo use

## What it does today
- rewrites U+2014 em dashes using context-aware heuristics
- skips fenced code blocks
- supports files, directories, and zip archives
- emits JSON reports for automation
- provides a pre-commit dispatcher pattern with additive drop-in hooks
- warns on selected AI-style phrases without blocking commits

## Install
```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

For local development:
```bash
. .venv/bin/activate
python -m pip install -e .[dev]
```

## Quick start
```bash
prose-hygiene README.md /tmp/README.clean.md --json
prose-hygiene docs/ /tmp/docs-clean --json
prose-hygiene docs/ /tmp/docs-clean --json --normalize-heading-commas
```

To skip a file entirely, add one of these markers near the top of the file:
```md
prose-hygiene: ignore-file
<!-- prose-hygiene: ignore-file -->
```

## Git hook model
- `hooks/pre-commit` runs all executable files in `hooks/pre-commit.d/`
- `10-prose-hygiene` auto-fixes staged documentation files and re-stages them
- `20-ai-word-scrub` warns on high-signal AI prose markers

If a staged file also has unstaged working-tree edits, `10-prose-hygiene` now skips that file rather than overwrite local changes.

## Release posture
The CLI and hook workflow are the primary polished surfaces.

> `web.py` is currently **experimental** and should be treated as a local/demo interface until it receives deeper review.

## Development checks
```bash
python -m compileall -q src tests
ruff check .
mypy src
PYTHONPATH=src pytest -q
```

## Docs
- `CHANGELOG.md`
- `DESIGN.md`
- `INSTALLATION.md`
- `DEV_NOTES.md`
- `KNOWN_LIMITATIONS.md`
- `SECURITY.md`
- `WEB_NOTES.md`
- `docs/ai-documentation-hygiene.md`
- `docs/comparison-with-linters.md`
- `docs/example-cleanup-walkthrough.md`
- `docs/tech-deep-dive.md`
- `docs/two-layer-model.md`
- `docs/git-hooks-architecture.md`
- `docs/codex-feature-request.md`
