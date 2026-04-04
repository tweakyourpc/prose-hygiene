# Git Hooks Architecture

This project uses a dispatcher model instead of a single monolithic hook.

## Pattern
- `pre-commit` acts as a dispatcher
- executable scripts in `pre-commit.d/` run in lexicographic order
- new hooks can be added without editing the dispatcher

## Included hooks
- `10-prose-hygiene`: auto-fix staged documentation-like files and re-stage them
- `20-ai-word-scrub`: advisory phrase detection without blocking commits

## Why the dispatcher is useful

This keeps repository hygiene additive. New checks can be introduced as separate executables with their own failure or advisory semantics, instead of forcing every behavior into one growing shell script.

## Safety behavior

The auto-fix hook reads the staged version of each file. If the working tree also contains unstaged edits for that file, the hook now skips it rather than overwrite local changes. That makes the hook safer for partial staging workflows.
