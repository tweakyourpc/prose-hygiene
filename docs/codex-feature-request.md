# Feature Request: Repository-Native Documentation Hygiene Feedback

## Problem statement

Coding agents can already receive repository instructions, but they usually do not have a standard way to consume deterministic hygiene feedback from the repository after they write documentation.

That leaves a gap:
- the repo can say "do not write this way"
- the repo can detect or rewrite violations at commit time
- the agent still does not learn from the result in a structured, native way

## Proof of concept in this repository

`prose-hygiene` demonstrates a two-layer pattern:
- upstream guidance through repository-local agent instructions and skills
- downstream deterministic cleanup or advisory feedback through Git hooks

The current proof of concept includes:
- deterministic dash normalization across em dashes, en dashes, and spaced `--`
- optional heading-comma normalization
- advisory AI phrase warnings
- structured JSON reports for automation

## Concrete workflow

1. An agent writes or edits documentation in a repository.
2. The repository provides local instructions that discourage certain stylistic artifacts.
3. A deterministic hook runs before commit.
4. The hook either rewrites the staged artifact or emits structured advisory output.
5. The agent sees a machine-readable explanation of what changed and can adapt future output.

Example structured feedback:

```json
{
  "kind": "file",
  "summary": {
    "fixed": 1,
    "matches": 3
  },
  "strategies": {
    "colon": 2,
    "comma": 1
  },
  "files": [
    {
      "relative_path": "README.md",
      "status": "fixed",
      "count": 3
    }
  ]
}
```

## Why this matters

This closes the loop on AI-generated documentation artifacts before they land in version control, without requiring another model pass.

## Why deterministic feedback is a good fit

- cheap
- explainable
- local
- auditable
- easy to run in hooks and CI

## Specific request

Add first-class support for repository-native hygiene feedback in agent tooling.

Examples of what that could look like:
- automatic discovery of repo-local instruction files on session start
- a standard place for hygiene tools to emit structured feedback
- a built-in way for agents to ingest and summarize post-write hook or checker output
- optional memory of repeated hygiene corrections inside the current repo session

## Why this is different from generic linting

This is not asking agents to run arbitrary editorial tooling by default. It is asking for a narrow, standardized bridge between:
- repository-local instructions
- deterministic cleanup tools
- the agent's next response

That bridge is the missing integration point.
