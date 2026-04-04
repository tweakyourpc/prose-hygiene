# Installation

## Basic install
```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

## Development install
```bash
. .venv/bin/activate
python -m pip install -e .[dev]
```

## Optional global Git hook setup
If you want to use the dispatcher pattern globally:

```bash
git config --global core.hooksPath "$HOME/.config/git/hooks"
mkdir -p "$HOME/.config/git/hooks/pre-commit.d"
cp hooks/pre-commit "$HOME/.config/git/hooks/pre-commit"
cp hooks/pre-commit.d/10-prose-hygiene "$HOME/.config/git/hooks/pre-commit.d/10-prose-hygiene"
cp hooks/pre-commit.d/20-ai-word-scrub "$HOME/.config/git/hooks/pre-commit.d/20-ai-word-scrub"
chmod +x "$HOME/.config/git/hooks/pre-commit" "$HOME/.config/git/hooks/pre-commit.d/10-prose-hygiene" "$HOME/.config/git/hooks/pre-commit.d/20-ai-word-scrub"
```

## Verification
```bash
python -m compileall -q src tests
ruff check .
mypy src
PYTHONPATH=src pytest -q
```
