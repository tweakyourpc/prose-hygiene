# The Two-Layer Model

## The loop

`prose-hygiene` is built around a simple feedback loop:

1. An agent writes or edits documentation.
2. The repository provides local instructions that discourage certain output patterns.
3. A deterministic tool runs locally on the staged artifact.
4. The tool rewrites or reports narrow, explainable issues.
5. The agent can use that feedback to improve the next revision.

## Layer 1: Upstream guidance

This repository uses local agent guidance in `codex/SKILL.md` to tell an agent when the cleanup tool should be used and what kind of output matters.

## Layer 2: Downstream enforcement

The hook scripts apply deterministic cleanup and advisory checks at commit time:
- `10-prose-hygiene` for auto-fix behavior
- `20-ai-word-scrub` for advisory-only phrase warnings

## Why the model matters

Most agent tooling already has some notion of project instructions. Most repositories can also run local checks. The missing integration point is a standard, structured bridge between those two layers.

That bridge is the core argument behind the feature-request document in this repository.
