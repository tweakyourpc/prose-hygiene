# prose-hygiene

Deterministic cleanup for AI-assisted documentation workflows.

`prose-hygiene` is a local rewrite layer for docs that are structurally useful but stylistically off. Its job is narrow on purpose: take common high-signal punctuation artifacts from AI-written documentation, normalize them predictably, and leave the rest of the prose alone.

## Intended use

Use `prose-hygiene` when:
- AI tools wrote the draft and the content is mostly right
- you want automatic cleanup before docs land in the repo
- you want a fast, explainable rewrite pass instead of another model pass
- you want hooks or CI to enforce repository prose norms consistently

Do not use it as a general-purpose prose improver. It is a deterministic hygiene tool, not an editorial assistant.

## What it rewrites

Today the rewrite engine normalizes a small set of punctuation artifacts with context-aware heuristics:
- U+2014 em dashes
- U+2013 en dashes in numeric ranges and prose-like separator usage
- space-flanked `--`
- optional heading-style comma normalization like `Foo, Bar` -> `Foo: Bar`

It preserves structured regions that should not be touched:
- fenced code blocks
- inline backticks
- YAML frontmatter
- HTML comments

## Why this exists

AI coding tools often produce documentation that is useful, readable, and still slightly off-style. The drift is usually repetitive rather than deep: dash overuse, typewriter-era separators, stock transitions, and similar narrow artifacts.

That is a good fit for deterministic cleanup because it is:
- cheap to run
- easy to audit
- local to the repository
- predictable enough for hooks and automation

## What it does today

- rewrites common punctuation artifacts using explainable heuristics
- skips structured regions that should remain verbatim
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

Examples:
- `It works: but only after restart.` -> `It works, but only after restart.`
- `Range 1–40 not allowed.` -> `Range 1-40 not allowed.`
- `Bad use -- like this.` -> `Bad use, like this.`

To skip a file entirely, add one of these markers near the top of the file:
```md
prose-hygiene: ignore-file
<!-- prose-hygiene: ignore-file -->
```

## Git hook model

- `hooks/pre-commit` runs all executable files in `hooks/pre-commit.d/`
- `10-prose-hygiene` auto-fixes staged documentation files and re-stages them
- `20-ai-word-scrub` warns on high-signal AI prose markers

If a staged file also has unstaged working-tree edits, `10-prose-hygiene` skips that file rather than overwrite local changes.

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
