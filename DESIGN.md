# Design

`prose-hygiene` is a deterministic cleanup layer for AI-assisted documentation workflows.

## Principles
- deterministic transforms over probabilistic rewrites
- advisory automation over blocking workflows
- local execution with no model dependency
- composable outputs for hooks and higher-level tooling

## Scope
The current implementation focuses on em dashes and a small advisory phrase detector, but the broader concept is **AI documentation hygiene**: catching and cleaning style drift introduced by coding agents.

## Non-goals
- It is not a general-purpose prose rewriter.
- It is not trying to infer author intent beyond narrow, explainable heuristics.
- It is not a replacement for broader editorial tooling such as Vale or markdownlint.

## Layers
- `style.py` - heuristic rewrite engine
- `engine.py` - traversal, ignore rules, reporting
- `cli.py` - command-line entry
- `web.py` - experimental local/demo UI
- `hooks/` - commit-time automation

## Architecture rationale

The project is intentionally split so the highest-risk logic stays easy to review:
- `style.py` owns the rewrite decisions
- `engine.py` owns traversal and artifact handling
- `cli.py` owns process boundaries and output formatting

That separation keeps the heuristic core testable without tying it to filesystem or process concerns.
