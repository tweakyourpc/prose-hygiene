# Contributing

## Setup
```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .[dev]
```

## Run checks
```bash
python -m compileall -q src tests
ruff check .
mypy src
PYTHONPATH=src pytest -q
```

## Scope
- The CLI and Git hook flow are the primary supported release surfaces.
- `web.py` is useful for local demos, but changes to it should keep the experimental label unless it receives deeper review.
- Heuristic rewrites must stay deterministic and explainable. Avoid adding model calls or probabilistic rewrites.

## Tests
- Add or update tests for any engine or CLI behavior change.
- Prefer focused unit tests over large snapshot fixtures.
- When changing heuristics, include at least one positive and one negative test case.

## Hook safety
- The Git hook intentionally skips files with unstaged working-tree changes so it does not overwrite local edits.
- If you change hook behavior, preserve that safety property.
